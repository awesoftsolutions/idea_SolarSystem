import math
import pytest

from src.scaling import (
    log_scale_distance,
    log_scale_size,
    get_neighborhood_bounds,
)


def test_distance_monotonicity():
    """Verify d1 > d2 => log_scale_distance(d1, base) >= log_scale_distance(d2, base)."""
    # d=0 case
    assert log_scale_distance(0.0, 10.0) == 0.0

    # Monotonicity
    d1 = 1.0
    d2 = 2.0
    s1 = log_scale_distance(d1, 10.0)
    s2 = log_scale_distance(d2, 10.0)
    assert s2 > s1

    # Large scale
    assert math.isfinite(log_scale_distance(1e12, 10.0))

    # Base parameter effect
    s_base2 = log_scale_distance(100.0, 2.0)
    s_base10 = log_scale_distance(100.0, 10.0)
    assert s_base2 != s_base10


def test_size_clamping():
    """Verify log_scale_size returns values within [MIN_BODY_PIXELS, MAX_BODY_PIXELS]."""
    min_p = 2.0
    max_p = 50.0
    base = 10.0

    # Lower bound
    assert log_scale_size(0.001, min_p, max_p, base) == min_p

    # Upper bound
    assert log_scale_size(1e15, min_p, max_p, base) == max_p

    # Zero/Negative
    assert log_scale_size(0.0, min_p, max_p, base) == min_p
    assert log_scale_size(-1.0, min_p, max_p, base) == min_p

    # Mid range
    mid = log_scale_size(1000.0, min_p, max_p, base)
    assert min_p < mid < max_p


def test_neighborhood_retrieval():
    """Verify correct bounds are returned for 'Sun' and 'Earth', and KeyError for unknown."""
    assert get_neighborhood_bounds("Sun") == 600.0
    assert get_neighborhood_bounds("Earth") == 15.0

    with pytest.raises(KeyError, match="Unknown body"):
        get_neighborhood_bounds("UnknownBody")
