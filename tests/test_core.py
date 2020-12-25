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
    model.res['testworld'] = WorldHandle()
    w = model.res['testworld'].get()
    w.add_processor(core.AbstractProcessor())
    model.switch(model.res['testworld'], immediate=True)
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


def test_gamemodel_init_handles(gamemodel):
    dirs = [pt.join(pt.dirname(__file__), 'files')]
    importer_dict = {accept_all: core.IdentityHandle}
    gamemodel.init_handles(dirs, importer_dict)

    gamemodel.res['gamemodel_res']['test.txt']
    with pytest.raises(KeyError):
        gamemodel.res['gamemodel_res']['test2.txt']

    dirs = [pt.join(pt.dirname(__file__), pt.join('files', 'fakefiles'))]
    gamemodel.init_handles(dirs, importer_dict)

    gamemodel.res['gamemodel_res']['test.txt']
    gamemodel.res['gamemodel_res']['test2.txt']


def test_gamemodel_quit_loop(gamemodel):
    w = gamemodel.current_world_handle.get()
    entity = w.create_entity(ModelComponent())

    gamemodel.loop()

    assert w.component_for_entity(entity, ModelComponent).var == 11


def test_gamemodel_switch(gamemodel):
    gamemodel.res['testworld'].get().create_entity(ModelComponent())
    gamemodel.res['testworld2'] = WorldHandle()
    testworld = gamemodel.current_world
    testworld2 = gamemodel.res['testworld2'].get()

    component = ModelComponent()
    testworld2.create_entity(component)
    testworld2.add_processor(core.AbstractProcessor())

    assert gamemodel.res['testworld'].get() == testworld
    assert gamemodel.current_world_handle == gamemodel.res['testworld']
    assert gamemodel.current_world == gamemodel.res['testworld'].get()
    gamemodel.loop()

    assert component.var == 0
    gamemodel.switch(gamemodel.res['testworld2'], cur_reset=True,
                     immediate=True)
    assert gamemodel.res['testworld'].get() != testworld

    assert gamemodel.current_world_handle == gamemodel.res['testworld2']
    assert gamemodel.current_world == gamemodel.res['testworld2'].get()
    gamemodel.loop()

    gamemodel.switch(gamemodel.res['testworld'])
    gamemodel.res['testworld'].get().add_processor(core.AbstractProcessor())
    gamemodel.res['testworld'].get().create_entity(ModelComponent())
    assert gamemodel.current_world_handle == gamemodel.res['testworld2']
    assert gamemodel.current_world == gamemodel.res['testworld2'].get()
    gamemodel.loop()

    assert gamemodel.current_world_handle == gamemodel.res['testworld']
    assert gamemodel.current_world == gamemodel.res['testworld'].get()

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


def test_importer_dict_builder(gamemodel):
    dic = core.importer_dict_builder.add_rule(accept_all, SquareHandle, 1) \
                                    .add_rule(accept_all_2, TextHandle, 0) \
                                    .build()

    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files' + pt.sep
                            + 'gamemodel_res')],
                           dic)

    assert isinstance(gamemodel.res['sounds.txt'], TextHandle)
    assert isinstance(gamemodel.res['test.txt'], TextHandle)


def test_controller_component(gamemodel):
    world = gamemodel.res['testworld'].get()
    controller = ControllerComponent()
    entity = world.create_entity(controller, ComponentA(), 10)

    assert isinstance(controller.get(ComponentA), ComponentA)
    assert isinstance(controller.get(ComponentA), ComponentA)
    with pytest.raises(KeyError):
        controller.get(ComponentB)

    world.remove_component(entity, ComponentA)
    with pytest.raises(KeyError):
        controller.get(ComponentA)

    with pytest.raises(TypeError):
        controller.get(int)


def test_controller_processor(gamemodel):
    world = gamemodel.res['testworld'].get()
    controller = ControllerComponent()
    world.create_entity(controller)
    processor = ProcessorA()
    world.add_processor(processor)

    assert controller.processor(ProcessorA) is processor
    assert controller.processor(ProcessorA) is processor
    assert controller.processor(ProcessorB) is None


def test_coroutine_processor_start():
    proc = core.CoroutineProcessor()
    component = CoroutineComponent()
    coroutine1 = proc.start(component.coroutine())
    coroutine2 = proc.start(component.coroutine2())
    proc.start(component.coroutine3())

    with pytest.raises(TypeError):
        proc.start(None)

    for _ in range(5):
        proc.process()

    assert component.counter == 0
    with pytest.raises(ValueError):
        proc.start(coroutine1)
    with pytest.raises(ValueError):
        proc.start(coroutine2)

    for _ in range(6):
        proc.process()

    assert component.counter == 1
    assert component.counter2 == 11

    proc.start(coroutine1)


def test_coroutine_processor_kill():
    proc = core.CoroutineProcessor()
    component = CoroutineComponent()
    coroutine1 = proc.start(component.coroutine())
    proc.start(component.coroutine2())
    coroutine3 = proc.start(component.coroutine3())

    with pytest.raises(TypeError):
        proc.kill(None)

    for _ in range(5):
        proc.process()

    proc.kill(coroutine3)
    with pytest.raises(ValueError):
        proc.kill(coroutine3)

    for _ in range(6):
        proc.process()

    with pytest.raises(ValueError):
        proc.kill(coroutine1)

    proc.start(coroutine3)


def test_coroutine_processor_state():
    proc = core.CoroutineProcessor()
    component = CoroutineComponent()

    gen0 = component.coroutine()
    assert proc.state(gen0) == core.CoroutineState.TERMINATED

    gen1 = proc.start(component.coroutine())
    gen2 = proc.start(component.coroutine2())

    proc.process()

    assert proc.state(gen1) == core.CoroutineState.PAUSED
    assert proc.state(gen2) == core.CoroutineState.ACTIVE

    for _ in range(10):
        proc.process()

    assert proc.state(gen1) == core.CoroutineState.TERMINATED
    assert proc.state(gen2) == core.CoroutineState.ACTIVE


def test_coroutine_processor_timer():
    proc = core.CoroutineProcessor()
    component = CoroutineComponent()

    old_coroutine = None
    for i in range(100):
        coroutine = proc.start(component.coroutine())
        for _ in range(6):
            proc.process()

        if old_coroutine is not None:
            with pytest.raises(ValueError):
                proc.kill(old_coroutine)

        with pytest.raises(ValueError):
            proc.start(coroutine)

        old_coroutine = coroutine


def test_coroutine_processor_free():
    coroutine_number = 10

    proc = core.CoroutineProcessor()
    component = CoroutineComponent()

    coroutines = [component.coroutine() for i in range(coroutine_number)]
    for cor in coroutines:
        proc.start(cor)

    for _ in range(11):
        proc.process()

    for cor in coroutines:
        with pytest.raises(ValueError):
            proc.kill(cor)


def test_prototypes(world):
    entity = world.create_entity(*Prototype1())

    assert world.try_component(entity, ComponentA) is not None
    assert world.try_component(entity, ComponentB) is not None
    assert world.try_component(entity, ComponentC) is None

    entity2 = world.create_entity(*Prototype2(10, 11))

    assert world.try_component(entity2, ComponentArgs1) is not None
    assert world.try_component(entity2, ComponentArgs2) is not None
    assert world.try_component(entity2, ComponentA) is not None
