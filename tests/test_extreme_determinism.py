"""Extreme determinism and time-reversal stress test suite.

Verifies perfect determinism and bidirectional consistency under high load,
high simulation rates, and extreme time jumps.
"""

import pytest
from src.simulation import Simulation, SimulationClock
from src.bodies import BODIES
from src.constants import SOLVER_TOLERANCE

@pytest.fixture(scope="module")
def test_bodies():
    """Fixture providing the full BODIES registry."""
    return BODIES

@pytest.fixture
def sim(test_bodies):
    """Fixture providing a fresh Simulation instance."""
    clock = SimulationClock(rate=1.0)
    return Simulation(clock, bodies=test_bodies)

def test_bidirectional_10k_frames(sim):
    """Scenario A: 10,000 frames forward and backward.
    
    Verifies zero positional delta after a long bidirectional run.
    Satisfies AC-1.
    """
    dt = 0.01667  # ~60 FPS
    steps = 10000
    
    initial_state = sim.get_system_state(0.0)
    
    # Forward
    for _ in range(steps):
        sim.clock.update(dt)
        
    # Backward
    sim.clock.set_rate(-1.0)
    for _ in range(steps):
        sim.clock.update(dt)
        
    final_state = sim.get_system_state(sim.clock.get_time())
    
    for body_name in initial_state:
        pos_i = initial_state[body_name]
        pos_f = final_state[body_name]
        assert pos_f.x == pytest.approx(pos_i.x, abs=SOLVER_TOLERANCE)
        assert pos_f.y == pytest.approx(pos_i.y, abs=SOLVER_TOLERANCE)

def test_reversal_at_high_rate(sim):
    """Scenario B: State consistency when toggling direction at 100x rate.
    
    Verifies that high simulation rates do not introduce jitter or drift.
    Satisfies AC-2.
    """
    dt = 0.1
    high_rate = 100.0
    
    sim.clock.set_rate(high_rate)
    for _ in range(100):
        sim.clock.update(dt)
    state_at_t1 = sim.get_system_state(sim.clock.get_time())
    
    # Reverse
    sim.clock.set_rate(-high_rate)
    for _ in range(100):
        sim.clock.update(dt)
    
    assert sim.clock.get_time() == pytest.approx(0.0, abs=1e-12)
    
    # Forward again
    sim.clock.set_rate(high_rate)
    for _ in range(100):
        sim.clock.update(dt)
    state_at_t2 = sim.get_system_state(sim.clock.get_time())
    
    for body_name in state_at_t1:
        pos1 = state_at_t1[body_name]
        pos2 = state_at_t2[body_name]
        # Exact match expected for pure function state at same t
        assert pos1.x == pos2.x
        assert pos1.y == pos2.y

def test_extreme_jump_reversal(sim):
    """Scenario C: 1,000,000 day jump and reverse.
    
    Verifies state consistency after extreme time offsets.
    Satisfies AC-3.
    """
    extreme_t = 1000000.0
    initial_state = sim.get_system_state(0.0)
    
    # Jump
    sim.clock.t_sim = extreme_t
    _ = sim.get_system_state(extreme_t)
    
    # Reverse in large steps
    sim.clock.set_rate(-1.0)
    steps = 1000
    dt = extreme_t / steps
    for _ in range(steps):
        sim.clock.update(dt)
        
    assert sim.clock.get_time() == pytest.approx(0.0, abs=1e-9)
    
    final_state = sim.get_system_state(0.0)
    for body_name in initial_state:
        pos_i = initial_state[body_name]
        pos_f = final_state[body_name]
        assert pos_f.x == pytest.approx(pos_i.x, abs=SOLVER_TOLERANCE)
        assert pos_f.y == pytest.approx(pos_i.y, abs=SOLVER_TOLERANCE)
