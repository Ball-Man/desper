from itertools import chain
from typing import (Protocol, runtime_checkable, Generic, TypeVar, Optional,
                    Union, ClassVar, Any)
from collections import ChainMap

_T = TypeVar('T')


class Handle(Generic[_T]):
    """Abstract wrapper resource.

    All resources that are not maps themselves shall be handles. A
    handle contains the logic necessary to load an actual resource into
    memory, either from file, or other means.

    Subclass this class to implement such behaviours for specific
    resource types.

    Common usage is through the ``()`` operator (i.e. :meth:`__call__`),
    which will automatically load, cache and return the resource.
    After caching for the first time, said value will be stored and
    returned each time it is needed (unless manually cleaned from memory
    using :meth:`clear`).
    """
    parent: 'ResourceMap' = None
    key: Optional[str] = None

    _cache: Optional[_T] = None
    _cached: bool = False

    def load(self) -> _T:
        """Load the targeted resource and return it.

        Override this method to implement specific loading behaviours.

        Note that this method does not affect the internal cache, but
        only represents the loading logic.
        """

    def __call__(self) -> _T:
        """Cache and return the wrapped resource."""
        if not self._cached:
            self._cache = self.load()
            self._cached = True

        return self._cache

    def clear(self):
        """Clear internal cache."""
        self._cached = False
        self._cache = None

    @property
    def cached(self) -> bool:
        """Get wheter the resource is cached or not."""
        return self._cached


class StaticResourceMap:
    """TBD."""
    __slots__ = ('_handle_names', )

    # Store names of handles for faster retrieval of unwrapped resources
    # If it's not a handle, it's a map
    _handle_names: frozenset[str]

    def __init__(self):
        object.__setattr__(self, '_handle_names', frozenset())

    def __setattr__(self, name, value):
        """Prevent setting new values."""
        raise ValueError('StaticResourceMaps are immutable')

    def __delattr__(self, name):
        """Prevent deletion of values."""
        raise ValueError('StaticResourceMaps are immutable')

    def __getitem__(self, key: str) -> Union[Any, 'StaticResourceMap']:
        """Retrieve either an unwrapped resource or a static subtree.


        Analogous to :meth:`ResourceMap.__getitem__`, but for static
        resource maps.
        """
        return getattr(self, key)

    def __getattribute__(self, name):
        """Retrieve either an unwrapped resource or a static subtree.


        Analogous to :meth:`ResourceMap.__getitem__`, but for static
        resource maps.
        """
        if name in object.__getattribute__(self, '_handle_names'):
            return object.__getattribute__(self, name)()

        return object.__getattribute__(self, name)

    def get(self, key: str) -> Union[Handle, 'StaticResourceMap']:
        """Retrieve either a resource handle or a static subtree.

        Analogous to :meth:`ResourceMap.get`, but for static resource
        maps.

        Use this method if retrieval a :class:`Handle` instance is
        necessary. To access the unwrapped values directly use direct
        attribute access or ``[]`` operator (:meth:`__getitem__`).
        """
        return object.__getattribute__(self, key)


