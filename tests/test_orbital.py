import math
from unittest.mock import patch

import pytest

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
