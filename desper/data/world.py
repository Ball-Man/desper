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
        for ent, comp in self.world.get_components(AbstractComponent):
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
    pass
