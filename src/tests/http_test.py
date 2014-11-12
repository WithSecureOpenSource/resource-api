"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import json

import mock

from werkzeug.test import Client as BaseClient
from werkzeug.wrappers import BaseResponse

from resource_api_http.http import Application
from resource_api import errors

from .base_test import BaseTest


class Client(BaseClient):

    def open(self, *args, **kw):
        kw["content_type"] = "application/json"
        if "data" in kw:
            kw["data"] = json.dumps(kw["data"])
        return BaseClient.open(self, *args, **kw)


class BaseHttpTest(BaseTest):

    def setUp(self):
        super(BaseHttpTest, self).setUp()
        self.client = Client(Application(self.srv), BaseResponse)

    def assertResponse(self, response, data=None, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        if data is not None:
            self.assertEqual(json.loads(response.data), data)


class HttpTest(BaseHttpTest):

    def test_get_schema(self):
        self.assertResponse(
            self.client.options("/"),
            self.srv.get_schema())

    def test_get_resource_collection(self):
        self.assertResponse(
            self.client.get("/foo.Source"),
            self.src.serialize())

    def test_get_resource_collection_with_filtering(self):
        self.client.get("/foo.Source?foo=bar&foo=bar2&wang.wong=3&query_param=Foo")
        self.assertEqual(self.srv.storage.call_log[-1],
                         ("GET_KEYS", "tests.sample_app.resources.Source", {"query_param": u"Foo"}))

    def test_get_resource_collection_count(self):
        self.assertResponse(
            self.client.get("/foo.Source:count"),
            len(self.src))

    def test_get_resource_collection_count_with_filtering(self):
        self.client.get("/foo.Source:count?foo=bar&foo=bar2&wang.wong=3&query_param=Foo")
        self.assertEqual(self.srv.storage.call_log[-1],
                         ("GET_KEYS", "tests.sample_app.resources.Source", {"query_param": u"Foo"}))

    def test_get_resource_item(self):
        self.assertResponse(
            self.client.get("/foo.Source/1"),
            self.src.get(1).serialize())

    def test_delete_resource_item(self):
        self.assertResponse(
            self.client.delete("/foo.Source/1"),
            status_code=204)
        self.assertRaises(errors.DoesNotExist, self.src.get, 1)

    def test_update_resource_item(self):
        self.assertResponse(
            self.client.patch("/foo.Source/1", data={"extra": "wuga wuga"}),
            status_code=204)
        self.assertEqual(self.src.get(1).data["extra"], "wuga wuga")

    def test_create_resource_item(self):
        self.assertResponse(
            self.client.post("/foo.Source", data={"pk": 3, "extra": "foo", "@links": {"targets": [{
                                                  "@target": 1, "extra": "woof", "more_data": "bar"}]}}),
            data=3, status_code=201)
        self.assertEqual(self.src.get(3).data["extra"], "foo")
        self.assertEqual(self.src.get(3).links.targets.get(1).data["extra"], "woof")

    def test_get_link_to_many_collection(self):
        self.assertResponse(
            self.client.get("/foo.Source/1/targets"),
            self.src.get(1).links.targets.serialize())

    def test_get_link_to_many_collection_with_filtering(self):
        self.client.get("/foo.Source/1/targets?foo=bar&foo=bar2&wang.wong=3&query_param=Foo")
        self.assertEqual(self.srv.storage.call_log[-1],
                         ("GET_KEYS", (1, "tests.sample_app.resources.Source:targets"), {"query_param": "Foo"}))

    def test_get_link_to_many_collection_count(self):
        self.assertResponse(
            self.client.get("/foo.Source/1/targets:count"),
            len(self.src.get(1).links.targets))

    def test_get_link_to_many_collection_count_with_filtering(self):
        self.client.get("/foo.Source/1/targets:count?foo=bar&foo=bar2&wang.wong=3&query_param=Foo")
        self.assertEqual(self.srv.storage.call_log[-1],
                         ("GET_KEYS", (1, "tests.sample_app.resources.Source:targets"), {"query_param": "Foo"}))

    def test_update_link_to_many_item(self):
        self.assertResponse(
            self.client.patch("/foo.Source/1/targets/1", data={"extra": "cadavr"}),
            status_code=204)
        self.assertEqual(self.src.get(1).links.targets.get(1).data["extra"], "cadavr")

    def test_delete_link_to_many_item(self):
        self.assertResponse(
            self.client.delete("/foo.Source/1/targets/1"),
            status_code=204)
        self.assertRaises(errors.DoesNotExist, self.src.get(1).links.targets.get, 1)

    def test_get_link_to_many_item_data(self):
        self.assertResponse(
            self.client.get("/foo.Source/1/targets/1:data"),
            self.src.get(1).links.targets.get(1).serialize())

    def test_get_reverse_link_to_many_item_data(self):
        self.assertResponse(
            self.client.get("/foo.Target/1/sources/1:data"),
            self.target.get(1).links.sources.get(1).serialize())

    def test_create_link_to_many_item(self):
        self.assertResponse(
            self.client.post("/foo.Source/1/targets", data={"@target": 2, "extra": "uff"}),
            status_code=201)
        self.assertEqual(self.src.get(1).links.targets.get(2).data["extra"], "uff")

    def test_set_link_to_one(self):
        self.assertResponse(
            self.client.put("/foo.Source/1/the_target", data={"@target": 2, "extra": "uff"}),
            status_code=201)
        self.assertEqual(self.src.get(1).links.the_target.item.data, {"extra": "uff"})

    def test_update_link_to_one(self):
        self.assertResponse(
            self.client.patch("/foo.Source/1/the_target/item", data={"extra": "cadavr"}),
            status_code=204)
        self.assertEqual(self.src.get(1).links.the_target.item.data["extra"], "cadavr")

    def test_delete_link_to_one(self):
        self.assertResponse(
            self.client.delete("/foo.Source/1/the_target/item"),
            status_code=204)
        self.assertResponse(self.client.get("/foo.Source/1/the_target/item"), status_code=404)

    def test_get_link_to_one_data(self):
        self.assertResponse(
            self.client.get("/foo.Source/1/the_target/item:data"),
            self.src.get(1).links.the_target.item.serialize())

    def test_get_link_to_one(self):
        self.assertResponse(self.client.get("/foo.Source/1/the_target/item"), data=2, status_code=200)


class HttpErrorTest(BaseHttpTest):

    def setUp(self):
        super(HttpErrorTest, self).setUp()

        self._url_map = url_map = mock.Mock()

        class CustomApp(Application):
            def __init__(self, service, debug=False):
                self._url_map = url_map
                self._debug = debug

        self.client = Client(CustomApp(self.srv), BaseResponse)

    def _check_exception(self, exception_class, data, error_code):
        self._url_map.bind_to_environ.side_effect = exception_class(data)
        self.assertResponse(
            self.client.get("/URL"),
            data=data,
            status_code=error_code)

    def test_does_not_exist(self):
        self._check_exception(errors.DoesNotExist, "Foo bar", 404)

    def test_multiple_found(self):
        self._check_exception(errors.MultipleFound, "Foo bar", 500)

    def test_validation_error(self):
        self._check_exception(errors.ValidationError, "Foo bar", 400)

    def test_data_conflict_error(self):
        self._check_exception(errors.DataConflictError, "Foo bar", 409)

    def test_forbidden(self):
        self._check_exception(errors.Forbidden, "Foo bar", 405)

    def test_authorization_error(self):
        self._check_exception(errors.AuthorizationError, "Foo bar", 403)

    def test_not_implemented_error(self):
        self._check_exception(NotImplementedError, "Foo bar", 501)

    def test_server_exception(self):
        self._url_map.bind_to_environ.side_effect = Exception("Foo bar")
        self.assertResponse(
            self.client.get("/URL"),
            data="Server error",
            status_code=500)
