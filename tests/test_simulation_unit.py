"""Unit tests for the core simulation engine.

These tests cover the SimulationClock for time management and the Simulation
class for deterministic, side-effect-free state retrieval.
"""

from unittest.mock import patch

import pytest

from src.vector import Vec2
from src.bodies import BODIES
from src.frames import resolve_absolute_position
from src.simulation import Simulation, SimulationClock


class TestSimulationCaching:
    """Tests for Simulation state caching behavior (AC1, AC2)."""

    @pytest.fixture
    def simulation(self) -> Simulation:
        """Provide a Simulation instance with a default clock and injected bodies."""
        clock = SimulationClock()
        return Simulation(clock=clock, bodies=BODIES)

    def test_cache_hit_ac1(self, simulation: Simulation) -> None:
        """Verify recursive resolutions are performed only once per t (AC1)."""
        t = 1.0
        # In the refactored Simulation, get_system_state passes self.bodies and a tick_cache
        # to resolve_absolute_position.
        # If Sun is in bodies, it is resolved via resolve_absolute_position.
        # If not, it is injected into tick_cache directly.
        from src.bodies import BodyProvider

        assert isinstance(simulation.bodies, BodyProvider)
        body_names = simulation.bodies.list_bodies()
        expected_calls = len([b for b in body_names if b != "Sun"])
        if "Sun" in body_names:
            expected_calls += 1

        with patch("src.simulation.resolve_absolute_position") as mock_resolve:
            mock_resolve.return_value = Vec2(100, 200)

            # First call: should trigger resolutions for all bodies in simulation.bodies
            state1 = simulation.get_system_state(t)
            first_call_count = mock_resolve.call_count
            assert first_call_count == expected_calls

            # Second call: should use simulation-level cache and NOT call resolve_absolute_position
            state2 = simulation.get_system_state(t)

            assert mock_resolve.call_count == first_call_count, (
                f"Expected {first_call_count} calls, but got {mock_resolve.call_count}. "
                "Simulation-level cache hit failed."
            )
            assert state1 == state2

    def test_cache_invalidation_ac2(self, simulation: Simulation) -> None:
        """Verify cache is invalidated when simulation time t changes (AC2)."""
        from src.bodies import BodyProvider

        assert isinstance(simulation.bodies, BodyProvider)
        body_names = simulation.bodies.list_bodies()
        expected_calls = len([b for b in body_names if b != "Sun"])
        if "Sun" in body_names:
            expected_calls += 1

        with patch("src.simulation.resolve_absolute_position") as mock_resolve:
            mock_resolve.return_value = Vec2(0, 0)

            # Call for t=1.0
            simulation.get_system_state(1.0)
            count_after_t1 = mock_resolve.call_count
            assert count_after_t1 == expected_calls

            # Call for t=2.0: should trigger new resolutions
            simulation.get_system_state(2.0)
            assert mock_resolve.call_count == count_after_t1 + expected_calls

    def test_cache_determinism(self, simulation: Simulation) -> None:
        """Verify caching/invalidation does not introduce state drift."""
        t1, t2 = 1.0, 2.0

        # Get baseline for t1
        state1_initial = simulation.get_system_state(t1)

        # Trigger invalidation with t2
        simulation.get_system_state(t2)

        # Get t1 again
        state1_final = simulation.get_system_state(t1)

        assert state1_initial == state1_final


class TestSimulationClock:
    """Tests for SimulationClock time progression and rate management."""

    def test_clock_initial_state(self):
        """Verify clock starts at t=0.0 with rate=1.0."""
        clock = SimulationClock()
        assert clock.get_time() == 0.0
        assert clock.rate == 1.0

    def test_clock_progression_positive_rate(self):
        """Verify clock advances by dt when rate is 1.0."""
        clock = SimulationClock(rate=1.0)
        clock.update(1.5)
        assert clock.get_time() == 1.5

    def test_clock_progression_negative_rate(self):
        """Verify clock retreats by 2*dt when rate is -2.0."""
        clock = SimulationClock(rate=-2.0)
        clock.update(1.0)
        assert clock.get_time() == -2.0

    def test_clock_progression_zero_rate(self):
        """Verify clock does not advance when rate is 0.0."""
        clock = SimulationClock(rate=0.0)
        clock.update(10.0)
        assert clock.get_time() == 0.0

    def test_clock_set_rate(self):
        """Verify set_rate updates the multiplier."""
        clock = SimulationClock()
        clock.set_rate(5.0)
        assert clock.rate == 5.0
        clock.update(1.0)
        assert clock.get_time() == 5.0


