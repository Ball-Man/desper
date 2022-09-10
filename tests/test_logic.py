from context import desper
from helpers import *

import pytest


@pytest.fixture
def world():
    return desper.World()


class TestWorld:

    def test_create_entity(self, world):
        entity1 = world.create_entity()
        entity2 = world.create_entity(SimpleChildComponent())

        assert not world.has_component(entity1, object)
        assert world.has_component(entity2, object)
        assert world.has_component(entity2, SimpleChildComponent)
        assert world.has_component(entity2, SimpleComponent)
        assert not world.has_component(entity2, SimpleComponent2)
        assert entity1 == 1
        assert entity2 == 2

    def test_create_entity_event_handling(self, world):
        component1_1 = SimpleHandlerComponent()
        component2_1 = SimpleHandlerComponent()
        components1 = [component1_1, component2_1]
        entity1 = world.create_entity(component1_1, component2_1)

        for component in components1:
            assert component.on_add_triggered
            assert component.entity == entity1
            assert component.world == world

        # Event handling when dispatching is disabled
        world.dispatch_enabled = False
        component1_2 = SimpleHandlerComponent()
        component2_2 = SimpleHandlerComponent()
        components2 = [component1_2, component2_2]
        entity2 = world.create_entity(component1_2, component2_2)

        for component in components2:
            assert not component.on_add_triggered

        world.dispatch_enabled = True

        for component in components2:
            assert component.on_add_triggered
            assert component.entity == entity2
            assert component.world == world

    def test_has_component(self, world):
        entity = world.create_entity(SimpleComponent())

        assert isinstance(world.has_component(entity, SimpleComponent), bool)
        assert isinstance(world.has_component(entity, SimpleComponent2), bool)

    def test_add_component(self, world):
        entity = world.create_entity()

        assert not world.has_component(entity, object)

        world.add_component(entity, SimpleComponent())

        assert world.has_component(entity, SimpleComponent)

        world.add_component(entity, SimpleComponent2())

        assert world.has_component(entity, SimpleComponent2)

    def test_event_handler(self, world):
        assert world.is_handler(world)

    def test_add_component_event_handling(self, world):
        entity = world.create_entity()
        component = SimpleHandlerComponent()
        world.add_component(entity, component)

        assert component.on_add_triggered
        assert component.entity == entity
        assert component.world == world
        assert world.is_handler(component)

        # Event handling when dispatching is disabled
        world.dispatch_enabled = False
        component2 = SimpleHandlerComponent()
        entity2 = world.create_entity()
        world.add_component(entity2, component2)

        assert not component2.on_add_triggered

        world.dispatch_enabled = True

        assert component2.on_add_triggered
        assert component2.entity == entity2
        assert component2.world == world
