"""Default resources for worlds."""
from collections import deque
from typing import Callable

from desper.core.model import Handle
from desper.core.logic import World

ON_WORLD_LOAD_EVENT_NAME = 'on_world_load'


class WorldHandle(Handle[World]):
    """Base class for loading :class:`World` resources.

    An implementation of :meth:`load` is provided. Such implementation
    creates an empty :class:`World` (event dispatching disabled) and
    executes an ordered list of functions on it.

    Such functions are stored in :attr:`transform_functions`. Each
    function shall accept two arguments,
    the world handle (``self``) and the :class:`World` instance being
    loaded. Return values are discarded. Despite the name, any
    callable that meets the listed requirements is accepted (not only
    functions).

    The :attr:`ON_WORLD_LOAD_EVENT_NAME` event is dispatched at last.
    This happens after the entire execution of :meth:`load`. This event
    accepts two arguments, the world handle (``self``) and the
    :class:`World` instance being loaded.
    """

    def __init__(self):
        self.transform_functions: deque[
            Callable[['WorldHandle', World], None]] = deque()

    def load(self) -> World:
        """Create and return a new :class:`World`.

        Event dispatching is disabled by default. Transform functions
        are executed in order.

        At last, :attr:`ON_WORLD_LOAD_EVENT_NAME` is dispatched.
        """
        world = World()
        world.dispatch_enabled = False

        # Execute transform functions
        for transform_function in self.transform_functions:
            transform_function(self, world)

        world.dispatch(ON_WORLD_LOAD_EVENT_NAME, self, world)

        return world
