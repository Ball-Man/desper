import queue
import weakref

import esper


class AbstractComponent:
    """An inheritance based component for an entity-component design.

    It's designed to be used with an :class:`AbstractProcessor`.
    Any :class:`AbstractComponent` subclass should implement the update
    method.
    """

    def update(self, entity, world, *args, **kwargs):
        """Base method for main game logic.

        This method is called presumably at each frame(at each
        :py:meth:`AbstractProcessor.process` call).

        :param entity: The entity ID owning this component.
        :param world: The world to which the component is bound.
        """
        raise NotImplementedError


class OnAttachListener:
    """An interface that enables components to be initialized.

    When a component is added to an :class:`AbstractWorld`, the
    :py:attr:`on_attach` method from this interface will be called(
    if implemented).

    Note: Unfortunately, during the attach event there is no direct
        access to eventual resource dictionaries(like the on from
        :class:`GameModel` ).

    Note that this won't work with standard ecs worlds(esper ``World``),
    but it's meant to be used with :class:`AbstractWorld`.
    """

    def on_attach(self, entity, world):
        raise NotImplementedError


class Controller(AbstractComponent, OnAttachListener):
    """A convenience class for easy access to entity components.

    A Controller is both a :class:`AbstractComponent` and a
    :class:`OnAttachListener`, that implements a convenience
    :py:meth:`get` method that retrieves and caches components from the
    given entities and a :py:meth:`processor` method that retrieves
    and caches processors from the current :class:`AbstractWorld` .

    The :py:meth:`on_attach` implementation for this class also
    saves as instance attributes the component's entity id and world,
    in :py:attr:`entity` and :py:attr:`world`.

    If you implement :py:meth:`on_attach` or a constructor, a call to
    `super` is required.
    For the :py:meth:`update` method no call to super is required.

    Note: This class will only work if all the used components and
    processors support weakrefs(e.g. builtin types don't).

    Note: This class can't be used with pure ecs ``esper.World`` and
    should instead be used with :class:`AbstractWorld` .
    """

    def __init__(self):
        self._component_cache = weakref.WeakValueDictionary()
        self._processor_cache = weakref.WeakValueDictionary()
        self.world: AbstractWorld = None
        self.entity = None

    def on_attach(self, entity, world):
        self.entity = entity
        self.world = world

    def get(self, component_type):
        """Retrieve a component from the same entity of this component.

        This method will retrieve and cache for quick access a component
        of the given type, from the same entity containing this
        Controller component.

        All subtypes of the given type will be searched, but once a
        component is found querying the same type will always lead to
        the same component(as long as the component is kept alive inside
        the game). This means that if you want prioritize some types
        (e.g. the base type over the subclasses) you should manually
        call the :class:`AbstractWorld` methods using :py:attr:`world`
        and :py:attr:`entity`.

        :param component_type: The given component type to find inside
                               the entity.
        :return: A component instance that implements the given type.
        :raises KeyError: If the ``component_type`` isn't found.
        :raises TypeError: If the ``component_type`` doesn't support
                           weakrefs.
        """
        cache_entry = self._component_cache.get((component_type, self.world))
        if cache_entry is None:
            comp = self.world.component_for_entity(self.entity, component_type)
            self._component_cache[(component_type, self.world)] = comp
            return comp

        return cache_entry

    def processor(self, processor_type):
        """Retrieve a processor from the current world.

        This method will retrieve and cache for quick access a processor
        of the given type, from the current world. Only the exact type
        will be checked, not subtypes(like when using
        :py:meth:`AbstractWorld.get_processor` .

        Note that using this method is generally more efficient than
        iterating over :py:meth:`AbstractWorld.get_processor`, since
        the results will be cached.

        :param processor_type: The type of the processor to search for.
        :return: The processor instance of type ``processor_type`` if
                 found. None otherwise.
        """
        cache_entry = self._processor_cache.get((processor_type, self.world))

        if cache_entry is None:
            proc = self.world.get_processor(processor_type)
            if proc is not None:
                self._processor_cache[(processor_type, self.world)] = proc
                return proc

            return None

        return cache_entry


