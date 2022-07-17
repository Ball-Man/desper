from context import desper
from helpers import *

import pytest


@pytest.fixture
def uncached_handle():
    handle = SimpleHandle(11)
    return handle


@pytest.fixture
def cached_handle():
    handle = SimpleHandle(10)
    handle()
    return handle


@pytest.fixture
def resource_map():
    map_ = desper.ResourceMap()

    resources = {'res1': SimpleHandle(1), 'res2': SimpleHandle(2)}

    map1 = desper.ResourceMap()
    map2 = desper.ResourceMap()
    map3 = desper.ResourceMap()

    map_.maps['map1'] = map1
    map1.maps['map2'] = map2
    map_.maps['map2'] = map3

    map_.handles.update(resources)
    map1.handles.update(resources)
    map2.handles.update(resources)
    map3.handles.update(resources)

    return map_


class TestHandle:

    def test_get(self):
        val = 10
        handle = SimpleHandle(val)

        assert handle() == val * 2

    def test_cached(self, cached_handle, uncached_handle):
        assert cached_handle.cached
        assert not uncached_handle.cached

    def test_clear(self, cached_handle):
        cached_handle.clear()
        assert not cached_handle.cached


class TestResourceMap:

    def test_get(self, resource_map):
        # Test simple retrieval
        res1 = resource_map.get('res1')
        assert isinstance(res1, desper.Handle)
        assert res1() == 2

        assert isinstance(resource_map.get('map1'), desper.ResourceMap)

        # Test simple failure
        assert resource_map.get('xxx') is None
        assert resource_map.get('xxx', 99) == 99

        # Test nested retrieval
        res2 = resource_map.get('map1/map2/res2')
        assert isinstance(res2, desper.Handle)
        assert res2() == 4

        assert isinstance(resource_map.get('map1/map2'), desper.ResourceMap)

        # Test nested failure
        assert resource_map.get('map1/xxx') is None
        assert resource_map.get('res1/xxx') is None
        assert resource_map.get('map1/map2/map3') is None
        assert resource_map.get('map1/map2/map3', 99) == 99
