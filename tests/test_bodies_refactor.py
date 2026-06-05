"""Tests for the Body Registry refactor and provider-based architecture.

Verifies that the new BodyProvider protocol and its implementations (Static,
AsteroidBelt, Composite) satisfy the architectural requirements and
acceptance criteria.
"""

import pytest

from src.bodies import (
    AsteroidBeltProvider,
    BodyData,
    CompositeBodyProvider,
    StaticBodyProvider,
)
from src.simulation import Simulation, SimulationClock
from src.vector import Vec2


class TestStaticBodyProvider:
    """Tests for StaticBodyProvider (AC3).

    Verifies that the static provider correctly wraps dictionary data and
    satisfies the BodyProvider protocol.
    """

    def test_static_provider_resolution(self) -> None:
        """Verify StaticBodyProvider correctly wraps a dictionary and retrieves data."""
        data: dict[str, BodyData] = {
            "Sun": {"radius": 696340.0, "color": (255, 255, 0), "primary": None},
            "Earth": {
                "primary": "Sun",
                "a": 1.0,
                "e": 0.0167,
                "T": 1.0,
                "radius": 6371.0,
                "color": (100, 149, 237),
            },
        }
        provider = StaticBodyProvider(data)

        assert provider.get_body("Sun") == data["Sun"]
        assert provider.get_body("Earth") == data["Earth"]
        assert "Sun" in provider
        assert "Earth" in provider
        assert set(provider.list_bodies()) == {"Sun", "Earth"}

    def test_static_provider_key_error(self) -> None:
        """Verify get_body raises KeyError for non-existent IDs (AC3)."""
        provider = StaticBodyProvider({})
        with pytest.raises(KeyError):
            provider.get_body("Unknown")

    def test_static_provider_iteration(self) -> None:
        """Verify provider supports iteration over body names for protocol compliance."""
        data: dict[str, BodyData] = {"A": {}, "B": {}}  # type: ignore
        provider = StaticBodyProvider(data)
        assert set(iter(provider)) == {"A", "B"}


class TestAsteroidBeltProvider:
    """Tests for AsteroidBeltProvider (AC2).

    Verifies procedural generation determinism and semantic grouping of asteroids.
    """

    def test_asteroid_belt_determinism(self) -> None:
        """Verify AsteroidBeltProvider is deterministic with a fixed seed (AC1).

        Ensures that two providers initialized with the same seed produce
        identical body lists and data.
        """
        seed = 42
        count = 10
        provider1 = AsteroidBeltProvider(seed=seed, count=count)
        provider2 = AsteroidBeltProvider(seed=seed, count=count)

        assert provider1.list_bodies() == provider2.list_bodies()
        for name in provider1.list_bodies():
            assert provider1.get_body(name) == provider2.get_body(name)

    def test_asteroid_belt_grouping(self) -> None:
        """Verify the belt is returned as a single semantic group (AC2).

        Ensures that the provider exposes a 'AsteroidBelt' group containing
        all generated asteroid names.
        """
        provider = AsteroidBeltProvider(seed=1, count=5)
        groups = provider.get_groups()

        assert "AsteroidBelt" in groups
        assert len(groups["AsteroidBelt"]) == 5
        assert all(name.startswith("Ast-") for name in groups["AsteroidBelt"])

    def test_asteroid_belt_contains(self) -> None:
        """Verify 'in' operator works for generated asteroids for protocol compliance."""
        provider = AsteroidBeltProvider(seed=1, count=5)
        bodies = provider.list_bodies()
        assert bodies[0] in provider
        assert "Sun" not in provider


