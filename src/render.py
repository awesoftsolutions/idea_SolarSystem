# CHANGELOG:
# - Sprint 5: Implement Renderer class for Pygame-based visualization.
# - Sprint 6: Implement exponential trail decay and glowing orbit paths.

"""Pygame-specific drawing routines for bodies, orbits, and trails."""

from __future__ import annotations
import math
import pygame
import pygame.gfxdraw
from src.simulation import Simulation
from src.vector import Vec2
from src.viewport import Viewport, world_to_screen
from src.scaling import (
    map_to_screen,
    map_to_world,
    scale_orbit_geometry,
    log_scale_size,
)
from src.frames import Frame
from src.trail import Trail
from src.scaling_constants import MIN_BODY_PIXELS, MAX_BODY_PIXELS, LOG_BASE_SIZE


class Renderer:
    """Handles Pygame visualization of the solar system simulation.

    Attributes:
        simulation: The Simulation instance providing system state.
        viewport: The Viewport instance for coordinate transformations.
    """

    def __init__(self, simulation: Simulation, viewport: Viewport) -> None:
        """Initialize the Renderer with simulation and viewport.

        Args:
            simulation: Simulation instance.
            viewport: Viewport instance.

        Returns:
            None
        """
        self.simulation = simulation
        self.viewport = viewport
        self._sprite_cache: dict[tuple[tuple[int, int, int], int], pygame.Surface] = {}

    def _get_asteroid_sprite(
        self, color: tuple[int, int, int], radius_px: int
    ) -> pygame.Surface:
        """Retrieve a cached asteroid sprite or create a new one.

        Args:
            color: RGB color tuple.
            radius_px: Radius in pixels.

        Returns:
            A Pygame surface containing the asteroid sprite.
        """
        key = (color, radius_px)
        if key in self._sprite_cache:
            return self._sprite_cache[key]

        size = max(1, radius_px * 2)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (radius_px, radius_px), radius_px)
        self._sprite_cache[key] = surface
        return surface

    def draw_asteroid_belt(
        self, surface: pygame.Surface, trails: dict[str, Trail]
    ) -> None:
        """Perform optimized batch rendering of the asteroid belt.

        Args:
            surface: The Pygame surface to draw on.
            trails: Dictionary of Trail instances.

        Returns:
            None
        """
        groups = self.simulation.bodies.get_groups()
        asteroid_names = groups.get("AsteroidBelt", [])

        if not asteroid_names:
            return

        batch_list = []
        t = self.simulation.clock.t_sim
        state = self.simulation.get_system_state(t)
        zoom = self.viewport.zoom

        for name in asteroid_names:
            if name not in state:
                continue
            actual_pos = state[name]

            # 1. LOD for Trails
            if zoom > 2.0 and name in trails:
                self.draw_trail(surface, name, trails[name])

            # 2. Coordinate Mapping
            frame_context = Frame(name, t)
            screen_pos = map_to_screen(actual_pos, frame_context, self.viewport)

            # 3. Sprite Selection
            body_data = self.simulation.bodies.get_body(name)
            radius_km = body_data["radius"]
            radius_px = log_scale_size(
                radius_km, MIN_BODY_PIXELS, MAX_BODY_PIXELS, LOG_BASE_SIZE
            )
            sprite = self._get_asteroid_sprite(body_data["color"], int(radius_px))

            # 4. Batch Collection
            blit_pos = (int(screen_pos.x - radius_px), int(screen_pos.y - radius_px))
            batch_list.append((sprite, blit_pos))

        # 5. Batch Execution
        if batch_list:
            surface.blits(batch_list)

    def draw_body(self, surface: pygame.Surface, body_name: str) -> None:
        """Draw a body as a colored circle at its scaled screen position.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body to draw.

        Returns:
            None
        """
        body_data = self.simulation.bodies.get_body(body_name)
        t = self.simulation.clock.t_sim
        state = self.simulation.get_system_state(t)
        actual_pos = state[body_name]

        frame_context = Frame(body_name, t)
        screen_pos = map_to_screen(actual_pos, frame_context, self.viewport)

        radius_km = body_data["radius"]
        radius_px = log_scale_size(
            radius_km, MIN_BODY_PIXELS, MAX_BODY_PIXELS, LOG_BASE_SIZE
        )

        color = body_data["color"]
        # Convert Vec2 to tuple for pygame.draw.circle compatibility
        pos_tuple = (int(screen_pos.x), int(screen_pos.y))
        pygame.draw.circle(surface, color, pos_tuple, int(radius_px))

    def draw_orbit_path(self, surface: pygame.Surface, body_name: str) -> None:
        """Draw the glowing elliptical orbit path with adaptive sampling.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body whose orbit to draw.

        Returns:
            None
        """
        body_data = self.simulation.bodies.get_body(body_name)
        primary_name = body_data.get("primary")
        if primary_name is None:
            return

        t = self.simulation.clock.t_sim
        orbit_geo = scale_orbit_geometry(body_data)

        state = self.simulation.get_system_state(t)
        primary_abs_pos = state[primary_name]

        primary_frame = Frame(primary_name, t)
        primary_world_pos = map_to_world(primary_abs_pos, primary_frame)

        world_center = primary_world_pos + orbit_geo["center_offset"]
        screen_center = world_to_screen(world_center, self.viewport)

        a_v = orbit_geo["a_v"]
        b_v = orbit_geo["b_v"]
        orientation = orbit_geo["orientation"]

        # Adaptive Sampling based on screen-space circumference
        # Approx circumference: 2 * pi * sqrt((a^2 + b^2) / 2)
        circumference_px = 2 * math.pi * math.sqrt((a_v**2 + b_v**2) / 2.0)
        num_points = max(64, min(1024, int(circumference_px / 5.0)))

        points = []
        cos_o = math.cos(orientation)
        sin_o = math.sin(orientation)

        # Pre-calculate trig values for the loop
        for i in range(num_points):
            theta = 2.0 * math.pi * i / num_points
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)

            lx = a_v * cos_t
            ly = b_v * sin_t

            rx = lx * cos_o - ly * sin_o
            ry = lx * sin_o + ly * cos_o

            points.append((int(screen_center.x + rx), int(screen_center.y + ry)))

        base_color = body_data["color"]

        # Multi-pass Glow Rendering
        # Pass 1: Outer glow (Wide, low alpha)
        glow_color_1 = (base_color[0], base_color[1], base_color[2], 32)
        pygame.draw.lines(surface, glow_color_1, True, points, width=3)

        # Pass 2: Inner glow (Medium, medium alpha)
        glow_color_2 = (base_color[0], base_color[1], base_color[2], 64)
        pygame.draw.lines(surface, glow_color_2, True, points, width=2)

        # Pass 3: Anti-aliased Core (1px, high alpha)
        core_color = (base_color[0], base_color[1], base_color[2], 128)
        pygame.gfxdraw.aapolygon(surface, points, core_color)

    def draw_trail(self, surface: pygame.Surface, body_name: str, trail: Trail) -> None:
        """Draw the trail with exponential alpha decay for smooth visual fading.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body.
            trail: The Trail instance containing historical positions.

        Returns:
            None
        """
        points = trail.get_points()
        num_points = len(points)
        if num_points < 2:
            return

        t = self.simulation.clock.t_sim
        body_data = self.simulation.bodies.get_body(body_name)
        base_color = body_data["color"]

        # Calculate exponential decay constant k such that alpha_min = 5.0
        alpha_min = 5.0
        # alpha = 255 * exp(-k * distance_from_head)
        # 5 = 255 * exp(-k * (N-1)) => k = ln(255/5) / (N-1)
        k = math.log(255.0 / alpha_min) / (num_points - 1)

        # Use a consistent frame context for all points in the trail
        # to ensure they are mapped relative to the same reference frame.
        frame_context = Frame(body_name, t)
        s1 = map_to_screen(points[0], frame_context, self.viewport)

        for i in range(num_points - 1):
            # For performance testing or generic bodies, use the body_name
            # provided to the method for the frame context.
            s2 = map_to_screen(points[i + 1], frame_context, self.viewport)

            # i+1 is the index of the 'head' of the current segment
            # Newest point in trail is at index num_points - 1
            distance_from_head = (num_points - 1) - (i + 1)
            alpha = int(255 * math.exp(-k * distance_from_head))
            color = (base_color[0], base_color[1], base_color[2], alpha)

            pygame.gfxdraw.line(
                surface, int(s1.x), int(s1.y), int(s2.x), int(s2.y), color
            )
            s1 = s2

    def draw_predictive_trail(
        self, surface: pygame.Surface, body_name: str, path: list[Vec2]
    ) -> None:
        """Draw a predictive future path for a body with a dashed visual style.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body.
            path: A list of future absolute positions.

        Returns:
            None
        """
        if len(path) < 2:
            return

        t = self.simulation.clock.t_sim
        body_data = self.simulation.bodies.get_body(body_name)
        base_color = body_data["color"]
        # Semi-transparent color for the predictive trail (alpha=100)
        trail_color = (base_color[0], base_color[1], base_color[2], 100)

        # Use the current body's frame context for consistent mapping
        frame_context = Frame(body_name, t)

        # Optimization: Pre-map all points to screen space to avoid redundant calculations
        screen_points = [map_to_screen(p, frame_context, self.viewport) for p in path]

        for i in range(len(screen_points) - 1):
            # Dashed effect: only draw even-indexed segments
            if i % 2 != 0:
                continue

            s1 = screen_points[i]
            s2 = screen_points[i + 1]

            # Use gfxdraw.line for proper alpha blending support
            pygame.gfxdraw.line(
                surface,
                int(s1.x),
                int(s1.y),
                int(s2.x),
                int(s2.y),
                trail_color,
            )
