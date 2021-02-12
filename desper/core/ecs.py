import inspect
import enum
from collections import deque
from dataclasses import dataclass, field
from typing import Any
import heapq
import esper


@dataclass(order=True)
class _WaitingGenerator:
    """Class used to contain a paused generator, for desper coroutines.

    Used by class :class:`CoroutineProcessor` to keep track of which
    generators are the next to be resumed.
    """
    generator: Any = field(compare=False)
    wait_time: int


class CoroutineState(enum.Enum):
    """Enumeration of possible states for a coroutine."""
    TERMINATED = 0
    PAUSED = 1
    ACTIVE = 2


class CoroutineProcessor(esper.Processor):
    """An ecs processor that manages coroutines.

    Note that with "coroutines" we **do not** mean python's
    `builtin coroutines <https://bit.ly/2FHc87u>`_. Builtin coroutines
    are asynchronous and consequently unstable for games(there might
    be instances in which python's coroutines can be helpful, but
    usually not for game logic). Desper coroutines are therefore
    generators(generator objects, precisely), which can be managed
    easily by a logic controller(this class).
    From now on, when "coroutine" is mentioned, "generator" is meant.

    Coroutines can be managed by two main methods, :py:meth:`start`,
    that will insert and start the coroutine into the system and
    :py:meth:`kill` that will stop and remove the coroutine from the
    system.
    The removed generator is returned, so that it can be started again
    if wanted by the user(the killed generator is simply removed,
    meaning that if reinserted with :py:meth:`start` it will resume
    from where it stopped).

    The coroutine will be called once per frame. To return the control
    use ``yield``.

    e.g::

        def coroutine():
            # Spawn enemies every 60 frames
            while True:
                spawn_enemies()
                yield 60

        # ...
        processor.start(coroutine())

    As shown in the example, when yielding a number(int) x the coroutine
    will be paused for x frames(60 frames in the example), and resumed
    immediately after.

    To stop a coroutine, use it's generator.

    e.g::

        def coroutine():
           # ...

        # ...
        gen = coroutine()       # Create generator
        processor.start(gen)    # Start coroutine
        # ...

        processor.kill(gen)     # Stop previously started coroutine

    When a coroutine ends(the generator terminates it's execution, when
    the end of the code is reached) it's automatically removed from
    execution.
    """

    def __init__(self, delta_factory=lambda: 1):
        self._generators = {}
        # Dictionary format: {generator: _WaitingGenerator}
        # _WaitingGenerator is None if the said generator isn't waiting.
        self._active_queue = deque((None,))
        self._wait_queue = []       # Heap
        self._timer = 0
        self.delta_factory = delta_factory

    def start(self, generator):
        """Add and start a coroutine, represented by a generator object.

        :param generator: The generator object representing the
                          coroutine.
        :return: The started generator object.
        :raises TypeError: If `generator` isn't a generator object.
        :raises ValueError: If `generator` is already being executed.
        """
        state = self.state(generator)

        if state != CoroutineState.TERMINATED:
            raise ValueError('Cannot start the same generator twice')

        self._active_queue.append(generator)
        self._generators[generator] = None
        return generator

    def kill(self, generator):
        """Stop and remove a coroutine, given the generator.

        Paused coroutines can be killed too.

        :param generator: The generator object representing the
                          coroutine.
        :return: The killed generator object.
        :raises TypeError: If `generator` isn't a generator object.
        :raises ValueError: If `generator` isn't being executed(has
                            already been killed or terminated it's
                            execution).
        """
        if not inspect.isgenerator(generator):
            raise TypeError('Only generator objects are accepted')

        # Sentinel is 0 since None is a valid element in the dictionary
        waiting_gen = self._generators.get(generator, 0)
        if waiting_gen == 0:
            raise ValueError('Generator not found')

        # Check in which queue the generator currently is
        if waiting_gen is None:
            self._active_queue.remove(generator)
        else:
            self._wait_queue.remove(waiting_gen)
        del self._generators[generator]

        return generator

    def state(self, generator):
        """Get the current state of the given coroutine.

        :param generator: The generator representing the coroutine.
        :return: A :class:`CoroutineState` instance representing
                 the state of the given coroutine.
                 If the coroutine isn't found
                 :py:attr:`CoroutineState.TERMINATED` will be returned.
        """
        if not inspect.isgenerator(generator):
            raise TypeError('Only generator objects are accepted')

        waiting_gen = self._generators.get(generator, 0)
        if waiting_gen == 0:
            return CoroutineState.TERMINATED

        # Check in which queue the generator currently is
        if waiting_gen is None:
            return CoroutineState.ACTIVE
        else:
            return CoroutineState.PAUSED

    def process(self, *args):
        """Process one frame of all the currently active coroutines.

        And unpause coroutines if necessary.
        """
        # Manage waiting coroutines
        if len(self._wait_queue) > 0:
            self._timer += self.delta_factory()
            # Free all the coroutines that waited long enough
            while (len(self._wait_queue)
                   and self._timer >= self._wait_queue[0].wait_time):
                gen = heapq.heappop(self._wait_queue).generator
                self._active_queue.append(gen)
                self._generators[gen] = None

            if len(self._wait_queue) == 0:
                self._timer = 0

        # # Manage active coroutines
        # if len(self._active_queue) <= 1:
        #     return

        # Rotate on the first element(should always be None)
        self._active_queue.rotate(-1)

        # Rotate and execue the coroutine(generator)
        while self._active_queue[0] is not None:
            gen = self._active_queue[0]

            try:
                wait = next(self._active_queue[0])  # Execute
            except StopIteration:
                gen = self._active_queue.popleft()
                del self._generators[gen]
                continue        # Do not rotate if last item was popped

            # Put in wait queue if requested
            if type(wait) is int and wait > 0:
                waiting_gen = _WaitingGenerator(gen, wait + self._timer)
                heapq.heappush(self._wait_queue, waiting_gen)
                self._generators[gen] = waiting_gen
                self._active_queue.popleft()
            else:       # Do not rotate if last item was popped
                self._active_queue.rotate(-1)