class AbstractProcessor(esper.Processor):
    """An inheritance based processor.

    It's designed to work on :class:`AbstractComponents` in an
    :class:`AbstractWorld` (will process all subclasses of
    AbstractComponents thanks to the AbstractWorld working with
    subclasses).

    NB: Despite the name, it's not an abstract class(in polymorphic
    terms. While it's designed to be derived, it's not compulsive).
    """

    def process(self, *args, **kwargs):
        """Base method for main game logic.

        This method calls :py:meth:`AbstractComponent.update` on all the
        :class:`AbstractComponent` s in his bound world. If bound to an
        :class:`AbstractWorld` this means calling all the update methods
        of all the instances deriving from AbstractComponent.
        """
        for ent, comp in self.world.get_component(AbstractComponent):
            comp.update(ent, self.world, *args, **kwargs)


class AbstractWorld(esper.World):
    """An AbstractWorld keeps track of the game state(or part of it).

    It contains a collection of all the Entity/Component assignments.
    It's designed for being used with :class:`AbstractComponent` s and
    :class:`AbstractProcessor` s. Basically, this emulates an
    inheritance-based Entity-Component design through specialization of
    an ECS design (that is esper.World).

    NB: Despite the name, it's not an abstract class(While it's designed
    to be derived, it's not compulsive).
    """

    def _get_component(self, component_type):
        """Get an iterator for Entity, Component pairs.

        :param component_type: The Component type to retrieve(will scan
        all subtypes).
        :return: An iterator for (Entity, Component) tuples.
        """
        entity_db = self._entities

        q = queue.SimpleQueue()
        q.put(component_type)
        while not q.empty():
            ex_type = q.get()

            for type_ in ex_type.__subclasses__():
                q.put(type_)

            for entity in self._components.get(ex_type, []):
                yield entity, entity_db[entity][ex_type]

    def component_for_entity(self, entity, component_type):
        """Retrieve a Component instance for a specific Entity.

        Retrieve a Component instance for a specific Entity. In some
        cases, it may be necessary to access a specific Component
        instance. For example: directly modifying a Component to handle
        user input.
        This will retrieve the Component based on its hierarchy, meaning
        that if a base-class type is requested, the output could be an
        instance of a derived class. Priority goes to the base class.

        :raises KeyError: If the given Entity and Component do not
                          exist.
        :param entity: The Entity ID to retrieve the Component for.
        :param component_type: The Component instance you wish to
                               retrieve.
        :return: The Component instance requested for the given Entity
                 ID.
        """
        ent_components = self._entities[entity]

        q = queue.SimpleQueue()
        q.put(component_type)

        while not q.empty():
            ex_type = q.get()

            if ex_type in ent_components:
                return ent_components[ex_type]

            [q.put(subtype) for subtype in ex_type.__subclasses__()]

        raise KeyError

    def try_component(self, entity, component_type):
        """Try to get a single component type for an Entity.

        This method will return the requested Component if it exists,
        but will pass silently if it does not. This allows a way to
        access optional Components that may or may not exist, without
        having to first querty the Entity to see if it has the Component
        type. Like with component_for_entity, this checks for subtypes.

        :param entity: The Entity ID to retrieve the Component for.
        :param component_type: The Component instance you wish to
                               retrieve.
        :return: A iterator containg the single Component instance
                 requested, which is empty if the component doesn't
                 exist.
        """
        # For performance reasons, the code is replicated from
        # component_for_entity
        ent_components = self._entities[entity]

        q = queue.SimpleQueue()
        q.put(component_type)

        while not q.empty():
            ex_type = q.get()

            if ex_type in ent_components:
                return ent_components[ex_type]

            [q.put(subtype) for subtype in ex_type.__subclasses__()]

    def has_component(self, entity, component_type):
        """Check if a specific Entity has a Component of a certain type.

        This checks for subtypes of the component_type too.

        :param entity: The Entity you are querying.
        :param component_type: The type of Component to check for.
        :return: True if the Entity has a Component of this type,
                 otherwise False
        """
        q = queue.SimpleQueue()
        q.put(component_type)

        while not q.empty():
            ex_type = q.get()

            if ex_type in self._entities[entity]:
                return True

            [q.put(subtype) for subtype in ex_type.__subclasses__()]

        return False

    def has_components(self, entity, *component_types):
        """Check if an Entity has all of the specified Component types.

        This checks for the subtypes of all the given component types
        too.

        :param entity: The Entity you are querying.
        :param component_types: Two or more Component types to check
                                for.
        :return: True if the Entity has all of the Components,
                 otherwise False
        """
        # For performance reasons, code is partially replicated from
        # has_component
        for component_type in component_types:
            q = queue.SimpleQueue()
            q.put(component_type)

            found = False
            while not q.empty():
                ex_type = q.get()

                found = found or ex_type in self._entities[entity]

                [q.put(subtype) for subtype in ex_type.__subclasses__()]

            if not found:
                return False

        return True

    def remove_component(self, entity, component_type):
        """Remove a Component instance from an Entity, by type.

        A Component instance can be removed by providing it's base type.
        For example: world.delete_component(enemy_a, Velocity) will
        remove the Velocity instance from the Entity enemy_a.

        This will remove one component, based on its base type.

        :raises KeyError: If either the given entity or Component type
                          are not found in the database.
        :param entity: The Entity to remove the Component from.
        :param component_type: The type of the Component to remove.
        :return: The entity ID which had its component removed.
        """
        q = queue.SimpleQueue()
        q.put(component_type)

        while not q.empty():
            ex_type = q.get()

            if ex_type in self._entities[entity]:
                self._components[component_type].discard(entity)

                if not self._components[ex_type]:
                    del self._components[ex_type]

                del self._entities[entity][ex_type]

                if not self._entities[entity]:
                    del self._entities[entity]

                self.clear_cache()
                return entity

            [q.put(subtype) for subtype in ex_type.__subclasses__()]

        raise KeyError

    def add_component(self, entity, component_instance, on_attach=True):
        """Add a new Component instance to an Entity.

        Add a Component instance to an Entiy. If a Component of the same
        type is already assigned to the Entity, it will be replaced.

        If the given `component_type` implements
        :class:`OnAttachListener`, the
        :py:meth:`OnAttachListener.on_attach` method will be called.
        The arguments passed to the listener are ``entity`` and the
        current :class:`AbstractWorld` (from the world point of view,
        ``self``).

        :param entity: The Entity to associate the Component with.
        :param component_instance: A Component instance.
        :param on_attach: Whether the on_attach event should be
                          triggered.
        """
        component_type = type(component_instance)

        if component_type not in self._components:
            self._components[component_type] = set()

        self._components[component_type].add(entity)

        if entity not in self._entities:
            self._entities[entity] = {}

        self._entities[entity][component_type] = component_instance
        self.clear_cache()

        if on_attach and isinstance(component_instance, OnAttachListener):
            component_instance.on_attach(entity, self)

    def create_entity(self, *components, on_attach=True):
        """Create a new Entity.
        This method returns an Entity ID, which is just a plain integer.
        You can optionally pass one or more Component instances to be
        assigned to the Entity.
        :param components: Optional components to be assigned to the
               entity on creation.
        :param on_attach: Whether the on_attach event should be
                          triggered.
        :return: The next Entity ID in sequence.
        """
        self._next_entity_id += 1

        # TODO: duplicate add_component code here for performance
        for component in components:
            self.add_component(self._next_entity_id, component, False)

        # Trigger on_attach event
        if on_attach:
            for component in components:
                if isinstance(component, OnAttachListener):
                    component.on_attach(self._next_entity_id, self)

        # self.clear_cache()
        return self._next_entity_id
