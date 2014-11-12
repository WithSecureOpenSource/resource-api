"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from .errors import DoesNotExist, ValidationError, DataConflictError, AuthorizationError
from .link import LinkHolder


class ResourceContainer(object):

    def __init__(self, entry_point, resource_interface):
        self._entry_point = entry_point
        self._res = resource_interface


class ResourceCollection(ResourceContainer):
    """
    The entity that represents a pile of resources.

    >>> student_collection = entry_point.get_resource(Student)

    The collection is iterable:

    >>> for student in student_collection:
    >>>    ...

    If :meth:`Resource.get_uris <resource_api.interfaces.Resource.get_uris>` is implemented to return an
    indexable entity the collection elements can be accessed by index as well:

    >>> student = student_collection[15]
    """

    def __init__(self, entry_point, resource_interface, params=None):
        super(ResourceCollection, self).__init__(entry_point, resource_interface)
        self._params = params or {}
        self._items = self._iter_items = None

    def _get(self, pk):
        return ResourceInstance(self._entry_point, self._res, pk)

    def __iter__(self):
        if self._items is None:
            if not self._res.can_get_uris(self._entry_point.user):
                raise AuthorizationError("Resource collection retrivial is not allowed")
            params = self._res.query_schema.deserialize(self._params, validate_required_constraint=False,
                                                        with_errors=False)
            self._items = self._res.get_uris(self._entry_point.user, params)
            self._iter_items = iter(self._items)
        return self

    def __getitem__(self, key):
        self.__iter__()
        target_pk = self._items[key]
        return self._get(target_pk)

    def __len__(self):
        self.__iter__()
        return len(self._items)

    def next(self):
        return self._get(self._iter_items.next())

    def filter(self, params=None):
        """
        Filtering options can be applied to collections to return new collections that contain a subset of original
        items:

        *NOTE*: filtering operations applied to root collections return normal collections

        >>> student_collection = entry_point.get_resource(Student)
        >>> new_collection = student_collection.filter(params={"name__startswith": "Abr"})
        """
        new_params = {}
        new_params.update(self._params)
        if params:
            new_params.update(params)
        return ResourceCollection(self._entry_point, self._res, new_params)

    def count(self):
        """ Returns count of all items within the system that satisfy filtering criterias.

        NOTE: :code:`len(collection)` is supposed to return the same result as :code:`collection.count()`. The key
        difference between them is that :code:`len` needs to fetch all items in the collection meanwhile
        :code:`collection.count()` relies on
        :meth:`Resource.get_count <resource_api.interfaces.Resource.get_count>`

        >>> len(student_collection)
        4569
        >>> student_collection.count()
        4569
        """
        if not self._res.can_get_uris(self._entry_point.user):
            raise AuthorizationError("Resource collection count retrivial is not allowed")
        params = self._res.query_schema.deserialize(self._params, validate_required_constraint=False,
                                                    with_errors=False)
        return self._res.get_count(self._entry_point.user, params)

    def serialize(self):
        rval = []
        for item in self:
            rval.append(item.serialize_pk())
        return rval


