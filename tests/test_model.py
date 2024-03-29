from context import desper
from helpers import *

import inspect

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


@pytest.fixture
def world_dict():
    return {
        'processors': [
            {
                'type': SimpleProcessor
            }
        ],

        'entities': [
            {
                'components': [
                    {
                        'type': SimpleComponent,
                        'args': [42]
                    }
                ],
            },
            {
                'id': 'string id',
                'components': [
                    {
                        'type': SimpleComponent,
                        'kwargs': {'val': 1}
                    },
                    {
                        'type': SimpleChildComponent
                    }
                ]
            }
        ]
    }


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

    def test_get_static_map(self, resource_map):
        static_map = resource_map.get_static_map()

        # Test generated hierarchy
        assert static_map.res1 is static_map['res1']
        assert static_map.map1 is static_map['map1']
        assert static_map.map1.map2 is static_map['map1']['map2']
        assert static_map.map1.map2.res1 is static_map['map1']['map2']['res1']

        assert static_map.get('res1') == resource_map.get('res1')
        assert (static_map.get('map1').get('map2').get('res1')
                == resource_map.get('map1/map2/res1'))


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


def test_world_handle():
    handle = desper.WorldHandle()
    handle.transform_functions.append(
        lambda h, w: w.create_entity(OnWorldLoadHandler()))

    assert not handle().dispatch_enabled

    _, handler = handle().get(OnWorldLoadHandler)[0]
    assert handler.world is None
    assert handler.handle is None

    handle().dispatch_enabled = True
    assert handle is handler.handle
    assert handle() is handler.world


def test_populate_world_from_dict(world_dict):
    world = desper.World()

    desper.populate_world_from_dict(world, {})
    assert not world.entities
    assert not world.processors

    desper.populate_world_from_dict(world, world_dict)
    assert populated_world_dict_verify(world, world_dict)


def test_world_from_file_transformer():
    transformer = desper.WorldFromFileTransformer(
        [dict_transformer_simple_type])

    world = desper.World()
    transformer(
        desper.WorldFromFileHandle(get_filename('files', 'simple_world.json')),
        world)

    assert world.get_processor(SimpleProcessor) is not None
    assert world.get(SimpleComponent)
    assert world.get(SimpleChildComponent)


def test_object_from_string():
    assert inspect.ismodule(desper.object_from_string('collections'))
    assert inspect.isclass(desper.object_from_string('collections.ChainMap'))

    with pytest.raises(ModuleNotFoundError):
        desper.object_from_string('xxxx')

    with pytest.raises(AttributeError):
        desper.object_from_string('collections.xxxx')


def test_type_dict_transformer():
    transformer = desper.WorldFromFileTransformer(
        [desper.type_dict_transformer])

    world = desper.World()
    transformer(
        desper.WorldFromFileHandle(
            get_filename('files', 'simple_world_namespace.json')),
        world)

    assert world.get(SimpleComponent)
    assert world.get(SimpleChildComponent)
    assert world.get_processor(SimpleProcessor) is not None


def test_object_dict_transformer():
    transformer = desper.WorldFromFileTransformer(
        [dict_transformer_simple_type, desper.object_dict_transformer])

    world = desper.World()
    transformer(
        desper.WorldFromFileHandle(get_filename('files', 'simple_world.json')),
        world)

    assert (world.get_component("string id", SimpleComponent).val
            is SimpleComponent)


def test_resource_dict_transformer(resource_map):
    transformer = desper.WorldFromFileTransformer(
        [dict_transformer_simple_type, desper.resource_dict_transformer])

    world = desper.World()
    handle = desper.WorldFromFileHandle(
        get_filename('files', 'simple_world.json'))
    resource_map['world_handle'] = handle
    transformer(handle, world)

    assert (world.get_component("string id 2", SimpleComponent).val
            is resource_map['map1/map2/res1'])

    assert (world.get_component("string id 2", SimpleChildComponent).val
            is resource_map.get('map1/map2/res1'))


def test_default_processors_transformer():
    handle = desper.WorldHandle()
    world = handle()

    desper.default_processors_transformer(handle, world)

    assert world.get_processor(desper.OnUpdateProcessor) is not None
    assert world.get_processor(desper.CoroutineProcessor) is not None


