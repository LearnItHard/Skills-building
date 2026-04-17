"""
Tests for calc_sponge_city.py -海绵城市年径流总量控制率计算.

Tests cover:
- 降雨量数据解析 (JSON/CSV)
- 升序排序
- 累积频率计算 (规范方法: m/(n+1))
- 控制率计算 (1 - 累积频率)
- 设计降雨量查找 (精确匹配/线性插值)
- CLI 输出结构验证
"""

import json
import os
import subprocess
import sys

import pytest

# Import the module directly for unit tests
sys.path.insert(0, "scripts")
from calc_sponge_city import (
    parse_rainfall_data,
    sort_rainfall_ascending,
    calc_cumulative_frequency,
    calc_control_rate_from_cumulative,
    find_design_rainfall,
    find_design_rainfall_interpolation,
)

# Get absolute path to skill root
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestParseRainfallData:
    """Test rainfall data parsing."""

    def test_parse_json_array(self):
        """Test parsing JSON array string."""
        data = parse_rainfall_data("[10,20,30]")
        assert data == [10.0, 20.0, 30.0]

    def test_parse_json_array_no_spaces(self):
        """Test parsing JSON array without spaces."""
        data = parse_rainfall_data("[10,20,30,40,50]")
        assert data == [10.0, 20.0, 30.0, 40.0, 50.0]

    def test_parse_csv(self):
        """Test parsing comma-separated values."""
        data = parse_rainfall_data("10,20,30")
        assert data == [10.0, 20.0, 30.0]

    def test_parse_csv_with_spaces(self):
        """Test parsing CSV with spaces."""
        data = parse_rainfall_data("10, 20, 30")
        assert data == [10.0, 20.0, 30.0]

    def test_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_rainfall_data("invalid")


class TestSortRainfall:
    """Test rainfall sorting."""

    def test_sort_ascending(self):
        """Test sorting in ascending order."""
        rainfall = [30, 10, 20]
        sorted_data = sort_rainfall_ascending(rainfall)
        assert sorted_data == [10, 20, 30]

    def test_sort_already_sorted(self):
        """Test that already sorted data remains sorted."""
        rainfall = [10, 20, 30]
        sorted_data = sort_rainfall_ascending(rainfall)
        assert sorted_data == [10, 20, 30]

    def test_sort_descending(self):
        """Test sorting descending data."""
        rainfall = [50, 40, 30, 20, 10]
        sorted_data = sort_rainfall_ascending(rainfall)
        assert sorted_data == [10, 20, 30, 40, 50]


class TestCumulativeFrequency:
    """Test cumulative frequency calculation."""

    def test_formula_m_over_n_plus_1(self):
        """Test formula: m/(n+1)."""
        rainfall = [10, 20, 30, 40, 50]  # n = 5
        # m=1: 1/6 = 0.1667
        # m=2: 2/6 = 0.3333
        # m=3: 3/6 = 0.5
        # m=4: 4/6 = 0.6667
        # m=5: 5/6 = 0.8333
        cum_freq = calc_cumulative_frequency(rainfall)
        assert len(cum_freq) == 5
        assert cum_freq[0] == pytest.approx(1/6, rel=0.001)
        assert cum_freq[-1] == pytest.approx(5/6, rel=0.001)

    def test_single_value(self):
        """Test with single value."""
        rainfall = [30]
        cum_freq = calc_cumulative_frequency(rainfall)
        assert cum_freq == [0.5]  # 1/(1+1) = 0.5

    def test_empty_list(self):
        """Test with empty list returns empty."""
        rainfall = []
        cum_freq = calc_cumulative_frequency(rainfall)
        assert cum_freq == []


class TestControlRate:
    """Test control rate calculation."""

    def test_control_rate_from_cumulative(self):
        """Test: control rate = 1 - cumulative frequency."""
        cum_freq = [0.1, 0.3, 0.5, 0.7, 0.9]
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        expected = [0.9, 0.7, 0.5, 0.3, 0.1]
        # Use approx for floating point comparison
        for i in range(len(expected)):
            assert control_rates[i] == pytest.approx(expected[i], rel=1e-6)

    def test_example_data(self):
        """Test with example data [10,20,30,40,50]."""
        rainfall = [10, 20, 30, 40, 50]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        # control rates: 5/6, 4/6, 3/6, 2/6, 1/6
        # = 0.8333, 0.6667, 0.5, 0.3333, 0.1667
        assert control_rates[0] == pytest.approx(5/6, rel=0.001)
        assert control_rates[-1] == pytest.approx(1/6, rel=0.001)


