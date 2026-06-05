import math
import pytest

from src.constants import AU_TO_KM
from src.frames import Frame, resolve_absolute_position
from src.scaling import (
    get_neighborhood_bounds,
    log_scale_distance,
    log_scale_size,
    map_to_screen,
    map_to_world,
    scale_orbit_geometry,
)
from src.viewport import Viewport, world_to_screen
from src.vector import Vec2
from src.bodies import BODIES


def test_distance_monotonicity():
    """Verify that log_scale_distance is monotonic."""
    d1 = 1.0
    d2 = 2.0
    base = 10.0

    s1 = log_scale_distance(d1, base)
    s2 = log_scale_distance(d2, base)

    assert s2 > s1
    assert log_scale_distance(0.0, base) == 0.0
    assert log_scale_distance(-1.0, base) == 0.0


def test_size_clamping():
    """Verify that log_scale_size respects min/max pixel bounds."""
    min_p = 2.0
    max_p = 50.0
    base = 10.0

    # Small radius
    assert log_scale_size(0.1, min_p, max_p, base) == min_p
    # Large radius
    assert log_scale_size(1e9, min_p, max_p, base) == max_p
    # Zero/Negative
    assert log_scale_size(0.0, min_p, max_p, base) == min_p
    # Lower bound for negative
    assert log_scale_size(-10.0, min_p, max_p, base) == min_p


def test_neighborhood_retrieval():
    """Verify neighborhood bounds are retrieved correctly from constants."""
    # Sun neighborhood (from constants)
    sun_bounds = get_neighborhood_bounds("Sun")
    assert sun_bounds > 0
    assert isinstance(sun_bounds, float)

    # Earth neighborhood
    earth_bounds = get_neighborhood_bounds("Earth")
    assert earth_bounds > 0

    with pytest.raises(KeyError, match="Unknown body"):
        get_neighborhood_bounds("UnknownBody")


def test_neptune_containment() -> None:
    """Ensure Neptune fits in the 1440x1080 viewport at default zoom 1.0."""
    d_neptune = 30.0  # AU
    # For Sun frame, s=1.0, k is calculated to fit Neptune at 500px from center
    scaled_d = log_scale_distance(d_neptune, 10.0, k=335.0, s=1.0)
    world_pos = Vec2(scaled_d, 0.0)
    v = Viewport(Vec2(0.0, 0.0), 1.0)

    s = world_to_screen(world_pos, v)

    # Assertion: s is within (0,0) to (1440, 1080)
    assert 0.0 <= s.x <= 1440.0
    assert 0.0 <= s.y <= 1080.0


def test_map_to_screen_moon_relative_to_earth():
    """Verify Moon screen offset from Earth matches linear-scaled distance."""
    t = 0.0
    viewport = Viewport(Vec2(0.0, 0.0), 1.0)
    earth_frame = Frame("Earth", t)
    moon_frame = Frame("Moon", t)

    # Physical positions (km)
    earth_abs = resolve_absolute_position("Earth", t)
    moon_abs = resolve_absolute_position("Moon", t)

    p_earth = map_to_screen(earth_abs, earth_frame, viewport)
    p_moon = map_to_screen(moon_abs, moon_frame, viewport)

    dist_screen = (p_moon - p_earth).magnitude()

    # Moon is ~384,400 km from Earth.
    assert dist_screen > 0
    assert dist_screen < 100.0  # Should be within Earth's neighborhood (50px)


def test_map_to_screen_planet_relative_to_sun():
    """Verify Planet offset relative to Sun matches log-scaled distance."""
    t = 0.0
    viewport = Viewport(Vec2(0.0, 0.0), 1.0)
    sun_frame = Frame("Sun", t)
    jupiter_frame = Frame("Jupiter", t)
    earth_frame = Frame("Earth", t)

    # Jupiter at ~5.2 AU
    jupiter_abs = resolve_absolute_position("Jupiter", t)
    sun_abs = Vec2(0.0, 0.0)

    p_sun = map_to_screen(sun_abs, sun_frame, viewport)
    p_jupiter = map_to_screen(jupiter_abs, jupiter_frame, viewport)

    dist_screen = (p_jupiter - p_sun).magnitude()

    # Expected screen distance should be monotonic with AU
    earth_abs = resolve_absolute_position("Earth", t)
    p_earth = map_to_screen(earth_abs, earth_frame, viewport)
    dist_earth = (p_earth - p_sun).magnitude()

    assert dist_screen > dist_earth


