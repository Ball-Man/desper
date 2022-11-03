"""Spatial positioning utilities."""
from desper.core.events import EventDispatcher
import desper.math as dmath

ON_POSITION_CHANGE_EVENT_NAME = 'on_position_change'
ON_ROTATION_CHANGE_EVENT_NAME = 'on_rotation_change'
ON_SCALE_CHANGE_EVENT_NAME = 'on_scale_change'


class Transform2D(EventDispatcher):
    """Spatial component: position, rotation and scale in a 2D world.

    These values are encapsuled through three main properties:
    :attr:`position`, :attr:`rotation` and :attr:`scale`.

    An event is dispatched when one of these properties undergoes a
    change.

    :attr:`position` changes dispatch
    :attr:`ON_POSITION_CHANGE_EVENT_NAME`. :attr:`rotation` changes
    dispatch :attr:`ON_ROTATION_CHANGE_EVENT_NAME`. :attr:`scale`
    changes dispatch :attr:`ON_SCALE_CHANGE_EVENT_NAME`.

    For all three events a single parameter is supported, which is the
    new property's value.
    """
    _position: dmath.Vec2 = dmath.Vec2()
    _rotation: float = 0
    _scale: dmath.Vec2 = dmath.Vec2(1., 1.)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.dispatch(ON_POSITION_CHANGE_EVENT_NAME, value)

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        self.dispatch(ON_ROTATION_CHANGE_EVENT_NAME, value)
