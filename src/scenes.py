# CHANGELOG:
# - Sprint 5: Implement Scene FSM with SceneManager, TitleScene, and SimulationScene.
# - Sprint 6: Implement predictive paths toggle and robust asteroid belt initialization.
# - Sprint 7: Centralize UI constants and optimize predictive path caching.

"""Scene Management & UI State Machine for the solar simulation.

This module implements a Finite State Machine (FSM) to manage different
application states such as the Title screen and the main Simulation view.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from src import constants
from src.trail import Trail

# Type hinting imports
if TYPE_CHECKING:
    from src.render import Renderer
    from src.simulation import Simulation
    from src.vector import Vec2

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
    if not pygame.font.get_init():
        pygame.font.init()
        _FONT_CACHE.clear()

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
    """Manages scene transitions and dispatches logic to the active scene.

    Attributes:
        active_scene: The currently active scene being updated and drawn.
    """

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
        """Dispatch event to the active scene if it exists.

        Args:
            event: The Pygame event to dispatch.
        """
        if self.active_scene:
            self.active_scene.handle_event(event)

    def update(self, dt: float) -> None:
        """Dispatch update to the active scene if it exists.

        Args:
            dt: The time delta since the last update.
        """
        if self.active_scene:
            self.active_scene.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Dispatch draw to the active scene if it exists.

        Args:
            surface: The Pygame surface to draw on.
        """
        if self.active_scene:
            self.active_scene.draw(surface)


class TitleScene(Scene):
    """Splash screen scene.

    Attributes:
        manager: The SceneManager instance.
        simulation: The Simulation model.
        renderer: The rendering engine.
    """

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
        """Transition to SimulationScene on SPACE.

        Args:
            event: The Pygame event to handle.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.manager and self.simulation and self.renderer:
                sim_scene = SimulationScene(self.simulation, self.renderer)
                self.manager.transition_to(sim_scene)

    def update(self, dt: float) -> None:
        """No logic for TitleScene.

        Args:
            dt: The time delta since the last update.
        """
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Render splash screen.

        Args:
            surface: The Pygame surface to draw on.
        """
        surface.fill(constants.COLOR_BLACK)

        font = _get_font("Arial", constants.FONT_SIZE_TITLE)
        title_surf = font.render("solar", True, constants.COLOR_WHITE)
        title_x = surface.get_width() // 2 - title_surf.get_width() // 2
        surface.blit(title_surf, (title_x, constants.TITLE_Y_POS))

        font_small = _get_font("Arial", constants.FONT_SIZE_SMALL)
        prompt_surf = font_small.render(
            "Press SPACE to Start", True, constants.COLOR_PROMPT
        )
        prompt_x = surface.get_width() // 2 - prompt_surf.get_width() // 2
        surface.blit(prompt_surf, (prompt_x, constants.PROMPT_Y_POS))


class SimulationScene(Scene):
    """Main simulation view scene.

    Attributes:
        simulation: The simulation model.
        renderer: The rendering engine.
        is_paused: Whether the simulation time is currently frozen.
        show_predictions: Whether future orbit paths are displayed.
        _asteroid_set: Cached set of asteroid names for fast lookup.
        _predictive_paths: Cached future trajectory segments.
        _last_predictive_update_t: Last time the predictive paths were updated.
        _trails: Dictionary of historical position trails for each body.
    """

    def __init__(self, simulation: Simulation, renderer: Renderer) -> None:
        """Initialize SimulationScene.

        Args:
            simulation: The simulation model.
            renderer: The rendering engine.

        Returns:
            None
        """
        self.simulation = simulation
        self.renderer = renderer
        self.is_paused = False
        self.show_predictions = False

        # Cache for asteroid set to avoid repeated lookups in draw()
        groups = self.simulation.bodies.get_groups()
        self._asteroid_set = set(groups.get("AsteroidBelt") or [])

        # Cache for predictive paths to avoid heavy calculations in draw()
        self._predictive_paths: dict[str, list[Vec2]] = {}
        self._last_predictive_update_t: float | None = None

        # Initialize trails for each body
        self._trails: dict[str, Trail] = {}
        body_names = self.simulation.bodies.list_bodies()
        for name in body_names:
            # Initialize trail with configured capacity.
            self._trails[name] = Trail(capacity=constants.TRAIL_CAPACITY)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Toggle pause on 'P' and predictions on 'F'.

        Args:
            event: The Pygame event to handle.

        Returns:
            None
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.is_paused = not self.is_paused
            elif event.key == pygame.K_f:
                self.show_predictions = not self.show_predictions

    def update(self, dt: float) -> None:
        """Update simulation clock and trails if not paused.

        Args:
            dt: The time delta since the last update.

        Returns:
            None
        """
        if not self.is_paused:
            self.simulation.clock.update(dt)

        # Record current positions in trails
        t = self.simulation.clock.t_sim
        state = self.simulation.get_system_state(t)
        for name, pos in state.items():
            if name in self._trails:
                self._trails[name].append(pos, t)

        # Update predictive paths if enabled and time has changed
        if self.show_predictions and t != self._last_predictive_update_t:
            self._predictive_paths.clear()
            all_body_names = self.simulation.bodies.list_bodies()
            for name in all_body_names:
                if name in self._asteroid_set:
                    continue

                body_data = self.simulation.bodies.get_body(name)
                # Skip bodies without orbital period T
                if "T" not in body_data:
                    continue

                period = float(body_data["T"])
                self._predictive_paths[name] = self.simulation.get_future_path(
                    name,
                    t,
                    duration=period * constants.PREDICTION_DURATION_FRACTION,
                    steps=constants.PREDICTION_STEPS,
                )
            self._last_predictive_update_t = t

    def draw(self, surface: pygame.Surface) -> None:
        """Dispatch draw calls to Renderer and draw UI overlays.

        Args:
            surface: The Pygame surface to draw on.

        Returns:
            None
        """
        surface.fill(constants.COLOR_BLACK)

        all_body_names = self.simulation.bodies.list_bodies()
        t_sim = self.simulation.clock.get_time()

        # Phase 1: Major Bodies (Orbits, Trails, Bodies)
        for name in all_body_names:
            if name in self._asteroid_set:
                continue

            self.renderer.draw_orbit_path(surface, name)
            if name in self._trails:
                self.renderer.draw_trail(surface, name, self._trails[name])
            self.renderer.draw_body(surface, name)

        # Phase 2: Optimized Asteroid Belt
        self.renderer.draw_asteroid_belt(surface, self._trails)

        # UI Overlays
        rate = self.simulation.clock.rate

        # Phase 3: Predictive Previews (using cached paths from update)
        if self.show_predictions:
            for name, path in self._predictive_paths.items():
                self.renderer.draw_predictive_trail(surface, name, path)

        font = _get_font("Arial", constants.FONT_SIZE_UI)
        time_surf = font.render(f"Time: {t_sim:.2f}", True, constants.COLOR_WHITE)
        rate_surf = font.render(f"Rate: {rate:.1f}x", True, constants.COLOR_WHITE)

        surface.blit(time_surf, (constants.UI_MARGIN_X, constants.UI_MARGIN_Y))
        surface.blit(
            rate_surf,
            (constants.UI_MARGIN_X, constants.UI_MARGIN_Y + constants.UI_SPACING_Y),
        )

        if self.is_paused:
            pause_surf = font.render("PAUSED", True, constants.COLOR_PAUSE)
            surface.blit(
                pause_surf,
                (surface.get_width() - constants.PAUSE_X_OFFSET, constants.UI_MARGIN_Y),
            )
