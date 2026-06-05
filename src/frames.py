# CHANGELOG:
# - Sprint 2: Implement recursive position resolution with cycle detection and unit conversion.

"""Hierarchical reference frame composition.

This module provides the logic for resolving the absolute (heliocentric)
position of bodies in a hierarchical system by recursively summing relative
orbital offsets and handling unit conversions.
"""

from typing import Any, TypedDict, cast, NamedTuple

from src.vector import Vec2
from src.constants import AU_TO_KM
from src.orbital import get_heliocentric_coords


class Frame(NamedTuple):
    """Reference frame context for coordinate mapping.

    Attributes:
        name: Name of the body defining the frame.
        t: Simulation time.
    """

    name: str
    t: float


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
    body_name: str,
    t: float,
    bodies: dict[str, Any],
    cache: dict[str, Vec2],
    visited: set[str] | None = None,
) -> Vec2:
    """Resolve the absolute (heliocentric) position of a body at simulation time t.

    Recursively sums relative orbital offsets from the body to the Sun root.
    Includes cycle detection and physical unit conversion (AU to km).

    Args:
        body_name: Name of the body to resolve.
        t: Simulation time.
        bodies: Injected dictionary of body data.
        cache: Per-tick cache for storing resolved positions.
        visited: Set of body names already encountered in the current recursive chain.

    Returns:
        The absolute position vector in km.

    Raises:
        KeyError: If body_name is not in bodies.
        RuntimeError: If a circular dependency is detected (ERR-003).
    """
    # 1. Cache Lookup
    if body_name in cache:
        return cache[body_name]

    # 2. Initialize visited set
    if visited is None:
        visited = set()

    # 3. Cycle Detection
    if body_name in visited:
        raise RuntimeError("ERR-003: CIRCULAR_FRAME_DEPENDENCY")
    visited.add(body_name)

    # 4. Base Case (Sun/Root)
    if body_name == "Sun":
        result = Vec2(0.0, 0.0)
        cache[body_name] = result
        return result

    # 5. Fetch Body Data
    if body_name not in bodies:
        raise KeyError(body_name)
    body_data = bodies[body_name]

    # 6. Recursive Step
    primary_name = body_data.get("primary")
    if not isinstance(primary_name, str):
        # This should only happen if Sun is misconfigured in bodies
        # but the base case handles "Sun" explicitly.
        # Added for mypy satisfaction.
        parent_pos = Vec2(0.0, 0.0)
    else:
        parent_pos = resolve_absolute_position(primary_name, t, bodies, cache, visited)

    # 7. Calculate Relative Position
    # Cast to satisfy mypy: body_data is FrameNode which matches get_heliocentric_coords
    rel_pos = get_heliocentric_coords(cast(dict[str, Any], body_data), t)

    # 8. Unit Conversion (AU to KM)
    if primary_name == "Sun":
        rel_pos_km = rel_pos * AU_TO_KM
    else:
        rel_pos_km = rel_pos

    # 9. Composition and Storage
    result = parent_pos + rel_pos_km
    cache[body_name] = result
    return result
