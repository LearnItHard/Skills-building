"""
海绵城市年径流总量控制率计算.

根据 GB 50014-2021 附录 A.0.1 计算年径流总量控制率对应的设计降雨量:
- 将多年降雨量数据按从小到大排序
- 计算累积频率（规范方法）
- 根据目标控制率确定设计降雨量

Reference: 附录A.0.1 年径流总量控制率对应的设计降雨量计算方法
"""

import argparse
import json
import sys
from typing import List, Tuple

try:
    from .common.citation import make_citation
except ImportError:
    from common.citation import make_citation


def parse_rainfall_data(rainfall_str: str) -> List[float]:
    """
    Parse rainfall data from JSON string or comma-separated values.

    Args:
        rainfall_str: JSON array string like "[10,20,30]" or comma-separated like "10,20,30"

    Returns:
        List of rainfall depths in mm

    Raises:
        ValueError: If input format is invalid
    """
    rainfall_str = rainfall_str.strip()

    # Try JSON format first
    if rainfall_str.startswith('[') or rainfall_str.startswith('['):
        try:
            return json.loads(rainfall_str)
        except json.JSONDecodeError:
            pass

    # Try comma-separated
    if ',' in rainfall_str:
        try:
            return [float(x.strip()) for x in rainfall_str.split(',')]
        except ValueError:
            raise ValueError(f"Invalid rainfall data format: {rainfall_str}")

    raise ValueError(
        f"Invalid rainfall data format: {rainfall_str}. "
        "Use JSON array like '[10,20,30]' or comma-separated like '10,20,30'"
    )


def sort_rainfall_ascending(rainfall_list: List[float]) -> List[float]:
    """
    Sort rainfall data in ascending order.

    Args:
        rainfall_list: List of annual rainfall depths (mm)

    Returns:
        Sorted list in ascending order
    """
    return sorted(rainfall_list)


def calc_cumulative_frequency(rainfall_sorted: List[float]) -> List[float]:
    """
    Calculate cumulative frequency for each rainfall depth using standard formula.

    Formula (规范方法): P = m / (n + 1)
    where m is the rank (1, 2, ..., n), n is total count

    Args:
        rainfall_sorted: Rainfall data sorted in ascending order

    Returns:
        List of cumulative frequencies (0-1)
    """
    n = len(rainfall_sorted)
    if n == 0:
        return []

    # Cumulative frequency: m/(n+1)
    # m is rank from 1 to n
    return [m / (n + 1) for m in range(1, n + 1)]


def calc_control_rate_from_cumulative(cumulative_freq: List[float]) -> List[float]:
    """
    Calculate control rate from cumulative frequency.

    Control rate = 1 - cumulative frequency (规范方法)

    Args:
        cumulative_freq: List of cumulative frequencies (0-1)

    Returns:
        List of control rates (0-1)
    """
    return [1 - p for p in cumulative_freq]


def find_design_rainfall(
    rainfall_sorted: List[float],
    control_rates: List[float],
    target_control_rate: float
) -> Tuple[float, float]:
    """
    Find design rainfall for given target control rate.

    Uses exact matching or interpolation if target is between values.

    Args:
        rainfall_sorted: Sorted rainfall depths
        control_rates: Corresponding control rates
        target_control_rate: Target control rate (0-1)

    Returns:
        Tuple of (design_rainfall_mm, actual_control_rate)

    Raises:
        ValueError: If target is outside valid range
    """
    if not rainfall_sorted:
        raise ValueError("No rainfall data provided")

    if target_control_rate < 0 or target_control_rate > 1:
        raise ValueError(f"Target control rate must be 0-1, got {target_control_rate}")

    # Find the rainfall depth where control rate >= target
    n = len(rainfall_sorted)

    # control_rates is in descending order: [0.833, 0.667, 0.5, 0.333, 0.167]
    # Boundary: target exceeds max control rate
    if target_control_rate > control_rates[0]:
        return rainfall_sorted[0], control_rates[0]

    # Boundary: target below min control rate
    if target_control_rate < control_rates[-1]:
        return rainfall_sorted[-1], control_rates[-1]

    # Find: control_rate <= target (i.e., this rainfall gives at most target control rate)
    # Example: target=0.5 → control_rate 0.5 at index 2 → rainfall 30mm
    for i, cr in enumerate(control_rates):
        if cr <= target_control_rate:
            return rainfall_sorted[i], cr

    # Fallback (shouldn't reach here)
    return rainfall_sorted[-1], control_rates[-1]


