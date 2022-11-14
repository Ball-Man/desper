import importlib
import os.path as pt
from typing import AnyStr

from .tree import *             # NOQA
from .world import *            # NOQA


def project_path(*names: AnyStr) -> AnyStr:
    """Return a path passing through the project root and given files.

    ``__main__`` is used to retrieve the absolute path of the project.
    This means that the "project root" is considered to be the directory
    where the program's entry point lies.
    """
    main = importlib.import_module('__main__')
    if main is not None and hasattr(main, '__file__'):
        project_dir = pt.dirname(main.__file__)

        if not names:
            return project_dir

        return pt.join(project_dir, *names)

    # If running in interactive mode, just return a relative path
    # to current working dir
    if not names:
        return '.'
    return pt.join(*names)
