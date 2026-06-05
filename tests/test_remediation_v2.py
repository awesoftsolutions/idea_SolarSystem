"""Verification suite for Sprint 7 remediation fixes.

This module contains tests for trail rendering frame consistency, simulation cache reuse,
and performance test logic alignment.
"""

from unittest.mock import MagicMock, patch

import pygame
import pytest

from src.constants import YEAR_TO_DAY
from src.frames import Frame
from src.render import Renderer
from src.simulation import Simulation, SimulationClock
from src.vector import Vec2


@pytest.fixture
def mock_bodies():
    """Provide a mock BodyProvider with a hierarchical system (Moon -> Earth -> Sun)."""
    provider = MagicMock()
    bodies_data = {
        "Sun": {"primary": None, "radius": 695700, "color": (255, 255, 0)},
        "Earth": {
            "a": 1.0,
            "e": 0.0167,
            "T": 1.0,
            "primary": "Sun",
            "radius": 6371,
            "color": (0, 0, 255),
        },
        "Moon": {
            "a": 0.00257,
            "e": 0.0549,
            "T": 0.0748,
            "primary": "Earth",
            "radius": 1737,
            "color": (200, 200, 200),
        },
    }
    provider.list_bodies.return_value = list(bodies_data.keys())
    provider.get_body.side_effect = lambda name: bodies_data.get(name)
    provider.__contains__.side_effect = lambda name: name in bodies_data
    return provider


def test_trail_frame_consistency(mock_bodies):
    """Verify that Renderer.draw_trail uses the primary body's frame context.

    AC-1: Trails must render correctly by using the primary body's frame context.
    """
    clock = SimulationClock()
    sim = Simulation(clock, mock_bodies)
    viewport = MagicMock()
    renderer = Renderer(sim, viewport)

    trail = MagicMock()
    trail.get_points.return_value = [Vec2(100, 100), Vec2(110, 110)]

    # Mock pygame.Surface for the surface argument
    surface = MagicMock(spec=pygame.Surface)

    # Mock map_to_screen to capture the frame_context passed to it
    with patch("src.render.map_to_screen") as mock_map, patch(
        "pygame.gfxdraw.line"
    ):
        mock_map.return_value = Vec2(50, 50)
        renderer.draw_trail(surface, "Moon", trail)

        # Verify map_to_screen was called
        assert mock_map.called

        # Check the frame context of the first call
        # The first argument to map_to_screen is the point, second is frame_context
        args, _ = mock_map.call_args
        frame_context = args[1]

        assert isinstance(frame_context, Frame)
        # For "Moon", the primary is "Earth". The fix should use "Earth" frame.
        assert (
            frame_context.name == "Earth"
        ), f"Expected frame 'Earth', got '{frame_context.name}'"


def test_simulation_cache_reuse(mock_bodies):
    """Verify that Simulation._tick_cache is reused but cleared between calls.

    AC-2: tick_cache initialization moved to Simulation.__init__ and reused.
    """
    clock = SimulationClock()
    sim = Simulation(clock, mock_bodies)

    # 1. Verify existence in __init__
    assert hasattr(
        sim, "_tick_cache"
    ), "Simulation should have a _tick_cache attribute"
    assert isinstance(sim._tick_cache, dict)

    initial_cache_id = id(sim._tick_cache)

    # 2. Verify reuse in get_system_state
    sim.get_system_state(0.0)
    assert id(sim._tick_cache) == initial_cache_id

    # 3. Verify reuse in get_future_path
    sim.get_future_path("Earth", 0.0, 1.0, 5)
    assert id(sim._tick_cache) == initial_cache_id

    # 4. Verify clearing (Logic check)
    # We mock resolve_absolute_position to check if the cache is empty when passed
    with patch("src.simulation.resolve_absolute_position") as mock_resolve:
        # We need to ensure resolve_absolute_position doesn't actually populate the cache
        # so we can verify it was empty upon entry.
        sim.get_system_state(10.0)

        # Inspect the 'cache' argument passed to resolve_absolute_position
        # It should be sim._tick_cache, and it should have been cleared before the call
        args, _ = mock_resolve.call_args
        passed_cache = args[3]  # cache is the 4th positional arg
        assert passed_cache is sim._tick_cache
        assert (
            len(passed_cache) == 0
        ), "Cache should be cleared before calling resolve_absolute_position"

    # 5. Verify clearing in get_future_path loop
    with patch("src.simulation.resolve_absolute_position") as mock_resolve:
        sim.get_future_path("Earth", 0.0, 1.0, 2)
        # Should be called 3 times (steps+1). Check each call had an empty cache.
        assert mock_resolve.call_count == 3
        for call in mock_resolve.call_args_list:
            passed_cache = call.args[3]
            assert len(passed_cache) == 0


def test_hit_rate_passing(mock_bodies):
    """Verify the fixed hit rate logic passes with > 90% hit rate.

    AC-3: test_persistent_cache_hit_rate must pass with > 90% hit rate.
    """
    clock = SimulationClock()
    sim = Simulation(clock, mock_bodies)

    # Use the fixed logic: t = i * YEAR_TO_DAY
    for i in range(20):
        t = float(i) * YEAR_TO_DAY
        sim.get_future_path("Earth", t, 1.0, 10)

    metrics = sim.get_cache_metrics()
    assert (
        metrics["hit_rate"] > 0.90
    ), f"Expected hit rate > 0.90, got {metrics['hit_rate']}"


def test_no_pygame_in_simulation():
    """Verify src.simulation does not import pygame.

    AC-4: No pygame imports allowed in src/simulation.py.
    """
    # Ensure src.simulation is loaded
    import src.simulation  # noqa: F401

    # Check if 'pygame' is in the module's globals
    import src.simulation as sim_mod

    assert "pygame" not in sim_mod.__dict__

    # Also check that it's not in the file content (simple grep-like check)
    with open("src/simulation.py", "r") as f:
        content = f.read()
        assert "import pygame" not in content
        assert "from pygame" not in content
