from context import desper

import os.path as pt
from collections import namedtuple


def get_filename(*path: str) -> str:
    """Get a path with respect to tests folder.

    Use varargs instead of slashes.
    """
    return pt.join(pt.dirname(__file__), *path)


class SimpleHandler:
    __events__ = {'event_name': 'event_method'}
    received = 0

    def event_method(self):
        self.received += 1


class SimpleHandler2:
    __events__ = {'another_event': 'event_method'}
    received = 0

    def event_method(self):
        self.received += 1


class RemovingHandler:
    __events__ = {'event_name': 'event_name'}

    def event_name(self, dispatcher: desper.EventDispatcher):
        dispatcher.remove_handler(self)


class SimpleHandle(desper.Handle):

    def __init__(self, value):
        self._value = value

    def load(self):
        return self._value * 2


class SimpleStaticMap(desper.StaticResourceMap):

    __slots__ = ['attr']

    def __init__(self, val):
        super().__init__()
        object.__setattr__(self, 'attr', val)

        if isinstance(val, desper.Handle):
            object.__setattr__(self, '_handle_names', frozenset(['attr']))


class SimpleComponent:

    def __init__(self, val=0):
        self.val = val


class SimpleChildComponent(SimpleComponent):
    pass


class SimpleComponent2:
    pass


@desper.event_handler(on_add='on_add2', on_remove='on_remove2')
class SimpleHandlerComponent(SimpleComponent):
    on_add_triggered = False
    entity = None
    world = None

    on_remove_triggered = False

    def on_add2(self, entity, world):
        self.on_add_triggered = True
        self.entity = entity
        self.world = world

    def on_remove2(self, entity, world):
        self.on_remove_triggered = True


class SimpleProcessor(desper.Processor):
    processed = 0

    def process(self, dt=1):
        self.processed += 1


@desper.event_handler('on_add', 'event_name', 'on_remove')
class SimpleHandlerProcessor(SimpleProcessor):
    on_add_triggered = False
    event_name_triggered = False
    on_remove_triggered = False

    def on_add(self):
        self.on_add_triggered = True

    def event_name(self):
        self.event_name_triggered = True

    def on_remove(self):
        self.on_remove_triggered = True


class SimpleProcessor2(desper.Processor):

    def process(self, dt=1):
        pass


class QuitProcessor(desper.Processor):

    def process(self, dt):
        raise desper.Quit()


@desper.event_handler(desper.ON_QUIT_EVENT_NAME)
class QuitFunctionProcessor(desper.Processor):
    on_quit_triggered = False

    def on_quit(self):
        self.on_quit_triggered = True

    def process(self, dt):
        desper.quit_loop(self.world)


class SwitchProcessor(desper.Processor):

    def __init__(self, target_handle, clear_current=False, clear_next=False):
        self.target_handle = target_handle
        self.clear_current = clear_current
        self.clear_next = clear_next

    def process(self, dt):
        raise desper.SwitchWorld(self.target_handle, self.clear_current,
                                 self.clear_next)


class SwitchFunctionProcessor(SwitchProcessor):

    def process(self, dt):
        desper.switch(self.target_handle, self.clear_current, self.clear_next,
                      from_world=self.world)


@desper.event_handler(desper.ON_SWITCH_IN_EVENT_NAME,
                      desper.ON_SWITCH_OUT_EVENT_NAME)
class SwitchEventsComponent:
    on_switch_in_triggered = False
    on_switch_out_triggered = False

    def on_switch_in(self, from_, to):
        self.on_switch_in_triggered = True

    def on_switch_out(self, from_, to):
        self.on_switch_out_triggered = True


class DeltaTimeProcessor(desper.Processor):

    def __init__(self, iterations=10):
        self.iterations = iterations
        self.dt_list = []

    def process(self, dt):
        # Store dt for a while and quit
        if self.iterations <= 0:
            raise desper.Quit()

        self.iterations -= 1
        self.dt_list.append(dt)


class SimpleWorldHandle(desper.Handle[desper.World]):

    def load(self) -> desper.World:
        world = desper.World()

        world.add_processor(SimpleProcessor())
        world.add_processor(QuitProcessor())

        return world


class SwitchFunctionWorldHandle(SimpleWorldHandle):

    def load(self) -> desper.World:
        world = super().load()

        world.create_entity(SwitchEventsComponent())

        return world


class DeltaTimeWorldHandle(desper.Handle[desper.World]):

    def load(self) -> desper.World:
        world = desper.World()

        world.add_processor(DeltaTimeProcessor())

        return world


class QuitFunctionWorldHandle(desper.Handle[desper.World]):

    def load(self) -> desper.World:
        world = desper.World()

        world.add_processor(QuitFunctionProcessor())

        return world


class FilenameHandle(desper.Handle[SimpleComponent]):

    def __init__(self, filename, *args, **kwargs):
        self.filename = filename
        self.args = args
        self.kwargs = kwargs

    def load(self) -> SimpleComponent:
        return SimpleComponent((pt.basename(self.filename),
                                self.args, self.kwargs))


def is_sorted(seq, key=None) -> bool:
    """Check if the given iterable is sorted (uses lte comparison)."""
    if not seq:
        return True

    # If a key function is specified, remap sequence
    if key is not None:
        seq = tuple(map(key, seq))

    prev_element = seq[0]
    for element in seq[1:]:
        if prev_element > element:
            print(prev_element, element)
            return False
        prev_element = element

    return True


def processor_key(processor):
    """Key function for comparison based functions on processors."""
    return processor.priority


SimpleController = namedtuple('SimpleController', ('entity', 'world'))


class ControllerWithReference(desper.Controller):
    simple_component = desper.ComponentReference(SimpleComponent)
    simple_processor = desper.ProcessorReference(SimpleProcessor)


class SimplePrototype(desper.Prototype):
    component_types = SimpleComponent, SimpleComponent2

    def __init__(self, val):
        self.val = val

    def init_SimpleComponent(self, cls):
        return cls(self.val)


@desper.event_handler('on_position_change', 'on_rotation_change',
                      'on_scale_change')
class TransformListener:
    position = None
    rotation = None
    scale = None

    def on_position_change(self, new_pos):
        self.position = new_pos

    def on_rotation_change(self, new_rot):
        self.rotation = new_rot

    def on_scale_change(self, new_scale):
        self.scale = new_scale


@desper.event_handler('on_world_load')
class OnWorldLoadHandler:
    world = None
    handle = None

    def on_world_load(self, handle, world):
        self.world = world
        self.handle = handle


def populated_world_dict_verify(world: desper.World, world_dict: dict) -> bool:
    """Verifiy that a world was correctly populated through given dict."""
    processors = world_dict['processors']
    entities = world_dict['entities']

    for processor_dict in processors:
        if world.get_processor(processor_dict['type']) is None:
            return False

    for entity_dict in entities:
        entity_id = entity_dict.get('id', None)
        if entity_id is None:
            continue            # How to test for unspecified ids..?

        for component_dict in entity_dict.get('components', []):
            if (world.get_component(entity_id, component_dict['type'])
                    is None):
                return False

    return True


def dict_transformer_simple_type(handle, world, initial_dict,
                                 passthrough_dict):
    passthrough_dict['type'] = globals()[passthrough_dict['type']]


class CoroutineComponent:

    def __init__(self):
        self.counter = 0
        self.counter2 = 0

    def coroutine(self):
        yield 10
        self.counter += 1
        return 10

    def coroutine2(self):
        while self.counter2 < 100:
            self.counter2 += 1
            yield

    def coroutine3(self):
        while True:
            yield 3
