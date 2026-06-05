# CHANGELOG:
# - Sprint 2: Implement recursive position resolution with cycle detection and unit conversion.
# - Sprint 4: Refactor resolve_absolute_position for Dependency Injection and local caching.
# - Sprint 5: Update for BodyProvider API.

from __future__ import annotations

import typing

from src.constants import AU_TO_KM
from src.orbital import get_heliocentric_coords
from src.vector import Vec2

if typing.TYPE_CHECKING:
    from src.bodies import BodyProvider

"""Hierarchical reference frame composition.

This module provides the logic for resolving the absolute (heliocentric)
position of bodies in a hierarchical system by recursively summing relative
orbital offsets and handling unit conversions.
"""


class Frame(typing.NamedTuple):
    """Reference frame context for coordinate mapping.

    Attributes:
        name: Name of the body defining the frame.
        t: Simulation time.
    """

    name: str
    t: float


def resolve_absolute_position(
    body_name: str,
    t: float,
    bodies: BodyProvider,
    cache: dict[str, Vec2],
    visited: set[str] | None = None,
) -> Vec2:
    """Resolve the absolute (heliocentric) position of a body at simulation time t.

    Recursively sums relative orbital offsets from the body to the Sun root.
    Includes cycle detection and physical unit conversion (AU to km).

    Args:
        body_name: Name of the body to resolve.
        t: Simulation time.
        bodies: Injected BodyProvider.
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

    body_data = bodies.get_body(body_name)

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
    # Cast to satisfy mypy: body_data matches get_heliocentric_coords signature
    rel_pos = get_heliocentric_coords(
        typing.cast(typing.Dict[str, typing.Any], body_data), t
    )

    # 8. Unit Conversion (AU to KM)
    if primary_name == "Sun":
        rel_pos_km = rel_pos * AU_TO_KM
    else:
        rel_pos_km = rel_pos

    # 9. Composition and Storage
    result = parent_pos + rel_pos_km
    cache[body_name] = result
    return result
