# CHANGELOG:
# - Sprint 3: Implement hierarchical logarithmic mapping and neighborhood logic.

"""Core scaling logic for hierarchical logarithmic mapping."""

import math
from typing import Any

from src.constants import AU_TO_KM
from src.frames import Frame, resolve_absolute_position
from src.vector import Vec2
from src.scaling_constants import (
    DISTANCE_LOG_SCALE_FACTOR,
    DISTANCE_LOG_K,
    SIZE_LOG_K,
    SIZE_LOG_OFFSET,
    DISPLAY_NEIGHBORHOODS,
    LOG_BASE_DISTANCE,
)
from src.bodies import BODIES
from src.viewport import Viewport, world_to_screen

# Module-level state (Internal)
_WORLD_CACHE: dict[tuple[str, float, float], Vec2] = {}
_FRAME_CACHE: dict[str, Vec2] = {}
_LAST_SIM_TIME: float | None = None

# Pre-calculated reference distances for neighborhood scaling
_NEIGHBORHOOD_D_REF: dict[str, float] = {}
# Pre-calculated K factors for neighborhood scaling
_NEIGHBORHOOD_K_CACHE: dict[str, float] = {}


def _initialize_neighborhood_refs() -> None:
    """Pre-calculate reference distances for all primaries in BODIES.

    This avoids O(N) scans during simulation.
    """
    # 1. Initialize Sun
    _NEIGHBORHOOD_D_REF["Sun"] = 30.0

    # 2. Find all other primaries
    primaries = {
        data["primary"] for data in BODIES.values() if data.get("primary") is not None
    }

    # 3. Calculate max 'a' for each primary's children
    for primary in primaries:
        if primary == "Sun" or primary is None:
            continue
        children_a = [
            float(data["a"])
            for data in BODIES.values()
            if data.get("primary") == primary and "a" in data
        ]
        _NEIGHBORHOOD_D_REF[primary] = max(children_a) if children_a else 1000.0


# Run initialization at module load
_initialize_neighborhood_refs()


def _get_neighborhood_d_ref(primary_name: str) -> float:
    """Retrieve the reference distance for a primary's neighborhood.

    Args:
        primary_name: Name of the primary body.

    Returns:
        Reference distance in the units used by the children of this primary
        in BODIES (AU for Sun-centered neighborhoods, km for planetary neighborhoods).
    """
    return _NEIGHBORHOOD_D_REF.get(primary_name, 1000.0)


def _get_scale_factor(primary_name: str) -> float:
    """Get the scale factor (s) for a primary's neighborhood.

    Args:
        primary_name: Name of the primary body.

    Returns:
        Scale factor (1.0 for Sun, DISTANCE_LOG_SCALE_FACTOR otherwise).
    """
    return 1.0 if primary_name == "Sun" else DISTANCE_LOG_SCALE_FACTOR


def _get_scaling_params(primary_name: str) -> tuple[float, float]:
    """Get neighborhood-specific K and S parameters.

    Args:
        primary_name: Name of the primary body.

    Returns:
        Tuple of (k, s).
    """
    s = _get_scale_factor(primary_name)

    # 1. Check K cache
    if primary_name in _NEIGHBORHOOD_K_CACHE:
        return _NEIGHBORHOOD_K_CACHE[primary_name], s

    # 2. Get neighborhood radius (pixels)
    try:
        r_neighborhood = get_neighborhood_bounds(primary_name)
    except KeyError:
        return DISTANCE_LOG_K, s

    # 3. Get reference distance
    d_ref = _get_neighborhood_d_ref(primary_name)

    # 4. Calculate K
    log_val = math.log(1 + d_ref / s, LOG_BASE_DISTANCE)
    k = r_neighborhood / log_val if log_val > 0 else DISTANCE_LOG_K

    # 5. Store in cache
    _NEIGHBORHOOD_K_CACHE[primary_name] = k

    return k, s


