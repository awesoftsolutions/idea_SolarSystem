import math

import pytest

from src.constants import SOLVER_TOLERANCE
from src.vector import Vec2


def test_vec2_immutability() -> None:
    """AC-1: Verify that Vec2 components are immutable."""
    v = Vec2(1.0, 2.0)

    # Attempting to modify existing attributes should raise AttributeError
    with pytest.raises(AttributeError):
        v.x = 3.0  # type: ignore

    with pytest.raises(AttributeError):
        v.y = 4.0  # type: ignore

    # Attempting to add new attributes should also raise AttributeError due to __slots__
    with pytest.raises(AttributeError):
        v.z = 5.0  # type: ignore

    # Attempting to delete attributes should raise AttributeError
    with pytest.raises(AttributeError):
        del v.x  # type: ignore

    # Attempting to delete attributes should raise AttributeError
    with pytest.raises(AttributeError):
        del v.x  # type: ignore

    with pytest.raises(AttributeError):
        del v.y  # type: ignore


def test_vec2_addition() -> None:
    """Verify vector addition."""
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    result = v1 + v2
    assert result == Vec2(4.0, 6.0)
    assert isinstance(result, Vec2)


def test_vec2_addition_type_safety() -> None:
    """Verify that adding non-Vec2 types raises TypeError (via NotImplemented)."""
    v = Vec2(1.0, 2.0)
    with pytest.raises(TypeError):
        _ = v + (1.0, 2.0)  # type: ignore


def test_vec2_subtraction() -> None:
    """Verify vector subtraction."""
    v1 = Vec2(5.0, 7.0)
    v2 = Vec2(2.0, 3.0)
    result = v1 - v2
    assert result == Vec2(3.0, 4.0)
    assert isinstance(result, Vec2)


def test_vec2_subtraction_type_safety() -> None:
    """Verify that subtracting non-Vec2 types raises TypeError (via NotImplemented)."""
    v = Vec2(1.0, 2.0)
    with pytest.raises(TypeError):
        _ = v - (1.0, 2.0)  # type: ignore


def test_vec2_multiplication() -> None:
    """Verify scalar multiplication."""
    v = Vec2(1.0, -2.0)
    result = v * 3.0
    assert result == Vec2(3.0, -6.0)
    assert isinstance(result, Vec2)


def test_vec2_rmul() -> None:
    """Verify commutative scalar multiplication (scalar * vector)."""
    v = Vec2(1.0, -2.0)
    result = 3.0 * v
    assert result == Vec2(3.0, -6.0)
    assert isinstance(result, Vec2)


def test_vec2_division() -> None:
    """Verify scalar division."""
    v = Vec2(10.0, -5.0)
    result = v / 5.0
    assert result == Vec2(2.0, -1.0)
    assert isinstance(result, Vec2)


def test_vec2_division_by_zero() -> None:
    """Verify that division by zero raises ZeroDivisionError."""
    v = Vec2(1.0, 1.0)
    with pytest.raises(ZeroDivisionError):
        _ = v / 0.0


def test_vec2_magnitude() -> None:
    """Verify magnitude calculation."""
    v = Vec2(3.0, 4.0)
    assert v.magnitude() == 5.0


def test_vec2_magnitude_sq() -> None:
    """Verify squared magnitude calculation."""
    v = Vec2(3.0, 4.0)
    assert v.magnitude_sq() == 25.0


def test_vec2_normalize() -> None:
    """Verify vector normalization."""
    v = Vec2(3.0, 0.0)
    result = v.normalize()
    assert result == Vec2(1.0, 0.0)
    assert math.isclose(result.magnitude(), 1.0, abs_tol=SOLVER_TOLERANCE)


def test_vec2_normalize_zero() -> None:
    """Verify that normalizing a zero vector returns a zero vector."""
    v = Vec2(0.0, 0.0)
    result = v.normalize()
    assert result == Vec2(0.0, 0.0)


def test_vec2_dot_product() -> None:
    """Verify dot product calculation."""
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    assert v1.dot(v2) == 11.0


def test_vec2_rotation() -> None:
    """AC-2: Verify vector rotation, including 360-degree precision."""
    v = Vec2(1.0, 0.0)

    # 90 degrees (pi/2)
    v_90 = v.rotate(math.pi / 2)
    assert v_90 == Vec2(0.0, 1.0)

    # 180 degrees (pi)
    v_180 = v.rotate(math.pi)
    assert v_180 == Vec2(-1.0, 0.0)

    # 360 degrees (2*pi) - should return original vector within tolerance
    v_orig = Vec2(1.2, 3.4)
    v_360 = v_orig.rotate(2 * math.pi)
    assert v_360 == v_orig


def test_vec2_equality() -> None:
    """Verify epsilon-based equality using SOLVER_TOLERANCE."""
    v1 = Vec2(1.0, 1.0)

    # Within tolerance
    v2 = Vec2(1.0 + SOLVER_TOLERANCE * 0.1, 1.0)
    assert v1 == v2

    # Outside tolerance
    v3 = Vec2(1.0 + SOLVER_TOLERANCE * 10.0, 1.0)
    assert v1 != v3

    # Different type
    assert v1 != (1.0, 1.0)


def test_vec2_equality_boundaries() -> None:
    """Verify equality at the exact boundary of SOLVER_TOLERANCE."""
    v1 = Vec2(1.0, 1.0)
    # Just inside boundary
    v2 = Vec2(1.0 + SOLVER_TOLERANCE * 0.99, 1.0)
    assert v1 == v2

    # Just outside boundary
    v3 = Vec2(1.0 + SOLVER_TOLERANCE * 1.01, 1.0)
    assert v1 != v3


def test_vec2_high_scale_precision() -> None:
    """Verify that SOLVER_TOLERANCE is absolute, not relative, at large scales."""
    # At 1 AU (1.5e11), a relative tolerance of 1e-9 would allow 150m error.
    # We require absolute tolerance of SOLVER_TOLERANCE (1e-9).
    # Note: 1.5e11 is near the limit of float64 precision for 1e-9 increments.
    # 1.5e11 has a machine epsilon of ~1.5e-5.
    # However, we can test at a scale where 1e-9 is still representable.
    # 1e6 (1,000 km) has an epsilon of ~1e-10.
    scale = 1e6
    v1 = Vec2(scale, 0.0)
    v2 = Vec2(scale + SOLVER_TOLERANCE * 2.0, 0.0)

    # This should be False if rel_tol=0.0 is used.
    # If default rel_tol=1e-9 is used, rel_tol * scale = 1e-3, so they would be "close".
    assert v1 != v2, f"Precision leak at scale {scale}: {v1} should not equal {v2}"


def test_vec2_arithmetic_type_safety() -> None:
    """Verify that arithmetic operators handle incompatible types gracefully."""
    v = Vec2(1.0, 2.0)

    with pytest.raises(TypeError):
        _ = v + (1.0, 2.0)  # type: ignore

    with pytest.raises(TypeError):
        _ = v - [1.0, 2.0]  # type: ignore


def test_vec2_repr() -> None:
    """Verify string representation."""
    v = Vec2(1.2, 3.4)
    assert repr(v) == "Vec2(1.2, 3.4)"
