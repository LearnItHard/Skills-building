"""
Tests for calc_storm_flow.py - storm flow calculation.

Tests cover:
- Rainfall intensity formula 4.1.9
- Design flow Q = ψ * q * F
- Time of concentration t = t1 + t2
- Applicability check for F > 2 km² (200 hm²)
"""

import json
import os
import subprocess
import sys

import pytest

# Import the module directly for unit tests
sys.path.insert(0, "scripts")
from calc_storm_flow import (
    calc_rainfall_intensity,
    calc_design_flow,
    calc_total_time,
)

# Get absolute path to skill root
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCalcRainfallIntensity:
    """Test rainfall intensity calculation using formula 4.1.9."""

    def test_basic_calculation(self):
        """Test basic rainfall intensity calculation."""
        # Given: A1=1.0, C=0.45, P=10, b=8, n=0.5, t=30
        # Expected: q = 167 * 1.0 * (1 + 0.45 * log10(10)) / (30 + 8)^0.5
        # log10(10) = 1, so (1 + 0.45 * 1) = 1.45
        # (30 + 8) = 38, sqrt(38) = 6.1644
        # q = 167 * 1.45 / 6.1644 = 39.23 L/s·hm²
        q = calc_rainfall_intensity(A1=1.0, C=0.45, P=10, b=8, n=0.5, t=30)
        assert 39.0 < q < 40.0  # Should be approximately 39.23

    def test_higher_P_increases_intensity(self):
        """Test that higher recurrence interval increases intensity."""
        q1 = calc_rainfall_intensity(A1=1.0, C=0.5, P=5, b=10, n=0.6, t=20)
        q2 = calc_rainfall_intensity(A1=1.0, C=0.5, P=50, b=10, n=0.6, t=20)
        assert q2 > q1

    def test_higher_duration_decreases_intensity(self):
        """Test that longer duration decreases intensity."""
        q1 = calc_rainfall_intensity(A1=1.0, C=0.5, P=10, b=8, n=0.5, t=10)
        q2 = calc_rainfall_intensity(A1=1.0, C=0.5, P=10, b=8, n=0.5, t=60)
        assert q2 < q1


class TestCalcDesignFlow:
    """Test design flow calculation using Q = ψ * q * F."""

    def test_basic_calculation(self):
        """Test basic design flow calculation."""
        # Q = ψ * q * F = 0.5 * 100 * 10 = 500 L/s
        Q = calc_design_flow(psi=0.5, q=100, F=10)
        assert Q == 500.0

    def test_runoff_coefficient_effect(self):
        """Test that higher runoff coefficient increases flow."""
        Q1 = calc_design_flow(psi=0.3, q=100, F=10)
        Q2 = calc_design_flow(psi=0.9, q=100, F=10)
        assert Q2 > Q1

    def test_area_effect(self):
        """Test that larger area increases flow."""
        Q1 = calc_design_flow(psi=0.5, q=100, F=5)
        Q2 = calc_design_flow(psi=0.5, q=100, F=15)
        assert Q2 > Q1


class TestCalcTotalTime:
    """Test total time of concentration calculation."""

    def test_addition(self):
        """Test that total time is sum of t1 and t2."""
        t = calc_total_time(10, 15)
        assert t == 25

    def test_zero_values(self):
        """Test with zero time values."""
        t = calc_total_time(0, 30)
        assert t == 30


class TestCLI:
    """Test command-line interface."""

    def test_normal_area_no_method_switch(self):
        """Test that F=10 hm² (0.1 km²) doesn't trigger method switch."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_storm_flow.py",
                    "--A1", "1.0",
                    "--C", "0.45",
                    "--P", "10",
                    "--b", "8",
                    "--n", "0.5",
                    "--t1", "10",
                    "--t2", "5",
                    "--psi", "0.5",
                    "--F", "10"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        assert output["applicability"]["method_switched"] is False
        assert output["design_flow"] > 0
        assert "rainfall_intensity" in output

    def test_large_area_triggers_method_switch(self):
        """Test that F=250 hm² (2.5 km²) triggers method_switched: true."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_storm_flow.py",
                    "--A1", "1.0",
                    "--C", "0.45",
                    "--P", "10",
                    "--b", "8",
                    "--n", "0.5",
                    "--t1", "10",
                    "--t2", "5",
                    "--psi", "0.5",
                    "--F", "250"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        # Should exit normally (code 0), but JSON should have method_switched: true
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["applicability"]["method_switched"] is True

    def test_boundary_area_200_hm2(self):
        """Test boundary case: F=200 hm² (exactly 2 km²)."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_storm_flow.py",
                    "--A1", "1.0",
                    "--C", "0.45",
                    "--P", "10",
                    "--b", "8",
                    "--n", "0.5",
                    "--t1", "10",
                    "--t2", "5",
                    "--psi", "0.5",
                    "--F", "200"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)
        # 200 hm² = 2 km², exactly at boundary, should NOT switch
        assert output["applicability"]["method_switched"] is False

    def test_output_structure(self):
        """Test that output contains all required fields."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_storm_flow.py",
                    "--A1", "1.0",
                    "--C", "0.45",
                    "--P", "10",
                    "--b", "8",
                    "--n", "0.5",
                    "--t1", "10",
                    "--t2", "5",
                    "--psi", "0.5",
                    "--F", "50"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        output = json.loads(result.stdout)

        # Check required fields
        assert "rainfall_intensity" in output
        assert "design_flow" in output
        assert "total_time" in output
        assert "unit" in output
        assert "citation" in output
        assert "applicability" in output

        # Check applicability fields
        assert "method_switched" in output["applicability"]
        assert "valid" in output["applicability"]
        assert "citation_clause" in output["applicability"]
        assert "message" in output["applicability"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])