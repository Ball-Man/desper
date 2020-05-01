"""A cross-platform lightweight game developement toolkit.

The main aim is letting the dev get to choose the balance between
ease-of-use out of the box and high customization based on specific
needs.

Desper implements a slim set of tools to create the working structure of
a game, but specific scopes are delegated to external libraries(e.g.
graphics). The subsystems can be adapted to any external library,
allowing for high customization. Desper also comes with some pre-written
modules which rely on some well-known open source projects.

To keep everything at its core, desper keeps as small as possible its
set of dependencies.
"""
from .core import *
