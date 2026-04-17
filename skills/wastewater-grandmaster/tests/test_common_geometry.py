import math
from common.geometry import (
    circular_pipe_area,
    hydraulic_radius_circular,
    trapezoidal_channel_area,
    trapezoidal_channel_hydraulic_radius,
)


def test_circular_pipe_area_half_full():
    # At h/D = 0.5, area should be pi/8 * D^2 (half circle area)
    D = 1.0
    area = circular_pipe_area(D, 0.5)
    expected = (math.pi / 8) * D ** 2
    assert abs(area - expected) < 1e-6


def test_hydraulic_radius_half_full():
    D = 1.0
    R = hydraulic_radius_circular(D, 0.5)
    assert abs(R - 0.25) < 1e-6


def test_trapezoidal_channel_area():
    # bottom 1m, slope 2:1, depth 0.5m -> (1 + 2*0.5)*0.5 = 1.0
    area = trapezoidal_channel_area(1.0, 2.0, 0.5)
    assert abs(area - 1.0) < 1e-6


def test_trapezoidal_channel_hydraulic_radius():
    area = trapezoidal_channel_area(1.0, 2.0, 0.5)
    perimeter = 1.0 + 2 * (0.5 * math.sqrt(1 + 2 ** 2))
    expected_R = area / perimeter
    R = trapezoidal_channel_hydraulic_radius(1.0, 2.0, 0.5)
    assert abs(R - expected_R) < 1e-6
