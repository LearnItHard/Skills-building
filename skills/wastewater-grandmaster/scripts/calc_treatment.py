"""
Bioreactor volume calculation script for wastewater treatment system design.

This module calculates biological reaction tank volume based on:
- Loading method (Formula 7.6.10-1)
- Sludge age method (Formula 7.6.10-2)
- Temperature correction for decay coefficient (Formula 7.6.11)

Formulas:
- Loading: V = Q * (So - Se) / (1000 * Ls * X)
- Sludge age: V = Q * Y * θc * (So - Se) / (1000 * Xv * (1 + Kd * θc))
- Temperature correction: KdT = Kd20 * θ_T^(T-20)

References:
- GB 50014-2021 Section 7.6.10 (bioreactor volume)
- GB 50014-2021 Section 7.6.11 (temperature correction)
"""

import argparse
import json
from typing import Dict, Optional

try:
    from .common.units import m3ps_to_m3pd
    from .common.validation import raise_if_out_of_bounds
    from .common.citation import make_citation
except ImportError:
    from common.units import m3ps_to_m3pd
    from common.validation import raise_if_out_of_bounds
    from common.citation import make_citation


# Valid ranges from GB 50014-2021
THETA_C_MIN = 3.0   # days for carbon removal
THETA_C_MAX = 15.0  # days for carbon removal
KD20_DEFAULT = 0.05  # d^-1, mid of 0.040~0.075
THETA_T_DEFAULT = 1.04  # temperature coefficient, mid of 1.02~1.06
DEFAULT_T = 12.0  # default design temperature in °C


def calc_volume_by_loading(
    Q_m3d: float,
    So: float,
    Se: float,
    Ls: float,
    X: float
) -> float:
    """
    Calculate bioreactor volume by污泥负荷 (sludge loading).

    Formula (7.6.10-1): V = Q * (So - Se) / (1000 * Ls * X)

    Args:
        Q_m3d: Design flow in m³/d
        So: Influent BOD5 concentration in mg/L
        Se: Effluent BOD5 concentration in mg/L
        Ls: BOD5 sludge loading in kgBOD5/(kgMLSS·d)
        X: MLSS concentration in gMLSS/L

    Returns:
        Bioreactor volume in m³
    """
    if Q_m3d <= 0:
        raise ValueError("Flow Q must be positive")
    if So <= 0:
        raise ValueError("Influent BOD5 So must be positive")
    if Se < 0:
        raise ValueError("Effluent BOD5 Se must be non-negative")
    if Se >= So:
        raise ValueError("Effluent Se must be less than influent So")
    if Ls <= 0:
        raise ValueError("Sludge loading Ls must be positive")
    if X <= 0:
        raise ValueError("MLSS concentration X must be positive")

    # V = Q * (So - Se) / (1000 * Ls * X)
    delta_S = So - Se
    V = Q_m3d * delta_S / (1000.0 * Ls * X)

    return round(V, 2)


def calc_volume_by_sludge_age(
    Q_m3d: float,
    So: float,
    Se: float,
    Y: float,
    theta_c: float,
    Xv: float,
    Kd: float
) -> float:
    """
    Calculate bioreactor volume by污泥龄 (sludge age).

    Formula (7.6.10-2): V = Q * Y * θc * (So - Se) / (1000 * Xv * (1 + Kd * θc))

    Args:
        Q_m3d: Design flow in m³/d
        So: Influent BOD5 concentration in mg/L
        Se: Effluent BOD5 concentration in mg/L
        Y: Sludge yield coefficient in kgVSS/kgBOD5
        theta_c: Design sludge age in days
        Xv: MLVSS concentration in gMLVSS/L
        Kd: Decay coefficient in d^-1

    Returns:
        Bioreactor volume in m³
    """
    if Q_m3d <= 0:
        raise ValueError("Flow Q must be positive")
    if So <= 0:
        raise ValueError("Influent BOD5 So must be positive")
    if Se < 0:
        raise ValueError("Effluent BOD5 Se must be non-negative")
    if Se >= So:
        raise ValueError("Effluent Se must be less than influent So")
    if Y <= 0:
        raise ValueError("Sludge yield Y must be positive")
    if theta_c <= 0:
        raise ValueError("Sludge age θc must be positive")
    if Xv <= 0:
        raise ValueError("MLVSS concentration Xv must be positive")
    if Kd < 0:
        raise ValueError("Decay coefficient Kd must be non-negative")

    # V = Q * Y * θc * (So - Se) / (1000 * Xv * (1 + Kd * θc))
    delta_S = So - Se
    denominator = 1000.0 * Xv * (1.0 + Kd * theta_c)
    V = Q_m3d * Y * theta_c * delta_S / denominator

    return round(V, 2)


def calc_temperature_corrected_kd(
    Kd20: float,
    theta_T: float,
    T: float
) -> float:
    """
    Calculate temperature-corrected decay coefficient.

    Formula (7.6.11): KdT = Kd20 * θ_T^(T-20)

    Args:
        Kd20: Decay coefficient at 20°C in d^-1
        theta_T: Temperature coefficient (default 1.02~1.06)
        T: Design temperature in °C

    Returns:
        Temperature-corrected KdT in d^-1
    """
    if Kd20 <= 0:
        raise ValueError("Kd20 must be positive")
    if theta_T <= 0:
        raise ValueError("theta_T must be positive")
    if T < 0:
        raise ValueError("Temperature T must be non-negative")

    # KdT = Kd20 * θ_T^(T-20)
    KdT = Kd20 * (theta_T ** (T - 20.0))

    return round(KdT, 4)


