![desper logo](https://github.com/Ball-Man/desper/blob/master/assets/desper-logo-raw.png?raw=true)
# desper
A Python3 game development toolkit for resource and logic management.
Meant to be used coupled with open source projects.

Inspired by the wonderful ECS library: [esper](https://github.com/benmoran56/esper). A special thanks to its author, Benjamin.

## Abstract
Desper provides a component based logic system, designed with game development in mind. The objective is to fill the lack of game logic management systems in the open source Python landscape.

In particular, while there are many valuable media libraries out there ([pyglet](https://github.com/pyglet/pyglet), [SDL2](https://github.com/py-sdl/py-sdl2), etc.) they mostly provide APIs for window and graphic management. Consequently, often times game logic has to be implemented and reinvented from scratch. Desper provides a minimal expandable API that aims at obtaining interoperation with these powerful media libraries. These expansions will be implemented over time and provided through separate packages.

The project started as an expansion of [esper](https://github.com/benmoran56/esper), hence many aspects of the API will result similar.

## Installation
Simple installation from PyPi (recommended):
```
pip install desper
```

Or installation from master branch:
```
git clone https://github.com/Ball-Man/desper
cd desper
pip install .
```

## Expansions
Expansion libraries the can offer interoperation with existing media libraries will be implemented over time and provided through separate packages. Current ones:

- [pyglet-desper](https://github.com/Ball-Man/pyglet-desper/) (work in progress), for [pyglet](https://github.com/pyglet/pyglet) interoperation

## Project status
*(updated 2022-12-29)*
A first draft of the docs (API reference only) can be found at [desper.readthedocs.io](https://desper.readthedocs.io/en/latest/). Examples and a user guide are in the making.

## desper in action
* current project, closed source: [Lone Planet](https://fmistri.it/lone/index.html)
* android game experiment, open source (uses an old alpha version of desper): [monospace](https://github.com/Ball-Man/monospace)