class TestSimulation:
    """Tests for Simulation state provider and determinism."""

    @pytest.fixture
    def simulation(self):
        """Provide a Simulation instance with a default clock and injected bodies."""
        clock = SimulationClock()
        return Simulation(clock=clock, bodies=BODIES)

    def test_get_system_state_returns_vec2_dict(self, simulation):
        """Verify get_system_state returns a dict of body names to Vec2."""
        state = simulation.get_system_state(0.0)
        assert isinstance(state, dict)
        body_names = simulation.bodies.list_bodies()
        for name in body_names:
            assert name in state
            assert isinstance(state[name], Vec2)
        # Sun should be in state if it's in the bodies registry
        if "Sun" in body_names:
            assert "Sun" in state
            assert isinstance(state["Sun"], Vec2)

    def test_state_retrieval_root(self, simulation):
        """Verify Sun (root) is always at (0, 0)."""
        state = simulation.get_system_state(123.45)
        if "Sun" in simulation.bodies.list_bodies():
            assert state["Sun"] == Vec2(0, 0)

    def test_state_retrieval_nested(self, simulation):
        """Verify nested body (Moon) position matches resolve_absolute_position."""
        t = 0.5
        state = simulation.get_system_state(t)
        # resolve_absolute_position now requires bodies and cache
        # We must include "Sun" in the bodies dict for resolution to work
        # Note: BODIES is now a provider, but resolve_absolute_position expects a provider.
        expected_moon_pos = resolve_absolute_position(
            "Moon", t, bodies=BODIES, cache={}
        )
        assert state["Moon"] == expected_moon_pos

    def test_simulation_dependency_injection(self):
        """Verify that Simulation only resolves bodies provided in its constructor."""
        from src.bodies import StaticBodyProvider

        clock = SimulationClock()
        custom_bodies_data = {
            "Mars": {
                "a": 1.523662,
                "e": 0.093412,
                "T": 1.8808476,
                "radius": 3390.0,
                "primary": "Sun",
                "color": (226, 110, 71),
            },
        }
        custom_bodies = StaticBodyProvider(custom_bodies_data)
        sim = Simulation(clock=clock, bodies=custom_bodies)
        state = sim.get_system_state(0.0)

        # Should only contain Mars (Sun is injected as virtual root but not in bodies)
        assert sorted(list(state.keys())) == ["Mars"]
        assert "Earth" not in state

    def test_simulation_determinism(self, simulation):
        """Verify repeated calls for the same t return identical results."""
        t = 100.0
        state1 = simulation.get_system_state(t)
        state2 = simulation.get_system_state(t)

        for name in state1:
            assert state1[name] == state2[name]

    def test_simulation_side_effect_free(self, simulation):
        """Verify state calculation does not modify injected bodies or Simulation state."""
        # Snapshot bodies count and clock time
        initial_bodies_count = len(simulation.bodies.list_bodies())
        initial_time = simulation.clock.get_time()

        simulation.get_system_state(10.0)

        assert len(simulation.bodies.list_bodies()) == initial_bodies_count
        assert simulation.clock.get_time() == initial_time

    def test_cache_integrity(self, simulation: Simulation) -> None:
        """Verify that mutating the returned state dict does not corrupt the cache.

        This test ensures that get_system_state returns a copy of the cached state,
        preventing external callers from accidentally modifying internal simulation data.
        """
        t = 5.0
        state = simulation.get_system_state(t)

        # Mutate the returned dictionary
        original_keys = list(state.keys())
        if original_keys:
            test_key = original_keys[0]
            original_val = state[test_key]
            state[test_key] = Vec2(999999, 999999)

            # Retrieve state again for the same t
            new_state = simulation.get_system_state(t)

            # Verification: The internal cache should remain unchanged
            assert (
                new_state[test_key] == original_val
            ), "Internal cache was corrupted by external mutation of returned dict."

    def test_get_future_path_accuracy(self, simulation: Simulation) -> None:
        """Verify that get_future_path returns points matching future system states (AC-2)."""
        t_start = 100.0
        duration = 50.0
        steps = 5
        dt = duration / steps

        path = simulation.get_future_path(
            body_name="Earth", t_start=t_start, duration=duration, steps=steps
        )

        assert len(path) == steps + 1
        for i, pos in enumerate(path):
            t_i = t_start + i * dt
            expected_state = simulation.get_system_state(t_i)
            assert pos == expected_state["Earth"]

    def test_get_future_path_invalid_steps(self, simulation: Simulation) -> None:
        """Verify that get_future_path raises ValueError for invalid steps (Robustness)."""
        with pytest.raises(ValueError, match="steps must be greater than 0"):
            simulation.get_future_path("Earth", 0, 100, 0)

        with pytest.raises(ValueError, match="steps must be greater than 0"):
            simulation.get_future_path("Earth", 0, 100, -1)

    def test_no_pygame_import(self) -> None:
        """Verify that src/simulation.py does not import pygame.

        Architectural requirement: Simulation logic must remain decoupled from the UI/Rendering library.
        """

        # Ensure pygame isn't already in sys.modules from other tests (though unlikely in this env)
        # We check the file content directly for the string 'pygame' as a more robust check.
        from pathlib import Path

        sim_path = Path("src/simulation.py")
        content = sim_path.read_text()

        assert (
            "pygame" not in content
        ), "src/simulation.py contains 'pygame' import or reference."


