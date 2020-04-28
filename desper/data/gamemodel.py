import glob
import os
import os.path as pt
import re
from functools import reduce


class GameModel:
    """A base class for game logic encapsulation.

    A GameModel is a master container containing "the whole game".
    The game is typically organized in one or multiple worlds. This
    worlds are contained, managed and loaded by a GameModel.

    A GameModel also manages the main game loop and contains useful
    data structures for resource usage and media(audio/video).

    Loaded resources can be accessed via the `res` parameter(int this
    implementation: a nested structure of dictionaries which keys are
    the directory names).
    """

    def __init__(self, dirs=[], importer_dict={}):
        """Construct a new GameModel from an importer dictionary.

        An importer dictionary is in the form:
        { lambda1: HandleType1, lambda2: HandleType2, ...}
        and specifies which Handle implementation should be used to load
        specific resources. Which resources are actually loaded using
        which Handle is decided by passing the pathnames (recursively
        explored) of the `dirs` parameter to the lambdas in the dict.
        The lambda should return None if the given pathname doesn't
        refer to its specific resource type. It should return an
        iterable containing the parameters passed to the Handle
        constructor otherwise.

        :param dirs: A list of directory paths that will be recursively
                     scanned in search of resources.
        :param importer_dict: A dictionary that associates regex
                              patterns to Handle implementations.
        """
        self.res = {}
        if dirs:
            self.init_handles(dirs, importer_dict)

    def init_handles(self, dirs, importer_dict):
        """Init a handle structure for resources and place it in `res`.

        An importer dictionary is in the form:
        { lambda1: HandleType1, lambda2: HandleType2, ...}
        and specifies which Handle implementation should be used to load
        specific resources. Which resources are actually loaded using
        which Handle is decided by passing the pathnames (recursively
        explored) of the `dirs` parameter to the lambdas in the dict.
        The lambda should return None if the given pathname doesn't
        refer to its specific resource type. It should return an
        iterable containing the parameters passed to the Handle
        constructor otherwise.

        This will call `_init_handles` as its internal implementation.
        If you need to reimplement this logic, please consider
        overriding `_init_handles` instead.

        :raises TypeError: If dirs is an empty list.
        :param dirs: A list of directory paths that will be recursively
                     scanned in search of resources.
        :param importer_dict: A dictionary that associates lamdas to
                              Handle implementations.
        """
        self.res.update(self._init_handles(dirs, importer_dict))

    def _init_handles(self, dirs, importer_dict):
        """Init a handle structure for resources and return it.

        An importer dictionary is in the form:
        { lambda1: HandleType1, lambda2: HandleType2, ...}
        and specifies which Handle implementation should be used to load
        specific resources. Which resources are actually loaded using
        which Handle is decided by passing the pathnames (recursively
        explored) of the `dirs` parameter to the lambdas in the dict.
        The lambda should return None if the given pathname doesn't
        refer to its specific resource type. It should return an
        iterable containing the parameters passed to the Handle
        constructor otherwise.

        :raises TypeError: If dirs is an empty list.
        :param dirs: A list of directory paths that will be recursively
                     scanned in search of resources.
        :param importer_dict: A dictionary that associates lamdas to
                              Handle implementations.
        :return: A data structure containing handles, used to access
                 resources from the main game logic(in this specific
                 implementation, a dict of dicts(each dict representing
                 a directory in the filesystem)).
        """
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
        for item, dirpath in pathnames:
            abs_path = pt.join(dirpath, item)
            p = res

            split = item.split(os.sep)
            for subitem in split:
                # If it's a leaf and it's not a dir, find a handle for
                # it
                if subitem == split[-1] and not pt.isdir(abs_path):
                    for lam, handle in importer_dict.items():
                        params = lam(abs_path)
                        if params is not None:
                            p[subitem] = handle(*params)
                elif subitem != split[-1]:
                    p = p.setdefault(subitem, {})

        return res
