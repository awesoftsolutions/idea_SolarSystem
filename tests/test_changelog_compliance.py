import pathlib


def has_changelog_entry(file_path: str, entry: str) -> bool:
    """Check if a file contains a specific changelog entry."""
    path = pathlib.Path(file_path)
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    return entry in content


def test_src_frames_changelog_sprint_4():
    """Verify src/frames.py has the Sprint 4 changelog entry."""
    entry = "# - Sprint 4: Refactor resolve_absolute_position for Dependency Injection and local caching."
    assert has_changelog_entry(
        "src/frames.py", entry
    ), f"Missing entry in src/frames.py: {entry}"


def test_src_simulation_changelog_sprint_4():
    """Verify src/simulation.py has its Sprint 4 changelog entries."""
    entries = [
        "# - Sprint 4: Implement core simulation engine with SimulationClock and Simulation state provider.",
        "# - Sprint 4: Implement per-tick state caching and Decimal-based deterministic clock.",
    ]
    for entry in entries:
        assert has_changelog_entry(
            "src/simulation.py", entry
        ), f"Missing entry in src/simulation.py: {entry}"


def test_src_bodies_changelog_sprint_4():
    """Verify src/bodies.py has its Sprint 4 changelog entry."""
    entry = "# - Sprint 4: Implement procedural asteroid belt generation with Kirkwood gaps."
    assert has_changelog_entry(
        "src/bodies.py", entry
    ), f"Missing entry in src/bodies.py: {entry}"


def test_no_changelogs_in_tests():
    """Verify no .py files in the tests/ directory contain a # CHANGELOG: block.

    Excludes tests/test_changelogs.py as it contains the string for verification logic.
    """
    test_dir = pathlib.Path("tests")
    py_files = list(test_dir.glob("**/*.py"))

    for py_file in py_files:
        if py_file.name in ["test_changelogs.py", "test_changelog_compliance.py"]:
            continue
        content = py_file.read_text(encoding="utf-8")
        assert (
            "# CHANGELOG:" not in content
        ), f"Forbidden # CHANGELOG: found in {py_file}"
