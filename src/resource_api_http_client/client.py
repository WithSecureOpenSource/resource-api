"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from resource_api.errors import DoesNotExist

from .transport import HttpClient, JsonClient


class Client(object):
    """ Client side entry point.

    It can be instanciated the following way with a URL of the HTTP service and authentication headers as parameters:

    >>> client = Client.create(base_url="http://example.com/api",
                               auth_headers={"auth_token": "foo-bar-17"})
    """

    @classmethod
    def create(cls, base_url, auth_headers=None):
        """ Instanciates the client

        base_url (string)
            URL of Resource API server (e.g.: "http://example.com/api")
        auth_headers (dict || None)
            Dictionary with fields that are later on used to
            `construct user object <resource_api.service.Service_get_user>`
        """
        http_client = HttpClient(auth_headers=auth_headers)
        transport_client = JsonClient(http_client)
        return cls(base_url, transport_client)

    def __init__(self, base_url, transport_client):
        """
        base_url (string)
            URL of Resource API server (e.g.: "http://example.com/api")
        transport_client
            instance of a class that must have one method with the following signature
            open(self, url, method="GET", query_string=None, data=None, schema=None)
        """
        self._transport_client = transport_client
        self._schema = None
        self._base_url = base_url.rstrip("/")

    def _open(self, suffix="", **kwargs):
        if suffix:
            url = self._base_url + "/" + suffix
        else:
            url = self._base_url
        return self._transport_client.open(url, **kwargs)

    @property
    def schema(self):
        """ Contains Resource API schema """
        if not self._schema:
            self._schema = self._open(method="OPTIONS")
        return self._schema

    def get_resource_by_name(self, resource_name):
        """
        resource_name (string)
            E.g.: "school.Student"
        @return
            <RootResourceCollection instance>
        """
        if resource_name not in self.schema:
            raise DoesNotExist("Resource does not exist")
        return RootResourceCollection(self, resource_name)


class ResourceCollection(object):
    """
    The entity that represents a pile of resources.

    >>> student_collection = client.get_resource_by_name("school.Student")

    The collection is iterable:

    >>> for student in student_collection:
    >>>    ...
    """

    def __init__(self, client, name, params=None):
        self._client = client
        self._name = name
        self._base_url = name
        self._params = params or {}
        self._items = self._iter_items = None

    def filter(self, params=None):
        """
        Filtering options can be applied to collections to return new collections that contain a subset of original
        items:

        *NOTE*: filtering operations applied to root collections return normal collections

        >>> student_collection = client.get_resource_by_name("school.Student")
        >>> new_collection = student_collection.filter(params={"name__startswith": "Abr"})
        """
        new_params = {}
        new_params.update(self._params)
        if params:
            new_params.update(params)
        return ResourceCollection(self._client, self._name, new_params)

    def __iter__(self):
        if self._items is None:
            self._items = self._client._open(self._base_url, params=self._params)
            self._iter_items = iter(self._items)
        return self

    def __getitem__(self, key):
        self.__iter__()
        pk = self._items[key]
        return self._get(pk)

    def __len__(self):
        self.__iter__()
        return len(self._items)

    def _get(self, pk):
        if pk is None:
            return None
        else:
            return ResourceInstance(self._client, self._name, pk)

    def count(self):
        """ Returns count of all items within the system that satisfy filtering criterias.

        NOTE: :code:`len(collection)` is supposed to return the same result as :code:`collection.count()`. The key
        difference between them is that :code:`len` needs to fetch all items in the collection meanwhile
        :code:`collection.count()` relies on **/<ResourceName>:count** URL

        >>> len(student_collection)
        4569
        >>> student_collection.count()
        4569
        """
        return self._client._open(self._base_url + ":count", params=self._params)

    def next(self):
        return self._get(self._iter_items.next())


class RootResourceCollection(ResourceCollection):
    """
    Root resource collection is actually a normal resource collection with two extra methods: *create* and *get*.
    """

    def get(self, pk):
        """
        >>> student_collection = client.get_resource_by_name("school.Student")
        >>> existing_student = student_collection.get("john@example.com")
        """
        self._client._open(self._base_url + "/" + str(pk), method="HEAD")
        return ResourceInstance(self._client, self._name, pk)

    def create(self, data, link_data=None):
        """
        >>> student_collection = client.get_resource_by_name("school.Student")
        >>> new_student = student_collection.create({"first_name": "John", "last_name": "Smith", "email": "foo@bar.com",
        >>>                                          "birthday": "1987-02-21T22:22:22"})
        """
        pk = self._client._open(self._name, method="POST", data=data)
        return ResourceInstance(self._client, self._name, pk, data)


