from .events import *       # NOQA
from .model import *        # NOQA
from .logic import *        # NOQA
from .loop import *         # NOQA

# Default global loop object.
# To simplify most common user cases, a loop object is constructed
# by default and will automatically be used by desper functions if
# different behaviour is not specified.
default_loop = SimpleLoop()
