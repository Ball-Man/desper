import queue

import esper


class AbstractComponent:
    """An inheritance based component for an entity-component design.

    It's designed to be used with an AbstractProcessor.
    Any AbstractComponent subclass should implement the update method.
    """

    def update(self, world, *args, **kwargs):
        """Base method for main game logic.

        This method is called presumably at each frame(at each
        AbstractProcessor.process call).

        :param world: The world to which the component is bound.
        """
        raise NotImplementedError


class AbstractProcessor(esper.Processor):
    """An inheritance based processor.

    It's designed to work on AbstractComponents in an AbstractWorld(
    will process all subclasses of AbstractComponents thanks to
    the AbstractWorld working with subclasses).

    NB: Despite the name, it's not an abstract class(in polymorphic
    terms. While it's designed to be derived, it's not compulsive).
    """

    def process(self, *args, **kwargs):
        """Base method for main game logic.

        This method calls AbstractComponent.update on all the
        AbstractComponents in his bound world. If bound to an
        AbstractWorld this means calling all the update methods of all
        the instances deriving from AbstractComponent.
        """
        for ent, comp in self.world.get_component(AbstractComponent):
            comp.update(self.world)


class AbstractWorld(esper.World):
    """An AbstractWorld keeps track of the game state(or part of it).

    It contains a collection of all the Entity/Component assignments.
    It's designed for being used with AbstractComponents and
    AbstractProcessors. Basically, this emulates an inheritance-based
    Entity-Component design through specialization of an ECS design.
    (that is esper.World).

    NB: Despite the name, it's not an abstract class(in polymorphic
    terms. While it's designed to be derived, it's not compulsive).
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
        requested, which is empty if the component doesn't exist.
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
