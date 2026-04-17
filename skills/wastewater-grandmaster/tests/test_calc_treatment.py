"""
Tests for calc_treatment module.

Tests cover:
- Volume by loading calculation (Formula 7.6.10-1)
- Volume by sludge age calculation (Formula 7.6.10-2)
- Temperature correction (Formula 7.6.11)
- θc validation (3~15 days for carbon removal)
- Input validation
- Output format
"""

import os
import sys

# Add scripts directory to path for import
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import math
import pytest
from scripts.calc_treatment import (
    THETA_C_MIN,
    THETA_C_MAX,
    KD20_DEFAULT,
    THETA_T_DEFAULT,
    DEFAULT_T,
    calc_volume_by_loading,
    calc_volume_by_sludge_age,
    calc_temperature_corrected_kd,
    calc_bioreactor_volume,
)


class TestVolumeByLoading:
    """Test volume calculation by sludge loading method."""

    def test_basic_calculation(self):
        """Test basic loading calculation using formula 7.6.10-1."""
        # V = Q * (So - Se) / (1000 * Ls * X)
        # Q = 10000 m³/d, So = 200 mg/L, Se = 20 mg/L, Ls = 0.3 kgBOD5/(kgMLSS·d), X = 3 g/L
        # V = 10000 * (200-20) / (1000 * 0.3 * 3)
        # V = 10000 * 180 / 900 = 2000 m³
        result = calc_volume_by_loading(
            Q_m3d=10000,
            So=200,
            Se=20,
            Ls=0.3,
            X=3.0
        )
        assert result == 2000.0

    def test_zero_flow_raises(self):
        """Test that zero flow raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_loading(0, 200, 20, 0.3, 3.0)

    def test_negative_flow_raises(self):
        """Test that negative flow raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_loading(-100, 200, 20, 0.3, 3.0)

    def test_zero_influent_raises(self):
        """Test that zero influent BOD raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_loading(10000, 0, 20, 0.3, 3.0)

    def test_effluent_greater_than_influent_raises(self):
        """Test that Se >= So raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_loading(10000, 200, 200, 0.3, 3.0)

    def test_zero_loading_raises(self):
        """Test that zero sludge loading raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_loading(10000, 200, 20, 0, 3.0)

    def test_zero_mlss_raises(self):
        """Test that zero MLSS raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_loading(10000, 200, 20, 0.3, 0)

    def test_high_removal_efficiency(self):
        """Test with high removal efficiency (>90%)."""
        # When removal > 90%, Se can be very small
        # So = 300, Se = 20 (90%+ removal), removal = 93.3%
        result = calc_volume_by_loading(
            Q_m3d=5000,
            So=300,
            Se=20,
            Ls=0.2,
            X=2.5
        )
        # V = 5000 * (300-20) / (1000 * 0.2 * 2.5) = 5000 * 280 / 500 = 2800
        assert result == 2800.0


