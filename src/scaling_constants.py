"""Scaling constants for the hierarchical logarithmic scaling system."""

# Distance Scaling Parameters
# Base for the logarithmic distance mapping within each reference frame.
LOG_BASE_DISTANCE: float = 10.0

# Reference distance factor (1.0 AU for Sun-centered orbits, 1.0 km for others).
DISTANCE_LOG_SCALE_FACTOR: float = 1.0

# Scaling coefficient to ensure the furthest body (Neptune) fits within the 1440x1080 viewport.
DISTANCE_LOG_K: float = 335.0

# Size Scaling Parameters
# Base for the shared logarithmic size law.
LOG_BASE_SIZE: float = 10.0

# Minimum and maximum body display sizes in pixels.
MIN_BODY_PIXELS: float = 2.0
MAX_BODY_PIXELS: float = 50.0

# Slope (K) and Offset for the size log law: pixels = K * log(radius) + Offset.
# Chosen to map Phobos (~11km) to ~2px and the Sun (~696k km) to ~50px.
SIZE_LOG_K: float = 10.0
SIZE_LOG_OFFSET: float = -8.4

# Display Neighborhoods (Radii in pixels)
# Capped radii for each primary body's display neighborhood to prevent overlap.
# UPDATED: Increased radii to prevent visual occlusion of moons by their primaries.
DISPLAY_NEIGHBORHOODS: dict[str, float] = {
    "Sun": 600.0,
    "Earth": 80.0,
    "Jupiter": 150.0,
    "Saturn": 120.0,
    "Mars": 40.0,
    "Neptune": 60.0,
}