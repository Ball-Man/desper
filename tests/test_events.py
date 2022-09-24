from context import desper
from helpers import *

import gc

import pytest


class TestEventDispatcher:

    def test_add_handler(self):
        dispatcher = desper.EventDispatcher()

        # Test typing
        with pytest.raises(AssertionError):
            dispatcher.add_handler(100)

        handler = SimpleHandler()
        dispatcher.add_handler(handler)

        # Test weak references
        del handler
        gc.collect()

    def test_is_handler(self):
        dispatcher = desper.EventDispatcher()

        # Test failing case
        handler = SimpleHandler()
        assert not dispatcher.is_handler(handler)

        # Test real case
        dispatcher.add_handler(handler)
        assert dispatcher.is_handler(handler)

    def test_remove_handler(self):
        dispatcher = desper.EventDispatcher()

        # Test removal of an foreign handler (shall remain silent)
        handler1 = SimpleHandler()
        dispatcher.remove_handler(handler1)

        # Test removal of a known handler
        handler2 = SimpleHandler()
        dispatcher.add_handler(handler1)
        dispatcher.add_handler(handler2)

        dispatcher.remove_handler(handler1)

        assert not dispatcher.is_handler(handler1)
        assert dispatcher.is_handler(handler2)

        dispatcher.remove_handler(handler2)
        assert not dispatcher.is_handler(handler2)

    def test_dispatch(self):
        dispatcher = desper.EventDispatcher()

        # Test missing event (shall remain silent)
        dispatcher.dispatch('event_name', 0, 1, 2, x=10)

        # Test actual usage with some interested and some uninterested
        # handlers
        handler1 = SimpleHandler()
        handler2 = SimpleHandler()
        handler_uninterested = SimpleHandler2()
        dispatcher.add_handler(handler1)
        dispatcher.add_handler(handler2)
        dispatcher.add_handler(handler_uninterested)

        dispatcher.dispatch('event_name')

        assert handler1.received
        assert handler2.received
        assert handler_uninterested.received == 0

        # Test correct disassociation after a removal
        dispatcher.remove_handler(handler1)
        dispatcher.dispatch('event_name')

        assert handler1.received == 1
        assert handler2.received == 2
        assert handler_uninterested.received == 0

    def test_dispatch_disabled(self):
        dispatcher = desper.EventDispatcher()
        dispatcher.dispatch_enabled = False

        handler = SimpleHandler()
        dispatcher.add_handler(handler)

        dispatcher.dispatch('event_name')

        assert len(dispatcher._event_queue) == 1
        assert handler.received == 0

        dispatcher.dispatch_enabled = True

        assert handler.received == 1
        assert not dispatcher._event_queue

    def test_remove_handler_during_event(self):
        dispatcher = desper.EventDispatcher()
        handler = RemovingHandler()

        dispatcher.add_handler(handler)

        dispatcher.dispatch('event_name', dispatcher)
        assert not dispatcher.is_handler(handler)

    def test_clear(self):
        dispatcher = desper.EventDispatcher()
        handler = SimpleHandler()

        dispatcher.dispatch_enabled = False
        dispatcher.add_handler(handler)
        dispatcher.dispatch('event_name')

        dispatcher.clear()

        assert dispatcher.dispatch_enabled
        assert not dispatcher.is_handler(handler)
        assert handler.received == 0


def test_event_handler():
    # Some random events to test the handler on
    event_list = ['ev1', 'ev2']
    event_mappings = {'ev3': 'k', 'ev4': 'z'}

    @desper.event_handler(*event_list, **event_mappings)
    class Handler:
        pass

    handler = Handler()

    # Check simple listed events
    for event in event_list:
        assert handler.__events__[event] == event

    # Check event mappings
    for event, method in event_mappings.items():
        assert handler.__events__[event] == method

    # Test inheritance
    new_event_list = ['ev10']
    new_event_mappings = {'ev1': 'p'}
    # Conflicting events shall be overwritten

    @desper.event_handler(*new_event_list, **new_event_mappings)
    class Handler2(Handler):
        pass

    handler2 = Handler2()

    for event in event_list + new_event_list:
        assert event in handler2.__events__

    for event, method in (event_mappings | new_event_mappings).items():
        assert event in handler2.__events__

    # Check for overwritten events
    for event, method in new_event_mappings.items():
        assert handler2.__events__[event] == method
