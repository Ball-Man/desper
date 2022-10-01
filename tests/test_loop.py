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
        world = handle()
        simple_loop.switch(handle)

        simple_loop.start()

        assert world is simple_loop.current_world and world is handle()

    def test_switch_clear(self, simple_loop):
        handle1 = SimpleWorldHandle()
        handle2 = SimpleWorldHandle()
        simple_loop.switch(handle1)
        world1 = handle1()

        # Test clear current
        simple_loop.switch(handle2, clear_current=True)
        world1_new = handle1()
        assert world1 is not world1_new

        # Test clear next
        simple_loop.switch(handle1, clear_next=True)
        assert simple_loop.current_world is not world1_new

    def test_start(self, simple_loop):
        handle = SimpleWorldHandle()
        simple_loop.switch(handle)

        simple_loop.start()

        assert simple_loop.current_world.get_processor(
            SimpleProcessor).processed == 1

    def test_switch_exception(self, simple_loop):
        handle1 = SimpleWorldHandle()
        handle2 = SimpleWorldHandle()

        handle1().add_processor(SwitchProcessor(handle2), -1)

        simple_loop.switch(handle1)
        simple_loop.start()

        assert simple_loop.current_world_handle is handle2

    def test_switch_exception_clear(self, simple_loop):
        handle1 = SimpleWorldHandle()
        handle2 = SimpleWorldHandle()

        # Test clear current
        handle1().add_processor(
            SwitchProcessor(handle2, clear_current=True), -1)

        simple_loop.switch(handle1)
        world1 = simple_loop.current_world
        simple_loop.start()

        world1_new = handle1()
        assert world1 is not world1_new

        # Test clear next
        handle2().add_processor(
            SwitchProcessor(handle1, clear_next=True), -1)
        simple_loop.start()

        assert world1_new is not handle1()

    def test_delta_time(self, simple_loop):
        handle = DeltaTimeWorldHandle()

        simple_loop.switch(handle)
        simple_loop.start()

        world = handle()
        processor = world.get_processor(DeltaTimeProcessor)

        assert processor.dt_list[0] == 0

        for dt in processor.dt_list[1:]:
            assert dt > 0

        # Test restarting
        simple_loop.start()

        assert processor.dt_list[0] == 0

    def test_running(self, simple_loop):
        handle = SimpleWorldHandle()

        simple_loop.switch(handle)
        assert not simple_loop.running
        simple_loop.start()

        assert not simple_loop.running


def test_quit(simple_loop):
    handle = QuitFunctionWorldHandle()
    simple_loop.switch(handle)

    simple_loop.start()

    assert handle().get_processor(QuitFunctionProcessor).on_quit_triggered
