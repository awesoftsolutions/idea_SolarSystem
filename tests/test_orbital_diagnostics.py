"""Integration tests for solver diagnostics."""

from unittest.mock import MagicMock

from src.orbital import solve_kepler


def test_solver_diagnostics_integration() -> None:
    """Ensure solve_kepler correctly triggers the callback.

    Goal: Ensure solve_kepler correctly triggers the callback.
    Setup: Create a mock callback function.
    Execution: Call solve_kepler(0.1, 0.05, iteration_callback=mock_callback).
    Verification: Assert mock_callback was called with an integer > 0.
    """
    mock_callback = MagicMock()

    # solve_kepler signature updated to accept iteration_callback.
    solve_kepler(0.1, 0.05, iteration_callback=mock_callback)

    assert mock_callback.called
    args, _ = mock_callback.call_args
    assert isinstance(args[0], int)
    assert args[0] > 0
