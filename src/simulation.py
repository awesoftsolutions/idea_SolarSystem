# CHANGELOG:
# - Sprint 4: Implement core simulation engine with SimulationClock and Simulation state provider.

"""Core simulation engine for time management and state retrieval.

This module provides the SimulationClock for managing simulation time
and the Simulation class for calculating the system state at any given time.
"""

from src.vector import Vec2
from src.bodies import BODIES
from src.frames import resolve_absolute_position


class SimulationClock:
    """Manages simulation time based on real-world delta time and a rate.

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
        self.t_sim: float = 0.0
        self.rate: float = rate

    def update(self, dt: float) -> None:
        """Advance simulation time by real-world delta time.

        Args:
            dt: Real elapsed time.
        """
        self.t_sim += dt * self.rate

    def set_rate(self, new_rate: float) -> None:
        """Set a new simulation rate.

        Args:
            new_rate: The new time multiplier.
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
    """

    def __init__(self, clock: SimulationClock) -> None:
        """Initialize Simulation with a clock.

        Args:
            clock: The SimulationClock instance to use.

        Returns:
            None
        """
        self.clock = clock

    def get_system_state(self, t: float) -> dict[str, Vec2]:
        """Calculate the absolute positions of all bodies at time t.

        This method is deterministic and side-effect free.

        Args:
            t: The simulation time at which to retrieve the state.

        Returns:
            A dictionary mapping body names to their absolute Vec2 positions in km.
        """
        state: dict[str, Vec2] = {}
        for body_name in BODIES:
            pos = resolve_absolute_position(body_name, t)
            state[body_name] = pos
        return state
