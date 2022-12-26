"""Desper's logic module.

Entities are collections of components (Python objects) catalogued in
centralized :class:`World`s.
"""
from typing import (Protocol, runtime_checkable, Optional, Hashable, Generic,
                    Callable, SupportsFloat)

from desper.events import event_handler
from .world import *        # NOQA
from .spatial import *      # NOQA
from .coroutines import *   # NOQA

C = TypeVar('C')
P = TypeVar('P', bound=Processor)

ON_UPDATE_EVENT_NAME = 'on_update'


@runtime_checkable
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

    add_component = add_component
    remove_component = remove_component
    has_component = has_component
    get_component = get_component
    get_components = get_components
    delete = delete


def controller(entity: Hashable, world: World) -> Controller:
    """Build a plain :class:`Controller` given a world and entity."""
    controller = Controller()
    controller.entity = entity
    controller.world = world

    return controller


class ComponentReference(Generic[C]):
    """Descriptor for easier cross-component access.

    Owner of component references descriptors shall implement the
    :class:`ControllerProtocol` protocol, that is, they shall provide
    ``world`` (:class:`World`) and ``entity`` attributes.

    Accessing this descriptor leads to a :meth:`World.get_component`
    query. Setting an element leads to :meth:`World.add_component` and
    deleting it (``del``) leads to :meth:`World.remove_component`.
    """

    def __init__(self, component_type: type[C]):
        self.component_type = component_type

    def __get__(self, obj: ControllerProtocol, objtype=None) -> C:
        """Retrieve component from the controller (owner), by type."""
        assert isinstance(obj, ControllerProtocol), (
            'Owner of ComponentRerefences must implement ControllerProtocol')

        return get_component(obj, self.component_type)

    def __set__(self, obj: ControllerProtocol, value: C):
        """Set component using the controller (owner)."""
        assert isinstance(obj, ControllerProtocol), (
            'Owner of ComponentRerefences must implement ControllerProtocol')
        assert isinstance(value, self.component_type), (
            f'Expected {self.component_type} (sub)object, got a {type(value)}')

        add_component(obj, value)

    def __delete__(self, obj: ControllerProtocol):
        """Remove component of the given type from the controller."""
        assert isinstance(obj, ControllerProtocol), (
            'Owner of ComponentRerefences must implement ControllerProtocol')

        remove_component(obj, self.component_type)


class ProcessorReference(Generic[P]):
    """Descriptor for easier processor access.

    Owner of processor references descriptors shall implement the
    :class:`ControllerProtocol` protocol, that is, they shall provide
    ``world`` (:class:`World`) and ``entity`` attributes.

    Accessing this descriptor leads to a :meth:`World.get_processor`
    query. Deleting (``del``) leads to :meth:`World.remove_processor`.

    When using the descriptor as setter, a new processor is set using
    :meth:`World.add_processor`. However, the ``priority`` parameter
    is not provided. This means that the default priority will be
    deduced through :attr:`Processor.priority`.
    """

    def __init__(self, processor_type: type[P]):
        assert issubclass(processor_type, Processor), (
            f'{processor_type} is not a subclass of Processor')

        self.processor_type = processor_type

    def __get__(self, obj: ControllerProtocol, objtype=None) -> P:
        """Retrieve processor from the controller (owner), by type."""
        assert isinstance(obj, ControllerProtocol), (
            'Owner of ComponentRerefences must implement ControllerProtocol')

        return obj.world.get_processor(self.processor_type)

    def __set__(self, obj: ControllerProtocol, value: P):
        """Set processor using the controller (owner)."""
        assert isinstance(obj, ControllerProtocol), (
            'Owner of ComponentRerefences must implement ControllerProtocol')
        assert isinstance(value, self.processor_type), (
            f'Expected {self.processor_type} (sub)object, got a {type(value)}')

        obj.world.add_processor(value)

    def __delete__(self, obj: ControllerProtocol):
        """Remove processor of the given type from the controller."""
        assert isinstance(obj, ControllerProtocol), (
            'Owner of ComponentRerefences must implement ControllerProtocol')

        obj.world.remove_processor(self.processor_type)


