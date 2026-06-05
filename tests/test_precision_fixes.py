"""Regression tests for numerical precision fixes.

Verifies that Sun-primary bodies do not 'freeze' due to temporal quantization
and that path projection uses high-precision accumulation.
"""

import pytest
from decimal import Decimal
from src.simulation import Simulation, SimulationClock
from src.bodies import BODIES
from src.constants import SOLVER_TOLERANCE

@pytest.fixture(scope="module")
def test_bodies():
    return BODIES

@pytest.fixture
def sim(test_bodies):
    clock = SimulationClock(rate=1.0)
    return Simulation(clock, bodies=test_bodies)

def test_sun_primary_movement_precision(sim):
    """Verify Earth moves significantly between t=0 and t=1s.
    
    With 6-decimal rounding of t_orbital (years), 1s is quantized to 0.
    Earth's orbital speed is ~29.78 km/s.
    """
    state0 = sim.get_system_state(0.0)
    # 1 second = 1 / 86400 days
    state1 = sim.get_system_state(1.0 / 86400.0)
    
    pos0 = state0["Earth"]
    pos1 = state1["Earth"]
    
    dist = (pos1 - pos0).magnitude()
    
    # Expected movement is ~29.78 km. 
    # If quantized to 0, dist will be 0.
    # If unit mismatch (days instead of years), dist will be ~2.6M km.
    assert dist > 0.1, f"Earth appears frozen. Movement: {dist} km"
    assert dist < 100.0, f"Earth moved too much (unit mismatch?). Movement: {dist} km"
    assert dist == pytest.approx(29.78, abs=1.0)

def test_future_path_decimal_precision(sim):
    """Verify get_future_path matches get_system_state exactly.
    
    Tests for float accumulation drift in long projections.
    """
    t_start = 0.0
    duration = 10000.0 # days
    steps = 1000
    
    path = sim.get_future_path("Earth", t_start, duration, steps)
    
    dt = duration / steps
    for i, pos_path in enumerate(path):
        t_check = t_start + (i * dt)
        state = sim.get_system_state(t_check)
        pos_state = state["Earth"]
        
        # We expect exact match if both use Decimal for time
        assert pos_path.x == pos_state.x, f"Mismatch at step {i}, t={t_check}"
        assert pos_path.y == pos_state.y