class TestCompositeBodyProvider:
    """Tests for CompositeBodyProvider (AC3).

    Verifies aggregation of multiple providers and priority-based resolution.
    """

    def test_composite_resolution(self) -> None:
        """Verify CompositeBodyProvider resolves from multiple sources.

        Ensures that bodies from both static and procedural providers are
        accessible through the composite interface.
        """
        static_data: dict[str, BodyData] = {"Sun": {"primary": None}}  # type: ignore
        static_p = StaticBodyProvider(static_data)
        belt_p = AsteroidBeltProvider(seed=42, count=5)

        composite = CompositeBodyProvider([static_p, belt_p])

        # Resolve from static
        assert composite.get_body("Sun") == static_data["Sun"]
        # Resolve from belt
        ast_name = belt_p.list_bodies()[0]
        assert composite.get_body(ast_name) == belt_p.get_body(ast_name)

        assert "Sun" in composite
        assert ast_name in composite

    def test_composite_priority(self) -> None:
        """Verify priority-based resolution (first provider wins).

        Ensures that if multiple providers contain the same body name, the
        one appearing earlier in the provider list takes precedence.
        """
        data1: dict[str, BodyData] = {"A": {"radius": 1}}  # type: ignore
        data2: dict[str, BodyData] = {"A": {"radius": 2}}  # type: ignore

        p1 = StaticBodyProvider(data1)
        p2 = StaticBodyProvider(data2)

        c1 = CompositeBodyProvider([p1, p2])
        assert c1.get_body("A")["radius"] == 1

        c2 = CompositeBodyProvider([p2, p1])
        assert c2.get_body("A")["radius"] == 2

    def test_composite_list_bodies(self) -> None:
        """Verify list_bodies combines all sources into a single set."""
        p1 = StaticBodyProvider({"A": {}})  # type: ignore
        p2 = StaticBodyProvider({"B": {}})  # type: ignore
        composite = CompositeBodyProvider([p1, p2])
        assert set(composite.list_bodies()) == {"A", "B"}

    def test_composite_groups_merge(self) -> None:
        """Verify groups from all providers are merged into a single dictionary."""

        # Mock providers with groups
        class MockProvider:
            def get_groups(self):
                return {"G1": ["A"]}

            def list_bodies(self):
                return ["A"]

            def __contains__(self, k):
                return k == "A"

        class MockProvider2:
            def get_groups(self):
                return {"G2": ["B"]}

            def list_bodies(self):
                return ["B"]

            def __contains__(self, k):
                return k == "B"

        composite = CompositeBodyProvider([MockProvider(), MockProvider2()])  # type: ignore
        groups = composite.get_groups()
        assert "G1" in groups
        assert "G2" in groups

    def test_composite_groups_collision_merge(self) -> None:
        """Verify that groups with the same name from different providers are combined."""

        class MockProvider1:
            def get_groups(self):
                return {"SharedGroup": ["A"]}

            def list_bodies(self):
                return ["A"]

            def __contains__(self, k):
                return k == "A"

        class MockProvider2:
            def get_groups(self):
                return {"SharedGroup": ["B"]}

            def list_bodies(self):
                return ["B"]

            def __contains__(self, k):
                return k == "B"

        composite = CompositeBodyProvider([MockProvider1(), MockProvider2()])  # type: ignore
        groups = composite.get_groups()

        assert "SharedGroup" in groups
        assert set(groups["SharedGroup"]) == {"A", "B"}

    def test_composite_key_error(self) -> None:
        """Verify KeyError if a body is not found in any provider (AC3)."""
        composite = CompositeBodyProvider([])
        with pytest.raises(KeyError):
            composite.get_body("Missing")


class TestSimulationIntegration:
    """Integration tests for Simulation with BodyProvider (AC1).

    Verifies that the Simulation engine correctly interacts with the new
    provider architecture.
    """

    def test_simulation_with_provider(self) -> None:
        """Verify Simulation correctly resolves positions using the provider interface (AC1).

        Ensures that the Simulation class can use a BodyProvider to calculate
        the system state.
        """
        static_data: dict[str, BodyData] = {
            "Sun": {"radius": 696340.0, "color": (255, 255, 0), "primary": None},
            "Earth": {
                "primary": "Sun",
                "a": 1.0,
                "e": 0.0,
                "T": 1.0,
                "radius": 6371.0,
                "color": (100, 149, 237),
            },
        }
        provider = StaticBodyProvider(static_data)
        clock = SimulationClock()
        sim = Simulation(clock=clock, bodies=provider)

        state = sim.get_system_state(0.0)
        assert "Sun" in state
        assert "Earth" in state
        assert isinstance(state["Sun"], Vec2)
        assert isinstance(state["Earth"], Vec2)

    def test_simulation_with_composite_provider(self) -> None:
        """Verify Simulation works with a mix of static and procedural bodies.

        Ensures that the Simulation engine can handle a CompositeBodyProvider
        containing both static planetary data and procedural asteroids.
        """
        static_p = StaticBodyProvider({"Sun": {"primary": None, "radius": 1}})  # type: ignore
        belt_p = AsteroidBeltProvider(seed=42, count=10)
        composite = CompositeBodyProvider([static_p, belt_p])

        sim = Simulation(clock=SimulationClock(), bodies=composite)
        state = sim.get_system_state(0.0)

        assert "Sun" in state
        # Check for an asteroid
        ast_name = belt_p.list_bodies()[0]
        assert ast_name in state
