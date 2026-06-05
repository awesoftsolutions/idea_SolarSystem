"""Unit tests for the Trail management system."""

from src.trail import Trail
from src.vector import Vec2


def test_trail_empty() -> None:
    """Verify a new Trail returns an empty list."""
    trail = Trail(capacity=10)
    assert trail.get_points() == []


def test_trail_append_and_get() -> None:
    """Verify points are stored and returned in chronological order."""
    trail = Trail(capacity=5)
    p1 = Vec2(1.0, 2.0)
    p2 = Vec2(3.0, 4.0)
    p3 = Vec2(5.0, 6.0)

    trail.append(p1)
    trail.append(p2)
    trail.append(p3)

    points = trail.get_points()
    assert len(points) == 3
    assert points[0] == p1
    assert points[1] == p2
    assert points[2] == p3


def test_trail_capacity_eviction() -> None:
    """Verify that when capacity is reached, the oldest point is removed on new append."""
    capacity = 3
    trail = Trail(capacity=capacity)

    p1 = Vec2(1.0, 1.0)
    p2 = Vec2(2.0, 2.0)
    p3 = Vec2(3.0, 3.0)
    p4 = Vec2(4.0, 4.0)

    trail.append(p1)
    trail.append(p2)
    trail.append(p3)

    # Verify full but no eviction yet
    assert trail.get_points() == [p1, p2, p3]

    # Append 4th point, p1 should be evicted
    trail.append(p4)

    points = trail.get_points()
    assert len(points) == capacity
    assert p1 not in points
    assert points == [p2, p3, p4]


def test_trail_data_integrity() -> None:
    """Verify that get_points() returns Vec2 objects identical to those appended."""
    trail = Trail(capacity=10)
    original_point = Vec2(123.456, 789.012)

    trail.append(original_point)
    retrieved_points = trail.get_points()

    assert len(retrieved_points) == 1
    assert retrieved_points[0] is original_point
    assert retrieved_points[0] == original_point
