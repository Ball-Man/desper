from context import *
from desper.math import *
from helpers import *

from operator import add, mul, truediv, sub, matmul
from itertools import repeat

import pytest

# Math tests are given by tuples of operands and results,
# given by fixture to the various test functions


def isexception(obj) -> bool:
    """Return whether the given object is a subclass of ``Exception``."""
    return type(obj) is type and issubclass(obj, Exception)


def assert_tuple(tup):
    """Test result based on the given tuple.

    Tuple structure is: ``callable, operand1, operand2, ..., result``.

    If ``result`` is an exception type it will be tested whether it is
    correctly raised.
    """
    operator = tup[0]
    result = tup[-1]
    operands = tup[1:-1]

    if isexception(result):
        with pytest.raises(result):
            operator(*operands)
        return

    assert operator(*operands) == result


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


def expand_operands_vectors_tuple(tests, exp_value=1, exp_amount=1):
    """Augment size of vectors in test tuple by 1.

    ``exp_value`` is used to specify with what value the vectors
    are expanded.

    ``exp_amount`` is used to specify by the "size" of the expansion.
    """
    test_tuples = []
    for tup in tests:
        operator = tup[0]
        result = tup[-1]
        operands = tup[1:-1]

        new_operands = [(*op, *repeat(exp_value, exp_amount))
                        for op in operands]

        # Update results accordingly
        new_result = result
        if not isexception(result):         # Eventually update result
            new_result = (*result, *repeat(operator(1, 1), exp_amount))

        test_tuples.append((operator, *new_operands, new_result))

    return test_tuples


@pytest.fixture
def vec3_operators_test_tuple(vec2_operators_test_tuple):
    # Manipulate vec2 tests
    return expand_operands_vectors_tuple(vec2_operators_test_tuple)


@pytest.fixture
def vec4_operators_test_tuple(vec3_operators_test_tuple):
    # Manipulate vec3 tests
    return expand_operands_vectors_tuple(vec3_operators_test_tuple)


@pytest.fixture
def mat3_operators_test_tuple():
    # Format operator, operand1, operand2, result
    return (
        (add, (0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 1, 1, 1, 1, 1, 1, 1, 1),
         (1, 1, 1, 1, 1, 1, 1, 1, 1)),
        (sub, (1, 1, 1, 1, 1, 1, 1, 1, 1), (2, 2, 2, 2, 2, 2, 2, 2, 2),
         (-1, -1, -1, -1, -1, -1, -1, -1, -1)),
        (mul, (0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0),
         NotImplementedError),
        (matmul, (0, 0, 0, 0, 0, 0, 0, 0, 0), (2, 2, 2, 2, 2, 2, 2, 2, 2),
         (0, 0, 0, 0, 0, 0, 0, 0, 0)),
        (matmul, (1, 0, 0, 0, 1, 0, 0, 0, 1), (2, 2, 2, 2, 2, 2, 2, 2, 2),
         (2, 2, 2, 2, 2, 2, 2, 2, 2))
    )


@pytest.fixture
def mat4_operators_test_tuple():
    # Format operator, operand1, operand2, result
    return (
        (add, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
         (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
         (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)),
        (sub, (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
         (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2),
         (-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1)),
        (mul, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
         (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
         NotImplementedError),
        (matmul, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
         (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2),
         (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
        (matmul, (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1),
         (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2),
         (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2))
    )


def test_vec2_operators(vec2_operators_test_tuple, operators_commutative):
    for op, vec1, vec2, result in vec2_operators_test_tuple:
        assert_tuple((op, Vec2(*vec1), Vec2(*vec2), result))

        # Tuple compatibility
        assert_tuple((op, Vec2(*vec1), vec2, result))

        # Commutativity
        if op in operators_commutative:
            assert_tuple((op, Vec2(*vec2), Vec2(*vec1), result))


def test_vec3_operators(vec3_operators_test_tuple, operators_commutative):
    for op, vec1, vec2, result in vec3_operators_test_tuple:
        assert_tuple((op, Vec3(*vec1), Vec3(*vec2), result))

        # Tuple compatibility
        assert_tuple((op, Vec3(*vec1), vec2, result))

        # Commutativity
        if op in operators_commutative:
            assert_tuple((op, Vec3(*vec2), Vec3(*vec1), result))


def test_vec4_operators(vec4_operators_test_tuple, operators_commutative):
    for op, vec1, vec2, result in vec4_operators_test_tuple:
        assert_tuple((op, Vec4(*vec1), Vec4(*vec2), result))

        # Tuple compatibility
        assert_tuple((op, Vec4(*vec1), vec2, result))

        # Commutativity
        if op in operators_commutative:
            assert_tuple((op, Vec4(*vec2), Vec4(*vec1), result))


def test_mat3_operators(mat3_operators_test_tuple, operators_commutative):
    for op, mat1, mat2, result in mat3_operators_test_tuple:
        assert_tuple((op, Mat3(mat1), Mat3(mat2), result))

        # Tuple compatibility
        assert_tuple((op, Mat3(mat1), mat2, result))

        # Commutativity
        if op in operators_commutative:
            assert_tuple((op, Mat3(mat2), Mat3(mat1), result))


def test_mat4_operators(mat4_operators_test_tuple, operators_commutative):
    for op, mat1, mat2, result in mat4_operators_test_tuple:
        assert_tuple((op, Mat4(mat1), Mat4(mat2), result))

        # Tuple compatibility
        assert_tuple((op, Mat4(mat1), mat2, result))

        # Commutativity
        if op in operators_commutative:
            assert_tuple((op, Mat4(mat2), Mat4(mat1), result))
