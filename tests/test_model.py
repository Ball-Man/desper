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

    map1 = desper.ResourceMap()
    map2 = desper.ResourceMap()
    map3 = desper.ResourceMap()

    map_.maps['map1'] = map1
    map1.parent = map_
    map1.key = 'map1'

    map1.maps['map2'] = map2
    map2.parent = map1
    map2.key = 'map2'

    map_.maps['map2'] = map3
    map3.parent = map_
    map3.key = 'map2'

    maps = [map_, map1, map2, map3]

    for m in maps:
        m.handles.update({'res1': SimpleHandle(1), 'res2': SimpleHandle(2)})
        for key, handle in m.handles.items():
            handle.parent = m
            handle.key = key

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

    def test_clear(self, resource_map):
        # Test submap clear
        submap_name = 'map1'
        submap = resource_map.maps[submap_name]
        subresources = [*submap.maps.values(), *submap.handles.values()]
        submap.clear()

        for res in subresources:
            assert res.parent is None
            assert res.key is None

        assert submap.parent == resource_map
        assert submap.key == submap_name

        assert not submap.maps
        assert not submap.handles

        # Test entire tree clear
        resource_map.clear()

        assert submap.parent is None
        assert submap.key is None

        assert not resource_map.handles
        assert not resource_map.maps


class TestStaticResourceMap:

    def test_immutability(self):
        val = 99

        map_ = SimpleStaticMap(val)

        with pytest.raises(ValueError):
            map_.attr = 0

        with pytest.raises(ValueError):
            setattr(map_, 'attr', 0)

        with pytest.raises(AttributeError):
            map_.__dict__['attr'] = 0

        with pytest.raises(ValueError):
            del map_.attr

    def test_getitem(self, uncached_handle):
        map_ = SimpleStaticMap(uncached_handle)

        assert map_.attr == uncached_handle()

        map_ = SimpleStaticMap(SimpleStaticMap(uncached_handle))

        assert type(map_.attr) is SimpleStaticMap
        assert map_.attr.attr == uncached_handle()

    def test_getattribute(self, uncached_handle):
        map_ = SimpleStaticMap(uncached_handle)

        assert map_['attr'] == uncached_handle()

        map_ = SimpleStaticMap(SimpleStaticMap(uncached_handle))

        assert type(map_['attr']) is SimpleStaticMap
        assert map_['attr']['attr'] == uncached_handle()

    def test_get(self, uncached_handle):
        map_ = SimpleStaticMap(uncached_handle)

        assert map_.get('attr') == uncached_handle