class Prototype:
    """Base class for prototypes.

    Define a type as a conglomerate of different components, with or
    without arguments.

    Creating entities with many (and complex) components can become
    quite verbose. Firstly, indentations and brackets can easily bloat
    code. Secondly, sometimes components do share some information,
    and repeating it is useless work.
    To work smarter and not harder, this class comes in help.

    | **Simple prototypes**

    The first use case is the simplest: define a conglomerate of
    components with no arguments (default constructor)::

        # Standard approach
        world.create_entity(ComponentA(), ComponentB(), ComponentC())

        # Prototype approach
        class PrototypeA(desper.Prototype):
            component_types = ComponentA, ComponentB, ComponentC

        world.create_entity(*PrototypeA())

    The default-initialized components are not too verbose even in the
    standard approach, but yet once the prototype is defined it can be
    used any time without having to remember the exact for of the
    conglomerate. In this case, we would say the standard approach is
    more error prone.

    Note that a prototype is an iterable that generates the given
    components (in fact, to correctly instantiate all the components
    in an entity the prototype instance has to be unpacked with a
    ``*`` expression).

    | **Complex prototypes**

    A second use case shows how using a prototype it is
    possible to remove bloat coming from indentation and redundancies.

    Arguments can be intuitively specified in the ``__init__`` method
    of this class. The user is free to specify whatever argument they
    want (no need for super calls).

    When instantiating the prototype, the class will eventually try and
    call some special methods for its component types (from now on,
    called init methods). If an init method is not found, the default
    constructor for that component is called (that is why and how the
    above example works, there is no need for init methods if all the
    components are instantiated without specifying parameters).
    By default, init methods follow this naming rule::

        ...
        def init_Component(self, component_type: type[Component]) -> Component:
            ...

    The return type has to be ``Component`` (for obvious reasons).

    e.g::

        # Standard approach
        w.create_entity(example.Position(x + offset_x,
                                         y + offset_y),
                        example.Sprite(x + offset_x, y + offset_y,
                                       image, offset_x,
                                       offset_y),
                        example.EnemyBehaviour())

        # Prototype approach
        class EnemyPrototype(desper.Prototype):
            component_types = (example.Position, example.Sprite,
                               example.EnemyBehaviour)

            def __init__(self, x, y, image, offset_x, offset_y):
                self.xx = x + offset_x
                self.yy = y + offset_y
                self.image = image
                self.offset_x = offset_x
                self.offset_y = offset_y

            def init_Position(self, component_type):
                return component_type(self.xx, self.yy)

            def init_Sprite(self, component_type):
                return component_type(self.xx, self.yy, self.image,
                                      self.offset_x, self.offset_y)

        w.create_entity(*EnemyPrototype(x, y, image, offset_x, offset_y))

    With the prototype approach you invest a few more lines,
    but will save time and effort every time that a new
    ``EnemyPrototype`` has to be instantiated. It is basically, a more
    structured way of making a free function that instantiates a set
    of components.

    Note that since the ``EnemyBehaviour`` had no arguments, no init
    method is defined for it.
    """
    component_types: tuple[type] = tuple()
    """List of types of the prototype's components."""

    init_methods: dict[type[C], Callable[[type[C]], C]] = dict()
    """Dictionary in the format ``{type: function}``.

    Used to specify custom functions instead of the standard
    init method (using :py:attr:`init_prefix`). The entries from this
    dictionary are prioritized (the standard init method will be
    ignored if an entry for that component type is given).

    This is also useful when name conflicts occur (same class name but
    different namespace).
    """

    init_prefix = 'init_'
    """Prefix for the init methods."""

    def _default_init(self, component_type: type[C]) -> C:
        """Init component with default constructor.

        Used as default init method.
        """
        return component_type()

    def __iter__(self):
        """Yield instantiated components."""
        return (self.init_methods.get(
                comp_t,
                getattr(self, f'{self.init_prefix}{comp_t.__name__}',
                        self._default_init))(comp_t)
                for comp_t in self.component_types)


class OnUpdateProcessor(Processor):
    """Dispatch :attr:`ON_UPDATE_EVENT_NAME` event at each frame.

    The event carries one decimal parameter, the delta time.
    """

    def process(self, dt: SupportsFloat = 1):
        """Dispatch event."""
        self.world.dispatch(ON_UPDATE_EVENT_NAME, dt)
