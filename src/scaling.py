"""Core scaling logic for hierarchical logarithmic mapping."""

import math
from typing import Any

from src.constants import AU_TO_KM, WINDOW_SIZE
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

# Module-level state (Internal)
_WORLD_CACHE: dict[tuple[str, float, float], Vec2] = {}
_LAST_SIM_TIME: float | None = None

# Pre-calculated reference distances for neighborhood scaling
_NEIGHBORHOOD_D_REF: dict[str, float] = {}
# Pre-calculated K factors for neighborhood scaling
_NEIGHBORHOOD_K_CACHE: dict[str, float] = {}


def _get_neighborhood_d_ref(primary_name: str) -> float:
    """Retrieve or calculate the reference distance for a primary's neighborhood.

    Args:
        primary_name: Name of the primary body.

    Returns:
        Reference distance (AU for Sun, km otherwise).
    """
    if primary_name in _NEIGHBORHOOD_D_REF:
        return _NEIGHBORHOOD_D_REF[primary_name]

    d_ref: float = 1.0
    if primary_name == "Sun":
        d_ref = 30.0
    else:
        # IMPLEMENTATION DECISION: O(N) scan is performed once per primary and cached.
        # Rationale: BODIES is static during simulation.
        children_a: list[float] = [
            float(data["a"])
            for name, data in BODIES.items()
            if data.get("primary") == primary_name and "a" in data
        ]
        if children_a:
            d_ref = max(children_a)
        else:
            d_ref = 1000.0

    _NEIGHBORHOOD_D_REF[primary_name] = d_ref
    return d_ref


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


class Viewport:
    """Viewport configuration for coordinate mapping.

    Attributes:
        center: The world-space position at the center of the viewport.
        zoom: The zoom level (default 1.0).
    """

    def __init__(self, center: Vec2, zoom: float = 1.0) -> None:
        """Initialize Viewport.

        Args:
            center: World-space center position.
            zoom: Zoom level.
        """
        self.center = center
        self.zoom = zoom


def world_to_screen(world_pos: Vec2, viewport: Viewport) -> Vec2:
    """Map world coordinates to screen coordinates.

    Args:
        world_pos: Position in world space.
        viewport: Viewport configuration.

    Returns:
        Position in screen space (pixels).
    """
    # 1. Calculate relative position from viewport center
    rel_pos = world_pos - viewport.center

    # 2. Apply zoom factor
    zoomed_pos = rel_pos * viewport.zoom

    # 3. Translate to screen space using dynamic anchor
    anchor = Vec2(WINDOW_SIZE[0] / 2.0, WINDOW_SIZE[1] / 2.0)
    screen_pos = zoomed_pos + anchor

    return screen_pos


def screen_to_world(screen_pos: Vec2, viewport: Viewport) -> Vec2:
    """Map screen coordinates back to world coordinates.

    Args:
        screen_pos: Position in screen space (pixels).
        viewport: Viewport configuration.

    Returns:
        Position in world space.
    """
    # 1. Translate from screen space to zoomed space
    anchor = Vec2(WINDOW_SIZE[0] / 2.0, WINDOW_SIZE[1] / 2.0)
    zoomed_pos = screen_pos - anchor

    # 2. Remove zoom factor (clamp zoom to prevent ZeroDivisionError)
    safe_zoom = max(viewport.zoom, 1e-6)
    rel_pos = zoomed_pos / safe_zoom

    # 3. Translate back to world space relative to viewport center
    world_pos = rel_pos + viewport.center

    return world_pos


def log_scale_distance(
    d: float,
    base: float,
    k: float = DISTANCE_LOG_K,
    s: float = DISTANCE_LOG_SCALE_FACTOR,
) -> float:
    """Apply logarithmic compression to a physical distance.

    Args:
        d: Physical distance (AU or km).
        base: Logarithm base.
        k: Scaling constant (pixels).
        s: Scale factor in the units of d (AU for Sun-centered, KM otherwise).

    Returns:
        Scaled distance in pixels.
    """
    if d <= 0:
        return 0.0

    log_val = math.log(1 + d / s, base)
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


def scale_orbit_geometry(
    elements: dict[str, Any], scale_factor: float
) -> dict[str, Any]:
    """Scale orbital ellipse geometry while preserving eccentricity and orientation.

    Args:
        elements: Dictionary containing 'a', 'e', 'longitude_of_perihelion', and 'primary'.
        scale_factor: Logarithm base for distance scaling.

    Returns:
        Dictionary with 'a_v', 'b_v', 'center_offset' (Vec2), and 'orientation'.
    """
    a = elements["a"]
    e = elements["e"]
    omega = elements.get("longitude_of_perihelion", 0.0)
    primary_name = elements.get("primary", "Sun")

    # 1. Calculate visual semi-major axis using neighborhood-specific K
    k, s = _get_scaling_params(primary_name)
    a_v = log_scale_distance(a, scale_factor, k, s)

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

    Applies hierarchical logarithmic scaling to preserve local legibility.
    The output is relative to the Sun at (0, 0).

    Args:
        actual_pos: Absolute physical position in km.
        frame_context: Reference frame context (name and time).
        use_cache: Whether to use/populate the world position cache.

    Returns:
        World-space position vector in pixels.
    """
    global _LAST_SIM_TIME

    # 1. Cache Invalidation Check
    if frame_context.t != _LAST_SIM_TIME:
        _WORLD_CACHE.clear()
        _NEIGHBORHOOD_K_CACHE.clear()  # Also clear K cache on time change
        _LAST_SIM_TIME = frame_context.t

    # 2. Cache Retrieval
    cache_key = (frame_context.name, actual_pos.x, actual_pos.y)
    if use_cache and cache_key in _WORLD_CACHE:
        return _WORLD_CACHE[cache_key]

    # 3. Base Case: Sun is at the world origin
    if frame_context.name == "Sun":
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
    primary_abs_pos = resolve_absolute_position(primary_name, frame_context.t)
    primary_frame = Frame(primary_name, frame_context.t)
    primary_world_pos = map_to_world(primary_abs_pos, primary_frame, use_cache)

    # 6. Calculate Relative Physical Offset
    relative_offset = actual_pos - primary_abs_pos

    # IMPLEMENTATION DECISION: Convert KM to AU for Sun-relative offsets.
    # Rationale: BODIES data for Sun-orbiting bodies uses AU for 'a',
    # but resolve_absolute_position returns KM.
    dist_km = relative_offset.magnitude()
    dist = dist_km / AU_TO_KM if primary_name == "Sun" else dist_km

    # 7. Apply Neighborhood-Specific Logarithmic Scaling
    k, s = _get_scaling_params(primary_name)
    scaled_dist = log_scale_distance(dist, LOG_BASE_DISTANCE, k, s)

    if dist > 0:
        unit_vec = relative_offset.normalize()
        scaled_offset = unit_vec * scaled_dist
    else:
        scaled_offset = Vec2(0.0, 0.0)

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
    """
    # 1. Map to world space (hierarchical log scaling)
    world_pos = map_to_world(actual_pos, frame_context)

    # 2. Map to screen space (viewport transformation)
    return world_to_screen(world_pos, viewport)