def test_world_from_file_handle(resource_map):
    handle = desper.WorldFromFileHandle(
        get_filename('files', 'simple_world_namespace.json'))
    resource_map['world_handle'] = handle

    world = handle()

    print(tuple(map(lambda x: x.val, world.get_components("string id"))))

    assert world.get(SimpleComponent)
    assert world.get(SimpleChildComponent)
    assert world.get_processor(SimpleProcessor) is not None
    assert (world.get_component("string id", SimpleComponent).val
            is SimpleComponent)
    assert (world.get_component("string id 2", SimpleComponent).val
            is resource_map['map1/map2/res1'])

    assert (world.get_component("string id 2", SimpleChildComponent).val
            is resource_map.get('map1/map2/res1'))

    assert world.get_processor(desper.OnUpdateProcessor) is not None
    assert world.get_processor(desper.CoroutineProcessor) is not None


def test_project_path():
    components = 'a', 'b', 'c'

    assert desper.project_path(*components).endswith(pt.join(*components))

    desper.project_path()


class TestDirectoryResourcePopulator:

    def test_add_rule(self, nest=True):
        populator = desper.DirectoryResourcePopulator(
            get_filename('files', 'fake_project'), nest_on_conflict=nest)

        populator.add_rule('dir', FilenameHandle, 'args', kwarg='kwarg')
        populator.add_rule('dir2', lambda filename: SimpleWorldHandle())
        populator.add_rule('dir3', FilenameHandle, file_exts=['.xml'])

        assert populator.rules[0].directory_path == 'dir'
        assert populator.rules[0].handle_type is FilenameHandle
        assert populator.rules[0].args == ('args',)
        assert populator.rules[0].kwargs == {'kwarg': 'kwarg'}

        assert populator.rules[1].directory_path == 'dir2'
        assert populator.rules[1].args == ()
        assert populator.rules[1].kwargs == {}

        assert populator.rules[2].directory_path == 'dir3'
        assert populator.rules[2].args == ()
        assert populator.rules[2].kwargs == {}

        return populator

    def test_call(self, resource_map):
        populator = self.test_add_rule()

        populator(resource_map)

        assert resource_map['dir/file1'].val == (
            'file1', ('args',), {'kwarg': 'kwarg'})

        assert resource_map['dir/subdir/file2'].val == (
            'file2', ('args',), {'kwarg': 'kwarg'})

        # .txt should have been filtered out
        assert resource_map['dir3/file1.xml']
        assert resource_map.get('dir3/file2.txt') is None

        assert resource_map.get('dir2') is None

    def test_call_root_override(self, resource_map):
        populator = self.test_add_rule()

        populator(resource_map, root=get_filename('files', 'fake_project2'))

        assert resource_map['dir/file1'].val == (
            'file1', ('args',), {'kwarg': 'kwarg'})

        assert resource_map['dir/subdir/file2'].val == (
            'file2', ('args',), {'kwarg': 'kwarg'})

        assert resource_map['dir/project2'].val == (
            'project2', ('args',), {'kwarg': 'kwarg'})

        assert resource_map.get('dir2') is None

    def test_call_conflicting_nest(self, resource_map):
        populator = self.test_add_rule(nest=True)

        populator(resource_map)
        populator(resource_map)

        assert len(resource_map['dir'].handles.maps) == 2
        for map_ in resource_map['dir'].handles.maps:
            assert 'file1' in map_ and isinstance(map_['file1'], desper.Handle)

    def test_call_conflicting_nest_override(self, resource_map):
        populator = self.test_add_rule(nest=False)

        populator(resource_map, nest_on_conflict=True)
        populator(resource_map, nest_on_conflict=True)

        assert len(resource_map['dir'].handles.maps) == 2
        for map_ in resource_map['dir'].handles.maps:
            assert 'file1' in map_ and isinstance(map_['file1'], desper.Handle)

    def test_call_conflicting_no_nest(self, resource_map):
        populator = self.test_add_rule(nest=False)

        populator(resource_map)
        populator(resource_map)

        assert len(resource_map['dir'].handles.maps) == 1

    def test_call_conflicting_no_nest_override(self, resource_map):
        populator = self.test_add_rule(nest=True)

        populator(resource_map, nest_on_conflict=False)
        populator(resource_map, nest_on_conflict=False)

        assert len(resource_map['dir'].handles.maps) == 1

    def test_call_trim_extensions_override(self, resource_map):
        populator = self.test_add_rule(nest=False)

        populator(resource_map, trim_extensions=True)

        assert resource_map.get('dir/file1')
        assert resource_map.get('dir/subdir/file2')
        assert resource_map.get('dir3/file1')
