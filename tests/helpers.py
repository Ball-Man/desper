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


@desper.event_handler(on_add='on_add2')
class SimpleHandlerComponent(SimpleComponent):
    on_add_triggered = False
    entity = None
    world = None

    def on_add2(self, entity, world):
        self.on_add_triggered = True
        self.entity = entity
        self.world = world
