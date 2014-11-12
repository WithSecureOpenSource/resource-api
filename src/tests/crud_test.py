"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import unittest

from resource_api.resource import RootResourceCollection, ResourceCollection
from resource_api.link import RootLinkCollection, LinkCollection
from resource_api import schema
from resource_api.errors import DoesNotExist, ValidationError, DataConflictError, Forbidden, MultipleFound

from .simulators import TestResource, TestService, TestLink
from .sample_app.resources import Target, Source
from .base_test import BaseTest


class RegistryTest(BaseTest):

    def test_get_unknown_resource_by_name(self):
        self.assertRaisesRegexp(DoesNotExist, "Resource foo does not exist", self.entry_point.get_resource_by_name,
                                "foo")

    def test_get_unknown_resource_by_class(self):

        class Bla(Target):
            pass

        self.assertRaisesRegexp(DoesNotExist, "Resource .+ does not exist", self.entry_point.get_resource, Bla)

    def test_get_unknown_link(self):
        self.assertRaisesRegexp(DoesNotExist, "Link 'smafg' is not defined", lambda: self.src.get(1).links.smafg)


class ResourceTest(BaseTest):

    def test_get(self):
        self.assertEqual(self.src.get(1).data, {"pk": 1, "extra": "foo", "more_data": "bla"})

    def test_update(self):
        item = self.src.get(1)
        item.update({"extra": "bar"})
        self.assertEqual(self.src.get(1).data, {"pk": 1, "extra": "bar", "more_data": "bla"})

    def test_filter(self):
        subcol = self.src.filter({"query_param": "Bla", "foo": 666})
        self.assertTrue(isinstance(subcol, ResourceCollection))
        self.assertFalse(isinstance(subcol, RootResourceCollection))
        list(subcol)
        self.assertEqual(self.storage._call_log[-1][2], {"query_param": "Bla"})

    def test_delete(self):
        item = self.src.get(1)
        item.delete()
        self.assertRaises(DoesNotExist, self.src.get, 1)

    def test_create(self):
        self.src.create({"pk": 3, "extra": "foo"})
        self.assertEqual(self.src.get(3).data, {"pk": 3, "extra": "foo"})

    def test_create_readonly_with_required_and_defaults(self):

        class CustomResource(TestResource):

            class Schema:
                name = schema.StringField(pk=True)
                foo = schema.StringField(readonly=True, default="Bla")
                bar = schema.StringField(readonly=True, required=True)

        srv = TestService()
        srv.register(CustomResource)
        srv.setup()
        res = srv.get_entry_point(None).get_resource(CustomResource)
        item = res.create({"name": "woop"})
        self.assertEqual(item.data, {"name": "woop"})

    def test_get_from_iteration(self):
        self.assertEqual(self.src[0].data, {"pk": 1, "extra": "foo", "more_data": "bla"})

    def test_get_non_existent(self):
        self.assertRaisesRegexp(DoesNotExist, "does not exist", self.src.get, 3)

    def test_get_wrong_pk_type(self):
        self.assertRaisesRegexp(DoesNotExist, "PK validation failed", self.src.get, "one")

    def test_create_with_bad_data(self):
        self.assertRaises(ValidationError, self.src.create, {"extra": "foo"})

    def test_update_with_bad_data(self):
        item = self.src.get(1)
        self.assertRaises(ValidationError, item.update, {"foo": 1})

    def test_create_with_existing_pk(self):
        self.assertRaisesRegexp(DataConflictError, "Resource with PK \w{1,2} already exists", self.src.create,
                                {"pk": 1, "extra": "foo"})


