from helpers import *
from context import desper
from desper import glet
from desper import core

import pytest


@pytest.fixture
def world():
    return core.AbstractWorld()


@pytest.fixture
def gamemodel():
    model = glet.GletGameModel()
    w = core.AbstractWorld()
    w.add_processor(core.AbstractProcessor())
    model.res['testworld'] = WorldHandle(w)
    model.switch(model.res['testworld'])
    return model


def test_gamemodel_quit_loop(gamemodel):
    w = gamemodel.current_world_handle.get()
    entity = w.create_entity(ModelComponent())

    gamemodel.loop()

    assert w.component_for_entity(entity, ModelComponent).var == 11
