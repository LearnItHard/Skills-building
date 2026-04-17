"""
Combined sewer pump station design calculation script.

This module calculates combined sewer pump station design parameters:
- Design flow: distinguishes pre-interception and post-interception flows
- Design head: static_head + head_loss + safety_head

According to GB 50014-2021 Section 6.2.3:
- 泵站前设污水截流装置时:
  - 雨水部分: Qp = Qs - n0(Qd + Qm) = pre-interception flow
  - 污水部分: Qp = (n0 + 1)(Qd + Qm) = post-interception flow

References:
- GB 50014-2021 Section 6.2.3 (合流污水泵站设计流量)
- GB 50014-2021 Section 6.2.4 (污水泵和合流污水泵的设计扬程)
"""

import argparse
import json
import sys
from typing import Dict

try:
    from .common.units import Lps_to_m3ps
    from .common.citation import make_citation
except ImportError:
    from common.units import Lps_to_m3ps
    from common.citation import make_citation


def calc_pump_combined(
    pre_interception_L_s: float,
    post_interception_L_s: float,
    static_head_m: float,
    head_loss_m: float,
    safety_head_m: float
) -> Dict[str, any]:
    """
    Calculate combined sewer pump station design parameters.

    Args:
        pre_interception_L_s: Pre-interception flow (雨水部分) in L/s
            After interception: Qp = Qs - n0(Qd + Qm)
        post_interception_L_s: Post-interception flow (污水部分) in L/s
            After interception: Qp = (n0 + 1)(Qd + Qm)
        static_head_m: Static head in meters (集水池水位与出水管渠水位差)
        head_loss_m: Head loss in pipeline system in meters
        safety_head_m: Safety head margin in meters

    Returns:
        Dictionary with all design parameters including:
        - pre_interception_L_s: Pre-interception design flow
        - post_interception_L_s: Post-interception design flow
        - design_head_m: Total design head
    """
    # Validate inputs
    if pre_interception_L_s < 0:
        raise ValueError("Pre-interception flow cannot be negative")
    if post_interception_L_s < 0:
        raise ValueError("Post-interception flow cannot be negative")
    if static_head_m < 0:
        raise ValueError("Static head cannot be negative")
    if head_loss_m < 0:
        raise ValueError("Head loss cannot be negative")
    if safety_head_m < 0:
        raise ValueError("Safety head cannot be negative")

    # Calculate design head: static_head + head_loss + safety_head
    design_head_m = static_head_m + head_loss_m + safety_head_m

    # Convert flows to m³/s for internal reference
    pre_interception_m3s = Lps_to_m3ps(pre_interception_L_s)
    post_interception_m3s = Lps_to_m3ps(post_interception_L_s)

    # Build result with distinct pre/post interception flows
    result = {
        "pre_interception_L_s": round(pre_interception_L_s, 2),
        "post_interception_L_s": round(post_interception_L_s, 2),
        "pre_interception_m3s": round(pre_interception_m3s, 4),
        "post_interception_m3s": round(post_interception_m3s, 4),
        "static_head_m": round(static_head_m, 2),
        "head_loss_m": round(head_loss_m, 2),
        "safety_head_m": round(safety_head_m, 2),
        "design_head_m": round(design_head_m, 2),
        "unit": {
            "pre_interception_L_s": "L/s",
            "post_interception_L_s": "L/s",
            "pre_interception_m3s": "m³/s",
            "post_interception_m3s": "m³/s",
            "design_head_m": "m",
            "static_head_m": "m",
            "head_loss_m": "m",
            "safety_head_m": "m"
        },
        "citation": make_citation("6.2.3", "80-62-设计流量和设计扬程"),
        "citations": {
            "pre_interception_flow": make_citation("6.2.3-1", "80-62-设计流量和设计扬程"),
            "post_interception_flow": make_citation("6.2.3-2", "80-62-设计流量和设计扬程"),
            "design_head": make_citation("6.2.4", "80-62-设计流量和设计扬程")
        }
    }

    return result


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate combined sewer pump station design parameters"
    )
    parser.add_argument(
        "--pre_interception_L_s", type=float, required=True,
        help="Pre-interception flow (雨水部分) in L/s: Qp = Qs - n0(Qd + Qm)"
    )
    parser.add_argument(
        "--post_interception_L_s", type=float, required=True,
        help="Post-interception flow (污水部分) in L/s: Qp = (n0 + 1)(Qd + Qm)"
    )
    parser.add_argument(
        "--static_head_m", type=float, required=True,
        help="Static head in meters (集水池水位与出水管渠水位差)"
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
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Calculate
    result = calc_pump_combined(
        pre_interception_L_s=args.pre_interception_L_s,
        post_interception_L_s=args.post_interception_L_s,
        static_head_m=args.static_head_m,
        head_loss_m=args.head_loss_m,
        safety_head_m=args.safety_head_m
    )

    sys.stdout.reconfigure(encoding='utf-8')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print("=" * 50)
        print("合流泵站设计参数计算结果")
        print("=" * 50)
        print(f"截留前流量(雨水部分): {result['pre_interception_L_s']:.2f} L/s")
        print(f"截留后流量(污水部分): {result['post_interception_L_s']:.2f} L/s")
        print(f"设计扬程: {result['design_head_m']:.2f} m")
        print(f"  - 静扬程: {result['static_head_m']:.2f} m")
        print(f"  - 损失扬程: {result['head_loss_m']:.2f} m")
        print(f"  - 安全扬程: {result['safety_head_m']:.2f} m")
        print("-" * 50)
        print(f"引用: {result['citation']}")
        print("=" * 50)


if __name__ == "__main__":
    main()