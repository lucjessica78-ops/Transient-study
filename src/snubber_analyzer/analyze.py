"""
Post-processing of ngspice's transient output: FFT-based resonance
detection and snubber-sizing metrics. Pure numpy on data ngspice already
produced -- no circuit solving happens here.
"""

import math
import numpy as np


def suggest_snubber(L_henry: float, C_farad: float) -> dict:
    Z0 = math.sqrt(L_henry / C_farad)
    f0 = 1.0 / (2 * math.pi * math.sqrt(L_henry * C_farad))
    return {"Z0_ohm": Z0, "f0_hz": f0, "Rs_ohm": Z0, "Cs_farad": C_farad * 2.5}


def analyze(t, v, iL, L, C, R_load, I0, V0, scenario, snub_on, Rsnub, Csnub, fsw) -> dict:
    dt = t[1] - t[0]
    n = len(t)
    window = np.hanning(n)
    spec = np.fft.rfft((v - v.mean()) * window)
    freqs = np.fft.rfftfreq(n, dt)
    mag = np.abs(spec)
    peak_idx = int(np.argmax(mag[1:]) + 1)
    peak_freq = freqs[peak_idx]

    peak_v = float(np.max(np.abs(v)))
    sug = suggest_snubber(L, C)
    bus_ref = V0 if scenario == "stepon" else I0 * math.sqrt(L / C)
    overshoot_pct = ((peak_v / abs(bus_ref)) - 1) * 100 if bus_ref else None
    zeta = (1 / (2 * R_load)) * math.sqrt(L / C)
    snub_loss_w = 0.5 * Csnub * peak_v ** 2 * fsw if (snub_on and fsw > 0) else None

    return {
        "freqs": freqs, "mag": mag, "peak_freq": peak_freq,
        "peak_v": peak_v, "overshoot_pct": overshoot_pct,
        "f0_theory": sug["f0_hz"], "Z0": sug["Z0_ohm"], "zeta": zeta,
        "Rs_suggest": sug["Rs_ohm"], "Cs_suggest": sug["Cs_farad"],
        "snub_loss_w": snub_loss_w,
    }
