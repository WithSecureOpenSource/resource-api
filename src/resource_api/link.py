"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from .errors import(
    DoesNotExist, Forbidden, ValidationError, MultipleFound, FrameworkError, AuthorizationError, DataConflictError)
from .interfaces import Link as BaseLink


class LinkHolder(object):
    """ Accessor for all the links associated with the resource

    For link with cardinality "MANY" :class:`RootLinkCollection <resource_api.link.RootLinkCollection>` is returned:

    >>> student.links.courses
    <RootLinkCollection object>

    For link with cardinality "ONE" :class:`LinkToOne <resource_api.link.LinkToOne>` is returned:

    >>> course.links.teacher
    <LinkToOne object>
    """

    def __init__(self, entry_point, resource_instance, pk):
        self._entry_point = entry_point
        self._res = resource_instance
        self._pk = pk

    def __getattr__(self, name):
        if not hasattr(self._res.links, name):
            raise DoesNotExist("Link %r is not defined" % name)
        forward_link_instance = getattr(self._res.links, name)
        target_collection = self._entry_point.get_resource_by_name(forward_link_instance.target)
        if forward_link_instance.cardinality == BaseLink.cardinalities.ONE:
            return LinkToOne(target_collection, forward_link_instance, forward_link_instance.related_link, self._pk)
        else:
            return RootLinkCollection(target_collection, forward_link_instance, forward_link_instance.related_link,
                                      self._pk)

    def _set_pk(self, pk):
        self._pk = pk

    def _clear(self):
        """ Removes all the outgoing links of the resource """
        for name, _ in self._res.iter_links():
            getattr(self, name)._clear()

    def _validate(self, links_data):
        required_links = set([link_name for link_name, link in self._res.iter_links() if link.required])
        links_data = links_data or {}
        if not isinstance(links_data, dict):
            raise ValidationError("Links' data must be a dict")
        missing_fields = list(required_links.difference(set(links_data.keys())))
        if missing_fields:
            raise ValidationError("Required links are missing: %s" % ", ".join(missing_fields))
        valid_links_data = {}
        for name, link_data in links_data.iteritems():
            try:
                valid_links_data[name] = getattr(self, name)._validate(link_data)
            except FrameworkError, msg:
                raise ValidationError("@Link %s: %s" % (name, msg))
        return valid_links_data

    def _set(self, links_data):
        for name, link_data in links_data.iteritems():
            getattr(self, name)._set(link_data)


class Link(object):

    def __init__(self, target_collection, forward_link_instance, backward_link_instance,
                 source_pk):
        self._entry_point = target_collection._entry_point
        self._target_collection = target_collection
        self._forward_link_instance = forward_link_instance
        self._backward_link_instance = backward_link_instance
        self._source_pk = source_pk

    @classmethod
    def _validate_readonly(cls, forward_link_instance, backward_link_instance):
        msg = "The link is readonly"
        if forward_link_instance.readonly:
            raise Forbidden("%s (forward link is readonly)" % msg)
        if not forward_link_instance.one_way and backward_link_instance.readonly:
            raise Forbidden("%s (backward link is readonly)" % msg)

    def _validate_changability(self, operation, msg=None):
        self._validate_readonly(self._forward_link_instance, self._backward_link_instance)
        msg = msg or "It is not allowed to %s unchangeable links" % operation
        if not self._forward_link_instance.changeable:
            raise Forbidden("%s (forward link is unchangeable)" % msg)
        if not self._forward_link_instance.one_way and not self._backward_link_instance.changeable:
            raise Forbidden("%s (backward link is unchangeable)" % msg)


