import pathlib


def check_changelog(path: pathlib.Path, expected_description: str):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 2, f"{path} is too short"
    assert lines[0].strip() == "# CHANGELOG:", f"{path} missing '# CHANGELOG:' header"
    assert (
        lines[1].strip() == f"# - Sprint 1: {expected_description}"
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