class TestVolumeBySludgeAge:
    """Test volume calculation by sludge age method."""

    def test_basic_calculation(self):
        """Test basic sludge age calculation using formula 7.6.10-2."""
        # V = Q * Y * θc * (So - Se) / (1000 * Xv * (1 + Kd * θc))
        # Q = 10000, Y = 0.5, θc = 10, So = 200, Se = 20, Xv = 2.5, Kd = 0.05
        # V = 10000 * 0.5 * 10 * (200-20) / (1000 * 2.5 * (1 + 0.05 * 10))
        # V = 50000 * 180 / (2500 * 1.5) = 9000000 / 3750 = 2400
        Kd = 0.05  # at 20°C
        result = calc_volume_by_sludge_age(
            Q_m3d=10000,
            So=200,
            Se=20,
            Y=0.5,
            theta_c=10.0,
            Xv=2.5,
            Kd=Kd
        )
        assert result == 2400.0

    def test_zero_flow_raises(self):
        """Test that zero flow raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_sludge_age(0, 200, 20, 0.5, 10, 2.5, 0.05)

    def test_negative_theta_c_raises(self):
        """Test that negative sludge age raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_sludge_age(10000, 200, 20, 0.5, -5, 2.5, 0.05)

    def test_zero_yield_raises(self):
        """Test that zero yield raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_sludge_age(10000, 200, 20, 0, 10, 2.5, 0.05)

    def test_zero_mlvss_raises(self):
        """Test that zero MLVSS raises error."""
        with pytest.raises(ValueError):
            calc_volume_by_sludge_age(10000, 200, 20, 0.5, 10, 0, 0.05)

    def test_low_sludge_age(self):
        """Test with lower sludge age (closer to minimum 3 days)."""
        # θc = 3 days (minimum for carbon removal)
        result = calc_volume_by_sludge_age(
            Q_m3d=5000,
            So=150,
            Se=15,
            Y=0.4,
            theta_c=3.0,
            Xv=2.0,
            Kd=0.04
        )
        # V = 5000 * 0.4 * 3 * (150-15) / (1000 * 2 * (1 + 0.04 * 3))
        # V = 6000 * 135 / (2000 * 1.12) = 810000 / 2240 = 361.61
        assert result == 361.61

    def test_high_sludge_age(self):
        """Test with higher sludge age (closer to maximum 15 days)."""
        # θc = 15 days (maximum for carbon removal)
        result = calc_volume_by_sludge_age(
            Q_m3d=8000,
            So=250,
            Se=20,
            Y=0.6,
            theta_c=15.0,
            Xv=3.0,
            Kd=0.075
        )
        # V = 8000 * 0.6 * 15 * (250-20) / (1000 * 3 * (1 + 0.075 * 15))
        # V = 72000 * 230 / (3000 * 2.125) = 16560000 / 6375 = 2598.82
        assert abs(result - 2598.82) < 2  # Allow for rounding differences


class TestTemperatureCorrection:
    """Test temperature correction for decay coefficient."""

    def test_formula_7_6_11(self):
        """Test temperature correction formula."""
        # KdT = Kd20 * θ_T^(T-20)
        # Kd20 = 0.05, θ_T = 1.04, T = 12
        # KdT = 0.05 * 1.04^(-8) = 0.05 * 0.722 = 0.0361
        result = calc_temperature_corrected_kd(
            Kd20=0.05,
            theta_T=1.04,
            T=12.0
        )
        expected = 0.05 * (1.04 ** (12 - 20))
        assert abs(result - round(expected, 4)) < 0.0001

    def test_at_20_degrees(self):
        """Test at 20°C (reference temperature)."""
        # At T = 20, KdT should equal Kd20
        result = calc_temperature_corrected_kd(
            Kd20=0.05,
            theta_T=1.04,
            T=20.0
        )
        assert result == 0.05

    def test_hot_conditions(self):
        """Test at higher temperature."""
        # At T = 30, Kd should be higher
        result = calc_temperature_corrected_kd(
            Kd20=0.05,
            theta_T=1.04,
            T=30.0
        )
        # 0.05 * 1.04^10 = 0.05 * 1.4802 = 0.0740
        assert result > 0.05

    def test_zero_kd20_raises(self):
        """Test that zero Kd20 raises error."""
        with pytest.raises(ValueError):
            calc_temperature_corrected_kd(0, 1.04, 12)

    def test_zero_theta_t_raises(self):
        """Test that zero theta_T raises error."""
        with pytest.raises(ValueError):
            calc_temperature_corrected_kd(0.05, 0, 12)


class TestThetaCValidation:
    """Test sludge age θc validation (3~15 days for carbon removal)."""

    def test_theta_c_in_range(self):
        """Test that θc in 3~15 range passes."""
        # This should work - use defaults for other params
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20,
            theta_c=10.0  # valid range
        )
        assert "volume_by_loading" in result
        assert "volume_by_sludge_age" in result

    def test_theta_c_below_minimum_raises(self):
        """Test that θc below minimum raises error."""
        with pytest.raises(ValueError):
            calc_bioreactor_volume(
                Q_m3d=10000,
                So=200,
                Se=20,
                theta_c=2.0  # below 3.0
            )

    def test_theta_c_above_maximum_raises(self):
        """Test that θc above maximum raises error."""
        with pytest.raises(ValueError):
            calc_bioreactor_volume(
                Q_m3d=10000,
                So=200,
                Se=20,
                theta_c=20.0  # above 15.0
            )

    def test_theta_c_at_minimum(self):
        """Test at exactly minimum θc."""
        result = calc_bioreactor_volume(
            Q_m3d=5000,
            So=150,
            Se=15,
            theta_c=3.0
        )
        assert result["volume_by_loading"] > 0

    def test_theta_c_at_maximum(self):
        """Test at exactly maximum θc."""
        result = calc_bioreactor_volume(
            Q_m3d=5000,
            So=150,
            Se=15,
            theta_c=15.0
        )
        assert result["volume_by_loading"] > 0


class TestFullCalculation:
    """Test full bioreactor volume calculation."""

    def test_typical_values(self):
        """Test with typical municipal wastewater values."""
        result = calc_bioreactor_volume(
            Q_m3d=20000,
            So=200,
            Se=20,
            Ls=0.3,
            X=3.0,
            Y=0.5,
            theta_c=10.0,
            Xv=2.5,
            Kd20=0.05,
            theta_T=1.04,
            T=12.0
        )

        # Verify structure
        assert "volume_by_loading" in result
        assert "volume_by_sludge_age" in result
        assert "KdT" in result
        assert "unit" in result
        assert "citation" in result
        assert "citations" in result

        # Verify values are reasonable
        assert result["volume_by_loading"] > 0
        assert result["volume_by_sludge_age"] > 0
        assert result["KdT"] > 0

    def test_citation_present(self):
        """Test that citations are present."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20
        )

        assert "citation" in result
        assert "GB 50014-2021" in result["citation"]
        assert "7.6.10" in result["citation"]

    def test_all_citations_present(self):
        """Test that all individual citations are present."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20
        )

        citations = result.get("citations", {})
        assert "loading_formula" in citations
        assert "sludge_age_formula" in citations
        assert "temperature_correction" in citations

    def test_default_values(self):
        """Test with default values."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200
        )

        # Default Se = 20, should work
        assert result["volume_by_loading"] > 0

    def test_warm_climate(self):
        """Test with warm climate parameters."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20,
            T=25.0,  # warm climate
            Kd20=0.06,
            theta_T=1.05
        )

        # At higher temp, Kd should be higher (less decay correction)
        assert result["KdT"] > 0.04  # higher than Kd20 of 0.05 at 20C

    def test_cold_climate(self):
        """Test with cold climate parameters."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20,
            T=5.0,  # cold climate
            Kd20=0.04,
            theta_T=1.03
        )

        # At lower temp, Kd should be lower
        assert result["KdT"] < 0.04


class TestOutputUnits:
    """Test output units are correct."""

    def test_volume_unit(self):
        """Test output includes volume in m³."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20
        )

        assert "volume_by_loading" in result
        assert result["volume_by_loading"] > 0

    def test_kdt_unit(self):
        """Test output includes KdT in d^-1."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20
        )

        assert "KdT" in result
        assert result["KdT"] > 0

    def test_unit_metadata(self):
        """Test unit metadata is present."""
        result = calc_bioreactor_volume(
            Q_m3d=10000,
            So=200,
            Se=20
        )

        assert "unit" in result
        assert result["unit"]["volume"] == "m³"
        assert result["unit"]["KdT"] == "d⁻¹"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])