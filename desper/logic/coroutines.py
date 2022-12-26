"""Coroutine management utilities."""
import inspect
import enum
from collections import deque
from dataclasses import dataclass, field
import functools
from typing import Generator, Callable, TypeVar, Generic
# from typing import ParamSpec          >= 3.10 only
import heapq

import desper
from desper.logic import Processor, World

# Params = ParamSpec('Params')          >= 3.10 only
T = TypeVar('T')


class CoroutineState(enum.IntEnum):
    """Enumeration of possible states for a coroutine."""
    TERMINATED = 0
    PAUSED = 1
    ACTIVE = 2


class CoroutinePromise(Generic[T]):
    """Monitor, manage a coroutine and retrieve return its value."""

    def __init__(self, generator: Generator, processor: 'CoroutineProcessor',
                 value: T = None):
        self._generator = generator
        self._processor = processor
        self.value: T = value

    @property
    def generator(self) -> Generator:
        return self._generator

    @property
    def processor(self) -> 'CoroutineProcessor':
        return self._processor

    @property
    def state(self) -> CoroutineState:
        """Get state of the coroutine."""
        return self._processor.state(self._generator)

    def kill(self):
        """Kill coroutine."""
        self._processor.kill(self._generator)


@dataclass(order=True)
class _WaitingGenerator:
    """Class used to contain a paused generator, for desper coroutines.

    Used by class :class:`CoroutineProcessor` to keep track of which
    generators are the next to be resumed.
    """
    generator: Generator = field(compare=False)
    wait_time: float


