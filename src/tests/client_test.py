"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from datetime import datetime
import unittest

import mock

from werkzeug.test import Client as HttpClient

from resource_api.errors import ValidationError, DoesNotExist, Forbidden
from resource_api.schema import DateTimeField, IntegerField

from resource_api_http.http import Application

from werkzeug.wrappers import Response

from resource_api_http_client.client import(Client, RootResourceCollection, ResourceInstance, ResourceCollection,
                                            LinkHolder, LinkToOne, RootLinkCollection, LinkCollection, LinkInstance)
from resource_api_http_client.transport import JsonClient

from .base_test import BaseTest
from .simulators import TestService, TestResource, TestLink


class JsonTest(unittest.TestCase):

    def _validate_exception(self, exception_class, status_code):
        resp = mock.Mock()
        resp.data = "666"
        resp.status_code = status_code
        client = mock.Mock()
        client.open.return_value = resp
        cli = JsonClient(client)
        self.assertRaises(exception_class, cli.open, "some_url")

    def test_item_does_not_exist(self):
        self._validate_exception(DoesNotExist, 404)

    def test_unknown_error(self):
        self._validate_exception(Exception, 500)
        self._validate_exception(Exception, 430)

    def test_ok(self):
        resp = mock.Mock()
        resp.data = "666"
        resp.status_code = 200
        client = mock.Mock()
        client.open.return_value = resp
        cli = JsonClient(client)
        self.assertEqual(cli.open("foo"), 666)

    def test_validation_error(self):
        self._validate_exception(ValidationError, 400)

    def test_not_implemented_error(self):
        self._validate_exception(NotImplementedError, 501)

    def test_not_allowed(self):
        self._validate_exception(Forbidden, 405)


class BaseClientTest(BaseTest):

    def setUp(self):
        super(BaseClientTest, self).setUp()
        self.client = Client("/", JsonClient(HttpClient(Application(self.srv), Response)))


class ResourceTest(BaseClientTest):

    def test_get_schema(self):
        self.assertEqual(self.client.schema, {"foo.Target": mock.ANY, "foo.Source": mock.ANY})

    def test_get_root_resource_collection(self):
        collection = self.client.get_resource_by_name("foo.Source")
        self.assertIsInstance(collection, RootResourceCollection)

    def test_get_resource(self):
        collection = self.client.get_resource_by_name("foo.Source")
        item = collection.get(1)
        self.assertIsInstance(item, ResourceInstance)
        self.assertTrue(item.pk, 1)
        self.assertEqual({"pk": 1, "more_data": "bla", "extra": "foo"}, item.data)

    def test_get_count(self):
        count = self.client.get_resource_by_name("foo.Source").count()
        self.assertEqual(count, 2)
        length = len(self.client.get_resource_by_name("foo.Source"))
        self.assertEqual(length, 2)

    def test_filter(self):
        collection = self.client.get_resource_by_name("foo.Source").filter(params={"foo": "bar"})
        self.assertNotIsInstance(collection, RootResourceCollection)
        self.assertIsInstance(collection, ResourceCollection)

    def test_iteration(self):
        collection = self.client.get_resource_by_name("foo.Source")
        items = list(collection)
        self.assertIsInstance(items[0], ResourceInstance)

    def test_access_by_index(self):
        item = self.client.get_resource_by_name("foo.Source")[0]
        self.assertIsInstance(item, ResourceInstance)

    def test_create(self):
        data = dict(pk=5, extra="Foo", more_data="Bar")
        item = self.client.get_resource_by_name("foo.Source").create(data)
        self.assertIsInstance(item, ResourceInstance)
        self.assertEqual(item.pk, 5)
        self.assertEqual(item.data, data)

    def test_update(self):
        item = self.client.get_resource_by_name("foo.Source")[0]
        item.update(data={"extra": "Zool!!!!"})
        self.assertEqual(item.data, {"extra": "Zool!!!!", "more_data": "bla", "pk": 1})

    def test_delete(self):
        collection = self.client.get_resource_by_name("foo.Source")
        item = collection.get(1)
        item.delete()
        self.assertRaises(DoesNotExist, collection.get, 1)


