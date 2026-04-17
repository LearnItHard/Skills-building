"""
Sewage flow calculation script for wastewater system design.

This module calculates design sewage flow based on:
- Domestic sewage: based on population, water quota, and discharge coefficient
- Industrial wastewater: based on production and unit wastewater volume
- Total variation coefficient Kz: from table lookup or fitted formula

Formula: Q_design = Kz * Q_domestic + Q_industrial + Q_infiltration

References:
- GB 50014-2021 Section 4.1.13 (formula 4.1.13)
- GB 50014-2021 Table 4.1.15 (variation coefficient)
"""

import argparse
import json
import math
from typing import Any, Dict, Optional, Tuple

try:
    from .common.units import m3ps_to_m3pd
    from .common.citation import make_citation
except ImportError:
    from common.units import m3ps_to_m3pd
    from common.citation import make_citation


# Table 4.1.15: Comprehensive domestic sewage variation coefficient
# Average daily flow (L/s) -> Variation coefficient
VARIATION_COEFFICIENT_TABLE = [
    (5, 2.7),
    (15, 2.4),
    (40, 2.1),
    (70, 2.0),
    (100, 1.9),
    (200, 1.8),
    (500, 1.6),
    (1000, 1.5),
]

VALID_PEAK_FACTOR_METHODS = {"table", "fitted"}


def lookup_variation_coefficient(Q_average_Ls: float) -> Tuple[float, bool]:
    """
    Lookup variation coefficient from Table 4.1.15.

    Uses interpolation for intermediate values.
    For values at or above 1000 L/s, uses Kz=1.5 (table note: >=1000).

    Args:
        Q_average_Ls: Average daily flow in L/s

    Returns:
        Tuple of (Kz value, whether fitted formula was used).
        The second element is kept for backward compatibility and is always False
        because table lookup remains the normative default path.
    """
    if Q_average_Ls <= 0:
        raise ValueError("Average flow must be positive")

    # Special case: exact match to table threshold
    for Q_threshold, Kz in VARIATION_COEFFICIENT_TABLE:
        if Q_average_Ls == Q_threshold:
            return Kz, False

    # Special case: >=1000 L/s -> Kz = 1.5 per table note
    if Q_average_Ls >= 1000:
        return 1.5, False

    # Direct table lookup with interpolation
    for i, (Q_threshold, Kz) in enumerate(VARIATION_COEFFICIENT_TABLE):
        if Q_average_Ls <= Q_threshold:
            # Check if we need interpolation
            if i == 0:
                # Below first threshold (Q <= 5), use table value directly
                return Kz, False
            # Get previous threshold and Kz for interpolation
            Q_prev, Kz_prev = VARIATION_COEFFICIENT_TABLE[i - 1]

            if Q_average_Ls == Q_threshold:
                return Kz, False

            ratio = (Q_average_Ls - Q_prev) / (Q_threshold - Q_prev)
            Kz_interpolated = Kz_prev + ratio * (Kz - Kz_prev)
            return round(Kz_interpolated, 2), False

    # Should not reach here, but handle safety
    return 1.5, False


def resolve_variation_coefficient(
    Q_average_Ls: float,
    peak_factor_override: Optional[float] = None,
    peak_factor_method: str = "table",
) -> Tuple[float, str, Optional[str]]:
    """Resolve Kz and record whether it came from the table, fitted formula, or override."""
    if peak_factor_override is not None:
        if peak_factor_override <= 0:
            raise ValueError("Peak factor override must be positive")
        return peak_factor_override, "user_override", None

    method = peak_factor_method.lower()
    if method not in VALID_PEAK_FACTOR_METHODS:
        valid_methods = ", ".join(sorted(VALID_PEAK_FACTOR_METHODS))
        raise ValueError(f"peak_factor_method must be one of: {valid_methods}")

    if method == "fitted":
        return (
            compute_variation_coefficient_fitted(Q_average_Ls),
            "fitted_formula",
            "Kz 来源于条文说明拟合式，非正文公式",
        )

    Kz, _ = lookup_variation_coefficient(Q_average_Ls)
    return Kz, "table_lookup", None


def compute_variation_coefficient_fitted(Q_average_Ls: float) -> float:
    """
    Compute variation coefficient using fitted formula from standard commentary.

    Formula: lgKz = -0.1156 * lgQ + 0.5052

    This is from the standard commentary/explanatory text, NOT the main standard formula.
    Use only when interpolation is not possible.

    Args:
        Q_average_Ls: Average daily flow in L/s

    Returns:
        Computed Kz value
    """
    if Q_average_Ls <= 0:
        raise ValueError("Average flow must be positive")

    # Fitted formula from standard commentary
    lgKz = -0.1156 * math.log10(Q_average_Ls) + 0.5052
    Kz = 10 ** lgKz
    return round(Kz, 2)


def calc_domestic_sewage_flow(
    population: int,
    water_quota_Lpd: float,
    discharge_coeff: float = 0.9
) -> Dict[str, float]:
    """
    Calculate average daily domestic sewage flow.

    Formula: Q_domestic = population * water_quota * discharge_coefficient

    Args:
        population: Population equivalent
        water_quota_Lpd: Water quota in L/(person·d)
        discharge_coeff: Discharge coefficient (default 0.9 per 4.1.14)

    Returns:
        Dictionary with flow values in different units
    """
    if population <= 0:
        raise ValueError("Population must be positive")
    if water_quota_Lpd <= 0:
        raise ValueError("Water quota must be positive")
    if not 0 < discharge_coeff <= 1:
        raise ValueError("Discharge coefficient must be between 0 and 1")

    # Average daily flow in m³/d
    avg_daily_m3d = population * water_quota_Lpd * discharge_coeff / 1000.0

    # Convert to L/s
    avg_daily_Ls = avg_daily_m3d * 1000.0 / 86400.0

    return {
        "average_daily_m3d": round(avg_daily_m3d, 2),
        "average_daily_Ls": round(avg_daily_Ls, 4),
    }


