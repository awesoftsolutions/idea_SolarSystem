import unittest.mock as mock
from typing import Any
import time
import pytest
from src.vector import Vec2
from src.frames import resolve_absolute_position
from src.constants import AU_TO_KM


def test_resolve_sun_root() -> None:
    """Scenario A: Root Resolution (Sun returns zero vector)."""
    # resolve_absolute_position now requires bodies and cache
    bodies = {"Sun": {"primary": None}}
    cache: dict[str, Vec2] = {}
    assert resolve_absolute_position("Sun", 0.0, bodies=bodies, cache=cache) == Vec2(
        0.0, 0.0
    )


def test_resolve_moon_recursive() -> None:
    """Scenario B: Multi-level Recursive Resolution (Moon heliocentric position)."""
    # Mock BODIES to ensure Moon -> Earth -> Sun
    mock_bodies = {
        "Sun": {"primary": None},
        "Earth": {"primary": "Sun", "a": 1.0, "e": 0.0, "T": 1.0},
        "Moon": {"primary": "Earth", "a": 384400.0, "e": 0.0, "T": 27.32},
    }

    # Mock get_heliocentric_coords
    # Earth relative to Sun: 1.0 AU
    # Moon relative to Earth: 384400.0 km
    with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:

        def side_effect(data: Any, t: float) -> Vec2:
            if data == mock_bodies["Earth"]:
                return Vec2(1.0, 0.0)
            if data == mock_bodies["Moon"]:
                return Vec2(0.0, 384400.0)
            return Vec2(0.0, 0.0)

        mock_coords.side_effect = side_effect

        cache: dict[str, Vec2] = {}
        pos = resolve_absolute_position("Moon", 0.0, bodies=mock_bodies, cache=cache)

        # Expected: Earth_pos_km + Moon_rel_pos
        # Earth_pos_km = 1.0 * AU_TO_KM
        expected = Vec2(1.0 * AU_TO_KM, 384400.0)
        assert pos == expected
        # Verify cache population
        assert "Moon" in cache
        assert "Earth" in cache


def test_resolve_circular_dependency() -> None:
    """Scenario C: Circular Dependency Detection (Raise ERR-003)."""
    mock_bodies = {"A": {"primary": "B"}, "B": {"primary": "A"}}

    with pytest.raises(RuntimeError, match="ERR-003: CIRCULAR_FRAME_DEPENDENCY"):
        resolve_absolute_position("A", 0.0, bodies=mock_bodies, cache={})


def test_unit_conversion_boundary() -> None:
    """Scenario D: Unit Conversion Boundary."""
    mock_bodies = {
        "Sun": {"primary": None},
        "Mercury": {"primary": "Sun", "a": 0.387, "e": 0.0, "T": 0.24},
    }

    with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
        mock_coords.return_value = Vec2(0.387, 0.0)

        pos = resolve_absolute_position("Mercury", 0.0, bodies=mock_bodies, cache={})
        # Should be scaled by AU_TO_KM
        assert pos == Vec2(0.387 * AU_TO_KM, 0.0)


def test_frames_dependency_injection() -> None:
    """Verify that resolve_absolute_position uses the provided bodies and cache."""
    bodies = {
        "Sun": {"primary": None},
        "Custom": {"primary": "Sun", "a": 10.0, "e": 0.0, "T": 100.0},
    }
    cache = {"Custom": Vec2(123, 456)}
    # Should return cached value immediately
    pos = resolve_absolute_position("Custom", 0.0, bodies=bodies, cache=cache)
    assert pos == Vec2(123, 456)


def test_resolve_caching_behavior() -> None:
    """AC1 & AC2: Verify caching behavior using the injected cache."""
    mock_bodies = {
        "Sun": {"primary": None},
        "Earth": {"primary": "Sun", "a": 1.0, "e": 0.0, "T": 1.0},
        "Moon": {"primary": "Earth", "a": 384400.0, "e": 0.0, "T": 27.32},
    }

    t = 9999.0
    cache: dict[str, Vec2] = {}

    with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
        mock_coords.return_value = Vec2(1.0, 0.0)

        # First call - should trigger calculation
        resolve_absolute_position("Moon", t, bodies=mock_bodies, cache=cache)
        initial_calls = mock_coords.call_count
        assert initial_calls > 0
        assert "Moon" in cache

        # Second call with same cache - should be cached
        resolve_absolute_position("Moon", t, bodies=mock_bodies, cache=cache)
        assert mock_coords.call_count == initial_calls

        # Third call with fresh cache - should recalculate
        fresh_cache: dict[str, Vec2] = {}
        resolve_absolute_position("Moon", t, bodies=mock_bodies, cache=fresh_cache)
        assert mock_coords.call_count > initial_calls


def test_performance_benchmark() -> None:
    """Verify 1000 recursive lookups take < 1ms with caching active."""
    from src.bodies import BODIES

    t = 0.0
    cache: dict[str, Vec2] = {}
    # Warm up
    resolve_absolute_position("Moon", t, bodies=BODIES, cache=cache)

    start_time = time.perf_counter()
    for _ in range(1000):
        resolve_absolute_position("Moon", t, bodies=BODIES, cache=cache)
    end_time = time.perf_counter()

    duration = end_time - start_time
    assert (
        duration < 0.001
    ), f"Performance requirement: 1000 lookups took {duration:.6f}s, expected < 0.001s"


def test_moon_earth_sun_stability() -> None:
    """AC3: Verify stability of Moon-Earth-Sun system over 100 years.

    Simulates 100 years (36525 days) at 1-day steps.
    Moon's heliocentric distance should remain within 1.0 AU +/- 0.02 AU.
    """
    from src.bodies import BODIES

    # This test uses real BODIES data.
    # Earth's eccentricity (0.0167) causes its distance to vary by +/- 0.0167 AU.
    # Moon's orbital radius is ~0.0025 AU.
    # Total variation is approx +/- 0.0192 AU.
    # 100 years = 36525 days.
    for day in range(36526):
        t = float(day)
        # Each tick in the simulation would have its own cache
        pos = resolve_absolute_position("Moon", t, bodies=BODIES, cache={})
        dist_au = pos.magnitude() / AU_TO_KM

        # Requirement: 1.0 AU +/- 0.02 AU
        assert (
            0.98 <= dist_au <= 1.02
        ), f"Stability failed at t={t}: dist={dist_au:.6f} AU"


def test_intermediate_node_caching() -> None:
    """Verify that resolving a child body populates the cache for its parent."""
    mock_bodies = {
        "Sun": {"primary": None},
        "Earth": {"primary": "Sun", "a": 1.0, "e": 0.0, "T": 1.0},
        "Moon": {"primary": "Earth", "a": 384400.0, "e": 0.0, "T": 27.32},
    }

    t = 123.456
    cache: dict[str, Vec2] = {}
    with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
        mock_coords.return_value = Vec2(1.0, 0.0)

        # Resolve Moon. This should recursively resolve Earth and Sun.
        resolve_absolute_position("Moon", t, bodies=mock_bodies, cache=cache)

        assert "Earth" in cache, "Parent 'Earth' should be cached"
        assert "Moon" in cache, "Child 'Moon' should be cached"

        # Earth should now be in the cache.
        calls_after_moon = mock_coords.call_count
        resolve_absolute_position("Earth", t, bodies=mock_bodies, cache=cache)

        assert (
            mock_coords.call_count == calls_after_moon
        ), "Earth should have been cached during Moon resolution"