class ResourceRelatedLinkTest(BaseTest):

    def test_delete_source(self):
        self.src.get(1).delete()
        links = self.target.get(1).links
        self.assertEqual(len(links.sources), 0)
        self.assertEqual(len(links.the_sources), 0)

    def test_delete_target(self):
        self.target.get(1).delete()
        self.target.get(2).delete()
        links = self.src.get(1).links
        self.assertEqual(len(links.targets), 0)
        self.assertRaises(DoesNotExist, lambda: links.the_target.item.target)

    def test_create_with_links(self):
        self.src.create({"pk": 3}, {
            "targets": [
                {"@target": 1},
                {"@target": 2}
            ],
            "the_target": {"@target": 1}
        })
        src = self.src.get(3)
        self.assertEqual(src.links.the_target.item.target.pk, 1)
        self.assertEqual(len(src.links.targets), 2)

    def test_create_with_links_errors(self):
        self.assertRaisesRegexp(ValidationError, "Links' data must be a dict", self.src.create, {"pk": 3}, "NON DICT")

        def _validate(msg, data):
            self.assertRaisesRegexp(ValidationError, msg, self.src.create, {"pk": 3}, data)

        _validate("@Link the_target: Link data must be a dict", {"the_target": "NON DICT"})
        _validate("@Link the_target: Target: Resource with pk \w{1,2} does not exist.", {"the_target": {"@target": 6}})
        _validate("@Link the_target: Target is not defined", {"the_target": {"foo": "bar"}})
        _validate("@Link targets: Links must be passed as a list of dicts", {"targets": "NON LIST"})
        _validate("@Link targets: @Element 0: Link data must be a dict", {"targets": ["NON DICT"]})
        _validate("@Link targets: @Element 0: Target: Resource with pk \w{1,2} does not exist.",
                  {"targets": [{"@target": 6}]})
        _validate("@Link targets: @Element 0: Target is not defined", {"targets": [{"foo": "bar"}]})


class LinkToManyTest(BaseTest):

    def test_create(self):
        lnk = self.src.get(1).links.targets.create({"@target": 2})
        self.assertEqual(lnk.target.pk, 2)

    def test_get_target(self):
        lnk = self.src.get(1).links.targets.get(1)
        self.assertEqual(lnk.target.pk, 1)

    def test_delete(self):
        self.src.get(1).links.targets[0].delete()
        self.assertEqual(len(self.src.get(1).links.targets), 0)

    def test_update(self):
        self.src.get(1).links.targets[0].update({"extra": "foo"})
        self.assertEqual(self.src.get(1).links.targets[0].data, {"extra": "foo", "more_data": "bla"})

    def test_create_already_existing(self):
        self.assertRaises(DataConflictError, self.src.get(1).links.targets.create, {"@target": 1})

    def test_create_with_bad_data(self):
        self.assertRaises(ValidationError, self.src.get(1).links.targets.create, {"@target": 2, "extra": 1})

    def test_update_with_bad_data(self):
        self.assertRaises(ValidationError, self.src.get(1).links.targets[0].update, {"extra": 1})

    def test_get_from_iteration(self):
        lnk = self.src.get(1).links.targets[0]
        self.assertEqual(lnk.target.pk, 1)

    def test_get_wrong_target_pk_type(self):
        self.assertRaisesRegexp(DoesNotExist, "PK validation failed", self.src.get(1).links.targets.get, "one")

    def test_create_with_wrong_target_pk_type(self):
        self.assertRaisesRegexp(ValidationError, "Target: PK validation failed", self.src.get(1).links.targets.create,
                                {"@target": "one"})

    def test_get_non_existent(self):
        self.assertRaises(DoesNotExist, self.src.get(1).links.targets.get, 2)

    def test_create_with_non_existent_target_pk(self):
        self.assertRaisesRegexp(ValidationError, "Target: Resource with pk \w{1,2} does not exist.",
                                self.src.get(1).links.targets.create, {"@target": 3})

    def test_filter(self):
        subcol = self.src.get(1).links.targets.filter({"query_param": "Bla", "foo": 666})
        self.assertTrue(isinstance(subcol, LinkCollection))
        self.assertFalse(isinstance(subcol, RootLinkCollection))
        list(subcol)
        self.assertEqual(self.storage._call_log[-1][2], {"query_param": "Bla"})


class LinkToManyReverseLinkTest(BaseTest):

    def test_create(self):
        self.src.get(1).links.targets.create({"@target": 2})
        self.assertTrue(self.target.get(2).links.sources.count() == 1)

    def test_delete(self):
        self.src.get(1).links.targets[0].delete()
        self.assertTrue(self.target.get(1).links.sources.count() == 0)

    def test_update(self):
        self.src.get(1).links.targets[0].update({"extra": "foo"})
        self.assertEqual(self.target.get(1).links.sources[0].data, {"extra": "foo", "more_data": "bla"})

    def test_create_related(self):
        self.target.get(1).links.sources.create({"@target": 2})
        self.assertTrue(self.src.get(2).links.targets.count() == 1)

    def test_delete_related(self):
        self.target.get(1).links.sources[0].delete()
        self.assertTrue(self.src.get(1).links.targets.count() == 0)

    def test_update_related(self):
        self.target.get(1).links.sources[0].update({"extra": "foo"})
        self.assertEqual(self.src.get(1).links.targets[0].data, {"extra": "foo", "more_data": "bla"})


