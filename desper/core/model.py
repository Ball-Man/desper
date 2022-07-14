from typing import Protocol


class ResourceMap:
    """ TBD. """


class ResourceProtocol(Protocol):
    """Protocol defining resources.

    The implemented format makes them suitable to be cointained in
    a :class:`ResourceMap`.
    """
    parent: ResourceMap
    key: str
