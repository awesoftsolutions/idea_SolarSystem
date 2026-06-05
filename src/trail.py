# CHANGELOG:
# - Sprint 5: Implement Trail class for position tracking using a ring buffer.

"""Trail management system using ring buffers for efficient position tracking."""

from collections import deque
from src.vector import Vec2


class Trail:
    """Manages a fixed-length history of position vectors.

    Attributes:
        _points: A deque acting as a ring buffer for Vec2 points.
    """

    def __init__(self, capacity: int) -> None:
        """Initialize the trail with a fixed maximum capacity.

        Args:
            capacity: The maximum number of points to store.
        """
        self._points: deque[Vec2] = deque(maxlen=capacity)

    def append(self, pos: Vec2) -> None:
        """Add a new position to the trail.

        Args:
            pos: The Vec2 position to add.
        """
        self._points.append(pos)

    def get_points(self) -> list[Vec2]:
        """Retrieve all points in the trail in chronological order.

        Returns:
            A list of Vec2 points from oldest to newest.
        """
        return list(self._points)
