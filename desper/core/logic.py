"""Desper's logic module.

Entities are collections of components (Python objects) catalogued in
centralized :class:`World`s.
"""
import abc
import bisect
from itertools import count
from functools import total_ordering
from typing import Hashable, Any, TypeVar, Iterable, Union, Optional

from desper.core.events import EventDispatcher, event_handler

C = TypeVar('C')
T = TypeVar('T')

ON_ADD_EVENT_NAME = 'on_add'
ON_REMOVE_EVENT_NAME = 'on_remove'
ON_COMP_DISPATCH_EVENT_NAME = '_on_component_dispatch'


@total_ordering
class Processor(abc.ABC):
    """Main executor over entities and components.

    When a Processor is added into a :class:`World`, its
    :attr:`world` attribute is updated accordingly.

    :meth:`World.process` will call the :meth:`process` method of each
    added Processor, in order of priority. Lower priorities are
    processed first. A class or instance level priority can be set
    through the :attr:`priority` attribute (defaults to ``0``).
    """
    world: Optional['World'] = None
    priority: int = 0

    @abc.abstractmethod
    def process(self):
        """Implement this method in a subclass to provide your logic."""

    def __eq__(self, other):
        """Define ordering based on priority values."""
        return self.priority == other.priority

    def __lt__(self, other):
        """Define ordering based on priority values."""
        return self.priority < other.priority


P = TypeVar('Processor', bound=Processor)


