from context import desper
from desper import data

import pytest


@pytest.fixture
def world():
    return data.AbstractWorld()

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

    world.add_processor(data.AbstractProcessor())

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

# Helpers


class ComponentA(data.AbstractComponent):
    pass


class ComponentB(ComponentA):
    pass


class ComponentC(data.AbstractComponent):

    def __init__(self):
        self.val = 0

    def update(self, world):
        self.val += 1


class ComponentD(ComponentC):
    INIT_VAL = 20

    def __init__(self):
        self.val = ComponentD.INIT_VAL
