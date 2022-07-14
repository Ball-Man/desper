from context import desper
from helpers import *

import pytest


@pytest.fixture
def uncached_handle():
    handle = SimpleHandle(11)
    return handle


@pytest.fixture
def cached_handle():
    handle = SimpleHandle(10)
    handle()
    return handle


class TestHandle:

    def test_get(self):
        val = 10
        handle = SimpleHandle(val)

        assert handle() == val * 2

    def test_cached(self, cached_handle, uncached_handle):
        assert cached_handle.cached
        assert not uncached_handle.cached

    def test_clear(self, cached_handle):
        cached_handle.clear()
        assert not cached_handle.cached
