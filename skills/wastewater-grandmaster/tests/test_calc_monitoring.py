"""
Tests for calc_monitoring.py - Online instrument and smart drainage checks.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, "scripts")
from calc_monitoring import check_online_instruments, check_smart_drainage_basic_items, REQUIRED_INSTRUMENTS, SMART_DRAINAGE_ITEMS

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestOnlineInstruments:
    """Test online instrument configuration checks."""

    def test_wwtp_all_installed(self):
        installed = REQUIRED_INSTRUMENTS["wwtp"]
        result = check_online_instruments("wwtp", installed)
        assert result["status"] == "PASS"
        assert result["missing"] == []

    def test_wwtp_missing_one(self):
        installed = ["flow_meter", "level_meter", "ph_meter", "cod_meter"]
        result = check_online_instruments("wwtp", installed)
        assert result["status"] == "FAIL"
        assert "nh3n_meter" in result["missing"]

    def test_pump_station_pass(self):
        installed = ["flow_meter", "level_meter"]
        result = check_online_instruments("pump_station", installed)
        assert result["status"] == "PASS"

    def test_unknown_facility(self):
        result = check_online_instruments("space_station", ["flow_meter"])
        assert result["status"] == "UNKNOWN"


class TestSmartDrainage:
    """Test smart drainage basic items check."""

    def test_all_items_enabled(self):
        result = check_smart_drainage_basic_items(SMART_DRAINAGE_ITEMS)
        assert result["status"] == "PASS"
        assert result["missing_items"] == []

    def test_missing_one_item(self):
        enabled = SMART_DRAINAGE_ITEMS.copy()
        enabled.remove("emergency_warning")
        result = check_smart_drainage_basic_items(enabled)
        assert result["status"] == "FAIL"
        assert "emergency_warning" in result["missing_items"]

    def test_empty_items(self):
        result = check_smart_drainage_basic_items([])
        assert result["status"] == "FAIL"
        assert len(result["missing_items"]) == len(SMART_DRAINAGE_ITEMS)


class TestCLI:
    """Test command-line interface."""

    def test_cli_wwtp_pass(self):
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_monitoring.py",
                    "--facility_type", "wwtp",
                    "--installed", "flow_meter,level_meter,ph_meter,cod_meter,nh3n_meter"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["overall_status"] == "PASS"

    def test_cli_smart_drainage_fail(self):
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_monitoring.py",
                    "--smart_items", "big_data_management,internet_application"
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["overall_status"] == "FAIL"

    def test_cli_combined_checks(self):
        result = subprocess.run(
                [
                    sys.executable, "scripts/calc_monitoring.py",
                    "--facility_type", "pump_station",
                    "--installed", "flow_meter,level_meter",
                    "--smart_items", ",".join(SMART_DRAINAGE_ITEMS)
                ],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["overall_status"] == "PASS"
        assert len(output["checks"]) == 2

    def test_cli_no_args_exits_with_help(self):
        result = subprocess.run(
                [sys.executable, "scripts/calc_monitoring.py"],
                capture_output=True, text=True, cwd=SKILL_ROOT, encoding='utf-8', errors='replace'
            )
        assert result.returncode == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