class LinkInstance(Link):
    """
    Whenever :class:`creating new or fetching existing <resource_api.link.RootLinkCollection>` links
    link instances are returned. Link instances are also returned whenever iterating over
    :class:`link collections <resource_api.link.LinkCollection>`.
    """

    def __init__(self, target_collection, forward_link_instance, backward_link_instance,
                 source_pk, target_pk):
        super(LinkInstance, self).__init__(target_collection, forward_link_instance, backward_link_instance,
                                           source_pk)
        self._target_pk = target_pk

    @classmethod
    def _validate(cls, target_collection, forward_link_instance, backward_link_instance, source_pk, link_data,
                  validate_conflict=True):

        cls._validate_readonly(forward_link_instance, backward_link_instance)

        if backward_link_instance and backward_link_instance.cardinality == BaseLink.cardinalities.ONE and \
           forward_link_instance.cardinality == BaseLink.cardinalities.MANY:
            # NOTE: the reason why it is prohibitied is because it is unclear what to do if the item is added
            # to a reverse linkage from several resources at the same time. Store the latest link? Or the first one?
            raise Forbidden("It is forbiddened to create one to many links. Try creating from another end of the "
                            "relationship")

        if not isinstance(link_data, dict):
            raise ValidationError("Link data must be a dict")
        if "@target" not in link_data:
            raise ValidationError("Target is not defined")

        link_data = dict(link_data)
        target_pk = link_data.pop("@target")

        try:
            target_collection.get(target_pk)
        except DoesNotExist, msg:
            raise ValidationError("Target: %s" % msg)

        # we need to perform authorization and validation against the master link

        def do(inst, src_pk, trg_pk):
            if not inst.can_create(target_collection._entry_point.user, src_pk, trg_pk, link_data):
                raise AuthorizationError("Linking is not allowed")
            if inst.exists(target_collection._entry_point.user, src_pk, trg_pk) and validate_conflict:
                raise DataConflictError("Link already exists")
            rval = inst.schema.deserialize(link_data)
            readonly = inst.schema.find_fields(readonly=True)
            intersection = readonly.intersection(set(rval.keys()))
            if intersection:
                raise ValidationError("Readonly fields can not be set: %s" % ", ".join(intersection))
            rval["@target"] = target_pk
            return rval

        if forward_link_instance.master:
            return do(forward_link_instance, source_pk, target_pk)
        else:
            return do(backward_link_instance, target_pk, source_pk)

    @classmethod
    def _create(cls, target_collection, forward_link_instance, backward_link_instance, source_pk, link_data):
        target_pk = link_data.pop("@target")
        lnk = LinkInstance(target_collection, forward_link_instance, backward_link_instance, source_pk, target_pk)
        lnk._set(link_data)
        return lnk

    def _set(self, link_data):

        # we need to store link data only once - in master link

        def do(master, slave, source_pk, target_pk):
            master.create(self._entry_point.user, source_pk, target_pk, link_data)
            if slave:
                slave.create(self._entry_point.user, target_pk, source_pk, None)

        if self._forward_link_instance.master:
            do(self._forward_link_instance, self._backward_link_instance, self._source_pk, self._target_pk)
        else:
            do(self._backward_link_instance, self._forward_link_instance, self._target_pk, self._source_pk)

    def _delete(self):
        self._forward_link_instance.delete(self._entry_point.user, self._source_pk, self._target_pk)
        if self._backward_link_instance:
            self._backward_link_instance.delete(self._entry_point.user, self._target_pk, self._source_pk)

    @property
    def target(self):
        """
        Returns a :class:`ResourceInstance <resource_api.resource.ResourceInstance>` associated with target
        resource.

        >>> link.target.pk
        "Maths"
        """
        return self._target_collection._get(self._target_pk)

    @property
    def data(self):
        """ Returns data associated with the link

        >>> link.data
        {"grade": 3}
        """

        # we need to fetch data from the master link
        # we need to perform authorization against the master link

        def do(inst, source_pk, target_pk):
            saved_data = inst.get_data(self._entry_point.user, source_pk, target_pk)
            if self._forward_link_instance.can_get_data(self._entry_point.user, source_pk, target_pk, saved_data):
                return saved_data
            raise AuthorizationError("Fetching link's data is not allowed")

        if self._forward_link_instance.master:
            return do(self._forward_link_instance, self._source_pk, self._target_pk)
        else:
            return do(self._backward_link_instance, self._target_pk, self._source_pk)

    def delete(self):
        """ Removes the link

        >>> link.delete()
        >>> link.data
        ...
        DoesNotExist: ...
        """

        self._validate_changability("delete")

        forward_link_required = self._forward_link_instance.required and \
                                self._forward_link_instance.cardinality == BaseLink.cardinalities.ONE  # noqa

        if self._forward_link_instance.one_way:
            backward_link_required = False
        else:
            backward_link_required = self._backward_link_instance.required and \
                                     self._backward_link_instance.cardinality == BaseLink.cardinalities.ONE  # noqa

        if forward_link_required or backward_link_required:
            raise Forbidden("It is forbidden to remove required links")

        # we need to perform authorization against the master link

        def do(inst, source_pk, target_pk):
            if not inst.can_delete(self._entry_point.user, source_pk, target_pk):
                raise AuthorizationError("Unlinking is not allowed")

        if self._forward_link_instance.master:
            do(self._forward_link_instance, self._source_pk, self._target_pk)
        else:
            do(self._backward_link_instance, self._target_pk, self._source_pk)

        self._delete()

    def update(self, data):
        """ Changes specified fields of the link

        >>> link.update({"grade": 4})
        >>> link.data
        {"grade": 4}

        *NOTE*: CANNOT be used to change *@target*
        """
        # we need to perform authorization, validation and storage of data against the master link only

        def do(inst, source_pk, target_pk):
            validated = inst.schema.deserialize(data, validate_required_constraint=False)
            unchangeable = inst.schema.find_fields(readonly=True, changeable=False)
            intersection = unchangeable.intersection(set(validated.keys()))
            if intersection:
                raise ValidationError("Unchangeable fields: %s" % ", ".join(intersection))
            if not inst.can_update(self._entry_point.user, source_pk, target_pk, validated):
                raise AuthorizationError("Link data update is not allowed")
            inst.update(self._entry_point.user, source_pk, target_pk, validated)

        self._validate_changability("update")

        if self._forward_link_instance.master:
            do(self._forward_link_instance, self._source_pk, self._target_pk)
        else:
            do(self._backward_link_instance, self._target_pk, self._source_pk)

    def serialize(self):
        if self._forward_link_instance.master:
            return self._forward_link_instance.schema.serialize(self.data)
        else:
            return self._backward_link_instance.schema.serialize(self.data)


