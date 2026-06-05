# CHANGELOG:
# - Sprint 5: Implement Diagnostics class for performance and solver monitoring.

"""Diagnostic infrastructure for solver convergence and performance monitoring."""

import logging
from typing import Any

from src.constants import DIAGNOSTICS_WINDOW


class Diagnostics:
    """Manages simulation health and performance data.

    Tracks frame times for FPS calculation and solver iterations for convergence monitoring.
    Provides a mechanism to toggle diagnostic overlays.
    """

    def __init__(self) -> None:
        """Initialize the diagnostics aggregator."""
        self._frame_times: list[float] = []
        self._max_window: int = DIAGNOSTICS_WINDOW
        self._solver_iterations: list[int] = []
        self._overlay_visible: bool = False
        self._logger = logging.getLogger("solar.diagnostics")
        self._accumulated_time: float = 0.0
        self._slow_convergence_count: int = 0
        self._max_iterations_in_interval: int = 0
        self._low_fps_detected: bool = False

    def record_frame(self, dt: float) -> None:
        """Record a frame's delta time.

        Tracks accumulated time for interval logging and checks for performance bottlenecks.

        Args:
            dt: Time elapsed since the last frame in seconds.
        """
        self._frame_times.append(dt)
        if len(self._frame_times) > self._max_window:
            self._frame_times.pop(0)

        self._accumulated_time += dt
        current_fps = self.get_fps()

        # Track low FPS for interval logging
        if 0 < current_fps < 30.0:
            self._low_fps_detected = True

        # Interval logging
        if self._accumulated_time >= 0.999:
            # Log warnings first
            if self._low_fps_detected:
                self._logger.warning("Performance bottleneck detected: %.1f FPS", current_fps)

            if self._slow_convergence_count > 0:
                self._logger.warning(
                    "Solver convergence slow for %d bodies. Max iterations: %d",
                    self._slow_convergence_count,
                    self._max_iterations_in_interval,
                )

            # Log info
            self._logger.info(
                "Performance: %.1f FPS, Avg Solver Iterations: %.1f",
                current_fps,
                self._get_avg_solver(),
            )

            # Reset interval metrics
            self._accumulated_time = 0.0
            self._slow_convergence_count = 0
            self._max_iterations_in_interval = 0
            self._low_fps_detected = False

    def record_solver_iterations(self, count: int) -> None:
        """Record the number of iterations taken by the solver.

        Tracks slow convergence for interval logging.

        Args:
            count: Number of iterations.
        """
        self._solver_iterations.append(count)
        if count > 10:
            self._slow_convergence_count += 1
            if count > self._max_iterations_in_interval:
                self._max_iterations_in_interval = count

        if len(self._solver_iterations) > self._max_window:
            self._solver_iterations.pop(0)

    def _get_avg_solver(self) -> float:
        """Calculate the average solver iterations over the moving window.

        Returns:
            Average solver iterations.
        """
        if not self._solver_iterations:
            return 0.0
        return sum(self._solver_iterations) / len(self._solver_iterations)

    def get_fps(self) -> float:
        """Calculate the average FPS over the moving window.

        Returns:
            Average frames per second.
        """
        if not self._frame_times:
            return 0.0

        avg_dt = sum(self._frame_times) / len(self._frame_times)
        if avg_dt > 0:
            return 1.0 / avg_dt
        return 0.0

    def toggle_overlay(self) -> None:
        """Toggle the visibility of the diagnostic overlay."""
        self._overlay_visible = not self._overlay_visible

    def is_overlay_visible(self) -> bool:
        """Check if the diagnostic overlay should be visible.

        Returns:
            True if visible, False otherwise.
        """
        return self._overlay_visible

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of current diagnostic metrics.

        Returns:
            Dictionary containing 'fps' (float), 'avg_solver_iterations' (float), and 'overlay_active' (bool).
        """
        return {
            "fps": self.get_fps(),
            "avg_solver_iterations": self._get_avg_solver(),
            "overlay_active": self._overlay_visible,
        }