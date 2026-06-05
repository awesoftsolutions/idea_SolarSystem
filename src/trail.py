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
        self._points: deque[tuple[float, Vec2]] = deque(maxlen=capacity)

    def append(self, pos: Vec2, t: float | None = None) -> None:
        """Add a new position to the trail, unwinding for time reversal.

        Args:
            pos: The Vec2 position to add.
            t: The simulation time associated with this position. If None,
               it is treated as monotonically increasing from the last point.
        """
        if t is None:
            # Fallback for legacy tests or calls without timestamp
            if self._points:
                t = self._points[-1][0] + 1.0
            else:
                t = 0.0
        # 1. Unwind trail for time reversal (KI-001)
        while self._points and self._points[-1][0] > t:
            self._points.pop()

        # 2. Update or add point
        if self._points and self._points[-1][0] == t:
            # Replace the last point if it has the same timestamp
            self._points.pop()
            self._points.append((t, pos))
        else:
            self._points.append((t, pos))

    def get_points(self) -> list[Vec2]:
        """Retrieve all points in the trail in chronological order.

        Returns:
            A list of Vec2 points from oldest to newest.
        """
        return [p[1] for p in self._points]
