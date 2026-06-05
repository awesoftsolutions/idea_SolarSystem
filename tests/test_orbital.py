import math
from unittest.mock import patch

import pytest

from src.bodies import BODIES
from src.constants import SOLVER_TOLERANCE
from src.orbital import (
    eccentric_to_true,
    get_heliocentric_coords,
    mean_to_eccentric,
    solve_kepler,
)
from src.vector import Vec2


def test_solve_kepler_convergence_low_e():
    """Scenario 1: Low Eccentricity (Planetary) convergence check."""
    e = 0.0167  # Earth
    mean_anomalies = [0, math.pi / 2, math.pi, 3 * math.pi / 2]

    for M in mean_anomalies:
        # Use patch to count iterations by tracking calls to math.cos (used in f'(E))
        with patch("math.cos", wraps=math.cos) as mock_cos:
            E = solve_kepler(M, e)
            # Verify convergence
            assert abs(E - e * math.sin(E) - M) < SOLVER_TOLERANCE
            # Earth should converge very quickly (< 10 iterations)
            assert mock_cos.call_count < 10


def test_solve_kepler_convergence_high_e():
    """Scenario 2: High Eccentricity (Cometary) convergence check."""
    e = 0.967  # Halley
    mean_anomalies = [0, 0.1, math.pi / 2, math.pi]

    for M in mean_anomalies:
        with patch("math.cos", wraps=math.cos) as mock_cos:
            E = solve_kepler(M, e)
            # Verify convergence
            assert abs(E - e * math.sin(E) - M) < SOLVER_TOLERANCE
            # High eccentricity should still converge within 100 iterations
            assert mock_cos.call_count < 100


def test_solve_kepler_convergence_extreme_e():
    """Scenario 3: Extreme Eccentricity convergence check."""
    e = 0.995  # Hale-Bopp
    M = 0.01
    E = solve_kepler(M, e)
    assert abs(E - e * math.sin(E) - M) < SOLVER_TOLERANCE


def test_circular_orbit():
    """Scenario 4: Circular Orbit consistency."""
    e = 0
    M = 1.0
    E = mean_to_eccentric(M, e)
    v = eccentric_to_true(E, e)
    assert E == pytest.approx(1.0)
    assert v == pytest.approx(1.0)


def test_zero_anomaly():
    """Scenario 5: Zero Anomaly consistency."""
    e = 0.5
    M = 0
    E = mean_to_eccentric(M, e)
    v = eccentric_to_true(E, e)
    assert E == 0
    assert v == 0


def test_get_heliocentric_coords_perihelion():
    """Scenario 6: Perihelion (t=0) position check."""
    elements = {"a": 1.0, "e": 0.1, "T": 1.0}
    t = 0
    pos = get_heliocentric_coords(elements, t)
    # At t=0, M=0, E=0, v=0. r = a(1-e) = 1.0(1-0.1) = 0.9
    assert isinstance(pos, Vec2)
    assert pos.x == pytest.approx(0.9, abs=SOLVER_TOLERANCE)
    assert pos.y == pytest.approx(0.0, abs=SOLVER_TOLERANCE)


def test_get_heliocentric_coords_aphelion():
    """Scenario 7: Aphelion (t=T/2) position check."""
    elements = {"a": 1.0, "e": 0.1, "T": 1.0}
    t = 0.5
    pos = get_heliocentric_coords(elements, t)
    # At t=T/2, M=pi, E=pi, v=pi. r = a(1+e) = 1.0(1+0.1) = 1.1. x = r*cos(pi) = -1.1
    assert isinstance(pos, Vec2)
    assert pos.x == pytest.approx(-1.1, abs=SOLVER_TOLERANCE)
    assert pos.y == pytest.approx(0.0, abs=SOLVER_TOLERANCE)


def test_get_heliocentric_coords_quadrant():
    """Scenario 8: Quadrant Check (t=T/4)."""
    elements = {"a": 1.0, "e": 0.1, "T": 1.0}
    t = 0.25
    pos = get_heliocentric_coords(elements, t)
    # At t=T/4, M=pi/2. Since e>0, E will be between pi/2 and pi.
    # Therefore x < 0 and y > 0.
    assert pos.x < 0
    assert pos.y > 0


def test_solve_kepler_convergence_failure():
    """Scenario 9: Convergence Failure error handling."""
    # Force failure by mocking MAX_ITERATIONS to a very low value
    with patch("src.orbital.MAX_ITERATIONS", 1):
        with pytest.raises(RuntimeError, match="ERR-001"):
            # Halley at M=0.1 is unlikely to converge in 1 iteration
            solve_kepler(0.1, 0.967)