class LinkToOne(Link):
    """ Represents a relationship with cardinality ONE """

    def _get_item(self):
        pks = self._forward_link_instance.get_uris(self._entry_point.user, self._source_pk)
        if len(pks) == 1:
            rel_pk = pks[0]
            if not self._forward_link_instance.can_discover(self._entry_point.user, self._source_pk, rel_pk):
                return None
            if not self._target_collection._res.can_discover(self._entry_point.user, rel_pk):
                return None
            return LinkInstance(self._target_collection, self._forward_link_instance, self._backward_link_instance,
                                self._source_pk, rel_pk)
        elif len(pks) == 0:
            return None
        else:
            raise MultipleFound("Several instances of a link with cardinality ONE were found")

    def _clear(self):
        the_item = self._get_item()
        if the_item is not None:
            if self._backward_link_instance.required and \
               self._backward_link_instance.cardinality == BaseLink.cardinalities.ONE:
                self._target_collection._res.delete(self._entry_point.user, the_item._target_pk)
            the_item._delete()

    def _validate(self, data):
        return LinkInstance._validate(self._target_collection, self._forward_link_instance,
                                      self._backward_link_instance, self._source_pk, data, False)

    def _set(self, data):
        LinkInstance._create(self._target_collection, self._forward_link_instance, self._backward_link_instance,
                             self._source_pk, data)

    @property
    def item(self):
        """
        Returns `LinkInstance <resource_api.link.LinkInstance>`_ if it exists, raises
        `DoesNotExist <resource_api.errors.DoesNotExist>`_ error otherwise

        >>> course.links.teacher.item.delete()
        >>> course.links.teacher.item
        ...
        DoesNotExist ...
        """
        the_item = self._get_item()
        if the_item is None:
            raise DoesNotExist("Link to one does not exist")
        return the_item

    def set(self, data):
        """ Does the same thing as :meth:`update <resource_api.link.LinkInstance.update>` method but CAN change the
        *@target*

        >>> course.links.teacher.item.target.pk
        "Hades"
        >>> course.links.teacher.set({"@target": "Zeuz"})
        >>> course.links.teacher.item.target.pk
        "Zeus"
        """
        valid_data = self._validate(data)
        the_item = self._get_item()
        self._validate_changability("set")
        if the_item is not None:
            the_item.delete()
        self._set(valid_data)


