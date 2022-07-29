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
