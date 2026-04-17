"""
Storm flow calculation using GB 50014-2021 rainwater formulas.

This script calculates:
- Rainfall intensity q using formula 4.1.9: q = 167 * A1 * (1 + C * log10(P)) / (t + b)^n
- Design flow Q = ψ * q * F (4.1.7)
- Total rainfall duration t = t1 + t2 (4.1.11)

References: 4.1.7, 4.1.9, 4.1.11
"""

import argparse
import json
import sys

try:
    from .common.validation import check_storm_applicability
    from .common.citation import make_citation
except ImportError:
    from common.validation import check_storm_applicability
    from common.citation import make_citation


def calc_rainfall_intensity(A1: float, C: float, P: float, b: float, n: float, t: float) -> float:
    """
    Calculate rainfall intensity using GB 50014-2021 formula 4.1.9.

    Formula: q = 167 * A1 * (1 + C * log10(P)) / (t + b)^n

    Args:
        A1: Parameter A1 (rainfall division)
        C: Parameter C
        P: Design recurrence interval (years)
        b: Parameter b
        n: Parameter n
        t: Rainfall duration (minutes)

    Returns:
        Rainfall intensity in L/s·hm²

    Example:
        >>> calc_rainfall_intensity(1.2, 0.45, 10, 8, 0.5, 30)
        ~240 L/s·hm²
    """
    import math
    # q = 167 * A1 * (1 + C * log10(P)) / (t + b)^n
    log_P = math.log10(P) if P > 0 else 0
    q = 167 * A1 * (1 + C * log_P) / ((t + b) ** n)
    return q


def calc_design_flow(psi: float, q: float, F: float) -> float:
    """
    Calculate design flow using rational formula.

    Formula: Q = ψ * q * F

    Args:
        psi: Runoff coefficient (dimensionless, 0-1)
        q: Rainfall intensity (L/s·hm²)
        F: Catchment area (hm²)

    Returns:
        Design flow in L/s
    """
    return psi * q * F


def calc_total_time(t1: float, t2: float) -> float:
    """
    Calculate total time of concentration.

    t = t1 + t2

    Args:
        t1: Pipe flow time (minutes)
        t2: Channel flow time (minutes)

    Returns:
        Total time in minutes
    """
    return t1 + t2


def main():
    parser = argparse.ArgumentParser(
        description="Calculate storm design flow using GB 50014-2021 formula 4.1.9"
    )
    parser.add_argument("--A1", type=float, required=True, help="Parameter A1 (rainfall division)")
    parser.add_argument("--C", type=float, required=True, help="Parameter C")
    parser.add_argument("--P", type=float, required=True, help="Design recurrence interval (years)")
    parser.add_argument("--b", type=float, required=True, help="Parameter b")
    parser.add_argument("--n", type=float, required=True, help="Parameter n")
    parser.add_argument("--t1", type=float, required=True, help="Pipe flow time (minutes)")
    parser.add_argument("--t2", type=float, required=True, help="Channel flow time (minutes)")
    parser.add_argument("--psi", type=float, required=True, help="Runoff coefficient (0-1)")
    parser.add_argument("--F", type=float, required=True, help="Catchment area (hm2)")

    args = parser.parse_args()

    # Check applicability
    applicability_result = check_storm_applicability(args.F)

    # Calculate total time
    total_time = calc_total_time(args.t1, args.t2)

    # Calculate rainfall intensity
    rainfall_intensity = calc_rainfall_intensity(
        args.A1, args.C, args.P, args.b, args.n, total_time
    )

    # Calculate design flow
    design_flow = calc_design_flow(args.psi, rainfall_intensity, args.F)

    # Build output - use ASCII-safe representation
    output = {
        "rainfall_intensity": round(rainfall_intensity, 4),
        "design_flow": round(design_flow, 4),
        "total_time": round(total_time, 2),
        "unit": "L/s",
        "citation": make_citation("4.1.7"),
        "citations": {
            "design_flow": make_citation("4.1.7"),
            "rainfall_intensity": make_citation("4.1.9"),
            "total_time": make_citation("4.1.11"),
        },
        "applicability": {
            "method_switched": applicability_result.get("method_switched", False),
            "valid": applicability_result.get("valid", True),
            "citation_clause": applicability_result.get("citation_clause", "4.1.9"),
            "message": applicability_result.get("message", "")
        }
    }

    # Print JSON output
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(output, indent=2, ensure_ascii=False))

    return output


if __name__ == "__main__":
    main()