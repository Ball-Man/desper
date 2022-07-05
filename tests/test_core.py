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
