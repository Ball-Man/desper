"""Loop management module."""
import abc
import time
from typing import Optional, TypeVar, Generic, Callable, SupportsFloat

import desper
from desper.events import EventDispatcher
from desper.logic import World
from desper.model import Handle

_T = TypeVar('T')

ON_QUIT_EVENT_NAME = 'on_quit'
ON_SWITCH_OUT_EVENT_NAME = 'on_switch_out'
ON_SWITCH_IN_EVENT_NAME = 'on_switch_in'


def quit_loop(target: Optional[EventDispatcher] = None):
    """Quit currently running loop and dispatch an event accordingly.

    Event :attr:`ON_QUIT_EVENT_NAME` is dispatched on the specified
    :class:`EventDispatcher` before quitting the loop. If not specified,
    the default global :attr:`desper.core.loop` will be used to infer
    the current running world. If a custom loop is used, it is advisable
    to specify the world manually.

    Quitting is signaled by raising a :class:`Quit` exception.
    """
    if target is None:
        target = desper.default_loop.current_world

    if target is not None:
        target.dispatch(ON_QUIT_EVENT_NAME)
    raise Quit()


def switch(target_handle: Handle[World], clear_current=False, clear_next=False,
           from_world: Optional[World] = None):
    """Switch to the given world, contained in the specified handle.

    Event :attr:`ON_SWITCH_OUT_EVENT` is dispatched in the world being
    left. Two parameters are expected, being the world being left and
    the world being entered.
    :attr:`ON_SWITCH_IN_EVENT` is dispatched in the world being entered.
    Two parameters are expected (as above). If there is no world to
    leave, ``None`` is passed as first parameter.

    If specified, the handle being left and/or the handle being entered
    can be cleared.

    Switching is signaled by raising a :class:`SwitchWorld` exception.
    For this reason, it not globally supported. It is supported by
    :class:`SimpleLoop` and similar implementations.
    """
    if from_world is None:
        from_world = desper.default_loop.current_world

    to_world = target_handle()

    if from_world is not None:
        from_world.dispatch(ON_SWITCH_OUT_EVENT_NAME, from_world, to_world)
        # Disable switched out worlds for a more synchronized behaviour
        from_world.dispatch_enabled = False

    # To have more control in the order of execution, temporarily
    # disable dispatching on the target world. It will be enabled again
    # as soon as the loop catches the exception.
    to_world.dispatch_enabled = False
    to_world.dispatch(ON_SWITCH_IN_EVENT_NAME, from_world, to_world)

    raise SwitchWorld(target_handle, clear_current=clear_current,
                      clear_next=clear_next)


class Quit(Exception):
    """Raise to quit the main loop.

    Supported by all :class:`Loop` implementations.
    """


class SwitchWorld(Exception):
    """Raise to switch from the current world to a new one.

    This exception carries information that is catched by the main
    loop and interpreted to perform a world switch.

    Supported by :class:`SimpleLoop` and similar implementations.
    """

    def __init__(self, world_handle: Handle, clear_current=False,
                 clear_next=False):
        self.world_handle = world_handle
        self.clear_current = clear_current
        self.clear_next = clear_next


class Loop(abc.ABC, Generic[_T]):
    """Base class for loop management.

    A loop keeps track of and executes a world. While the world instance
    can in general be of any type, desper will only provide specific
    implementations towards the :class:`World` class.

    Specialized subclasses shall implement the :meth:`loop` method,
    where the actual loop is expected to take place.

    The world which is currently being executed can be queried with
    :attr:`current_world`, and can be internally switched at any time
    with the :meth:`_switch` method.
    """
    _current_world: Optional[_T] = None
    _current_world_handle: Optional[Handle[_T]] = None
    running: bool = False

    def start(self):
        """Setup internal state and start the main loop.

        Wraps :meth:`loop`. If a :class:`Quit` exception is catched,
        quits the loop.
        """
        self.running = True
        try:
            self.loop()
        except Quit:
            self.running = False

    @abc.abstractmethod
    def loop(self):
        """Execute the main loop.

        Subclass to define custom behaviour.
        """

    def switch(self, world_handle: Handle[_T], clear_current=False,
               clear_next=False):
        """Switch current world.

        :attr:`current_world` is updated with the content of the given
        handle.

        If specified, the current handle can be cleared before switching
        to the next one. Accordingly, the next one can be cleared before
        being executed.
        """
        assert isinstance(world_handle, Handle), \
            '%s is not of type %s' % (world_handle, Handle[_T])
        assert isinstance(clear_current, bool), \
            '%s is not of type bool'
        assert isinstance(clear_next, bool), \
            '%s is not of type bool'

        if clear_current and self._current_world_handle is not None:
            self._current_world_handle.clear()

        if clear_next:
            world_handle.clear()

        self._current_world_handle = world_handle
        self._current_world = world_handle()

        assert isinstance(self._current_world, World), \
            '%s is not of type World' % self._current_world

    @property
    def current_world(self) -> Optional[_T]:
        return self._current_world

    @property
    def current_world_handle(self) -> Optional[Handle[_T]]:
        return self._current_world_handle


class SimpleLoop(Loop[World]):
    """Simple specialized loop implementation for desper worlds.

    Process current world once per iteration, computing delta time.
    First delta time value is always ``0``. A custom function can be
    passed for time evaluation.

    :class:`SwitchWorld` exceptions are catched and managed to switch
    accordingly to a new world.
    """

    def __init__(self, time_function: Callable[
            [], SupportsFloat] = time.perf_counter):
        self.time_function = time_function
        self.last_timestamp = None

    def start(self):
        """Setup and start the main loop.

        See :meth:`Loop.start` for more details.
        """
        super().start()
        self.last_timestamp = None

    def loop(self):
        """Simple main loop.

        Process current world once per iteration, computing delta
        time. First delta time value is always ``0``.

        :class:`SwitchWorld` exceptions are catched and managed to
        switch accordingly to a new world.
        """
        while True:
            try:
                timestamp = self.time_function()
                if self.last_timestamp is None:
                    dt = 0
                else:
                    dt = timestamp - self.last_timestamp
                self.last_timestamp = timestamp

                self._current_world.process(dt)

            except SwitchWorld as ex:
                self.switch(ex.world_handle, ex.clear_current, ex.clear_next)

    def switch(self, world_handle: Handle[World], clear_current=False,
               clear_next=False):
        """Switch world and ensure correct dispatching of events.

        See :meth:`Loop._switch` for the basic behaviour.
        """
        super().switch(world_handle, clear_current, clear_next)

        world_handle().dispatch_enabled = True
