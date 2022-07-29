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

    def test_getitem(self, resource_map):
        # Test simple retrieval
        assert resource_map['res1'] == 2
        assert isinstance(resource_map['map1'], desper.ResourceMap)

        # Test simple failure
        with pytest.raises(KeyError):
            resource_map['xxx']

        # Test nested retrieval
        assert resource_map['map1/map2/res2'] == 4
        assert isinstance(resource_map['map1/map2'], desper.ResourceMap)

        # Test nested failure
        with pytest.raises(KeyError):
            resource_map['map1/xxx']
            resource_map['res1/xxx']
            resource_map['map1/map2/map3']

    def test_setitem(self, resource_map):
        # Test simple insertion
        newres_name = 'newres'
        newmap_name = 'newmap'

        resource_map[newres_name] = SimpleHandle(3)
        assert newres_name in resource_map.handles
        assert newres_name not in resource_map.maps

        resource_map[newmap_name] = desper.ResourceMap()
        assert newmap_name not in resource_map.handles
        assert newmap_name in resource_map.maps

        # Test protocol attributes
        assert resource_map.handles[newres_name].parent == resource_map
        assert resource_map.handles[newres_name].key == newres_name
        assert resource_map.maps[newmap_name].parent == resource_map
        assert resource_map.maps[newmap_name].key == newmap_name

        # Test nested insertion
        nested_res_name = f'{newmap_name}/{newmap_name}/{newres_name}'
        nested_map_name = f'{newmap_name}/{newmap_name}/{newmap_name}'

        resource_map[nested_res_name] = SimpleHandle(4)
        assert newres_name in resource_map.maps[newmap_name].maps[
            newmap_name].handles
        assert newres_name not in resource_map.maps[newmap_name].maps[
            newmap_name].maps

        resource_map[nested_map_name] = desper.ResourceMap()
        assert newmap_name not in resource_map.maps[newmap_name].maps[
            newmap_name].handles
        assert newmap_name in resource_map.maps[newmap_name].maps[
            newmap_name].maps

        # Test protocol attributes
        assert (resource_map.maps[newmap_name].maps[newmap_name]
                .handles[newres_name].parent
                == resource_map.maps[newmap_name].maps[newmap_name])
        assert (resource_map.maps[newmap_name].maps[newmap_name]
                .handles[newres_name].key == newres_name)

        assert (resource_map.maps[newmap_name].maps[newmap_name]
                .maps[newmap_name].parent
                == resource_map.maps[newmap_name].maps[newmap_name])
        assert (resource_map.maps[newmap_name].maps[newmap_name]
                .maps[newmap_name].key == newmap_name)

        # Test overwritten resources
        resource_map[nested_map_name] = SimpleHandle(10)
        assert newmap_name in resource_map.maps[newmap_name].maps[
            newmap_name].handles
        assert newmap_name not in resource_map.maps[newmap_name].maps[
            newmap_name].maps

        resource_map['res1/res2'] = SimpleHandle(2)
        assert 'res2' in resource_map.maps['res1'].handles
        assert 'res1' not in resource_map.handles
        assert 'res1' in resource_map.maps


class TestStaticResourceMap:

    def test_immutability(self):
        map_ = desper.StaticResourceMap()

        with pytest.raises(ValueError):
            map_.attr = 0

        with pytest.raises(ValueError):
            setattr(map_, 'attr', 0)

        with pytest.raises(AttributeError):
            map_.__dict__['attr'] = 0
