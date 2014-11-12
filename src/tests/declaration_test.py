"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import unittest

from resource_api.errors import ResourceDeclarationError
from resource_api import schema

from .simulators import TestResource, TestService, TestLink


class ResourceDeclarationTest(unittest.TestCase):

    def setUp(self):
        self.srv = TestService()

    def test_normal(self):

        class OkeishResource(TestResource):
            class Schema:
                name = schema.IntegerField(pk=True, description="PK field")

        self.srv.register(OkeishResource)

    def test_no_pk(self):

        class ResourceWithoutPk(TestResource):
            class Schema:
                name = schema.StringField(description="Foo")

        self.assertRaisesRegexp(ResourceDeclarationError, "PK field is not defined", self.srv.register,
                                ResourceWithoutPk)

    def test_multiple_pks(self):

        class ResourceWithMultiplePks(TestResource):
            class Schema:
                pk_one = schema.StringField(pk=True, description="PK 1")
                pk_two = schema.StringField(pk=True, description="PK 2")

        self.assertRaisesRegexp(ResourceDeclarationError, "Multiple PKs found: pk_one, pk_two",
                                self.srv.register, ResourceWithMultiplePks)


class ResourceInterfaceTest(unittest.TestCase):

    def setUp(self):
        class ResourceWithPk(TestResource):
            class Schema:
                name = schema.StringField(description="Foo", pk=True)
        self.res = ResourceWithPk(None)

    def test_string_representation(self):
        self.assertEqual(str(self.res), "tests.declaration_test.ResourceWithPk")

    def test_default_permissions(self):
        # NOTE: input is not important - we just verify that all return True
        self.assertTrue(self.res.can_get_data(None, None, None))
        self.assertTrue(self.res.can_discover(None, None))
        self.assertTrue(self.res.can_get_uris(None))
        self.assertTrue(self.res.can_update(None, None, None))
        self.assertTrue(self.res.can_create(None, None))
        self.assertTrue(self.res.can_delete(None, None))


class LinkDeclarationTest(unittest.TestCase):

    def setUp(self):
        self.srv = TestService()

    def test_missing_target(self):

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    related_name = "foo"

        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "target is not defined", self.srv.setup)

    def test_unregistered_target(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_link"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    target = "Target"
                    related_name = "sources"

        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "target resource .* is not registered",
                                self.srv.setup)

    def test_one_way_link(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class targets(TestLink):
                    target = "Target"
                    related_name = "sources"
                    one_way = True

        self.srv.register(Source)
        self.srv.register(Target)
        self.srv.setup()

    def test_missing_related_name(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_link"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    target = "Target"

        self.srv.register(Target)
        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "related_name is not defined", self.srv.setup)

    def test_wrong_cardinality(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_link"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    target = "Target"
                    related_name = "sources"
                    cardinality = "DDD"

        self.srv.register(Target)
        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "cardinality must be ONE or MANY",
                                self.srv.setup)

    def _check_wrong_param(self, name):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_link"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    target = "Target"
                    related_name = "sources"

        setattr(Source.Links.the_link, name, "DDD")

        self.srv.register(Target)
        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "%s must be boolean" % name, self.srv.setup)

    def test_wrong_master(self):
        self._check_wrong_param("master")

    def test_wrong_required(self):
        self._check_wrong_param("required")

    def test_wrong_one_way(self):
        self._check_wrong_param("one_way")

    def test_wrong_changeable(self):
        self._check_wrong_param("changeable")

    def test_failed_link_connection(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_link"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    target = "Target"
                    related_name = "sourceszzzzzzzzzz"
                    master = True

        self.srv.register(Target)
        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "Unable to link .+ to .+", self.srv.setup)

    def test_required_to_many_link(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "the_link"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class the_link(TestLink):
                    target = "Target"
                    related_name = "sources"
                    master = True
                    required = True

        self.srv.register(Target)
        self.srv.register(Source)
        self.assertRaisesRegexp(ResourceDeclarationError, "Link to many can't be required", self.srv.setup)

    def test_no_master_link(self):

        class Target(TestResource):

            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class sources(TestLink):
                    target = "Source"
                    related_name = "targets"

        class Source(TestResource):
            class Schema:
                pk = schema.IntegerField(pk=True)

            class Links:
                class targets(TestLink):
                    target = "Target"
                    related_name = "sources"

        self.srv.register(Target)
        self.srv.register(Source)

        self.assertRaisesRegexp(ResourceDeclarationError, "this or related link must be a master one", self.srv.setup)


class LinkInterfaceTest(unittest.TestCase):

    def test_default_permissions(self):

        class TheLink(TestLink):
            source = "Bla"
            target = "Foo"
            related_name = "bar"

        lnk = TheLink(None)

        # NOTE: input is not important - we just verify that all return True
        self.assertTrue(lnk.can_get_data(None, None, None, None))
        self.assertTrue(lnk.can_discover(None, None, None))
        self.assertTrue(lnk.can_get_uris(None, None))
        self.assertTrue(lnk.can_update(None, None, None, None))
        self.assertTrue(lnk.can_create(None, None, None, None))
        self.assertTrue(lnk.can_delete(None, None, None))
