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
    rel_pos_cache: dict[tuple[float, float, float, float], Vec2] | None = None,
    on_cache_hit: typing.Callable[[], None] | None = None,
    on_cache_miss: typing.Callable[[], None] | None = None,
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
        rel_pos_cache: Optional persistent cache for relative positions (DR-016).
            This cache stores heliocentric coordinates keyed by orbital elements
            and quantized time (t % period), enabling cross-body and cross-frame
            optimization for bodies sharing identical orbits.
        on_cache_hit: Optional callback for persistent cache hits.
        on_cache_miss: Optional callback for persistent cache misses.

    Returns:
        The absolute position vector in km.

    Raises:
        KeyError: If body_name is not in bodies.
        RuntimeError: If a circular dependency is detected (ERR-003).
    """
    # 1. Cache Lookup (Per-tick)
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
        parent_pos = resolve_absolute_position(
            primary_name,
            t,
            bodies,
            cache,
            visited,
            rel_pos_cache=rel_pos_cache,
            on_cache_hit=on_cache_hit,
            on_cache_miss=on_cache_miss,
        )

    # 7. Calculate Relative Position (with Persistent Cache)
    rel_pos: Vec2 | None = None
    if rel_pos_cache is not None and all(k in body_data for k in ("a", "e", "T")):
        a, e, period = (
            float(body_data["a"]),
            float(body_data["e"]),
            float(body_data["T"]),
        )
        t_key = round(t % period, 6)
        cache_key = (a, e, period, t_key)

        if cache_key in rel_pos_cache:
            rel_pos = rel_pos_cache[cache_key]
            if on_cache_hit:
                on_cache_hit()
        else:
            rel_pos = get_heliocentric_coords(
                typing.cast(typing.Dict[str, typing.Any], body_data), t
            )
            rel_pos_cache[cache_key] = rel_pos
            if on_cache_miss:
                on_cache_miss()
    else:
        # Fallback to fresh calculation if cache not provided or elements missing
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
