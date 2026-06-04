"""Hierarchical reference frame composition.

This module provides the logic for resolving the absolute (heliocentric)
position of bodies in a hierarchical system by recursively summing relative
orbital offsets and handling unit conversions.
"""

# CHANGELOG:
# - Sprint 2: Implement recursive position resolution with cycle detection and unit conversion.

from typing import Any, TypedDict, cast

from src.vector import Vec2
from src.bodies import BODIES
from src.constants import AU_TO_KM
from src.orbital import get_heliocentric_coords

# Module-level state (Internal)
_FRAME_CACHE: dict[str, Vec2] = {}
_LAST_SIM_TIME: float | None = None


class FrameNode(TypedDict, total=False):
    """Data contract for a reference frame node.

    Attributes:
        primary: Name of the parent body, or None for the root (Sun).
        a: Semi-major axis (AU for Sun-primary, km otherwise).
        e: Eccentricity.
        T: Orbital period (years for Sun-primary, days otherwise).
        radius: Mean physical radius in km.
        color: RGB tuple for visualization.
    """

    primary: str | None
    a: float
    e: float
    T: float
    radius: float
    color: tuple[int, int, int]


def resolve_absolute_position(
    body_name: str, t: float, visited: set[str] | None = None
) -> Vec2:
    """Resolve the absolute (heliocentric) position of a body at simulation time t.

    Recursively sums relative orbital offsets from the body to the Sun root.
    Includes cycle detection and physical unit conversion (AU to km).

    Args:
        body_name: Name of the body to resolve.
        t: Simulation time.
        visited: Set of body names already encountered in the current recursive chain.

    Returns:
        The absolute position vector in km.

    Raises:
        KeyError: If body_name is not in BODIES.
        RuntimeError: If a circular dependency is detected (ERR-003).
    """
    global _LAST_SIM_TIME

    # 1. Cache Invalidation Check
    if t != _LAST_SIM_TIME:
        _FRAME_CACHE.clear()
        _LAST_SIM_TIME = t

    # 2. Cache Lookup
    if body_name in _FRAME_CACHE:
        return _FRAME_CACHE[body_name]

    # 3. Initialize visited set
    if visited is None:
        visited = set()

    # 4. Cycle Detection
    if body_name in visited:
        raise RuntimeError("ERR-003: CIRCULAR_FRAME_DEPENDENCY")
    visited.add(body_name)

    # 5. Base Case (Sun/Root)
    if body_name == "Sun":
        return Vec2(0.0, 0.0)

    # 6. Fetch Body Data
    if body_name not in BODIES:
        raise KeyError(body_name)
    body_data = BODIES[body_name]

    # 7. Recursive Step
    primary_name = body_data.get("primary")
    if not isinstance(primary_name, str):
        # This should only happen if Sun is misconfigured in BODIES
        # but the base case handles "Sun" explicitly.
        # Added for mypy satisfaction.
        parent_pos = Vec2(0.0, 0.0)
    else:
        parent_pos = resolve_absolute_position(primary_name, t, visited)

    # 8. Calculate Relative Position
    # Cast to satisfy mypy: body_data is FrameNode which matches get_heliocentric_coords
    rel_pos = get_heliocentric_coords(cast(dict[str, Any], body_data), t)

    # 9. Unit Conversion (AU to KM)
    if primary_name == "Sun":
        rel_pos_km = rel_pos * AU_TO_KM
    else:
        rel_pos_km = rel_pos

    # 10. Composition and Storage
    result = parent_pos + rel_pos_km
    _FRAME_CACHE[body_name] = result
    return result
