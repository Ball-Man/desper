import glob
import os
import os.path as pt
import inspect as insp
import collections.abc
from functools import reduce

from .res import Handle
from ._signature import LooseSignature
from .options import options


class GameModel:
    """A base class for game logic encapsulation.

    A GameModel is a master container containing "the whole game".
    The game is typically organized in one or multiple worlds. This
    worlds are contained, managed and loaded by a GameModel.

    A GameModel also manages the main game loop and contains useful
    data structures for resource usage and media(audio/video).

    Loaded resources can be accessed via the :py:attr:`res`
    attribute(int this implementation: a nested structure of
    dictionaries which keys are the directory names).
    """

    LAMBDA_SIG = LooseSignature(
        [insp.Parameter('resource_root', insp.Parameter.POSITIONAL_OR_KEYWORD),
         insp.Parameter('rel_path', insp.Parameter.POSITIONAL_OR_KEYWORD),
         insp.Parameter('model', insp.Parameter.POSITIONAL_OR_KEYWORD)])
    """``(resource_root: string, rel_path: string, model: GameModel) -> tuple``

    Where `resource_root` will be populated by the absolute path to
    one of the resource directories(an element of `dir`),
    `rel_path` will be populated by the relative path from the
    `resource_root` to the actual resource file and `resources` will
    be populated with :py:attr`res`(the dict of :class:`Handle`
    pointing to the already loaded resources).

    The lambda should return None if the given pathname doesn't
    refer to its specific resource type. It should return an
    iterable containing the parameters passed to the Handle
    constructor otherwise."""

    # Used for switching
    _waiting_world_handle = None
    _waiting_cur_reset = False
    _waiting_dest_reset = False

    _current_world = None
    _current_world_handle = None

    # Used to quit the loop
    quit = False

    def __init__(self, dirs=[], importer_dict={}):
        """Construct a new GameModel from an importer dictionary.

        An importer dictionary is in the form:
        ``{ lambda1: HandleType1, lambda2: HandleType2, ...}``
        and specifies which Handle implementation should be used to load
        specific resources. Which resources are actually loaded using
        which Handle is decided by passing the pathnames (recursively
        explored) of the `dirs` parameter to the lambdas in the dict.

        The correct lambda signature can be found at
        :py:attr:`GameModel.LAMBDA_SIG`

        Note: `dirs` will be scanned in the given order, which is very
        important when loading resources that rely on others(e.g.
        ``World`` ).

        :raises TypeError: If the functions in `importer_dict` don't
                           match :py:attr:`GameModel.LAMBDA_SIG`.
        :param dirs: A list of directory paths that will be recursively
                     scanned in search of resources.
        :param importer_dict: A dictionary that associates regex
                              patterns to Handle implementations.
        """
        self.res = {}
        self.dirs = dirs
        if dirs:
            self.init_handles(importer_dict, dirs)

    def init_handles(self, importer_dict, dirs=None):
        """Init a handle structure for resources and place it in `res`.

        An importer dictionary is in the form:
        ``{ lambda1: HandleType1, lambda2: HandleType2, ...}``
        and specifies which Handle implementation should be used to load
        specific resources. Which resources are actually loaded using
        which Handle is decided by passing the pathnames (recursively
        explored) of the `dirs` parameter to the lambdas in the dict.

        The correct lambda signature can be found at
        :py:attr:`GameModel.LAMBDA_SIG`

        Note: `dirs` will be scanned in the given order, which is very
            important when loading resources that rely on others(e.g.
            ``World`` ).

        Note: Once a resource is loaded thanks to the `importer_dict`,
            it won't be used anymore(meaning that each file will be
            considered at most once).

        This will call :py:meth:`_init_handles` as its internal
        implementation. If you need to reimplement this logic, please
        consider overriding :py:meth:`_init_handles` instead.

        :raises TypeError: If the functions in `importer_dict` don't
                           match :py:attr:`GameModel.LAMBDA_SIG`.
        :param dirs: A list of directory paths that will be recursively
                     scanned in search of resources. If not specified,
                     :attr:`dirs` will be used (specified in the
                     constructor).
        :param importer_dict: A dictionary that associates lamdas to
                              Handle implementations.
        """
        dirs = dirs or self.dirs

        stack = []
        stack.append((self.res, self._init_handles(dirs, importer_dict)))
        while stack:
            p, new = stack.pop()

            for k, v in list(new.items()):
                # Add missing keys and substitute leaves
                if k not in p \
                   or k in p and not isinstance(v, collections.abc.Mapping):
                    p[k] = v
                # DFS on nested dictionaries
                elif k in p and isinstance(p[k], collections.abc.Mapping) \
                     and isinstance(v, collections.abc.Mapping):
                    stack.append((p[k], v))

    def _init_handles(self, dirs, importer_dict):
        """Init a handle structure for resources and return it.

        An importer dictionary is in the form:
        ``{ lambda1: HandleType1, lambda2: HandleType2, ...}``
        and specifies which Handle implementation should be used to load
        specific resources. Which resources are actually loaded using
        which Handle is decided by passing the pathnames (recursively
        explored) of the `dirs` parameter to the lambdas in the dict.

        The correct lambda signature can be found at
        :py:attr:`GameModel.LAMBDA_SIG`

        Note: `dirs` will be scanned in the given order, which is very
            important when loading resources that rely on others(e.g.
            ``World`` ).

        Note: Once a resource is loaded thanks to the `importer_dict`,
            it won't be used anymore(meaning that each file will be
            considered at most once) and once a resource is in the dict,
            it won't be replaces but any other(e.g. in case of conflicts
            due to file extensions being disabled the model will keep
            the first loaded :class:`Handle` .

        :raises TypeError: If dirs is an empty list.
        :raises TypeError: If the functions in `importer_dict` don't
                           match :py:attr:`GameModel.LAMBDA_SIG`.
        :param dirs: A list of directory paths that will be recursively
                     scanned in search of resources.
        :param importer_dict: A dictionary that associates lamdas to
                              Handle implementations.
        :return: A data structure containing handles, used to access
                 resources from the main game logic(in this specific
                 implementation, a dict of dicts(each dict representing
                 a directory in the filesystem)).
        """
        # Check lambda signatures
        if not all([insp.signature(fun) == GameModel.LAMBDA_SIG
                    for fun in importer_dict]):
            raise TypeError

        # Get recursively all the content of the given dirs
        pathnames = reduce(
            lambda x, y: x + y,
            [[(pt.relpath(glob_path, start=dirpath), dirpath) for glob_path
              in glob.glob(pt.join(dirpath, '**'), recursive=True)]
             for dirpath in dirs])

        # Get a dictionary in the form: {rel_path: abs_path}
        # where rel_path is relative to the given
        # path_dict = {rel_path: abs_path for abs_path in pathnames}

        # Parse the dirs creating the handle structure from
        # importer_dict
        res = {}
        used_paths = set()
        for item, dirpath in pathnames:
            abs_path = pt.join(dirpath, item)
            p = res

            split = item.split(os.sep)
            for subitem in split:
                # If it's a leaf and it's not a dir, find a handle for
                # it
                if subitem == split[-1] and not pt.isdir(abs_path):
                    for lam, handle in importer_dict.items():
                        # If the resource has already been loaded, skip
                        if abs_path in used_paths:
                            break

                        params = lam(pt.abspath(dirpath), item, self)
                        if params is not None:
                            # Check if extensions are kept or ignored
                            if options['resource_extensions']:
                                res_key = subitem
                            else:
                                res_key = pt.splitext(subitem)[0]

                            # Actually create the Handle (skip if
                            # already existing).
                            if res_key not in p:
                                p[res_key] = handle(*params)

                            # Keep track of already loaded resources
                            # so that it won't be considered in future
                            # iterations
                            used_paths.add(abs_path)

                # If it's not a leaf, it's a directory. Make a subtree.
                elif subitem != split[-1]:
                    p = p.setdefault(subitem, {})

        # Remove empty dictionaries
        pre_stack = []
        post_stack = []
        pre_stack.append(res)

        # Setup postvisit
        while pre_stack:
            p = pre_stack.pop()
            if isinstance(p, collections.abc.Mapping):
                post_stack.append(p)
                pre_stack += p.values()

        while post_stack:
            p = post_stack.pop()
            for k, v in list(p.items()):
                # Delete empty dictionaries from the parent
                if not v:
                    del p[k]

        return res

    def loop(self):
        """Start the main loop.

        To stop the loop, set `quit` to True. Before calling this,
        initialize the current world with `switch`.

        :raises AttributeError: If the current world isn't initialized.
        """
        self.quit = False

        while not self.quit:
            if self._waiting_world_handle is not None:
                self._finalize_switch()

            self._current_world.process(self)

    @property
    def current_world_handle(self):
        """Get the handle of the world currently executed world."""
        return self._current_world_handle

    @property
    def current_world(self):
        """Get the world currently executed in the main loop."""
        return self._current_world

    def switch(self, world_handle, cur_reset=False, dest_reset=False,
               immediate=False):
        """Switch to a new world.

        Optionally, reset the current world handle before leaving.

        :raises TypeError: If world_handle isn't a :class:`Handle` type
                           or the inner world isn't a
                           :class:`esper.World` implementation.
        :param world_handle: The world handle instance to game should
                      switch.
        :param cur_reset: Whether the current world handle should be
                          reset before switching.
        :param dest_reset: Whether the destination world handle should
                           be reset before switching.
        :param immediate: If set to ``True``, :py:attr:`current_world`
                          and :py:attr:`current_world_handle` will be
                          immediately set to the new values.
                          If set to ``False``, the attributes will be
                          set to the new values at the beginning of the
                          next game iteration.
                          Be aware that switching immediately will
                          cause any other execution in the current
                          iteration that relies on
                          :py:attr:`current_world` (or its handle)
                          to retrieve misleading information(they will
                          basically believe for that frame of time that
                          their current world is the destination one,
                          while being part of the previous).
        """
        if not isinstance(world_handle, Handle):
            raise TypeError

        # Prepare in case it's not immediate
        self._waiting_world_handle = world_handle
        self._waiting_cur_reset = cur_reset
        self._waiting_dest_reset = dest_reset

        if immediate:
            self._finalize_switch()

    def _finalize_switch(self):
        """Finalize a world switch initiated by :py:meth:`switch`.

        This method is to be used inside :py:meth:`loop` to finalize
        a switch in case it was set to be `not` immediate.
        """
        # Reset if requested
        if self._waiting_cur_reset and self._current_world is not None:
            self._current_world_handle.clear()
        if self._waiting_dest_reset:
            self._waiting_world_handle.clear()

        self._current_world_handle = self._waiting_world_handle
        self._waiting_world_handle = None
        self._current_world = self._current_world_handle.get()

    def __getitem__(self, index):
        """Retrieve an item from the resources dictionary.

        Same as ``GameModel.res[index]``.
        """
        return self.res[index]
