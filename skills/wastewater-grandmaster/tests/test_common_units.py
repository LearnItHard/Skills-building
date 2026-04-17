from common.units import Lps_to_m3ps, m3pd_to_m3ps, mm_to_m, hm2_to_m2, m3ps_to_Lps, m3ps_to_m3pd, m_to_mm


def test_Lps_to_m3ps():
    assert abs(Lps_to_m3ps(1000) - 1.0) < 1e-9


def test_m3pd_to_m3ps():
    assert abs(m3pd_to_m3ps(86400) - 1.0) < 1e-9


def test_mm_to_m():
    assert mm_to_m(1000) == 1.0


def test_hm2_to_m2():
    assert hm2_to_m2(1.0) == 10000.0


def test_round_trip():
    assert abs(m3ps_to_Lps(Lps_to_m3ps(500)) - 500.0) < 1e-9
    assert abs(m3ps_to_m3pd(m3pd_to_m3ps(1000)) - 1000.0) < 1e-9
    assert m_to_mm(mm_to_m(250)) == 250.0
