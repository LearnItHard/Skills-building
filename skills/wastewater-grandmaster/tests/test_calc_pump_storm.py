"""
Tests for calc_pump_storm module.

Tests cover:
- Storm pump design head calculation
- Storm pump design flow calculation
- Design flow equals input (pass-through)
- Total head includes safety head
"""

import pytest
from scripts.calc_pump_storm import (
    calc_pump_storm_head,
    calc_pump_storm,
)


class TestPumpStormHead:
    """Test storm pump design head calculation."""

    def test_basic_head_calculation(self):
        """Test basic head calculation."""
        result = calc_pump_storm_head(
            static_head_m=10.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert result["static_head_m"] == 10.0
        assert result["head_loss_m"] == 2.0
        assert result["safety_head_m"] == 0.5
        # 10 + 2 + 0.5 = 12.5
        assert result["design_head_m"] == 12.5

    def test_head_includes_safety(self):
        """Test that total head includes safety head."""
        result = calc_pump_storm_head(
            static_head_m=8.0,
            head_loss_m=1.5,
            safety_head_m=0.5
        )

        # Must include safety head
        assert result["design_head_m"] == 10.0
        assert result["design_head_m"] == 8.0 + 1.5 + 0.5

    def test_zero_static_head(self):
        """Test with zero static head."""
        result = calc_pump_storm_head(
            static_head_m=0.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert result["design_head_m"] == 2.5

    def test_zero_head_loss(self):
        """Test with zero head loss."""
        result = calc_pump_storm_head(
            static_head_m=10.0,
            head_loss_m=0.0,
            safety_head_m=0.5
        )

        assert result["design_head_m"] == 10.5

    def test_negative_static_head_raises(self):
        """Test negative static head raises error."""
        with pytest.raises(ValueError):
            calc_pump_storm_head(-1.0, 2.0, 0.5)

    def test_negative_head_loss_raises(self):
        """Test negative head loss raises error."""
        with pytest.raises(ValueError):
            calc_pump_storm_head(10.0, -1.0, 0.5)

    def test_negative_safety_head_raises(self):
        """Test negative safety head raises error."""
        with pytest.raises(ValueError):
            calc_pump_storm_head(10.0, 2.0, -0.5)


class TestPumpStorm:
    """Test storm pump station design calculation."""

    def test_basic_calculation(self):
        """Test basic design calculation."""
        result = calc_pump_storm(
            design_flow_L_s=2000.0,
            static_head_m=10.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert result["design_flow_L_s"] == 2000.0
        # 2000 L/s = 2.0 m³/s
        assert result["design_flow_m3s"] == 2.0
        assert result["design_head_m"] == 12.5

    def test_design_flow_equals_input(self):
        """Test that design flow equals input (pass-through)."""
        result = calc_pump_storm(
            design_flow_L_s=1500.0,
            static_head_m=8.0,
            head_loss_m=1.5,
            safety_head_m=0.5
        )

        # Design flow equals input (no calculation, just pass-through)
        assert result["design_flow_L_s"] == 1500.0

    def test_default_safety_head(self):
        """Test default safety head of 0.5m."""
        result = calc_pump_storm(
            design_flow_L_s=1000.0,
            static_head_m=5.0,
            head_loss_m=1.0
        )

        # 5 + 1 + 0.5 = 6.5
        assert result["design_head_m"] == 6.5
        assert result["safety_head_m"] == 0.5

    def test_zero_design_flow_raises(self):
        """Test zero design flow raises error."""
        with pytest.raises(ValueError):
            calc_pump_storm(0.0, 10.0, 2.0, 0.5)

    def test_negative_design_flow_raises(self):
        """Test negative design flow raises error."""
        with pytest.raises(ValueError):
            calc_pump_storm(-100.0, 10.0, 2.0, 0.5)

    def test_large_flow_calculation(self):
        """Test calculation with large flow values."""
        result = calc_pump_storm(
            design_flow_L_s=10000.0,
            static_head_m=15.0,
            head_loss_m=3.0,
            safety_head_m=1.0
        )

        # 15 + 3 + 1 = 19
        assert result["design_flow_L_s"] == 10000.0
        assert result["design_flow_m3s"] == 10.0
        assert result["design_head_m"] == 19.0


class TestOutputStructure:
    """Test output JSON structure."""

    def test_required_fields_present(self):
        """Test all required fields are present."""
        result = calc_pump_storm(
            design_flow_L_s=1000.0,
            static_head_m=10.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert "design_flow_L_s" in result
        assert "design_head_m" in result
        assert "unit" in result
        assert "citation" in result

    def test_unit_metadata(self):
        """Test unit metadata is correct."""
        result = calc_pump_storm(
            design_flow_L_s=1000.0,
            static_head_m=10.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert result["unit"]["design_flow_L_s"] == "L/s"
        assert result["unit"]["design_head_m"] == "m"
        assert result["unit"]["static_head_m"] == "m"
        assert result["unit"]["head_loss_m"] == "m"
        assert result["unit"]["safety_head_m"] == "m"

    def test_citation_present(self):
        """Test citation is present."""
        result = calc_pump_storm(
            design_flow_L_s=1000.0,
            static_head_m=10.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert "citation" in result
        assert "GB 50014-2021" in result["citation"]

    def test_citations_dict_present(self):
        """Test citations dictionary is present."""
        result = calc_pump_storm(
            design_flow_L_s=1000.0,
            static_head_m=10.0,
            head_loss_m=2.0,
            safety_head_m=0.5
        )

        assert "citations" in result
        assert "design_flow" in result["citations"]
        assert "design_head" in result["citations"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])