def test_map_to_screen_origin_mapping():
    """Verify Body at primary origin maps to primary screen position."""
    t = 0.0
    viewport = Viewport(Vec2(0.0, 0.0), 1.0)

    # Mock Moon at exactly Earth's position
    earth_abs = resolve_absolute_position("Earth", t)

    earth_frame = Frame("Earth", t)
    moon_frame = Frame("Moon", t)
    w_earth = map_to_world(earth_abs, earth_frame, use_cache=False)
    w_moon = map_to_world(earth_abs, moon_frame, use_cache=False)

    assert math.isclose(w_earth.x, w_moon.x, abs_tol=1e-7)
    assert math.isclose(w_earth.y, w_moon.y, abs_tol=1e-7)


def test_map_to_screen_monotonicity():
    """Verify scaling consistency within the same frame (monotonicity)."""
    t = 0.0
    viewport = Viewport(Vec2(0.0, 0.0), 1.0)
    sun_frame = Frame("Sun", t)

    # Body A at distance D, Body B at distance D + epsilon
    d_km = 1.0 * AU_TO_KM
    pos_a = Vec2(d_km, 0.0)
    pos_b = Vec2(d_km + 1000.0, 0.0)

    p_a = map_to_screen(pos_a, sun_frame, viewport)
    p_b = map_to_screen(pos_b, sun_frame, viewport)

    assert (p_b - p_a).x > 0


def test_map_to_screen_high_zoom():
    """Verify map_to_screen scales correctly with high zoom."""
    t = 0.0
    viewport = Viewport(Vec2(0.0, 0.0), 100.0)
    earth_frame = Frame("Earth", t)

    earth_abs = resolve_absolute_position("Earth", t)

    p_earth = map_to_screen(earth_abs, earth_frame, viewport)

    # With zoom 100, Earth should be much further from center
    assert p_earth.x > 10000.0


def test_map_to_world_cache_hit():
    """Verify that map_to_world uses _WORLD_CACHE with composite keys."""
    from src import scaling

    t = 123.456
    pos = Vec2(1e8, 0)
    frame = Frame("Earth", t)
    cache_key = (frame.name, pos.x, pos.y)

    scaling._WORLD_CACHE.clear()
    scaling._LAST_SIM_TIME = t

    map_to_world(pos, frame)

    assert cache_key in scaling._WORLD_CACHE
    scaling._WORLD_CACHE[cache_key] = Vec2(999, 999)

    res2 = map_to_world(pos, frame)
    assert res2 == Vec2(999, 999)


def test_map_to_world_cache_invalidation():
    """Verify that the cache is cleared when simulation time changes."""
    from src import scaling

    t1 = 10.0
    t2 = 456.789
    frame1 = Frame("Sun", t1)
    frame2 = Frame("Sun", t2)
    pos = Vec2(100.0, 100.0)

    scaling._WORLD_CACHE.clear()
    scaling._LAST_SIM_TIME = t1

    map_to_world(pos, frame1)
    assert len(scaling._WORLD_CACHE) > 0

    pos2 = Vec2(200.0, 200.0)
    map_to_world(pos2, frame2)

    assert scaling._LAST_SIM_TIME == t2
    assert (frame2.name, pos2.x, pos2.y) in scaling._WORLD_CACHE
    assert (frame1.name, pos.x, pos.y) not in scaling._WORLD_CACHE


@pytest.mark.parametrize("e", [0.0, 0.1, 0.5, 0.9, 0.99, 0.999])
def test_eccentricity_preservation(e):
    """Verify b_v / a_v == sqrt(1 - e^2) for various eccentricities."""
    elements = {"a": 1.0, "e": e, "longitude_of_perihelion": 0.0, "primary": "Sun"}
    result = scale_orbit_geometry(elements)

    a_v = result["a_v"]
    b_v = result["b_v"]

    if a_v > 0:
        expected_ratio = math.sqrt(1.0 - e**2)
        assert math.isclose(b_v / a_v, expected_ratio, rel_tol=1e-9)
    else:
        assert b_v == 0.0


