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


def test_try_component(world):
    component = ComponentD()
    entity = world.create_entity(component)

    assert world.try_component(entity, ComponentC) == component
    assert world.try_component(entity, ComponentA) is None

# def test_abstract_processor(world):
#     range_entity = 500
#     range_update = 50

#     for i in range(range_entity):
#         world.create_entity(ComponentC())
#     for i in range(range_entity):
#         world.create_entity(ComponentD())

#     world.add_processor(data.AbstractProcessor())

#     for i in range(range_update):
#         world.process()

#     for i in range(range_entity):
#         assert len(world.get_component(ComponentC))

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
