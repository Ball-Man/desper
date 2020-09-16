import inspect
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

    e.g.
    .. code-block

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

    e.g.
    .. code-block

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

    def __init__(self):
        self._generators = {}
        # Dictionary format: {generator: _WaitingGenerator}
        # _WaitingGenerator is None if the said generator isn't waiting.
        self._active_queue = deque((None,))
        self._wait_queue = []       # Heap
        self._timer = 0

    def start(self, generator):
        """Add and start a coroutine, represented by a generator object.

        :param generator: The generator object representing the
                          coroutine.
        :return: The started generator object.
        :raises TypeError: If `generator` isn't a generator object.
        :raises ValueError: If `generator` is already being executed.
        """
        if not inspect.isgenerator(generator):
            raise TypeError('Only generator objects are accepted')

        if self._generators.get(generator, 0) != 0:
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

    def process(self, *args):
        """Process one frame of all the currently active coroutines.

        And unpause coroutines if necessary.
        """
        # Manage waiting coroutines
        if len(self._wait_queue) > 0:
            self._timer += 1
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
