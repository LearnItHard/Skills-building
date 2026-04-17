import pytest
from common.validation import check_storm_applicability, raise_if_out_of_bounds


def test_check_storm_applicability_normal():
    result = check_storm_applicability(150)  # 1.5 km²
    assert result["method_switched"] is False
    assert result["valid"] is True


def test_check_storm_applicability_exceeds():
    result = check_storm_applicability(250)  # 2.5 km²
    assert result["method_switched"] is True
    assert "4.1.7" in result["message"]


def test_raise_if_out_of_bounds_ok():
    raise_if_out_of_bounds(0.5, 0.0, 1.0, "5.2.4")


def test_raise_if_out_of_bounds_fail():
    with pytest.raises(ValueError) as exc_info:
        raise_if_out_of_bounds(1.5, 0.0, 1.0, "5.2.4")
    assert "GB 50014-2021" in str(exc_info.value)
    assert "5.2.4" in str(exc_info.value)
