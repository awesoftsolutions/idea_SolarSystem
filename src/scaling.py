# CHANGELOG:
# - Sprint 3: Created scaling module with hierarchical logarithmic mapping functions.

"""Core scaling logic for hierarchical logarithmic mapping."""

import math
from src.scaling_constants import (
    DISTANCE_LOG_SCALE_FACTOR,
    DISTANCE_LOG_K,
    SIZE_LOG_K,
    SIZE_LOG_OFFSET,
    DISPLAY_NEIGHBORHOODS,
)

def log_scale_distance(d: float, base: float) -> float:
    """Apply logarithmic compression to a physical distance.
    
    Args:
        d: Physical distance (AU or km).
        base: Logarithm base.
        
    Returns:
        Scaled distance in pixels.
    """
    if d <= 0:
        return 0.0
    
    log_val = math.log(1 + d / DISTANCE_LOG_SCALE_FACTOR, base)
    return log_val * DISTANCE_LOG_K

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
        raise KeyError(f"Unknown body: '{body_name}' has no defined display neighborhood.")
        
    return DISPLAY_NEIGHBORHOODS[body_name]
