"""Hierarchical reference frame composition.

This module provides the logic for resolving the absolute (heliocentric)
position of bodies in a hierarchical system by recursively summing relative
orbital offsets and handling unit conversions.
"""

# CHANGELOG:
# - Sprint 2: Implement recursive position resolution with cycle detection and unit conversion.

from typing import TypedDict

from src.vector import Vec2
from src.bodies import BODIES
from src.constants import AU_TO_KM
from src.orbital import get_heliocentric_coords

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


def resolve_absolute_position(body_name: str, t: float, visited: set[str] | None = None) -> Vec2:
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
    # 1. Initialize visited set
    if visited is None:
        visited = set()

    # 2. Cycle Detection
    if body_name in visited:
        raise RuntimeError("ERR-003: CIRCULAR_FRAME_DEPENDENCY")
    visited.add(body_name)

    # 3. Base Case (Sun/Root)
    if body_name == "Sun":
        return Vec2(0.0, 0.0)

    # 4. Fetch Body Data
    if body_name not in BODIES:
        raise KeyError(body_name)
    body_data = BODIES[body_name]

    # 5. Recursive Step
    primary_name = body_data.get("primary")
    parent_pos = resolve_absolute_position(primary_name, t, visited)

    # 6. Calculate Relative Position
    rel_pos = get_heliocentric_coords(body_data, t)

    # 7. Unit Conversion (AU to KM)
    if primary_name == "Sun":
        rel_pos_km = rel_pos * AU_TO_KM
    else:
        rel_pos_km = rel_pos

    # 8. Composition
    return parent_pos + rel_pos_km