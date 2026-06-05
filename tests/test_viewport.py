import math
import pytest
from src.viewport import Viewport, world_to_screen, screen_to_world, ANCHOR
from src.vector import Vec2
from src.constants import WINDOW_SIZE

def test_viewport_invertibility() -> None:
    """Verify that world -> screen -> world returns the original point."""
    p = Vec2(500.0, 600.0)
    v = Viewport(Vec2(100.0, 200.0), 2.5)

    s = world_to_screen(p, v)
    p2 = screen_to_world(s, v)

    assert p2 == p

def test_viewport_shifting() -> None:
    """Moving the viewport center shifts all bodies in the opposite direction."""
    v = Viewport(Vec2(100.0, 0.0), 1.0)
    p = Vec2(0.0, 0.0)

    s = world_to_screen(p, v)
    # Expected: (720 - 100, 540) = (620, 540)
    assert s == Vec2(ANCHOR.x - 100.0, ANCHOR.y)

def test_zoom_scaling() -> None:
    """Increasing zoom moves bodies further from the screen center."""
    p = Vec2(100.0, 0.0)
    v = Viewport(Vec2(0.0, 0.0), 2.0)

    s = world_to_screen(p, v)
    # Expected: (720 + 200, 540) = (920, 540)
    assert s == Vec2(ANCHOR.x + 200.0, ANCHOR.y)

def test_zero_zoom_handling() -> None:
    """Handle zoom = 0.0 gracefully (prevent division by zero)."""
    v = Viewport(Vec2(0.0, 0.0), 0.0)
    s = Vec2(820.0, 540.0)

    try:
        p = screen_to_world(s, v)
        assert isinstance(p, Vec2)
    except ZeroDivisionError:
        pytest.fail("screen_to_world raised ZeroDivisionError for zoom=0.0")

def test_negative_zoom_handling() -> None:
    """Verify that negative zoom values are handled gracefully (clamped)."""
    v = Viewport(Vec2(0.0, 0.0), -5.0)
    s = Vec2(820.0, 540.0)

    try:
        p = screen_to_world(s, v)
        assert isinstance(p, Vec2)
        assert p.x > 0
    except ZeroDivisionError:
        pytest.fail("screen_to_world raised ZeroDivisionError for negative zoom")
