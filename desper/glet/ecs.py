import pyglet
import esper


class Position:
    """ECS component used to manage the position of an entity.

    Other components/processor from this module might be using this
    to reference their position(e.g. :class:`Camera` /
    :class:`CameraProcessor`).
    """

    def __init__(self, x=0, y=0, z=0):
        """Create a new position at x, y[, z]."""
        self.x = x
        self.y = y
        self.z = z


class ActiveSpriteProcessor(esper.Processor):
    """ECS system that manages how `pyglet.sprite.Sprite` s move.

    This system will update the position of any `pyglet.sprite.Sprite`
    based on the value of :class:`Position`.

    If an entity has no `pyglet.sprite.Sprite`, or has no
    :class:`Position`, no action will be taken.
    `Sprite` s without :class:`Position` are called "passive".

    Note: Don't manually update the position using
    `pyglet.sprite.Sprite.x` or `y` since it's by far less efficient.
    """

    def process(self, *args, **kwargs):
        for ent, (sprite, pos) in self.world.get_components(
                pyglet.sprite.Sprite, Position):
            if sprite.position != (pos.x, pos.y):
                sprite.position = (pos.x, pos.y)


class ActivePositionProcessor(esper.Processor):
    """ECS system that manages active updates for positional components.

    Many components have a position of their own (x, y, eventually a z),
    and updating all the positions when necessary can be a pain.
    This processor updates all the given components types (accepted by
    the constructor) according to the :class:`Position` instance of
    their entity.

    Of course, if no :class:`Position` component is present for an
    entity, no updates will be done for that specific entity.

    The updated attributes are 'x' and 'y' (if specified in the
    constructor, 'z' too), so be sure that the wanted components
    do have these attributes. These names can be customized in the
    constructor.

    To update :class:`pyglet.sprite.Sprite` components
    :class:`ActiveSpriteProcessor` is recommended (more efficient).
    """

    def __init__(self, *args, x_name='x', y_name='y', z_name='z',
                 compute_z=False):
        self.to_update_types = args
        self.x_name = x_name
        self.y_name = y_name
        self.z_name = z_name

        self.compute_z = compute_z

    def process(self, *args):
        for ent, comps in self.world.get_components(Position,
                                                    *self.to_update_types):
            pos = comps[0]
            cc = comps[1:]

            # Update positions
            for comp in cc:
                if (pos.x, pos.y) != (getattr(comp, self.x_name),
                                      getattr(comp, self.y_name)):
                    setattr(comp, self.x_name, pos.x)
                    setattr(comp, self.y_name, pos.y)

            # Update z
            if self.compute_z:
                for comp in cc:
                    if pos.z != getattr(comp, self.z_name):
                        setattr(comp, self.z_name, pos.z)


class Camera:
    """ECS component used to define a rendering camera."""

    def __init__(self, viewport=None, zoom=1):
        """Construct a camera with the given properties.

        Note that for all coordinates, point (0, 0) is bottom-left.

        :param viewport: A vector of 4 elements(x, y, width, height)
                         representing the viewport of the camera on
                         screen(0,0 is bottom-left). Defaults to None(
                         which means the whole window).
        :param zoom: The zoom of the camera(1 means no zoom, and it's
                     set as default).
        """
        self.viewport = viewport
        self.zoom = zoom
