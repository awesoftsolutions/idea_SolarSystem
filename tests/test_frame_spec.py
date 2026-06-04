from src.constants import AU_TO_KM
from src.frames import FrameNode
from src.bodies import BODIES

def test_au_to_km_value():
    """Verify AU_TO_KM is exactly 149,597,870.7."""
    assert AU_TO_KM == 149597870.7

def test_frame_node_schema():
    """Verify FrameNode structure against J2000 data schema in src/bodies.py."""
    # Example check against Earth
    earth_data = BODIES["Earth"]
    # FrameNode is TypedDict(total=False), so we check if fields exist and match types
    _node: FrameNode = earth_data
    assert "primary" in earth_data
    assert "a" in earth_data
    assert "e" in earth_data
    assert "T" in earth_data
    assert "radius" in earth_data
    assert "color" in earth_data
