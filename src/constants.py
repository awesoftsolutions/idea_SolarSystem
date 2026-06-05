# CHANGELOG:
# - Sprint 1: Define mathematical constants for solver tolerance and iterations.
# - Sprint 5: Add DIAGNOSTICS_WINDOW for performance monitoring.

"""Mathematical and physical constants for the solar system simulation."""

# Mathematical constants for the Keplerian simulation
SOLVER_TOLERANCE = 1e-9
MAX_ITERATIONS = 100

# Physical constants
AU_TO_KM: float = 149597870.7

# Viewport constants
WINDOW_SIZE: tuple[int, int] = (1440, 1080)

# Diagnostics constants
DIAGNOSTICS_WINDOW = 60

# Simulation rate and performance constants
MIN_RATE = 0.1
MAX_RATE = 10000.0
FPS_CAP = 60
