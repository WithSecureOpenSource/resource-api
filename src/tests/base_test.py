"""
Copyright (c) 2014-2015 F-Secure
See LICENSE for details
"""
import unittest

from .simulators import TestService
from .sample_app.resources import Target, Source


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.srv = srv = TestService()
        srv.register(Target, "foo.Target")
        srv.register(Source, "foo.Source")
        srv.setup()

        def _c(model, pk):
            srv.storage.set(model.get_name(), pk, {"pk": pk, "extra": "foo", "more_data": "bla"})

        _c(Source, 1)
        _c(Source, 2)
        _c(Target, 1)
        _c(Target, 2)

        src = srv._resources_py[Source.get_name()]
        target = srv._resources_py[Target.get_name()]

        srv.storage.set((1, src.links.targets.get_name()), 1, {"extra": "foo", "more_data": "bla"})
        srv.storage.set((1, target.links.sources.get_name()), 1, {"extra": "foo", "more_data": "bla"})
        srv.storage.set((1, src.links.the_target.get_name()), 2, {"extra": "foo", "more_data": "bla"})
        srv.storage.set((2, target.links.the_sources.get_name()), 1, {"extra": "foo", "more_data": "bla"})
        srv.storage.set((1, src.links.one_to_one_target.get_name()), 2, {"extra": "foo", "more_data": "bla"})
        srv.storage.set((2, target.links.one_to_one_source.get_name()), 1, {"extra": "foo", "more_data": "bla"})

        self.entry_point = ep = srv.get_entry_point({})
        self.storage = srv.storage

        self.src = ep.get_resource(Source)
        self.target = ep.get_resource(Target)
