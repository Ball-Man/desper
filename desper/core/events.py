"""Desper's event system.

the event system is based on a simple broadcast pattern.
"""
from typing import Protocol, Mapping, Callable, runtime_checkable
import weakref


@runtime_checkable
class EventHandler(Protocol):
    """Protocol descripting event handlers.

    An event handler has a field :attr:`__events__`, describing
    the mapping between event names (that are observed) and callback
    (method) names. This information is encoded in a list of pairs.

    Such information is processed by :class:`EventDispatcher` to obtain
    the actual methods from the instances.
    """

    __events__: Mapping[str, str]


class EventDispatcher:
    """Stores :class:`EventHandler` instances and dispatches events.

    A dispatcher is basically observable object, handlers are pushed
    using :meth:`add_handler` and events are broadcasted to all
    interested handlers with :meth:`dispatch`.
    """

    def __init__(self):
        self._events: dict[str, set[Callable]] = {}
        self._handlers: dict[
            weakref.ref[EventHandler],
            tuple[tuple[str, Callable], ...]] = {}

    def add_handler(self, handler: EventHandler):
        """Add an event handler to the dispatcher.

        Weak references to it are kept, meaning that if the handler ever
        gets out of scope it will be left by the dispatcher.
        """
        assert isinstance(handler, EventHandler)

        # Populate _events
        for event_name, method_name in handler.__events__.items():
            self._events.setdefault(event_name, set()).add(
                getattr(handler, method_name))

        # Populate _handlers
        self._handlers[weakref.ref(handler)] = tuple(
            (event_name, getattr(handler, method_name))
            for event_name, method_name in handler.__events__.items()
        )

    def is_handler(self, handler: EventHandler) -> bool:
        """Return whether or not a handler is into the dispatcher."""
        assert isinstance(handler, EventHandler)

        return weakref.ref(handler) in self._handlers
