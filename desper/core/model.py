from typing import (Protocol, runtime_checkable, Generic, TypeVar, Optional,
                    Union, ClassVar)
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


class ResourceMap:
    """ TBD. """
    parent: Optional['ResourceMap'] = None
    key: Optional[str] = None

    split_char: ClassVar[str] = '/'

    def __init__(self):
        self.maps: dict = {}
        self.handles: ChainMap = ChainMap()

    def get(self, key: str, default: _T = None) -> Union[
            Handle, 'ResourceProtocol', _T]:
        """Retrieve either a resource handle or a resource subtree.

        Nested exploration of resource maps can be achieved by providing
        a composite key using the special delimiter ``/``.
        Eg. ``resource_map.get('media/level1/ex1')``.

        The delimiter character can be changed at any time by setting
        the class attribute :attr:`split_char` (defaults to ``/``).
        """
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


@runtime_checkable
class ResourceProtocol(Protocol):
    """Protocol defining resources.

    The implemented format makes them suitable to be cointained in
    a :class:`ResourceMap`.
    """
    parent: ResourceMap
    key: str
