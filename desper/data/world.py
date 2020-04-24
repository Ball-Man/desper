import esper


class AbstractProcessor(esper.Processor):
    """An inheritance based processor.

    It's designed to work on AbstractComponents in an AbstractWorld(
    will process all subclasses of AbstractComponents thanks to
    the AbstractWorld working with subclasses).

    NB: Despite the name, it's not an abstract class(in polymorphic
    terms. While it's designed to be derived, it's not compulsive).
    """
    def process(world, *args, **kwargs):
        pass


class AbstractComponent:
    """An inheritance based component for an entity-component design.

    It's designed to be used with an AbstractProcessor.
    Any AbstractComponent subclass should implement the update method.
    """
    def update(world, *args, **kwargs):
        """Base method for main game logic.

        This method is called presumably at each frame(at each
        AbstractProcessor.process call).
        """
        raise NotImplementedError


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
