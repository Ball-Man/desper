"""Loop management module."""
import abc
import time
from typing import Optional, TypeVar, Generic, Callable, SupportsFloat

from desper.core.logic import World
from desper.core.model import Handle

_T = TypeVar('T')


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
    _current_world: Optional[_T]
    _current_world_handle: Optional[Handle[_T]]

    def start(self):
        """Setup internal state and start the main loop.

        Wraps :meth:`loop`. If a :class:`Quit` exception is catched,
        quits the loop.
        """
        try:
            self.loop()
        except Quit:
            pass

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

        world_handle().dispatching_enabled = True
