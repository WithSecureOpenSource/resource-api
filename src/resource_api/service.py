"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from abc import ABCMeta, abstractmethod

from .resource import RootResourceCollection
from .errors import DeclarationError, ResourceDeclarationError, DoesNotExist


class EntryPoint(object):
    """ Represents user specific means of access to object interface. """

    def __init__(self, service, user):
        self._service = service
        self._user = user

    @property
    def user(self):
        """ User object returned by :meth:`Service._get_user <resource_api.service.Service._get_user>` method """
        return self._user

    def _check_ready(self):
        if not self._service._ready:
            raise DeclarationError("service's setup method was not called")

    def get_resource_by_name(self, resource_name):
        """
        resource_name (string)
            namespace + "." + resource_name, where namespace can be a custom namespace or resource's module name

        >>> entry_point.get_resource_by_name("school.Student")
        <RootResourceCollection object>
        >>> entry_point.get_resource_by_name("com.example.module.education.Student")
        <RootResourceCollection object>
        """
        self._check_ready()
        if resource_name in self._service._resources:
            res = self._service._resources[resource_name]
        elif resource_name in self._service._resources_py:
            res = self._service._resources_py[resource_name]
        else:
            raise DoesNotExist("Resource %s does not exist" % resource_name)
        return RootResourceCollection(self, res)

    def get_resource(self, resource_class):
        """
        resource_class (:class:`Resource <resource_api.interfaces.Resource>` subclass)

        >>> entry_point.get_resource(Student)
        <RootResourceCollection object>
        """
        self._check_ready()
        name = resource_class.get_name()
        if name not in self._service._resources_py:
            raise DoesNotExist("Resource %s does not exist" % name)
        return RootResourceCollection(self, self._service._resources_py[resource_class.get_name()])


class Service(object):
    """ Entity responsible for holding a registry of all resources that are supposed to be exposed

    Service has to be subclassed in order to implement usecase specific *_get_context* and *_get_user* methods.

    NOTE: do not override any of the public methods - it may cause framework's misbehavior.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self._resources = {}
        self._resources_py = {}
        self._python_to_human = {}
        self._ready = False

    @abstractmethod
    def _get_context(self):
        """ MUST BE OVERRIDEN IN A SUBCLASS

        Must return an object holding all database connections, sockets etc. It is later on passed to all individual
        resources.
        """

    @abstractmethod
    def _get_user(self, data):
        """ MUST BE OVERRIDEN IN A SUBCLASS

        Must return an object representing currently authenticated user. It is later on passed to individual *can_??*
        methods of various resources for authorization purposes.
        """

    def _connect_links(self, inst):
        for field_name, field in inst.iter_links():
            cls = inst.__class__
            link_field = getattr(inst.links, field_name)
            if field.target not in self._resources_py:
                raise ResourceDeclarationError(field, "target resource %r is not registered" % field.target)
            target = self._resources_py[link_field.target]

            if field.one_way:
                continue

            related_link = getattr(target.links, field.related_name, None)

            if related_link is None:
                raise ResourceDeclarationError(cls, "Unable to link %s:%s to %s:%s. Related link undefiend." %
                                               (field.source, field.name, field.target, field.related_name))

            if link_field.related_link:  # prevent connecting the links twice
                continue

            link_field.related_link = related_link
            related_link.related_link = link_field

            # check master/slave link relationship

            if not field.master and not related_link.master:
                raise ResourceDeclarationError(cls, "this or related link must be a master one")
            if field.master and related_link.master:
                raise ResourceDeclarationError(cls, "this and related link cannot be master ones at the same time")

    def register(self, resource, name=None):
        """ Add resource to the registry

        resource (:class:`Resource <resource_api.interfaces.Resource>` subclass)
            entity to be added to the registry
        name (string)
            string to be used for resource registration, by default it is resource's module name + class name with "."
            as a delimiter
        """
        name = name or resource.get_name()
        self._python_to_human[resource.get_name()] = name
        self._resources[name] = self._resources_py[resource.get_name()] = resource(self._get_context())

    def setup(self):
        """ Finalizes resource registration.

        MUST be called after all desired resources are registered.
        """
        if self._ready:
            return
        for inst in self._resources_py.values():
            for field_name, field in inst.iter_links():
                setattr(inst.links, field_name, field(self._get_context()))
        for inst in self._resources_py.values():
            self._connect_links(inst)
        self._ready = True

    def get_schema(self, human=True):
        """ Returns schema for all registered resources.

        human (bool = True)
            if True it returns schema with namespaces used during registration
            if False it returns schema with resource module names as namespaces
        """
        rval = dict([(name, res.get_schema()) for name, res in self._resources_py.iteritems()])
        if not human:
            return rval
        new_rval = {}
        for key, value in rval.iteritems():
            for link_val in value.get("links", {}).itervalues():
                link_val["target"] = self._python_to_human[link_val["target"]]
            new_rval[self._python_to_human[key]] = value
        return new_rval

    def get_entry_point(self, data):
        """ Returns :class:`entry point <resource_api.service.EntryPoint>`

        data
            intormation to be used to construct user object via *_get_user* method
        """
        return EntryPoint(self, self._get_user(data))
