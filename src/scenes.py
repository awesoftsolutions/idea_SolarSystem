# CHANGELOG:
# - Sprint 5: Implement Scene FSM with SceneManager, TitleScene, and SimulationScene.

"""Scene Management & UI State Machine for the solar simulation.

This module implements a Finite State Machine (FSM) to manage different
application states such as the Title screen and the main Simulation view.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from src.trail import Trail

# Type hinting imports
if TYPE_CHECKING:
    from src.render import Renderer
    from src.simulation import Simulation

# Module-level font cache
_FONT_CACHE: dict[tuple[str, int], pygame.font.Font] = {}


def _get_font(name: str, size: int) -> pygame.font.Font:
    """Retrieve a font from the cache or initialize it if not present.

    Args:
        name: The name of the font (e.g., "Arial").
        size: The font size in pixels.

    Returns:
        A Pygame Font instance.
    """
    key = (name, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(name, size)
    return _FONT_CACHE[key]


class Scene(ABC):
    """Abstract base class for all application scenes."""

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle Pygame events."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update scene logic."""
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the scene to the surface."""
        pass


class SceneManager:
    """Manages scene transitions and dispatches logic to the active scene."""

    def __init__(self, initial_scene: Scene | None = None) -> None:
        """Initialize with an optional initial scene.

        Args:
            initial_scene: The first scene to display, or None to set later.
        """
        self.active_scene = initial_scene

    def transition_to(self, new_scene: Scene) -> None:
        """Transition to a new scene.

        Args:
            new_scene: The scene to transition to.
        """
        self.active_scene = new_scene

    def handle_event(self, event: pygame.event.Event) -> None:
        """Dispatch event to the active scene if it exists."""
        if self.active_scene:
            self.active_scene.handle_event(event)

    def update(self, dt: float) -> None:
        """Dispatch update to the active scene if it exists."""
        if self.active_scene:
            self.active_scene.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Dispatch draw to the active scene if it exists."""
        if self.active_scene:
            self.active_scene.draw(surface)


class TitleScene(Scene):
    """Splash screen scene."""

    def __init__(
        self,
        manager: SceneManager | None = None,
        simulation: Simulation | None = None,
        renderer: Renderer | None = None,
    ) -> None:
        """Initialize TitleScene.

        Args:
            manager: The SceneManager instance.
            simulation: The Simulation model.
            renderer: The rendering engine.
        """
        self.manager = manager
        self.simulation = simulation
        self.renderer = renderer

    def handle_event(self, event: pygame.event.Event) -> None:
        """Transition to SimulationScene on SPACE."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.manager and self.simulation and self.renderer:
                sim_scene = SimulationScene(self.simulation, self.renderer)
                self.manager.transition_to(sim_scene)

    def update(self, dt: float) -> None:
        """No logic for TitleScene."""
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Render splash screen."""
        surface.fill((0, 0, 0))

        font = _get_font("Arial", 64)
        title_surf = font.render("solar", True, (255, 255, 255))
        surface.blit(
            title_surf,
            (surface.get_width() // 2 - title_surf.get_width() // 2, 200),
        )

        font_small = _get_font("Arial", 24)
        prompt_surf = font_small.render(
            "Press SPACE to Start", True, (200, 200, 200)
        )
        surface.blit(
            prompt_surf,
            (surface.get_width() // 2 - prompt_surf.get_width() // 2, 400),
        )


class SimulationScene(Scene):
    """Main simulation view scene."""

    def __init__(self, simulation: Simulation, renderer: Renderer) -> None:
        """Initialize SimulationScene.

        Args:
            simulation: The simulation model.
            renderer: The rendering engine.
        """
        self.simulation = simulation
        self.renderer = renderer
        self.is_paused = False

        # Initialize trails for each body
        self._trails: dict[str, Trail] = {}
        body_names = self.simulation.bodies.list_bodies()
        for name in body_names:
            # Capacity of 100 points for the trail
            self._trails[name] = Trail(capacity=100)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Toggle pause on 'P'."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.is_paused = not self.is_paused

    def update(self, dt: float) -> None:
        """Update simulation clock and trails if not paused."""
        if not self.is_paused:
            self.simulation.clock.update(dt)

            # Record current positions in trails
            t = self.simulation.clock.t_sim
            state = self.simulation.get_system_state(t)
            for name, pos in state.items():
                if name in self._trails:
                    self._trails[name].append(pos)

    def draw(self, surface: pygame.Surface) -> None:
        """Dispatch draw calls to Renderer and draw UI overlays."""
        surface.fill((0, 0, 0))

        body_names = self.simulation.bodies.list_bodies()
        for name in body_names:
            self.renderer.draw_orbit_path(surface, name)
            if name in self._trails:
                self.renderer.draw_trail(surface, name, self._trails[name])
            self.renderer.draw_body(surface, name)

        # UI Overlays
        t_sim = self.simulation.clock.get_time()
        rate = self.simulation.clock.rate

        font = _get_font("Arial", 18)
        time_surf = font.render(f"Time: {t_sim:.2f}", True, (255, 255, 255))
        rate_surf = font.render(f"Rate: {rate:.1f}x", True, (255, 255, 255))

        surface.blit(time_surf, (10, 10))
        surface.blit(rate_surf, (10, 30))

        if self.is_paused:
            pause_surf = font.render("PAUSED", True, (255, 100, 100))
            surface.blit(pause_surf, (surface.get_width() - 80, 10))