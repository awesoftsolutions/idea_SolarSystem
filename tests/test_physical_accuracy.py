"""Physical accuracy tests for orbital mechanics.

Verifies that bodies complete their orbits in the time specified in src/bodies.py
and follow expected physical laws (e.g., retrograde motion).
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

def test_earth_orbital_period(sim):
    """Verify Earth completes an orbit in exactly 1.0 year (365.25 days).
    
    This test is expected to fail if the unit mismatch in src/frames.py exists.
    """
    # Earth period T = 1.0 year. 
    # If t is in days, we expect Earth to be back at start after 365.25 days.
    period_days = 365.25
    
    initial_state = sim.get_system_state(0.0)
    pos_i = initial_state["Earth"]
    
    # Jump to 1 period
    final_state = sim.get_system_state(period_days)
    pos_f = final_state["Earth"]
    
    # Check if position matches within tolerance
    assert pos_f.x == pytest.approx(pos_i.x, abs=SOLVER_TOLERANCE), \
        f"Earth position mismatch after 365.25 days. Delta: {pos_f.x - pos_i.x}"
    assert pos_f.y == pytest.approx(pos_i.y, abs=SOLVER_TOLERANCE)

def test_moon_orbital_period(sim):
    """Verify Moon completes an orbit around Earth in 27.32 days.
    
    Planetary moons use days for T, so this should pass even with the Sun-unit bug.
    """
    period_days = 27.32
    
    # Get relative positions
    def get_moon_rel_pos(t):
        state = sim.get_system_state(t)
        return state["Moon"] - state["Earth"]
        
    pos_i = get_moon_rel_pos(0.0)
    pos_f = get_moon_rel_pos(period_days)
    
    assert pos_f.x == pytest.approx(pos_i.x, abs=SOLVER_TOLERANCE)
    assert pos_f.y == pytest.approx(pos_i.y, abs=SOLVER_TOLERANCE)

def test_retrograde_motion(sim):
    """Verify Triton (retrograde) moves in the opposite direction of other bodies.
    
    Triton has T = -5.88 days.
    """
    # Compare Triton (retrograde) with Moon (prograde)
    # At t=0, both are at perihelion (on the x-axis in the orbital plane)
    # After a small dt, prograde should have y > 0, retrograde should have y < 0
    dt = 0.1
    
    def get_rel_pos(name, t):
        state = sim.get_system_state(t)
        primary = BODIES.get_body(name)["primary"]
        return state[name] - state[primary]
        
    pos_moon = get_rel_pos("Moon", dt)
    pos_triton = get_rel_pos("Triton", dt)
    
    # Moon is prograde (counter-clockwise) -> y > 0
    assert pos_moon.y > 0
    # Triton is retrograde (clockwise) -> y < 0
    assert pos_triton.y < 0
