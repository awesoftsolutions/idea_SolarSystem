import pathlib


def check_changelog(path: pathlib.Path, expected_description: str, sprint: int = 1):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 2, f"{path} is too short"
    assert lines[0].strip() == "# CHANGELOG:", f"{path} missing '# CHANGELOG:' header"
    assert (
        lines[1].strip() == f"# - Sprint {sprint}: {expected_description}"
    ), f"{path} has incorrect changelog content"


def test_orbital_changelog():
    check_changelog(
        pathlib.Path("src/orbital.py"),
        "Implement Newton-Raphson Kepler solver and heliocentric coordinate logic.",
    )


def test_vector_changelog():
    check_changelog(
        pathlib.Path("src/vector.py"),
        "Implement immutable Vec2 library with arithmetic and geometric operations.",
    )


def test_bodies_changelog():
    check_changelog(
        pathlib.Path("src/bodies.py"),
        "Initialize J2000 reference data for solar system bodies.",
    )


def test_constants_changelog():
    check_changelog(
        pathlib.Path("src/constants.py"),
        "Define mathematical constants for solver tolerance and iterations.",
    )


def test_frames_changelog():
    check_changelog(
        pathlib.Path("src/frames.py"),
        "Implement recursive position resolution with cycle detection and unit conversion.",
        sprint=2,
    )


def test_scaling_changelog():
    check_changelog(
        pathlib.Path("src/scaling.py"),
        "Implement hierarchical logarithmic mapping and neighborhood logic.",
        sprint=3,
    )


def test_scaling_constants_changelog():
    check_changelog(
        pathlib.Path("src/scaling_constants.py"),
        "Define display neighborhoods and scaling constants.",
        sprint=3,
    )


def test_viewport_changelog():
    check_changelog(
        pathlib.Path("src/viewport.py"),
        "Implement Viewport class and coordinate transformations.",
        sprint=3,
    )
