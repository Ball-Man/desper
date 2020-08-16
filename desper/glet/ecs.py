import pyglet
import esper


class ActivePosition:
    """ECS component used to manage the position of an entity."""

    def __init__(self, x, y, z=0):
        """Create a new position at x, y[, z]."""
        self.x = x
        self.y = y
        self.z = z


class ActiveSpriteProcessor(esper.Processor):
    """ECS system that manages how `pyglet.sprite.Sprite` s move.

    This system will update the position of any `pyglet.sprite.Sprite`
    based on the value of :class:`ActivePosition`.

    If an entity has no `pyglet.sprite.Sprite`, or has no
    :class:`ActivePosition`, no action will be taken.
    `Sprite` s without :class:`ActivePosition` are called "passive".

    Note: Don't manually update the position using
    `pyglet.sprite.Sprite.x` or `y` since it's by far less efficient.
    Use a :class:`ActiveComponent` instead.
    """

    def process(self, *args, **kwargs):
        for ent, (sprite, pos) in self.world.get_components(
                pyglet.sprite.Sprite, ActivePosition):
            if sprite.position != (pos.x, pos.y):
                sprite.position = (pos.x, pos.y)


class Camera:
    """ECS component used to define a rendering camera."""

    def __init__(self, x=0, y=0, viewport=None, zoom=1):
        """Construct a camera with the given properties.

        Note that for all coordinates, point (0, 0) is bottom-left.

        :param x: The x coordinate(position) of the camera(defaults to
                  0).
        :param y: The y coordinate(position) of the camera(defaults to
                  0)..
        :param viewport: A vector of 4 elements(x, y, width, height)
                         representing the viewport of the camera on
                         screen(0,0 is bottom-left). Defaults to None(
                         which means the whole window).
        :param zoom: The zoom of the camera(1 means no zoom, and it's
                     set as default).
        """
        self.x = x
        self.y = y
        self.viewport = viewport
        self.zoom = zoom


class CameraProcessor(esper.Processor):
    """ECS system that renders cameras on screen.

    Warning: This processor `assumes` the use of a
    :class:`GletGameModel`, and won't work otherwise.
    """

    def __init__(self):
        super().__init__()

        self._batch = None

    def process(self, model, *args, **kwargs):
        for _, camera in self.world.get_component(Camera):
            # Retrieve batch to be drawn
            if self._batch is None:
                self._batch = model.get_batch(self.world)

            # Transform according to camera
            pyglet.gl.glTranslatef(-camera.x * camera.zoom,
                                   -camera.y * camera.zoom, 0)
            pyglet.gl.glScalef(camera.zoom, camera.zoom, 1)
            if camera.viewport is not None:
                pyglet.gl.glViewport(*camera.viewport)

            self._batch.draw()      # Actual draw

            # Transform back
            if camera.viewport is not None:
                pyglet.gl.glViewport(0, 0, model.window.width,
                                     model.window.height)
            pyglet.gl.glScalef(1 / camera.zoom, 1 / camera.zoom, 1)
            pyglet.gl.glTranslatef(camera.x * camera.zoom,
                                   camera.y * camera.zoom, 0)
