"""
Tests for calc_pump_sewage.py - Sewage pump station design calculation.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, "scripts")
from calc_pump_sewage import calc_pump_sewage

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCalcPumpSewage:
    """Test sewage pump station calculations."""

    def test_basic_calculation(self):
        """Test basic sewage pump calculation."""
        result = calc_pump_sewage(
            design_flow_L_s=100.0,
            static_head_m=5.0,
            head_loss_m=2.0,
            safety_head_m=1.0,
            max_pump_flow_L_s=120.0
        )
        assert result["design_flow_L_s"] == 100.0
        assert result["design_head_m"] == 8.0
        # sump_volume = 120 L/s * 300 s / 1000 = 36 m³
        assert result["sump_volume_m3"] == 36.0

    def test_zero_design_flow_raises(self):
        """Test zero design flow raises error."""
        with pytest.raises(ValueError, match="Design flow must be positive"):
            calc_pump_sewage(0, 5, 2, 1, 120)

    def test_negative_design_flow_raises(self):
        """Test negative design flow raises error."""
        with pytest.raises(ValueError, match="Design flow must be positive"):
            calc_pump_sewage(-10, 5, 2, 1, 120)

    def test_negative_static_head_raises(self):
        """Test negative static head raises error."""
        with pytest.raises(ValueError, match="Static head cannot be negative"):
            calc_pump_sewage(100, -1, 2, 1, 120)

    def test_negative_head_loss_raises(self):
        """Test negative head loss raises error."""
        with pytest.raises(ValueError, match="Head loss cannot be negative"):
            calc_pump_sewage(100, 5, -1, 1, 120)

    def test_negative_safety_head_raises(self):
        """Test negative safety head raises error."""
        with pytest.raises(ValueError, match="Safety head cannot be negative"):
            calc_pump_sewage(100, 5, 2, -1, 120)

    def test_zero_max_pump_flow_raises(self):
        """Test zero max pump flow raises error."""
        with pytest.raises(ValueError, match="Max pump flow must be positive"):
            calc_pump_sewage(100, 5, 2, 1, 0)

    def test_sump_volume_calculation(self):
        """Test sump volume is 5 minutes of max pump flow."""
        result = calc_pump_sewage(50, 3, 1, 0.5, 80)
        # 80 L/s * 300 s / 1000 = 24 m³
        assert result["sump_volume_m3"] == 24.0

    def test_output_structure(self):
        """Test that output contains all required fields."""
        result = calc_pump_sewage(100, 5, 2, 1, 120)
        required_keys = [
            "design_flow_L_s", "design_head_m", "sump_volume_m3",
            "unit", "citation", "citations"
        ]
        for key in required_keys:
            assert key in result

    def test_citation_present(self):
        """Test citation references GB standard."""
        result = calc_pump_sewage(100, 5, 2, 1, 120)
        assert "GB 50014-2021" in result["citation"]


class TestCLI:
    """Test command-line interface."""

    def test_cli_json_output(self):
        """Test CLI JSON output."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_pump_sewage.py",
                    "--design_flow_L_s", "100",
                    "--static_head_m", "5",
                    "--head_loss_m", "2",
                    "--safety_head_m", "1",
                    "--max_pump_flow_L_s", "120",
                    "--json"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["design_head_m"] == 8.0
        assert output["sump_volume_m3"] == 36.0

    def test_cli_missing_args_fails(self):
        """Test CLI fails when required args are missing."""
        result = subprocess.run(
                [sys.executable, "scripts/calc_pump_sewage.py", "--json"],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
