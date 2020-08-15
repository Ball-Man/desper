"""The core module contains the base classes used for game structure.

Some of this classes are not very useful on their own, and should be
derived in order to get something out of it. Some derived classes are
included in this project and are located in other subpackes.

The basic structure of a desper game is based on the ECS architecture
and is as follows:

:class:`GameModel` -> ``World`` -> entity, ``Processor``,
``Component``

Where a :class:`GameModel` contains all the game resources(graphics,
etc.), including the game ``World`` s(game levels, basically).
Each ``World`` works with entities and ``Component`` s. Entities are
"virtual", meaning that there is no class Entity(inside a ``World``
they're just plain ``int`` s).

Each entity can contain a set of ``Component`` s. The ``Component`` s
are processed by ``Processor`` s, which query them, edit them and execute
the main game logic. This is the ECS pattern so far.

Note that the ``World`` and ``Processor`` base classes comes from
`esper <https://github.com/benmoran56/esper>`_.

Desper implements new classes that break the basic ECS structure
(derived from esper classes), introducing polymorphic components.
Desper's polymorphic data structures emulate the classic OOP
entity-component design(e.g. `Unity <https://unity.com/>`_'s
MonoBehaviour).
Polymorphic data structures can be used as a standard ECS anyway, which
means that it's possible to combine the polymorphic design with an ECS
design when needed.

:class:`GameModel` works with both ``esper.World`` s(pure ECS) and
desper's :class:`AbstractWorld` (which can be freely derived). The set
of base polymorphic types is made of: :class:`AbstractWorld`,
:class:`AbstractProcessor`, :class:`AbstractComponent`.
"""
from .world import *
from .gamemodel import *
from .options import *
from .res import *
