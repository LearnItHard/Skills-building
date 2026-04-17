"""
Tests for calc_clearance.py - Pipe clearance checks based on GB 50014-2021 Appendix C.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, "scripts")
from calc_clearance import check_clearance, CLEARANCE_DATA, _parse_clearance_data, APPENDIX_C_PATH

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestParseClearanceData:
    """Test Appendix C data parsing."""

    def test_data_not_empty(self):
        assert len(CLEARANCE_DATA) > 0

    def test_building_deep_has_values(self):
        info = CLEARANCE_DATA["building_deep"]
        assert info["horizontal_m"] == 3.00
        assert info["vertical_m"] is None

    def test_water_supply_small(self):
        info = CLEARANCE_DATA["water_supply_small"]
        assert info["horizontal_m"] == 1.00
        assert info["vertical_m"] == 0.40

    def test_gas_high_2(self):
        info = CLEARANCE_DATA["gas_high_2"]
        assert info["horizontal_m"] == 2.00
        assert info["vertical_m"] == 0.15

    def test_railway(self):
        info = CLEARANCE_DATA["railway"]
        assert info["horizontal_m"] == 5.00
        assert info["vertical_m"] == 1.20
        assert "轨底" in info["notes"]

    def test_reference_file_exists(self):
        assert os.path.exists(APPENDIX_C_PATH)


class TestCheckClearance:
    """Test clearance lookup function."""

    def test_valid_structure(self):
        result = check_clearance("building_deep")
        assert result["status"] == "INFO"
        assert result["horizontal_m"] == 3.00
        assert "建筑物" in result["structure_name"]

    def test_unknown_structure(self):
        result = check_clearance("alien_tower")
        assert result["status"] == "UNKNOWN"
        assert "Unknown structure type" in result["message"]


class TestCLI:
    """Test command-line interface."""

    def test_cli_building_deep(self):
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_clearance.py",
                    "--structure_type", "building_deep"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["result"]["horizontal_m"] == 3.00
        assert "GB 50014-2021" in output["citation"]

    def test_cli_gas_medium(self):
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_clearance.py",
                    "--structure_type", "gas_medium"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["result"]["horizontal_m"] == 1.20
        assert output["result"]["vertical_m"] == 0.15

    def test_cli_missing_arg_fails(self):
        result = subprocess.run(
                [sys.executable, "scripts/calc_clearance.py"],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
