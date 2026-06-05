"""Tests for Predictive Orbit Previews.

These tests verify the deterministic future path calculation in Simulation,
the UI toggle logic in SimulationScene, and the renderer dispatch.
"""

import unittest.mock as mock
import pytest
import pygame

from src.scenes import SimulationScene
from src.simulation import Simulation
from src.vector import Vec2


@pytest.fixture
def mock_pygame():
    """Mock pygame and its submodules for headless testing."""
    with mock.patch("pygame.draw") as mock_draw, mock.patch(
        "pygame.Surface"
    ) as mock_surface, mock.patch("pygame.font.SysFont") as mock_font, mock.patch(
        "pygame.font.init"
    ):
        # Mock font.render to return a mock surface
        mock_font_instance = mock.MagicMock()
        mock_font.return_value = mock_font_instance
        mock_font_instance.render.return_value = mock.MagicMock()

        mock_gfxdraw = mock.MagicMock()
        with mock.patch("pygame.gfxdraw", mock_gfxdraw, create=True):
            yield {
                "draw": mock_draw,
                "gfxdraw": mock_gfxdraw,
                "surface": mock_surface,
                "font": mock_font,
            }


@pytest.fixture
def mock_simulation():
    """Mock the Simulation and its components."""
    sim = mock.MagicMock()
    sim.clock.t_sim = 100.0
    sim.clock.rate = 1.0
    sim.clock.get_time.return_value = 100.0
    sim.bodies.list_bodies.return_value = ["Sun", "Earth"]
    # Ensure get_body returns data with 'T' for Earth
    sim.bodies.get_body.side_effect = lambda name: (
        {"T": 365.0, "color": (0, 255, 0)}
        if name == "Earth"
        else {"color": (255, 255, 0)}
    )
    return sim


@pytest.fixture
def mock_renderer():
    """Mock the Renderer."""
    return mock.MagicMock()


def test_get_future_path_accuracy():
    """Verify that get_future_path returns points matching future system states (AC-4)."""
    mock_clock = mock.MagicMock()
    mock_bodies = mock.MagicMock()
    mock_bodies.list_bodies.return_value = ["Earth"]

    sim = Simulation(mock_clock, mock_bodies)

    t_start = 100.0
    duration = 50.0
    steps = 5
    dt = duration / steps

    # Mock resolve_absolute_position to return predictable values
    with mock.patch("src.simulation.resolve_absolute_position") as mock_resolve:
        # resolve_absolute_position(body_name, t, bodies, cache, **kwargs)
        mock_resolve.side_effect = lambda name, t, bodies, cache, **kwargs: Vec2(t, t)

        path = sim.get_future_path(
            body_name="Earth", t_start=t_start, duration=duration, steps=steps
        )

        assert len(path) == steps + 1
        for i, pos in enumerate(path):
            t_i = t_start + i * dt
            assert pos == Vec2(t_i, t_i)


def test_predictive_preview_toggle(mock_simulation, mock_renderer):
    """Verify that 'F' key toggles show_predictions in SimulationScene (AC-3)."""
    # This test might fail with AttributeError if show_predictions is not in __init__ yet.
    scene = SimulationScene(mock_simulation, mock_renderer)

    # Initial state should be False
    assert hasattr(
        scene, "show_predictions"
    ), "SimulationScene should have show_predictions attribute"
    assert scene.show_predictions is False

    # Simulate 'F' key press
    event = mock.MagicMock(spec=pygame.event.Event)
    event.type = pygame.KEYDOWN
    event.key = pygame.K_f

    scene.handle_event(event)
    assert scene.show_predictions is True

    # Toggle back
    scene.handle_event(event)
    assert scene.show_predictions is False


def test_draw_predictive_trail_calls(mock_simulation, mock_renderer, mock_pygame):
    """Verify renderer.draw_predictive_trail is called when enabled (AC-2, AC-3)."""
    # Ensure both Sun and Earth have 'T' for this test
    mock_simulation.bodies.get_body.side_effect = lambda name: {
        "T": 365.0,
        "color": (255, 255, 255),
    }

    scene = SimulationScene(mock_simulation, mock_renderer)
    surface = mock_pygame["surface"]

    # Mock get_future_path to return a dummy path
    mock_simulation.get_future_path.return_value = [Vec2(0, 0), Vec2(1, 1)]

    # 1. Disabled state
    scene.show_predictions = False
    scene.draw(surface)
    assert mock_renderer.draw_predictive_trail.call_count == 0

    # 2. Enabled state
    scene.show_predictions = True
    scene.update(0.1)
    scene.draw(surface)

    # Should be called for each body (Sun, Earth)
    assert mock_renderer.draw_predictive_trail.call_count == 2
    mock_renderer.draw_predictive_trail.assert_any_call(surface, "Sun", mock.ANY)
    mock_renderer.draw_predictive_trail.assert_any_call(surface, "Earth", mock.ANY)