def find_design_rainfall_interpolation(
    rainfall_sorted: List[float],
    control_rates: List[float],
    target_control_rate: float
) -> Tuple[float, float]:
    """
    Find design rainfall using linear interpolation.

    This is an engineering convenience method only.
    Should be used with caution - not the standard method.

    Args:
        rainfall_sorted: Sorted rainfall depths
        control_rates: Corresponding control rates
        target_control_rate: Target control rate (0-1)

    Returns:
        Tuple of (interpolated_design_rainfall_mm, actual_control_rate)
    """
    if not rainfall_sorted:
        raise ValueError("No rainfall data provided")

    n = len(rainfall_sorted)

    # control_rates is in descending order: [0.833, 0.667, 0.5, 0.333, 0.167]
    # Boundary: target exceeds max control rate
    if target_control_rate > control_rates[0]:
        return rainfall_sorted[0], control_rates[0]
    # Boundary: target below min control rate
    if target_control_rate < control_rates[-1]:
        return rainfall_sorted[-1], control_rates[-1]

    # Linear interpolation between two points in descending order
    for i in range(n - 1):
        p_high, p_low = control_rates[i], control_rates[i + 1]  # e.g., 0.75, 0.5
        r_high, r_low = rainfall_sorted[i], rainfall_sorted[i + 1]  # 10, 20

        # Find where target is between p_low and p_high (inclusive)
        if p_low <= target_control_rate <= p_high:
            # Interpolate: r = r_low + (target - p_low) / (p_high - p_low) * (r_high - r_low)
            if abs(p_high - p_low) < 1e-9:
                return r_low, target_control_rate

            ratio = (target_control_rate - p_low) / (p_high - p_low)
            design_rainfall = r_low + ratio * (r_high - r_low)
            return design_rainfall, target_control_rate

            return design_rainfall, target_control_rate

    # Fallback
    return rainfall_sorted[-1], control_rates[-1]


def main():
    parser = argparse.ArgumentParser(
        description="计算海绵城市年径流总量控制率对应的设计降雨量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python calc_sponge_city.py --rainfall_mm "[10,20,30,40,50]"
  python calc_sponge_city.py --rainfall_mm "10,20,30,40,50" --target_control_rate 0.8
  python calc_sponge_city.py --rainfall_mm "[10,20,30]" --method sorting
        """
    )
    parser.add_argument(
        "--rainfall_mm",
        type=str,
        required=True,
        help="年降雨量数据，JSON数组如'[10,20,30]'或逗号分隔如'10,20,30'"
    )
    parser.add_argument(
        "--target_control_rate",
        type=float,
        default=None,
        help="目标控制率 (0-1)，如0.8表示80%%"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["sorting", "interpolation"],
        default="sorting",
        help="计算方法: sorting=规范方法(默认), interpolation=线性插值(工程便捷法)"
    )

    args = parser.parse_args()

    # Parse rainfall data
    try:
        rainfall_data = parse_rainfall_data(args.rainfall_mm)
    except ValueError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

    if len(rainfall_data) < 2:
        print(json.dumps({
            "error": "至少需要2个降雨量数据点"
        }), file=sys.stderr)
        sys.exit(1)

    # Sort ascending
    rainfall_sorted = sort_rainfall_ascending(rainfall_data)

    # Calculate cumulative frequency
    cum_freq = calc_cumulative_frequency(rainfall_sorted)

    # Calculate control rate
    control_rates = calc_control_rate_from_cumulative(cum_freq)

    # Build output
    result = {
        "rainfall_sorted": rainfall_sorted,
        "control_rate": control_rates,
        "method": args.method,
        "unit": "mm",
    }

    # Add citation
    result["citation"] = make_citation(
        "附录A.0.1",
        "附录A-年径流总量控制率对应的设计降雨量计算方法"
    )

    # If target provided, calculate design rainfall
    if args.target_control_rate is not None:
        target = args.target_control_rate

        if args.method == "interpolation":
            design_rainfall, actual_rate = find_design_rainfall_interpolation(
                rainfall_sorted, control_rates, target
            )
        else:
            design_rainfall, actual_rate = find_design_rainfall(
                rainfall_sorted, control_rates, target
            )

        result["design_rainfall_mm"] = round(design_rainfall, 2)
        result["target_control_rate"] = target
        result["actual_control_rate"] = round(actual_rate, 4)

    # Print JSON output
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result


if __name__ == "__main__":
    main()