@event_handler(on_component_dispatch=ON_COMP_DISPATCH_EVENT_NAME)
class World(EventDispatcher):
    """Main container for entities and components."""

    def __init__(self, id_generator=None):
        super().__init__()

        # Listen to self dispatched events
        self.add_handler(self)

        self._sorted_processors: list[Processor] = []
        self._processors: dict[type[Processor], Processor] = {}

        if id_generator is None:
            self.id_generator = count(1)
        else:
            self.id_generator = id_generator
        self._components: dict[set[Hashable]] = {}
        self._entities: dict[dict[Any]] = {}
        self._dead_entities = set()

    def create_entity(self, *components: C,
                      entity_id: Hashable = None) -> Hashable:
        """Create a new entity.

        The newly create entity ID is returned, which is just a hashable
        used to identify it. By default, increasing integers are used (
        first entity has ID 1). A custom ID can be imposed via
        ``entity_id``.

        One or more components can be passed to be assigned to
        the entity.
        """
        assert isinstance(entity_id, Hashable), (
            f'Entity ID must be hashble, found {entity_id}, which is not')

        if entity_id is None:
            entity_id = next(self.id_generator)

        # Code duplication for performance, see add_component
        for component in components:
            component_type = type(component)
            if component_type not in self._components:
                self._components[component_type] = set()

            self._components[component_type].add(entity_id)

            if entity_id not in self._entities:
                self._entities[entity_id] = {}

            self._entities[entity_id][component_type] = component

        # Event handling takes effect after adding all components, so
        # to prevent criticalities on component addition order.
        for component in components:
            if hasattr(component, '__events__'):
                self.add_handler(component)

                # If dispatching is enabled, call on_add directly to gain
                # performance. Otherwise an event is dispatched
                if (ON_ADD_EVENT_NAME in component.__events__
                        and self._dispatch_enabled):
                    getattr(
                        component,
                        component.__events__[ON_ADD_EVENT_NAME])(
                            entity_id, self)
                # on_add exists but dispatching is disabled
                elif not self._dispatch_enabled:
                    self.dispatch('on_component_dispatch', ON_ADD_EVENT_NAME,
                                  component, entity_id)

        return entity_id

    def add_component(self, entity: Hashable, component: C):
        """Add a new component instance to an entity.

        Add a component instance to an entity. If a component of the
        same type is already assigned to the entity, it will be
        replaced.
        """
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        component_type = type(component)
        if component_type not in self._components:
            self._components[component_type] = set()

        self._components[component_type].add(entity)

        if entity not in self._entities:
            self._entities[entity] = {}

        self._entities[entity][component_type] = component

        # Event handling, if component is an event handler for the
        # special event on_add, manage it
        # For performance reasons, check for the __events__ attribute
        # instead of using isinstance
        if hasattr(component, '__events__'):
            self.add_handler(component)

            # If dispatching is enabled, call on_add directly to gain
            # performance. Otherwise an event is dispatched
            if (ON_ADD_EVENT_NAME in component.__events__
                    and self._dispatch_enabled):
                getattr(component,
                        component.__events__[ON_ADD_EVENT_NAME])(entity, self)
            # on_add exists but dispatching is disabled
            elif not self._dispatch_enabled:
                self.dispatch('on_component_dispatch', ON_ADD_EVENT_NAME,
                              component, entity)

    def _on_component_dispatch(self, event, component, entity):
        """Handler method, dispatch the given event to a component.

        Designed to be used when adding or removing components while
        dispatching is disabled. A World is always a handler of itself,
        listening to this event to relay ``on_add`` and ``on_remove``
        events.
        """
        getattr(component, component.__events__[event])(entity, self)

    def has_component(self, entity: Hashable, component_type: type[C]) -> bool:
        """Check whether an entity has a component of the given type.

        Subtypes are also checked.
        """
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        if entity not in self._entities:
            return False

        fringe = [component_type]

        while fringe:
            subtype = fringe.pop()
            fringe += subtype.__subclasses__()

            if subtype in self._entities[entity]:
                return True

        return False

    def entity_exists(self, entity: Hashable) -> bool:
        """Check if a specific entity exists.

        Empty entities (with no components) and dead entities (destroyed
        by :meth:`delete_entity`) will not count as existing ones.
        """
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        return entity in self._entities and entity not in self._dead_entities

    def get(self, component_type: type[C]) -> list[tuple[Hashable, C]]:
        """Retrieve all stored components of the given type.

        Subtypes are also checked. Return value is a list of pairs
        where the first item is the entity id of the component's owner.
        The second item of the pair is the actual queried component.
        """
        return list(self._get(component_type))

    def _get(self, component_type: type[C]) -> Iterable[tuple[Hashable, C]]:
        """Retrieve all stored components of the given type.

        Subtypes are also checked. Return value is a generator of pairs
        where the first item is the entity id of the component's owner.
        The second item of the pair is the actual queried component.

        This method is for internal use. Public method :meth:`get`
        (TODO) returns cached results from this method.
        """
        fringe = [component_type]

        while fringe:
            subtype = fringe.pop()
            fringe += subtype.__subclasses__()

            for entity in self._components.get(subtype, []):
                yield entity, self._entities[entity][subtype]

    def get_component(self, entity: Hashable, component_type: type[C],
                      default: T = None) -> Union[C, T]:
        """Retrieve a component from an entity, if the entity owns one.

        Subtypes are also checked. Priority goes to the specified type.
        If no components for the given type are found, ``default``
        value is returned.
        """
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        fringe = [component_type]

        while fringe:
            subtype = fringe.pop()

            if subtype in self._entities.get(entity, {}):
                return self._entities[entity][subtype]

            fringe += subtype.__subclasses__()

        return default

    def get_components(self, entity: Hashable) -> tuple[C]:
        """Retrieve a tuple of all components from an entity."""
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        return tuple(self._entities.get(entity, {}).values())

    def delete_entity(self, entity: Hashable, immediate=False) -> None:
        """Delete an entity.

        Delete an entity and all of it's assigned component instances
        from the world. By default, Entity deletion is delayed until
        the next call to :meth:`process` (override this behaviour with
        the ``immediate`` flag). This should generally not be
        done during entity iteration (:meth:`get`).

        Raises a ``KeyError`` if the given entity does not exist.
        """
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        if immediate:
            for component_type in self._entities[entity]:
                self._components[component_type].discard(entity)

                if not self._components[component_type]:
                    del self._components[component_type]

            del self._entities[entity]

        else:
            self._dead_entities.add(entity)

    def _clear_dead_entities(self):
        """Finalize deletion of any entities marked as dead.

        In the interest of performance, this method duplicates code from
        the :meth:`delete_entity` method. If that method is changed,
        those changes should be duplicated here as well.
        """
        for entity in self._dead_entities:

            for component_type in self._entities[entity]:
                self._components[component_type].discard(entity)

                if not self._components[component_type]:
                    del self._components[component_type]

            del self._entities[entity]

        self._dead_entities.clear()

    def remove_component(self, entity: Hashable, component_type: type[C]):
        """Remove a component from an entity, if the entity owns one.

        Subtypes are also checked, but only the first matching component
        is actually removed. Priority goes to the specified type.
        The removed component is returned (if any), ``None`` otherwise.
        """
        assert isinstance(entity, Hashable), (
            f'Entity ID must be hashble, found {entity}, which is not')

        removed = None
        fringe = [component_type]

        while fringe:
            subtype = fringe.pop()

            if subtype in self._entities.get(entity, {}):
                self._components[subtype].discard(entity)

                # Free dict entry for a component type when empty
                if not self._components[subtype]:
                    del self._components[subtype]

                if subtype in self._entities.get(entity, {}):
                    removed = self._entities[entity][subtype]
                    del self._entities[entity][subtype]

                # Free dict entry for an entity if empty
                if not self._entities[entity]:
                    del self._entities[entity]

                if removed is not None:
                    # No need to check if it is an handler, just check
                    # if it implements the interface.
                    if not hasattr(removed, '__events__'):
                        return removed

                    # Code replication
                    # If dispatching is enabled, call on_remove directly
                    # to gain performance. Otherwise an event is dispatched
                    if (ON_REMOVE_EVENT_NAME in removed.__events__
                            and self._dispatch_enabled):
                        getattr(removed,
                                removed.__events__[ON_REMOVE_EVENT_NAME])(
                                    entity, self)
                    # on_add exists but dispatching is disabled
                    elif not self._dispatch_enabled:
                        self.dispatch('on_component_dispatch',
                                      ON_REMOVE_EVENT_NAME,
                                      removed, entity)

                    return removed

            fringe += subtype.__subclasses__()

        return removed

    def add_processor(self, processor: Processor,
                      priority: Optional[int] = None):
        """Add a processor into the system.

        ``priority`` defines the order of execution upon calling
        :meth:`process`. Lower priorities are processed first. If not
        given, the internally defined default priority for the given
        processor's type is used (see :class:`Processor`).

        If a processor of the same exact type is present, it will be
        replaced.
        """
        assert isinstance(processor, Processor), (
            f'{processor} is not of type Processor')
        assert isinstance(priority, int) or priority is None, (
            f'{priority} is not of type int')

        processor_type = type(processor)
        if processor_type in self._processors:
            self.remove_processor(processor_type)

        if priority is not None:
            processor.priority = priority

        bisect.insort(self._sorted_processors, processor)
        self._processors[processor_type] = processor

    @property
    def processors(self) -> tuple[Processor]:
        return tuple(self._sorted_processors)

    def process(self, *args, **kwargs):
        """Execute code from all processors, in order of their priority.

        (TBD)
        """
        self._clear_dead_entities()
