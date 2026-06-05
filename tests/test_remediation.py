"""Verification tests for Sprint 6 remediation fixes.

This module contains tests for the robust initialization of SimulationScene
and a functional check of the simulation launch to verify the fixes for
the TypeError and cache optimization.
"""

from unittest.mock import MagicMock

from src.scenes import SimulationScene
from src.simulation import Simulation, SimulationClock
from src.bodies import StaticBodyProvider
from src.vector import Vec2


def test_asteroid_belt_initialization_robustness():
    """Verify that SimulationScene handles None values in body groups gracefully.

    This test targets the TypeError: 'NoneType' object is not iterable regression
    where groups.get("AsteroidBelt") returns None instead of an empty list.
    """
    # Mock Simulation and its bodies provider
    mock_sim = MagicMock(spec=Simulation)
    mock_bodies = MagicMock()
    mock_sim.bodies = mock_bodies

    # Mock bodies.get_groups to return the problematic None value
    mock_bodies.get_groups.return_value = {"AsteroidBelt": None}
    mock_bodies.list_bodies.return_value = []

    # Mock Renderer
    mock_renderer = MagicMock()

    # This should not raise TypeError after the fix.
    # In the current (buggy) state, it is expected to FAIL with TypeError.
    scene = SimulationScene(mock_sim, mock_renderer)
    assert isinstance(scene._asteroid_set, set)
    assert len(scene._asteroid_set) == 0


def test_simulation_launch():
    """Functional check of the simulation launch and state retrieval."""
    # Setup a minimal simulation with a single body
    clock = SimulationClock(rate=1.0)
    sun_data = {
        "primary": None,
        "a": 0.0,
        "e": 0.0,
        "T": 1.0,
        "radius": 695700.0,
        "color": (255, 255, 0),
    }
    bodies = StaticBodyProvider({"Sun": sun_data})
    sim = Simulation(clock, bodies)

    # Verify simulation can retrieve system state
    state = sim.get_system_state(0.0)

    assert "Sun" in state
    assert isinstance(state["Sun"], Vec2)
    # Sun at t=0 should be at origin in absolute coordinates
    assert state["Sun"].x == 0.0
    assert state["Sun"].y == 0.0
