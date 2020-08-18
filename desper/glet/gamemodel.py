import desper

import pyglet


class GletGameModel(desper.GameModel):
    """A pyglet-centered implementation for :class:`GameModel`.

    This class has a behaviour similar to :class:`GameModel`, but has
    some extra attributes. In particular, it works using pyglet's data
    structures.

    It's designed to work with :py:mod:`desper.graphics` objects, but
    any System/Component can be used.

    For more info, see :class:`GameModel`.
    """

    def __init__(self, dirs=[], importer_dict={}, window=None):
        """Construct a new GletGameModel.

        For more info about `importer_dict` and `dirs` see
        :class:`GameModel`.

        :param dirs: The list of base directories used for the
                     resources's lookup.
        :param importer_dict: The dictionary of functions used to load
                              the :class:`Hook` s.
        :param window: A `pyglet.window.Window` instance of a window,
                       used by the game. If omitted the GameModel will
                       create a standard one.
        """
        super().__init__(dirs, importer_dict)

        if window is None:
            window = pyglet.window.Window()

        self.window = window    # `pyglet.window.Window` instance

        # Dict of `pyglet.graphics.Batch`. All the game render should
        # be added to this batches to optimize performance.
        # Different render order for different graphic components can
        # be achived with groups
        # (accessible using :py:meth:`get_order_group`).
        # Batches can be accessed with :py:meth:`get_batch`, which
        # requires a `World` instance(`esper.World` or any derived class
        # such as :class:`AbstractWorld`).
        self._batches = {}

        # Dict of `pyglet.graphics.OrderedGroup`. Managed internally
        # to optimize GPU batches. The user can get a specific group
        # (matching an integer) with :py:meth:`get_order_group`.
        self._groups = {}

    def get_order_group(self, order):
        """Get a `pyglet.graphics.OrderedGroup` based on the given order.

        The use of this method instead of manually creating a new
        `pyglet.graphics.OrderedGroup` is because it will reuse groups
        with the same order, limiting the draw calls for each batch.

        :param order: The integer value that defines the render order
                      assigned to the wanted group. High values are
                      foreground, low values are background(negative
                      values are accepted).

        :return: The `pyglet.graphics.OrderedGroup` associated with the
                 given order value.
        """
        group = self._groups.get(order, None)

        if group is None:
            group = self._groups[order] = pyglet.graphics.OrderedGroup(order)

        return group

    def get_batch(self, world=None):
        """Get the rendering batch associated to the given `World`.

        In order to get something correctly drawn on screen the correct
        rendering `Batch` should be used(instance of
        `pyglet.graphics.Batch`). Using this method you can get the
        correct render `Batch` for the given `World`.

        :param world: The `esper.World` instance to retrieve the `Batch`
                      for. By default, the current `World` is taken.
        :return: The `pyglet.graphics.Batch` associated to the given
                 `World`.
        """
        if world is None:
            world = self._current_world

        batch = self._batches.get(world, None)

        if batch is None:
            batch = self._batches[world] = pyglet.graphics.Batch()

        return batch

    def _iteration(self, dt):
        """Used as iteration inside the main loop."""
        # Render clear
        self.window.clear()

        self._current_world.process(self)

        # print(pyglet.clock.get_fps())

        if self.quit:
            self.quit = False
            pyglet.app.exit()

    def loop(self):
        """Start the main loop.

        To stop the loop, set `quit` to True. Before calling this,
        initialize the current world with `switch`.

        :raises AttributeError: If the current world isn't initialized.
        """
        pyglet.clock.schedule(self._iteration)
        pyglet.app.run()

    def switch(self, world_handle, reset=False):
        """Switch to a new world.

        Optionally, reset the current world handle before leaving.

        :raises TypeError: If world_handle isn't a :class:`Handle` type
                           or the inner world isn't a
                           :class:`esper.World` implementation.
        :param world_handle: The world handle instance to game should
                      switch.
        :param reset: Whether the current world handle should be.
        """
        super().switch(world_handle, reset)

        self.get_batch()        # Cache a new batch for the cur World


class EventHandler:
    """Decorator for pyglet window events.

    Instances of this class are callable, and can be used as decorators.
    An instance of EventHandler also encapsulates a
    ``pyglet.window.Window`` and when used as decorator will ensure that
    the newly created instance is added as an event handler using
    ``pyglet.window.Window.push_handlers``.

    An instance of this class will be automatically constructed at
    :py:attr:`event_handler` .
    """

    def __init__(self, window=None):
        self.window = window

    def __call__(self, cls, *args, **kwargs):
        """Decorator implementation.

        For details on how this works, see :class:`EventHandler`.
        """
        def decorated_constructor():
            # If no window is set, notify
            if not isinstance(self.window, pyglet.window.Window):
                raise TypeError('"window" argument not set or invalid type. '
                                + 'Expected: pyglet.window.Window')

            instance = cls(*args, **kwargs)
            self.window.push_handlers(instance)

            return instance

        return decorated_constructor


event_handler = EventHandler()
"""Convenience instance of :class:`EventHandler`, usable as decorator.

Keep in mind that for this to work the correctly
``pyglet.window.Window`` has to be added to the handler using
:py:meth:`EventHandler.event_handler` .
"""
