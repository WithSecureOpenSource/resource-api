"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import inspect

from abc import ABCMeta, abstractmethod, abstractproperty

from .schema import Schema
from .errors import ResourceDeclarationError


class BaseMetaClass(ABCMeta):

    def __init__(cls, name, bases, dct):
        super(BaseMetaClass, cls).__init__(name, bases, dct)

        class ResourceSchema(cls.Schema, Schema):
            pass

        cls.Schema = ResourceSchema

        class QuerySchema(cls.QuerySchema, Schema):
            pass

        cls.QuerySchema = QuerySchema


class BaseInterface(object):
    __metaclass__ = BaseMetaClass

    @classmethod
    def get_name(cls):
        return cls.__module__ + "." + cls.__name__

    class Schema:
        pass

    class QuerySchema:
        pass

    class Meta:
        pass

    def __str__(self):
        return self.get_name()

    def __init__(self, context):
        """
        context (object)
            entity that is supposed to hold DAL (data access layer) related functionality like database connections,
            network sockets, etc.
        """

        self.schema = self.Schema()
        self.query_schema = self.QuerySchema()
        self.meta = self.Meta()
        self.context = context

        # Readonly fields cannot be required and have default values
        for field_name in self.schema.find_fields(readonly=True):
            self.schema._required_fields.discard(field_name)
            self.schema._defaults.pop(field_name, None)
            self.schema.fields[field_name].default = None
            self.schema.fields[field_name].required = False

    def get_schema(self):
        meta = {}
        for key in dir(self.Meta):
            if not key.startswith("_"):
                meta[key] = getattr(self.Meta, key)
        if meta:
            return {"meta": meta}
        else:
            return {}


class AbstractUriPolicy(object):
    """
    Defines a way to generate `URI <http://en.wikipedia.org/wiki/Uniform_resource_identifier>`_ based on data that was
    passed when creating the resource.
    """
    __metaclass__ = ABCMeta

    def __init__(self, resource_instance):
        """
        resource_instance (Resource instance)
            entity that can be used to access previously created items
        """
        self._resource_instance = resource_instance

    @abstractproperty
    def type(self):
        """ A string that would give a hint to the client which PK policy is in use """

    @abstractmethod
    def generate_pk(self, data, link_data=None):
        """ Generates a PK based on input data

        data (dict):
            the same data that is passed to Resource's *create* method
        link_data (dict):
            the same link_data that is passed to Resource's *create* method
        @return
            generated PK
        """

    @abstractmethod
    def deserialize(self, pk):
        """ Transforms data sent over the wire into sth. usable inside DAL

        pk
            PK value as it comes over the wire - e.g. string in case of HTTP
        @return
            PK transformed to the data type expected to by DAL in order to fetch data
        """

    @abstractmethod
    def serialize(self, pk):
        """ Transforms value into sth. ready to transfer over the wire

        pk
            PK value used within DAL to identify stored entries
        @return
            PK transformed into something that can be sent over the wire - e.g. string in case of HTTP
        """

    def get_schema(self):
        """ Returns meta information (dict) to be included into resource's schema """
        return {
            "description": self.__doc__,
            "type": self.type
        }


class PkUriPolicy(AbstractUriPolicy):
    """ Uses value of a field marked as "pk=True" as resource's URI """

    def __init__(self, resource_instance):
        super(PkUriPolicy, self).__init__(resource_instance)

        def _err(msg):
            raise ResourceDeclarationError(resource_instance.__class__, msg)

        found = resource_instance.schema.find_fields(pk=True)
        if len(found) == 0:
            _err("PK field is not defined")
        elif len(found) == 1:
            self._pk_name = list(found)[0]
            self._pk_field = resource_instance.schema.fields[self._pk_name]
        else:
            _err("Multiple PKs found: %s" % ", ".join(found))

    @property
    def type(self):
        return "pk_policy"

    def generate_pk(self, data, link_data=None):
        return data.get(self._pk_name)

    def deserialize(self, pk):
        return self._pk_field.deserialize(pk)

    def serialize(self, pk):
        return self._pk_field.serialize(pk)


class ResourceMetaClass(BaseMetaClass):

    def __init__(cls, name, bases, dct):
        super(ResourceMetaClass, cls).__init__(name, bases, dct)

        for field_name, field in cls.iter_links():
            field.source = cls.get_name()
            field.name = field_name


