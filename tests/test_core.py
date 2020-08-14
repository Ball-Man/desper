import os
import os.path as pt
import inspect

from helpers import *
from context import desper
from desper import core
from desper.core import _signature

import pytest


@pytest.fixture
def world():
    return core.AbstractWorld()


@pytest.fixture
def gamemodel():
    model = core.GameModel()
    w = core.AbstractWorld()
    w.add_processor(core.AbstractProcessor())
    model.res['testworld'] = WorldHandle(w)
    model.switch(model.res['testworld'])
    return model

# Test functions


def test_abstract_get_component(world):
    range_ = 500

    for i in range(range_):
        world.create_entity(ComponentA())
    for i in range(range_):
        world.create_entity(ComponentB())

    comp_a_len = 0
    for en, comp in world.get_component(ComponentA):
        assert type(en) == int
        comp_a_len += 1

    comp_b_len = 0
    for en, comp in world.get_component(ComponentB):
        assert type(en) == int
        comp_b_len += 1

    assert comp_a_len == range_ * 2
    assert comp_b_len == range_


def test_entity_for_component(world):
    component = ComponentD()
    entity = world.create_entity(component)

    assert world.component_for_entity(entity, ComponentC) == component
    with pytest.raises(KeyError):
        world.component_for_entity(entity, ComponentA)

    component2 = ComponentC()
    world.add_component(entity, component2)

    assert type(world.component_for_entity(entity, ComponentC)) is ComponentC


def test_try_component(world):
    component = ComponentD()
    entity = world.create_entity(component)

    assert world.try_component(entity, ComponentC) == component
    assert world.try_component(entity, ComponentA) is None

    component2 = ComponentC()
    world.add_component(entity, component2)

    assert type(world.try_component(entity, ComponentC)) is ComponentC


def test_abstract_processor(world):
    range_update = 50

    entity1 = world.create_entity(ComponentC())
    entity2 = world.create_entity(ComponentD())

    world.add_processor(core.AbstractProcessor())

    for i in range(range_update):
        world.process()

    assert world.try_component(entity1, ComponentC).val == range_update
    assert world.try_component(entity2, ComponentD).val == (ComponentD.INIT_VAL
                                                   + range_update)


def test_has_component(world):
    entity = world.create_entity()

    world.add_component(entity, ComponentB())

    assert world.has_component(entity, ComponentA)
    assert world.has_component(entity, ComponentB)
    assert not world.has_component(entity, ComponentC)


def test_has_components(world):
    entity = world.create_entity()

    world.add_component(entity, ComponentA())
    world.add_component(entity, ComponentB())
    world.add_component(entity, ComponentC())

    assert world.has_components(entity, ComponentA, ComponentB)
    assert world.has_components(entity, ComponentB)
    assert not world.has_components(entity, ComponentC, ComponentD)
    assert not world.has_components(entity, ComponentD)


def test_remove_component(world):
    entity = world.create_entity(ComponentB(), ComponentA())

    world.remove_component(entity, ComponentA)

    assert len(world.components_for_entity(entity)) == 1
    assert type(world.components_for_entity(entity)[0]) is ComponentB


def test_handle():
    test_val = 10
    handle = SquareHandle(test_val)

    assert handle._value is None
    assert handle.get() == test_val ** 2
    assert handle._value == test_val ** 2
    assert handle.get() == test_val ** 2

    handle.clear()
    assert handle._value is None


def test_gamemodel_res(gamemodel):
    dirs = [pt.join(pt.dirname(__file__), pt.join('files', 'gamemodel_res'))]
    check_string = open(pt.dirname(__file__) + os.sep + 'files' + os.sep
                        + 'gamemodel_res' + os.sep + 'sounds.txt').read()

    # Try importing nothing
    import_dict = {accept_none: TextHandle}
    gamemodel.init_handles(dirs, import_dict)

    with pytest.raises(KeyError):
        gamemodel.res['sounds.txt']

    # Try importing sound files
    import_dict = {accept_sounds: TextHandle}
    gamemodel.init_handles(dirs, import_dict)

    assert gamemodel.res['sounds.txt'].get() == check_string
    with pytest.raises(KeyError):
        gamemodel.res['test.txt']

    # Try importing everything
    import_dict = {accept_all: TextHandle}
    gamemodel.init_handles(dirs, import_dict)

    assert type(gamemodel.res['test.txt']) is TextHandle


def test_gamemodel_res_no_extensions(gamemodel):
    dirs = [pt.join(pt.dirname(__file__), pt.join('files', 'gamemodel_res'))]
    import_dict = {accept_sounds: TextHandle}

    desper.options['resource_extensions'] = False

    gamemodel.init_handles(dirs, import_dict)

    desper.options['resource_extensions'] = True

    assert type(gamemodel.res['sounds']) is TextHandle
    with pytest.raises(KeyError):
        gamemodel.res['sounds.txt']


def test_gamemodel_quit_loop(gamemodel):
    w = gamemodel.current_world_handle.get()
    entity = w.create_entity(ModelComponent())

    gamemodel.loop()

    assert w.component_for_entity(entity, ModelComponent).var == 11


def test_gamemodel_switch(gamemodel, world):
    gamemodel.res['testworld'].get().create_entity(ModelComponent())
    gamemodel.res['testworld2'] = WorldHandle(world)

    component = ModelComponent()
    world.create_entity(component)
    world.add_processor(core.AbstractProcessor())

    assert gamemodel.current_world_handle == gamemodel.res['testworld']
    assert gamemodel.current_world == gamemodel.res['testworld'].get()
    gamemodel.loop()

    assert component.var == 0

    gamemodel.switch(gamemodel.res['testworld2'])
    assert gamemodel.current_world_handle == gamemodel.res['testworld2']
    assert gamemodel.current_world == gamemodel.res['testworld2'].get()
    gamemodel.loop()

    assert component.var == 11


def test_loose_signature():
    sig = _signature.LooseSignature([
        inspect.Parameter('x', inspect.Parameter.POSITIONAL_OR_KEYWORD)])

    def fun1(y):
        pass

    def fun2(x, y):
        pass

    assert sig == inspect.signature(fun1)
    assert inspect.signature(fun1) == sig
    assert sig != inspect.signature(fun2)


def test_on_attach(world):
    comp = OnAttachComponent()
    en = world.create_entity(comp)

    assert comp.entity == en
    assert comp.world == world