class ResourceInstance(object):
    """
    Whenever :class:`creating new or fetching existing <resource_api_http_client.client.RootResourceCollection>`
    resources resource instances are returned. Resource instances are also returned whenever iterating over
    :class:`resource collections <resource_api_http_client.client.ResourceCollection>`.
    """

    def __init__(self, client, name, pk, data=None):
        self._client = client
        self._name = name
        self._pk = pk
        self._links = None
        self._data = data
        self._url = self._name + "/" + str(self._pk)

    @property
    def pk(self):
        """ Returns PK of the resource

        >>> student.pk
        "foo@bar.com"
        """
        return self._pk

    @property
    def links(self):
        """ Returns a :class:`link holder <resource_api_http_client.client.LinkHolder>` """
        if self._links is None:
            self._links = LinkHolder(self._client, self._url, self._client.schema[self._name].get("links", {}))
        return self._links

    @property
    def data(self):
        """ Returns data associated with the resource

        >>> student.data
        {"first_name": "John", "last_name": "Smith", "email": "foo@bar.com", "birthday": "1987-02-21T22:22:22"}
        """
        if self._data is None:
            self._data = self._client._open(self._url, schema=self._client.schema[self._name]["schema"])
        return self._data

    def update(self, data):
        """ Changes specified fields of the resource

        >>> student.update({"first_name": "Looper"})
        >>> student.data
        {"first_name": "Looper", "last_name": "Smith", "email": "foo@bar.com", "birthday": "1987-02-21T22:22:22"}
        """
        self._client._open(self._url, method="PATCH", data=data)
        self._data = None

    def delete(self):
        """ Removes the resource

        >>> student.delete()
        >>> student.data
        ...
        DoesNotExist: ...
        """
        self._client._open(self._url, method="DELETE")
        self._data = None


class LinkHolder(object):
    """ Accessor for all the links associated with the resource

    For link with cardinality "MANY" :class:`RootLinkCollection <resource_api_http_client.client.RootLinkCollection>`
    is returned:

    >>> student.links.courses
    <RootLinkCollection object>

    For link with cardinality "ONE" :class:`LinkToOne <resource_api_http_client.client.LinkToOne>` is returned:

    >>> course.links.teacher
    <LinkToOne object>
    """

    def __init__(self, client, url, schema):
        self._client = client
        self._url = url
        self._schema = schema

    def __getattr__(self, link_name):
        link = self._schema.get(link_name)
        if link is None:
            raise DoesNotExist("Link does not exist")
        target_name = self._schema[link_name]["target"]
        if link.get("cardinality", "MANY") == "ONE":
            return LinkToOne(self._client, self._url, target_name, link_name)
        else:
            return RootLinkCollection(self._client, self._url, target_name, link_name)


class LinkInstance(object):
    """
    Whenever :class:`creating new or fetching existing <resource_api_http_client.client.RootLinkCollection>` links
    link instances are returned. Link instances are also returned whenever iterating over
    :class:`link collections <resource_api_http_client.client.LinkCollection>`.
    """

    def __init__(self, client, base_url, target_name, target_pk, data=None, unique=False):
        self._client = client
        self._target_name = target_name
        self._target_pk = target_pk
        self._data = data
        self._url = base_url
        if unique:
            self._url += "/item"
        else:
            self._url += "/" + str(target_pk)

    def update(self, data):
        self._client._open(self._url, method="PATCH", data=data)
        self._data = None

    @property
    def target(self):
        """
        Returns a :class:`ResourceInstance <resource_api_http_client.client.ResourceInstance>` associated with target
        resource.

        >>> link.target.pk
        "Maths"
        """
        return ResourceInstance(self._client, self._target_name, self._target_pk)

    @property
    def data(self):
        """ Returns data associated with the link

        >>> link.data
        {"grade": 3}
        """
        if self._data is None:
            parts = self._url.split("/")
            link_name, resource_name = parts[-2], parts[-4]
            schema = self._client.schema[resource_name]["links"][link_name]["schema"]
            self._data = self._client._open(self._url + ":data", method="GET", schema=schema)
        return self._data

    def delete(self):
        """ Removes the link

        >>> link.delete()
        >>> link.data
        ...
        DoesNotExist: ...
        """
        self._client._open(self._url, method="DELETE")
        self._data = None


