"""Keep track of the mouse state.

Access :py:attr:`state` using the code of the wanted mouse button to
get its state. Currently, the state is ``True`` if the button is being
pressed, ``False`` otherwise.

Access :py:attr:`state` with key :py:attr:`X` or :py:attr:`Y` to get
the last recorded position of the mouse(relative to the current window).
"""
import pyglet
from pyglet.window.mouse import *


X = 10
Y = 11

class MouseStateHandler(pyglet.window.mouse.MouseStateHandler):
    """Expansion of the pyglet handler.

    Keeps track of the buttons' states and of the x and y coordinates.

    Use :py:attr:`X` and :py:attr:`Y` as index to get the last recorded
    x and y coordinates of the mouse (relative to the window).
    """

    def on_mouse_motion(self, x, y, dx, dy):
        self[X] = x
        self[Y] = y

    def on_mouse_drag(self, x, y, dx, dy, buttons, mods):
        self[X] = x
        self[Y] = y


state = MouseStateHandler()
