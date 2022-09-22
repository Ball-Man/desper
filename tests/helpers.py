from context import desper


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

    def process(self):
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

    def process(self):
        pass


def is_sorted(seq) -> bool:
    """Check if the given iterable is sorted (uses lte comparison)."""
    if not seq:
        return True

    prev_element = seq[0]
    for element in seq[1:]:
        if prev_element > element:
            print(prev_element, element)
            return False
        prev_element = element

    return True
