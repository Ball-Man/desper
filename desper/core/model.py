from typing import Protocol, runtime_checkable, Generic, TypeVar, Optional

_T = TypeVar('T')


class ResourceMap:
    """ TBD. """


@runtime_checkable
class ResourceProtocol(Protocol):
    """Protocol defining resources.

    The implemented format makes them suitable to be cointained in
    a :class:`ResourceMap`.
    """
    parent: ResourceMap
    key: str


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
    parent: ResourceMap = None
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
