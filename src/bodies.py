# CHANGELOG:
# - Sprint 1: Initialize J2000 reference data for solar system bodies.
# - Sprint 3: Add BodyData TypedDict for type safety.
# - Sprint 4: Implement procedural asteroid belt generation with Kirkwood gaps.
# - Sprint 5: Refactor to provider-based architecture (BodyProvider).

from __future__ import annotations

import math
import random
from collections.abc import Iterator
from typing import Protocol, TypedDict, runtime_checkable

"""J2000-epoch reference values for the solar system.
a = semi-major axis (AU for Sun orbits, km for others)
e = eccentricity
T = orbital period (years for Sun orbits, days for others)
radius = mean physical radius (km)

Note: A negative orbital period (T) signifies retrograde motion (e.g., Triton).
"""


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


@runtime_checkable
class BodyProvider(Protocol):
    """Protocol for body data retrieval and grouping."""

    def get_body(self, name: str) -> BodyData:
        """Return data for a specific body.

        Args:
            name: Unique identifier of the body.

        Returns:
            BodyData dictionary.

        Raises:
            KeyError: If the body name is not found in the provider.
        """
        ...

    def list_bodies(self) -> list[str]:
        """Return names of all individual bodies managed by this provider.

        Returns:
            List of body name strings.
        """
        ...

    def get_groups(self) -> dict[str, list[str]]:
        """Return semantic groups of bodies (e.g., 'AsteroidBelt').

        Returns:
            Dictionary mapping group names to lists of body names.
        """
        ...

    def __contains__(self, name: str) -> bool:
        """Check if a body exists in the provider.

        Args:
            name: Unique identifier of the body.

        Returns:
            True if the body exists, False otherwise.
        """
        ...

    def __iter__(self) -> Iterator[str]:
        """Iterate over all body names managed by this provider.

        Returns:
            Iterator of body name strings.
        """
        ...


_STATIC_BODIES_DATA: dict[str, BodyData] = {
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


def generate_asteroid_belt(seed: int, count: int = 1000) -> dict[str, BodyData]:
    """Procedurally generate a deterministic asteroid belt with Kirkwood gaps.

    Returns a new dictionary of asteroids instead of mutating global state.

    Args:
        seed: PRNG seed for determinism.
        count: Number of asteroids to generate.

    Returns:
        A dictionary mapping asteroid names to their BodyData.
    """
    rng = random.Random(seed)
    asteroids: dict[str, BodyData] = {}

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

            asteroids[name] = {
                "primary": "Sun",
                "a": a,
                "e": e,
                "T": t_period,
                "radius": radius,
                "color": color,
            }

            generated_count += 1

    return asteroids


class StaticBodyProvider:
    """Wraps a static dictionary of BodyData."""

    def __init__(self, data: dict[str, BodyData]) -> None:
        """Initialize with a dictionary of body data.

        Args:
            data: Dictionary mapping body names to BodyData.

        Returns:
            None
        """
        self._data = data

    def get_body(self, name: str) -> BodyData:
        """Return data for a specific body.

        Args:
            name: Unique identifier of the body.

        Returns:
            BodyData dictionary.

        Raises:
            KeyError: If the body name is not found.
        """
        return self._data[name]

    def list_bodies(self) -> list[str]:
        """Return names of all individual bodies.

        Returns:
            List of body name strings.
        """
        return list(self._data.keys())

    def get_groups(self) -> dict[str, list[str]]:
        """Return semantic groups of bodies. Static provider has no groups.

        Returns:
            Empty dictionary.
        """
        return {}

    def __contains__(self, name: str) -> bool:
        """Check if a body exists in the provider.

        Args:
            name: Unique identifier of the body.

        Returns:
            True if the body exists, False otherwise.
        """
        return name in self._data

    def __iter__(self) -> Iterator[str]:
        """Iterate over all body names.

        Returns:
            Iterator of body name strings.
        """
        return iter(self._data)


class AsteroidBeltProvider:
    """Procedurally generates an asteroid belt and exposes it as a group."""

    def __init__(self, seed: int, count: int = 1000) -> None:
        """Initialize and generate the asteroid belt.

        Args:
            seed: PRNG seed for deterministic generation.
            count: Number of asteroids to generate.

        Returns:
            None
        """
        self._asteroids = generate_asteroid_belt(seed, count)

    def get_body(self, name: str) -> BodyData:
        """Return data for a specific asteroid.

        Args:
            name: Unique identifier of the asteroid.

        Returns:
            BodyData dictionary.

        Raises:
            KeyError: If the asteroid name is not found.
        """
        return self._asteroids[name]

    def list_bodies(self) -> list[str]:
        """Return names of all generated asteroids.

        Returns:
            List of asteroid name strings.
        """
        return list(self._asteroids.keys())

    def get_groups(self) -> dict[str, list[str]]:
        """Return semantic groups. Asteroids are grouped under 'AsteroidBelt'.

        Returns:
            Dictionary mapping 'AsteroidBelt' to the list of asteroid names.
        """
        return {"AsteroidBelt": self.list_bodies()}

    def __contains__(self, name: str) -> bool:
        """Check if an asteroid exists in the provider.

        Args:
            name: Unique identifier of the asteroid.

        Returns:
            True if the asteroid exists, False otherwise.
        """
        return name in self._asteroids

    def __iter__(self) -> Iterator[str]:
        """Iterate over all asteroid names.

        Returns:
            Iterator of asteroid name strings.
        """
        return iter(self._asteroids)


class CompositeBodyProvider:
    """Aggregates multiple providers with priority-based resolution."""

    def __init__(self, providers: list[BodyProvider]) -> None:
        """Initialize with a list of providers.

        Args:
            providers: List of BodyProvider instances.

        Returns:
            None
        """
        self._providers = providers

    def get_body(self, name: str) -> BodyData:
        """Return data for a specific body, searching providers in order.

        Args:
            name: Unique identifier of the body.

        Returns:
            BodyData dictionary.

        Raises:
            KeyError: If the body name is not found in any provider.
        """
        for provider in self._providers:
            if name in provider:
                return provider.get_body(name)
        raise KeyError(name)

    def list_bodies(self) -> list[str]:
        """Return names of all individual bodies from all providers.

        Returns:
            Sorted list of unique body name strings.
        """
        bodies: set[str] = set()
        for provider in self._providers:
            bodies.update(provider.list_bodies())
        return sorted(list(bodies))

    def get_groups(self) -> dict[str, list[str]]:
        """Return semantic groups merged from all providers.

        Returns:
            Dictionary mapping group names to lists of body names.
        """
        groups: dict[str, list[str]] = {}
        for provider in self._providers:
            for group_name, members in provider.get_groups().items():
                if group_name in groups:
                    groups[group_name].extend(members)
                else:
                    groups[group_name] = list(members)
        return groups

    def __contains__(self, name: str) -> bool:
        """Check if a body exists in any of the providers.

        Args:
            name: Unique identifier of the body.

        Returns:
            True if the body exists, False otherwise.
        """
        for provider in self._providers:
            if name in provider:
                return True
        return False

    def __iter__(self) -> Iterator[str]:
        """Iterate over all unique body names from all providers.

        Returns:
            Iterator of body name strings.
        """
        return iter(self.list_bodies())


# Initialize the global registry
BODIES: BodyProvider = CompositeBodyProvider(
    [
        StaticBodyProvider(_STATIC_BODIES_DATA),
        AsteroidBeltProvider(seed=42, count=1000),
    ]
)
