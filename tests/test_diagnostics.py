"""Unit tests for the Diagnostics class."""

from unittest.mock import MagicMock, patch

import pytest

from src.diagnostics import Diagnostics


@pytest.fixture
def diagnostics() -> Diagnostics:
    """Fixture to provide a fresh Diagnostics instance."""
    return Diagnostics()


def test_iteration_warning() -> None:
    """Verify solver warning is logged during the interval summary.

    Goal: Verify solver warning is logged during the interval summary.
    Setup: Mock logging.getLogger("solar.diagnostics").
    Execution:
        1. Call record_solver_iterations(11).
        2. Record frames until 1.0s accumulated.
    Verification: Assert logger.warning was called with "Solver convergence slow".
    """
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        diag = Diagnostics()
        diag.record_solver_iterations(11)

        # Should NOT log immediately
        assert mock_logger.warning.call_count == 0

        # Record frames until 1.0s accumulated
        diag.record_frame(0.5)
        diag.record_frame(0.5)

        # Verify warning was called during interval summary
        mock_logger.warning.assert_called()
        args, _ = mock_logger.warning.call_args
        assert "Solver convergence slow" in args[0]


def test_fps_calculation() -> None:
    """Verify accurate FPS calculation over a moving window.

    Goal: Verify accurate FPS calculation over a moving window.
    Execution:
        1. Call record_frame(0.01666) 60 times.
    Verification: Assert get_fps() returns a value between 59.0 and 61.0.
    """
    diag = Diagnostics()
    for _ in range(60):
        diag.record_frame(0.01666)

    fps = diag.get_fps()
    assert 59.0 <= fps <= 61.0


def test_overlay_toggle() -> None:
    """Verify toggle logic.

    Goal: Verify toggle logic.
    Execution:
        1. Check is_overlay_visible() (should be False).
        2. Call toggle_overlay().
        3. Check is_overlay_visible() (should be True).
    Verification: Assert states match expectations.
    """
    diag = Diagnostics()
    assert diag.is_overlay_visible() is False
    diag.toggle_overlay()
    assert diag.is_overlay_visible() is True
    diag.toggle_overlay()
    assert diag.is_overlay_visible() is False


def test_summary_report() -> None:
    """Verify summary dictionary structure.

    Goal: Verify summary dictionary structure.
    Execution:
        1. Record 1 frame and 1 solver iteration.
        2. Call get_summary().
    Verification: Assert keys fps, avg_solver_iterations, and overlay_active exist and have correct types.
    """
    diag = Diagnostics()
    diag.record_frame(0.016)
    diag.record_solver_iterations(5)

    summary = diag.get_summary()
    assert "fps" in summary
    assert "avg_solver_iterations" in summary
    assert "overlay_active" in summary

    assert isinstance(summary["fps"], (int, float))
    assert isinstance(summary["avg_solver_iterations"], (int, float))
    assert isinstance(summary["overlay_active"], bool)


def test_fps_interval_logging() -> None:
    """Verify that FPS and solver stats are logged at ~1.0s intervals.

    Goal: Verify FPS is logged at ~1s intervals.
    Execution:
        1. Record 10 frames of 0.1s each (total 1.0s).
    Verification: Assert logger.info was called with FPS info.
    """
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        diag = Diagnostics()
        # Record 9 frames of 0.1s (0.9s total) - should not log yet
        for _ in range(9):
            diag.record_frame(0.1)
        assert mock_logger.info.call_count == 0

        # Record 10th frame (1.0s total) - should log
        diag.record_frame(0.1)
        assert mock_logger.info.call_count == 1
        args, _ = mock_logger.info.call_args
        assert "Performance" in args[0]
        assert "10.0" in str(args)


def test_low_fps_warning() -> None:
    """Verify low FPS warning is logged during the interval summary.

    Goal: Verify low FPS warning is logged during the interval summary.
    Setup: Mock logging.getLogger("solar.diagnostics").
    Execution:
        1. Record frames at 20 FPS until 1.0s accumulated.
    Verification: Assert logger.warning was called with "Performance bottleneck".
    """
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        diag = Diagnostics()
        # 0.05s dt = 20 FPS. Record 19 frames (0.95s) - should NOT log yet
        for _ in range(19):
            diag.record_frame(0.05)

        assert mock_logger.warning.call_count == 0

        # Record 20th frame (1.0s total) - should log
        diag.record_frame(0.05)

        # Verify warning was called during interval summary
        mock_logger.warning.assert_called()
        args, _ = mock_logger.warning.call_args
        assert "Performance bottleneck detected" in args[0]
        assert "20.0" in str(args)
