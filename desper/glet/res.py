import os.path as pt

import desper

import pyglet


DEFAULT_SPRITES_LOCATION = 'sprites'
DEFAULT_IMAGE_EXTS = ('.png', '.bmp', '.jpg', '.jpeg')


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
    def sprite_importer(root, rel_path, *args):
        """Return the joined path `root` + `rel_path` if accepted.

        Designed to be used with :class:`ImageHandle`.

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

    This is used for static images only(see :class:`AnimationHandle`)
    for animated images(`pyglet.image.animation.Animation`).
    """

    def __init__(self, filename):
        """Construct a new Handle based on the given `filename`.

        :param filename: The filename that will be used to load the
                         desired resource.
        """
        super().__init__()

        self._filename = pt.relpath(filename, pt.curdir)
        self._filename = self._filename.replace(pt.sep, '/')

    def _load(self):
        """Implementation of the load logic for this Handle type."""
        return pyglet.resource.image(self._filename)
