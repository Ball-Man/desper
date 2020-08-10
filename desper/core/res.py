import os.path as pt


def get_resource_importer(location, accepted_exts):
    """Get an importer function for resources, based on filename.

    Given the resource subfolder and accepted extensions, return a
    function in the form of :py:attr:`GameModel.LAMBDA_SIG` that will
    only accept files in the given resource subfolder(`location`) and
    returns the path to the given media resource if it's considered
    accepted.

    :param location: The resource subfolder for the game where resource
                     should be stored(other directories won't be
                     accepted).
    :param accepted_exts: An iterable of extensions recognized as valid
                          resource file.
    """
    def importer(root, rel_path, resources):
        """Return the joined path `root` + `rel_path` if accepted.

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

    return importer
