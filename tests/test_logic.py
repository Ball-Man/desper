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

    def test_add_component_event_handling(self, world):
        entity = world.create_entity()
        component = SimpleHandlerComponent()
        world.add_component(entity, component)

        assert component.on_add_triggered
        assert component.entity == entity
        assert component.world == world
        assert world.is_handler(component)
