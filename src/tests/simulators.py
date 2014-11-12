"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
from collections import defaultdict
from pprint import pprint

from resource_api.service import Service
from resource_api.interfaces import Resource, Link


class RamStorage(object):

    def __init__(self):
        self._items = defaultdict(dict)
        self._call_log = []
        self._actions = []

    def set(self, namespace, pk, value):
        self._call_log.append(("SET", namespace, pk, value))
        if value is None:
            self._items[namespace][pk] = {}
        else:
            data = self._items[namespace].get(pk, {})
            data.update(value)
            self._items[namespace][pk] = data

    def get(self, namespace, pk):
        self._call_log.append(("GET", namespace, pk))
        return dict(self._items[namespace][pk])

    def exists(self, namespace, pk):
        self._call_log.append(("EXISTS", namespace, pk))
        return pk in self._items[namespace]

    def delete(self, namespace, pk):
        self._call_log.append(("DELETE", namespace, pk))
        self._items[namespace].pop(pk)

    def get_keys(self, namespace, params=None):
        self._call_log.append(("GET_KEYS", namespace, params))
        return self._items[namespace].keys()

    def show(self):
        pprint(dict(self._items))

    def show_log(self):
        pprint(self._call_log)

    @property
    def call_log(self):
        return self._call_log

    def invoke_action(self, *args):
        self._actions.append(args)

    @property
    def actions(self):
        return self._actions


class TestService(Service):

    def __init__(self):
        super(TestService, self).__init__()
        self._storage = RamStorage()

    def _get_context(self):
        return {"storage": self._storage}

    def _get_user(self, data):
        return data

    @property
    def storage(self):
        return self._storage


class TestResource(Resource):

    def exists(self, user, pk):
        return self.context["storage"].exists(self.get_name(), pk)

    def get_data(self, user, pk):
        return self.context["storage"].get(self.get_name(), pk)

    def delete(self, user, pk):
        self.context["storage"].delete(self.get_name(), pk)

    def create(self, user, pk, data):
        self.context["storage"].set(self.get_name(), pk, data)

    def update(self, user, pk, data):
        self.context["storage"].set(self.get_name(), pk, data)

    def get_uris(self, user, params=None):
        return self.context["storage"].get_keys(self.get_name(), params)

    def get_count(self, user, params=None):
        return len(self.get_uris(user, params))


class TestLink(Link):

    def exists(self, user, pk, rel_pk):
        return self.context["storage"].exists((pk, self.get_name()), rel_pk)

    def get_data(self, user, pk, rel_pk):
        return self.context["storage"].get((pk, self.get_name()), rel_pk)

    def create(self, user, pk, rel_pk, data=None):
        self.context["storage"].set((pk, self.get_name()), rel_pk, data)

    def update(self, user, pk, rel_pk, data):
        self.context["storage"].set((pk, self.get_name()), rel_pk, data)

    def delete(self, user, pk, rel_pk):
        self.context["storage"].delete((pk, self.get_name()), rel_pk)

    def get_uris(self, user, pk, params=None):
        return self.context["storage"].get_keys((pk, self.get_name()), params)

    def get_count(self, user, pk, params=None):
        return len(self.get_uris(user, pk, params))