class RootResourceCollection(ResourceCollection):
    """
    Root resource collection is actually a normal resource collection with two extra methods: *create* and *get*.
    """

    def get(self, pk):
        """
        >>> student_collection = entry_point.get_resource(Student)
        >>> existing_student = student_collection.get("john@example.com")
        """
        def _err():
            raise DoesNotExist("Resource with pk %r does not exist." % pk)
        try:
            pk = self._res.UriPolicy.deserialize(pk)
            if not self._res.exists(self._entry_point.user, pk):
                _err()
        except ValidationError, msg:
            raise DoesNotExist("PK validation failed: %s" % msg)
        if not self._res.can_discover(self._entry_point.user, pk):
            _err()
        return ResourceInstance(self._entry_point, self._res, pk)

    def create(self, data, link_data=None):
        """
        >>> student_collection = entry_point.get_resource(Student)
        >>> new_student = student_collection.create({"first_name": "John",
        >>>                                          "last_name": "Smith",
        >>>                                          "email": "foo@bar.com",
        >>>                                          "birthday": "1987-02-21T22:22:22"},
        >>>                                         {"courses": [{"@target": "Maths", "grade": 4},
        >>>                                                      {"@target": "Sports"}]})
        """
        data = self._res.schema.deserialize(data)
        if not self._res.can_create(self._entry_point.user, data):
            raise AuthorizationError("Resource creation is not allowed")
        rval = ResourceInstance(self._entry_point, self._res, None)
        readonly = self._res.schema.find_fields(readonly=True)
        intersection = readonly.intersection(set(data.keys()))
        if intersection:
            raise ValidationError("Readonly fields can not be set: %s" % ", ".join(intersection))
        valid_link_data = rval.links._validate(link_data)
        pk = self._res.UriPolicy.generate_pk(data, link_data)
        if pk is None:  # DAL has to generate PK in the UriPolicy instance didn't
            pk = self._res.create(self._entry_point.user, pk, data)
        else:
            if self._res.exists(self._entry_point.user, pk):
                raise DataConflictError("Resource with PK %r already exists" % pk)
            self._res.create(self._entry_point.user, pk, data)
        rval._set_pk(pk)
        rval.links._set(valid_link_data)
        return rval


class ResourceInstance(ResourceContainer):
    """
    Whenever :class:`creating new or fetching existing <resource_api.resource.RootResourceCollection>` resources
    resource instances are returned. Resource instances are also returned whenever iterating over
    :class:`resource collections <resource_api.resource.ResourceCollection>`.
    """

    def __init__(self, entry_point, resource_interface, pk):
        super(ResourceInstance, self).__init__(entry_point, resource_interface)
        self._pk = pk
        self._links = LinkHolder(entry_point, resource_interface, pk)

    def _set_pk(self, pk):
        """ NOTE: is used only AFTER resource creation """
        self._pk = pk
        self._links._set_pk(pk)

    @property
    def links(self):
        """ Returns a :class:`link holder <resource_api.link.LinkHolder>` """
        return self._links

    @property
    def data(self):
        """ Returns data associated with the resource

        >>> student.data
        {"first_name": "John", "last_name": "Smith", "email": "foo@bar.com", "birthday": "1987-02-21T22:22:22"}
        """
        saved_data = self._res.get_data(self._entry_point.user, self._pk)
        if not self._res.can_get_data(self._entry_point.user, self._pk, saved_data):
            raise AuthorizationError("Resource fetching is not allowed")
        return saved_data

    @property
    def pk(self):
        """ Returns PK of the resource

        >>> student.pk
        "foo@bar.com"
        """
        return self._pk

    def update(self, data):
        """ Changes specified fields of the resource

        >>> student.update({"first_name": "Looper"})
        >>> student.data
        {"first_name": "Looper", "last_name": "Smith", "email": "foo@bar.com", "birthday": "1987-02-21T22:22:22"}
        """
        data = self._res.schema.deserialize(data, validate_required_constraint=False)
        if not self._res.can_update(self._entry_point.user, self._pk, data):
            raise AuthorizationError("Resource updating is not allowed")
        unchangeable = self._res.schema.find_fields(readonly=True, changeable=False)
        intersection = unchangeable.intersection(set(data.keys()))
        if intersection:
            raise ValidationError("Unchangeable fields: %s" % ", ".join(intersection))
        self._res.update(self._entry_point.user, self._pk, data)

    def delete(self):
        """ Removes the resource

        >>> student.delete()
        >>> student.data
        ...
        DoesNotExist: ...
        """
        if not self._res.can_delete(self._entry_point.user, self._pk):
            raise AuthorizationError("Resource deletion is not allowed")
        self.links._clear()
        self._res.delete(self._entry_point.user, self._pk)

    def serialize(self):
        return self._res.schema.serialize(self.data)

    def serialize_pk(self):
        return self._res.UriPolicy.serialize(self.pk)