class LinkToOne(object):
    """ Represents a relationship with cardinality ONE """

    def __init__(self, client, base_url, target_name, name):
        self._client = client
        self._target_name = target_name
        self._target_pk = None
        self._url = base_url + "/" + name

    def _get_target_pk(self):
        if self._target_pk is None:
            self._target_pk = self._client._open(self._url + "/item", method="GET")
        return self._target_pk

    def set(self, data):
        """ Does the same thing as :meth:`update <resource_api_http_client.client.LinkInstance.update>` method but CAN
        change the *@target*

        >>> course.links.teacher.item.target.pk
        "Hades"
        >>> course.links.teacher.set({"@target": "Zeuz"})
        >>> course.links.teacher.item.target.pk
        "Zeus"
        """
        self._client._open(self._url, method="PUT", data=data)
        self._target_pk = data["@target"]

    @property
    def item(self):
        """
        Returns `LinkInstance <resource_api_http_client.client.LinkInstance>`_ if it exists, raises
        `DoesNotExist <resource_api.errors.DoesNotExist>`_ error otherwise

        >>> course.links.teacher.item.delete()
        >>> course.links.teacher.item
        ...
        DoesNotExist ...
        """
        return LinkInstance(self._client, self._url, self._target_name, self._get_target_pk(), unique=True)


class LinkCollection(object):
    """
    The entity that represents a pile of resource links.

    >>> student_courses = student.links.courses

    The collection is iterable:

    >>> for link in student_courses:
    >>>    ...

    Accessing items by index is also possible:
    >>> link = student_courses[15]
    """

    def __init__(self, client, base_url, target_name, name, params=None):
        self._client = client
        self._target_name = target_name
        self._target_pk = None
        self._base_url = base_url
        self._name = name
        self._url = base_url + "/" + name
        self._params = params or {}
        self._items = self._iter_items = None

    def filter(self, params=None):
        """
        Filtering options can be applied to collections to return new collections that contain a subset of original
        items:

        *NOTE*: filtering operations applied to root collections return normal collections

        >>> student_courses = student.links.courses
        >>> new_link_collection = student_courses.filter(grade__gte=3)
        """
        new_params = {}
        new_params.update(self._params)
        if params:
            new_params.update(params)
        return LinkCollection(self._client, self._base_url, self._target_name, self._name, new_params)

    def __iter__(self):
        if self._items is None:
            self._items = self._client._open(self._url, params=self._params)
            self._iter_items = iter(self._items)
        return self

    def __getitem__(self, key):
        self.__iter__()
        pk = self._items[key]
        return self._get(pk)

    def __len__(self):
        self.__iter__()
        return len(self._items)

    def _get(self, target_pk):
        if target_pk is None:
            return None
        else:
            return LinkInstance(self._client, self._url, self._target_name, target_pk)

    def count(self):
        """ Returns count of all items within the system that satisfy filtering criterias.

        NOTE: :code:`len(collection)` is supposed to return the same result as :code:`collection.count()`. The key
        difference between them is that :code:`len` needs to fetch all items in the collection meanwhile
        :code:`collection.count()` relies on **/<ResourceName>:count** URL

        >>> len(student_courses)
        4569
        >>> student_courses.count()
        4569
        """
        return self._client._open(self._url + ":count", params=self._params)

    def next(self):
        return self._get(self._iter_items.next())


class RootLinkCollection(LinkCollection):
    """
    Root link collection is actually a normal link collection with two extra methods: *create* and *get*.
    """

    def create(self, data):
        """
        data (dict)
            has to have at least one key called **@target** - its value must be a PK of target resource instance

        >>> student_courses = student.links.courses
        >>> new_link_to_course = student_courses.create({"@target": "Maths"})
        """
        self._client._open(self._url, method="POST", data=data)
        return LinkInstance(self._client, self._url, self._target_name, data["@target"])

    def get(self, target_pk):
        """
        target_pk
            PK of target resource instance

        >>> student_courses = student.links.courses
        >>> exisiting_link_to_course = student_courses.get("Biology")
        """
        self._client._open(self._url + "/" + str(target_pk) + ":data", method="HEAD")
        return LinkInstance(self._client, self._url, self._target_name, target_pk)