@pytest.mark.parametrize("omega", [0.0, math.pi / 4, math.pi / 2, math.pi, 2 * math.pi])
def test_orientation_preservation(omega):
    """Verify orientation matches input longitude_of_perihelion."""
    elements = {"a": 1.0, "e": 0.1, "longitude_of_perihelion": omega, "primary": "Sun"}
    result = scale_orbit_geometry(elements)

    assert math.isclose(result["orientation"], omega, abs_tol=1e-9)


@pytest.mark.parametrize("e", [0.0, 0.1, 0.5, 0.9])
@pytest.mark.parametrize("omega", [0.0, math.pi / 4, math.pi / 2])
def test_focus_alignment(e, omega):
    """Verify that the primary focus remains at (0,0) in scaled space."""
    elements = {"a": 1.5, "e": e, "longitude_of_perihelion": omega, "primary": "Sun"}
    result = scale_orbit_geometry(elements)

    a_v = result["a_v"]
    center_offset = result["center_offset"]
    orientation = result["orientation"]

    # The primary (focus) should be at (0,0)
    focus = center_offset + Vec2(a_v * e, 0.0).rotate(orientation)
    assert focus.magnitude() < 1e-9


def test_circular_orbit():
    """Verify e=0 results in a_v == b_v and zero center_offset."""
    elements = {"a": 1.0, "e": 0.0, "longitude_of_perihelion": 0.5, "primary": "Sun"}
    result = scale_orbit_geometry(elements)

    assert math.isclose(result["a_v"], result["b_v"])
    assert result["center_offset"].magnitude() < 1e-9


def test_zero_a():
    """Verify a=0 results in zeroed geometry."""
    elements = {"a": 0.0, "e": 0.5, "longitude_of_perihelion": 0.0, "primary": "Sun"}
    result = scale_orbit_geometry(elements)

    assert result["a_v"] == 0.0
    assert result["b_v"] == 0.0
    assert result["center_offset"].magnitude() < 1e-9


def test_high_eccentricity_edge_case():
    """Verify stability for e very close to 1.0."""
    e = 0.9999
    elements = {"a": 10.0, "e": e, "longitude_of_perihelion": 1.0, "primary": "Sun"}
    result = scale_orbit_geometry(elements)

    assert result["a_v"] > 0
    assert result["b_v"] >= 0
    assert math.isfinite(result["b_v"])

    # Focus should still be at origin
    focus = result["center_offset"] + Vec2(result["a_v"] * e, 0.0).rotate(
        result["orientation"]
    )
    assert focus.magnitude() < 1e-9


def test_orbit_path_alignment():
    """CRITICAL: Verify that body position lies exactly on the visual orbit path.
    
    This test confirms that the linear scaling fix resolves the geometric disconnect.
    """
    t = 0.0
    # Use Mercury (high eccentricity e=0.2) for testing
    body_name = "Mercury"
    elements = BODIES[body_name]
    
    # 1. Get visual orbit geometry
    orbit_v = scale_orbit_geometry(elements)
    
    # 2. Calculate physical position at perihelion (anomaly = 0)
    # At perihelion, r = a(1-e)
    a = elements["a"]
    e = elements["e"]
    r_peri = a * (1 - e)
    # Position in AU relative to Sun (assuming omega=0 for simplicity in this check)
    pos_peri_au = Vec2(r_peri, 0.0)
    pos_peri_km = pos_peri_au * AU_TO_KM
    
    # 3. Map to world space
    frame = Frame(body_name, t)
    world_pos = map_to_world(pos_peri_km, frame, use_cache=False)
    
    # 4. Verify alignment
    # The visual orbit is an ellipse centered at 'center_offset' with semi-axes a_v, b_v.
    # The body at perihelion should be at: center_offset + Vec2(a_v, 0)
    expected_world_pos = orbit_v["center_offset"] + Vec2(orbit_v["a_v"], 0.0)
    
    assert world_pos == expected_world_pos
