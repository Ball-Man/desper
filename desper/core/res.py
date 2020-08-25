import os.path as pt
from queue import PriorityQueue
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


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
        if (location in pt.dirname(rel_path).split(pt.sep)
                and pt.splitext(rel_path)[1] in accepted_exts):
            return pt.join(root, rel_path),

        return None

    return importer


class Handle:
    """A base class helper class for resource access.

    A Handle exposes a :py:meth:`get` method which loads a resource from
    given attributes(e.g. a filename) and caches it for later use.
    When deriving, the :py:meth:`__init__` and :py:meth:`_load` method
    should be overridden in order to reproduce the desired
    behaviour(correctly load and cache the desired resource).
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
        """Get the handled resource(and cache it if it's not already).

        NB: This method generally doesn't need to be overridden.

        :return: The specific resource instance handled by this Handle.
        """
        if self._value is None:
            self._value = self._load()

        return self._value

    def clear(self):
        """Clear the cached resource.

        The cached value is wiped and will need to be reloaded(that is
        overhead) when calling :py:meth:`get`.
        This won't necessarily free the memory allocated by the given
        resource. The handle will simply "forget" about the value, which
        may or may not release the memory based on the garbage
        collector.
        """
        self._value = None


class IdentityHandle(Handle):
    """Special kind of :class:`Handle` that returns the given value.

    This handle accepts any value, and when :py:meth:`get` is called,
    returns the given value itself(basically, there is no "generated"
    value).

    This is used to inject manually resources into the resources
    dictionary of a :class:`GameModel`.
    """

    def __init__(self, value):
        super().__init__()
        self._value = value

    def _load(self):
        """Return the given value as it is."""
        return self._value


@dataclass(order=True)
class _PrioritizedDictEntry:
    """Class used to contain a prioritized entry for importer dicts.

    Used by :class:`ImporterDictBuilder` to keep track of the entries in
    a priority queue.
    """
    key_lambda: Any = field(compare=False)
    handle_type: Handle = field(compare=False)
    priority: int


class ImporterDictBuilder:
    """Builder class for importer dictionaries(for :class:`GameModel`)

    This class observes the GOF Builder pattern and facilitates the
    creation of importer dictionaries. In particular, it facilitates
    the creation of ordered dictionaries with a specified priority for
    each entity(since the order of the entries in the dictionary defines
    which resource is as first, this might be quite important for
    certain setups).

    Smaller values in priority will be placed first.

    A default instance of this class is constructed by default at module
    level attribute :py:attr:`importer_dict_builder` (so that, if not
    strictly necessary, you don't have to instantiate this class
    manually each time).
    """

    def __init__(self):
        self._queue = PriorityQueue()

    def add_rule(self, key_lambda, handle_type, priority=0):
        """Add a resource importer rule, given the key and the handle.

        The `key_lambda` is a callable(usually a function). The
        `handle_type` is a subtype of :class:`Handle`. The `priority`
        helps defining the order in which the rules will be executed by
        the :class:`GameModel`.

        For more info about the meaning of `key_lambda` and
        `handle_type` see :class:`GameModel`.

        :param key_lambda: The lambda function used as a key inside the
                           importer dictionary.
        :param handle_type: A subtype of :class:`Handle` used as value
                            inside the importer dictionary for the given
                            lambda key.
        :param priority: An integer defining the order of execution for
                         rules inside the importer dict(lower values of
                         `priority` are placed first).
        :return: The :class:`ImporterDictBuilder` class instance(self),
                 so that multiple :py:meth:`add_rule` can be
                 concatenated.
        """
        self._queue.put(_PrioritizedDictEntry(key_lambda, handle_type,
                                              priority))
        return self

    def build(self):
        """Build and return an importer dictionary.

        Note that once an dictionary is built, the builder will be
        cleaned up(so it's not possible to build multiple times the same
        dictionary calling build multiple times).

        :return: An importer dictionary which rules are defined by
                 previous calls to :py:meth:`add_rule`.
        """
        importer_dict = OrderedDict()
        while not self._queue.empty():
            el = self._queue.get()
            importer_dict[el.key_lambda] = el.handle_type

        return importer_dict


importer_dict_builder = ImporterDictBuilder()
"""Pre-constructed instance of :class:`ImporterDictBuilder`."""
