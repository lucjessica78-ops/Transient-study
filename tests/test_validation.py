"""
End-to-end validation: runs the real ngspice solver and checks the result
against closed-form theory. These are the tests that actually prove the
netlist -> ngspice -> FFT pipeline is wired correctly, not just that the
Python runs without raising.

Skipped automatically if ngspice isn't installed (the CI workflow in
.github/workflows/ci.yml installs it, so these run there).
"""

import shutil
import pytest

from snubber_analyzer.runner import run_case

pytestmark = pytest.mark.skipif(
    shutil.which("ngspice") is None,
    reason="ngspice is not installed on this system"
)


BASE_CFG = {
    "cable_size": "1/0 AWG", "material": "cu", "stranded": True,
    "length_ft": 150.0, "temp_c": 75.0, "config": "single",
    "spacing_in": 6.0, "eps_r": 2.3,
    "xfmr_enable": False,
    "scenario": "interrupt", "I0_amps": 50.0,
    "R_load_ohm": 10000.0, "c_extra_pf": 50.0,
    "Rsnub_ohm": 100.0, "Csnub_pf": 400.0,
    "fsw_hz": 20000.0,
}


def test_bare_lc_resonance_matches_theory_without_snubber(tmp_path):
    cfg = dict(BASE_CFG, snub_on=False)
    out = run_case(cfg, workdir=str(tmp_path))
    measured = out["metrics"]["peak_freq"]
    theory = out["metrics"]["f0_theory"]
    # ngspice's own FFT'd output should land within 1% of the closed-form
    # f0 = 1/(2*pi*sqrt(LC)) when there's no snubber loading the node.
    assert measured == pytest.approx(theory, rel=0.01)


def test_snubber_reduces_peak_overshoot(tmp_path):
    on = run_case(dict(BASE_CFG, snub_on=True), workdir=str(tmp_path / "on"))
    off = run_case(dict(BASE_CFG, snub_on=False), workdir=str(tmp_path / "off"))
    assert on["metrics"]["peak_v"] < off["metrics"]["peak_v"]


def test_higher_load_current_gives_higher_peak_voltage(tmp_path):
    low = run_case(dict(BASE_CFG, I0_amps=10.0, snub_on=False), workdir=str(tmp_path / "low"))
    high = run_case(dict(BASE_CFG, I0_amps=100.0, snub_on=False), workdir=str(tmp_path / "high"))
    assert high["metrics"]["peak_v"] > low["metrics"]["peak_v"]


def test_generated_netlist_is_independently_runnable(tmp_path):
    """The .cir file itself, re-run standalone with the ngspice binary
    directly (bypassing this package entirely), should produce output."""
    import subprocess
    out = run_case(dict(BASE_CFG, snub_on=True), workdir=str(tmp_path))
    result = subprocess.run(
        ["ngspice", "-b", out["cir_path"], "-o", str(tmp_path / "standalone.log")],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0
