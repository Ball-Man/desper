"""Desper's logic module.

Entities are collections of components (Python objects) catalogued in
centralized :class:`World`s.
"""
from itertools import count
from typing import Hashable, Any, TypeVar

from desper.core.events import EventDispatcher

C = TypeVar('C')

ON_ADD_EVENT_NAME = 'on_add'


class World(EventDispatcher):
    """Main container for entities and components."""

    def __init__(self, id_generator=count(1)):
        super().__init__()

        self._processors = []
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

        # Code duplication for performance
        for component in components:
            component_type = type(component)
            if component_type not in self._components:
                self._components[component_type] = set()

            self._components[component_type].add(entity_id)

            if entity_id not in self._entities:
                self._entities[entity_id] = {}

            self._entities[entity_id][component_type] = component

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

            if (ON_ADD_EVENT_NAME in component.__events__
                    and self._dispatch_enabled):
                getattr(component,
                        component.__events__[ON_ADD_EVENT_NAME])(entity, self)
            # TODO: on_add exists but dispatching is disabled
            elif not self._dispatch_enabled:
                pass


    def has_component(self, entity: Hashable, component_type: type[C]) -> bool:
        """Check whether an entity has a component of the given type.

        Subtypes are also checked.
        """
        if entity not in self._entities:
            return False

        fringe = [component_type]

        while fringe:
            subtype = fringe.pop()
            fringe += subtype.__subclasses__()

            if subtype in self._entities[entity]:
                return True

        return False
