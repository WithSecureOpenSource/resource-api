"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from resource_api.errors import AuthorizationError, DoesNotExist, ValidationError

from .base_test import BaseTest


# NOTE: here we access self.entry_point._user to avoid test code duplication. In real life it should not be done.


class ResourceAuthorizationTest(BaseTest):

    def test_get_not_authorized(self):
        self.entry_point._user = {"source": {"view": False}}
        self.assertRaises(AuthorizationError, lambda: self.src.get(1).data)

    def test_delete_not_authorized(self):
        self.entry_point._user = {"source": {"delete": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).delete)

    def test_create_not_authorized(self):
        self.entry_point._user = {"source": {"create": False}}
        self.assertRaises(AuthorizationError, self.src.create, {"pk": 3, "extra": "foo"})

    def test_update_not_authorized(self):
        self.entry_point._user = {"source": {"update": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).update, {"extra": "Neo"})

    def test_get_collection_not_authorized(self):
        self.entry_point._user = {"source": {"list": False}}
        self.assertRaises(AuthorizationError, lambda: list(self.src))

    def test_get_collection_count_not_authorized(self):
        self.entry_point._user = {"source": {"list": False}}
        self.assertRaises(AuthorizationError, self.src.count)

    def test_get_non_discoverable(self):
        self.entry_point._user = {"source": {"discover": False}}
        self.assertRaises(DoesNotExist, lambda: self.src.get(1).data)


class LinkToManyAuthorizationTest(BaseTest):

    def test_get_data_not_authorized(self):
        self.entry_point._user = {"link": {"view": False}}
        self.assertRaises(AuthorizationError, lambda: self.src.get(1).links.targets.get(1).data)
        self.assertRaises(AuthorizationError, lambda: self.target.get(1).links.sources.get(1).data)

    def test_delete_not_authorized(self):
        self.entry_point._user = {"link": {"delete": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.targets.get(1).delete)

    def test_create_not_authorized(self):
        self.entry_point._user = {"link": {"create": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.targets.create, {"@target": 2, "extra": "Bal"})

    def test_update_not_authorized(self):
        self.entry_point._user = {"link": {"update": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.targets.get(1).update, {"extra": "Neo"})

    def test_get_collection_not_authorized(self):
        self.entry_point._user = {"link": {"list": False}}
        self.assertRaises(AuthorizationError, list, self.src.get(1).links.targets)

    def test_get_collection_count_not_authorized(self):
        self.entry_point._user = {"link": {"list": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.targets.count)

    def test_get_collection_of_non_discoverable_links(self):
        self.entry_point._user = {"target": {"discover": False}}
        self.assertEqual(list(self.src.get(1).links.targets), [None])
        self.entry_point._user = {"source": {"discover": False}}
        self.assertEqual(list(self.target.get(1).links.sources), [None])
        self.entry_point._user = {"link": {"discover": False}}
        self.assertEqual(list(self.target.get(1).links.sources), [None])
        self.assertEqual(list(self.src.get(1).links.targets), [None])

    def test_get_non_discoverable_link(self):
        self.entry_point._user = {"link": {"discover": False}}
        self.assertRaises(DoesNotExist, self.src.get(1).links.targets.get, 1)
        self.assertRaises(DoesNotExist, self.target.get(1).links.sources.get, 1)

    def test_get_link_with_non_discoverable_target(self):
        self.entry_point._user = {"target": {"discover": False}}
        self.assertRaises(DoesNotExist, self.src.get(1).links.targets.get, 1)

    def test_create_link_with_non_discoverable_target(self):
        self.entry_point._user = {"target": {"discover": False}}
        self.assertRaises(ValidationError, self.src.get(1).links.targets.create, {"@target": 2, "extra": "Bal"})


class LinkToOneAuthorizationTest(BaseTest):

    def test_create_not_authorized(self):
        self.entry_point._user = {"link": {"create": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.the_target.set, {"@target": 2, "extra": "Bal"})

    def test_delete_not_authorized(self):
        self.entry_point._user = {"link": {"delete": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.the_target.set, {"@target": 2, "extra": "Bal"})

    def test_update_not_authorized(self):
        self.entry_point._user = {"link": {"update": False}}
        self.assertRaises(AuthorizationError, self.src.get(1).links.the_target.item.update, {"extra": "Fpo"})

    def test_set_with_non_discoverable_target(self):
        self.entry_point._user = {"target": {"discover": False}}
        self.assertRaisesRegexp(ValidationError, "Target: Resource with pk \w{1,2} does not exist.",
                                self.src.get(1).links.the_target.set, {"@target": 2, "extra": "Bal"})

    def test_get_non_discoverable_link(self):
        self.entry_point._user = {"link": {"discover": False}}
        self.assertRaisesRegexp(DoesNotExist, lambda: self.src.get(1).links.the_target.item.target)

    def test_get_link_with_non_discoverable_target(self):
        self.entry_point._user = {"target": {"discover": False}}
        self.assertRaisesRegexp(DoesNotExist, lambda: self.src.get(1).links.the_target.item.target)
