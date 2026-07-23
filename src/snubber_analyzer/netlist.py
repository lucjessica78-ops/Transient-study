"""
SPICE netlist generation.

This module writes an ordinary ngspice/SPICE3-compatible netlist. It does not
solve anything itself -- the .cir file it produces can be handed to ngspice,
LTspice, or any other SPICE3-compatible simulator on any machine, completely
independent of this codebase, and should reproduce the same result.

Topology:
  interrupt: inductor L carries initial current I0 (switch has just opened,
             interrupting that current) -- series Rseries -- NODE
             NODE has shunt C, shunt R_load, and an optional series
             Rsnub-Csnub branch, all to ground.
  stepon:    a voltage source steps to V0 at t=0 (switch has just closed)
             feeding through Rseries and L into the same NODE.
"""

import math


def build_netlist(scenario: str, L: float, C: float, R_load: float, R_series: float,
                   I0: float, V0: float, Rsnub: float, Csnub: float,
                   snub_on: bool, tmax: float, dt: float = None) -> str:
    if scenario not in ("interrupt", "stepon"):
        raise ValueError("scenario must be 'interrupt' or 'stepon'")

    if dt is None:
        f0 = 1.0 / (2 * math.pi * math.sqrt(L * C))
        dt = 1.0 / (f0 * 200)  # ~200 points per ring cycle

    lines = ["* Auto-generated snubber ringdown netlist"]
    if scenario == "interrupt":
        lines.append(f"L1 0 N1 {L:.6e} IC={I0:.6f}")
        lines.append(f"Rseries N1 NODE {max(R_series, 1e-6):.6e}")
        lines.append(".ic v(NODE)=0")
        tran_extra = " UIC"
    else:
        lines.append(f"Vsrc SRC 0 PULSE(0 {V0:.6f} 0 1n 1n {tmax*10:.3e} {tmax*20:.3e})")
        lines.append(f"Rseries SRC N1 {max(R_series, 1e-6):.6e}")
        lines.append(f"L1 N1 NODE {L:.6e}")
        tran_extra = ""

    lines.append(f"C1 NODE 0 {C:.6e}")
    lines.append(f"Rload NODE 0 {max(R_load, 1e-6):.6e}")
    if snub_on:
        lines.append(f"Rsnub NODE NS {max(Rsnub, 1e-6):.6e}")
        lines.append(f"Csnub NS 0 {max(Csnub, 1e-15):.6e}")

    lines.append(f".tran {dt:.6e} {tmax:.6e}{tran_extra}")
    lines.append(".control")
    lines.append("run")
    lines.append("wrdata spice_out.dat v(NODE) i(L1)")
    lines.append("quit")
    lines.append(".endc")
    lines.append(".end")
    return "\n".join(lines) + "\n"