class ResourceMap:
    """ Nested resource container.

    Main model container for entire desper projects, it represents
    resources in a tree like structure (contains other maps or resources
    wrapped into :class:`Handle`s).

    Resources can be queried using strings as keys, in particular, using
    :meth:`get` retrieves a submap or a :class:`Handle` corresponding to
    the given key. An unwrapped resource can be directly extrapolated
    with the convenience ``[]`` operator (:meth:`__getitem__`) (quicker
    than using :meth:`get` and obtaining the value manually with ``()``)
    .

    Key strings can be composed to simplify the retrieval process (a
    delimiter character is used in this case, :attr:`split_char` which
    is ``/`` by default). For example::

        resource_map['sprites']['level1']['player']

    is equivalent to::

        resource_map['sprites/level1/player']

    which in turn is equivalent to::

        resource_map.get('sprites/level1/player')()

    Adding a resource can be achieved similarly using the ``[]``
    operator (:meth:`__setitem__`). Key composition is supported as
    well::

        resource_map['sprites/level2/player'] = ...

    """
    parent: Optional['ResourceMap'] = None
    key: Optional[str] = None

    split_char: ClassVar[str] = '/'

    def __init__(self):
        self.maps: dict = {}
        self.handles: ChainMap = ChainMap()

    def get(self, key: str, default: _T = None) -> Union[
            Handle, 'ResourceMap', _T]:
        """Retrieve either a resource handle or a resource subtree.

        Nested exploration of resource maps can be achieved by providing
        a composite key using the special delimiter ``/``.
        Eg. ``resource_map.get('media/level1/ex1')``.

        The delimiter character can be changed at any time by setting
        the class attribute :attr:`split_char` (defaults to ``/``).
        """
        assert isinstance(key, str)

        keys = key.split(self.split_char)
        last_key = keys[-1]
        value = self
        try:
            # Last key is queried at last, as it is not necessarily
            # a map
            for subkey in keys[:-1]:
                value = value.maps[subkey]

            if last_key in value.handles:
                return value.handles[last_key]
            else:
                return value.maps[last_key]

        except KeyError:
            return default

    def __getitem__(self, key: str) -> Union[Any, 'ResourceMap']:
        """Retrieve either an unwrapped resource or a resource subtree.

        Similar to :meth:`get` but if the resulting resource is a
        :class:`Handle` the internal cached value is directly returned
        instead (if no value is currently cached, it gets loaded
        immediately).

        :raises KeyError: If the query is invalid (no resource
            corresponds to it).
        """
        assert isinstance(key, str)

        # Code is duplicated for extra performance
        keys = key.split(self.split_char)
        last_key = keys[-1]
        value = self
        # Last key is queried at last, as it is not necessarily
        # a map
        for subkey in keys[:-1]:
            value = value.maps[subkey]

        if last_key in value.handles:
            return value.handles[last_key]()
        else:
            return value.maps[last_key]

    def __setitem__(self, key: str, value: Union['ResourceMap', Handle]):
        """Add a resource to the resource map.

        The given resource shall be a :class:`ResourceMap` or a
        :class:`Handle`.

        Nested insertion can be achieved by providing a composite key
        using the special delimiter ``/`` (see :meth:`get`).
        Any missing intermediate maps will automatically be created.
        If the creation of an intermediate map conflicts with an
        existing handle, the handle will be overwritten by a new map.
        """
        assert isinstance(key, str)
        assert isinstance(value, (ResourceMap, Handle)), \
            ('Invalid resource type (valid types are Handles '
             'and ResourceMaps')

        # Code is duplicated for extra performance
        keys = key.split(self.split_char)
        last_key = keys[-1]
        target_map = self
        # Last key is queried at last, as the value has to be
        # discriminated between handles and maps.
        for subkey in keys[:-1]:
            target_map.handles.pop(subkey, None)    # Overwrite duplicates
            target_map = target_map.maps.setdefault(subkey, ResourceMap())

        # For better performance, only one type check is done at this
        # point.
        # If the value is not a ResourceMap, it is assumed to be a
        # Handle.
        # More extensive checks are done through assertions in debug
        # mode.
        dest_map = target_map.handles
        other_map = target_map.maps
        if isinstance(value, ResourceMap):
            dest_map, other_map = other_map, dest_map

        other_map.pop(last_key, None)         # Delete duplicates
        dest_map[last_key] = value

        # Set added value's key in its immediate parent (last_key)
        # and the parent itself
        value.parent = target_map
        value.key = last_key

    def clear(self):
        """Clear contents of the resource tree.

        All resources will be scrapped. Note that this simply clears
        data structures internal to this specific map. Submaps can
        still be alive and intact if referenced elsewhere.

        :attr:`parent` and :attr:`key` of contained resources is reset
        if necessary, while current map's ones are left untouched (
        contents are freed but this map could still be part of
        supermap).
        """
        # Before scrapping everything, update their parent information
        for handle in self.handles.values():
            if handle.parent == self:
                handle.parent = None
                handle.key = None

        for map_ in self.maps.values():
            if map_.parent == self:
                map_.parent = None
                map_.key = None

        self.maps.clear()
        self.handles.clear()

    def get_static_map(self) -> StaticResourceMap:
        """Generate a static map for convenience resource access.

        The returned static map mirrors the structure of the original.

        Internal implementation is recursive, hence extremely deep
        nested resource maps are not ideal.
        """
        # Set valid identifiers as slots
        slots_resources = tuple(filter(
            lambda x: x.isidentifier(), chain(self.handles.keys(),
                                              self.maps.keys())))

        # Don't add a dict if all the resources can be encoded into
        # slots
        dict_list = []
        if len(slots_resources) < len(self.handles) + len(self.maps):
            dict_list.append('__dict__')

        class StaticSubmap(StaticResourceMap):
            __slots__ = (*slots_resources, *dict_list)

            def __init__(subself):
                super().__init__()
                for key, value in self.handles.items():
                    object.__setattr__(subself, key, value)

                object.__setattr__(subself, '_handle_names',
                                   frozenset(self.handles.keys()))

                # Recursively retrieve nested static maps
                for key, value in self.maps.items():
                    object.__setattr__(subself, key, value.get_static_map())

        return StaticSubmap()


@runtime_checkable
class ResourceProtocol(Protocol):
    """Protocol defining resources.

    The implemented format makes them suitable to be cointained in
    a :class:`ResourceMap`.
    """
    parent: ResourceMap
    key: str
