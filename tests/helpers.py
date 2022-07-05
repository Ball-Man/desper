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
