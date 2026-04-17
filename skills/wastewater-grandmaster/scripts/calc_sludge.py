"""
Digester volume calculation using GB 50014-2021 formulas (8.3.6-1 and 8.3.6-2).

This script calculates:
- Volume by time: V = Q0 * td (formula 8.3.6-1)
- Volume by load: V = Ws / Lv (formula 8.3.6-2)
- Optional gas production estimate with disclaimer

Reference: 145-Ⅱ-污泥厌氧消化.md
"""

import argparse
import json
import sys

try:
    from .common.citation import make_citation
except ImportError:
    from common.citation import make_citation


def calc_volume_by_time(Q0_m3d: float, td_d: float) -> float:
    """
    Calculate digester volume using time-based formula (8.3.6-1).

    Formula: V = Q0 * td

    Args:
        Q0_m3d: Daily sludge flow (m³/d)
        td_d: Digestion time (d)

    Returns:
        Digester volume in m³

    Example:
        >>> calc_volume_by_time(100, 20)
        2000.0
    """
    return Q0_m3d * td_d


def calc_volume_by_load(Ws_kg_d: float, Lv_kg_m3d: float) -> float:
    """
    Calculate digester volume using load-based formula (8.3.6-2).

    Formula: V = Ws / Lv

    Args:
        Ws_kg_d: Daily sludge solids load (kg/d)
        Lv_kg_m3d: Volumetric loading (kg/m³/d)

    Returns:
        Digester volume in m³

    Example:
        >>> calc_volume_by_load(2000, 1.5)
        1333.33...
    """
    if Lv_kg_m3d <= 0:
        raise ValueError("Lv must be positive")
    return Ws_kg_d / Lv_kg_m3d


def calc_gas_estimate(Ws_kg_d: float, gas_yield_m3_kg: float = 0.8) -> float:
    """
    Calculate empirical gas production.

    This is an empirical estimation based on typical digestion yields.
    Not from GB 50014-2021 standard formulas.

    Formula: Q_gas = Ws * gas_yield

    Args:
        Ws_kg_d: Daily sludge solids load (kg/d)
        gas_yield_m3_kg: Gas yield per kg of solids (m³/kg), default 0.8

    Returns:
        Daily gas production in m³/d
    """
    return Ws_kg_d * gas_yield_m3_kg


def main():
    parser = argparse.ArgumentParser(
        description="Calculate anaerobic digester volume using GB 50014-2021 formulas"
    )
    parser.add_argument(
        "--Q0_m3d", type=float, required=True,
        help="Daily sludge flow (m³/d)"
    )
    parser.add_argument(
        "--td_d", type=float, required=True,
        help="Digestion time (d)"
    )
    parser.add_argument(
        "--Ws_kg_d", type=float, required=True,
        help="Daily sludge solids load (kg/d)"
    )
    parser.add_argument(
        "--Lv_kg_m3d", type=float, required=True,
        help="Volumetric loading (kg/m³/d)"
    )
    parser.add_argument(
        "--estimate_gas", action="store_true",
        help="Estimate gas production"
    )
    parser.add_argument(
        "--gas_yield_m3_kg", type=float, default=0.8,
        help="Gas yield per kg of solids (m³/kg), default 0.8"
    )

    args = parser.parse_args()

    # Calculate volumes
    volume_by_time = calc_volume_by_time(args.Q0_m3d, args.td_d)
    volume_by_load = calc_volume_by_load(args.Ws_kg_d, args.Lv_kg_m3d)

    # Build output
    output = {
        "volume_by_time": round(volume_by_time, 2),
        "volume_by_load": round(volume_by_load, 2),
        "unit": "m³",
        "citation": make_citation("8.3.6", "145-Ⅱ-污泥厌氧消化")
    }

    # Add gas estimate if requested
    if args.estimate_gas:
        gas_estimate = calc_gas_estimate(args.Ws_kg_d, args.gas_yield_m3_kg)
        output["gas_estimate_m3d"] = round(gas_estimate, 2)
        output["disclaimer"] = "产气量估算来源于外部工艺资料/经验数据，非 GB 50014-2021 正文公式"

    # Print JSON output
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(output, indent=2, ensure_ascii=False))

    return output


if __name__ == "__main__":
    main()