import pytest
from common.table_lookup import roughness_coefficient, max_fullness, min_velocity


def test_roughness_concrete():
    assert roughness_coefficient("concrete") == 0.013


def test_roughness_chinese_alias():
    assert roughness_coefficient("钢筋混凝土管") == 0.013


def test_max_fullness_200mm():
    assert max_fullness(200) == 0.55
    assert max_fullness(300) == 0.55


def test_max_fullness_400mm():
    assert max_fullness(350) == 0.65
    assert max_fullness(450) == 0.65


def test_max_fullness_1000mm():
    assert max_fullness(1000) == 0.75
    assert max_fullness(1500) == 0.75


def test_min_velocity_sewage():
    assert min_velocity("sewage") == 0.6


def test_min_velocity_storm_combined():
    assert min_velocity("storm_combined") == 0.75


def test_min_velocity_pressure_sludge():
    assert min_velocity("pressure_sludge") == 0.9


def test_min_velocity_invalid():
    with pytest.raises(ValueError):
        min_velocity("invalid_category")
