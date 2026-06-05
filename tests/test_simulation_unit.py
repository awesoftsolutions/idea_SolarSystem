"""Unit tests for the core simulation engine.

These tests cover the SimulationClock for time management and the Simulation
class for deterministic, side-effect-free state retrieval.
"""

import pytest

from src.vector import Vec2
from src.bodies import BODIES
from src.frames import resolve_absolute_position

from src.simulation import Simulation, SimulationClock


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
        """Provide a Simulation instance with a default clock."""
        clock = SimulationClock()
        return Simulation(clock=clock)

    def test_get_system_state_returns_vec2_dict(self, simulation):
        """Verify get_system_state returns a dict of body names to Vec2."""
        state = simulation.get_system_state(0.0)
        assert isinstance(state, dict)
        for name in BODIES:
            assert name in state
            assert isinstance(state[name], Vec2)

    def test_state_retrieval_root(self, simulation):
        """Verify Sun (root) is always at (0, 0)."""
        state = simulation.get_system_state(123.45)
        assert state["Sun"] == Vec2(0, 0)

    def test_state_retrieval_nested(self, simulation):
        """Verify nested body (Moon) position matches resolve_absolute_position."""
        t = 0.5
        state = simulation.get_system_state(t)
        expected_moon_pos = resolve_absolute_position("Moon", t)
        assert state["Moon"] == expected_moon_pos

    def test_simulation_determinism(self, simulation):
        """Verify repeated calls for the same t return identical results."""
        t = 100.0
        state1 = simulation.get_system_state(t)
        state2 = simulation.get_system_state(t)
        
        for name in BODIES:
            assert state1[name] == state2[name]

    def test_simulation_side_effect_free(self, simulation):
        """Verify state calculation does not modify BODIES or Simulation state."""
        # Snapshot BODIES count and clock time
        initial_bodies_count = len(BODIES)
        initial_time = simulation.clock.get_time()
        
        simulation.get_system_state(10.0)
        
        assert len(BODIES) == initial_bodies_count
        assert simulation.clock.get_time() == initial_time
