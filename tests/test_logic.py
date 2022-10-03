from context import desper
from helpers import *

import pytest


@pytest.fixture
def world():
    return desper.World()


@pytest.fixture
def population():
    return {
        1: [SimpleChildComponent(), SimpleComponent()],
        2: [SimpleChildComponent()],
        3: [SimpleComponent()],
        4: [SimpleComponent2()],
        5: [SimpleHandlerComponent()]
    }


@pytest.fixture
def processors():
    return [SimpleProcessor(), SimpleHandlerProcessor()]


@pytest.fixture
def populated_world(population, processors):
    world = desper.World()

    for entity, components in population.items():
        world.create_entity(*components)

    for processor in processors:
        world.add_processor(processor)

    return world


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

    def test_entity_exists(self, populated_world, population):
        for entity in population:
            assert populated_world.entity_exists(entity)

        assert not populated_world.entity_exists(max(population) + 1)

    def test_entities(self, populated_world, population):
        assert populated_world.entities == tuple(population)

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

        replacing_component = SimpleHandlerComponent()
        world.add_component(entity, replacing_component)
        assert component.on_remove_triggered

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

    def test_get(self, populated_world, population):
        for entity, component in populated_world.get(SimpleComponent):
            assert component in population[entity]

        query_result = populated_world.get(SimpleComponent)
        for entity, components in population.items():
            for component in components:
                if isinstance(component, SimpleComponent):
                    assert entity, component in query_result

    def test_get_component(self, populated_world, population):
        for entity, components in population.items():
            for component in components:
                assert populated_world.get_component(
                    entity, type(component)) == component

    def test_get_components(self, populated_world, population):
        for entity, components in population.items():
            assert set(components) == set(
                populated_world.get_components(entity))

        assert len(populated_world.get_components(max(population) + 1)) == 0

    def test_remove_component(self, populated_world, population):
        for entity, components in population.items():
            # Assumes that components is in "subclass" order, that is,
            # any components that are subtype of others are listed
            # before them.
            for component in components:
                assert populated_world.has_component(
                    entity, type(component))
                assert populated_world.remove_component(
                    entity, type(component)) == component
                assert not populated_world.has_component(
                    entity, type(component))

            assert populated_world.remove_component(
                next(iter(population.keys())),
                SimpleChildComponent) is None

    def test_remove_component_event_handling(self, populated_world,
                                             population):
        for entity, components in population.items():
            # Assumes that components is in "subclass" order, that is,
            # any components that are subtype of others are listed
            # before them.
            for component in components:
                removed = populated_world.remove_component(
                    entity, type(component))
                if isinstance(removed, SimpleHandlerComponent):
                    assert not populated_world.is_handler(removed)
                    assert removed.on_remove_triggered

    def test_remove_component_event_handling_disabled(self, populated_world,
                                                      population):
        populated_world.dispatch_enabled = False

        handlers = []
        for entity, components in population.items():
            for component in components:
                if isinstance(component, SimpleHandlerComponent):
                    handlers.append(component)

        self.test_remove_component(populated_world, population)

        for component in handlers:
            assert not component.on_remove_triggered

        populated_world.dispatch_enabled = True

        for component in handlers:
            assert component.on_remove_triggered

    def test_delete_entity_immediate(self, populated_world, population):
        for entity in population:
            populated_world.delete_entity(entity, immediate=True)
            assert not populated_world.entity_exists(entity)

        with pytest.raises(KeyError):
            populated_world.delete_entity(max(population) + 1, immediate=True)

    def test_delete_entity(self, populated_world, population):
        for entity in population:
            populated_world.delete_entity(entity)
            assert not populated_world.entity_exists(entity)

        populated_world.delete_entity(max(population) + 1)
        with pytest.raises(KeyError):
            populated_world.process()

    def test_delete_entity_event_handling(self, populated_world, population):
        actual_population = {entity: populated_world.get_components(entity)
                             for entity in population}

        for components in actual_population.values():
            for component in components:
                if isinstance(component, desper.EventHandler):
                    assert populated_world.is_handler(component)

        for entity in population:
            populated_world.delete_entity(entity)
        populated_world.process()

        for components in actual_population.values():
            for component in components:
                if isinstance(component, desper.EventHandler):
                    assert not populated_world.is_handler(component)

    def test_processors(self, populated_world, processors):
        for original, in_world in zip(sorted(processors, key=processor_key),
                                      populated_world.processors):
            assert type(original) is type(in_world)

    def test_add_processor(self, populated_world):
        new_processor = SimpleProcessor2()
        lowest_priority = min(populated_world.processors,
                              key=processor_key).priority - 1
        populated_world.add_processor(new_processor, lowest_priority)

        assert new_processor in populated_world.processors
        assert new_processor.world is populated_world
        assert is_sorted(populated_world.processors, key=processor_key)
        assert populated_world.processors[0] is new_processor

        # Test substitution of conflicting types processors
        substitute_processor = SimpleProcessor2()
        populated_world.add_processor(substitute_processor)

        assert new_processor not in populated_world.processors
        assert substitute_processor in populated_world.processors
        assert is_sorted(populated_world.processors, key=processor_key)

    def test_add_processor_event_handling(self, populated_world):
        for processor in populated_world.processors:
            if isinstance(processor, desper.EventHandler):
                assert populated_world.is_handler(processor)
                assert processor.on_add_triggered

        new_processor = SimpleHandlerProcessor()
        assert not populated_world.is_handler(new_processor)
        assert not new_processor.on_add_triggered

        populated_world.add_processor(new_processor)
        assert populated_world.is_handler(new_processor)
        assert new_processor.on_add_triggered

    def test_remove_processor(self, populated_world):
        for processor in populated_world.processors:
            n_processors = len(populated_world.processors)

            assert populated_world.remove_processor(type(processor)) \
                   is processor
            assert processor not in populated_world.processors
            assert is_sorted(populated_world.processors, key=processor_key)

            assert len(populated_world.processors) == n_processors - 1

    def test_remove_processor_event_handling(self, populated_world):
        # Test replacement, the substituted
        handler_processor = None
        for processor in populated_world.processors:
            if isinstance(processor, SimpleHandlerProcessor):
                handler_processor = processor
                break
        assert handler_processor is not None
        assert populated_world.is_handler(handler_processor)

        populated_world.add_processor(SimpleHandlerProcessor())
        assert handler_processor.on_remove_triggered
        assert not populated_world.is_handler(handler_processor)

        for processor in populated_world.processors:
            if isinstance(processor, desper.EventHandler):
                assert populated_world.is_handler(processor)

                populated_world.remove_processor(type(processor))
                assert processor.on_remove_triggered
                assert not populated_world.is_handler(processor)

    def test_get_processor(self, populated_world):
        for processor in populated_world.processors:
            assert populated_world.get_processor(type(processor)) \
                   is processor

        # Test subtypes
        populated_world.remove_processor(SimpleProcessor)
        assert populated_world.get_processor(SimpleProcessor) is not None

        # Test empty results
        assert populated_world.get_processor(SimpleProcessor2) is None

    def test_process(self, populated_world):
        assert all(p.processed == 0 for p in populated_world.processors)

        populated_world.process()

        assert all(p.processed == 1 for p in populated_world.processors)

    def test_clear(self, populated_world, population):
        processors = populated_world.processors

        populated_world.clear()

        for entity in population:
            assert not populated_world.entity_exists(entity)

        for processor in processors:
            assert processor not in populated_world.processors

        assert populated_world.create_entity() == 1


def test_add_component(world):
    entity = world.create_entity()
    controller = SimpleController(entity, world)
    desper.add_component(controller, SimpleComponent())

    assert world.has_component(entity, SimpleComponent)


def test_remove_component(populated_world, population):
    for entity, components in population.items():
        component = components[0]
        controller = SimpleController(entity, populated_world)
        assert desper.remove_component(controller, type(component)) \
               is component
        assert not populated_world.has_component(entity, type(component))


def test_has_component(populated_world, population):
    for entity, components in population.items():
        for component in components:
            controller = SimpleController(entity, populated_world)
            assert desper.has_component(controller, type(component))


class TestController:

    def test_event(self, world):
        controller = desper.Controller()
        entity = world.create_entity(controller)

        assert controller.entity == entity
        assert controller.world == world
