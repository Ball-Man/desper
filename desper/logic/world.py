""":class:`World` and :class:`Processor` main definitions."""
import abc
from itertools import count
from typing import (Hashable, Any, TypeVar, Iterable, Union, Optional,
                    Callable, SupportsFloat)

import desper.bisect as bisect
from desper.events import EventDispatcher, event_handler

C = TypeVar('C')
T = TypeVar('T')

ON_ADD_EVENT_NAME = 'on_add'
ON_REMOVE_EVENT_NAME = 'on_remove'
ON_SINGLE_DISPATCH_EVENT_NAME = 'on_single_dispatch'


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
    def process(self, dt: SupportsFloat = 1):
        """Implement this method in a subclass to provide your logic."""


P = TypeVar('Processor', bound=Processor)


@event_handler(on_single_dispatch='_on_single_dispatch')
class World(EventDispatcher):
    """Main container for entities and components."""

    def __init__(self,
                 id_generator_factory: Callable[[], Iterable]
                 = lambda: count(1)):
        super().__init__()

        # Listen to self dispatched events
        self.add_handler(self)

        self._sorted_processors: list[Processor] = []
        self._processors: dict[type[Processor], Processor] = {}

        self.id_generator_factory = id_generator_factory
        self.id_generator = self.id_generator_factory()

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
                elif (ON_ADD_EVENT_NAME in component.__events__
                        and not self._dispatch_enabled):
                    self.dispatch(ON_SINGLE_DISPATCH_EVENT_NAME,
                                  ON_ADD_EVENT_NAME,
                                  component, entity_id, self)

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

        # Manage replaced components
        if component_type in self._entities.get(entity, {}):
            self.remove_component(entity, component_type)

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
            elif (ON_ADD_EVENT_NAME in component.__events__
                    and not self._dispatch_enabled):
                self.dispatch(ON_SINGLE_DISPATCH_EVENT_NAME, ON_ADD_EVENT_NAME,
                              component, entity, self)

    def _on_single_dispatch(self, event, handler, *args):
        """Dispatch the given event to a single handler.

        Designed to be used when adding or removing
        components/processors while dispatching is disabled. A World
        is always a handler of itself, listening to this event to relay
        ``on_add`` and ``on_remove`` events.
        """
        getattr(handler, handler.__events__[event])(*args)

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

    @property
    def entities(self) -> tuple[Hashable]:
        """Retrieve all the living entities in the system."""
        return tuple(entity for entity in self._entities
                     if entity not in self._dead_entities)

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

            for component_type, component in self._entities[entity].items():
                self._components[component_type].discard(entity)

                if not self._components[component_type]:
                    del self._components[component_type]

                # Event handling
                if (hasattr(component, '__events__')
                        and ON_REMOVE_EVENT_NAME in component.__events__):
                    # Code replication
                    # If dispatching is enabled, call on_remove directly
                    # to gain performance. Otherwise an event is dispatched
                    if (ON_REMOVE_EVENT_NAME in component.__events__
                            and self._dispatch_enabled):
                        getattr(component,
                                component.__events__[ON_REMOVE_EVENT_NAME])(
                                    entity, self)
                    # on_add exists but dispatching is disabled
                    elif not self._dispatch_enabled:
                        self.dispatch(ON_SINGLE_DISPATCH_EVENT_NAME,
                                      ON_REMOVE_EVENT_NAME,
                                      component, entity, self)

                    self.remove_handler(component)

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
                        self.dispatch(ON_SINGLE_DISPATCH_EVENT_NAME,
                                      ON_REMOVE_EVENT_NAME,
                                      removed, entity, self)

                    self.remove_handler(removed)
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

        bisect.insort(self._sorted_processors, processor,
                      key=lambda p: p.priority)
        self._processors[processor_type] = processor

        processor.world = self

        # Event handling, if processor is an event handler for the
        # special event on_add, manage it
        # For performance reasons, check for the __events__ attribute
        # instead of using isinstance
        if hasattr(processor, '__events__'):
            self.add_handler(processor)

            # If dispatching is enabled, call on_add directly to gain
            # performance. Otherwise an event is dispatched
            if (ON_ADD_EVENT_NAME in processor.__events__
                    and self._dispatch_enabled):
                getattr(processor,
                        processor.__events__[ON_ADD_EVENT_NAME])()
            # on_add exists but dispatching is disabled
            elif (ON_ADD_EVENT_NAME in processor.__events__
                    and not self._dispatch_enabled):
                self.dispatch(ON_SINGLE_DISPATCH_EVENT_NAME, ON_ADD_EVENT_NAME,
                              processor)

    def remove_processor(self, processor_type: type[P]) -> Optional[P]:
        """Remove a processor of the given type from the system.

        If it exists. Subtypes are also checked.
        """
        assert issubclass(processor_type, Processor), (
            f'{processor_type} is not of a subtype of Processor')

        fringe = [processor_type]

        while fringe:
            subtype = fringe.pop()

            if subtype in self._processors:
                removed = self._processors[subtype]

                # Filter based on type instead of using list.remove
                # as definitions of __eq__ could make it inconsistent.
                self._sorted_processors = list(
                    filter(lambda p: type(p) is not subtype,
                           self._sorted_processors))
                del self._processors[subtype]

                # Event handling for on_remove event
                # Code duplication, see add_processor
                if not hasattr(removed, '__events__'):
                    return removed

                # If dispatching is enabled, call on_remove directly to gain
                # performance. Otherwise an event is dispatched
                if (ON_REMOVE_EVENT_NAME in removed.__events__
                        and self._dispatch_enabled):
                    getattr(removed,
                            removed.__events__[ON_REMOVE_EVENT_NAME])()
                # on_add exists but dispatching is disabled
                elif not self._dispatch_enabled:
                    self.dispatch(ON_SINGLE_DISPATCH_EVENT_NAME,
                                  ON_REMOVE_EVENT_NAME, removed)

                self.remove_handler(removed)
                return removed

            fringe += subtype.__subclasses__()

    def get_processor(self, processor_type: type[P]) -> Optional[P]:
        """Get a processor of the given type from the system.

        If it exists. Subtypes are also checked.
        """
        fringe = [processor_type]

        while fringe:
            subtype = fringe.pop()

            if subtype in self._processors:
                return self._processors[subtype]

            fringe += subtype.__subclasses__()

        return None

    @property
    def processors(self) -> tuple[Processor]:
        return tuple(self._sorted_processors)

    def process(self, dt: SupportsFloat = 1):
        """Execute code from all processors, in order of their priority.

        Stored :class:`Processor`s are executed according to their
        ascending priority. In particular, :meth:`Processor.process`
        is called for each of them.
        """
        self._clear_dead_entities()

        for processor in self._sorted_processors:
            processor.process(dt)

    def clear(self):
        """Clear the entire database.

        Removal events are dispatched (``on_remove``).
        Pending events (in case of disabled dispatching) are not.
        Entities are removed before processors.
        """
        for entity in tuple(self._entities):
            self.delete_entity(entity, immediate=True)
        self._dead_entities.clear()

        for processor in tuple(self._sorted_processors):
            self.remove_processor(type(processor))

        self.id_generator = self.id_generator_factory()

        super().clear()     # Clear event dispatching system
