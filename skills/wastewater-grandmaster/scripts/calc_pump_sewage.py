"""
Sewage pump station design calculation script.

This module calculates:
- Design flow: equal to sewage pipe design flow (GB 50014-2021 6.2.1)
- Design head: static_head + head_loss + safety_head (GB 50014-2021 6.2.4)
- Sump volume: 5 min of max pump output (GB 50014-2021 6.3.1)

References:
- GB 50014-2021 Section 6.2 (Design flow and head)
- GB 50014-2021 Section 6.3.1 (Sump volume)
"""

import argparse
import json
import sys
from typing import Dict

try:
    from .common.citation import make_citation
except ImportError:
    from common.citation import make_citation


def calc_pump_sewage(
    design_flow_L_s: float,
    static_head_m: float,
    head_loss_m: float,
    safety_head_m: float,
    max_pump_flow_L_s: float
) -> Dict[str, any]:
    """
    Calculate sewage pump station design parameters.

    Args:
        design_flow_L_s: Design flow in L/s (equal to sewage pipe design flow)
        static_head_m: Static head in meters
        head_loss_m: Head loss in pipeline system in meters
        safety_head_m: Safety head margin in meters
        max_pump_flow_L_s: Maximum pump flow in L/s

    Returns:
        Dictionary with all calculated values and metadata
    """
    # Validate inputs
    if design_flow_L_s <= 0:
        raise ValueError("Design flow must be positive")
    if static_head_m < 0:
        raise ValueError("Static head cannot be negative")
    if head_loss_m < 0:
        raise ValueError("Head loss cannot be negative")
    if safety_head_m < 0:
        raise ValueError("Safety head cannot be negative")
    if max_pump_flow_L_s <= 0:
        raise ValueError("Max pump flow must be positive")

    # Calculate design head: static_head + head_loss + safety_head
    design_head_m = static_head_m + head_loss_m + safety_head_m

    # Calculate sump volume: 5 min of max pump output
    # 5 minutes = 300 seconds
    # Flow in L/s * 300 s = liters, convert to m³ (divide by 1000)
    sump_volume_m3 = max_pump_flow_L_s * 300 / 1000.0

    # Build result
    result = {
        "design_flow_L_s": round(design_flow_L_s, 2),
        "design_head_m": round(design_head_m, 2),
        "sump_volume_m3": round(sump_volume_m3, 2),
        "unit": {
            "design_flow_L_s": "L/s",
            "design_head_m": "m",
            "sump_volume_m3": "m³"
        },
        "citation": make_citation("6.3.1", "81-63-集水池"),
        "citations": {
            "design_flow": make_citation("6.2.1", "80-62-设计流量和设计扬程"),
            "design_head": make_citation("6.2.4", "80-62-设计流量和设计扬程"),
            "sump_volume": make_citation("6.3.1", "81-63-集水池")
        }
    }

    return result


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate sewage pump station design parameters"
    )
    parser.add_argument(
        "--design_flow_L_s", type=float, required=True,
        help="Design flow in L/s (equal to sewage pipe design flow)"
    )
    parser.add_argument(
        "--static_head_m", type=float, required=True,
        help="Static head in meters"
    )
    parser.add_argument(
        "--head_loss_m", type=float, required=True,
        help="Head loss in pipeline system in meters"
    )
    parser.add_argument(
        "--safety_head_m", type=float, required=True,
        help="Safety head margin in meters"
    )
    parser.add_argument(
        "--max_pump_flow_L_s", type=float, required=True,
        help="Maximum pump flow in L/s"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Calculate
    result = calc_pump_sewage(
        design_flow_L_s=args.design_flow_L_s,
        static_head_m=args.static_head_m,
        head_loss_m=args.head_loss_m,
        safety_head_m=args.safety_head_m,
        max_pump_flow_L_s=args.max_pump_flow_L_s
    )

    sys.stdout.reconfigure(encoding='utf-8')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print("=" * 50)
        print("Sewage Pump Station Design Calculation Results")
        print("=" * 50)
        print(f"Design Flow: {result['design_flow_L_s']:.2f} L/s")
        print(f"Design Head: {result['design_head_m']:.2f} m")
        print(f"Sump Volume: {result['sump_volume_m3']:.2f} m³")
        print("-" * 50)
        print(f"Citation: {result['citation']}")
        print("=" * 50)


if __name__ == "__main__":
    main()