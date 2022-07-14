from context import desper
from helpers import *

import pytest


class TestHandle:

    def test_get(self):
        val = 10
        handle = SimpleHandle(val)

        assert handle() == val * 2
