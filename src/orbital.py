# CHANGELOG:
# - Sprint 1: Implement Newton-Raphson Kepler solver and heliocentric coordinate logic.

"""Orbital mechanics engine for deterministic Keplerian motion."""

import math

from src.constants import MAX_ITERATIONS, SOLVER_TOLERANCE
from src.vector import Vec2


def solve_kepler(mean_anomaly: float, eccentricity: float) -> float:
    """Solve the transcendental Kepler equation M = E - e*sin(E) for E.

    Uses Newton-Raphson iteration to find the eccentric anomaly given the
    mean anomaly and eccentricity.

    Args:
        mean_anomaly: The mean anomaly (M) in radians.
        eccentricity: The orbital eccentricity (e).

    Returns:
        The eccentric anomaly (E) in radians.

    Raises:
        ValueError: If eccentricity is not in the range from 0 (inclusive) to 1 (exclusive).
        RuntimeError: If the solver fails to converge within MAX_ITERATIONS (ERR-001).
    """
    if not (0 <= eccentricity < 1.0):
        raise ValueError("Kepler solver only supports elliptical orbits (0 <= e < 1)")

    m = mean_anomaly
    e = eccentricity
    tol = SOLVER_TOLERANCE
    max_iter = MAX_ITERATIONS

    # Initial guess strategy (DR-001)
    if e < 0.8:
        eccentric_anomaly = m
    else:
        eccentric_anomaly = math.pi

    for _ in range(max_iter):
        f_e = eccentric_anomaly - e * math.sin(eccentric_anomaly) - m
        f_prime_e = 1 - e * math.cos(eccentric_anomaly)
        delta = f_e / f_prime_e
        eccentric_anomaly -= delta

        if abs(delta) < tol:
            return eccentric_anomaly

    raise RuntimeError("ERR-001: SOLVER_CONVERGENCE_FAILURE")


def mean_to_eccentric(mean_anomaly: float, eccentricity: float) -> float:
    """Convert mean anomaly to eccentric anomaly.

    Args:
        mean_anomaly: Mean anomaly (M) in radians.
        eccentricity: Orbital eccentricity (e).

    Returns:
        Eccentric anomaly (E) in radians.
    """
    return solve_kepler(mean_anomaly, eccentricity)


def eccentric_to_true(eccentric_anomaly: float, eccentricity: float) -> float:
    """Convert eccentric anomaly to true anomaly.

    Args:
        eccentric_anomaly: Eccentric anomaly (E) in radians.
        eccentricity: Orbital eccentricity (e).

    Returns:
        True anomaly (v) in radians.

    Raises:
        ValueError: If eccentricity is not in the range from 0 (inclusive) to 1 (exclusive).
    """
    if not (0 <= eccentricity < 1.0):
        raise ValueError("Kepler solver only supports elliptical orbits (0 <= e < 1)")

    e = eccentricity
    half_v = math.atan2(
        math.sqrt(1 + e) * math.sin(eccentric_anomaly / 2),
        math.sqrt(1 - e) * math.cos(eccentric_anomaly / 2),
    )
    return 2 * half_v


def get_heliocentric_coords(elements: dict[str, float], t: float) -> Vec2:
    """Calculate heliocentric coordinates for a body at simulation time t.

    Args:
        elements: Dictionary containing orbital elements:
            'a': Semi-major axis (AU or km)
            'e': Eccentricity
            'T': Orbital period (years or days)
        t: Simulation time.

    Returns:
        A Vec2 representing the position vector in the orbital plane.

    Raises:
        ValueError: If semi-major axis is not positive or eccentricity is not in the range from 0 (inclusive) to 1 (exclusive).
    """
    a = elements["a"]
    e = elements["e"]

    if a <= 0:
        raise ValueError("Semi-major axis must be positive")

    if not (0 <= e < 1.0):
        raise ValueError("Kepler solver only supports elliptical orbits (0 <= e < 1)")
    period = elements["T"]

    # Calculate mean motion n = 2*pi / T
    mean_motion = 2 * math.pi / period

    # Normalize t to the range [0, period) to maintain precision for large t
    t_norm = math.fmod(t, period)

    # Calculate mean anomaly M = (n * t_norm) mod (2*pi)
    mean_anomaly = (mean_motion * t_norm) % (2 * math.pi)

    # Convert anomalies
    eccentric_anomaly = mean_to_eccentric(mean_anomaly, e)
    true_anomaly = eccentric_to_true(eccentric_anomaly, e)

    # Calculate distance r = a * (1 - e * cos(E))
    distance = a * (1 - e * math.cos(eccentric_anomaly))

    # Create position vector in orbital plane
    return Vec2(distance * math.cos(true_anomaly), distance * math.sin(true_anomaly))
