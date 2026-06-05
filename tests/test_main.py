"""Tests for the main entry point and global input handling.

These tests use mocks for Pygame display and event calls to remain
headless-compatible.
"""

import unittest.mock

import pygame
import pytest

from src.constants import WINDOW_SIZE
from src.simulation import SimulationClock
from src.main import handle_global_input, main


def test_main_loop_execution() -> None:
    """Test Case 1 & 4: Window Properties and Main Loop (AC-1, AC-4).

    Verifies window initialization and that the main loop records frames and ticks the clock.
    """
    from src.constants import FPS_CAP

    with unittest.mock.patch(
        "pygame.display.set_mode"
    ) as mock_set_mode, unittest.mock.patch(
        "pygame.display.set_caption"
    ) as mock_set_caption, unittest.mock.patch("pygame.init"), unittest.mock.patch(
        "pygame.event.get", return_value=[pygame.event.Event(pygame.QUIT)]
    ), unittest.mock.patch("src.main.SceneManager"), unittest.mock.patch(
        "src.main.TitleScene"
    ), unittest.mock.patch("src.main.Renderer"), unittest.mock.patch(
        "src.main.Diagnostics"
    ) as mock_diag_cls, unittest.mock.patch("src.main.Simulation"), unittest.mock.patch(
        "pygame.time.Clock"
    ) as mock_clock_cls, unittest.mock.patch(
        "pygame.display.flip"
    ), unittest.mock.patch("pygame.quit"), pytest.raises(SystemExit):
        mock_clock = mock_clock_cls.return_value
        mock_clock.tick.return_value = 16  # 16ms for ~60fps

        mock_diag = mock_diag_cls.return_value

        main()

        # AC-1
        mock_set_mode.assert_called_once_with(WINDOW_SIZE)
        mock_set_caption.assert_called_once_with("Favur Visual Test")

        # AC-4
        mock_clock.tick.assert_called_with(FPS_CAP)
        mock_diag.record_frame.assert_called()


def test_rate_clamping_plus() -> None:
    """Test Case 2: Rate Clamping - Upper Bound (AC-2)."""
    sim_clock = SimulationClock(rate=9500.0)
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PLUS})
    mock_manager = unittest.mock.Mock()

    # Increase until clamped
    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=mock_manager)
    assert sim_clock.rate == 10000.0

    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=mock_manager)
    assert sim_clock.rate == 10000.0


def test_rate_clamping_minus() -> None:
    """Test Case 2: Rate Clamping - Lower Bound (AC-2)."""
    sim_clock = SimulationClock(rate=0.105)
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_MINUS})
    mock_manager = unittest.mock.Mock()

    # Decrease until clamped
    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=mock_manager)
    assert sim_clock.rate == 0.1

    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=mock_manager)
    assert sim_clock.rate == 0.1


def test_graceful_shutdown_quit() -> None:
    """Test Case 3: Graceful Shutdown - QUIT (AC-3)."""
    event = pygame.event.Event(pygame.QUIT)
    mock_manager = unittest.mock.Mock()
    result = handle_global_input(
        event, SimulationClock(), unittest.mock.Mock(), manager=mock_manager
    )
    assert result is False


def test_graceful_shutdown_escape() -> None:
    """Test Case 3: Graceful Shutdown - ESCAPE (AC-3)."""
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    mock_manager = unittest.mock.Mock()
    result = handle_global_input(
        event, SimulationClock(), unittest.mock.Mock(), manager=mock_manager
    )
    assert result is False


def test_time_reversal() -> None:
    """Test Case 4: Time Reversal (AC-5).

    Verifies that SPACE inverts the clock direction only when in SimulationScene.
    """
    from src.scenes import SceneManager, SimulationScene

    sim_clock = SimulationClock(rate=1.0)
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})

    # Mock dependencies for SimulationScene
    mock_sim = unittest.mock.Mock()
    mock_sim.bodies.list_bodies.return_value = []
    mock_sim.bodies.get_groups.return_value = {}
    mock_renderer = unittest.mock.Mock()

    # Create a real SceneManager with a SimulationScene
    sim_scene = SimulationScene(mock_sim, mock_renderer)
    manager = SceneManager(sim_scene)

    # Test reversal in SimulationScene
    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=manager)
    assert sim_clock.rate == -1.0

    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=manager)
    assert sim_clock.rate == 1.0

    # Test no reversal in other scenes (e.g., TitleScene)
    from src.scenes import TitleScene

    title_scene = TitleScene(manager, mock_sim, mock_renderer)
    manager.transition_to(title_scene)

    sim_clock.rate = 1.0
    handle_global_input(event, sim_clock, unittest.mock.Mock(), manager=manager)
    assert sim_clock.rate == 1.0


def test_scene_manager_init_none() -> None:
    """Test that SceneManager can be initialized with None and handles it gracefully."""
    from src.scenes import SceneManager

    # This is expected to fail or raise type error until src/scenes.py is refactored
    manager = SceneManager(initial_scene=None)  # type: ignore[arg-type]
    assert manager.active_scene is None

    # Verify methods don't crash when active_scene is None
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    manager.handle_event(event)
    manager.update(0.1)
    manager.draw(pygame.Surface((10, 10)))
