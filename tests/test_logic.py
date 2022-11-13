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


def test_get_component(populated_world, population):
    for entity, components in population.items():
        for component in components:
            controller = SimpleController(entity, populated_world)
            assert desper.get_component(controller, type(component)) \
                   is component


def test_get_components(populated_world, population):
    for entity, components in population.items():
        controller = SimpleController(entity, populated_world)
        assert set(desper.get_components(controller)) == set(components)


def test_delete(populated_world, population):
    for entity in population:
        controller = SimpleController(entity, populated_world)
        desper.delete(controller)
        assert not populated_world.entity_exists(entity)


def test_build_controller(populated_world, population):
    for entity in population:
        controller = desper.controller(entity, populated_world)
        assert isinstance(controller, desper.ControllerProtocol)
        assert controller.entity == entity
        assert controller.world == populated_world


class TestController:

    def test_event(self, world):
        controller = desper.Controller()
        entity = world.create_entity(controller)

        assert controller.entity == entity
        assert controller.world == world


class TestComponentReference:

    def test_get(self, populated_world, population):
        entity = tuple(population)[0]
        controller = ControllerWithReference()
        populated_world.add_component(entity, controller)

        assert controller.simple_component \
            is populated_world.get_component(entity, SimpleComponent)

    def test_set(self, populated_world, population):
        entity = tuple(population)[0]
        controller = ControllerWithReference()
        populated_world.add_component(entity, controller)
        old_simple_component = populated_world.get_component(
            entity, SimpleComponent)

        simple_component = SimpleComponent()
        controller.simple_component = simple_component

        assert controller.simple_component is simple_component
        assert controller.simple_component is not old_simple_component

    def test_delete(self, populated_world, population):
        entity = tuple(population)[0]
        controller = ControllerWithReference()
        populated_world.add_component(entity, controller)
        simple_component = populated_world.get_component(
            entity, SimpleComponent)

        del controller.simple_component

        assert simple_component not in controller.get_components()
        assert type(controller.simple_component) is not SimpleComponent


class TestProcessorReference:

    def test_get(self, populated_world, population):
        entity = tuple(population)[0]
        controller = ControllerWithReference()
        populated_world.add_component(entity, controller)

        assert controller.simple_processor \
            is populated_world.get_processor(SimpleProcessor)

    def test_set(self, populated_world, population):
        old_simple_processor = populated_world.get_processor(SimpleProcessor)

        entity = tuple(population)[0]
        controller = ControllerWithReference()
        populated_world.add_component(entity, controller)

        simple_processor = SimpleProcessor()
        controller.simple_processor = simple_processor

        assert controller.simple_processor is simple_processor
        assert controller.simple_processor is not old_simple_processor

    def test_delete(self, populated_world, population):
        entity = tuple(population)[0]
        controller = ControllerWithReference()
        populated_world.add_component(entity, controller)
        simple_processor = populated_world.get_processor(SimpleProcessor)

        del controller.simple_processor

        assert simple_processor not in populated_world.processors
        assert type(controller.simple_processor) is not SimpleProcessor


def test_prototype(world):
    val = 1432

    entity = world.create_entity(*SimplePrototype(val))

    assert world.get_component(entity, SimpleComponent) is not None
    assert world.get_component(entity, SimpleComponent2) is not None
    assert world.get_component(entity, SimpleChildComponent) is None


class TestTransform2D:

    def test_position(self, world):
        transform_listener = TransformListener()
        transform = desper.Transform2D()
        transform.add_handler(transform_listener)
        world.create_entity(transform_listener, transform)

        position_delta = (1, 1)
        transform.position += position_delta

        assert transform_listener.position == position_delta
        assert transform_listener.position == transform.position

    def test_rotation(self, world):
        transform_listener = TransformListener()
        transform = desper.Transform2D()
        transform.add_handler(transform_listener)
        world.create_entity(transform_listener, transform)

        rotation_delta = 42
        transform.rotation += rotation_delta

        assert transform_listener.rotation == rotation_delta
        assert transform_listener.rotation == transform.rotation

    def test_scale(self, world):
        transform_listener = TransformListener()
        transform = desper.Transform2D()
        transform.add_handler(transform_listener)
        world.create_entity(transform_listener, transform)

        scale_delta = (1, 1)
        transform.scale += scale_delta

        assert transform_listener.scale == desper.math.Vec2(1, 1) + scale_delta
        assert transform_listener.scale == transform.scale


class TestTransform3D:

    def test_position(self, world):
        transform_listener = TransformListener()
        transform = desper.Transform3D()
        transform.add_handler(transform_listener)
        world.create_entity(transform_listener, transform)

        position_delta = (1, 1, 1)
        transform.position += position_delta

        assert transform_listener.position == position_delta
        assert transform_listener.position == transform.position

    def test_rotation(self, world):
        transform_listener = TransformListener()
        transform = desper.Transform3D()
        transform.add_handler(transform_listener)
        world.create_entity(transform_listener, transform)

        rotation_delta = (42, 42, 42)
        transform.rotation += rotation_delta

        assert transform_listener.rotation == rotation_delta
        assert transform_listener.rotation == transform.rotation

    def test_scale(self, world):
        transform_listener = TransformListener()
        transform = desper.Transform3D()
        transform.add_handler(transform_listener)
        world.create_entity(transform_listener, transform)

        scale_delta = (1, 1, 1)
        transform.scale += scale_delta

        assert (transform_listener.scale
                == desper.math.Vec3(1, 1, 1) + scale_delta)
        assert transform_listener.scale == transform.scale


