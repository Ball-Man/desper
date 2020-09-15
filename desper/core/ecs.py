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
    """An ecs processor that manages coroutines."""

    def __init__(self):
        self._generators = {}
        # Dictionary format: {generator: _WaitingGenerator}
        # _WaitingGenerator is None if the said generator isn't waiting.
        self._active_queue = deque((None,))
        self._wait_queue = []       # Heap
        self._timer = 0

    def start(self, generator):
        """Add and start a coroutine, represented by a generator object."""
        if not inspect.isgenerator(generator):
            raise TypeError('Only generator objects are accepted')

        if self._generators.get(generator, 0) != 0:
            raise ValueError('Cannot start the same generator twice')

        self._active_queue.append(generator)
        self._generators[generator] = None
        return generator

    def kill(self, generator):
        """Stop and remove a coroutine, given the generator."""
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
            if wait is not None:
                waiting_gen = _WaitingGenerator(gen, wait + self._timer)
                heapq.heappush(self._wait_queue, waiting_gen)
                self._generators[gen] = waiting_gen
                self._active_queue.popleft()
            else:       # Do not rotate if last item was popped
                self._active_queue.rotate(-1)
