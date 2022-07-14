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
