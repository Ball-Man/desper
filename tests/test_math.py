from context import *
from desper.math import *
from helpers import *

from operator import add, mul, truediv, sub

import pytest

# Math tests are given by tuples of operands and results,
# given by fixture to the various test functions


@pytest.fixture
def clamp_test_tuple():
    # Format: val, min, max, result
    return (
        (0, 0, 0, 0),
        (0, -10, 10, 0),
        (100, -10, 10, 10),
        (-100, -10, 10, -10)
    )


def test_clamp(clamp_test_tuple):
    for val, val_min, val_max, result in clamp_test_tuple:
        assert clamp(val, val_min, val_max) == result


@pytest.fixture
def operators_commutative():
    return {add, mul}


@pytest.fixture
def vec2_operators_test_tuple():
    # Format operator, operand1, operand2, result
    return (
        (add, (0, 0), (1, 2), (1, 2)),
        (add, (-3, 10), (1, 2), (-2, 12)),
        (add, (0, 0), (1, 2), (1, 2)),
        (sub, (0, 0), (1, 2), (-1, -2)),
        (sub, (1, 2), (1, 2), (0, 0)),
        (sub, (3, 10), (0, 0), (3, 10)),
        (mul, (0, 0), (1, 10), (0, 0)),
        (mul, (1, 2), (1, 1), (1, 2)),
        (mul, (1, 2), (3, 4), (3, 8)),
        (truediv, (2, 3), (0, 0), ZeroDivisionError),
        (truediv, (2, 3), (1, 0), ZeroDivisionError),
        (truediv, (2, 3), (0, 1), ZeroDivisionError),
        (truediv, (2, 3), (2, 3), (1, 1)),
        (truediv, (10, 10), (10, 5), (1, 2))
    )


def assert_tuple(tup):
    """Test result based on the given tuple.

    Tuple structure is: ``callable, operand1, operand2, ..., result``.

    If ``result`` is an exception type it will be tested whether it is
    correctly raised.
    """
    operator = tup[0]
    result = tup[-1]
    operands = tup[1:-1]

    if type(result) is type and issubclass(result, Exception):
        with pytest.raises(result):
            operator(*operands)
        return

    assert operator(*operands) == result


def test_vec2_operators(vec2_operators_test_tuple, operators_commutative):
    for op, vec1, vec2, result in vec2_operators_test_tuple:
        assert_tuple((op, Vec2(*vec1), Vec2(*vec2), result))

        # Tuple compatibility
        assert_tuple((op, Vec2(*vec1), vec2, result))

        # Commutativity
        if op in operators_commutative:
            assert_tuple((op, Vec2(*vec2), Vec2(*vec1), result))
