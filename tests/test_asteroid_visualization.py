import unittest.mock as mock
import pytest
import pygame

# Initialize pygame for headless testing
pygame.init()
pygame.font.init()

from src.render import Renderer  # noqa: E402
from src.scenes import SimulationScene  # noqa: E402
from src.viewport import Viewport  # noqa: E402
from src.simulation import Simulation  # noqa: E402
from src.vector import Vec2  # noqa: E402


@pytest.fixture
def mock_simulation():
    sim = mock.MagicMock(spec=Simulation)
    # Explicitly mock clock to avoid spec issues
    sim.clock = mock.MagicMock()
    sim.clock.t_sim = 100.0
    sim.clock.get_time.return_value = 100.0
    sim.clock.rate = 1.0
    sim.get_system_state.return_value = {
        f"Ast-{i:04d}": Vec2(i, i) for i in range(1000)
    }

    # Setup bodies provider
    bodies = mock.MagicMock()
    bodies.get_groups.return_value = {
        "AsteroidBelt": [f"Ast-{i:04d}" for i in range(1000)]
    }
    bodies.get_body.return_value = {"radius": 1000.0, "color": (200, 200, 200)}
    bodies.list_bodies.return_value = [f"Ast-{i:04d}" for i in range(1000)] + [
        "Sun",
        "Earth",
    ]
    sim.bodies = bodies

    return sim


@pytest.fixture
def mock_viewport():
    vp = mock.MagicMock(spec=Viewport)
    vp.zoom = 1.0
    return vp


class TestRendererAsteroids:
    def test_sprite_caching(self, mock_simulation, mock_viewport):
        renderer = Renderer(mock_simulation, mock_viewport)
        color = (255, 0, 0)
        radius = 5

        # Identity check
        sprite1 = renderer._get_asteroid_sprite(color, radius)
        sprite2 = renderer._get_asteroid_sprite(color, radius)
        assert sprite1 is sprite2

        # Different parameters
        sprite3 = renderer._get_asteroid_sprite((0, 255, 0), radius)
        assert sprite1 is not sprite3


class TestAsteroidLOD:
    @mock.patch("src.render.map_to_screen")
    @mock.patch("src.render.log_scale_size")
    def test_trail_lod_threshold_low(
        self, mock_log_scale, mock_map, mock_simulation, mock_viewport
    ):
        mock_viewport.zoom = 2.0
        renderer = Renderer(mock_simulation, mock_viewport)
        renderer.draw_trail = mock.MagicMock()

        surface = mock.MagicMock(spec=pygame.Surface)
        trails = {f"Ast-{i:04d}": mock.MagicMock() for i in range(1000)}

        renderer.draw_asteroid_belt(surface, trails)

        # draw_trail should NOT be called for asteroids at zoom <= 2.0
        assert renderer.draw_trail.call_count == 0

    @mock.patch("src.render.map_to_screen")
    @mock.patch("src.render.log_scale_size")
    def test_trail_lod_threshold_high(
        self, mock_log_scale, mock_map, mock_simulation, mock_viewport
    ):
        mock_viewport.zoom = 2.1
        renderer = Renderer(mock_simulation, mock_viewport)
        renderer.draw_trail = mock.MagicMock()

        surface = mock.MagicMock(spec=pygame.Surface)
        trails = {f"Ast-{i:04d}": mock.MagicMock() for i in range(1000)}

        renderer.draw_asteroid_belt(surface, trails)

        # draw_trail SHOULD be called for asteroids at zoom > 2.0
        assert renderer.draw_trail.call_count == 1000


class TestAsteroidBatching:
    @mock.patch("src.render.map_to_screen")
    @mock.patch("src.render.log_scale_size")
    def test_batch_blits_called(
        self, mock_log_scale, mock_map, mock_simulation, mock_viewport
    ):
        renderer = Renderer(mock_simulation, mock_viewport)
        surface = mock.MagicMock(spec=pygame.Surface)
        mock_map.return_value = Vec2(100, 100)
        mock_log_scale.return_value = 2.0

        renderer.draw_asteroid_belt(surface, {})

        # Verify blits is called exactly once
        assert surface.blits.call_count == 1
        # Verify it contains 1000 asteroids
        args, kwargs = surface.blits.call_args
        assert len(args[0]) == 1000


class TestSceneIntegration:
    def test_simulation_scene_calls_belt_renderer(self, mock_simulation):
        renderer = mock.MagicMock(spec=Renderer)
        scene = SimulationScene(mock_simulation, renderer)
        surface = mock.MagicMock(spec=pygame.Surface)

        scene.draw(surface)

        # Verify draw_asteroid_belt is called
        renderer.draw_asteroid_belt.assert_called_once()

        # Verify draw_body is NOT called for asteroids (only for Sun and Earth)
        # Total bodies = 1000 asteroids + Sun + Earth = 1002
        # draw_body should be called 2 times
        assert renderer.draw_body.call_count == 2