class TestCoroutineProcessor():

    def test_start(self):
        proc = desper.CoroutineProcessor()
        component = CoroutineComponent()
        coroutine1 = component.coroutine()
        promise1 = proc.start(coroutine1)

        assert promise1.processor is proc
        assert promise1.generator is coroutine1
        assert promise1.value is None

        coroutine2 = proc.start(component.coroutine2()).generator
        proc.start(component.coroutine3())

        with pytest.raises(TypeError):
            proc.start(None)

        for _ in range(5):
            proc.process(1)

        assert component.counter == 0
        with pytest.raises(ValueError):
            proc.start(coroutine1)
        with pytest.raises(ValueError):
            proc.start(coroutine2)

        for _ in range(6):
            proc.process(1)

        assert component.counter == 1
        assert promise1.value == 10
        assert component.counter2 == 11

        proc.start(coroutine1)

    def test_kill(self):
        proc = desper.CoroutineProcessor()
        component = CoroutineComponent()
        coroutine1 = proc.start(component.coroutine()).generator
        proc.start(component.coroutine2())
        coroutine3 = proc.start(component.coroutine3()).generator

        with pytest.raises(TypeError):
            proc.kill(None)

        for _ in range(5):
            proc.process(1)

        proc.kill(coroutine3)
        with pytest.raises(ValueError):
            proc.kill(coroutine3)

        for _ in range(6):
            proc.process(1)

        with pytest.raises(ValueError):
            proc.kill(coroutine1)

        proc.start(coroutine3)

    def test_state(self):
        proc = desper.CoroutineProcessor()
        component = CoroutineComponent()

        gen0 = component.coroutine()
        assert proc.state(gen0) == desper.CoroutineState.TERMINATED

        gen1 = proc.start(component.coroutine()).generator
        gen2 = proc.start(component.coroutine2()).generator

        proc.process(1)

        assert proc.state(gen1) == desper.CoroutineState.PAUSED
        assert proc.state(gen2) == desper.CoroutineState.ACTIVE

        for _ in range(10):
            proc.process(1)

        assert proc.state(gen1) == desper.CoroutineState.TERMINATED
        assert proc.state(gen2) == desper.CoroutineState.ACTIVE

    def test_timer(self):
        proc = desper.CoroutineProcessor()
        component = CoroutineComponent()

        old_coroutine = None
        for i in range(100):
            coroutine = proc.start(component.coroutine()).generator
            for _ in range(6):
                proc.process(1)

            if old_coroutine is not None:
                with pytest.raises(ValueError):
                    proc.kill(old_coroutine)

            with pytest.raises(ValueError):
                proc.start(coroutine)

            old_coroutine = coroutine

    def test_free(self):
        coroutine_number = 10

        proc = desper.CoroutineProcessor()
        component = CoroutineComponent()

        coroutines = [component.coroutine() for i in range(coroutine_number)]
        for cor in coroutines:
            proc.start(cor)

        for _ in range(11):
            proc.process(1)

        for cor in coroutines:
            with pytest.raises(ValueError):
                proc.kill(cor)


class TestCoroutinePromise:

    def generator(self):
        yield 1
        return 10

    def test_init(self):
        generator = self.generator()
        processor = desper.CoroutineProcessor()
        value = 100
        promise = desper.CoroutinePromise(generator, processor, value)

        assert promise.generator is generator
        assert promise.processor is processor
        assert promise.value is value

    def test_kill(self):
        processor = desper.CoroutineProcessor()
        generator = self.generator()

        promise = processor.start(generator)

        promise.kill()
        assert (processor.state(promise.generator)
                == desper.CoroutineState.TERMINATED)

    def test_state(self):
        processor = desper.CoroutineProcessor()
        generator = self.generator()

        promise = processor.start(generator)

        assert promise.state == processor.state(promise.generator)

        processor.process(1)

        assert promise.state == processor.state(promise.generator)

        processor.process(1)

        assert promise.state == processor.state(promise.generator)
        assert promise.value == 10


def test_coroutine_decorator(world):
    world.add_processor(desper.CoroutineProcessor())

    @desper.coroutine
    def coroutine(world=world):
        yield

    promise = coroutine()

    assert promise.state == desper.CoroutineState.ACTIVE


def test_coroutine_decorator_default_loop():
    handle = SimpleWorldHandle()
    handle().add_processor(desper.CoroutineProcessor())
    desper.default_loop.switch(handle)

    @desper.coroutine
    def coroutine():
        yield

    promise = coroutine()
    assert promise.state == desper.CoroutineState.ACTIVE

    @desper.coroutine
    def coroutine(world=None):
        yield

    promise = coroutine()
    assert promise.state == desper.CoroutineState.ACTIVE
