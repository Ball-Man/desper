from context import desper
from helpers import *

import pytest


@pytest.fixture
def simple_loop():
    return desper.SimpleLoop()


class TestSimpleLoop:

    def test_switch(self, simple_loop):
        handle = SimpleWorldHandle()
        simple_loop.switch(handle)

        assert simple_loop.current_world is handle()
        assert simple_loop.current_world_handle is handle

    def test_quit(self, simple_loop):
        handle = SimpleWorldHandle()
        simple_loop.switch(handle)

        simple_loop.start()

    def test_switch_clear(self, simple_loop):
        handle1 = SimpleWorldHandle()
        handle2 = SimpleWorldHandle()
        simple_loop.switch(handle1)
        world1 = handle1()

        simple_loop.switch(handle2, clear_current=True)
        assert world1 is not handle1()

    def test_start(self, simple_loop):
        handle = SimpleWorldHandle()
        simple_loop.switch(handle)

        simple_loop.start()

        assert simple_loop.current_world.get_processor(
            SimpleProcessor).processed == 1