def test_predictive_duration_calculation(mock_simulation, mock_renderer, mock_pygame):
    """Verify that SimulationScene.draw passes duration=period * 0.25 to get_future_path (AC-1)."""
    # Fix the side_effect from mock_simulation fixture to return 400.0 for this test
    mock_simulation.bodies.get_body.side_effect = None
    mock_simulation.bodies.get_body.return_value = {
        "T": 400.0,
        "radius": 1000.0,
        "color": (255, 255, 255),
    }

    scene = SimulationScene(mock_simulation, mock_renderer)
    surface = mock_pygame["surface"]
    scene.show_predictions = True

    scene.update(0.1)
    scene.draw(surface)

    # Verify get_future_path was called with duration = 400.0 * 0.25 = 100.0
    mock_simulation.get_future_path.assert_any_call(
        mock.ANY, mock.ANY, duration=100.0, steps=20
    )


def test_asteroid_exclusion(mock_simulation, mock_renderer, mock_pygame):
    """Verify that SimulationScene.draw skips bodies in the 'AsteroidBelt' group (LOD)."""
    # Ensure all bodies have 'T'
    mock_simulation.bodies.get_body.side_effect = lambda name: {
        "T": 365.0,
        "color": (255, 255, 255),
    }

    scene = SimulationScene(mock_simulation, mock_renderer)
    surface = mock_pygame["surface"]
    scene.show_predictions = True

    # Setup bodies: Sun, Earth (Major), Ceres (Asteroid)
    mock_simulation.bodies.list_bodies.return_value = ["Sun", "Earth", "Ceres"]
    mock_simulation.bodies.get_groups.return_value = {"AsteroidBelt": ["Ceres"]}
    # Re-init scene to pick up new asteroid set
    scene = SimulationScene(mock_simulation, mock_renderer)
    scene.show_predictions = True

    # Reset mock to clear calls from __init__ or previous setup
    mock_renderer.draw_predictive_trail.reset_mock()

    scene.update(0.1)
    scene.draw(surface)

    # Should be called for Sun and Earth, but NOT Ceres
    assert mock_renderer.draw_predictive_trail.call_count == 2

    # Get all calls to draw_predictive_trail
    called_bodies = [
        call.args[1] for call in mock_renderer.draw_predictive_trail.call_args_list
    ]
    assert "Sun" in called_bodies
    assert "Earth" in called_bodies
    assert "Ceres" not in called_bodies


def test_predictive_path_caching(mock_simulation, mock_renderer, mock_pygame):
    """Verify that predictive paths are calculated in update() and cached (Performance)."""
    scene = SimulationScene(mock_simulation, mock_renderer)
    surface = mock_pygame["surface"]
    scene.show_predictions = True

    # 1. First update: should calculate paths
    scene.update(0.1)
    initial_call_count = mock_simulation.get_future_path.call_count
    assert initial_call_count > 0

    # 2. Draw: should NOT calculate paths
    scene.draw(surface)
    assert mock_simulation.get_future_path.call_count == initial_call_count

    # 3. Second update with same t: should NOT recalculate
    scene.update(0.0)
    assert mock_simulation.get_future_path.call_count == initial_call_count

    # 4. Third update with new t: should recalculate
    mock_simulation.clock.t_sim = 100.1
    scene.update(0.1)
    assert mock_simulation.get_future_path.call_count > initial_call_count


def test_missing_orbital_period(mock_simulation, mock_renderer, mock_pygame):
    """Verify that bodies without orbital period 'T' are skipped (Robustness)."""
    scene = SimulationScene(mock_simulation, mock_renderer)
    surface = mock_pygame["surface"]
    scene.show_predictions = True

    # Earth has T, Sun does not (in this mock setup)
    mock_simulation.bodies.get_body.side_effect = lambda name: (
        {"T": 365.0, "color": (0, 255, 0)}
        if name == "Earth"
        else {"color": (255, 255, 0)}
    )

    scene.update(0.1)
    scene.draw(surface)

    # Should only be called for Earth
    called_bodies = [
        call.args[1] for call in mock_renderer.draw_predictive_trail.call_args_list
    ]
    assert "Earth" in called_bodies
    assert "Sun" not in called_bodies


def test_asteroid_set_caching(mock_simulation, mock_renderer):
    """Verify that asteroid_set is cached in __init__ and not recreated in draw (Performance)."""
    mock_simulation.bodies.get_groups.return_value = {"AsteroidBelt": ["Ceres"]}
    scene = SimulationScene(mock_simulation, mock_renderer)

    assert hasattr(scene, "_asteroid_set")
    assert "Ceres" in scene._asteroid_set

    # Reset mock to see if draw calls get_groups
    mock_simulation.bodies.get_groups.reset_mock()
    scene.draw(mock.MagicMock())
    assert mock_simulation.bodies.get_groups.call_count == 0