class LinkToOneTest(BaseClientTest):

    def test_get_link_holder(self):
        links = self.client.get_resource_by_name("foo.Source")[0].links
        self.assertIsInstance(links, LinkHolder)

    def test_get_link_to_one(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.the_target
        self.assertIsInstance(link, LinkToOne)

    def test_get_link_to_one_target(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.the_target
        self.assertEqual(link.item.target.pk, 2)

    def test_get_link_to_one_data(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.the_target
        self.assertEqual(link.item.data, {"extra": "foo", "more_data": "bla"})

    def test_update(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.the_target
        link.item.update({"extra": "Baga fel"})
        self.assertEqual(link.item.data, {"extra": "Baga fel", "more_data": "bla"})

    def test_set(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.the_target
        link.set({"@target": 1, "extra": "Baga fel"})
        self.assertEqual(link.item.target.pk, 1)

    def test_delete(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.the_target
        link.item.delete()
        self.assertRaises(DoesNotExist, lambda: link.item.data)


class LinkToManytest(BaseClientTest):

    def test_get_root_link_collection(self):
        links = self.client.get_resource_by_name("foo.Source")[0].links.targets
        self.assertIsInstance(links, RootLinkCollection)

    def test_filter(self):
        links = self.client.get_resource_by_name("foo.Source")[0].links.targets.filter()
        self.assertNotIsInstance(links, RootLinkCollection)
        self.assertIsInstance(links, LinkCollection)

    def test_iteration(self):
        links = list(self.client.get_resource_by_name("foo.Source")[0].links.targets)
        link = links[0]
        self.assertIsInstance(link, LinkInstance)

    def test_access_by_index(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.targets[0]
        self.assertIsInstance(link, LinkInstance)

    def test_get_count(self):
        links = self.client.get_resource_by_name("foo.Source")[0].links.targets
        count = links.count()
        self.assertEqual(count, 1)
        length = len(links)
        self.assertEqual(length, 1)

    def test_update(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.targets[0]
        link.update({"extra": "Baga fel"})
        self.assertEqual(link.data, {"extra": "Baga fel", "more_data": "bla"})

    def test_delete(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.targets[0]
        link.delete()
        self.assertRaises(DoesNotExist, lambda: link.data)

    def test_create(self):
        links = self.client.get_resource_by_name("foo.Source")[0].links.targets
        link = links.create({"@target": 2})
        self.assertIsInstance(link, LinkInstance)
        self.assertEqual(links.count(), 2)

    def test_get(self):
        link = self.client.get_resource_by_name("foo.Source")[0].links.targets.get(1)
        self.assertEqual(link.target.pk, 1)


class SerializationTest(unittest.TestCase):

    def setUp(self):

        class Source(TestResource):

            class Schema:
                pk = IntegerField(pk=True)
                datetieme_field = DateTimeField(required=False)

            class Links:

                class targets(TestLink):
                    target = "Target"
                    one_way = True

                    class Schema:
                        datetieme_field = DateTimeField(required=False)

        class Target(TestResource):

            class Schema:
                pk = IntegerField(pk=True)

        self.srv = srv = TestService()
        srv.register(Target, "foo.Target")
        srv.register(Source, "foo.Source")
        srv.setup()

        def _c(model, pk):
            srv.storage.set(model.get_name(), pk, {"pk": pk, "datetieme_field": datetime(1, 1, 1, 1, 1, 1)})

        _c(Source, 1)
        _c(Target, 1)

        src = srv._resources_py[Source.get_name()]

        srv.storage.set((1, src.links.targets.get_name()), 1, {"datetieme_field": datetime(1, 1, 1, 1, 1, 1)})

        self.entry_point = ep = srv.get_entry_point({})
        self.storage = srv.storage

        self.src = ep.get_resource(Source)
        self.target = ep.get_resource(Target)
        self.client = Client("/", JsonClient(HttpClient(Application(srv), Response)))

    def test_get_resource_datetime(self):
        collection = self.client.get_resource_by_name("foo.Source")
        item = collection.get(1)
        self.assertEqual({"pk": 1, "datetieme_field": datetime(1, 1, 1, 1, 1, 1)}, item.data)

    def test_get_link_datetime(self):
        collection = self.client.get_resource_by_name("foo.Source")
        item = collection.get(1)
        link = item.links.targets.get(1)
        self.assertEqual({"datetieme_field": datetime(1, 1, 1, 1, 1, 1)}, link.data)
