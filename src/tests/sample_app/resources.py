"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from resource_api import schema

from ..simulators import TestResource, TestLink


PERMS = {
    "create": True,
    "update": True,
    "delete": True,
    "discover": True,
    "list": True,
    "view": True
}

ACLS = {
    "source": PERMS,
    "target": PERMS,
    "link": PERMS
}


def create_new_perms(diff):
    rval = {}
    for key, value in ACLS.iteritems():
        rval[key] = dict(value)
    for key, value in diff.iteritems():
        if key in ["source", "target", "link"]:
            rval[key].update(value)
    return rval


class BaseExampleResource(TestResource):

    class Schema:
        pk = schema.IntegerField(pk=True)
        extra = schema.StringField(required=False)
        more_data = schema.StringField(required=False)

    def _extract_perms(self, user):
        raise NotImplementedError

    def can_get_data(self, user, pk, saved_data):
        return self._extract_perms(user)["view"]

    def can_delete(self, user, pk):
        return self._extract_perms(user)["delete"]

    def can_create(self, user, data):
        return self._extract_perms(user)["create"]

    def can_update(self, user, pk, data):
        return self._extract_perms(user)["update"]

    def can_get_uris(self, user):
        return self._extract_perms(user)["list"]

    def can_discover(self, user, pk):
        return self._extract_perms(user)["discover"]


class BaseExampleLink(TestLink):

    def _extract_perms(self, user):
        return create_new_perms(user)["link"]

    def can_get_data(self, user, pk, rel_pk, saved_data):
        return self._extract_perms(user)["view"]

    def can_delete(self, user, pk, rel_pk):
        return self._extract_perms(user)["delete"]

    def can_create(self, user, pk, rel_pk, data=None):
        return self._extract_perms(user)["create"]

    def can_update(self, user, pk, rel_pk, data):
        return self._extract_perms(user)["update"]

    def can_get_uris(self, user, pk):
        return self._extract_perms(user)["list"]

    def can_discover(self, user, pk, rel_pk):
        return self._extract_perms(user)["discover"]


class LinkSchema:
    extra = schema.StringField(required=False)
    more_data = schema.StringField(required=False)


class LinkQuerySchema:
    query_param = schema.StringField()


class Target(BaseExampleResource):
    """ Target Foo """

    class QuerySchema:
        query_param = schema.StringField()

    def _extract_perms(self, user):
        return create_new_perms(user)["target"]

    class Links:

        non_link_field = True

        class sources(BaseExampleLink):
            "Link to many sources"
            QuerySchema = LinkQuerySchema
            target = "Source"
            related_name = "targets"

        class the_sources(BaseExampleLink):
            "Link to many sources as well"
            target = "Source"
            related_name = "the_target"

        class one_to_one_source(BaseExampleLink):
            "Link to just one source"
            cardinality = TestLink.cardinalities.ONE
            target = "Source"
            related_name = "one_to_one_target"


class Source(BaseExampleResource):
    """ Source Bar """

    class QuerySchema:
        query_param = schema.StringField()

    class Meta:
        is_bar = False

    class Links:

        class targets(BaseExampleLink):
            "Link to many targets"
            Schema = LinkSchema
            QuerySchema = LinkQuerySchema
            target = "Target"
            related_name = "sources"
            master = True

            class Meta:
                hoster = "Nope"

        class the_target(BaseExampleLink):
            "Link to just one target"
            Schema = LinkSchema
            target = "Target"
            related_name = "the_sources"
            cardinality = TestLink.cardinalities.ONE
            master = True

        class one_to_one_target(BaseExampleLink):
            "Another link to just one target"
            Schema = LinkSchema
            target = "Target"
            related_name = "one_to_one_source"
            cardinality = TestLink.cardinalities.ONE
            master = True

    def _extract_perms(self, user):
        return create_new_perms(user)["source"]
