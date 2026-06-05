"""Tests for the procedural asteroid belt generator.

Verifies determinism, Kirkwood gap distribution, Keplerian physics,
and integration with the hierarchical frame system.
"""

from typing import Generator

import pytest

from src.bodies import BODIES, calculate_depletion
from src.constants import AU_TO_KM
from src.frames import resolve_absolute_position
from src.vector import Vec2

# Import the generator - expected to fail in TDD Red phase
try:
    from src.bodies import generate_asteroid_belt
except ImportError:
    generate_asteroid_belt = None  # type: ignore


@pytest.fixture
def clean_bodies() -> Generator[None, None, None]:
    """Isolates the BODIES registry for asteroid generation tests.

    Saves the original state, clears it to just the Sun, and restores
    the original state after the test.
    """
    original_bodies = BODIES.copy()
    BODIES.clear()
    # Asteroids orbit the Sun, so it must be present
    BODIES["Sun"] = original_bodies["Sun"]

    yield

    BODIES.clear()
    BODIES.update(original_bodies)


def test_generator_exists() -> None:
    """Verify that the generator function is defined in src.bodies."""
    assert generate_asteroid_belt is not None, "generate_asteroid_belt not found in src.bodies"


def test_calculate_depletion_at_gap_center() -> None:
    """Verify that survival probability is low at the center of a Kirkwood gap."""
    # Gap at 2.50 AU
    prob = calculate_depletion(2.50)
    # Expected: 1.0 - STRENGTH (0.999) = 0.001
    assert prob < 0.01, f"Expected low survival probability at gap center, got {prob}"


def test_calculate_depletion_outside_gaps() -> None:
    """Verify that survival probability is high far from Kirkwood gaps."""
    # 2.20 AU is far from [2.50, 2.82, 2.96, 3.27]
    prob = calculate_depletion(2.20)
    assert prob > 0.90, f"Expected high survival probability outside gaps, got {prob}"


@pytest.mark.usefixtures("clean_bodies")
def test_asteroid_determinism() -> None:
    """Verify that calling the generator with the same seed produces identical results."""
    seed = 42
    count = 10

    # First generation
    generate_asteroid_belt(seed=seed, count=count)
    state_1 = {name: data.copy() for name, data in BODIES.items() if name != "Sun"}

    # Reset and second generation
    BODIES.clear()
    BODIES["Sun"] = {"radius": 696340.0, "color": (255, 255, 0), "primary": None}
    generate_asteroid_belt(seed=seed, count=count)
    state_2 = {name: data.copy() for name, data in BODIES.items() if name != "Sun"}

    assert state_1 == state_2
    assert len(state_1) == count


@pytest.mark.usefixtures("clean_bodies")
def test_kirkwood_gap_distribution() -> None:
    """Verify that Kirkwood gaps have significantly lower asteroid density.

    Gaps are expected at 2.50, 2.82, 2.96, and 3.27 AU.
    Density in gap bins should be >= 70% lower than neighboring non-gap bins.
    """
    generate_asteroid_belt(seed=123, count=5000)
    asteroids = [data for name, data in BODIES.items() if name != "Sun"]

    gap_centers = [2.50, 2.82, 2.96, 3.27]
    bin_width = 0.05
    min_a, max_a = 2.1, 3.3

    # Create bins
    num_bins = int((max_a - min_a) / bin_width) + 1
    bins = [0] * num_bins

    for ast in asteroids:
        a = ast["a"]
        bin_idx = int((a - min_a) / bin_width)
        if 0 <= bin_idx < num_bins:
            bins[bin_idx] += 1

    for gap in gap_centers:
        gap_bin_idx = int((gap - min_a) / bin_width)

        # Calculate neighbor average (avoiding other gaps if possible)
        neighbors = []
        # Use a wider window for neighbors to get a better baseline
        for offset in range(-5, 6):
            if offset == 0:
                continue
            idx = gap_bin_idx + offset
            if 0 <= idx < num_bins:
                # Only include if not another gap bin (using 0.06 AU threshold)
                bin_center = min_a + idx * bin_width + bin_width / 2
                is_another_gap = any(abs(bin_center - g) < 0.06 for g in gap_centers)
                if not is_another_gap:
                    neighbors.append(bins[idx])

        if not neighbors:
            continue

        avg_neighbor_density = sum(neighbors) / len(neighbors)
        gap_density = bins[gap_bin_idx]

        # Requirement: >= 70% lower density
        # gap_density <= avg_neighbor_density * (1 - 0.70)
        assert gap_density <= avg_neighbor_density * 0.30, (
            f"Gap at {gap} AU (bin {gap_bin_idx}) failed density check. "
            f"Gap density: {gap_density}, Neighbor avg: {avg_neighbor_density}"
        )


@pytest.mark.usefixtures("clean_bodies")
def test_kepler_third_law_compliance() -> None:
    """Verify that generated asteroids satisfy T^2 / a^3 = 1.0."""
    generate_asteroid_belt(seed=999, count=100)
    for name, data in BODIES.items():
        if name == "Sun":
            continue
        a = data["a"]
        T = data["T"]
        # Kepler's 3rd Law: T^2 / a^3 = 1.0 (for AU and Years)
        ratio = (T**2) / (a**3)
        assert abs(ratio - 1.0) < 1e-6, f"Asteroid {name} violates Kepler's 3rd Law: ratio={ratio}"


@pytest.mark.usefixtures("clean_bodies")
def test_belt_boundaries() -> None:
    """Verify that all generated asteroids fall within the [2.1, 3.3] AU range."""
    generate_asteroid_belt(seed=777, count=1000)
    for name, data in BODIES.items():
        if name == "Sun":
            continue
        a = data["a"]
        assert 2.1 <= a <= 3.3, f"Asteroid {name} outside belt boundaries: a={a}"


@pytest.mark.usefixtures("clean_bodies")
def test_frame_resolution_for_asteroids() -> None:
    """Verify that generated asteroids are correctly resolved by the frame system."""
    generate_asteroid_belt(seed=1, count=10)
    # Pick the first asteroid
    ast_names = [name for name in BODIES.keys() if name.startswith("Ast-")]
    assert ast_names, "No asteroids generated with 'Ast-' prefix"

    target_name = ast_names[0]
    pos = resolve_absolute_position(target_name, t=0.0)

    assert isinstance(pos, Vec2), f"Expected Vec2 from resolve_absolute_position, got {type(pos)}"
    # Basic sanity check: asteroid at ~2.1-3.3 AU should be at correct distance in km
    dist = pos.magnitude()
    # Use a slightly wider tolerance for the distance check to account for eccentricity
    # r = a(1-e) to a(1+e). e is [0.05, 0.30].
    # Min r = 2.1 * (1 - 0.30) = 1.47 AU
    # Max r = 3.3 * (1 + 0.30) = 4.29 AU
    assert 1.4 * AU_TO_KM <= dist <= 4.4 * AU_TO_KM, f"Asteroid {target_name} at unexpected distance: {dist} km"
