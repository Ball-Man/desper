from dataclasses import dataclass, field
import glob
import importlib
import os.path as pt
from typing import (Iterable, Sequence, Mapping, AnyStr, Callable, Optional,
                    Container)

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


@dataclass
class DirectoryPopulatorRule:
    directory_path: str
    handle_type: Callable[..., Handle]
    args: Sequence = field(default_factory=lambda: [])
    file_exts: Container[str] = ()
    kwargs: Mapping = field(default_factory=lambda: {})

    def instantiate(self, filename: str) -> Handle:
        """Call :attr:`handle_type` passing filename and stored args."""
        return self.handle_type(filename, *self.args, **self.kwargs)


class DirectoryResourcePopulator:
    """Populate a :class:`ResourceMap` from a hierarchy of directories.

    Instances of this populator are callables which accept a map and
    populate it with the resources gathered from the file system.
    Filenames are used as handle names.

    ``nest_on_conflict`` can be used to enable/disable nesting of
    conflicting handles. When trying to place a new :class:`Handle` in
    the resource map, it is possible that a resource for the same key
    already exists.
    If nesting is enabled, both the new and the old
    handles are kept in memory. The new one will become the default
    value, but it will always be possible to retrieve the shadowed one.
    If nesting is disabled, only the new resource is kept.

    ``trim_extensions`` can be used to drop file extensions from the
    name of the generated handles. This makes names more memorable,
    but can cause conflicting handles (make sure ``nest_on_conflict``
    was properly set, based your expected behaviour). Moreover, dropping
    extensions simple usage of :class:`StaticResourceMap` (
    see :meth:`ResourceMap.get_static_map`). Defaults
    to ``False`` (disabled), but enabling it is recommended.
    """

    def __init__(self, root: str = project_path('resources'),
                 nest_on_conflict: bool = True, trim_extensions: bool = False):
        self.root: str = root
        self.nest_on_conflict = nest_on_conflict
        self.trim_extensions = trim_extensions

        self.rules: list[DirectoryPopulatorRule] = []

    def add_rule(self, relative_path: str, handle_type: Callable[..., Handle],
                 *args, file_exts: Iterable[str] = (), **kwargs):
        """Add a rule that maps a subdirectory to a resource type.

        Whenever a file from the given subdirectory (``relative_path``)
        is encountered, a handle is instantiated using ``handle_type``.
        ``handle_type`` must accept as first positional argument a
        string (filename).

        ``relative_path`` is the path of the target directory, relative
        to :attr:`root`.

        Keyword argument ``file_exts`` can be specified if filtering
        on specific extensions is desired (an empty iterable defaults
        to: accept all extensions). Extensions shall be given in the
        form `.ext`.

        Additional arguments (positional and keywords) can be specified.
        They will be passed to ``handle_type`` at invocation time.
        """
        self.rules.append(
            DirectoryPopulatorRule(relative_path, handle_type, args,
                                   set(file_exts), kwargs))

    def __call__(self, resource_map: ResourceMap, root: Optional[str] = None,
                 nest_on_conflict: Optional[bool] = None,
                 trim_extensions: Optional[bool] = None):
        """Apply populator on given map.

        Based on given rules (specified with :meth:`add_rule` and stored
        in :attr:`rules`):

        - All files encountered in a directory mentioned in a rule
          will cause the instantiation of the corresponding
          :class:`Handle`. The filename is given as first parameter.
          Such handle will have its filename as key.
        - All subdirectories encountered will cause the instantiation of
          a submap, i.e. a new :class:`ResourceMap` having as key the
          directory name.

        Keyword arguments' meaning can be inspected at
        :class:`DirectoryResourcePopulator`. ``None`` values will fall
        back to the values specified during construction.

        TODO: Manage separately rules for subdirectories
        """
        if root is None:
            root = self.root

        if nest_on_conflict is None:
            nest_on_conflict = self.nest_on_conflict

        if trim_extensions is None:
            trim_extensions = self.trim_extensions

        for rule in self.rules:
            full_dir_path = pt.join(root, rule.directory_path)

            # Silently skip if non-existing, but get angry if it exists
            # and is not a directory
            if not pt.exists(full_dir_path):
                continue

            if not pt.isdir(full_dir_path):
                raise ValueError(
                    f"Trying to gather resources from {full_path}, but it's "
                    'not a directory')

            for full_file_path in glob.iglob(pt.join(full_dir_path, '**'),
                                             recursive=True):
                # Filter rule extensions
                # Empty container means all extensions. Explicitly use
                # len to check it as the container type is unsure
                if (len(rule.file_exts)
                    and pt.splitext(full_file_path)[1]
                        not in rule.file_exts):
                    continue

                # Prepare some paths for map insertion
                relpath = pt.relpath(full_file_path, root)
                resource_string = pt.normpath(relpath).replace(
                    pt.sep, ResourceMap.split_char)
                # Optionally trim extensions from files
                if trim_extensions and pt.isfile(full_file_path):
                    resource_string = pt.splitext(resource_string)[0]

                new_resource = None
                if (pt.isdir(full_file_path)
                        and resource_map.get(resource_string) is None):
                    new_resource = ResourceMap()
                elif pt.isfile(full_file_path):
                    new_resource = rule.instantiate(full_file_path)

                    # Add scope level if a conflicting handle is encountered?
                    if nest_on_conflict:
                        handle = resource_map.get(resource_string)
                        if (handle is not None
                            and handle is handle.parent.handles.maps[0].get(
                                handle.key)):
                            handle.parent.handles.maps.insert(0, {})

                if new_resource is not None:
                    resource_map[resource_string] = new_resource
