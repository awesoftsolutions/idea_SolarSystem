import src.scaling_constants as sc

def test_distance_constants_types():
    assert isinstance(sc.LOG_BASE_DISTANCE, float)
    assert isinstance(sc.DISTANCE_LOG_SCALE_FACTOR, float)
    assert isinstance(sc.DISTANCE_LOG_K, float)

def test_size_constants_types():
    assert isinstance(sc.LOG_BASE_SIZE, float)
    assert isinstance(sc.MIN_BODY_PIXELS, float)
    assert isinstance(sc.MAX_BODY_PIXELS, float)
    assert isinstance(sc.SIZE_LOG_K, float)
    assert isinstance(sc.SIZE_LOG_OFFSET, float)

def test_neighborhood_types():
    assert isinstance(sc.DISPLAY_NEIGHBORHOODS, dict)
    for name, radius in sc.DISPLAY_NEIGHBORHOODS.items():
        assert isinstance(name, str)
        assert isinstance(radius, float)

def test_constant_bounds():
    assert sc.LOG_BASE_DISTANCE > 1.0
    assert sc.LOG_BASE_SIZE > 1.0
    assert sc.MIN_BODY_PIXELS >= 0.0
    assert sc.MAX_BODY_PIXELS >= sc.MIN_BODY_PIXELS
    for radius in sc.DISPLAY_NEIGHBORHOODS.values():
        assert radius >= 0.0
        assert radius <= 1440.0
