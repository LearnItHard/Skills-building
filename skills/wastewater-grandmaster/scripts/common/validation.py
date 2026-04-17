"""
Validation and applicability checking for wastewater calculations.
"""

from .citation import make_citation


def check_applicability(domain: str, inputs: dict) -> dict:
    """
    Check if inputs are within the applicable range for a given calculation domain.

    Returns a dict with 'valid' (bool) and 'warnings' (list of str).
    """
    warnings = []
    valid = True

    if domain == "stormwater":
        result = check_storm_applicability(inputs.get("F_hm2", 0))
        if result.get("method_switched"):
            warnings.append(result.get("message", ""))
        valid = result.get("valid", True)

    return {"valid": valid, "warnings": warnings}


def raise_if_out_of_bounds(value: float, min_val: float, max_val: float, clause: str):
    """
    Raise ValueError if value is outside [min_val, max_val], citing the clause.
    """
    if value < min_val or value > max_val:
        citation = make_citation(clause)
        raise ValueError(
            f"Value {value} out of bounds [{min_val}, {max_val}]. {citation}"
        )


def check_storm_applicability(F_hm2: float) -> dict:
    """
    Check stormwater calculation applicability.

    GB 50014-2021 第4.1.7条:
    - F ≤ 2 km² (200 hm²): use rational formula 4.1.9
    - F > 2 km²: must switch method
    """
    F_km2 = F_hm2 / 100.0
    if F_km2 > 2.0:
        return {
            "valid": True,
            "method_switched": True,
            "citation_clause": "4.1.7",
            "message": (
                "汇水面积 > 2 km²，应采用数学模型法计算（"
                + make_citation("4.1.7")
                + "）"
            ),
        }
    return {
        "valid": True,
        "method_switched": False,
        "citation_clause": "4.1.9",
        "message": "",
    }
