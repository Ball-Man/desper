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
