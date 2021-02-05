"""Keep track of the keyboard state.

Access :py:attr:`state` using the code of the wanted key to get its
state. Currently, the state is ``True`` if the key is pressed, ``False``
otherwise.
"""
import pyglet
from pyglet.window.key import *

state = pyglet.window.key.KeyStateHandler()