class LinkToOneTest(BaseTest):

    @property
    def lnk(self):
        return self.entry_point.get_resource(Source).get(1).links.the_target

    def test_set(self):
        self.lnk.set({"@target": 1})
        self.assertEqual(self.lnk.item.target.pk, 1)

    def test_set_with_bad_data(self):
        self.assertRaises(ValidationError, self.lnk.set, {"@target": 1, "extra": 1})

    def test_set_with_wrong_target_pk_type(self):
        self.assertRaises(ValidationError, self.lnk.set, {"@target": "one"})

    def test_set_with_non_existent_target_pk(self):
        self.assertRaises(ValidationError, self.lnk.set, {"@target": 3})

    def test_set_without_target_pk(self):
        self.assertRaises(ValidationError, self.lnk.set, {"extra": "Fooo"})

    def test_get_target(self):
        self.assertEqual(self.lnk.item.target.pk, 2)

    def test_get_data(self):
        self.assertEqual(self.lnk.item.data, {"extra": "foo", "more_data": "bla"})

    def test_clear(self):
        self.lnk.item.delete()
        self.assertRaises(DoesNotExist, lambda: self.lnk.item.target)

    def test_multiple_found(self):
        # This case should not happen in real life as long as nobody touches data directly
        src = self.srv._resources_py[Source.get_name()]
        self.storage.set((1, src.links.the_target.get_name()), 1, {"extra": "foo", "more_data": "bla"})
        self.assertRaises(MultipleFound, lambda: self.src.get(1).links.the_target.item)


class LinkToOneReverseLinkTest(BaseTest):

    def test_create(self):

        _len = lambda pk: len(self.target.get(pk).links.the_sources)

        self.assertEqual(_len(1), 0)
        self.assertEqual(_len(2), 1)
        self.src.get(1).links.the_target.set({"@target": 1})
        self.assertEqual(_len(1), 1)
        self.assertEqual(_len(2), 0)

    def test_update(self):
        self.src.get(1).links.the_target.set({"@target": 1, "extra": "sss"})
        self.assertEqual(self.target.get(1).links.the_sources[0].data, {"extra": "sss"})

    def test_create_related_error(self):
        self.assertRaises(Forbidden, self.target.get(1).links.the_sources.create, {"@target": 2, "extra": "foo"})

    def test_update_related(self):
        self.target.get(2).links.the_sources[0].update({"extra": "sss"})
        self.assertEqual(self.src.get(1).links.the_target.item.data, {"extra": "sss", "more_data": "bla"})

    def test_delete_related(self):
        self.target.get(2).links.the_sources[0].delete()
        self.assertRaises(DoesNotExist, lambda: self.src.get(1).links.the_target.item.target)

    def test_clear(self):
        self.src.get(1).links.the_target.item.delete()
        self.assertEqual(len(self.target.get(1).links.the_sources), 0)


class OneToOneLinkTest(BaseTest):

    def test_create(self):
        self.assertRaises(DoesNotExist, lambda: self.target.get(1).links.one_to_one_source.item.target)
        self.assertEqual(self.target.get(2).links.one_to_one_source.item.data, {"extra": "foo", "more_data": "bla"})
        self.src.get(1).links.one_to_one_target.set({"@target": 1, "extra": "foo"})
        self.assertEqual(self.target.get(1).links.one_to_one_source.item.data, {"extra": "foo"})
        self.assertRaises(DoesNotExist, lambda: self.target.get(2).links.one_to_one_source.item.target)

    def test_clear(self):
        self.target.get(2).links.one_to_one_source.item.delete()
        self.assertRaises(DoesNotExist, lambda: self.target.get(2).links.one_to_one_source.item.target)


