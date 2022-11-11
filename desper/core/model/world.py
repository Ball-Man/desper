"""Default resources for worlds."""
import copy
import json
import functools
import importlib
import re
from collections import deque
from typing import Callable, Sequence, Any

from desper.core.model import Handle
from desper.core.logic import World

ON_WORLD_LOAD_EVENT_NAME = 'on_world_load'

OBJECT_STRING_REGEX = re.compile(r'\$\{(.+)\}')
RESOURCE_STRING_REGEX = re.compile(r'\$res\{(.+)\}')


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


class WorldFromFileHandle(WorldHandle):
    """Specialized handle for loading worlds from file."""

    def __init__(self, filename: str):
        super().__init__()

        self.filename = filename
        self.fromfile_transformer = WorldFromFileTransformer
        self.transform_functions.append(self.fromfile_transformer)


class WorldFromFileTransformer:
    """Populate a :class:`World` from file.

    Callable to be used as transfomer function in class:`WorldHandle`.
    """

    def __init__(self,
                 dict_transformers:
                 Sequence[Callable[[WorldHandle, World, dict, dict], None]]
                 = tuple()):
        self.dict_transformers = dict_transformers

    def __call__(self, world_handle: WorldFromFileHandle, world: World):
        """Apply processor and component transformers."""
        with open(world_handle.filename) as fin:
            world_dict = json.load(fin)

        # Apply transformers on processor dictionaries
        for processor_dict in world_dict.get('processors', []):
            self._apply_transformers(world_handle, world, processor_dict)

        # Apply transformers on component dictionaries
        for entity_dict in world_dict.get('entities', []):
            for component_dict in entity_dict.get('components', []):
                self._apply_transformers(world_handle, world, component_dict)

        populate_world_from_dict(world, world_dict)

    def _apply_transformers(self, world_handle: WorldFromFileHandle,
                            world: World, data_dict: dict):
        """Apply all transformers on the given world with given data."""
        for transformer in self.dict_transformers:
            passthrough_dict = data_dict
            initial_dict = copy.deepcopy(passthrough_dict)

            try:
                # Only the passthrough dict is supposed to be modifiable
                transformer(world_handle, world, initial_dict,
                            passthrough_dict)
            except Exception as ex:
                # Relay exceptions and add information
                raise type(ex)(
                    f"While loading World from file {world_handle.filename}, "
                    f"\non dictionary: {data_dict}\n"
                    f"with dict transformer: {transformer}\n"
                    + str(ex))


@functools.lru_cache()
def object_from_string(name: str) -> Any:
    """Retrieve object from namespace given its string name.

    The name shall be in the form: ``package.subpackage.etc.obj_name``.
    """
    assert isinstance(name, str), f'{name} is not a string'

    name_split = name.split('.')

    # Import the module itertively
    module = None
    for i, _ in enumerate(name_split):
        try:
            module = importlib.import_module(
                '.'.join(name_split[0 : i + 1]))        # NOQA
        except ModuleNotFoundError:
            i -= 1
            break

    if module is None:
        raise ModuleNotFoundError(
            f'No module named {name_split[0]}')

    # Import subcomponents from module
    last_index = i + 1
    comp = module
    for comp_str in name_split[last_index:]:
        comp = getattr(comp, comp_str)

    return comp


def type_dict_transformer(world_handle: WorldFromFileHandle, world: World,
                          initial_dict: dict, passthrough_dict: dict):
    """Dict transformer, use with :class:`WorldFromFileTransformer`.

    Translates string types (key "type") into actual types. Only
    callables are accepted.
    """
    type_object = object_from_string(passthrough_dict['type'])

    if not callable(type_object):
        raise TypeError(f'Trying to use {type_object} as component type, '
                        'which is not a callable')

    passthrough_dict['type'] = type_object


def object_dict_transformer(world_handle: WorldFromFileHandle, world: World,
                            initial_dict: dict, passthrough_dict: dict):
    """Dict transformer, use with :class:`WorldFromFileTransformer`.

    Resolves certain string arguments (keys "args" and "kwargs") into
    corresponding objects. In particular, strings in the form:
    ``${package.subpackage.etc.obj_name}``, that is, that match the
    regex :attr:`OBJECT_STRING_REGEX`.

    Internally, :func:`object_from_string` is used to resolve the
    object.
    """
    def map_function(arg):
        if not isinstance(arg, str):        # Skip non-strings
            return

        match = OBJECT_STRING_REGEX.match(arg)
        if match is not None:
            return object_from_string(match.groups()[0])

    args_list = passthrough_dict.get('args', [])
    kwargs_map = passthrough_dict.get('kwargs', {})

    args_list[:] = map(map_function, args_list)
    kwargs_map.update({k: map_function(v) for k, v in kwargs_map.items()})