class Resource(BaseInterface):
    """ Represents entity that is supposed to be exposed via public interface

    Methods have the following arguments:

        pk
            PK of exisiting resource
        data (dict)
            information to be stored within the resource
        params (dict)
            extra parameters to be used for collection filtering
        user (object)
            entity that corresponds to the user that performs certain operation on the resource

    """

    __metaclass__ = ResourceMetaClass
    UriPolicy = PkUriPolicy

    def __init__(self, context):
        super(Resource, self).__init__(context)
        self.UriPolicy = self.UriPolicy(self)
        self.links = self.Links()

    __init__.__doc__ = BaseInterface.__init__.__doc__

    @classmethod
    def iter_links(cls):
        for field_name in dir(cls.Links):
            if field_name.startswith("_"):
                continue
            link_class = getattr(cls.Links, field_name)
            if not inspect.isclass(link_class) or not issubclass(link_class, Link):
                continue
            yield field_name, link_class

    class Links:
        pass

    def get_schema(self):
        rval = {
            "description": self.__doc__,
            "schema": self.schema.get_schema(),
            "uri_policy": self.UriPolicy.get_schema()
        }
        rval.update(super(Resource, self).get_schema())
        query_schema = self.query_schema.get_schema()
        if query_schema:
            rval["query_schema"] = query_schema
        links = dict([(link_name, getattr(self.links, link_name).get_schema()) for link_name, _ in self.iter_links()])
        if links:
            rval["links"] = links
        return rval

    # Accessors

    @abstractmethod
    def exists(self, user, pk):
        """ Returns True if the resource exists """

    @abstractmethod
    def create(self, user, pk, data):
        """ Creates a new instance"""

    @abstractmethod
    def update(self, user, pk, data):
        """ Updates specified fields of a given instance """

    @abstractmethod
    def get_data(self, user, pk):
        """ Returns fields of the resource """

    @abstractmethod
    def delete(self, user, pk):
        """ Removes the resource """

    @abstractmethod
    def get_uris(self, user, params=None):
        """ Returns an iterable over primary keys """

    @abstractmethod
    def get_count(self, user, params=None):
        """ Returns total amount of items that fit filtering criterias """

    # AUTH methods

    def can_get_data(self, user, pk, data):
        """ Returns only the fields that user is allowed to fetch """
        return True

    def can_discover(self, user, pk):
        """ Returns False if user is not allowed to know about resoure's existence """
        return True

    def can_get_uris(self, user):
        """ Returns True if user is allowed to list the items in the collection or get their count """
        return True

    def can_update(self, user, pk, data):
        """ Returns True if user is allowed to update the resource """
        return True

    def can_create(self, user, data):
        """ Returns True if user is allowed to create resource with certain data """
        return True

    def can_delete(self, user, pk):
        """ Returns True if user is allowed to delete the resource """
        return True


class Link(BaseInterface):
    """ Represents a relationship between two resources that needs to be exposed via public interface

    Methods have the following arguments:

        pk
            PK of exisiting source resource (the one that defines link field)
        data (dict)
            extra information to be stored for this relationship
        rel_pk (digit|string)
            PK of exisiting target resource (the one to which we are linking to)
        params (dict)
            extra parameters to be used for collection filtering
        user (object)
            entity that corresponds to the user that performs certain operation on the link

    """

    __metaclass__ = BaseMetaClass

    class cardinalities:
        ONE = "ONE"
        MANY = "MANY"

    related_link = None
    cardinality = cardinalities.MANY
    master = False
    required = False
    one_way = False
    changeable = True
    readonly = False
    related_name = target = None

    def __init__(self, context):
        super(Link, self).__init__(context)
        cls = self.__class__

        for name in ["master", "required", "one_way", "changeable"]:
            if not isinstance(getattr(cls, name), bool):
                raise ResourceDeclarationError(cls, "%s must be boolean" % name)

        if self.one_way:
            self.master = True
        elif self.related_name is None:
            raise ResourceDeclarationError(cls, "related_name is not defined")

        if self.target is None:
            raise ResourceDeclarationError(cls, "target is not defined")

        if self.required and self.cardinality == cls.cardinalities.MANY:
            raise ResourceDeclarationError(cls, "Link to many can't be required")

        if "." not in cls.source:
            cls.source = cls.__module__ + "." + cls.source

        if "." not in cls.target:
            cls.target = cls.__module__ + "." + cls.target

        card = cls.cardinality
        if card not in [Link.cardinalities.ONE, Link.cardinalities.MANY]:
            raise ResourceDeclarationError(cls, "cardinality must be ONE or MANY is %r" % card)

    __init__.__doc__ = BaseInterface.__init__.__doc__

    def get_schema(self):
        if self.master:
            schema, query_schema = self.schema, self.query_schema
        else:
            schema, query_schema = self.related_link.schema, self.related_link.query_schema
        rval = {
            "target": self.target,
            "description": self.__doc__,
            "schema": schema.get_schema(),
            "required": self.required,
            "cardinality": self.cardinality,
            "changeable": self.changeable,
            "readonly": self.readonly
        }
        rval.update(super(Link, self).get_schema())
        if self.cardinality == self.cardinalities.MANY:
            query_schema = query_schema.get_schema()
            if query_schema:
                rval["query_schema"] = query_schema
        if self.one_way:
            rval["one_way"] = True
        else:
            rval["related_name"] = self.related_name
        return rval

    @classmethod
    def get_name(cls):
        return cls.source + ":" + cls.name

    @abstractmethod
    def exists(self, user, pk, rel_pk):
        """ Returns True if the link exists (is not nullable) """

    @abstractmethod
    def get_data(self, user, pk, rel_pk):
        """ Returns link data """

    @abstractmethod
    def create(self, user, pk, rel_pk, data=None):
        """ Creates a new link with optional extra data """

    @abstractmethod
    def update(self, user, pk, rel_pk, data):
        """ Updates exisiting link with specified data """

    @abstractmethod
    def delete(self, user, pk, rel_pk):
        """ Removes the link. If rel_pk is None - removes all links """

    @abstractmethod
    def get_uris(self, user, pk, params=None):
        """ Returns an iterable over target primary keys """

    @abstractmethod
    def get_count(self, user, pk, params=None):
        """ Returns total amount of items that fit filtering criterias """

    # AUTH methods

    def can_get_data(self, user, pk, rel_pk, data):
        """ Returns only the fields that user is allowed to fetch """
        return True

    def can_discover(self, user, pk, rel_pk):
        """ Returns False if user is not allowed to know about resoure's existence """
        return True

    def can_get_uris(self, user, pk):
        """ Returns True if user is allowed to list the items in the collection or get their count """
        return True

    def can_update(self, user, pk, rel_pk, data):
        """ Returns True if user is allowed to update the resource """
        return True

    def can_create(self, user, pk, rel_pk, data):
        """ Returns True if user is allowed to create resource with certain data """
        return True

    def can_delete(self, user, pk, rel_pk):
        """ Returns True if user is allowed to delete the resource """
        return True
