#!/usr/bin/env python3
"""
Hydraulic calculation script for circular pipes using Manning's equation.

This script calculates velocity and flow rate for circular pipes based on:
- Pipe diameter
- Slope
- Pipe material (affects roughness coefficient)
- System type (sewage/storm_combined)

References:
- GB 50014-2021 Section 5.2.1: Q = A * v
- GB 50014-2021 Section 5.2.2: v = (1/n) * R^(2/3) * I^(1/2)
"""

import argparse
import json
import math
import sys

try:
    from .common.geometry import circular_pipe_area, hydraulic_radius_circular
    from .common.table_lookup import roughness_coefficient, max_fullness, min_velocity
    from .common.citation import make_citation
except ImportError:
    from common.geometry import circular_pipe_area, hydraulic_radius_circular
    from common.table_lookup import roughness_coefficient, max_fullness, min_velocity
    from common.citation import make_citation


def calculate_velocity(n: float, hydraulic_radius_m: float, slope: float) -> float:
    """
    Calculate velocity using Manning's equation.
    
    v = (1/n) * R^(2/3) * I^(1/2)
    
    Args:
        n: Manning's roughness coefficient
        hydraulic_radius_m: Hydraulic radius in meters
        slope: Slope (m/m), e.g., 0.001 for 1‰
    
    Returns:
        Velocity in m/s
    
    Reference: GB 50014-2021 第5.2.2条
    """
    if n <= 0 or hydraulic_radius_m <= 0 or slope <= 0:
        return 0.0
    
    # v = (1/n) * R^(2/3) * I^(1/2)
    velocity = (1.0 / n) * (hydraulic_radius_m ** (2.0 / 3.0)) * (slope ** 0.5)
    
    return velocity


def calculate_flow(area_m2: float, velocity_m_s: float) -> float:
    """
    Calculate flow rate using Q = A * v.
    
    Args:
        area_m2: Cross-sectional area in m²
        velocity_m_s: Velocity in m/s
    
    Returns:
        Flow rate in m³/s
    
    Reference: GB 50014-2021 第5.2.1条
    """
    return area_m2 * velocity_m_s


def calculate_hydraulics(diameter_mm: float, slope: float, material: str, 
                         system_type: str, fullness_ratio: float = 1.0) -> dict:
    """
    Calculate hydraulic parameters for a circular pipe.
    
    Args:
        diameter_mm: Pipe diameter in millimeters
        slope: Slope (m/m), e.g., 0.001 for 1‰
        material: Pipe material (e.g., "concrete", "upvc", "reinforced_concrete")
        system_type: System type ("sewage" or "storm_combined")
        fullness_ratio: Fullness ratio (default 1.0 for full flow)
    
    Returns:
        Dictionary with calculated hydraulic parameters
    """
    # Convert diameter to meters
    diameter_m = diameter_mm / 1000.0
    
    # Get roughness coefficient
    n = roughness_coefficient(material)
    
    # Calculate area and hydraulic radius
    area = circular_pipe_area(diameter_m, fullness_ratio)
    hydraulic_radius = hydraulic_radius_circular(diameter_m, fullness_ratio)
    
    # Calculate velocity using Manning's equation
    velocity = calculate_velocity(n, hydraulic_radius, slope)
    
    # Calculate flow rate
    flow_m3_s = calculate_flow(area, velocity)
    
    # Get max fullness for this diameter
    max_fullness_ratio = max_fullness(diameter_mm)
    
    # Get min velocity for system type
    min_vel = min_velocity(system_type)
    
    # Convert flow to L/s
    flow_L_s = flow_m3_s * 1000.0
    
    return {
        "velocity_m_s": round(velocity, 4),
        "flow_m3_s": round(flow_m3_s, 6),
        "flow_L_s": round(flow_L_s, 4),
        "fullness_ratio": fullness_ratio,
        "max_fullness": max_fullness_ratio,
        "min_velocity_m_s": min_vel,
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate hydraulic parameters for circular pipes using Manning's equation"
    )
    parser.add_argument(
        "--diameter_mm",
        type=float,
        required=True,
        help="Pipe diameter in millimeters"
    )
    parser.add_argument(
        "--slope",
        type=float,
        required=True,
        help="Pipe slope (m/m), e.g., 0.001 for 1‰"
    )
    parser.add_argument(
        "--material",
        type=str,
        required=True,
        help="Pipe material (e.g., concrete, reinforced_concrete, upvc, pe, plastic)"
    )
    parser.add_argument(
        "--system_type",
        type=str,
        required=True,
        choices=["sewage", "storm_combined"],
        help="System type: sewage or storm_combined"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.diameter_mm <= 0:
        print("Error: diameter_mm must be positive", file=sys.stderr)
        sys.exit(1)
    
    if args.slope <= 0:
        print("Error: slope must be positive", file=sys.stderr)
        sys.exit(1)
    
    # Calculate hydraulics for full flow
    result = calculate_hydraulics(
        args.diameter_mm,
        args.slope,
        args.material,
        args.system_type,
        fullness_ratio=1.0
    )
    
    # Add citation
    result["citation"] = make_citation("5.2.2")
    result["unit"] = "metric"
    
    # Output JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with appropriate code based on min velocity check
    if result["velocity_m_s"] < result["min_velocity_m_s"]:
        print(f"Warning: Calculated velocity {result['velocity_m_s']} m/s is below "
              f"minimum required {result['min_velocity_m_s']} m/s for {args.system_type}",
              file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()