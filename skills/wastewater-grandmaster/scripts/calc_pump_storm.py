"""
Storm pump station design flow and head calculation script.

This module calculates storm pump station design parameters:
- Design flow: equals storm pipe design flow
- Design head: static_head + head_loss + safety_head

According to GB 50014-2021 Section 6.2:
- Design flow: should equal the storm pipe design flow
- Design head: based on 6.2.5 (static water level difference + head loss)

References:
- GB 50014-2021 Section 6.2.2 (storm pump design flow)
- GB 50014-2021 Section 6.2.5 (storm pump design head)
"""

import argparse
import json
from typing import Dict

try:
    from .common.units import Lps_to_m3ps, m3ps_to_Lps
    from .common.citation import make_citation
except ImportError:
    from common.units import Lps_to_m3ps, m3ps_to_Lps
    from common.citation import make_citation


def calc_pump_storm_head(
    static_head_m: float,
    head_loss_m: float,
    safety_head_m: float = 0.5
) -> Dict[str, any]:
    """
    Calculate storm pump design head.

    Formula: H_design = H_static + h_loss + h_safety

    Args:
        static_head_m: Static head (water level difference) in meters
        head_loss_m: Pipe system head loss in meters
        safety_head_m: Safety margin in meters (default 0.5m)

    Returns:
        Dictionary with head calculation results
    """
    if static_head_m < 0:
        raise ValueError("Static head must be non-negative")
    if head_loss_m < 0:
        raise ValueError("Head loss must be non-negative")
    if safety_head_m < 0:
        raise ValueError("Safety head must be non-negative")

    design_head = static_head_m + head_loss_m + safety_head_m

    return {
        "static_head_m": round(static_head_m, 2),
        "head_loss_m": round(head_loss_m, 2),
        "safety_head_m": round(safety_head_m, 2),
        "design_head_m": round(design_head, 2),
    }


def calc_pump_storm(
    design_flow_L_s: float,
    static_head_m: float,
    head_loss_m: float,
    safety_head_m: float = 0.5
) -> Dict[str, any]:
    """
    Calculate storm pump station design parameters.

    Args:
        design_flow_L_s: Design flow in L/s (equals storm pipe design flow)
        static_head_m: Static head (water level difference) in meters
        head_loss_m: Pipe system head loss in meters
        safety_head_m: Safety margin in meters (default 0.5m)

    Returns:
        Dictionary with all design parameters
    """
    if design_flow_L_s <= 0:
        raise ValueError("Design flow must be positive")
    if static_head_m < 0:
        raise ValueError("Static head must be non-negative")
    if head_loss_m < 0:
        raise ValueError("Head loss must be non-negative")
    if safety_head_m < 0:
        raise ValueError("Safety head must be non-negative")

    # Calculate design head
    head_result = calc_pump_storm_head(static_head_m, head_loss_m, safety_head_m)
    design_head = head_result["design_head_m"]

    # Convert flow to m³/s for internal use
    design_flow_m3s = Lps_to_m3ps(design_flow_L_s)

    # Build result
    result = {
        "static_head_m": head_result["static_head_m"],
        "head_loss_m": head_result["head_loss_m"],
        "safety_head_m": head_result["safety_head_m"],
        "design_flow_L_s": round(design_flow_L_s, 2),
        "design_flow_m3s": round(design_flow_m3s, 4),
        "design_head_m": design_head,
        "unit": {
            "design_flow_L_s": "L/s",
            "design_flow_m3s": "m3/s",
            "design_head_m": "m",
            "static_head_m": "m",
            "head_loss_m": "m",
            "safety_head_m": "m"
        },
        "citation": make_citation("6.2.5", "80-62-设计流量和设计扬程"),
        "citations": {
            "design_flow": make_citation("6.2.2", "80-62-设计流量和设计扬程"),
            "design_head": make_citation("6.2.5", "80-62-设计流量和设计扬程")
        }
    }

    return result


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate storm pump station design flow and head"
    )
    parser.add_argument(
        "--design_flow_L_s", type=float, required=True,
        help="Design flow in L/s (equals storm pipe design flow)"
    )
    parser.add_argument(
        "--static_head_m", type=float, required=True,
        help="Static head in meters (water level difference)"
    )
    parser.add_argument(
        "--head_loss_m", type=float, required=True,
        help="Pipe system head loss in meters"
    )
    parser.add_argument(
        "--safety_head_m", type=float, default=0.5,
        help="Safety margin in meters (default: 0.5)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Calculate
    result = calc_pump_storm(
        design_flow_L_s=args.design_flow_L_s,
        static_head_m=args.static_head_m,
        head_loss_m=args.head_loss_m,
        safety_head_m=args.safety_head_m
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print("=" * 50)
        print("雨水泵站设计参数计算结果")
        print("=" * 50)
        print(f"设计流量: {result['design_flow_L_s']:.2f} L/s")
        print(f"设计流量: {result['design_flow_m3s']:.4f} m3/s")
        print(f"设计扬程: {result['design_head_m']:.2f} m")
        print(f"  - 静扬程: {result.get('static_head_m', args.static_head_m):.2f} m")
        print(f"  - 损失扬程: {result.get('head_loss_m', args.head_loss_m):.2f} m")
        print(f"  - 安全扬程: {result.get('safety_head_m', args.safety_head_m):.2f} m")
        print("-" * 50)
        print(f"引用: {result['citation']}")
        print("=" * 50)


if __name__ == "__main__":
    main()