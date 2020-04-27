class Handle:
    """A base class helper class for resource access.

    A Handle exposes a `get` method which loads a resource from given
    attributes(e.g. a filename) and caches it for later use.
    When deriving, the `__init__` and `_load` method should be overridden
    in order to reproduce the desired behaviour(correctly load and
    cache the desired resource).
    """

    def __init__(self):
        """Construct an empty handle."""
        self._value = None

    def _load(self):
        """Base method for resource loading.

        Implement this method to customize the loading process and make
        your own resource loading logic. This method should load the
        resource using any necessary attribute from `self`, and return
        it.
        """
        raise NotImplementedError

    def get(self):
        """Get the handled resource(and cache it not already).

        NB: This method generally doesn't need to be overridden.

        :return: The specific resource instance handled by this Handle.
        """
        if self._value is None:
            self._value = self._load()

        return self._value

    def clear(self):
        """Clear the cached resource.

        The cached value is wiped and will need to be reloaded(that is
        overhead) when calling `get`.
        This won't necessarily free the memory allocated by the given
        resource. The handle will simply "forget" about the value, which
        may or may not release the memory based on the garbage
        collector.
        """
        self._value = None
