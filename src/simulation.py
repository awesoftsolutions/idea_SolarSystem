# CHANGELOG:
# - Sprint 4: Implement core simulation engine with SimulationClock and Simulation state provider.
# - Sprint 4: Implement per-tick state caching and Decimal-based deterministic clock.
# - Sprint 5: Update for BodyProvider API.
# - Sprint 6: Implement predictive path projection (get_future_path) and optimize projection cache.
# - Sprint 7: Implement persistent hierarchical projection caching (DR-016).
# - Sprint 7 Remediation: Fix trail rendering smears and optimize path projection cache reuse.

from __future__ import annotations

import typing
from decimal import Decimal

from src.frames import resolve_absolute_position
from src.vector import Vec2

if typing.TYPE_CHECKING:
    from src.bodies import BodyProvider

"""Core simulation engine for time management and state retrieval.

This module provides the SimulationClock for managing simulation time
and the Simulation class for calculating the system state at any given time.
"""


class SimulationClock:
    """Manages simulation time based on real-world delta time and a rate.

    Uses Decimal internally to eliminate floating-point accumulation drift
    during long simulation runs or time-reversal operations.

    Attributes:
        t_sim: Current simulation time.
        rate: Time multiplier (default 1.0).
    """

    def __init__(self, rate: float = 1.0) -> None:
        """Initialize SimulationClock.

        Args:
            rate: The initial simulation rate.

        Returns:
            None
        """
        self._t_sim: Decimal = Decimal("0.0")
        self._rate: Decimal = Decimal(str(rate))

    @property
    def rate(self) -> float:
        """Return the current simulation rate as a float.

        Returns:
            The current simulation rate.
        """
        return float(self._rate)

    @rate.setter
    def rate(self, value: float) -> None:
        """Set the current simulation rate.

        Args:
            value: The new simulation rate.

        Returns:
            None
        """
        self._rate = Decimal(str(value))

    @property
    def t_sim(self) -> float:
        """Return the current simulation time as a float for compatibility.

        Returns:
            The current simulation time.
        """
        return float(self._t_sim)

    @t_sim.setter
    def t_sim(self, value: float) -> None:
        """Set the current simulation time.

        Args:
            value: The new simulation time.

        Returns:
            None
        """
        self._t_sim = Decimal(str(value))

    def update(self, dt: float) -> None:
        """Update simulation time by real-world delta time.

        Args:
            dt: Real elapsed time in seconds.

        Returns:
            None
        """
        # Convert to string first to ensure Decimal precision matches float representation
        self._t_sim += Decimal(str(dt)) * self._rate

    def set_rate(self, new_rate: float) -> None:
        """Set a new simulation rate.

        Args:
            new_rate: The new time multiplier.

        Returns:
            None
        """
        self.rate = new_rate

    def get_time(self) -> float:
        """Return the current simulation time.

        Returns:
            The current t_sim value.
        """
        return self.t_sim


class Simulation:
    """Provides the system state at any given simulation time.

    Attributes:
        clock: The SimulationClock instance associated with this simulation.
        bodies: Injected BodyProvider.
    """

    def __init__(self, clock: SimulationClock, bodies: BodyProvider) -> None:
        """Initialize Simulation with a clock and bodies.

        Args:
            clock: The SimulationClock instance to use.
            bodies: Injected BodyProvider.

        Returns:
            None
        """
        self.clock = clock
        self.bodies = bodies
        self._cache_t: float | None = None
        self._cache_state: dict[str, Vec2] | None = None

        # Persistent projection cache (DR-016)
        self._rel_pos_cache: dict[tuple[float, float, float, float], Vec2] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        # Persistent tick cache for optimization (AC-2)
        self._tick_cache: dict[str, Vec2] = {}

    def get_cache_metrics(self) -> dict[str, int | float]:
        """Return hit rate and raw metrics for the projection cache.

        Returns:
            A dictionary containing 'hits', 'misses', and 'hit_rate'.
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": hit_rate,
        }

    def get_system_state(self, t: float) -> dict[str, Vec2]:
        """Calculate the absolute positions of all bodies at time t.

        This method is deterministic and side-effect free. It uses a per-tick
        cache to optimize repeated calls for the same simulation time.

        Args:
            t: The simulation time at which to retrieve the state.

        Returns:
            A dictionary mapping body names to their absolute Vec2 positions in km.
            Returns a copy of the internal state to ensure cache integrity.
        """
        if self._cache_state is not None and self._cache_t == t:
            return self._cache_state.copy()

        def _record_cache_hit() -> None:
            self._cache_hits += 1

        def _record_cache_miss() -> None:
            self._cache_misses += 1

        # Reuse and clear persistent tick cache (AC-2)
        self._tick_cache.clear()

        # Resolve all bodies in the injected registry.
        # resolve_absolute_position handles its own recursion and internal cache filling.
        body_names = self.bodies.list_bodies()
        for body_name in body_names:
            if body_name not in self._tick_cache:
                resolve_absolute_position(
                    body_name,
                    t,
                    self.bodies,
                    self._tick_cache,
                    rel_pos_cache=self._rel_pos_cache,
                    on_cache_hit=_record_cache_hit,
                    on_cache_miss=_record_cache_miss,
                )

        # Filter the results to only include bodies present in the injected registry.
        # This ensures that if resolve_absolute_position injected 'Sun' as a base case
        # but 'Sun' wasn't in self.bodies, it won't be in the returned state.
        filtered_state = {
            name: self._tick_cache[name]
            for name in body_names
            if name in self._tick_cache
        }

        self._cache_t = t
        self._cache_state = filtered_state
        return filtered_state.copy()

    def get_future_path(
        self, body_name: str, t_start: float, duration: float, steps: int
    ) -> list[Vec2]:
        """Calculate a list of future positions for a specific body with caching.

        Args:
            body_name: The name of the body to project.
            t_start: The starting simulation time.
            duration: The time duration to project into the future.
            steps: The number of segments to calculate.

        Returns:
            A list of absolute Vec2 positions.

        Raises:
            ValueError: If steps is less than or equal to 0.
        """
        if steps <= 0:
            raise ValueError(f"steps must be greater than 0, got {steps}")

        dt = duration / steps
        path: list[Vec2] = []

        def _record_cache_hit() -> None:
            self._cache_hits += 1

        def _record_cache_miss() -> None:
            self._cache_misses += 1

        for i in range(steps + 1):
            # IMPLEMENTATION DECISION: Decimal precision for path projection.
            # Rationale: Matches SimulationClock's Decimal accumulation to prevent drift.
            t_future = float(Decimal(str(t_start)) + (Decimal(i) * Decimal(str(dt))))

            # Reuse and clear persistent tick cache (AC-2)
            self._tick_cache.clear()

            pos = resolve_absolute_position(
                body_name,
                t_future,
                self.bodies,
                self._tick_cache,
                rel_pos_cache=self._rel_pos_cache,
                on_cache_hit=_record_cache_hit,
                on_cache_miss=_record_cache_miss,
            )
            path.append(pos)

        return path
