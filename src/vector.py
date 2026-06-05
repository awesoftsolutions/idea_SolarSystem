# CHANGELOG:
# - Sprint 1: Implement immutable Vec2 library with arithmetic and geometric operations.

"""Immutable 2D vector math for deterministic physics."""

from __future__ import annotations

import math
from typing import Any

from src.constants import SOLVER_TOLERANCE


class Vec2:
    """An immutable 2D vector.

    Attributes:
        x: The x-coordinate.
        y: The y-coordinate.
    """

    __slots__ = ("x", "y")
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        """Initialize Vec2 with x and y components.

        Args:
            x: The x-coordinate.
            y: The y-coordinate.
        """
        # Use object.__setattr__ to bypass immutability during initialization
        object.__setattr__(self, "x", float(x))
        object.__setattr__(self, "y", float(y))

    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent modification of attributes to ensure immutability.

        Args:
            name: The attribute name.
            value: The value to set.

        Raises:
            AttributeError: Always raised to prevent modification.
        """
        raise AttributeError(f"Vec2 is immutable, cannot set {name}")

    def __delattr__(self, name: str) -> None:
        """Prevent deletion of attributes to ensure immutability.

        Args:
            name: The attribute name.

        Raises:
            AttributeError: Always raised to prevent deletion.
        """
        raise AttributeError(f"Vec2 is immutable, cannot delete {name}")

    def __add__(self, other: Vec2) -> Vec2:
        """Add two vectors.

        Args:
            other: The other vector to add.

        Returns:
            A new Vec2 representing the sum.
        """
        if not isinstance(other, Vec2):
            return NotImplemented
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        """Subtract another vector from this one.

        Args:
            other: The vector to subtract.

        Returns:
            A new Vec2 representing the difference.
        """
        if not isinstance(other, Vec2):
            return NotImplemented
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        """Multiply the vector by a scalar.

        Args:
            scalar: The scalar value to multiply by.

        Returns:
            A new Vec2 representing the product.
        """
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vec2:
        """Multiply the vector by a scalar (commutative).

        Args:
            scalar: The scalar value to multiply by.

        Returns:
            A new Vec2 representing the product.
        """
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vec2:
        """Divide the vector by a scalar.

        Args:
            scalar: The scalar value to divide by.

        Returns:
            A new Vec2 representing the quotient.

        Raises:
            ZeroDivisionError: If the scalar is zero.
        """
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide Vec2 by zero")
        return Vec2(self.x / scalar, self.y / scalar)

    def magnitude_sq(self) -> float:
        """Calculate the squared magnitude of the vector.

        Returns:
            The squared magnitude (x^2 + y^2).
        """
        return self.x * self.x + self.y * self.y

    def magnitude(self) -> float:
        """Calculate the magnitude (length) of the vector.

        Returns:
            The Euclidean magnitude.
        """
        return math.sqrt(self.magnitude_sq())

    def normalize(self) -> Vec2:
        """Return a unit vector in the same direction.

        Returns:
            A new Vec2 with magnitude 1.0, or (0.0, 0.0) if the vector is zero.
        """
        mag = self.magnitude()
        if mag == 0:
            return Vec2(0.0, 0.0)
        return self / mag

    def dot(self, other: Vec2) -> float:
        """Calculate the dot product with another vector.

        Args:
            other: The other vector.

        Returns:
            The dot product (x1*x2 + y1*y2).
        """
        return self.x * other.x + self.y * other.y

    def rotate(self, angle_rad: float) -> Vec2:
        """Rotate the vector by an angle in radians.

        Args:
            angle_rad: The rotation angle in radians.

        Returns:
            A new rotated Vec2.
        """
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        new_x = self.x * cos_a - self.y * sin_a
        new_y = self.x * sin_a + self.y * cos_a
        return Vec2(new_x, new_y)

    def __eq__(self, other: object) -> bool:
        """Check equality with another Vec2 within SOLVER_TOLERANCE.

        Args:
            other: The object to compare with.

        Returns:
            True if other is a Vec2 and components match within tolerance.
        """
        if not isinstance(other, Vec2):
            return False
        # rel_tol=0.0 ensures SOLVER_TOLERANCE is an absolute bound regardless of scale.
        return math.isclose(
            self.x, other.x, rel_tol=0.0, abs_tol=SOLVER_TOLERANCE
        ) and math.isclose(self.y, other.y, rel_tol=0.0, abs_tol=SOLVER_TOLERANCE)

    def __repr__(self) -> str:
        """Return a string representation of the vector.

        Returns:
            A string in the format 'Vec2(x, y)'.
        """
        return f"Vec2({self.x}, {self.y})"
