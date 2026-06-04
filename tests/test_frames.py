import unittest.mock as mock
import time
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
        "Moon": {"primary": "Earth", "a": 384400.0, "e": 0.0, "T": 27.32},
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
    mock_bodies = {"A": {"primary": "B"}, "B": {"primary": "A"}}

    with mock.patch("src.frames.BODIES", mock_bodies):
        with pytest.raises(RuntimeError, match="ERR-003: CIRCULAR_FRAME_DEPENDENCY"):
            resolve_absolute_position("A", 0.0)


def test_unit_conversion_boundary():
    """Scenario D: Unit Conversion Boundary."""
    mock_bodies = {
        "Sun": {"primary": None},
        "Mercury": {"primary": "Sun", "a": 0.387, "e": 0.0, "T": 0.24},
    }

    with mock.patch("src.frames.BODIES", mock_bodies):
        with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
            mock_coords.return_value = Vec2(0.387, 0.0)

            pos = resolve_absolute_position("Mercury", 0.0)
            # Should be scaled by AU_TO_KM
            assert pos == Vec2(0.387 * AU_TO_KM, 0.0)


def test_resolve_caching_behavior() -> None:
    """AC1 & AC2: Verify caching and invalidation behavior."""
    mock_bodies = {
        "Sun": {"primary": None},
        "Earth": {"primary": "Sun", "a": 1.0, "e": 0.0, "T": 1.0},
        "Moon": {"primary": "Earth", "a": 384400.0, "e": 0.0, "T": 27.32},
    }

    # Use a unique simulation time to avoid interference with other tests
    t_initial = 9999.0
    t_new = 10000.0

    with mock.patch("src.frames.BODIES", mock_bodies):
        with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
            mock_coords.return_value = Vec2(1.0, 0.0)

            # First call - should trigger calculation
            resolve_absolute_position("Moon", t_initial)
            initial_calls = mock_coords.call_count
            assert (
                initial_calls > 0
            ), "First call should trigger coordinate calculations"

            # Second call at same time - should be cached
            resolve_absolute_position("Moon", t_initial)
            # AC1: call_count should not increase
            assert (
                mock_coords.call_count == initial_calls
            ), f"AC1: Second call at t={t_initial} should return cached value"

            # Third call at different time - should invalidate cache
            resolve_absolute_position("Moon", t_new)
            # AC2: call_count should increase
            assert (
                mock_coords.call_count > initial_calls
            ), f"AC2: Different time t={t_new} should invalidate cache"




def test_performance_benchmark() -> None:
    """Verify 1000 recursive lookups take < 1ms with caching active.

    Expected to FAIL until caching is implemented in src/frames.py.
    """
    # Use a deep hierarchy if possible, but Moon->Earth->Sun is 2 levels deep.
    # 1000 calls to a 2-level recursion without caching might already be fast,
    # but caching should make it significantly faster.

    t = 0.0
    # Warm up (and populate cache once implemented)
    resolve_absolute_position("Moon", t)

    start_time = time.perf_counter()
    for _ in range(1000):
        resolve_absolute_position("Moon", t)
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
    # This test uses real BODIES data.
    # Earth's eccentricity (0.0167) causes its distance to vary by +/- 0.0167 AU.
    # Moon's orbital radius is ~0.0025 AU.
    # Total variation is approx +/- 0.0192 AU.
    # 100 years = 36525 days.
    for day in range(36526):
        t = float(day)
        pos = resolve_absolute_position("Moon", t)
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
    with mock.patch("src.frames.BODIES", mock_bodies):
        with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
            mock_coords.return_value = Vec2(1.0, 0.0)

            # Resolve Moon. This should recursively resolve Earth and Sun.
            resolve_absolute_position("Moon", t)

            # Earth should now be in the cache.
            # We verify this by calling resolve_absolute_position("Earth", t)
            # and checking that mock_coords was NOT called again.
            calls_after_moon = mock_coords.call_count

            resolve_absolute_position("Earth", t)

            assert (
                mock_coords.call_count == calls_after_moon
            ), "Earth should have been cached during Moon resolution"


def test_cache_initialization_edge_case() -> None:
    """Verify cache behavior at t=0.0 and transitions from None."""
    # _LAST_SIM_TIME starts as None. t=0.0 should trigger a clear and update.
    mock_bodies = {
        "Sun": {"primary": None},
        "Earth": {"primary": "Sun", "a": 1.0, "e": 0.0, "T": 1.0},
    }

    with mock.patch("src.frames.BODIES", mock_bodies):
        with mock.patch("src.frames.get_heliocentric_coords") as mock_coords:
            mock_coords.return_value = Vec2(1.0, 0.0)

            # Call at t=0.0
            resolve_absolute_position("Earth", 0.0)
            assert mock_coords.call_count > 0

            # Call again at t=0.0 - should be cached
            calls_first = mock_coords.call_count
            resolve_absolute_position("Earth", 0.0)
            assert mock_coords.call_count == calls_first

            # Call at t=1.0 - should invalidate
            resolve_absolute_position("Earth", 1.0)
            assert mock_coords.call_count > calls_first