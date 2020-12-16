import os.path as pt
import collections


from context import desper
from desper import core
import esper


class ComponentA(core.AbstractComponent):
    pass


class ComponentB(ComponentA):
    pass


class ComponentC(core.AbstractComponent):

    def __init__(self):
        self.val = 0

    def update(self, en, world):
        self.val += 1


class ComponentD(ComponentC):
    INIT_VAL = 20

    def __init__(self):
        self.val = ComponentD.INIT_VAL


class ModelComponent(core.AbstractComponent):

    def __init__(self):
        self.var = 0

    def update(self, en, world, model):
        self.var += 1
        if self.var > 10:
            model.quit = True


class OnAttachComponent(core.OnAttachListener):

    def __init__(self):
        self.entity = -1
        self.world = None

    def on_attach(self, en, world):
        self.entity = en
        self.world = world


class ControllerComponent(core.Controller):
    pass


class ProcessorA(esper.Processor):
    pass


class ProcessorB(esper.Processor):
    pass


class SquareHandle(desper.Handle):
    def __init__(self, n):
        super().__init__()

        self._n = n

    def _load(self):
        return self._n ** 2


class TextHandle(desper.Handle):
    def __init__(self, filepath):
        super().__init__()

        self._filepath = filepath

    def _load(self):
        return open(self._filepath).read()


class WorldHandle(desper.Handle):

    def __init__(self, w):
        super().__init__()
        self._w = w

    def _load(self):
        return self._w


class CoroutineComponent:

    def __init__(self):
        self.counter = 0
        self.counter2 = 0

    def coroutine(self):
        yield 10
        self.counter += 1

    def coroutine2(self):
        while self.counter2 < 100:
            self.counter2 += 1
            yield

    def coroutine3(self):
        while True:
            yield 3


def accept_all(root, path, res):
    return pt.abspath(pt.join(root, path)),


def accept_all_2(root, path, res):
    return pt.abspath(pt.join(root, path)),


def accept_none(resource_root, rel_path, resources):
    return None


def accept_sounds(resource_root, rel_path, resources):
    if 'sounds' in rel_path:
        return pt.abspath(pt.join(resource_root, rel_path)),


class ComponentArgs1:

    def __init__(self, x):
        self.x = x


class ComponentArgs2:

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Prototype1(desper.Prototype):
    component_types = ComponentA, ComponentB


class Prototype2(desper.Prototype):
    component_types = ComponentArgs1, ComponentArgs2, ComponentA

    def __init__(self, x, y):
        self.init_methods = {ComponentArgs2: self.init_comp2}

        self.x = x
        self.y = y

    def init_ComponentArgs1(self):
        return ComponentArgs1(self.x)

    def init_comp2(self):
        return ComponentArgs2(self.x, self.y)


class BuiltinPrototype(desper.Prototype):
    component_types = collections.defaultdict, collections.deque
