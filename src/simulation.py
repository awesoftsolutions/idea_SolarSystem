# CHANGELOG:
# - Sprint 4: Implement core simulation engine with SimulationClock and Simulation state provider.
# - Sprint 4: Implement per-tick state caching and Decimal-based deterministic clock.

"""Core simulation engine for time management and state retrieval.

This module provides the SimulationClock for managing simulation time
and the Simulation class for calculating the system state at any given time.
"""

from typing import Any
from decimal import Decimal
from src.vector import Vec2
from src.frames import resolve_absolute_position


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
        bodies: Injected dictionary of body data.
    """

    def __init__(self, clock: SimulationClock, bodies: dict[str, Any]) -> None:
        """Initialize Simulation with a clock and bodies.

        Args:
            clock: The SimulationClock instance to use.
            bodies: Injected dictionary of body data.

        Returns:
            None
        """
        self.clock = clock
        self.bodies = bodies
        self._cache_t: float | None = None
        self._cache_state: dict[str, Vec2] | None = None

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

        tick_cache: dict[str, Vec2] = {}

        # Resolve all bodies in the injected registry.
        # resolve_absolute_position handles its own recursion and internal cache filling.
        for body_name in self.bodies:
            if body_name not in tick_cache:
                resolve_absolute_position(body_name, t, self.bodies, tick_cache)

        # Filter the results to only include bodies present in the injected registry.
        # This ensures that if resolve_absolute_position injected 'Sun' as a base case
        # but 'Sun' wasn't in self.bodies, it won't be in the returned state.
        filtered_state = {
            name: tick_cache[name] for name in self.bodies if name in tick_cache
        }

        self._cache_t = t
        self._cache_state = filtered_state
        return filtered_state.copy()
