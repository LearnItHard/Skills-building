"""
Tests for calc_sludge.py - digester volume calculation.

Tests cover:
- Volume by time formula (8.3.6-1): V = Q0 * td
- Volume by load formula (8.3.6-2): V = Ws / Lv
- Gas production estimate with disclaimer
"""

import json
import os
import subprocess
import sys

import pytest

# Import the module directly for unit tests
sys.path.insert(0, "scripts")
from calc_sludge import (
    calc_volume_by_time,
    calc_volume_by_load,
    calc_gas_estimate,
)

# Get absolute path to skill root
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCalcVolumeByTime:
    """Test volume calculation using formula 8.3.6-1: V = Q0 * td."""

    def test_basic_calculation(self):
        """Test basic volume by time calculation."""
        # V = Q0 * td = 100 * 20 = 2000 m³
        V = calc_volume_by_time(Q0_m3d=100, td_d=20)
        assert V == 2000.0

    def test_zero_time(self):
        """Test with zero digestion time."""
        V = calc_volume_by_time(Q0_m3d=100, td_d=0)
        assert V == 0.0

    def test_fractional_time(self):
        """Test with fractional digestion time."""
        V = calc_volume_by_time(Q0_m3d=100, td_d=15.5)
        assert V == 1550.0


class TestCalcVolumeByLoad:
    """Test volume calculation using formula 8.3.6-2: V = Ws / Lv."""

    def test_basic_calculation(self):
        """Test basic volume by load calculation."""
        # V = Ws / Lv = 2000 / 1.5 = 1333.33... m³
        V = calc_volume_by_load(Ws_kg_d=2000, Lv_kg_m3d=1.5)
        assert 1333.0 < V < 1334.0

    def test_high_load(self):
        """Test with higher volumetric loading."""
        # Higher Lv means smaller volume needed
        V1 = calc_volume_by_load(Ws_kg_d=1000, Lv_kg_m3d=1.0)
        V2 = calc_volume_by_load(Ws_kg_d=1000, Lv_kg_m3d=2.0)
        assert V2 < V1

    def test_zero_loading_raises_error(self):
        """Test that zero loading raises ValueError."""
        with pytest.raises(ValueError):
            calc_volume_by_load(Ws_kg_d=100, Lv_kg_m3d=0)

    def test_negative_loading_raises_error(self):
        """Test that negative loading raises ValueError."""
        with pytest.raises(ValueError):
            calc_volume_by_load(Ws_kg_d=100, Lv_kg_m3d=-1)


class TestCalcGasEstimate:
    """Test gas production estimation."""

    def test_default_yield(self):
        """Test gas estimate with default yield (0.8 m³/kg)."""
        # Q_gas = Ws * 0.8 = 1000 * 0.8 = 800 m³/d
        gas = calc_gas_estimate(Ws_kg_d=1000)
        assert gas == 800.0

    def test_custom_yield(self):
        """Test gas estimate with custom yield."""
        gas = calc_gas_estimate(Ws_kg_d=1000, gas_yield_m3_kg=1.0)
        assert gas == 1000.0

    def test_low_yield(self):
        """Test gas estimate with lower yield."""
        gas = calc_gas_estimate(Ws_kg_d=500, gas_yield_m3_kg=0.5)
        assert gas == 250.0


class TestCLI:
    """Test command-line interface."""

    def test_basic_calculation(self):
        """Test basic CLI calculation without gas estimate."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_sludge.py",
                    "--Q0_m3d", "100",
                    "--td_d", "20",
                    "--Ws_kg_d", "2000",
                    "--Lv_kg_m3d", "1.5"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Check required fields
        assert "volume_by_time" in output
        assert "volume_by_load" in output
        assert "unit" in output
        assert "citation" in output

        # Check values
        assert output["volume_by_time"] == 2000.0
        assert 1333.0 < output["volume_by_load"] < 1334.0
        assert output["unit"] == "m³"
        assert "8.3.6" in output["citation"]

        # Should NOT have gas fields
        assert "gas_estimate_m3d" not in output
        assert "disclaimer" not in output

    def test_with_gas_estimate(self):
        """Test CLI with gas estimation enabled."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_sludge.py",
                    "--Q0_m3d", "100",
                    "--td_d", "20",
                    "--Ws_kg_d", "1000",
                    "--Lv_kg_m3d", "1.0",
                    "--estimate_gas"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Should have gas fields
        assert "gas_estimate_m3d" in output
        assert "disclaimer" in output
        assert output["gas_estimate_m3d"] == 800.0
        assert "非 GB 50014-2021 正文公式" in output["disclaimer"]

    def test_with_custom_gas_yield(self):
        """Test CLI with custom gas yield."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_sludge.py",
                    "--Q0_m3d", "100",
                    "--td_d", "20",
                    "--Ws_kg_d", "500",
                    "--Lv_kg_m3d", "1.0",
                    "--estimate_gas",
                    "--gas_yield_m3_kg", "0.6"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        assert output["gas_estimate_m3d"] == 300.0

    def test_missing_required_args_fails(self):
        """Test that missing required arguments fails."""
        result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calc_sludge.py",
                    "--Q0_m3d", "100"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])