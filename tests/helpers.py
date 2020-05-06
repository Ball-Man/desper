import os.path as pt


from context import desper
from desper import core


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


def accept_all(root, path, res):
    return pt.abspath(pt.join(root, path)),


def accept_none(resource_root, rel_path, resources):
    return None


def accept_sounds(resource_root, rel_path, resources):
    if 'sounds' in rel_path:
        return pt.abspath(pt.join(resource_root, rel_path)),
