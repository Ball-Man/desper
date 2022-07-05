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
