"""Tests for the Scene Management & UI State Machine.

These tests verify the SceneManager FSM logic, TitleScene transitions,
and SimulationScene behavior (pause toggle, renderer dispatch).
"""

import unittest.mock as mock
import pytest
import pygame

from src.scenes import SceneManager, TitleScene, SimulationScene, Scene
from src.vector import Vec2


@pytest.fixture
def mock_pygame():
    """Mock pygame and its submodules."""
    with mock.patch("pygame.draw") as mock_draw, \
         mock.patch("pygame.Surface") as mock_surface, \
         mock.patch("pygame.font.SysFont") as mock_font, \
         mock.patch("pygame.font.init") as mock_font_init:
        
        # Mock font.render to return a mock surface
        mock_font_instance = mock.MagicMock()
        mock_font.return_value = mock_font_instance
        mock_font_instance.render.return_value = mock.MagicMock()

        # Mock gfxdraw separately since it's a C extension and might not be in all pygame builds
        mock_gfxdraw = mock.MagicMock()
        with mock.patch("pygame.gfxdraw", mock_gfxdraw, create=True):
            yield {
                "draw": mock_draw,
                "gfxdraw": mock_gfxdraw,
                "surface": mock_surface,
                "font": mock_font
            }


@pytest.fixture
def mock_simulation():
    """Mock the Simulation and its components."""
    sim = mock.MagicMock()
    sim.clock.t_sim = 100.0
    sim.clock.rate = 1.0
    sim.clock.get_time.return_value = 100.0
    sim.bodies.list_bodies.return_value = ["Sun", "Earth"]
    return sim


@pytest.fixture
def mock_renderer():
    """Mock the Renderer."""
    return mock.MagicMock()


class TestSceneManager:
    """Unit tests for SceneManager FSM core logic."""

    def test_initial_state(self):
        """Verify manager.active_scene is set to the initial scene."""
        initial_scene = mock.MagicMock(spec=Scene)
        manager = SceneManager(initial_scene)
        assert manager.active_scene == initial_scene

    def test_transition(self):
        """Verify manager.transition_to updates the active scene."""
        initial_scene = mock.MagicMock(spec=Scene)
        new_scene = mock.MagicMock(spec=Scene)
        manager = SceneManager(initial_scene)
        manager.transition_to(new_scene)
        assert manager.active_scene == new_scene

    def test_event_dispatch(self):
        """Verify manager.handle_event calls active_scene.handle_event."""
        active_scene = mock.MagicMock(spec=Scene)
        manager = SceneManager(active_scene)
        event = mock.MagicMock(spec=pygame.event.Event)
        manager.handle_event(event)
        active_scene.handle_event.assert_called_once_with(event)

    def test_update_dispatch(self):
        """Verify manager.update calls active_scene.update."""
        active_scene = mock.MagicMock(spec=Scene)
        manager = SceneManager(active_scene)
        manager.update(0.016)
        active_scene.update.assert_called_once_with(0.016)

    def test_draw_dispatch(self):
        """Verify manager.draw calls active_scene.draw."""
        active_scene = mock.MagicMock(spec=Scene)
        manager = SceneManager(active_scene)
        surface = mock.MagicMock(spec=pygame.Surface)
        manager.draw(surface)
        active_scene.draw.assert_called_once_with(surface)


