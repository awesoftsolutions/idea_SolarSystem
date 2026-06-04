import unittest.mock as mock
import pytest
from src.vector import Vec2
from src.frames import resolve_absolute_position
from src.constants import AU_TO_KM

def test_resolve_sun_root():
    """Scenario A: Root Resolution (Sun returns zero vector)."""
    assert resolve_absolute_position("Sun", 0.0) == Vec2(0.0, 0.0)

def test_resolve_moon_recursive():
    """Scenario B: Multi-level Recursive Resolution (Moon heliocentric position)."""
    # Mock BODIES to ensure Moon -> Earth -> Sun
    mock_bodies = {
        "Sun": {"primary": None},
        "Earth": {"primary": "Sun", "a": 1.0, "e": 0.0, "T": 1.0},
        "Moon": {"primary": "Earth", "a": 384400.0, "e": 0.0, "T": 27.32}
    }
    
    # Mock get_heliocentric_coords
    # Earth relative to Sun: 1.0 AU
    # Moon relative to Earth: 384400.0 km
    with mock.patch("src.frames.BODIES", mock_bodies):
        with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
            def side_effect(data, t):
                if data == mock_bodies["Earth"]:
                    return Vec2(1.0, 0.0)
                if data == mock_bodies["Moon"]:
                    return Vec2(0.0, 384400.0)
                return Vec2(0.0, 0.0)
            
            mock_coords.side_effect = side_effect
            
            pos = resolve_absolute_position("Moon", 0.0)
            
            # Expected: Earth_pos_km + Moon_rel_pos
            # Earth_pos_km = 1.0 * AU_TO_KM
            expected = Vec2(1.0 * AU_TO_KM, 384400.0)
            assert pos == expected

def test_resolve_circular_dependency():
    """Scenario C: Circular Dependency Detection (Raise ERR-003)."""
    mock_bodies = {
        "A": {"primary": "B"},
        "B": {"primary": "A"}
    }
    
    with mock.patch("src.frames.BODIES", mock_bodies):
        with pytest.raises(RuntimeError, match="ERR-003: CIRCULAR_FRAME_DEPENDENCY"):
            resolve_absolute_position("A", 0.0)

def test_unit_conversion_boundary():
    """Scenario D: Unit Conversion Boundary."""
    mock_bodies = {
        "Sun": {"primary": None},
        "Mercury": {"primary": "Sun", "a": 0.387, "e": 0.0, "T": 0.24}
    }
    
    with mock.patch("src.frames.BODIES", mock_bodies):
        with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
            mock_coords.return_value = Vec2(0.387, 0.0)
            
            pos = resolve_absolute_position("Mercury", 0.0)
            # Should be scaled by AU_TO_KM
            assert pos == Vec2(0.387 * AU_TO_KM, 0.0)
