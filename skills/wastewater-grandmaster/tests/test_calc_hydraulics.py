import subprocess
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from calc_hydraulics import calculate_velocity, calculate_flow, calculate_hydraulics


def test_calculate_velocity_basic():
    # n=0.013, R=0.25m (D=1m half full), slope=0.001
    v = calculate_velocity(0.013, 0.25, 0.001)
    expected = (1 / 0.013) * (0.25 ** (2 / 3)) * (0.001 ** 0.5)
    assert abs(v - expected) < 1e-6


def test_calculate_flow_basic():
    assert abs(calculate_flow(0.5, 1.0) - 0.5) < 1e-9


def test_calculate_hydraulics_full_flow():
    result = calculate_hydraulics(1000, 0.001, "concrete", "sewage", fullness_ratio=1.0)
    assert result["fullness_ratio"] == 1.0
    assert result["max_fullness"] == 0.75
    assert result["min_velocity_m_s"] == 0.6
    assert "flow_m3_s" in result
    assert "flow_L_s" in result


def test_calculate_hydraulics_storm():
    result = calculate_hydraulics(500, 0.003, "plastic", "storm_combined", fullness_ratio=1.0)
    assert result["min_velocity_m_s"] == 0.75
    assert result["max_fullness"] == 0.70


def test_cli_success():
    calc = os.path.join(os.path.dirname(__file__), "..", "scripts", "calc_hydraulics.py")
    result = subprocess.run(
        [sys.executable, calc, "--diameter_mm", "1000", "--slope", "0.01", "--material", "concrete", "--system_type", "sewage"],
        capture_output=True, text=True
    )
    # High slope should give velocity >= min velocity
    data = json.loads(result.stdout)
    assert "velocity_m_s" in data
    assert "citation" in data
    assert "GB 50014-2021" in data["citation"]


def test_cli_json_schema():
    calc = os.path.join(os.path.dirname(__file__), "..", "scripts", "calc_hydraulics.py")
    result = subprocess.run(
        [sys.executable, calc, "--diameter_mm", "300", "--slope", "0.005", "--material", "concrete", "--system_type", "sewage"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    assert "velocity_m_s" in data
    assert "flow_m3_s" in data
    assert "flow_L_s" in data
    assert "fullness_ratio" in data
    assert "max_fullness" in data
    assert "min_velocity_m_s" in data
    assert "citation" in data
    assert "unit" in data
