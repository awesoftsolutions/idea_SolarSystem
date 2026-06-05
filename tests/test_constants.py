"""Unit tests for the centralized constants module."""
import sys
import pytest
from src import constants

def test_constants_accessibility():
    """Verify all required constants are accessible from src.constants."""
    # MATH
    assert hasattr(constants, "SOLVER_TOLERANCE")
    assert hasattr(constants, "MAX_ITERATIONS")
    assert hasattr(constants, "AU_TO_KM")
    assert hasattr(constants, "SUN_POS_THRESHOLD")

    # VIEWPORT
    assert hasattr(constants, "WINDOW_SIZE")
    assert hasattr(constants, "FPS_CAP")
    assert hasattr(constants, "MIN_RATE")
    assert hasattr(constants, "MAX_RATE")
    assert hasattr(constants, "DIAGNOSTICS_WINDOW")

    # RENDERING
    assert hasattr(constants, "TRAIL_CAPACITY")
    assert hasattr(constants, "TRAIL_ALPHA_MIN")
    assert hasattr(constants, "TRAIL_ALPHA_MAX")
    assert hasattr(constants, "PREDICTION_ALPHA")
    assert hasattr(constants, "PREDICTION_DURATION_FRACTION")
    assert hasattr(constants, "PREDICTION_STEPS")
    assert hasattr(constants, "ORBIT_GLOW_WIDTH_OUTER")
    assert hasattr(constants, "ORBIT_GLOW_WIDTH_INNER")
    assert hasattr(constants, "ORBIT_GLOW_ALPHA_OUTER")
    assert hasattr(constants, "ORBIT_GLOW_ALPHA_INNER")
    assert hasattr(constants, "ORBIT_CORE_ALPHA")
    assert hasattr(constants, "ADAPTIVE_SAMPLING_DIVISOR")
    assert hasattr(constants, "MIN_ORBIT_POINTS")
    assert hasattr(constants, "MAX_ORBIT_POINTS")
    assert hasattr(constants, "LOD_ZOOM_THRESHOLD")

    # UI
    assert hasattr(constants, "COLOR_BLACK")
    assert hasattr(constants, "COLOR_WHITE")
    assert hasattr(constants, "COLOR_PROMPT")
    assert hasattr(constants, "COLOR_PAUSE")
    assert hasattr(constants, "FONT_SIZE_TITLE")
    assert hasattr(constants, "FONT_SIZE_SMALL")
    assert hasattr(constants, "FONT_SIZE_UI")
    assert hasattr(constants, "UI_MARGIN_X")
    assert hasattr(constants, "UI_MARGIN_Y")
    assert hasattr(constants, "UI_SPACING_Y")
    assert hasattr(constants, "TITLE_Y_POS")
    assert hasattr(constants, "PROMPT_Y_POS")
    assert hasattr(constants, "PAUSE_X_OFFSET")

    # SCALING
    assert hasattr(constants, "LOG_BASE_DISTANCE")
    assert hasattr(constants, "DISTANCE_LOG_SCALE_FACTOR")
    assert hasattr(constants, "DISTANCE_LOG_K")
    assert hasattr(constants, "LOG_BASE_SIZE")
    assert hasattr(constants, "MIN_BODY_PIXELS")
    assert hasattr(constants, "MAX_BODY_PIXELS")
    assert hasattr(constants, "SIZE_LOG_K")
    assert hasattr(constants, "SIZE_LOG_OFFSET")
    assert hasattr(constants, "DISPLAY_NEIGHBORHOODS")
    assert hasattr(constants, "SUN_NEIGHBORHOOD_REF")
    assert hasattr(constants, "FALLBACK_NEIGHBORHOOD_REF")

def test_constants_types():
    """Verify the types of the constants."""
    assert isinstance(constants.SOLVER_TOLERANCE, float)
    assert isinstance(constants.MAX_ITERATIONS, int)
    assert isinstance(constants.WINDOW_SIZE, tuple)
    assert len(constants.WINDOW_SIZE) == 2
    assert isinstance(constants.COLOR_BLACK, tuple)
    assert len(constants.COLOR_BLACK) == 3
    assert isinstance(constants.TRAIL_CAPACITY, int)
    assert isinstance(constants.DISPLAY_NEIGHBORHOODS, dict)

def test_constants_ranges():
    """Verify range constraints for specific constants."""
    # Alphas
    alphas = [
        constants.TRAIL_ALPHA_MIN,
        constants.TRAIL_ALPHA_MAX,
        constants.PREDICTION_ALPHA,
        constants.ORBIT_GLOW_ALPHA_OUTER,
        constants.ORBIT_GLOW_ALPHA_INNER,
        constants.ORBIT_CORE_ALPHA
    ]
    for alpha in alphas:
        assert 0 <= alpha <= 255

    # Simulation rates
    assert constants.MAX_RATE > constants.MIN_RATE > 0

    # Window dimensions
    assert constants.WINDOW_SIZE[0] > 0
    assert constants.WINDOW_SIZE[1] > 0

    # Capacities and steps
    assert constants.TRAIL_CAPACITY > 0
    assert constants.PREDICTION_STEPS > 0

def test_no_pygame_import():
    """Verify that importing src.constants does not import pygame."""
    # Ensure constants is imported (already done at module level, but for clarity)
    _ = constants.SOLVER_TOLERANCE
    
    # Check sys.modules for pygame
    assert "pygame" not in sys.modules, "Importing src.constants should not trigger a pygame import."
