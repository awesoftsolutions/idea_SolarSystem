# CHANGELOG:
# - Sprint 5: Implement Renderer class for Pygame-based visualization.

"""Pygame-specific drawing routines for bodies, orbits, and trails."""

from __future__ import annotations
import math
import pygame
import pygame.gfxdraw
from src.simulation import Simulation
from src.viewport import Viewport, world_to_screen
from src.scaling import map_to_screen, map_to_world, scale_orbit_geometry, log_scale_size
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
        """
        self.simulation = simulation
        self.viewport = viewport

    def draw_body(self, surface: pygame.Surface, body_name: str) -> None:
        """Draw a body as a colored circle at its scaled screen position.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body to draw.
        """
        body_data = self.simulation.bodies.get_body(body_name)
        t = self.simulation.clock.t_sim
        state = self.simulation.get_system_state(t)
        actual_pos = state[body_name]

        frame_context = Frame(body_name, t)
        screen_pos = map_to_screen(actual_pos, frame_context, self.viewport)

        radius_km = body_data["radius"]
        radius_px = log_scale_size(radius_km, MIN_BODY_PIXELS, MAX_BODY_PIXELS, LOG_BASE_SIZE)

        color = body_data["color"]
        pygame.draw.circle(surface, color, screen_pos, radius_px)

    def draw_orbit_path(self, surface: pygame.Surface, body_name: str) -> None:
        """Draw the faint elliptical orbit path for a body using polygon approximation.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body whose orbit to draw.
        """
        body_data = self.simulation.bodies.get_body(body_name)
        primary_name = body_data.get("primary")
        if primary_name is None:
            return  # Sun or bodies without primary have no orbit

        t = self.simulation.clock.t_sim
        orbit_geo = scale_orbit_geometry(body_data)

        state = self.simulation.get_system_state(t)
        primary_abs_pos = state[primary_name]

        primary_frame = Frame(primary_name, t)
        primary_world_pos = map_to_world(primary_abs_pos, primary_frame)

        # Calculate visual center in world space
        world_center = primary_world_pos + orbit_geo["center_offset"]
        screen_center = world_to_screen(world_center, self.viewport)

        # Orbit color (body color with low alpha)
        base_color = body_data["color"]
        color = (base_color[0], base_color[1], base_color[2], 64)

        # Polygon approximation for rotated ellipse
        num_points = 128
        points = []
        a_v = orbit_geo["a_v"]
        b_v = orbit_geo["b_v"]
        orientation = orbit_geo["orientation"]
        
        cos_o = math.cos(orientation)
        sin_o = math.sin(orientation)

        for i in range(num_points):
            theta = 2.0 * math.pi * i / num_points
            # Local ellipse coordinates
            lx = a_v * math.cos(theta)
            ly = b_v * math.sin(theta)
            
            # Rotate by orientation
            rx = lx * cos_o - ly * sin_o
            ry = lx * sin_o + ly * cos_o
            
            # Translate to screen center
            points.append((int(screen_center.x + rx), int(screen_center.y + ry)))

        pygame.gfxdraw.aapolygon(surface, points, color)
        pygame.gfxdraw.polygon(surface, points, color)

    def draw_trail(self, surface: pygame.Surface, body_name: str, trail: Trail) -> None:
        """Draw the fading trail behind a body with optimized coordinate mapping.

        Args:
            surface: The Pygame surface to draw on.
            body_name: The name of the body.
            trail: The Trail instance containing historical positions.
        """
        points = trail.get_points()
        num_points = len(points)
        if num_points < 2:
            return

        t = self.simulation.clock.t_sim
        body_data = self.simulation.bodies.get_body(body_name)
        base_color = body_data["color"]
        frame_context = Frame(body_name, t)

        # Cache the first point's screen position
        s1 = map_to_screen(points[0], frame_context, self.viewport)
        
        for i in range(num_points - 1):
            # The next point's screen position
            s2 = map_to_screen(points[i + 1], frame_context, self.viewport)

            alpha = int(255 * (i + 1) / num_points)
            color = (base_color[0], base_color[1], base_color[2], alpha)

            pygame.gfxdraw.line(
                surface, 
                int(s1.x), int(s1.y), 
                int(s2.x), int(s2.y), 
                color
            )
            # Current s2 becomes s1 for the next segment
            s1 = s2