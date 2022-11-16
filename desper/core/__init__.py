from .events import *       # NOQA
from .model import *        # NOQA
from .logic import *        # NOQA
from .loop import *         # NOQA

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