class LinkCollection(Link):
    """
    The entity that represents a pile of resource links.

    >>> student_courses = student.links.courses

    The collection is iterable:

    >>> for link in student_courses:
    >>>    ...

    If :meth:`Link.get_uris <resource_api.interfaces.Link.get_uris>` is implemented to return an
    indexable entity the collection elements can be accessed by index as well:

    >>> link = student_courses[15]
    """

    def __init__(self, target_collection, forward_link_instance, backward_link_instance, source_pk, params=None):
        super(LinkCollection, self).__init__(target_collection, forward_link_instance, backward_link_instance,
                                             source_pk)
        self._params = params or {}
        self._items = self._iter_items = None

    def _get(self, target_pk):
        if not self._forward_link_instance.can_discover(self._entry_point.user, self._source_pk, target_pk):
            return None
        if not self._target_collection._res.can_discover(self._entry_point.user, target_pk):
            return None
        return LinkInstance(self._target_collection, self._forward_link_instance, self._backward_link_instance,
                            self._source_pk, target_pk)

    def __iter__(self):
        if self._items is None:
            if not self._forward_link_instance.can_get_uris(self._entry_point.user, self._source_pk):
                raise AuthorizationError("Fetching link collection is not allowed")
            params = self._forward_link_instance.query_schema.deserialize(self._params, with_errors=False,
                                                                          validate_required_constraint=False)
            self._items = self._forward_link_instance.get_uris(self._entry_point.user, self._source_pk, params)
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

        >>> student_courses = student.links.courses
        >>> new_link_collection = student_courses.filter(grade__gte=3)
        """
        new_params = {}
        new_params.update(self._params)
        if params:
            new_params.update(params)
        return LinkCollection(self._target_collection, self._forward_link_instance, self._backward_link_instance,
                              self._source_pk, new_params)

    def count(self):
        """ Returns count of all items within the system that satisfy filtering criterias.

        NOTE: :code:`len(collection)` is supposed to return the same result as :code:`collection.count()`. The key
        difference between them is that :code:`len` needs to fetch all items in the collection meanwhile
        :code:`collection.count()` relies on
        :meth:`Link.get_count <resource_api.interfaces.Link.get_count>`

        >>> len(student_courses)
        4569
        >>> student_courses.count()
        4569
        """
        if not self._forward_link_instance.can_get_uris(self._entry_point.user, self._source_pk):
            raise AuthorizationError("Fetching link collection count is not allowed")
        params = self._forward_link_instance.query_schema.deserialize(self._params, with_errors=False,
                                                                      validate_required_constraint=False)
        return self._forward_link_instance.get_count(self._entry_point.user, self._source_pk, params)

    def serialize(self):
        rval = []
        for item in self:
            rval.append(item.target.serialize_pk())
        return rval


class RootLinkCollection(LinkCollection):
    """
    Root link collection is actually a normal link collection with two extra methods: *create* and *get*.
    """

    def _clear(self):
        for lnk in self:
            if self._backward_link_instance.required and \
               self._backward_link_instance.cardinality == BaseLink.cardinalities.ONE:
                self._target_collection._res.delete(self._entry_point.user, lnk._target_pk)
            lnk._delete()

    def _validate_item(self, link_data):
        return LinkInstance._validate(self._target_collection, self._forward_link_instance,
                                      self._backward_link_instance, self._source_pk, link_data)

    def _create_item(self, link_data):
        return LinkInstance._create(self._target_collection, self._forward_link_instance,
                                    self._backward_link_instance, self._source_pk, link_data)

    def _validate(self, links_data):
        if not isinstance(links_data, list):
            raise ValidationError("Links must be passed as a list of dicts")
        count = 0
        valid_links_data = []
        try:
            for link_data in links_data:
                valid_links_data.append(self._validate_item(link_data))
                count += 1
        except FrameworkError, msg:
            raise ValidationError("@Element %d: %s" % (count, msg))
        return valid_links_data

    def _set(self, links_data):
        for link_data in links_data:
            self._create_item(link_data)

    def get(self, target_pk):
        """
        target_pk
            PK of target resource instance

        >>> student_courses = student.links.courses
        >>> exisiting_link_to_course = student_courses.get("Biology")
        """
        target = self._target_collection.get(target_pk)
        target_pk = target.pk
        if not self._forward_link_instance.exists(self._entry_point.user, self._source_pk, target_pk):
            raise DoesNotExist("Link does not exist")
        rval = self._get(target_pk)
        if rval is None:
            raise DoesNotExist("Link does not exist")
        return rval

    def create(self, data):
        """
        data (dict)
            has to have at least one key called **@target** - its value must be a PK of target resource instance

        >>> student_courses = student.links.courses
        >>> new_link_to_course = student_courses.create({"@target": "Maths"})
        """
        valid_data = self._validate_item(data)
        self._validate_changability(None, "It is not allowed to create links in unchangeable collections")
        return self._create_item(valid_data)