class TestSimulationClockPrecision:
    """Tests for SimulationClock precision and Decimal behavior."""

    def test_clock_decimal_precision(self) -> None:
        """Verify that SimulationClock avoids floating-point accumulation errors.

        Adding 0.1 one hundred times should equal exactly 10.0, which often fails
        with standard floats (e.g., 0.1 * 100 != 10.0 exactly).
        """
        clock = SimulationClock(rate=1.0)
        dt = 0.1
        steps = 100

        for _ in range(steps):
            clock.update(dt)

        # With Decimal, this should be exactly 10.0
        # float(10.0) is safe for comparison if the underlying Decimal is exactly 10
        assert clock.get_time() == 10.0

        # More rigorous check: 0.0001 * 10000
        clock.t_sim = 0.0
        dt = 0.0001
        steps = 10000
        for _ in range(steps):
            clock.update(dt)

        assert clock.get_time() == 1.0


class TestSimulationFuturePath:
    """Tests for deterministic future path calculation (AC-4)."""

    @pytest.fixture
    def simulation(self) -> Simulation:
        """Provide a Simulation instance with a default clock and injected bodies."""
        clock = SimulationClock()
        return Simulation(clock=clock, bodies=BODIES)

    def test_get_future_path_accuracy(self, simulation: Simulation) -> None:
        """Verify that get_future_path returns points matching future system states (AC-4)."""
        t_start = 100.0
        duration = 50.0
        steps = 5
        dt = duration / steps
        body_name = "Earth"

        # Calculate path using get_future_path
        path = simulation.get_future_path(
            body_name=body_name, t_start=t_start, duration=duration, steps=steps
        )

        assert len(path) == steps + 1

        # Verify each point matches get_system_state at the corresponding future time
        for i, pos in enumerate(path):
            t_future = t_start + (i * dt)
            state = simulation.get_system_state(t_future)
            assert pos == state[body_name], f"Mismatch at step {i}, time {t_future}"