def calc_design_sewage_flow(
    population: int,
    water_quota_Lpd: float,
    discharge_coeff: float = 0.9,
    industrial_m3d: float = 0.0,
    infiltration_m3d: float = 0.0,
    peak_factor_override: Optional[float] = None,
    peak_factor_method: str = "table",
) -> Dict[str, Any]:
    """
    Calculate design sewage flow for wastewater system.

    Formula: Q_design = Kz * Q_domestic + Q_industrial + Q_infiltration

    Args:
        population: Population equivalent
        water_quota_Lpd: Water quota in L/(person·d)
        discharge_coeff: Discharge coefficient (default 0.9 per 4.1.14)
        industrial_m3d: Industrial wastewater in m³/d
        infiltration_m3d: Infiltration water in m³/d
        peak_factor_override: Optional override for Kz (bypasses table lookup)
        peak_factor_method: "table" or "fitted" when not using an override

    Returns:
        Dictionary with all calculated values and metadata
    """
    # Calculate domestic sewage
    domestic = calc_domestic_sewage_flow(population, water_quota_Lpd, discharge_coeff)
    Q_domestic_Ls = domestic["average_daily_Ls"]
    Q_domestic_m3d = domestic["average_daily_m3d"]

    Kz, formula_source, disclaimer = resolve_variation_coefficient(
        Q_domestic_Ls,
        peak_factor_override=peak_factor_override,
        peak_factor_method=peak_factor_method,
    )

    # Calculate industrial flow in L/s
    industrial_Ls = industrial_m3d * 1000.0 / 86400.0

    # Calculate infiltration in L/s
    infiltration_Ls = infiltration_m3d * 1000.0 / 86400.0

    # Design flow: Q_design = Kz * Q_domestic + Q_industrial + Q_infiltration
    design_flow_Ls = Kz * Q_domestic_Ls + industrial_Ls + infiltration_Ls
    design_flow_m3d = m3ps_to_m3pd(design_flow_Ls / 1000.0)

    # Build result
    result = {
        "average_daily_m3d": round(Q_domestic_m3d, 2),
        "design_flow_L_s": round(design_flow_Ls, 2),
        "design_flow_m3d": round(design_flow_m3d, 2),
        "Kz": round(Kz, 2),
        "peak_factor_source": formula_source,
        "unit": {
            "design_flow_L_s": "L/s",
            "design_flow_m3d": "m³/d",
            "Kz": "dimensionless"
        },
        "citation": make_citation("4.1.13", "56-Ⅱ污水量"),
        "citations": {
            "formula": make_citation("4.1.13", "56-Ⅱ污水量"),
            "variation_table": make_citation("4.1.15", "56-Ⅱ污水量")
        }
    }

    # Add disclaimer if using fitted formula
    if disclaimer:
        result["disclaimer"] = disclaimer

    return result


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate design sewage flow for wastewater system"
    )
    parser.add_argument(
        "--population", type=int, required=True,
        help="Population equivalent"
    )
    parser.add_argument(
        "--water_quota_Lpd", type=float, required=True,
        help="Water quota in L/(person·d)"
    )
    parser.add_argument(
        "--discharge_coeff", type=float, default=0.9,
        help="Discharge coefficient (default: 0.9)"
    )
    parser.add_argument(
        "--industrial_m3d", type=float, default=0.0,
        help="Industrial wastewater in m³/d (default: 0)"
    )
    parser.add_argument(
        "--infiltration_m3d", type=float, default=0.0,
        help="Infiltration water in m³/d (default: 0)"
    )
    parser.add_argument(
        "--peak_factor", type=float, default=None,
        help="Optional override for variation coefficient Kz"
    )
    parser.add_argument(
        "--peak_factor_method", choices=sorted(VALID_PEAK_FACTOR_METHODS), default="table",
        help="Peak factor method when --peak_factor is not supplied (default: table)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Calculate
    result = calc_design_sewage_flow(
        population=args.population,
        water_quota_Lpd=args.water_quota_Lpd,
        discharge_coeff=args.discharge_coeff,
        industrial_m3d=args.industrial_m3d,
        infiltration_m3d=args.infiltration_m3d,
        peak_factor_override=args.peak_factor,
        peak_factor_method=args.peak_factor_method,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        # Human-readable output (ASCII-safe)
        print("=" * 50)
        print("Design Sewage Flow Calculation Results")
        print("=" * 50)
        print(f"Average Daily Domestic: {result['average_daily_m3d']:.2f} m3/d")
        print(f"Design Flow: {result['design_flow_L_s']:.2f} L/s")
        print(f"Design Flow: {result['design_flow_m3d']:.2f} m3/d")
        print(f"Variation Coefficient Kz: {result['Kz']:.2f}")
        print(f"Peak Factor Source: {result['peak_factor_source']}")
        print("-" * 50)
        print(f"Citation: {result['citation']}")
        if "disclaimer" in result:
            print(f"WARNING: {result['disclaimer']}")
        print("=" * 50)


if __name__ == "__main__":
    main()