def log_scale_distance(
    d: float,
    log_base: float = LOG_BASE_DISTANCE,
    k: float = DISTANCE_LOG_K,
    s: float = DISTANCE_LOG_SCALE_FACTOR,
) -> float:
    """Apply logarithmic compression to a physical distance.

    Args:
        d: Physical distance (AU or km).
        log_base: Logarithm base.
        k: Scaling constant (pixels).
        s: Scale factor in the units of d (AU for Sun-centered, KM otherwise).

    Returns:
        Scaled distance in pixels.
    """
    if d <= 0:
        return 0.0

    log_val = math.log(1 + d / s, log_base)
    return log_val * k


def log_scale_size(r: float, min_p: float, max_p: float, base: float) -> float:
    """Apply logarithmic scaling to a physical radius with clamping.

    Args:
        r: Physical radius (km).
        min_p: Minimum display size in pixels.
        max_p: Maximum display size in pixels.
        base: Logarithm base.

    Returns:
        Scaled radius in pixels, clamped to [min_p, max_p].
    """
    if r <= 0:
        return min_p

    log_val = math.log(r, base)
    raw_pixels = (SIZE_LOG_K * log_val) + SIZE_LOG_OFFSET

    return max(min_p, min(max_p, raw_pixels))


def get_neighborhood_bounds(body_name: str) -> float:
    """Retrieve the display neighborhood radius for a primary body.

    Args:
        body_name: Name of the primary body (e.g., 'Sun', 'Earth').

    Returns:
        Neighborhood radius in pixels.

    Raises:
        KeyError: If the body is not a known primary with a defined neighborhood.
    """
    if body_name not in DISPLAY_NEIGHBORHOODS:
        raise KeyError(
            f"Unknown body: '{body_name}' has no defined display neighborhood."
        )

    return DISPLAY_NEIGHBORHOODS[body_name]


def get_neighborhood_k(primary_name: str) -> float:
    """Calculate the neighborhood-specific K factor for distance scaling.

    Args:
        primary_name: Name of the primary body.

    Returns:
        Scaling factor K in pixels.
    """
    # Ensure _NEIGHBORHOOD_D_REF is populated for testing/consistency
    _get_neighborhood_d_ref(primary_name)

    k, _ = _get_scaling_params(primary_name)
    return k


def get_body_scale_factor(a: float, primary_name: str) -> float:
    """Calculate the body-specific linear scale factor (k_linear).

    k_linear = log_scale_distance(a, ...) / a.
    This ensures that each body's average distance is log-scaled, but its
    local orbital motion is linear, preserving the elliptical shape.

    Args:
        a: Semi-major axis of the body.
        primary_name: Name of the primary body.

    Returns:
        Scale factor in pixels/AU (Sun) or pixels/km (others).
    """
    if a <= 0:
        return 0.0

    k_p, s_p = _get_scaling_params(primary_name)
    d_scaled = log_scale_distance(a, LOG_BASE_DISTANCE, k_p, s_p)

    return d_scaled / a


def scale_orbit_geometry(elements: dict[str, Any]) -> dict[str, Any]:
    """Scale orbital ellipse geometry while preserving eccentricity and orientation.

    Args:
        elements: Dictionary containing 'a', 'e', 'longitude_of_perihelion', and 'primary'.

    Returns:
        Dictionary with 'a_v', 'b_v', 'center_offset' (Vec2), and 'orientation'.
    """
    a = elements["a"]
    e = elements["e"]
    omega = elements.get("longitude_of_perihelion", 0.0)
    primary_name = elements.get("primary", "Sun")

    # 1. Calculate visual semi-major axis using body-specific linear scale factor
    k_linear = get_body_scale_factor(a, primary_name)
    a_v = a * k_linear

    # 2. Calculate visual semi-minor axis to preserve eccentricity
    ratio = math.sqrt(1.0 - e * e)
    b_v = a_v * ratio

    # 3. Calculate visual linear eccentricity (center-to-focus distance)
    c_v = a_v * e

    # 4. Calculate visual center offset
    local_center = Vec2(-c_v, 0.0)

    # Rotate the center offset by the longitude of perihelion
    center_offset = local_center.rotate(omega)

    return {
        "a_v": a_v,
        "b_v": b_v,
        "center_offset": center_offset,
        "orientation": omega,
    }


