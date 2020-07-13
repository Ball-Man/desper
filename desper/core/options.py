options = {'resource_extensions': True}
"""Dictionary of global options for desper.

`resource_extensions`:
Whether extensions should be kept in resource names or not when
imported by a :class:`GameModel`.

When set to `True`, accessing resources will require that the
file extension, or an exception will be raised(e.g.
res['music']['bip.ogg']).

When set to `False`, resources won't need the original file
extensions, but this could potentially lead to overlapping names.
Based on this, as a best practice you should never have two or more
files in the same resource dir with the same name(and different
extension), one would override the other since in the resource dict
there can only be one resource with a given name. Note that
overlapping names could be allowed in special cases(e.g. an image
file and its metadata might have the same name, based on their
importer lambda's/:class:`Handle` s).
"""
