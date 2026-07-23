import math
import pytest

from snubber_analyzer.transformer import transformer_equivalents


def test_disabled_returns_zeros():
    out = transformer_equivalents(enabled=False)
    assert out == {"R_ohm": 0.0, "L_henry": 0.0, "C_farad": 0.0}


def test_distribution_transformer_hand_calc():
    # 75 kVA, 12.47 kV, 2.5% Z, X/R=3 -- hand-derive and compare
    kva, kv, pct_z, xr = 75.0, 12.47, 2.5, 3.0
    z_base = (kv ** 2 * 1000.0) / kva
    z_leak = (pct_z / 100.0) * z_base
    r_expected = z_leak / math.sqrt(1 + xr ** 2)
    x_expected = xr * r_expected
    l_expected = x_expected / (2 * math.pi * 60.0)

    out = transformer_equivalents(True, "dist", kva, kv, pct_z, xr)
    assert out["R_ohm"] == pytest.approx(r_expected, rel=1e-9)
    assert out["L_henry"] == pytest.approx(l_expected, rel=1e-9)


def test_pt_uses_direct_values():
    out = transformer_equivalents(True, "pt", pt_L_henry=3.3, pt_R_ohm=250.0, c_pf=300.0)
    assert out["L_henry"] == pytest.approx(3.3)
    assert out["R_ohm"] == pytest.approx(250.0)
    assert out["C_farad"] == pytest.approx(300e-12)


def test_higher_pct_z_gives_more_leakage_inductance():
    low = transformer_equivalents(True, "dist", pct_z=1.5)
    high = transformer_equivalents(True, "dist", pct_z=6.0)
    assert high["L_henry"] > low["L_henry"]
