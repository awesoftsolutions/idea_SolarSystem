import tomllib
from src.constants import SOLVER_TOLERANCE, MAX_ITERATIONS
from src.bodies import BODIES


def test_pyproject_metadata():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["tool"]["poetry"]["name"] == "solar"
    assert "pygame" in data["tool"]["poetry"]["dependencies"]
    assert "pytest" in data["tool"]["poetry"]["group"]["dev"]["dependencies"]


def test_constants():
    assert SOLVER_TOLERANCE == 1e-9
    assert MAX_ITERATIONS == 100


def test_bodies_integrity():
    bodies_list = BODIES.list_bodies()
    assert len(bodies_list) >= 25
    assert "Sun" in BODIES
    assert BODIES.get_body("Sun")["primary"] is None

    # Check a few specific bodies
    assert BODIES.get_body("Earth")["primary"] == "Sun"
    assert BODIES.get_body("Moon")["primary"] == "Earth"
    assert BODIES.get_body("Triton")["T"] < 0  # Retrograde

    for name in bodies_list:
        data = BODIES.get_body(name)
        assert "radius" in data
        assert "color" in data
        if name != "Sun":
            assert "a" in data
            assert "e" in data
            assert "T" in data
            assert "primary" in data


def test_model_separation():
    # Verify no pygame imports in model files
    for path in ["src/bodies.py", "src/constants.py"]:
        with open(path, "r") as f:
            content = f.read()
            assert "pygame" not in content
