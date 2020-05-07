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
