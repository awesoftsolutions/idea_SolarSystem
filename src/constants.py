# CHANGELOG:
# - Sprint 1: Define mathematical constants for solver tolerance and iterations.
# - Sprint 5: Add DIAGNOSTICS_WINDOW for performance monitoring.
# - Sprint 7: Centralize all hardcoded constants from render, scenes, and scaling.

"""Mathematical and physical constants for the solar system simulation."""

# Group: MATH
SOLVER_TOLERANCE: float = 1e-9
"""Tolerance for Kepler solver convergence."""

MAX_ITERATIONS: int = 100
"""Maximum iterations for Kepler solver."""

AU_TO_KM: float = 149597870.7
"""Conversion factor from Astronomical Units to kilometers."""

YEAR_TO_DAY: float = 365.25
"""Conversion factor from years to days."""

SUN_POS_THRESHOLD: float = 1e-3
"""Threshold for treating position as Sun-center."""

# Group: VIEWPORT
WINDOW_SIZE: tuple[int, int] = (1440, 1080)
"""Default application window dimensions."""

FPS_CAP: int = 60
"""Target frames per second."""

MIN_RATE: float = 0.1
"""Minimum simulation time rate."""

MAX_RATE: float = 10000.0
"""Maximum simulation time rate."""

DIAGNOSTICS_WINDOW: int = 60
"""Number of frames for performance averaging."""

# Group: RENDERING
TRAIL_CAPACITY: int = 100
"""Number of points kept in body trails."""

TRAIL_ALPHA_MIN: float = 5.0
"""Minimum alpha value for trail tail."""

TRAIL_ALPHA_MAX: float = 255.0
"""Maximum alpha value for trail head."""

PREDICTION_ALPHA: int = 100
"""Alpha value for predictive path drawing."""

PREDICTION_DURATION_FRACTION: float = 0.25
"""Fraction of orbital period to predict."""

PREDICTION_STEPS: int = 20
"""Number of segments in predictive path."""

ORBIT_GLOW_WIDTH_OUTER: int = 3
"""Width of the outer orbit glow pass."""

ORBIT_GLOW_WIDTH_INNER: int = 2
"""Width of the inner orbit glow pass."""

ORBIT_GLOW_ALPHA_OUTER: int = 32
"""Alpha of the outer orbit glow pass."""

ORBIT_GLOW_ALPHA_INNER: int = 64
"""Alpha of the inner orbit glow pass."""

ORBIT_CORE_ALPHA: int = 128
"""Alpha of the anti-aliased orbit core."""

ADAPTIVE_SAMPLING_DIVISOR: float = 5.0
"""Pixels per sample for adaptive orbit drawing."""

MIN_ORBIT_POINTS: int = 64
"""Minimum points for orbit drawing."""

MAX_ORBIT_POINTS: int = 1024
"""Maximum points for orbit drawing."""

LOD_ZOOM_THRESHOLD: float = 2.0
"""Zoom level above which trails are drawn for asteroids."""

# Group: UI
COLOR_BLACK: tuple[int, int, int] = (0, 0, 0)
"""Background color."""

COLOR_WHITE: tuple[int, int, int] = (255, 255, 255)
"""Primary text color."""

COLOR_PROMPT: tuple[int, int, int] = (200, 200, 200)
"""Secondary/prompt text color."""

COLOR_PAUSE: tuple[int, int, int] = (255, 100, 100)
"""Pause indicator color."""

FONT_SIZE_TITLE: int = 64
"""Font size for the main title."""

FONT_SIZE_SMALL: int = 24
"""Font size for prompts."""

FONT_SIZE_UI: int = 18
"""Font size for UI overlays."""

UI_MARGIN_X: int = 10
"""Horizontal margin for UI elements."""

UI_MARGIN_Y: int = 10
"""Vertical margin for UI elements."""

UI_SPACING_Y: int = 20
"""Vertical spacing between UI lines."""

TITLE_Y_POS: int = 200
"""Y position for the main title."""

PROMPT_Y_POS: int = 400
"""Y position for the start prompt."""

PAUSE_X_OFFSET: int = 80
"""Right-aligned margin for the pause indicator."""

# Group: SCALING (Merged from scaling_constants.py)
LOG_BASE_DISTANCE: float = 10.0
"""Base for logarithmic distance mapping."""

DISTANCE_LOG_SCALE_FACTOR: float = 1.0
"""Reference distance factor."""

DISTANCE_LOG_K: float = 335.0
"""Scaling coefficient for viewport fit."""

LOG_BASE_SIZE: float = 10.0
"""Base for shared logarithmic size law."""

MIN_BODY_PIXELS: float = 2.0
"""Minimum body display size."""

MAX_BODY_PIXELS: float = 50.0
"""Maximum body display size."""

SIZE_LOG_K: float = 10.0
"""Slope for the size log law."""

SIZE_LOG_OFFSET: float = -8.4
"""Offset for the size log law."""

DISPLAY_NEIGHBORHOODS: dict[str, float] = {
    "Sun": 600.0,
    "Earth": 80.0,
    "Jupiter": 150.0,
    "Saturn": 120.0,
    "Mars": 40.0,
    "Neptune": 60.0,
}
"""Capped radii for each primary body's display neighborhood to prevent overlap."""

SUN_NEIGHBORHOOD_REF: float = 30.0
"""Reference distance for Sun neighborhood."""

FALLBACK_NEIGHBORHOOD_REF: float = 1000.0
"""Fallback reference distance."""
