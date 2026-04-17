"""
Tests for calc_sewage_flow module.

Tests cover:
- Domestic sewage flow calculation
- Variation coefficient table lookup
- Fitted formula with disclaimer
- Design flow calculation
"""

import math
import pytest
from scripts.calc_sewage_flow import (
    lookup_variation_coefficient,
    compute_variation_coefficient_fitted,
    calc_domestic_sewage_flow,
    calc_design_sewage_flow,
    resolve_variation_coefficient,
)


class TestVariationCoefficientTable:
    """Test variation coefficient table values from Table 4.1.15."""

    def test_table_values(self):
        """Verify exact table values."""
        # Q=5 -> Kz=2.7
        kz, fitted = lookup_variation_coefficient(5)
        assert kz == 2.7
        assert fitted is False

        # Q=15 -> Kz=2.4
        kz, fitted = lookup_variation_coefficient(15)
        assert kz == 2.4
        assert fitted is False

        # Q=100 -> Kz=1.9
        kz, fitted = lookup_variation_coefficient(100)
        assert kz == 1.9
        assert fitted is False

        # Q=500 -> Kz=1.6
        kz, fitted = lookup_variation_coefficient(500)
        assert kz == 1.6
        assert fitted is False

        # Q>=1000 -> Kz=1.5
        kz, fitted = lookup_variation_coefficient(1000)
        assert kz == 1.5
        assert fitted is False

        kz, fitted = lookup_variation_coefficient(5000)
        assert kz == 1.5
        assert fitted is False

    def test_interpolation(self):
        """Test linear interpolation between table values."""
        # Q=10 is between 5 and 15
        # Expected: 2.7 - (10-5)/(15-5) * (2.7-2.4) = 2.7 - 0.5*0.3 = 2.55
        kz, fitted = lookup_variation_coefficient(10)
        assert kz == 2.55
        assert fitted is False

        # Q=40 exactly -> 2.1
        kz, fitted = lookup_variation_coefficient(40)
        assert kz == 2.1
        assert fitted is False

        # Q=70 exactly -> 2.0
        kz, fitted = lookup_variation_coefficient(70)
        assert kz == 2.0
        assert fitted is False

        # Q=750 is between 500 and 1000 -> interpolate between 1.6 and 1.5
        kz, fitted = lookup_variation_coefficient(750)
        assert kz == 1.55
        assert fitted is False


class TestFittedFormula:
    """Test fitted formula computation."""

    def test_fitted_formula_values(self):
        """Verify fitted formula produces reasonable values."""
        # Formula: lgKz = -0.1156 * lgQ + 0.5052
        # Test Q=10: lgKz = -0.1156 * 1 + 0.5052 = 0.3896 -> Kz = 2.45
        kz = compute_variation_coefficient_fitted(10)
        expected = 10 ** (-0.1156 * 1 + 0.5052)
        assert abs(kz - round(expected, 2)) < 0.01

    def test_fitted_formula_disclaimer(self):
        """Test that explicit fitted method reports the correct disclaimer."""
        kz, source, disclaimer = resolve_variation_coefficient(10, peak_factor_method="fitted")
        assert kz > 0
        assert source == "fitted_formula"
        assert disclaimer == "Kz 来源于条文说明拟合式，非正文公式"


class TestDomesticSewageFlow:
    """Test domestic sewage flow calculation."""

    def test_basic_calculation(self):
        """Test basic calculation with defaults."""
        # 10000 people, 150 L/(person·d), discharge=0.9
        result = calc_domestic_sewage_flow(
            population=10000,
            water_quota_Lpd=150,
            discharge_coeff=0.9
        )

        # Expected: 10000 * 150 * 0.9 / 1000 = 1350 m³/d
        assert result["average_daily_m3d"] == 1350.0

    def test_zero_population_raises(self):
        """Test that zero population raises error."""
        with pytest.raises(ValueError):
            calc_domestic_sewage_flow(0, 150)

    def test_zero_water_quota_raises(self):
        """Test that zero water quota raises error."""
        with pytest.raises(ValueError):
            calc_domestic_sewage_flow(10000, 0)

    def test_invalid_discharge_coeff_raises(self):
        """Test that invalid discharge coeff raises error."""
        with pytest.raises(ValueError):
            calc_domestic_sewage_flow(10000, 150, 1.5)


