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

    A dispatcher is basically an observable object, handlers are pushed
    using :meth:`add_handler` and events are broadcasted to all
    interested handlers with :meth:`dispatch`.

    An event dispatcher can be enabled (default) or disabled
    (:attr:`dispatch_enabled`). A disabled dispatcher stops dispatching
    events but buffers them internally and releases them as soon as
    it is enabled again.
    Disabling does not affect other behaviours (eg. adding new
    handlers).
    """
    _dispatch_enabled: bool = True

    def __init__(self):
        self._events: dict[str, set[tuple[weakref.ref[EventHandler],
                                          Callable]]] = {}
        self._handlers: dict[
            weakref.ref[EventHandler],
            tuple[tuple[str, Callable], ...]] = {}

        # Queue events by storing event's name, args and keyword args
        self._event_queue: list[tuple[str, tuple, dict]] = []

    def add_handler(self, handler: EventHandler):
        """Add an event handler to the dispatcher.

        Weak references to it are kept, meaning that if the handler ever
        gets out of scope it will be left by the dispatcher.
        """
        assert isinstance(handler, EventHandler)

        # Populate _events
        handler_ref = weakref.ref(handler, self._remove_weak_handler)
        for event_name, method_name in handler.__events__.items():
            self._events.setdefault(event_name, set()).add(
                (handler_ref, getattr(handler.__class__, method_name)))

        # Populate _handlers
        self._handlers[handler_ref] = \
            tuple(
                (event_name, getattr(handler.__class__, method_name))
                for event_name, method_name in handler.__events__.items()
        )

    def is_handler(self, handler: EventHandler) -> bool:
        """Return whether or not a handler is into the dispatcher."""
        assert isinstance(handler, EventHandler)

        return weakref.ref(handler) in self._handlers

    def _remove_weak_handler(self, handler_ref: weakref.ref[EventHandler]):
        """Remove handler given its weak reference.

        The reference may or may not be dead.
        """
        if handler_ref not in self._handlers:
            return

        for event_name, method_ref in self._handlers[handler_ref]:
            self._events[event_name].remove((handler_ref, method_ref))

        del self._handlers[handler_ref]

    def remove_handler(self, handler: EventHandler):
        """Remove handler from the dispatcher.

        Said handler will stop receiving all dispatched events.
        """
        self._remove_weak_handler(weakref.ref(handler))

    def dispatch(self, event_name: str, *args, **kwargs):
        """Broadcast an event to all registered listeners.

        Additional parameters are passed to each handler's callback.

        Unknown events (for which there are and there have never been
        handlers) are silently dropped.
        """
        if event_name not in self._events:
            return

        # If disabled, queue events
        if not self._dispatch_enabled:
            self._event_queue.append((event_name, args, kwargs))
            return

        # Existance of the referents shall be guaranteed by the
        # automatic cleanup
        for handler_ref, method_ref in set(self._events[event_name]):
            method_ref(handler_ref(), *args, **kwargs)

    @property
    def dispatch_enabled(self) -> bool:
        return self._dispatch_enabled

    @dispatch_enabled.setter
    def dispatch_enabled(self, value: bool):
        self._dispatch_enabled = value

        # This if is redundant as the queue would necessarily be empty
        # if switching from enabled to disabled state.
        # For extra safety (eg. the user modifies manually the queue)
        # we keep this selection
        if not value:
            return

        # Deplete queue if enabling
        for event_name, args, kwargs in self._event_queue:
            self.dispatch(event_name, *args, **kwargs)
        self._event_queue.clear()

    def clear(self):
        """Remove all handlers and pending events.

        Pending events are lost forever. Dispatch is enabled after this
        operation.
        """
        self._event_queue.clear()
        self._events.clear()
        self._handlers.clear()

        self._dispatch_enabled = True


def event_handler(*event_names: str, **event_mappings: str) -> Callable[
        [type], type]:
    """Decorator: implements :class:`EventHandler` in the decorated class.

    The given event names shall match the method name that is to be
    used as callback. If discrepancy between event and method names
    is needed, keyword arguments can be used (argument name =
    event name, argument value = method name).
    """

    def decorator(cls):
        # For slightly better performance in the whole event system,
        # ignore empty handlers
        if not event_names and not event_mappings:
            return cls

        # Composite behaviour, compose eventually discovered events
        # (eg. inherited events) with newly specified events
        events = getattr(cls, '__events__', {})
        cls.__events__ = (events | dict(zip(event_names, event_names))
                          | event_mappings)

        # TODO: manage __slots__ (create a new subclass)

        return cls

    return decorator
