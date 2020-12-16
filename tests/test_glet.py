import os.path as pt
import os
import collections
from helpers import *
from context import desper
from desper import glet
from desper import core

import pytest
import pyglet


pyglet.resource.path = [pt.abspath(os.curdir).replace(os.sep, '/')]
pyglet.resource.reindex()

IMAGE = pyglet.image.load(
    pt.join(pt.dirname(__file__), 'files' + os.sep + 'test.png'))


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


@pytest.fixture
def sprite():
    return pyglet.sprite.Sprite(IMAGE)


def test_gamemodel_quit_loop(gamemodel):
    w = gamemodel.current_world_handle.get()
    entity = w.create_entity(ModelComponent())

    gamemodel.loop()

    assert w.component_for_entity(entity, ModelComponent).var == 11


def test_active_sprite_processor(gamemodel, sprite):
    w = gamemodel.current_world
    w.add_processor(glet.ActiveSpriteProcessor())

    entity = w.create_entity(glet.Position(50, 50), sprite,
                             ModelComponent())

    gamemodel.loop()

    pos = w.component_for_entity(entity, glet.Position)
    spr = w.component_for_entity(entity, pyglet.sprite.Sprite)
    assert pos.x == spr.x
    assert pos.y == spr.y


def test_image_handle(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_image_importer(): glet.ImageHandle})

    assert isinstance(gamemodel.res['sprites']['test.png'].get(),
                      pyglet.image.AbstractImage)


def test_animation_handle(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_animation_importer():
                            glet.AnimationHandle})

    assert isinstance(gamemodel.res['sprites']['anim.json'].get(),
                      pyglet.image.Animation)


def test_media_handle(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_media_importer(): glet.MediaHandle})

    assert isinstance(gamemodel.res['media']['volt.wav'].get(),
                      pyglet.media.Source)


def test_font_importer(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_font_importer(): core.IdentityHandle})

    assert pyglet.font.have_font('The Godfather')


def test_world_handle(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_world_importer(): glet.WorldHandle})

    w = gamemodel.res['worlds']['test.json'].get()
    assert isinstance(w, esper.World)
    assert len(w.get_component(collections.deque)) == 2
    assert len(w.get_component(collections.Counter)) == 1

    counter = w.component_for_entity(1, collections.Counter)
    assert counter['x'] == 100

    deque = w.component_for_entity(1, collections.deque)
    assert deque == collections.deque([0, 1, 2, 3])


def test_world_handle_proto(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_world_importer(): glet.WorldHandle})

    w = gamemodel.res['worlds']['proto.json'].get()
    w.component_for_entity(1, collections.defaultdict)
    w.component_for_entity(1, collections.deque)


def test_event_handler(gamemodel):
    glet.event_handler.window = gamemodel.window

    @glet.event_handler
    class TestHandler:
        pass

    assert callable(TestHandler)

    glet.event_handler.window = None

    with pytest.raises(TypeError):
        TestHandler()
