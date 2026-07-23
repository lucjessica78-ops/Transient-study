# snubber-analyzer

HV switching-transient / snubber sizing tool. Computes cable and transformer
equivalent R, L, C from standard AWG/kcmil geometry and nameplate data, then
runs the actual transient simulation in **ngspice** (open source, Berkeley
SPICE lineage: https://ngspice.sourceforge.io) rather than a custom solver.

```
Source -- switch -- [Rcable, Lcable] -- (optional transformer/PT) -- NODE
                                                                       |-- C (cable + xfmr + parasitic)
                                                                       |-- Rload
                                                                       |-- Rsnub-Csnub (optional)
```

## Why ngspice, not a custom solver

Anyone can write RLC differential equations; the point of using ngspice is
that the numerical solver itself is independently maintained, widely used,
and not something you have to take on faith from this repo. The `.cir`
netlist this tool generates is a plain SPICE3-compatible file — copy it out
of `examples/` or out of a run's working directory and simulate it with
ngspice, LTspice, or any other SPICE3-compatible tool on a different machine
entirely, with zero dependency on this codebase, and you should get the same
waveform.

**This still is not a certified design tool.** There's no UL/IEC/ANSI
certification process that applies to code like this, and there never will
be just by virtue of open-sourcing it. Treat it as a fast, checkable
first-pass sizing aid. For real HV hardware, follow up with a
PSCAD/EMTP-class transient study and a licensed PE's review — this tool does
not model skin/proximity effects, core saturation, distributed
(traveling-wave) cable behavior, or corona.

## Install

```bash
sudo apt-get install ngspice        # Debian/Ubuntu
# brew install ngspice              # macOS
# see https://ngspice.sourceforge.io for Windows / other platforms

git clone https://github.com/<you>/snubber-analyzer.git
cd snubber-analyzer
pip install -e ".[dev]"
```

## Use

```bash
snubber-analyzer --config examples/example_config.json --workdir ./run --plot ringdown.png
```

or from Python:

```python
from snubber_analyzer import run_case

cfg = {
    "cable_size": "1/0 AWG", "length_ft": 150.0,
    "scenario": "interrupt", "I0_amps": 50.0,
    "R_load_ohm": 10_000.0, "Rsnub_ohm": 100.0, "Csnub_pf": 400.0,
}
out = run_case(cfg, workdir="./run")
print(out["metrics"]["peak_v"], out["metrics"]["peak_freq"])
print(out["cir_path"])   # <-- hand this .cir file to anyone, on any machine, to double-check
```

## Validation

`tests/test_validation.py` runs the real ngspice solver (skipped automatically
if ngspice isn't installed) and checks that, with the snubber disabled, the
FFT of ngspice's own output lands within 1% of the closed-form resonance
f0 = 1/(2π√(LC)). That agreement — not anything printed by this README — is
the actual evidence the netlist-generation → ngspice → FFT pipeline is wired
correctly. CI (`.github/workflows/ci.yml`) installs ngspice on the runner and
runs this check on every push.

## Repository layout

```
src/snubber_analyzer/
  cable.py        # AWG/kcmil -> equivalent R, L, C
  transformer.py  # nameplate %Z (or PT direct entry) -> leakage L, R
  netlist.py      # builds the SPICE netlist (no simulation happens here)
  simulate.py     # calls the ngspice binary, reads its output back in
  analyze.py      # FFT + snubber-sizing metrics on ngspice's output
  runner.py       # ties the above together from a config dict
  cli.py          # command-line entry point
tests/
  test_cable.py         # formula checks against known reference values
  test_transformer.py   # hand-calculated %Z conversion checks
  test_netlist.py        # netlist text generation, no ngspice required
  test_validation.py     # end-to-end checks against the real ngspice solver
examples/
  example_config.json
.github/workflows/
  ci.yml       # installs ngspice, runs tests on 3.10/3.11/3.12, builds wheel
  release.yml  # on a version tag, re-runs tests then attaches build to a GitHub Release
```

## What's still a judgment call, not a fact

- Cable L/C use a two-conductor (or GMD) geometric model. Real shielded MV
  cable capacitance depends on insulation-screen geometry, not spacing alone
  — check manufacturer data sheets.
- Transformer winding-to-ground capacitance is always a direct input here;
  there's no reliable general formula for it.
- Suggested snubber values (Rs ≈ Z0 = √(L/C), Cs ≈ 2.5×C) are a standard
  rule-of-thumb starting point, not an optimization result — tune from there
  against the actual waveform.
