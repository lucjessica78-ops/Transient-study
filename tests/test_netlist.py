import pytest

from snubber_analyzer.netlist import build_netlist


def test_interrupt_scenario_has_initial_condition_and_uic():
    text = build_netlist("interrupt", L=1e-6, C=1e-9, R_load=1e4, R_series=0.1,
                          I0=50.0, V0=0.0, Rsnub=100.0, Csnub=1e-9,
                          snub_on=True, tmax=1e-6)
    assert "IC=50.000000" in text
    assert "UIC" in text
    assert "Rsnub" in text and "Csnub" in text


def test_stepon_scenario_has_pulse_source_no_uic():
    text = build_netlist("stepon", L=1e-6, C=1e-9, R_load=1e4, R_series=0.1,
                          I0=0.0, V0=500.0, Rsnub=100.0, Csnub=1e-9,
                          snub_on=False, tmax=1e-6)
    assert "PULSE" in text
    assert "UIC" not in text
    assert "Rsnub" not in text


def test_snubber_off_omits_snubber_elements():
    text = build_netlist("interrupt", L=1e-6, C=1e-9, R_load=1e4, R_series=0.1,
                          I0=10.0, V0=0.0, Rsnub=100.0, Csnub=1e-9,
                          snub_on=False, tmax=1e-6)
    assert "Rsnub" not in text
    assert "Csnub" not in text


def test_invalid_scenario_raises():
    with pytest.raises(ValueError):
        build_netlist("not_a_scenario", L=1e-6, C=1e-9, R_load=1e4, R_series=0.1,
                       I0=0.0, V0=0.0, Rsnub=100.0, Csnub=1e-9,
                       snub_on=False, tmax=1e-6)
