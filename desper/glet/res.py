import os.path as pt
import json

import desper

import pyglet


DEFAULT_SPRITES_LOCATION = 'sprites'
DEFAULT_IMAGE_EXTS = ('.png', '.bmp', '.jpg', '.jpeg')

DEFAULT_ANIMATION_EXTS = ('.json')
"""Default exts for the animation metadata files."""
DEFAULT_ANIMATION_SHEET_EXTS = DEFAULT_IMAGE_EXTS
"""Default exts for the animation sprite sheet files."""


def _pyglet_path(path):
    """Manipulate path to match pyglet.resource requirements.

    Note that pyglet.resource requires paths to be relative to the
    current dir and using only '/' as separator.
    Note also that changing pyglet.resource.path this behaviour can be
    changed, but in this case it should not.

    :param path: The target path(absolute or using '\\').
    :return: A path usable with pyglet.resource.
    """
    return pt.relpath(path, pt.curdir).replace(pt.sep, '/')


def get_resource_from_path(res, rel_path, default=None):
    """Get a specific resource :class:`Handle` from a res dictionary.

    The given path should be relative to one of the resource directories
    chosen when initializing the :class:`GameModel`.

    :param res: A resource dictionary (presumably from a
                :class:`GameModel`).
    :param rel_path: Relative path from one of the resources root
                     directory(chosen when initializing the
                     :class:`GameModel`).
    :param default: The default returned value if the queried
                    :class:`Handle` doesn't exist. Defaults to ``None``.
    :return: The :class:`Handle` loaded from the given `rel_path` if
             exists, `default` otherwise.
    """
    for path in rel_path.split(pt.sep):
        p = res.get(path, None)

        if p is None:
            return default


def get_image_importer(location=DEFAULT_SPRITES_LOCATION,
                       accepted_exts=DEFAULT_IMAGE_EXTS):
    """Get an importer function for `pyglet.image.AbstractImage`.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given image if it's considered accepted
    (designed to be used with :class:`ImageHandle`).

    :param location: The resource subfolder for the game where sprites
                     should be stored(other directories won't be
                     accepted).
    :param accepted_exts: An iterable of extensions recognized as valid
                          images.
    :return: A function usable as key in an `importer_dict`.
    """
    def sprite_importer(root, rel_path, resources):
        """Return the joined path `root` + `rel_path` if accepted.

        Designed to be used with :class:`ImageHandle`. If in the
        resource dictionary a :class:`Handle` is already present(e.g.
        there is another file with the same name in the same directory)
        then nothing will happen(this importer will return ``None``).

        :param root: The root resource directory.
        :param rel_path: The relative path from the resource directory
                         to the specific resource being analyzed.
        :return: The joined path `root` + `rel_path` if accepted, None
                 otherwise(as stated in :py:attr:`GameModel.LAMBDA_SIG`
                 ).
        """
        abspath = pt.join(root, rel_path)

        if (location in pt.dirname(rel_path) and pt.splitext(rel_path)[1] in
            accepted_exts and not isinstance(
                get_resource_from_path(resources, rel_path), desper.Handle)):
            return abspath,

        return None

    return sprite_importer


def get_animation_importer(location=DEFAULT_SPRITES_LOCATION,
                           accepted_exts=DEFAULT_ANIMATION_EXTS,
                           accepted_sheet_exts=DEFAULT_ANIMATION_SHEET_EXTS):
    """Get an importer function for `pyglet.image.animation.Animation`.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given image if it's considered accepted
    (designed to be used with :class:`AnimationHandle`).

    For more information about the metadata file format see
    :class:`AnimationHandle`.

    :param location: The resource subfolder for the game where sprites
                     should be stored(other directories won't be
                     accepted).
    :param accepted_exts: An iterable of extensions recognized as valid
                          animation metadata.
    :param accepted_sheet_exts: An iterable of extensions recognized as
                                valid animation files(sprite sheets).
    :return: A function usable as key in an `importer_dict`.
    """
    def sprite_importer(root, rel_path, resources):
        """Return the joined path `root` + `rel_path` if accepted.

        Designed to be used with :class:`AnimationHandle`. If a
        :class:`Handle` is found in the resource dict where the
        :class:`AnimationHandle` from this importer should go(e.g.
        there is a file with the relative path of the given one) it
        will merely be overwritten by an :class:`AnimationHandle`.

        :param root: The root resource directory.
        :param rel_path: The relative path from the resource directory
                         to the specific resource being analyzed.
        :return: The joined path `root` + `rel_path` if accepted, None
                 otherwise(as stated in :py:attr:`GameModel.LAMBDA_SIG`
                 ).
        """
        if (location in pt.dirname(rel_path) and pt.splitext(rel_path)[1] in
                accepted_exts):
            return pt.join(root, rel_path),

        return None

    return sprite_importer


class ImageHandle(desper.Handle):
    """Handle implementation for a `pyglet.image.AbstractImage`.

    This is used for static images only. See :class:`AnimationHandle`
    for animated images(`pyglet.image.animation.Animation`).
    """

    def __init__(self, filename):
        """Construct a new Handle based on the given `filename`.

        :param filename: The filename that will be used to load the
                         desired resource.
        """
        super().__init__()

        # Manipulate the path for pyglet(pyglet.resource requires
        # relative paths using only '/')
        self._filename = _pyglet_path(filename)

    def _load(self):
        """Implementation of the load logic for this Handle type."""
        return pyglet.resource.image(self._filename)


class AnimationHandle(desper.Handle):
    """Handle implementation for a `pyglet.image.Animation`.

    This is used for animations only. For static images
    (`pyglet.image.AbstractImage`) see :class:`ImageHandle`.

    This Handle accepts a file in its constructor, which should be in
    a specific format(the extension doesn't matter).
    The file content should be in json format, with this structure:
        TBD

    This structure can be easily achieved by using `Aseprite
    <https://www.aseprite.org/>`_'s spritesheet export(by checking the
    JSON Data checkbox).
    """

    def __init__(self, filename):
        """Construct a new Handle for an animation file.

        The animation file should be in json format. For the correct
        data structure see the doc of :class:`AnimationHandle`.
        """
        super().__init__()

        self._filename = filename

    def _load(self):
        """Implementation of the load logic for this Handle type."""
        with open(self._filename) as fin:
            data = json.load(fin)
            if isinstance(data['frames'], dict):
                data['frames'] = data['frames'].values()

        filedir = _pyglet_path(pt.join(pt.dirname(
            self._filename), data['meta']['image']))
        image = pyglet.resource.image(filedir)
        return pyglet.image.Animation(
            frames=[pyglet.image.AnimationFrame(image.get_region(
                frame['frame']['x'], frame['frame']['y'],
                frame['frame']['w'], frame['frame']['h']),
                frame['duration'] / 1000) for frame in data['frames']])
