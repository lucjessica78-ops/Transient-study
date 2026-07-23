"""
Command-line entry point.

    snubber-analyzer --config myconfig.json --workdir ./run --plot out.png

Config file is JSON with the same keys as the CONFIG dict in the README
example. Any key you omit falls back to a documented default in runner.py.
"""

import argparse
import json
import sys

from .runner import run_case


def main(argv=None):
    parser = argparse.ArgumentParser(description="HV transient / snubber sizing tool (ngspice-backed)")
    parser.add_argument("--config", required=True, help="Path to a JSON config file")
    parser.add_argument("--workdir", default="./run", help="Directory for the netlist and ngspice output")
    parser.add_argument("--plot", default=None, help="Optional path to save a waveform+spectrum PNG")
    args = parser.parse_args(argv)

    with open(args.config) as f:
        cfg = json.load(f)

    out = run_case(cfg, workdir=args.workdir)

    print(f"L_total        = {out['L_total']*1e6:.3f} uH")
    print(f"C_total        = {out['C_total']*1e12:.1f} pF")
    print(f"R_series_total = {out['R_series_total']:.4f} ohm")
    print(f"Peak V         = {out['metrics']['peak_v']:.1f} V")
    print(f"FFT resonance  = {out['metrics']['peak_freq']/1e3:.2f} kHz")
    print(f"Theory f0      = {out['metrics']['f0_theory']/1e3:.2f} kHz")
    print(f"Suggested Rs   = {out['metrics']['Rs_suggest']:.1f} ohm")
    print(f"Suggested Cs   = {out['metrics']['Cs_suggest']*1e12:.1f} pF")
    print(f"Netlist        = {out['cir_path']}")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        import numpy as np
        fig, axes = plt.subplots(2, 1, figsize=(9, 7))
        axes[0].plot(out["spice"]["t"] * 1e6, out["spice"]["vNode"], color="#5ec8ff")
        axes[0].set_xlabel("Time (µs)"); axes[0].set_ylabel("Node voltage (V)")
        axes[0].grid(alpha=0.3)
        axes[1].plot(out["metrics"]["freqs"] / 1e3, 20 * np.log10(out["metrics"]["mag"] + 1e-9), color="#7fffb0")
        axes[1].set_xlim(0, out["metrics"]["peak_freq"] / 1e3 * 6 + 1)
        axes[1].set_xlabel("Frequency (kHz)"); axes[1].set_ylabel("|V(f)| (dB)")
        axes[1].grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(args.plot, dpi=140)
        print(f"Plot           = {args.plot}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
