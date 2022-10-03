"""Desper's logic module.

Entities are collections of components (Python objects) catalogued in
centralized :class:`World`s.
"""
from typing import Protocol, Optional, Hashable

from desper.core.events import event_handler
from .world import *        # NOQA

C = TypeVar('C')


class ControllerProtocol(Protocol):
    """Protocol for special components, aware of their world."""
    world: Optional[World] = None
    entity: Optional[Hashable] = None


def add_component(controller: ControllerProtocol, component):
    """Add a component to the entity represented by given controller.

    A shorthand for controllers on :meth:`World.add_component`.
    """
    controller.world.add_component(controller.entity, component)


def remove_component(controller: ControllerProtocol,
                     component_type: type[C]) -> C:
    """Remove a component from the entity represented by controller.

    A shorthand for controllers on :meth:`World.remove_component`.
    """
    return controller.world.remove_component(controller.entity, component_type)


def has_component(controller: ControllerProtocol,
                  component_type: type[C]) -> bool:
    """Get whether the entity represented by controller has a component.

    A shorthand for controllers on :meth:`World.has_component`.
    """
    return controller.world.has_component(controller.entity, component_type)


def get_component(controller: ControllerProtocol,
                  component_type: type[C]) -> C:
    """Retrieve a component from the entity represented by controller.

    A shorthand for controllers on :meth:`World.get_component`.
    """
    return controller.world.get_component(controller.entity, component_type)


def get_components(controller: ControllerProtocol) -> tuple[C]:
    """Retrieve all components from the entity represented by controller.

    A shorthand for controllers on :meth:`World.get_components`.
    """
    return controller.world.get_components(controller.entity)


def delete(controller: ControllerProtocol):
    """Delete entity represented by the controller.

    A shorthand for controllers on :meth:`World.delete_entity`.
    """
    controller.world.delete_entity(controller.entity)


@event_handler('on_add')
class Controller:
    """Special component, aware of their world and entity id.

    This awareness is resolved during the ``on_add`` event. For this
    reason, a base implementation of this method is provided. If
    overridden, a super call is necessary.
    """
    world: Optional[World] = None
    entity: Optional[Hashable] = None

    def on_add(self, entity: Hashable, world: World):
        """Store given entity id and world instance.

        If overridden, a super call is necessary.
        """
        self.entity = entity
        self.world = world