class Prototype:
    """Base class for ECS prototypes.

    Define a type as a conglomerate of different components, with or
    without arguments.

    Creating entities with many (and complex) components can become
    quite verbose. Firstly, you bloat pretty easily your code due to
    the many indentations and brackets. Secondly, sometimes components
    do share some information, and repeating it is useless work for you.
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
    components(in fact, to correctly instantiate all the components
    in an entity the prototype instance has to be unpacked with a
    ``*`` expression).

    | **Complex prototypes**

    In this second use case let's see how using a prototype it's
    possible to remove bloat coming from indentation and redundancies.

    Arguments can be intuitively specified in the ``__init__`` method
    of this class. The user is free to specify whatever argument they
    want(no need to call super).

    When instantiating the prototype, the class will eventually try and
    call some special methods for its component types (that we will call
    init methods). If an init method isn't found, the default
    constructor for that component is called (that's why and how the
    above example works, there's no need for init methods if all the
    components are instantiated without specifying parameters).
    By default, init methods follow this naming rule::

        ...
        def init_ComponentType(self):
            ...

    The return type has to be ``ComponentType`` (for obvious reasons).

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

            def init_Position(self):
                return example.Position(self.xx, self.yy)

            def init_Sprite(self):
                return example.Sprite(self.xx, self.yy, self.image,
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
    component_types = tuple()
    """Iterable of types that compose the prototype."""
    init_methods = dict()
    """Dictionary in the format ``{type: function}``.

    It's used to specify custom functions instead of the standard
    init method (using :py:attr:`init_prefix`). The entries from this
    dictionary are prioritized (the standard init method will be
    ignored if an entry for that component type is given).

    This is also useful when name conflicts occur (same class name but
    different namespace).
    """
    init_prefix = 'init_'
    """The prefix for the init methods."""

    def __iter__(self):
        return (self.init_methods.get(
            comp_t,
            getattr(self, f'{self.init_prefix}{comp_t.__name__}', comp_t))()
            for comp_t in self.component_types)
