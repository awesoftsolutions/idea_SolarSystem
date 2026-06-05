# CHANGELOG:
# - Sprint 5: Implement main application entry point, event loop, and input validation.

"""Main entry point for the solar system simulation.

This module initializes Pygame, sets up the simulation environment,
and manages the main application loop and event dispatching.
"""

import math
import sys

import pygame

from src.constants import FPS_CAP, MAX_RATE, MIN_RATE, WINDOW_SIZE
from src.bodies import BODIES
from src.simulation import Simulation, SimulationClock
from src.viewport import Viewport
from src.render import Renderer
from src.scenes import SceneManager, TitleScene, SimulationScene
from src.diagnostics import Diagnostics
from src.vector import Vec2


def active_scene_is_simulation(manager: SceneManager) -> bool:
    """Check if the active scene is SimulationScene.

    This helper is used for input validation logic that is scene-dependent.

    Args:
        manager: The SceneManager instance to check.

    Returns:
        True if the active scene is a SimulationScene, False otherwise.
    """
    return isinstance(manager.active_scene, SimulationScene)


def handle_global_input(
    event: pygame.event.Event,
    sim_clock: SimulationClock,
    diagnostics: Diagnostics,
    manager: SceneManager | None = None,
) -> bool:
    """Handle global application inputs.

    Args:
        event: The Pygame event to handle.
        sim_clock: The simulation clock for rate adjustments.
        diagnostics: The diagnostics system.
        manager: The scene manager to check active scene state.

    Returns:
        False if the application should shut down, True otherwise.
    """
    if event.type == pygame.QUIT:
        return False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return False

        # AC-3: Time Reversal (SPACE)
        if event.key == pygame.K_SPACE:
            if manager and active_scene_is_simulation(manager):
                sim_clock.rate = -1.0 * sim_clock.rate

        # AC-2: Rate Adjustment (+/-)
        if event.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
            new_rate = sim_clock.rate * 1.1
            if abs(new_rate) > MAX_RATE:
                new_rate = math.copysign(MAX_RATE, new_rate)
            sim_clock.rate = new_rate

        if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            new_rate = sim_clock.rate / 1.1
            if abs(new_rate) < MIN_RATE:
                new_rate = math.copysign(MIN_RATE, new_rate)
            sim_clock.rate = new_rate

        # Toggle diagnostics overlay
        if event.key == pygame.K_d:
            diagnostics.toggle_overlay()

    return True


def main() -> None:
    """Initialize and run the main application loop."""
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Favur Visual Test")
    pygame_clock = pygame.time.Clock()

    diagnostics = Diagnostics()
    sim_clock = SimulationClock(rate=1.0)
    simulation = Simulation(clock=sim_clock, bodies=BODIES)
    viewport = Viewport(center=Vec2(0.0, 0.0), zoom=1.0)
    renderer = Renderer(simulation=simulation, viewport=viewport)

    # Initialize SceneManager with TitleScene
    # TitleScene needs manager, simulation, and renderer
    # We create a placeholder TitleScene first, then initialize the manager
    scene_manager = SceneManager(initial_scene=None)
    initial_scene = TitleScene(
        manager=scene_manager, simulation=simulation, renderer=renderer
    )
    scene_manager.transition_to(initial_scene)

    running = True
    while running:
        # 1. Delta Time (AC-4)
        dt_ms = pygame_clock.tick(FPS_CAP)
        dt = dt_ms / 1000.0

        # 2. Performance Tracking
        diagnostics.record_frame(dt)

        # 3. Event Dispatch
        for event in pygame.event.get():
            running = handle_global_input(event, sim_clock, diagnostics, scene_manager)
            if not running:
                break
            scene_manager.handle_event(event)

        if not running:
            break

        # 4. Logic Update
        scene_manager.update(dt)

        # 5. Rendering
        scene_manager.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
