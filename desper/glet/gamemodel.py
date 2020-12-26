import os.path as pt
import __main__

import desper
import desper.glet as dg
import desper.glet.keyboard as kbd
import desper.glet.mouse as mouse

import pyglet


DEFAULT_RES_ROOT = 'res'


class GletGameModel(desper.GameModel):
    """A pyglet-centered implementation for :class:`GameModel`.

    This class has a behaviour similar to :class:`GameModel`, but has
    some extra attributes. In particular, it works using pyglet's data
    structures.

    It's designed to work with :py:mod:`desper.graphics` objects, but
    any System/Component can be used.

    For more info, see :class:`GameModel`.
    """

    def __init__(self, dirs=[], importer_dict={}, window=None,
                 event_handlers=(kbd.state, mouse.state), fps=60):
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
        :param event_handlers: An iterable of event handlers for pyglet
                               ``Window``. They will be applied using
                               ``set_handlers``. The given defaults will
                               manage the basic events for desper
                               (updating the keyboard).
        """
        super().__init__(dirs, importer_dict)

        if window is None:
            window = pyglet.window.Window()

        self.window = window    # `pyglet.window.Window` instance

        self.window.set_handlers(*event_handlers)

        self.fps = 60

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
        if self._waiting_world_handle is not None:
            self._finalize_switch()

        self._current_world.process(self)

        # print(pyglet.clock.get_fps())

        if self.quit:
            self.quit = False
            pyglet.app.exit()

    def _draw(self):
        self.window.clear()
        if self._current_world is not None:
            self.get_batch(self._current_world).draw()

    def loop(self):
        """Start the main loop.

        To stop the loop, set `quit` to True. Before calling this,
        initialize the current world with `switch`.

        :raises AttributeError: If the current world isn't initialized.
        """
        self.window.set_handler('on_draw', self._draw)
        if self.fps is None or self.fps <= 0:
            pyglet.clock.schedule(self._iteration)
        else:
            pyglet.clock.schedule_interval(self._iteration, 1 / self.fps)

        pyglet.app.run()

    def switch(self, world_handle, cur_reset=False, dest_reset=False,
               immediate=False):
        """Switch to a new world.

        Optionally, reset the current world handle before leaving.

        :raises TypeError: If world_handle isn't a :class:`Handle` type
                           or the inner world isn't a
                           :class:`esper.World` implementation.
        :param world_handle: The world handle instance to game should
                      switch.
        :param cur_reset: Whether the current world handle should be
                          reset before switching.
        :param dest_reset: Whether the destination world handle should
                           be reset before switching.
        :param immediate: If set to ``True``, :py:attr:`current_world`
                          and :py:attr:`current_world_handle` will be
                          immediately set to the new values.
                          If set to ``False``, the attributes will be
                          set to the new values at the beginning of the
                          next game iteration.
                          Be aware that switching immediately will
                          cause any other execution in the current
                          iteration that relies on
                          :py:attr:`current_world` (or its handle)
                          to retrieve misleading information(they will
                          basically believe for that frame of time that
                          their current world is the destination one,
                          while being part of the previous).
        """
        super().switch(world_handle, cur_reset, dest_reset, immediate)

    def _finalize_switch(self):
        # Clear batches
        if self._waiting_cur_reset and self._current_world in self._batches:
            del self._batches[self._current_world]
        if self._waiting_dest_reset \
           and self._waiting_world_handle is not None \
           and self._waiting_world_handle.loaded \
           and self._waiting_world_handle.get() in self._batches:
            dest_world = self._waiting_world_handle.get()
            del self._batches[dest_world]

        super()._finalize_switch()

        self.get_batch()        # Cache a new batch for the cur World


class DefaultGletGameModel(GletGameModel):
    """Default implementation of GameModel for pyglet.

    This model defines by default a project structure that loads
    pyglet media files, static images, animations, fonts and worlds
    from the ``res`` directory (the default subdirectories names are
    specified in :py:mod:`).
    The directory is automatically searched at the game project's root.

    A ``pyglet.window.Window`` is the only required addition.

    FPS is automatically fixed to 60 by default.
    """

    def __init__(self, window, fps=60):
        importer_dict = desper.importer_dict_builder \
            .add_rule(dg.get_font_importer(), desper.IdentityHandle) \
            .add_rule(dg.get_animation_importer(), dg.AnimationHandle) \
            .add_rule(dg.get_image_importer(), dg.ImageHandle) \
            .add_rule(dg.get_media_importer(), dg.MediaHandle) \
            .add_rule(desper.get_world_importer(), dg.GletWorldHandle, 1) \
            .build()

        super().__init__(window=window, fps=fps,
                         dirs=[pt.join(pt.dirname(__main__.__file__),
                                       DEFAULT_RES_ROOT)],
                         importer_dict=importer_dict)