def map_to_world(
    actual_pos: Vec2, frame_context: Frame, use_cache: bool = True
) -> Vec2:
    """Map physical heliocentric coordinates to world-space pixels.

    Applies hierarchical linear-within-log scaling to preserve local legibility
    and orbital geometry. The output is relative to the Sun at (0, 0).

    Args:
        actual_pos: Absolute physical position in km.
        frame_context: Reference frame context (name and time).
        use_cache: Whether to use/populate the world position cache.

    Returns:
        World-space position vector in pixels.

    Raises:
        KeyError: If body_name is not in BODIES.
        RuntimeError: If a circular dependency is detected.
    """
    global _LAST_SIM_TIME

    # 1. Cache Invalidation Check
    if frame_context.t != _LAST_SIM_TIME:
        _WORLD_CACHE.clear()
        _FRAME_CACHE.clear()
        _LAST_SIM_TIME = frame_context.t

    # 2. Cache Retrieval
    cache_key = (frame_context.name, actual_pos.x, actual_pos.y)
    if use_cache and cache_key in _WORLD_CACHE:
        return _WORLD_CACHE[cache_key]

    # 3. Base Case: Sun is at the world origin
    if frame_context.name == "Sun":
        # If actual_pos is not (0,0), we still need to scale it relative to the Sun
        if actual_pos.magnitude() < 1e-3:
            sun_pos = Vec2(0.0, 0.0)
            if use_cache:
                _WORLD_CACHE[cache_key] = sun_pos
            return sun_pos

    # 4. Identify Parent Frame
    body_data = BODIES[frame_context.name]
    primary_name_raw = body_data.get("primary")
    primary_name: str = "Sun"
    if isinstance(primary_name_raw, str):
        primary_name = str(primary_name_raw)

    # 5. Resolve Parent Positions
    primary_abs_pos = resolve_absolute_position(
        primary_name, frame_context.t, BODIES, _FRAME_CACHE
    )
    primary_frame = Frame(primary_name, frame_context.t)
    primary_world_pos = map_to_world(primary_abs_pos, primary_frame, use_cache)

    # 6. Calculate Relative Physical Offset
    relative_offset = actual_pos - primary_abs_pos

    # 7. Apply Body-Specific Linear Scaling
    # Retrieve semi-major axis 'a' for the body
    body_data = BODIES.get(frame_context.name, {})
    a = body_data.get("a", 0.0)

    # Convert relative_offset to AU if primary is Sun
    if primary_name == "Sun":
        relative_offset = relative_offset / AU_TO_KM

    # Fallback: if 'a' is missing or 0, use instantaneous distance 'd'
    if a <= 0:
        d = relative_offset.magnitude()
        k_linear = get_body_scale_factor(d, primary_name)
    else:
        k_linear = get_body_scale_factor(a, primary_name)

    scaled_offset = relative_offset * k_linear

    # 8. Compose Final World Position
    world_pos = primary_world_pos + scaled_offset

    # 9. Store in Cache
    if use_cache:
        _WORLD_CACHE[cache_key] = world_pos

    return world_pos


def map_to_screen(actual_pos: Vec2, frame_context: Frame, viewport: Viewport) -> Vec2:
    """Map physical heliocentric coordinates to screen coordinates.

    Args:
        actual_pos: Absolute physical position in km.
        frame_context: Reference frame context (name and time).
        viewport: Viewport configuration.

    Returns:
        Position in screen space (pixels).

    Raises:
        KeyError: If body_name is not in BODIES.
        RuntimeError: If a circular dependency is detected.
    """
    # 1. Map to world space (hierarchical log scaling)
    world_pos = map_to_world(actual_pos, frame_context)

    # 2. Map to screen space (viewport transformation)
    return world_to_screen(world_pos, viewport)