class TestDesignFlow:
    """Test design flow calculation."""

    def test_basic_calculation(self):
        """Test basic design flow calculation."""
        result = calc_design_sewage_flow(
            population=50000,
            water_quota_Lpd=150,
            discharge_coeff=0.9,
        )

        # Q_domestic = 50000 * 150 * 0.9 / 1000 = 6750 m³/d
        # Q_domestic_Ls = 6750 * 1000 / 86400 = 78.125 L/s
        # Kz for Q=78 is between 70(2.0) and 100(1.9), ~interpolated
        assert result["average_daily_m3d"] == 6750.0
        assert "Kz" in result
        assert result["Kz"] > 0

    def test_with_industrial(self):
        """Test with industrial wastewater."""
        result = calc_design_sewage_flow(
            population=50000,
            water_quota_Lpd=150,
            discharge_coeff=0.9,
            industrial_m3d=1000,
        )

        # Design = Kz * 6750 + 1000 = ~7563 m³/d
        assert result["average_daily_m3d"] == 6750.0
        assert result["design_flow_m3d"] > result["average_daily_m3d"]

    def test_with_infiltration(self):
        """Test with infiltration."""
        result = calc_design_sewage_flow(
            population=50000,
            water_quota_Lpd=150,
            discharge_coeff=0.9,
            infiltration_m3d=200,
        )

        assert result["design_flow_m3d"] > result["average_daily_m3d"] + 200

    def test_peak_factor_override(self):
        """Test peak factor override."""
        result = calc_design_sewage_flow(
            population=50000,
            water_quota_Lpd=150,
            peak_factor_override=2.5,
        )

        assert result["Kz"] == 2.5
        assert result["peak_factor_source"] == "user_override"
        assert "disclaimer" not in result  # No disclaimer when user-provided

    def test_invalid_peak_factor_method(self):
        with pytest.raises(ValueError):
            calc_design_sewage_flow(
                population=50000,
                water_quota_Lpd=150,
                peak_factor_method="invalid",
            )

    def test_citation_present(self):
        """Test that citation is present."""
        result = calc_design_sewage_flow(
            population=10000,
            water_quota_Lpd=150,
        )

        assert "citation" in result
        assert "GB 50014-2021" in result["citation"]

    def test_disclaimer_for_fitted_formula(self):
        """Test disclaimer appears when fitted formula is explicitly requested."""
        result = calc_design_sewage_flow(
            population=100,
            water_quota_Lpd=100,
            peak_factor_method="fitted",
        )

        assert "Kz" in result
        assert "design_flow_L_s" in result
        assert "design_flow_m3d" in result
        assert "average_daily_m3d" in result
        assert result["peak_factor_source"] == "fitted_formula"
        assert result["disclaimer"] == "Kz 来源于条文说明拟合式，非正文公式"
        assert result["design_flow_L_s"] > 0


class TestOutputUnits:
    """Test output units are correct."""

    def test_output_in_L_s(self):
        """Test output includes L/s."""
        result = calc_design_sewage_flow(
            population=10000,
            water_quota_Lpd=150,
        )

        assert "design_flow_L_s" in result
        assert result["design_flow_L_s"] > 0

    def test_output_in_m3d(self):
        """Test output includes m³/d."""
        result = calc_design_sewage_flow(
            population=10000,
            water_quota_Lpd=150,
        )

        assert "design_flow_m3d" in result
        assert result["design_flow_m3d"] > 0

    def test_unit_field(self):
        """Test unit metadata is present."""
        result = calc_design_sewage_flow(
            population=10000,
            water_quota_Lpd=150,
        )

        assert "unit" in result
        assert result["unit"]["design_flow_L_s"] == "L/s"
        assert result["unit"]["design_flow_m3d"] == "m³/d"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])