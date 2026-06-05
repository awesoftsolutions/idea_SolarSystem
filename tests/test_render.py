"""Tests for the Renderer class in src/render.py.

These tests verify the rendering logic, coordinate mapping, and alpha decay
calculations using mocks for pygame and internal simulation components.
"""

import unittest.mock as mock
import pytest
from src.vector import Vec2
from src.frames import Frame

from src.render import Renderer


@pytest.fixture
def mock_pygame():
    """Mock pygame and its submodules."""
    with mock.patch("pygame.draw") as mock_draw, mock.patch(
        "pygame.gfxdraw"
    ) as mock_gfxdraw, mock.patch("pygame.Surface") as mock_surface:
        yield {"draw": mock_draw, "gfxdraw": mock_gfxdraw, "surface": mock_surface}


@pytest.fixture
def mock_simulation():
    """Mock the Simulation and its components."""
    sim = mock.MagicMock()
    sim.clock.t_sim = 100.0
    sim.bodies.get_body.return_value = {
        "name": "Earth",
        "color": (0, 0, 255),
        "radius": 6371.0,
        "primary": "Sun",
    }
    sim.get_system_state.return_value = {
        "Earth": Vec2(149600000.0, 0.0),
        "Sun": Vec2(0.0, 0.0),
    }
    return sim


@pytest.fixture
def mock_viewport():
    """Mock the Viewport."""
    return mock.MagicMock()


@pytest.fixture
def renderer(mock_simulation, mock_viewport):
    """Create a Renderer instance with mocked dependencies."""
    return Renderer(mock_simulation, mock_viewport)


def test_renderer_init(mock_simulation, mock_viewport):
    """Verify Renderer correctly stores injected instances."""
    r = Renderer(mock_simulation, mock_viewport)
    assert r.simulation == mock_simulation
    assert r.viewport == mock_viewport


def test_draw_body(renderer, mock_pygame, mock_simulation):
    """Verify draw_body calls scaling and pygame.draw.circle correctly."""
    surface = mock_pygame["surface"]

    with mock.patch("src.render.map_to_screen") as mock_map, mock.patch(
        "src.render.log_scale_size"
    ) as mock_scale_size:
        mock_map.return_value = Vec2(400, 300)
        mock_scale_size.return_value = 10.0

        renderer.draw_body(surface, "Earth")

        # Verify simulation state retrieval
        mock_simulation.get_system_state.assert_called_with(100.0)

        # Verify scaling calls
        mock_map.assert_called_once()
        args, _ = mock_map.call_args
        assert args[0] == Vec2(149600000.0, 0.0)  # Earth's pos
        assert isinstance(args[1], Frame)
        assert args[1].name == "Earth"
        assert args[1].t == 100.0

        # Verify drawing call
        mock_pygame["draw"].circle.assert_called_once_with(
            surface, (0, 0, 255), (400, 300), 10
        )


def test_draw_orbit_path_sun(renderer, mock_pygame, mock_simulation):
    """Verify draw_orbit_path returns early for the Sun."""
    surface = mock_pygame["surface"]
    mock_simulation.bodies.get_body.return_value = {"primary": None}

    renderer.draw_orbit_path(surface, "Sun")

    mock_pygame["gfxdraw"].aapolygon.assert_not_called()


def test_draw_orbit_path_body(renderer, mock_pygame, mock_simulation, mock_viewport):
    """Verify draw_orbit_path centers orbits on primaries and uses polygon approximation."""
    surface = mock_pygame["surface"]

    # Setup body and primary data
    mock_simulation.bodies.get_body.side_effect = lambda name: {
        "Earth": {"primary": "Sun", "color": (0, 0, 255)},
        "Sun": {"primary": None},
    }[name]

    with mock.patch("src.render.scale_orbit_geometry") as mock_geo, mock.patch(
        "src.render.map_to_world"
    ) as mock_map_world, mock.patch(
        "src.render.world_to_screen"
    ) as mock_world_to_screen:
        mock_geo.return_value = {
            "a_v": 100,
            "b_v": 80,
            "center_offset": Vec2(10, 0),
            "orientation": 0.5,
        }
        mock_map_world.return_value = Vec2(200, 200)  # Primary world pos
        mock_world_to_screen.return_value = Vec2(210, 200)

        renderer.draw_orbit_path(surface, "Earth")

        # Verify geometry scaling
        mock_geo.assert_called_once()

        # Verify primary position resolution
        mock_map_world.assert_called_once()
        args, _ = mock_map_world.call_args
        assert args[0] == Vec2(0.0, 0.0)  # Sun's pos
        assert args[1].name == "Sun"

        # Verify drawing calls (3-pass glow rendering)
        # Pass 1: lines (width 3)
        # Pass 2: lines (width 2)
        # Pass 3: aapolygon
        assert mock_pygame["draw"].lines.call_count == 2
        assert mock_pygame["gfxdraw"].aapolygon.call_count == 1

        # Verify adaptive sampling (approx 113 points for a=100, b=80)
        # circumference = 2 * pi * sqrt((100^2 + 80^2)/2) = 2 * pi * sqrt(8200) approx 569
        # num_points = max(64, min(1024, int(569 / 5.0))) = 113
        args_aa, _ = mock_pygame["gfxdraw"].aapolygon.call_args
        points_list = args_aa[1]
        assert len(points_list) == 113


def test_draw_trail(renderer, mock_pygame, mock_simulation):
    """Verify draw_trail renders fading segments correctly and optimizes mapping calls."""
    surface = mock_pygame["surface"]
    mock_trail = mock.MagicMock()
    # 3 points -> 2 segments
    points = [Vec2(0, 0), Vec2(10, 0), Vec2(20, 0)]
    mock_trail.get_points.return_value = points

    with mock.patch("src.render.map_to_screen") as mock_map:
        # map_to_screen should be called exactly once per point (3 times total)
        mock_map.side_effect = [
            Vec2(100, 100),
            Vec2(110, 100),
            Vec2(120, 100),
        ]

        renderer.draw_trail(surface, "Earth", mock_trail)

        # Verify mapping optimization
        assert mock_map.call_count == 3

        # Verify segment drawing
        assert mock_pygame["gfxdraw"].line.call_count == 2

        # Verify exponential alpha decay
        # alpha_min = 5.0, num_points = 3
        # Verify exponential alpha decay
        # alpha = 255 * exp(-k * distance_from_head)
        # Verify exponential alpha decay
        # alpha = 255 * exp(-k * distance_from_head)
        # k = ln(255/5) / (3-1) = ln(51) / 2 approx 1.965
        # Segment 0 (dist=1): alpha = 255 * exp(-1.965) approx 35
        # Segment 1 (dist=0): alpha = 255 * exp(0) = 255
        calls = mock_pygame["gfxdraw"].line.call_args_list

        # First segment (oldest)
        args0 = calls[0][0]
        assert abs(args0[5][3] - 35) <= 1

        # Second segment (newest)
        args1 = calls[1][0]
        assert args1[5][3] == 255


def test_draw_trail_empty(renderer, mock_pygame):
    """Verify draw_trail does nothing for empty or single-point trails."""
    surface = mock_pygame["surface"]
    mock_trail = mock.MagicMock()

    # Empty
    mock_trail.get_points.return_value = []
    renderer.draw_trail(surface, "Earth", mock_trail)
    mock_pygame["gfxdraw"].line.assert_not_called()

    # Single point
    mock_trail.get_points.return_value = [Vec2(0, 0)]
    renderer.draw_trail(surface, "Earth", mock_trail)
    mock_pygame["gfxdraw"].line.assert_not_called()