class RequiredOneToOneLinkTest(BaseTest):

    def test_target_removal_because_of_required_link(self):
        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_source(TestLink):
                    target = "Source"
                    related_name = "the_target"
                    cardinality = TestLink.cardinalities.ONE

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_target(TestLink):
                    target = "Target"
                    related_name = "the_source"
                    cardinality = TestLink.cardinalities.ONE
                    master = True
                    required = True

        srv = TestService()
        srv.register(Target)
        srv.register(Source)
        srv.setup()

        srv.storage.set(Source.get_name(), 1, {})
        srv.storage.set(Target.get_name(), 1, {})
        srv.storage.set((1, Source.Links.the_target.get_name()), 1, {})
        srv.storage.set((1, Target.Links.the_source.get_name()), 1, {})

        ep = srv.get_entry_point({})

        src = ep.get_resource(Source)
        target = ep.get_resource(Target)

        src.get(1)
        target.get(1).delete()
        self.assertRaises(DoesNotExist, src.get, 1)


class RequiredLinkTest(unittest.TestCase):

    def setUp(self):
        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_target"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_target(TestLink):
                    target = "Target"
                    related_name = "sources"
                    cardinality = TestLink.cardinalities.ONE
                    master = True
                    required = True

        srv = TestService()
        srv.register(Target)
        srv.register(Source)
        srv.setup()

        srv.storage.set(Source.get_name(), 1, {})
        srv.storage.set(Target.get_name(), 1, {})
        srv.storage.set((1, Source.Links.the_target.get_name()), 1, {})
        srv.storage.set((1, Target.Links.sources.get_name()), 1, {})

        self.entry_point = ep = srv.get_entry_point({})
        self.storage = srv.storage

        self.src = ep.get_resource(Source)
        self.target = ep.get_resource(Target)

    def test_create_without_required_links(self):
        self.assertRaisesRegexp(ValidationError, "Required links are missing: the_target", self.src.create, {
            "pk": 666
        })

    def test_delete_required_link(self):
        self.assertRaises(Forbidden, self.src.get(1).links.the_target.item.delete)

    def test_delete_required_related_link(self):
        self.assertRaises(Forbidden, self.target.get(1).links.sources[0].delete)

    def test_create_ok(self):
        self.src.create({"pk": 666}, {"the_target":  {"@target": 1}})

    def test_delete_target_resource(self):
        """ Deleting target resource with a required link to it should trigger source removal """
        self.target.get(1).delete()
        self.assertRaises(DoesNotExist, self.src.get, 1)


class ReadonlyAndChangeableTest(unittest.TestCase):

    def setUp(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)
                extra = schema.StringField(changeable=False)
                readonly = schema.StringField(readonly=True, required=False)

            class Links:

                class targets(TestLink):
                    target = "Target"
                    related_name = "sources"
                    master = True

                    class Schema:
                        extra = schema.StringField(changeable=False)
                        readonly = schema.StringField(readonly=True, required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)
                extra = schema.StringField(changeable=False)
                readonly = schema.StringField(readonly=True, required=False)

            class Links:

                class sources(TestLink):
                    target = "Source"
                    related_name = "targets"

        srv = TestService()
        srv.register(Target, "foo.Target")
        srv.register(Source, "foo.Source")
        srv.setup()

        def _c(model, pk):
            srv.storage.set(model.get_name(), pk, {"pk": pk, "extra": "foo"})

        _c(Source, 1)
        _c(Source, 2)
        _c(Target, 1)
        _c(Target, 2)

        src = srv._resources_py[Source.get_name()]
        target = srv._resources_py[Target.get_name()]

        srv.storage.set((1, src.links.targets.get_name()), 1, {"extra": "foo"})
        srv.storage.set((1, target.links.sources.get_name()), 1, {"extra": "foo"})

        self.entry_point = ep = srv.get_entry_point({})
        self.storage = srv.storage

        self.src = ep.get_resource(Source)
        self.target = ep.get_resource(Target)

    def test_create_resource_with_readonly(self):
        self.assertRaisesRegexp(ValidationError, "Readonly fields can not be set: readonly",
                                self.src.create, {"pk": 6, "extra": "Zbams", "readonly": "Uff"})

    def test_update_resource_with_unchangeable(self):
        self.assertRaisesRegexp(ValidationError, "Unchangeable fields: extra",
                                self.src.get(1).update, {"extra": "Zbams"})

    def test_create_link_with_readonly(self):
        self.assertRaisesRegexp(ValidationError, "Readonly fields can not be set: readonly",
                                self.src.get(1).links.targets.create,
                                {"@target": 2, "extra": "Zbams", "readonly": "Uff"})

    def test_update_link_with_readonly(self):
        self.assertRaisesRegexp(ValidationError, "Unchangeable fields: extra",
                                self.src.get(1).links.targets[0].update,
                                {"extra": "Zbams"})


