"""
Tests for calc_pump_combined.py - Combined sewer pump station design calculation.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, "scripts")
from calc_pump_combined import calc_pump_combined

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCalcPumpCombined:
    """Test combined sewer pump station calculations."""

    def test_basic_calculation(self):
        """Test basic combined pump calculation."""
        result = calc_pump_combined(
            pre_interception_L_s=500.0,
            post_interception_L_s=150.0,
            static_head_m=5.0,
            head_loss_m=2.0,
            safety_head_m=1.0
        )
        assert result["pre_interception_L_s"] == 500.0
        assert result["post_interception_L_s"] == 150.0
        assert result["design_head_m"] == 8.0
        assert result["static_head_m"] == 5.0
        assert result["head_loss_m"] == 2.0
        assert result["safety_head_m"] == 1.0

    def test_negative_pre_interception_raises(self):
        """Test negative pre-interception flow raises error."""
        with pytest.raises(ValueError, match="Pre-interception flow cannot be negative"):
            calc_pump_combined(-1, 100, 5, 2, 1)

    def test_negative_post_interception_raises(self):
        """Test negative post-interception flow raises error."""
        with pytest.raises(ValueError, match="Post-interception flow cannot be negative"):
            calc_pump_combined(100, -1, 5, 2, 1)

    def test_negative_static_head_raises(self):
        """Test negative static head raises error."""
        with pytest.raises(ValueError, match="Static head cannot be negative"):
            calc_pump_combined(100, 50, -1, 2, 1)

    def test_zero_design_head(self):
        """Test zero design head when all inputs are zero."""
        result = calc_pump_combined(0, 0, 0, 0, 0)
        assert result["design_head_m"] == 0.0

    def test_output_structure(self):
        """Test that output contains all required fields."""
        result = calc_pump_combined(100, 50, 5, 2, 1)
        required_keys = [
            "pre_interception_L_s", "post_interception_L_s",
            "pre_interception_m3s", "post_interception_m3s",
            "design_head_m", "unit", "citation", "citations"
        ]
        for key in required_keys:
            assert key in result

    def test_citation_present(self):
        """Test citation is present and references GB standard."""
        result = calc_pump_combined(100, 50, 5, 2, 1)
        assert "GB 50014-2021" in result["citation"]


class TestCLI:
    """Test command-line interface."""

    def test_cli_json_output(self):
        """Test CLI JSON output."""
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_pump_combined.py",
                    "--pre_interception_L_s", "500",
                    "--post_interception_L_s", "150",
                    "--static_head_m", "5",
                    "--head_loss_m", "2",
                    "--safety_head_m", "1",
                    "--json"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["design_head_m"] == 8.0
        assert output["pre_interception_L_s"] == 500.0

    def test_cli_missing_args_fails(self):
        """Test CLI fails when required args are missing."""
        result = subprocess.run(
                [sys.executable, "scripts/calc_pump_combined.py", "--json"],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
