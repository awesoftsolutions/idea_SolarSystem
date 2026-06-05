# CHANGELOG:
# - Sprint 1: Initialize J2000 reference data for solar system bodies.
# - Sprint 3: Add BodyData TypedDict for type safety.
# - Sprint 4: Implement procedural asteroid belt generation with Kirkwood gaps.

"""J2000-epoch reference values for the solar system.
a = semi-major axis (AU for Sun orbits, km for others)
e = eccentricity
T = orbital period (years for Sun orbits, days for others)
radius = mean physical radius (km)

Note: A negative orbital period (T) signifies retrograde motion (e.g., Triton).
"""

import math
import random
from typing import TypedDict


class BodyData(TypedDict, total=False):
    """Data contract for a solar system body.

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


BODIES: dict[str, BodyData] = {
    "Sun": {"radius": 696340.0, "color": (255, 255, 0), "primary": None},
    # Bodies orbiting the Sun
    # High-precision J2000 semi-major axis (a) values.
    # T is calculated as a^1.5 to satisfy Kepler's 3rd Law (T^2/a^3 = 1.0) within 0.1%.
    "Mercury": {
        "a": 0.387098,
        "e": 0.205630,
        "T": 0.2408467,
        "radius": 2440.0,
        "primary": "Sun",
        "color": (165, 165, 165),
    },
    "Venus": {
        "a": 0.723332,
        "e": 0.006773,
        "T": 0.6151972,
        "radius": 6052.0,
        "primary": "Sun",
        "color": (255, 198, 73),
    },
    "Earth": {
        "a": 1.000000,
        "e": 0.016708,
        "T": 1.0000000,
        "radius": 6371.0,
        "primary": "Sun",
        "color": (100, 149, 237),
    },
    "Mars": {
        "a": 1.523662,
        "e": 0.093412,
        "T": 1.8808476,
        "radius": 3390.0,
        "primary": "Sun",
        "color": (226, 110, 71),
    },
    "Jupiter": {
        "a": 5.203363,
        "e": 0.048392,
        "T": 11.868203,
        "radius": 69911.0,
        "primary": "Sun",
        "color": (255, 165, 0),
    },
    "Saturn": {
        "a": 9.537070,
        "e": 0.054150,
        "T": 29.447498,
        "radius": 58232.0,
        "primary": "Sun",
        "color": (210, 180, 140),
    },
    "Uranus": {
        "a": 19.191263,
        "e": 0.047167,
        "T": 84.074743,
        "radius": 25362.0,
        "primary": "Sun",
        "color": (173, 216, 230),
    },
    "Neptune": {
        "a": 30.068963,
        "e": 0.008585,
        "T": 164.884675,
        "radius": 24622.0,
        "primary": "Sun",
        "color": (65, 105, 225),
    },
    # Moons
    "Moon": {
        "primary": "Earth",
        "a": 384400.0,
        "e": 0.0549,
        "T": 27.32,
        "radius": 1737.0,
        "color": (200, 200, 200),
    },
    "Io": {
        "primary": "Jupiter",
        "a": 421700.0,
        "e": 0.0041,
        "T": 1.77,
        "radius": 1822.0,
        "color": (255, 255, 0),
    },
    "Europa": {
        "primary": "Jupiter",
        "a": 671000.0,
        "e": 0.0094,
        "T": 3.55,
        "radius": 1561.0,
        "color": (240, 230, 140),
    },
    "Ganymede": {
        "primary": "Jupiter",
        "a": 1070000.0,
        "e": 0.0013,
        "T": 7.15,
        "radius": 2634.0,
        "color": (128, 128, 128),
    },
    "Callisto": {
        "primary": "Jupiter",
        "a": 1883000.0,
        "e": 0.0074,
        "T": 16.69,
        "radius": 2410.0,
        "color": (105, 105, 105),
    },
    "Titan": {
        "primary": "Saturn",
        "a": 1222000.0,
        "e": 0.0288,
        "T": 15.95,
        "radius": 2575.0,
        "color": (255, 215, 0),
    },
    "Phobos": {
        "primary": "Mars",
        "a": 9376.0,
        "e": 0.0151,
        "T": 0.319,
        "radius": 11.0,
        "color": (139, 69, 19),
    },
    "Deimos": {
        "primary": "Mars",
        "a": 23460.0,
        "e": 0.0002,
        "T": 1.26,
        "radius": 6.0,
        "color": (160, 82, 45),
    },
    "Triton": {
        "primary": "Neptune",
        "a": 354800.0,
        "e": 0.000016,
        "T": -5.88,
        "radius": 1353.0,
        "color": (255, 250, 250),
    },
    # Minor bodies
    "Ceres": {
        "a": 2.766,
        "e": 0.0758,
        "T": 4.599,
        "radius": 473.0,
        "primary": "Sun",
        "color": (210, 210, 210),
    },
    "Vesta": {
        "a": 2.362,
        "e": 0.0887,
        "T": 3.630,
        "radius": 263.0,
        "primary": "Sun",
        "color": (220, 220, 220),
    },
    "Pallas": {
        "a": 2.773,
        "e": 0.2306,
        "T": 4.617,
        "radius": 256.0,
        "primary": "Sun",
        "color": (230, 230, 230),
    },
    "Hygiea": {
        "a": 3.142,
        "e": 0.1125,
        "T": 5.5695,
        "radius": 217.0,
        "primary": "Sun",
        "color": (240, 240, 240),
    },
    # Comets
    "1P/Halley": {
        "a": 17.834,
        "e": 0.967,
        "T": 75.31,
        "radius": 5.5,
        "primary": "Sun",
        "color": (255, 255, 255),
    },
    "2P/Encke": {
        "a": 2.215,
        "e": 0.848,
        "T": 3.297,
        "radius": 2.4,
        "primary": "Sun",
        "color": (245, 245, 245),
    },
    "Hale-Bopp": {
        "a": 186.0,
        "e": 0.995,
        "T": 2536.8,
        "radius": 30.0,
        "primary": "Sun",
        "color": (250, 250, 250),
    },
}


def calculate_depletion(a: float) -> float:
    """Calculate the survival probability of an asteroid at semi-major axis a.

    Uses Gaussian depletion at Kirkwood gaps (2.50, 2.82, 2.96, 3.27 AU).

    Args:
        a: Semi-major axis in AU.

    Returns:
        Survival probability in range [0.0, 1.0].
    """
    gaps = [2.50, 2.82, 2.96, 3.27]
    sigma = 0.04  # Even wider gaps for stronger depletion in the bin
    strength = 0.999  # Near-total depletion at center

    max_depletion = 0.0
    for gap in gaps:
        diff = a - gap
        factor = strength * math.exp(-(diff**2) / (2 * sigma**2))
        max_depletion = max(max_depletion, factor)

    return 1.0 - max_depletion


def generate_asteroid_belt(seed: int, count: int = 1000) -> None:
    """Procedurally generate a deterministic asteroid belt with Kirkwood gaps.

    Mutates the global BODIES dictionary.

    Args:
        seed: PRNG seed for determinism.
        count: Number of asteroids to generate.
    """
    rng = random.Random(seed)

    generated_count = 0
    while generated_count < count:
        a = rng.uniform(2.1, 3.3)
        prob = calculate_depletion(a)

        if rng.random() < prob:
            e = rng.uniform(0.05, 0.30)
            t_period = a**1.5  # Kepler's 3rd Law: T^2 = a^3 -> T = a^1.5

            name = f"Ast-{str(generated_count).zfill(4)}"
            color = (
                rng.randint(150, 220),
                rng.randint(150, 220),
                rng.randint(150, 220),
            )
            radius = rng.uniform(1.0, 5.0)

            BODIES[name] = {
                "primary": "Sun",
                "a": a,
                "e": e,
                "T": t_period,
                "radius": radius,
                "color": color,
            }

            generated_count += 1
