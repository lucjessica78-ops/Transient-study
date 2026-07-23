"""
Transformer / potential-transformer equivalent leakage L, R, and winding C.

Distribution/power transformers: leakage impedance derived from nameplate
%Z and X/R ratio (standard base-impedance conversion, evaluated at 60 Hz).
Potential transformers (PTs): not conventionally specified by %Z, so L and R
are entered directly (from a factory test report if available).

Winding-to-ground capacitance is highly design-specific and is always a
direct user input here -- there is no reliable geometric formula for it.
"""

import math


def transformer_equivalents(enabled: bool, kind: str = "dist", kva: float = 75.0,
                             kv: float = 12.47, pct_z: float = 2.5,
                             xr_ratio: float = 3.0, pt_L_henry: float = 5.0,
                             pt_R_ohm: float = 500.0, c_pf: float = 3000.0) -> dict:
    if not enabled:
        return {"R_ohm": 0.0, "L_henry": 0.0, "C_farad": 0.0}
    if kind not in ("dist", "pt"):
        raise ValueError("kind must be 'dist' or 'pt'")

    C = c_pf * 1e-12
    if kind == "dist":
        z_base = (kv ** 2 * 1000.0) / kva
        z_leak = (pct_z / 100.0) * z_base
        r_leak = z_leak / math.sqrt(1 + xr_ratio ** 2)
        x_leak = xr_ratio * r_leak
        L = x_leak / (2 * math.pi * 60.0)
        return {"R_ohm": r_leak, "L_henry": L, "C_farad": C}
    return {"R_ohm": pt_R_ohm, "L_henry": pt_L_henry, "C_farad": C}
