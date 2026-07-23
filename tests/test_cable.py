import math
import pytest

from snubber_analyzer.cable import conductor_diameter_mils, cable_equivalents


def test_250kcmil_diameter_matches_solid_conductor_reference():
    # 250 kcmil solid conductor diameter is exactly 0.500 in by definition
    # (250,000 circular mils = 500^2).
    d = conductor_diameter_mils("250 kcmil")
    assert d == pytest.approx(500.0, rel=1e-9)


def test_awg_1_0_diameter_reasonable():
    # 1/0 AWG conductor diameter is well known to be ~0.3249 in (325 mils).
    d = conductor_diameter_mils("1/0 AWG")
    assert d == pytest.approx(325.0, rel=0.01)


def test_larger_awg_number_is_smaller_wire():
    d14 = conductor_diameter_mils("14 AWG")
    d4 = conductor_diameter_mils("4 AWG")
    assert d14 < d4


def test_resistance_scales_inversely_with_area():
    small = cable_equivalents("14 AWG", length_ft=1000)
    large = cable_equivalents("4/0 AWG", length_ft=1000)
    assert small["R_ohm"] > large["R_ohm"]


def test_resistance_scales_linearly_with_length():
    r100 = cable_equivalents("1/0 AWG", length_ft=100)["R_ohm"]
    r200 = cable_equivalents("1/0 AWG", length_ft=200)["R_ohm"]
    assert r200 == pytest.approx(2 * r100, rel=1e-9)


def test_aluminum_more_resistive_than_copper():
    cu = cable_equivalents("1/0 AWG", material="cu", length_ft=100)
    al = cable_equivalents("1/0 AWG", material="al", length_ft=100)
    assert al["R_ohm"] > cu["R_ohm"]


def test_wider_spacing_increases_inductance():
    close = cable_equivalents("1/0 AWG", spacing_in=2.0, length_ft=100)
    wide = cable_equivalents("1/0 AWG", spacing_in=12.0, length_ft=100)
    assert wide["L_henry"] > close["L_henry"]


def test_wider_spacing_decreases_capacitance():
    close = cable_equivalents("1/0 AWG", spacing_in=2.0, length_ft=100)
    wide = cable_equivalents("1/0 AWG", spacing_in=12.0, length_ft=100)
    assert wide["C_farad"] < close["C_farad"]


def test_unknown_size_raises():
    with pytest.raises(ValueError):
        cable_equivalents("not a real size")
