"""Tests for trail continuity and time-reversal unwinding logic."""

from src.trail import Trail
from src.vector import Vec2

def test_trail_forward_continuity():
    """Verify trail grows correctly during forward simulation.
    
    AC-1: When simulation direction is forward, points are appended normally.
    """
    trail = Trail(capacity=10)
    p1 = Vec2(100, 100)
    p2 = Vec2(200, 200)
    
    # Current implementation only takes pos, but pseudocode requires (pos, t)
    # This test is expected to fail or need adjustment during implementation.
    # We follow the pseudocode signature: append(pos, t)
    trail.append(p1, 0.0)
    trail.append(p2, 1.0)
    
    points = trail.get_points()
    assert len(points) == 2
    assert points[0] == p1
    assert points[1] == p2

def test_trail_reversal_unwinding():
    """Verify trail pops points with timestamp greater than current simulation time.
    
    AC-1: When simulation direction is reversed, then trails remain continuous 
    and correctly attached to bodies by 'unwinding' future points.
    """
    trail = Trail(capacity=100)
    
    # Simulate forward to t=10.0
    for t in range(11):
        trail.append(Vec2(float(t), float(t)), float(t))
    
    assert len(trail.get_points()) == 11
    
    # Reverse to t=5.0
    # The logic should remove points for t=6, 7, 8, 9, 10
    trail.append(Vec2(5.0, 5.0), 5.0)
    
    points = trail.get_points()
    # Depending on implementation, t=5 might be updated or kept.
    # Pseudocode says: If newest_point.t == t: Update newest_point.pos = pos
    # So we expect 6 points (0, 1, 2, 3, 4, 5)
    assert len(points) == 6
    
    # Verify no "smear" - the last point should be exactly at t=5.0
    assert points[-1] == Vec2(5.0, 5.0)

def test_trail_deterministic_regrowth():
    """Verify trail consistency after a reversal and forward re-simulation cycle.
    
    DR-003: Strict determinism must be maintained.
    """
    trail = Trail(capacity=100)
    
    # 1. Forward to t=10.0
    for t in range(11):
        trail.append(Vec2(float(t), float(t)), float(t))
    
    original_points = trail.get_points()
    
    # 2. Reverse to t=5.0
    trail.append(Vec2(5.0, 5.0), 5.0)
    
    # 3. Run forward again to t=10.0
    for t in range(6, 11):
        trail.append(Vec2(float(t), float(t)), float(t))
        
    new_points = trail.get_points()
    
    assert len(new_points) == len(original_points)
    for p_orig, p_new in zip(original_points, new_points):
        assert p_orig == p_new
