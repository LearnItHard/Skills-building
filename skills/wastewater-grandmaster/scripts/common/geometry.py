"""
Geometry calculation functions for wastewater hydraulic calculations.

This module provides geometric calculations for:
- Circular pipes: cross-sectional area by fullness ratio, hydraulic radius
- Trapezoidal channels: cross-sectional area
"""

import math
from typing import Union


def circular_pipe_area(diameter_m: float, fullness_ratio: float) -> float:
    """
    Calculate the cross-sectional area of a circular pipe at a given fullness.
    
    For a circular pipe flowing partially full, the wetted area is calculated
    based on the angle subtended by the water surface.
    
    Args:
        diameter_m: Pipe diameter in meters (m)
        fullness_ratio: Fullness ratio (h/D), where h is water depth and D is diameter
                       Must be between 0 and 1
        
    Returns:
        Cross-sectional area of flow in square meters (m²)
        
    Example:
        >>> circular_pipe_area(1.0, 0.5)  # 500mm diameter at 50% fullness
        0.288...
        
    Note:
        When fullness_ratio = 0 or 1, returns 0 (empty or full circle not handled)
        The formula uses the circular segment area calculation.
    """
    if not 0 < fullness_ratio < 1:
        return 0.0
    
    # Angle subtended by water surface (in radians)
    # theta = 2 * arccos(1 - 2 * h/D)
    theta = 2 * math.acos(1 - 2 * fullness_ratio)
    
    # Cross-sectional area
    r = diameter_m / 2
    area = (r * r / 2) * (theta - math.sin(theta))
    
    return area


def hydraulic_radius_circular(diameter_m: float, fullness_ratio: float) -> float:
    """
    Calculate the hydraulic radius of a circular pipe at a given fullness.
    
    The hydraulic radius is defined as the flow area divided by the wetted perimeter.
    
    Args:
        diameter_m: Pipe diameter in meters (m)
        fullness_ratio: Fullness ratio (h/D), where h is water depth and D is diameter
                       Must be between 0 and 1
        
    Returns:
        Hydraulic radius in meters (m)
        
    Example:
        >>> hydraulic_radius_circular(1.0, 0.5)
        0.25
    """
    if not 0 < fullness_ratio < 1:
        return 0.0
    
    # Wetted perimeter
    theta = 2 * math.acos(1 - 2 * fullness_ratio)
    r = diameter_m / 2
    wetted_perimeter = r * theta
    
    # Flow area
    area = circular_pipe_area(diameter_m, fullness_ratio)
    
    if wetted_perimeter == 0:
        return 0.0
    
    return area / wetted_perimeter


def trapezoidal_channel_area(bottom_width_m: float, side_slope_ratio: float, 
                              water_depth_m: float) -> float:
    """
    Calculate the cross-sectional area of a trapezoidal channel.
    
    A trapezoidal channel has a rectangular bottom and sloped sides.
    
    Args:
        bottom_width_m: Width of channel bottom in meters (m)
        side_slope_ratio: Side slope as ratio (horizontal:vertical), e.g., 2 means 2:1
        water_depth_m: Water depth in meters (m)
        
    Returns:
        Cross-sectional area in square meters (m²)
        
    Example:
        >>> trapezoidal_channel_area(1.0, 2.0, 0.5)  # 1m bottom, 2:1 slope, 0.5m depth
        1.0
        
    Note:
        For a trapezoid with bottom width b and side slope z (horizontal per vertical),
        the area = (b + z*h) * h where h is water depth.
    """
    if water_depth_m <= 0:
        return 0.0
    
    # Area = (bottom_width + side_slope * depth) * depth
    area = (bottom_width_m + side_slope_ratio * water_depth_m) * water_depth_m
    
    return area


def trapezoidal_channel_wetted_perimeter(bottom_width_m: float, side_slope_ratio: float,
                                          water_depth_m: float) -> float:
    """
    Calculate the wetted perimeter of a trapezoidal channel.
    
    Args:
        bottom_width_m: Width of channel bottom in meters (m)
        side_slope_ratio: Side slope as ratio (horizontal:vertical)
        water_depth_m: Water depth in meters (m)
        
    Returns:
        Wetted perimeter in meters (m)
        
    Example:
        >>> trapezoidal_channel_wetted_perimeter(1.0, 2.0, 0.5)
        2.236...
    """
    if water_depth_m <= 0:
        return 0.0
    
    # Wetted perimeter = bottom + 2 * side_length
    # side_length = depth * sqrt(1 + slope^2)
    side_length = water_depth_m * math.sqrt(1 + side_slope_ratio ** 2)
    wetted_perimeter = bottom_width_m + 2 * side_length
    
    return wetted_perimeter


def trapezoidal_channel_hydraulic_radius(bottom_width_m: float, side_slope_ratio: float,
                                           water_depth_m: float) -> float:
    """
    Calculate the hydraulic radius of a trapezoidal channel.
    
    Args:
        bottom_width_m: Width of channel bottom in meters (m)
        side_slope_ratio: Side slope as ratio (horizontal:vertical)
        water_depth_m: Water depth in meters (m)
        
    Returns:
        Hydraulic radius in meters (m)
    """
    area = trapezoidal_channel_area(bottom_width_m, side_slope_ratio, water_depth_m)
    perimeter = trapezoidal_channel_wetted_perimeter(bottom_width_m, side_slope_ratio, water_depth_m)
    
    if perimeter == 0:
        return 0.0
    
    return area / perimeter


def circular_pipe_wetted_perimeter(diameter_m: float, fullness_ratio: float) -> float:
    """
    Calculate the wetted perimeter of a circular pipe at a given fullness.
    
    Args:
        diameter_m: Pipe diameter in meters (m)
        fullness_ratio: Fullness ratio (h/D)
        
    Returns:
        Wetted perimeter in meters (m)
    """
    if not 0 < fullness_ratio < 1:
        return 0.0
    
    theta = 2 * math.acos(1 - 2 * fullness_ratio)
    r = diameter_m / 2
    
    return r * theta