def calc_bioreactor_volume(
    Q_m3d: float,
    So: float,
    Se: float = 20.0,
    Ls: float = 0.3,
    X: float = 3.0,
    Y: float = 0.5,
    theta_c: float = 10.0,
    Xv: float = 2.5,
    Kd20: float = KD20_DEFAULT,
    theta_T: float = THETA_T_DEFAULT,
    T: float = DEFAULT_T
) -> Dict:
    """
    Calculate bioreactor volume using both loading and sludge age methods.

    Args:
        Q_m3d: Design flow in m³/d
        So: Influent BOD5 concentration in mg/L
        Se: Effluent BOD5 concentration in mg/L
        Ls: BOD5 sludge loading in kgBOD5/(kgMLSS·d)
        X: MLSS concentration in gMLSS/L
        Y: Sludge yield coefficient in kgVSS/kgBOD5
        theta_c: Design sludge age in days
        Xv: MLVSS concentration in gMLVSS/L
        Kd20: Decay coefficient at 20°C in d^-1
        theta_T: Temperature coefficient
        T: Design temperature in °C

    Returns:
        Dictionary with all calculated values and metadata
    """
    # Validate θc range for carbon removal (3~15 days per 7.6.10)
    raise_if_out_of_bounds(theta_c, THETA_C_MIN, THETA_C_MAX, "7.6.10")

    # Calculate temperature-corrected Kd
    KdT = calc_temperature_corrected_kd(Kd20, theta_T, T)

    # Calculate volume by loading method
    volume_by_loading = calc_volume_by_loading(Q_m3d, So, Se, Ls, X)

    # Calculate volume by sludge age method
    volume_by_sludge_age = calc_volume_by_sludge_age(
        Q_m3d, So, Se, Y, theta_c, Xv, KdT
    )

    # Build result
    result = {
        "volume_by_loading": volume_by_loading,
        "volume_by_sludge_age": volume_by_sludge_age,
        "KdT": KdT,
        "unit": {
            "volume": "m³",
            "KdT": "d⁻¹"
        },
        "citation": make_citation("7.6.10"),
        "citations": {
            "loading_formula": make_citation("7.6.10-1"),
            "sludge_age_formula": make_citation("7.6.10-2"),
            "temperature_correction": make_citation("7.6.11")
        }
    }

    return result


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate bioreactor volume for wastewater treatment"
    )
    parser.add_argument(
        "--Q_m3d", type=float, required=True,
        help="Design flow in m³/d"
    )
    parser.add_argument(
        "--So", type=float, required=True,
        help="Influent BOD5 concentration in mg/L"
    )
    parser.add_argument(
        "--Se", type=float, default=20.0,
        help="Effluent BOD5 concentration in mg/L (default: 20)"
    )
    parser.add_argument(
        "--Ls", type=float, default=0.3,
        help="BOD5 sludge loading in kgBOD5/(kgMLSS·d) (default: 0.3)"
    )
    parser.add_argument(
        "--X", type=float, default=3.0,
        help="MLSS concentration in gMLSS/L (default: 3.0)"
    )
    parser.add_argument(
        "--Y", type=float, default=0.5,
        help="Sludge yield coefficient in kgVSS/kgBOD5 (default: 0.5)"
    )
    parser.add_argument(
        "--theta_c", type=float, default=10.0,
        help="Design sludge age in days (default: 10)"
    )
    parser.add_argument(
        "--Xv", type=float, default=2.5,
        help="MLVSS concentration in gMLVSS/L (default: 2.5)"
    )
    parser.add_argument(
        "--Kd20", type=float, default=KD20_DEFAULT,
        help="Decay coefficient at 20°C in d^-1 (default: 0.05)"
    )
    parser.add_argument(
        "--theta_T", type=float, default=THETA_T_DEFAULT,
        help="Temperature coefficient (default: 1.04)"
    )
    parser.add_argument(
        "--T", type=float, default=DEFAULT_T,
        help="Design temperature in °C (default: 12)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Calculate
    result = calc_bioreactor_volume(
        Q_m3d=args.Q_m3d,
        So=args.So,
        Se=args.Se,
        Ls=args.Ls,
        X=args.X,
        Y=args.Y,
        theta_c=args.theta_c,
        Xv=args.Xv,
        Kd20=args.Kd20,
        theta_T=args.theta_T,
        T=args.T
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print("=" * 60)
        print("生物反应池容积计算结果")
        print("=" * 60)
        print(f"按污泥负荷计算容积: {result['volume_by_loading']:.2f} m³")
        print(f"按污泥龄计算容积: {result['volume_by_sludge_age']:.2f} m³")
        print(f"温度校正衰减系数 KdT: {result['KdT']:.4f} d⁻¹")
        print("-" * 60)
        print(f"引用: {result['citation']}")
        print("=" * 60)


if __name__ == "__main__":
    main()