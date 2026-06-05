"""Viewport configuration and coordinate transformations."""

from src.constants import WINDOW_SIZE
from src.vector import Vec2

# Module-level anchor for screen transformations (center of the window)
ANCHOR = Vec2(WINDOW_SIZE[0] / 2.0, WINDOW_SIZE[1] / 2.0)

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

    # 3. Translate to screen space using the fixed anchor
    return zoomed_pos + ANCHOR


def screen_to_world(screen_pos: Vec2, viewport: Viewport) -> Vec2:
    """Map screen coordinates back to world coordinates.

    Args:
        screen_pos: Position in screen space (pixels).
        viewport: Viewport configuration.

    Returns:
        Position in world space.
    """
    # 1. Translate from screen space to zoomed space
    zoomed_pos = screen_pos - ANCHOR

    # 2. Remove zoom factor (clamp zoom to prevent ZeroDivisionError)
    # IMPLEMENTATION DECISION: Clamp zoom to 1e-6 for invertibility at zero/negative zoom.
    safe_zoom = max(viewport.zoom, 1e-6)
    rel_pos = zoomed_pos / safe_zoom

    # 3. Translate back to world space relative to viewport center
    return rel_pos + viewport.center