def calculate_swept_area(
    elements: dict[str, float], start_t: float, duration: float
) -> float:
    """Numerical integration of swept area over 2000 steps.

    Uses the triangle area formula 0.5 * abs(x1*y2 - x2*y1) for each step.

    Args:
        elements: Orbital elements dictionary.
        start_t: Start time of the interval.
        duration: Duration of the interval.

    Returns:
        Total swept area.
    """
    total_area = 0.0
    steps = 2000
    dt = duration / steps

    for i in range(steps):
        t1 = start_t + i * dt
        t2 = start_t + (i + 1) * dt

        r1 = get_heliocentric_coords(elements, t1)
        r2 = get_heliocentric_coords(elements, t2)

        # 2D Cross product magnitude for triangle area
        triangle_area = 0.5 * abs(r1.x * r2.y - r2.x * r1.y)
        total_area += triangle_area

    return total_area


def test_kepler_second_law_functional():
    """Verify Kepler's 2nd Law: Equal areas swept in equal time."""
    interval_days = 30.0
    interval_years = interval_days / 365.25

    for name in BODIES.list_bodies():
        data = BODIES.get_body(name)
        if data.get("primary") != "Sun" or name == "Sun":
            continue

        # Area at perihelion (t=0)
        area_perihelion = calculate_swept_area(data, 0.0, interval_years)

        # Area at aphelion (t=T/2)
        area_aphelion = calculate_swept_area(data, data["T"] / 2.0, interval_years)

        # Tolerance: 1e-7 for planets, 1e-6 for comets (as per requirements)
        tolerance = 1e-6 if data["e"] > 0.8 else 1e-7

        assert area_perihelion == pytest.approx(area_aphelion, abs=tolerance), (
            f"Kepler's 2nd Law failed for {name}: "
            f"perihelion area {area_perihelion}, aphelion area {area_aphelion}"
        )


def test_kepler_third_law_functional():
    """Verify Kepler's 3rd Law: T^2 / a^3 is constant for heliocentric bodies."""
    ratios = {}

    for name in BODIES.list_bodies():
        data = BODIES.get_body(name)
        if data.get("primary") == "Sun":
            a = data["a"]
            t = data["T"]
            ratios[name] = (t * t) / (a * a * a)

    # Use Mercury as the reference (as per requirements)
    mercury_ratio = ratios["Mercury"]

    for name, ratio in ratios.items():
        # Ratios should match within 0.1% (Sprint 1 Task 4 Requirement)
        # Note: J2000 reference data has slight variations due to planetary masses.
        # High-precision data is required to meet this tolerance.
        assert ratio == pytest.approx(mercury_ratio, rel=0.001), (
            f"Kepler's 3rd Law failed for {name}: ratio {ratio}, "
            f"expected approx {mercury_ratio}"
        )


def test_get_heliocentric_coords_large_t():
    """Verify precision for very large simulation times."""
    # Use Earth elements
    elements = BODIES.get_body("Earth")
    period = elements["T"]

    # Position at t=0
    pos_start = get_heliocentric_coords(elements, 0.0)

    # Position after 1 billion orbits (t = 10^9 * T)
    # This should be identical to t=0 in a perfect periodic system.
    large_t = 1_000_000_000.0 * period
    pos_large = get_heliocentric_coords(elements, large_t)

    assert pos_large.x == pytest.approx(
        pos_start.x, abs=SOLVER_TOLERANCE
    ), f"Precision loss at large t: {pos_large.x} vs {pos_start.x}"
    assert pos_large.y == pytest.approx(
        pos_start.y, abs=SOLVER_TOLERANCE
    ), f"Precision loss at large t: {pos_large.y} vs {pos_start.y}"


def test_solve_kepler_invalid_eccentricity() -> None:
    """Verify solve_kepler raises ValueError for invalid eccentricity."""
    # e < 0
    with pytest.raises(ValueError, match="elliptical orbits"):
        solve_kepler(0.1, -0.1)
    # e = 1.0 (parabolic)
    with pytest.raises(ValueError, match="elliptical orbits"):
        solve_kepler(0.1, 1.0)
    # e > 1.0 (hyperbolic)
    with pytest.raises(ValueError, match="elliptical orbits"):
        solve_kepler(0.1, 1.5)


def test_eccentric_to_true_invalid_eccentricity() -> None:
    """Verify eccentric_to_true raises ValueError for invalid eccentricity."""
    # e < 0
    with pytest.raises(ValueError, match="elliptical orbits"):
        eccentric_to_true(0.1, -0.1)
    # e = 1.0
    with pytest.raises(ValueError, match="elliptical orbits"):
        eccentric_to_true(0.1, 1.0)


def test_get_heliocentric_coords_invalid_elements() -> None:
    """Verify get_heliocentric_coords raises ValueError for invalid elements."""
    # Invalid eccentricity
    with pytest.raises(ValueError, match="elliptical orbits"):
        get_heliocentric_coords({"a": 1.0, "e": 1.1, "T": 1.0}, 0.0)

    # Invalid semi-major axis (a <= 0)
    with pytest.raises(ValueError, match="Semi-major axis must be positive"):
        get_heliocentric_coords({"a": 0.0, "e": 0.1, "T": 1.0}, 0.0)
    with pytest.raises(ValueError, match="Semi-major axis must be positive"):
        get_heliocentric_coords({"a": -1.0, "e": 0.1, "T": 1.0}, 0.0)
