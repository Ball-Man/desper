"""A Python3 game development toolkit for resource and logic management.

Desper implements a slim set of tools to create the working structure of
a game, but specific scopes are delegated to external libraries (e.g.
graphics).

In particular, the package provides:

- (Lazy) resource management (see :mod:`model`)
- Component and event based logics (see :mod:`logic`)
- Simple scene management (see :mod:`loop`)
- Easy interoperation with existing open source tools
"""
from .events import *       # NOQA
from .model import *        # NOQA
from .logic import *        # NOQA
from .loop import *         # NOQA

version = '1.1.1'

default_loop = SimpleLoop()
"""Default global loop object.

To simplify most common user cases, a loop object is constructed
by default and will automatically be used by desper functions if
different behaviour is not specified.
"""

resource_map = ResourceMap()
"""Default resource map container.

To simplify most common use cases, a default global resource map is
constructed. Users are encouraged to use this instance for global
project resources. Instancing a custom map is obviously always an
option, but it is unnecessary in common cases.
"""
