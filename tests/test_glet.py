import os.path as pt
import os
import collections
from helpers import *
from context import desper
from desper import glet
from desper import core

import tests

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
    model.res['testworld'] = WorldHandle()
    w = model.res['testworld'].get()
    w.add_processor(core.AbstractProcessor())
    model.switch(model.res['testworld'], immediate=True)
    return model


@pytest.fixture
def sprite():
    return pyglet.sprite.Sprite(IMAGE)


def test_gamemodel_quit_loop(gamemodel):
    w = gamemodel.current_world_handle.get()
    entity = w.create_entity(ModelComponent())

    gamemodel.loop()

    assert w.component_for_entity(entity, ModelComponent).var == 11


def test_gamemodel_switch(gamemodel):
    testworld = gamemodel.current_world
    testworld.create_entity(ModelComponent())
    testworld2_hand = WorldHandle()
    testworld2 = testworld2_hand.get()
    testworld2.create_entity(ModelComponent())
    testworld2.add_processor(core.AbstractProcessor())

    batch1 = gamemodel.get_batch(testworld)
    batch2 = gamemodel.get_batch(testworld2)

    gamemodel.switch(testworld2_hand, immediate=True, cur_reset=True)

    assert batch2 is gamemodel.get_batch()
    assert batch1 is not gamemodel.get_batch(testworld)

    gamemodel.switch(testworld2_hand, immediate=True, dest_reset=True)

    assert batch2 is not gamemodel.get_batch()

    gamemodel.loop()


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

    assert w.get_processor(esper.Processor) is not None


def test_world_handle_proto(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_world_importer(): glet.WorldHandle})

    w = gamemodel.res['worlds']['proto.json'].get()
    w.component_for_entity(1, collections.defaultdict)
    w.component_for_entity(1, collections.deque)


def test_world_handle_res_resolve(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_media_importer(): glet.MediaHandle,
                            glet.get_world_importer(): glet.WorldHandle})

    w = gamemodel.res['worlds']['res.json'].get()
    comp = w.component_for_entity(10, tests.helpers.ComponentArgs1)

    assert isinstance(comp.x, pyglet.media.Source)

    with pytest.raises(IndexError):
        w = gamemodel.res['worlds']['res2.json'].get()


def test_glet_world_handle_importer(gamemodel):
    gamemodel.init_handles([pt.join(pt.dirname(__file__), 'files')],
                           {glet.get_animation_importer():
                            glet.AnimationHandle,
                            glet.get_world_importer(): glet.GletWorldHandle})

    w = gamemodel.res['worlds']['glet.json'].get()
    gamemodel.switch(gamemodel.res['worlds']['glet.json'], immediate=True)
    comp = w.get_component(pyglet.sprite.Sprite)[0][1]

    assert type(comp.image) is pyglet.image.Animation
    assert comp.batch == gamemodel.get_batch()
    assert comp.group == gamemodel.get_order_group(10)