class CoroutineProcessor(Processor):
    """Seemingly parallel execution of arbitrary code.

    Note that *coroutine* is not intended as Python's
    `builtin coroutines <https://bit.ly/2FHc87u>`_. Desper coroutines
    are `generators <https://bit.ly/3fWKi9U>`_.
    From now on, when *coroutine* is mentioned, *generator* is meant.

    Coroutines can be managed by two main methods, :meth:`start`,
    that will insert and start the coroutine into the system and
    :meth:`kill` that will stop and remove the coroutine from the
    system.
    The removed generator is returned, so that it can be started again
    if wanted by the user (the killed generator is simply removed,
    meaning that if reinserted with :meth:`start` it will resume
    from where it stopped).

    Once started, the coroutine will be called once per :meth:`process`
    (typically once per frame).
    To return control use ``yield``.

    e.g::

        def coroutine():
            # Spawn enemies every 2 seconds
            while True:
                spawn_enemies()
                yield 2

        # ...
        processor.start(coroutine())

    As shown above, when yielding a number ``n`` the coroutine will be
    paused for ``n`` seconds, and resumed immediately after.

    To stop a coroutine, use its generator and the :meth:`kill` method.

    e.g::

        def coroutine():
           # ...

        # ...
        gen = coroutine()       # Create generator
        processor.start(gen)    # Start coroutine
        # ...

        processor.kill(gen)     # Stop previously started coroutine
    """

    def __init__(self):
        self._generators = {}
        # Dictionary format: {generator: _WaitingGenerator}
        # _WaitingGenerator is None if the said generator isn't waiting.
        self._active_queue = deque((None,))
        self._wait_queue = []       # Heap
        self._kill_queue = set()    # Coroutines waiting to be killed
        self._promises = {}     # Dict format: {generator: CoroutinePromise}
        self._timer = 0.

    def start(self, generator: Generator) -> CoroutinePromise:
        """Add and start a coroutine, represented by a generator object.

        :param generator: The generator object representing the
                          coroutine.
        :return: A promise object for the started coroutine.
        :raises TypeError: If `generator` isn't a generator object.
        :raises ValueError: If `generator` is already being executed.
        """
        state = self.state(generator)

        if state != CoroutineState.TERMINATED:
            raise ValueError('Cannot start the same generator twice')

        self._active_queue.append(generator)
        self._generators[generator] = None
        promise = CoroutinePromise(generator, self)
        self._promises[generator] = promise
        return promise

    def kill(self, generator: Generator):
        """Stop and remove a coroutine, given the generator.

        Paused coroutines can be killed too.

        Internally, the coroutine is not killed immediately. The
        generator is simply marked so that it shall not be executed
        again.

        :param generator: The generator object representing the
                          coroutine.
        :raises TypeError: If ``generator`` isn't a generator object.
        :raises ValueError: If ``generator`` isn't being executed (has
                            already been killed or terminated its
                            execution).
        """
        if not inspect.isgenerator(generator):
            raise TypeError('Only generator objects are accepted')

        # Sentinel is 0 since None is a valid element in the dictionary
        waiting_gen = self._generators.get(generator, 0)
        if waiting_gen == 0 or generator in self._kill_queue:
            raise ValueError('Generator not found')

        self._kill_queue.add(generator)

    def state(self, generator: Generator):
        """Get the current state of the given coroutine.

        :param generator: The generator representing the coroutine.
        :return: A :class:`CoroutineState` instance representing
                 the state of the given coroutine.
                 If the coroutine isn't found
                 :attr:`CoroutineState.TERMINATED` will be returned.
        """
        if not inspect.isgenerator(generator):
            raise TypeError('Only generator objects are accepted')

        waiting_gen = self._generators.get(generator, 0)
        if waiting_gen == 0 or generator in self._kill_queue:
            return CoroutineState.TERMINATED

        # Check in which queue the generator currently is
        if waiting_gen is None:
            return CoroutineState.ACTIVE
        else:
            return CoroutineState.PAUSED

    def process(self, dt):
        """Process one frame of all the currently active coroutines.

        And unpause coroutines if necessary.
        """
        # Manage waiting coroutines
        if len(self._wait_queue) > 0:
            self._timer += dt
            # Free all the coroutines that waited long enough
            while (len(self._wait_queue)
                   and self._timer >= self._wait_queue[0].wait_time):
                gen = heapq.heappop(self._wait_queue).generator

                # If a kill was pending, just drop the coroutine
                if gen in self._kill_queue:
                    del self._generators[gen]
                    self._kill_queue.discard(gen)
                    del self._promises[gen]
                else:
                    self._active_queue.append(gen)
                    self._generators[gen] = None

            if len(self._wait_queue) == 0:
                self._timer = 0

        # # Manage active coroutines
        # if len(self._active_queue) <= 1:
        #     return

        # Rotate on the first element(should always be None)
        self._active_queue.rotate(-1)

        # Rotate and execute the coroutine (generator)
        while self._active_queue[0] is not None:
            gen = self._active_queue[0]

            # If a kill is pending, don't execute and drop
            if gen in self._kill_queue:
                del self._generators[gen]
                self._kill_queue.discard(gen)
                self._active_queue.popleft()
                del self._promises[gen]
                continue        # Do not rotate if last item was popped

            try:
                wait = next(self._active_queue[0])  # Execute
            except StopIteration as exception:
                gen = self._active_queue.popleft()
                del self._generators[gen]
                self._promises[gen].value = exception.value
                del self._promises[gen]
                continue        # Do not rotate if last item was popped

            # Put in wait queue if requested
            if wait is not None and wait > 0:
                waiting_gen = _WaitingGenerator(gen, wait + self._timer)
                heapq.heappush(self._wait_queue, waiting_gen)
                self._generators[gen] = waiting_gen
                self._active_queue.popleft()
            else:       # Do not rotate if last item was popped
                self._active_queue.rotate(-1)


def coroutine(function: Callable[..., T]
              ) -> Callable[..., CoroutinePromise[T]]:
    """Decorator: easy coroutine startup.

    The wrapped function must be a generator function. As a result,
    calling it instantly starts it as a coroutine, returning the
    associated :class:`CoroutinePromise`.

    Requires a :class:`CoroutineProcessor` in the target :class:`World`.
    By default, current world from the main loop
    (:attr:`desper.default_loop`) is used.
    A custom world can be targeted by specifying an argument named
    ``world`` in the wrapped function. ``None`` values for such argument
    will fall back on the default loop.
    """
    signature = inspect.signature(function)

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()

        world: World = bound_args.arguments.get(
            'world', )

        if world is None:
            world = desper.default_loop.current_world

        assert world is not None, (
            'Could not find a viable World to start the coroutine. '
            'Consider setting up the default loop (desper.default_loop) '
            'or providing a world manually, adding the keyword argument '
            '"world" to the wrapped function.')

        processor = world.get_processor(CoroutineProcessor)

        assert processor is not None, (
            'A CoroutineProcessor is necessary to start a coroutine')

        return processor.start(function(*bound_args.args, **bound_args.kwargs))

    return wrapper