class OneWayLinkTest(unittest.TestCase):

    def setUp(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:

                class targets(TestLink):
                    target = "Target"
                    one_way = True

                class the_target(TestLink):
                    target = "Target"
                    cardinality = TestLink.cardinalities.ONE
                    one_way = True

        srv = TestService()
        srv.register(Target)
        srv.register(Source)
        srv.setup()

        def _c(model, pk):
            srv.storage.set(model.get_name(), pk, {"pk": pk, "extra": "foo"})

        _c(Source, 1)
        _c(Source, 2)
        _c(Target, 1)
        _c(Target, 2)

        ep = srv.get_entry_point({})
        self.src = ep.get_resource(Source)

    def test_linking_to_many(self):
        self.src.get(1).links.targets.create({"@target": 1})
        self.assertEqual(self.src.get(1).links.targets.count(), 1)
        self.src.get(1).links.targets.get(1).delete()
        self.assertEqual(self.src.get(1).links.targets.count(), 0)

    def test_linking_to_one(self):
        self.src.get(1).links.the_target.set({"@target": 1})
        self.assertEqual(self.src.get(1).links.the_target.item.target.pk, 1)
        self.src.get(1).links.the_target.item.delete()
        self.assertRaises(DoesNotExist, lambda: self.src.get(1).links.the_target.item)

    def test_reset_link_to_one(self):
        self.src.get(1).links.the_target.set({"@target": 1})
        self.assertEqual(self.src.get(1).links.the_target.item.target.pk, 1)
        self.src.get(1).links.the_target.set({"@target": 2})
        self.assertEqual(self.src.get(1).links.the_target.item.target.pk, 2)

    def test_create_resource_with_one_way_links(self):
        self.src.create({
            "pk": 3,
        }, {"the_target":  {"@target": 1}, "targets": [{"@target": 2}]})


class _BaseChangeabilityTests(unittest.TestCase):

    def _reg(self, source, target):

        srv = TestService()
        srv.register(target, "foo.Target")
        srv.register(source, "foo.Source")
        srv.setup()

        def _c(model, pk):
            srv.storage.set(model.get_name(), pk, {})

        _c(source, 1)
        _c(source, 2)
        _c(target, 1)
        _c(target, 2)

        src = srv._resources_py[source.get_name()]
        target = srv._resources_py[target.get_name()]

        srv.storage.set((1, src.links.target_link.get_name()), 1, {})
        srv.storage.set((1, target.links.source_link.get_name()), 1, {})

        self.entry_point = ep = srv.get_entry_point({})
        self.storage = srv.storage

        self.src = ep.get_resource(source)
        self.target = ep.get_resource(target)


class UnchangeableLinksTest(_BaseChangeabilityTests):

    def test_modify_unchangeable_link_to_many(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    changeable = False
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    target = "Source"
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "%s unchangeable links \(forward link is unchangeable\)"

        def _assert(method, operation, *args):
            self.assertRaisesRegexp(Forbidden, err % operation, method, *args)

        _assert(self.src.get(1).links.target_link.get(1).delete, "delete")
        _assert(self.src.get(1).links.target_link.get(1).update, "update", {"foo": "bar"})
        self.assertRaisesRegexp(Forbidden,
                                "create links in unchangeable collections \(forward link is unchangeable\)",
                                self.src.get(1).links.target_link.create, {"@target": 2})

        self.src.create({"pk": 3}, {"target_link": [{"@target": 1}]})

    def test_modify_reverse_unchangeable_link_to_many(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    changeable = False
                    target = "Source"
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "%s unchangeable links \(backward link is unchangeable\)"

        def _assert(method, operation, *args):
            self.assertRaisesRegexp(Forbidden, err % operation, method, *args)

        _assert(self.src.get(1).links.target_link.get(1).delete, "delete")
        _assert(self.src.get(1).links.target_link.get(1).update, "update", {"foo": "bar"})
        self.assertRaisesRegexp(Forbidden,
                                "create links in unchangeable collections \(backward link is unchangeable\)",
                                self.src.get(1).links.target_link.create, {"@target": 2})

        self.src.create({"pk": 3}, {"target_link": [{"@target": 1}]})

    def test_set_unchangeable_link_to_one(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    cardinality = TestLink.cardinalities.ONE
                    changeable = False
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    target = "Source"
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "%s unchangeable links \(forward link is unchangeable\)"

        def _assert(method, operation, *args):
            self.assertRaisesRegexp(Forbidden, err % operation, method, *args)

        _assert(self.src.get(1).links.target_link.item.delete, "delete")
        _assert(self.src.get(1).links.target_link.item.update, "update", {"foo": "bar"})
        _assert(self.src.get(1).links.target_link.set, "set", {"@target": 2})

        self.src.create({"pk": 3}, {"target_link": {"@target": 1}})

    def test_set_reverse_unchangeable_link_to_one(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    cardinality = TestLink.cardinalities.ONE
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    target = "Source"
                    changeable = False
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "%s unchangeable links \(backward link is unchangeable\)"

        def _assert(method, operation, *args):
            self.assertRaisesRegexp(Forbidden, err % operation, method, *args)

        _assert(self.src.get(1).links.target_link.item.delete, "delete")
        _assert(self.src.get(1).links.target_link.item.update, "update", {"foo": "bar"})
        _assert(self.src.get(1).links.target_link.set, "set", {"@target": 2})

        self.src.create({"pk": 3}, {"target_link": {"@target": 1}})


class ReadonlyLinksTest(_BaseChangeabilityTests):

    def test_modify_readonly_link_to_many(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    readonly = True
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    target = "Source"
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "link is readonly \(forward link is readonly\)"

        def _assert(method, *args):
            self.assertRaisesRegexp(Forbidden, err, method, *args)

        _assert(self.src.get(1).links.target_link.get(1).delete)
        _assert(self.src.get(1).links.target_link.get(1).update, {"foo": "bar"})
        _assert(self.src.get(1).links.target_link.create, {"@target": 2})

        self.assertRaisesRegexp(ValidationError, err, self.src.create, {"pk": 3}, {"target_link": [{"@target": 1}]})

    def test_modify_reverse_readonly_link_to_many(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    readonly = True
                    target = "Source"
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "link is readonly \(backward link is readonly\)"

        def _assert(method, *args):
            self.assertRaisesRegexp(Forbidden, err, method, *args)

        _assert(self.src.get(1).links.target_link.get(1).delete)
        _assert(self.src.get(1).links.target_link.get(1).update, {"foo": "bar"})
        _assert(self.src.get(1).links.target_link.create, {"@target": 2})

        self.assertRaisesRegexp(ValidationError, err, self.src.create, {"pk": 3}, {"target_link": [{"@target": 1}]})

    def test_set_unchangeable_link_to_one(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    cardinality = TestLink.cardinalities.ONE
                    readonly = True
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    target = "Source"
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "link is readonly \(forward link is readonly\)"

        def _assert(method, *args):
            self.assertRaisesRegexp(Forbidden, err, method, *args)

        _assert(self.src.get(1).links.target_link.item.delete)
        _assert(self.src.get(1).links.target_link.item.update, {"foo": "bar"})
        _assert(self.src.get(1).links.target_link.set, {"@target": 2})

        self.assertRaisesRegexp(ValidationError, err, self.src.create, {"pk": 3}, {"target_link": {"@target": 1}})

    def test_set_reverse_unchangeable_link_to_one(self):

        class Source(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class target_link(TestLink):
                    target = "Target"
                    related_name = "source_link"
                    cardinality = TestLink.cardinalities.ONE
                    master = True

                    class Schema:
                        foo = schema.StringField(required=False)

        class Target(TestResource):

            class Schema:

                pk = schema.IntegerField(pk=True)

            class Links:

                class source_link(TestLink):
                    target = "Source"
                    readonly = True
                    related_name = "target_link"

        self._reg(Source, Target)

        err = "link is readonly \(backward link is readonly\)"

        def _assert(method, *args):
            self.assertRaisesRegexp(Forbidden, err, method, *args)

        _assert(self.src.get(1).links.target_link.item.delete)
        _assert(self.src.get(1).links.target_link.item.update, {"foo": "bar"})
        _assert(self.src.get(1).links.target_link.set, {"@target": 2})

        self.assertRaisesRegexp(ValidationError, err, self.src.create, {"pk": 3}, {"target_link": {"@target": 1}})