class TestFindDesignRainfall:
    """Test design rainfall lookup."""

    def test_exact_match(self):
        """Test exact match of target control rate."""
        rainfall = [10, 20, 30, 40, 50]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)

        # Target 0.5: find control_rate <= 0.5
        # control_rates: [0.833, 0.667, 0.5, 0.333, 0.167]
        # At index 2, control_rate = 0.5 <= 0.5 → rainfall 30mm
        design_rain, actual_rate = find_design_rainfall(rainfall, control_rates, 0.5)
        assert design_rain == 30
        assert actual_rate == pytest.approx(0.5, rel=0.001)

    def test_target_above_max_control_rate(self):
        """Test target > max control rate returns min rainfall."""
        # n=3: cum_freq = [0.25, 0.5, 0.75], control_rates = [0.75, 0.5, 0.25]
        rainfall = [10, 20, 30]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        # max control_rate = 0.75 at rainfall 10mm
        # target 0.99 > 0.75 → returns min rainfall 10mm
        design_rain, actual_rate = find_design_rainfall(rainfall, control_rates, 0.99)
        assert design_rain == 10
        assert actual_rate == pytest.approx(0.75, rel=0.001)

    def test_target_below_min_control_rate(self):
        """Test target < min control rate returns max rainfall."""
        # target=0.01 < min control_rate=0.167 for 3 items
        rainfall = [10, 20, 30]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        # control_rates: [0.667, 0.333, 0.167]
        # index 2: 0.167 <= 0.01 is false (0.167 > 0.01)
        # need to find first where control <= 0.01
        # none, so return max
        design_rain, actual_rate = find_design_rainfall(rainfall, control_rates, 0.01)
        # None <= 0.01, should return max rainfall
        assert design_rain == 30

    def test_target_zero(self):
        """Test target control rate of 0 returns max rainfall."""
        rainfall = [10, 20, 30, 40, 50]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        # target 0 < min control rate → return largest rainfall
        design_rain, actual_rate = find_design_rainfall(rainfall, control_rates, 0.0)
        assert design_rain == 50

    def test_empty_data_raises(self):
        """Test empty data raises ValueError."""
        with pytest.raises(ValueError):
            find_design_rainfall([], [], 0.5)


class TestFindDesignRainfallInterpolation:
    """Test linear interpolation method."""

    def test_basic_interpolation(self):
        """Test basic linear interpolation."""
        rainfall = [10, 20, 30, 40, 50]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)

        # Interpolate at exactly middle
        design_rain, actual_rate = find_design_rainfall_interpolation(
            rainfall, control_rates, 0.5
        )
        assert design_rain == 30

    def test_between_points(self):
        """Test interpolation between two points."""
        rainfall = [10, 20, 30]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        # control_rates: [0.75, 0.5, 0.25] for n=3
        # Target 0.25 exactly matches last value, should return 30mm
        design_rain, actual_rate = find_design_rainfall_interpolation(
            rainfall, control_rates, 0.25
        )
        assert design_rain == 30

    def test_interpolation_midpoint(self):
        """Test interpolation at midpoint between two control rates."""
        rainfall = [10, 20, 30]
        cum_freq = calc_cumulative_frequency(rainfall)
        control_rates = calc_control_rate_from_cumulative(cum_freq)
        # control_rates: [0.75, 0.5, 0.25]
        # Target 0.375 is between 0.5 (20mm) and 0.75 (10mm)
        # Interpolation: 0.5->20mm, 0.75->10mm
        # (0.375-0.5)/(0.75-0.5) = -0.125/0.25 = -0.5
        # r = 20 + (-0.5)*(10-20) = 20 + 5 = 25
        design_rain, actual_rate = find_design_rainfall_interpolation(
            rainfall, control_rates, 0.375
        )
        assert 24 < design_rain < 26


class TestCLI:
    """Test command-line interface."""

    def test_json_array_input(self):
        """Test JSON array input."""
        result = subprocess.run(
                [sys.executable, "scripts/calc_sponge_city.py", "--rainfall_mm", "[10,20,30,40,50]"],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        assert "rainfall_sorted" in output
        assert "control_rate" in output
        assert output["rainfall_sorted"] == [10, 20, 30, 40, 50]

    def test_csv_input(self):
        """Test comma-separated input."""
        result = subprocess.run(
                [sys.executable, "scripts/calc_sponge_city.py", "--rainfall_mm", "10,20,30"],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        assert "rainfall_sorted" in output
        assert output["rainfall_sorted"] == [10, 20, 30]

    def test_with_target_control_rate(self):
        """Test with target control rate."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_sponge_city.py",
                    "--rainfall_mm", "[10,20,30,40,50]",
                    "--target_control_rate", "0.5"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        assert "design_rainfall_mm" in output
        assert output["design_rainfall_mm"] == 30
        assert output["target_control_rate"] == 0.5

    def test_method_interpolation(self):
        """Test interpolation method."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_sponge_city.py",
                    "--rainfall_mm", "[10,20,30]",
                    "--target_control_rate", "0.3",
                    "--method", "interpolation"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        assert output["method"] == "interpolation"
        # n=3: control_rates = [0.75, 0.5, 0.25]
        # 0.3 is between 0.5 (20mm) and 0.25 (30mm)
        # interpolation should give around 28mm
        assert 25 < output["design_rainfall_mm"] < 30

    def test_default_method_is_sorting(self):
        """Test that default method is sorting."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_sponge_city.py",
                    "--rainfall_mm", "[10,20,30]"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        assert output["method"] == "sorting"

    def test_output_structure(self):
        """Test output contains all required fields."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_sponge_city.py",
                    "--rainfall_mm", "[10,20,30,40,50]",
                    "--target_control_rate", "0.8"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)

        # Required fields
        assert "rainfall_sorted" in output
        assert "control_rate" in output
        assert "method" in output
        assert "unit" in output
        assert "citation" in output
        assert "design_rainfall_mm" in output
        assert "target_control_rate" in output
        assert "actual_control_rate" in output

        # Values are valid
        assert output["unit"] == "mm"
        assert output["method"] == "sorting"

    def test_insufficient_data_error(self):
        """Test error with less than 2 data points."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_sponge_city.py",
                    "--rainfall_mm", "[10]"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 1
        error = json.loads(result.stderr)
        assert "error" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])