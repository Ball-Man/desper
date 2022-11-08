"""Default resources for worlds."""
from collections import deque
from typing import Callable

from desper.core.model import Handle
from desper.core.logic import World

ON_WORLD_LOAD_EVENT_NAME = 'on_world_load'


class WorldHandle(Handle[World]):
    """Base class for loading :class:`World` resources.

    An implementation of :meth:`load` is provided. Such implementation
    creates an empty :class:`World` (event dispatching disabled) and
    executes an ordered list of functions on it.

    Such functions are stored in :attr:`transform_functions`. Each
    function shall accept two arguments,
    the world handle (``self``) and the :class:`World` instance being
    loaded. Return values are discarded. Despite the name, any
    callable that meets the listed requirements is accepted (not only
    functions).

    The :attr:`ON_WORLD_LOAD_EVENT_NAME` event is dispatched at last.
    This happens after the entire execution of :meth:`load`. This event
    accepts two arguments, the world handle (``self``) and the
    :class:`World` instance being loaded.
    """

    def __init__(self):
        self.transform_functions: deque[
            Callable[['WorldHandle', World], None]] = deque()

    def load(self) -> World:
        """Create and return a new :class:`World`.

        Event dispatching is disabled by default. Transform functions
        are executed in order.

        At last, :attr:`ON_WORLD_LOAD_EVENT_NAME` is dispatched.
        """
        world = World()
        world.dispatch_enabled = False

        # Execute transform functions
        for transform_function in self.transform_functions:
            transform_function(self, world)

        world.dispatch(ON_WORLD_LOAD_EVENT_NAME, self, world)

        return world


def populate_world_from_dict(world: World, world_dict: dict):
    """Populate given world with data from dictionary.

    The given dictionary shall be formatted appropriately. In
    particular::

        {
            'processors': [
                {'type': ProcessorType, 'args': [...], 'kwargs': {...}},
                ...
            ],
            entities: [
                {
                    'id': ...,
                    'components': [
                        {'type': ComponentType, 'args': [...], 'kwargs' {...}},
                        ...
                    ],
                },

                ...
            ]
        }

    Each processor and entity listed in the dictionary will be
    instatiated by calling their classes (``type``) and by passing them
    ``args`` and ``kwargs`` accordingly. IDs for entities are optional
    (if omitted, the default id generator will be used, see
    :attr:`World.id_generator` and :attr:`World.id_generator_factory`).

    Processors are instantiated and added before entitites.
    """
    processors = world_dict.get('processors', [])
    entities = world_dict.get('entities', [])

    for processor_dict in processors:
        world.add_processor(
            processor_dict['type'](*processor_dict.get('args', []),
                                   **processor_dict.get('kwargs', {})))

    for entity_dict in entities:
        entity_id = entity_dict.get('id', None)

        components = []
        for component_dict in entity_dict.get('components', []):
            args = component_dict.get('args', [])
            kwargs = component_dict.get('kwargs', {})
            components.append(component_dict['type'](*args, **kwargs))

        world.create_entity(*components, entity_id=entity_id)
