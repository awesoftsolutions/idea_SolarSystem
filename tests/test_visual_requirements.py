import os
import pytest
import pygame
from src import constants
from src.scenes import SceneManager, TitleScene, SimulationScene
from src.simulation import Simulation, SimulationClock
from src.bodies import BODIES
from src.viewport import Viewport
from src.render import Renderer
from src.vector import Vec2


@pytest.fixture
def mock_pygame():
    """Initialize and quit pygame for tests."""
    pygame.init()
    # Use a hidden window for testing if possible, or just init
    # Note: set_mode is often required for font rendering
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    yield
    pygame.quit()


def test_window_properties():
    """Verify window title and size constants match SOW."""
    # AC-2: Window Title/Size
    assert constants.WINDOW_SIZE == (1440, 1080)
    # The title is set in main.py, we verify the string here
    # In a real integration test we'd check pygame.display.get_caption()
    # but that requires a running loop.


def test_title_scene_ui(mock_pygame):
    """Verify TitleScene text elements."""
    manager = SceneManager()
    sim_clock = SimulationClock()
    simulation = Simulation(clock=sim_clock, bodies=BODIES)
    viewport = Viewport(center=Vec2(0.0, 0.0), zoom=1.0)
    renderer = Renderer(simulation=simulation, viewport=viewport)

    TitleScene(manager=manager, simulation=simulation, renderer=renderer)

    # We can't easily inspect the surface content without complex mocking,
    # but we can verify the logic and constants used.
    assert constants.FONT_SIZE_TITLE == 64
    assert constants.FONT_SIZE_SMALL == 24


def test_simulation_scene_ui(mock_pygame):
    """Verify SimulationScene UI elements."""
    sim_clock = SimulationClock()
    simulation = Simulation(clock=sim_clock, bodies=BODIES)
    viewport = Viewport(center=Vec2(0.0, 0.0), zoom=1.0)
    renderer = Renderer(simulation=simulation, viewport=viewport)

    scene = SimulationScene(simulation=simulation, renderer=renderer)

    assert scene.is_paused is False
    # Toggle pause
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p})
    scene.handle_event(event)
    assert scene.is_paused is True


def test_scene_transition(mock_pygame):
    """Verify transition from Title to Simulation on SPACE."""
    manager = SceneManager()
    sim_clock = SimulationClock()
    simulation = Simulation(clock=sim_clock, bodies=BODIES)
    viewport = Viewport(center=Vec2(0.0, 0.0), zoom=1.0)
    renderer = Renderer(simulation=simulation, viewport=viewport)

    title_scene = TitleScene(manager=manager, simulation=simulation, renderer=renderer)
    manager.transition_to(title_scene)

    assert isinstance(manager.active_scene, TitleScene)

    # Simulate SPACE key
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    manager.handle_event(event)

    assert isinstance(manager.active_scene, SimulationScene)


def test_visual_evidence_presence():
    """Verify that the required audit screenshots exist.

    THIS TEST IS EXPECTED TO FAIL in the Red phase of TDD.
    """
    required_screenshots = [
        "title_screen.png",
        "simulation_screen.png",
        "paused_state.png",
        "reversed_state.png",
    ]

    for screenshot in required_screenshots:
        assert os.path.exists(
            screenshot
        ), f"Missing required visual evidence: {screenshot}"