class TestTitleScene:
    """Functional tests for TitleScene behavior."""

    def test_space_transition(self, mock_simulation, mock_renderer):
        """Verify SPACE transition to SimulationScene (AC 1)."""
        initial_scene = TitleScene()
        manager = SceneManager(initial_scene)
        initial_scene.manager = manager

        # Inject dependencies for the test
        initial_scene.simulation = mock_simulation
        initial_scene.renderer = mock_renderer

        # Mock event
        event = mock.MagicMock(spec=pygame.event.Event)
        event.type = pygame.KEYDOWN
        event.key = pygame.K_SPACE

        with mock.patch("src.scenes.SimulationScene") as MockSimScene:
            mock_sim_instance = mock.MagicMock(spec=SimulationScene)
            MockSimScene.return_value = mock_sim_instance

            initial_scene.handle_event(event)

            assert manager.active_scene == mock_sim_instance

    def test_ignore_other_keys(self):
        """Verify TitleScene ignores non-SPACE keys."""
        initial_scene = TitleScene()
        manager = SceneManager(initial_scene)
        initial_scene.manager = manager
        
        event = mock.MagicMock(spec=pygame.event.Event)
        event.type = pygame.KEYDOWN
        event.key = pygame.K_ESCAPE

        initial_scene.handle_event(event)
        assert manager.active_scene == initial_scene


class TestSimulationScene:
    """Functional tests for SimulationScene behavior."""

    def test_pause_toggle(self, mock_simulation, mock_renderer):
        """Verify pause toggle on 'P' (AC 2)."""
        sim_scene = SimulationScene(mock_simulation, mock_renderer)
        assert sim_scene.is_paused is False

        event = mock.MagicMock(spec=pygame.event.Event)
        event.type = pygame.KEYDOWN
        event.key = pygame.K_p

        sim_scene.handle_event(event)
        assert sim_scene.is_paused is True

        sim_scene.handle_event(event)
        assert sim_scene.is_paused is False

    def test_pause_effect_on_update(self, mock_simulation, mock_renderer):
        """Verify pause effect on simulation clock update."""
        sim_scene = SimulationScene(mock_simulation, mock_renderer)
        
        # Not paused
        sim_scene.is_paused = False
        sim_scene.update(0.016)
        mock_simulation.clock.update.assert_called_once_with(0.016)
        
        mock_simulation.clock.update.reset_mock()
        
        # Paused
        sim_scene.is_paused = True
        sim_scene.update(0.016)
        mock_simulation.clock.update.assert_not_called()

    def test_renderer_dispatch(self, mock_simulation, mock_renderer, mock_pygame):
        """Verify renderer dispatch for bodies and orbits (AC 3)."""
        sim_scene = SimulationScene(mock_simulation, mock_renderer)
        surface = mock_pygame["surface"]
        
        sim_scene.draw(surface)
        
        # Verify calls for 'Sun' and 'Earth'
        assert mock_renderer.draw_orbit_path.call_count == 2
        assert mock_renderer.draw_body.call_count == 2
        assert mock_renderer.draw_trail.call_count == 2
        
        mock_renderer.draw_orbit_path.assert_any_call(surface, "Sun")
        mock_renderer.draw_orbit_path.assert_any_call(surface, "Earth")
        mock_renderer.draw_body.assert_any_call(surface, "Sun")
        mock_renderer.draw_body.assert_any_call(surface, "Earth")
        
        # Verify draw_trail is called with a Trail instance
        mock_renderer.draw_trail.assert_any_call(surface, "Sun", mock.ANY)
        mock_renderer.draw_trail.assert_any_call(surface, "Earth", mock.ANY)

    def test_trail_update(self, mock_simulation, mock_renderer):
        """Verify SimulationScene.update appends positions to trails."""
        # Mock system state
        pos_sun = Vec2(0, 0)
        pos_earth = Vec2(100, 0)
        mock_simulation.get_system_state.return_value = {
            "Sun": pos_sun,
            "Earth": pos_earth
        }

        sim_scene = SimulationScene(mock_simulation, mock_renderer)

        # Initial update to trigger trail recording
        sim_scene.update(0.016)

        # Verify that trails were updated by checking internal state
        assert "Sun" in sim_scene._trails
        assert "Earth" in sim_scene._trails
        assert sim_scene._trails["Sun"].get_points() == [pos_sun]
        assert sim_scene._trails["Earth"].get_points() == [pos_earth]

        # Verify that the simulation state was requested.
        mock_simulation.get_system_state.assert_called_with(
            mock_simulation.clock.t_sim
        )