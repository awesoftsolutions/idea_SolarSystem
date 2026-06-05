"""Functional validation suite for simulation determinism and time-reversal symmetry.

This suite verifies that the simulation engine adheres to DR-003 (Pure Function State)
and maintains mathematical integrity across forward and backward time flow.
"""

from typing import TYPE_CHECKING

import pytest

from src.bodies import BODIES, generate_asteroid_belt
from src.constants import SOLVER_TOLERANCE
from src.simulation import Simulation, SimulationClock

if TYPE_CHECKING:
    from src.bodies import StaticBodyProvider


@pytest.fixture(scope="session")
def test_bodies() -> "StaticBodyProvider":
    """Initialize a deterministic set of bodies for the entire test session.

    Returns:
        A StaticBodyProvider containing the base BODIES plus 100 generated asteroids.
    """
    # generate_asteroid_belt now returns a dict instead of mutating global state
    from src.bodies import StaticBodyProvider

    asteroids = generate_asteroid_belt(seed=42, count=100)
    bodies_data = {name: BODIES.get_body(name) for name in BODIES.list_bodies()}
    bodies_data.update(asteroids)
    return StaticBodyProvider(bodies_data)


@pytest.fixture
def sim(test_bodies: "StaticBodyProvider") -> Simulation:
    """Provide a fresh Simulation instance with a default clock and injected bodies.

    Returns:
        A Simulation instance initialized with a SimulationClock at rate 1.0.
    """
    clock = SimulationClock(rate=1.0)
    return Simulation(clock, bodies=test_bodies)


def test_determinism_jump(sim: Simulation) -> None:
    """Verify that state at t is identical regardless of the path taken to reach it.

    AC-2: state_at(t) is perfectly deterministic regardless of jumping.
    """
    target_t = 100.0
    jump_t = 200.0

    # Capture initial state at target_t
    state_initial = sim.get_system_state(target_t)

    # Jump to a future time
    sim.clock.t_sim = jump_t
    _ = sim.get_system_state(jump_t)

    # Jump back to target_t
    sim.clock.t_sim = target_t
    state_final = sim.get_system_state(target_t)

    # Verify all bodies match
    assert state_initial.keys() == state_final.keys()
    for name in state_initial:
        pos_i = state_initial[name]
        pos_f = state_final[name]
        assert pos_i.x == pytest.approx(pos_f.x, abs=SOLVER_TOLERANCE)
        assert pos_i.y == pytest.approx(pos_f.y, abs=SOLVER_TOLERANCE)


def test_time_reversal_symmetry(sim: Simulation) -> None:
    """Verify forward and backward simulation runs produce identical states.

    AC-1: Final state matches initial state within 1e-9 after 10,000 steps forward/backward.
    """
    dt = 0.01
    steps = 10000
    initial_t = sim.clock.get_time()

    # Capture start state
    state_start = sim.get_system_state(initial_t)

    # Forward phase
    sim.clock.set_rate(1.0)
    for _ in range(steps):
        sim.clock.update(dt)

    # Backward phase
    sim.clock.set_rate(-1.0)
    for _ in range(steps):
        sim.clock.update(dt)

    final_t = sim.clock.get_time()
    state_end = sim.get_system_state(final_t)

    # Verify time returned to start (within float precision)
    assert final_t == pytest.approx(initial_t, abs=1e-12)

    # Verify all bodies match
    for name in state_start:
        pos_s = state_start[name]
        pos_e = state_end[name]
        assert pos_s.x == pytest.approx(pos_e.x, abs=SOLVER_TOLERANCE)
        assert pos_s.y == pytest.approx(pos_e.y, abs=SOLVER_TOLERANCE)


def test_rate_consistency(sim: Simulation) -> None:
    """Verify that reaching t via different rates produces the same state.

    AC-3: Rate multiplier does not affect the resulting state for the same simulation time.
    """
    dt = 1.0
    target_t = 10.0

    # Path A: Rate 1.0 (10 steps)
    sim.clock.set_rate(1.0)
    for _ in range(10):
        sim.clock.update(dt)
    state_rate_1 = sim.get_system_state(sim.clock.get_time())

    # Reset clock
    sim.clock.t_sim = 0.0

    # Path B: Rate 10.0 (1 step)
    sim.clock.set_rate(10.0)
    sim.clock.update(dt)
    state_rate_10 = sim.get_system_state(sim.clock.get_time())

    # Verify time reached is the same
    assert sim.clock.get_time() == pytest.approx(target_t, abs=1e-12)

    # Verify all bodies match
    for name in state_rate_1:
        pos_1 = state_rate_1[name]
        pos_10 = state_rate_10[name]
        assert pos_1.x == pytest.approx(pos_10.x, abs=SOLVER_TOLERANCE)
        assert pos_1.y == pytest.approx(pos_10.y, abs=SOLVER_TOLERANCE)
