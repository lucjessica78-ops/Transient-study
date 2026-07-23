"""
snubber_analyzer
================
HV switching-transient / snubber sizing tool.

The transient physics is solved by ngspice (open source, Berkeley-SPICE
lineage: https://ngspice.sourceforge.io). This package computes cable and
transformer equivalent R/L/C from standard engineering formulas, builds a
SPICE netlist, runs ngspice, and post-processes the result (FFT, metrics).

See README.md for the validation performed against closed-form theory.
"""

from .cable import cable_equivalents, conductor_diameter_mils, AWG_TABLE
from .transformer import transformer_equivalents
from .netlist import build_netlist
from .simulate import run_ngspice, NgspiceNotFoundError
from .analyze import analyze, suggest_snubber
from .runner import run_case

__all__ = [
    "cable_equivalents", "conductor_diameter_mils", "AWG_TABLE",
    "transformer_equivalents", "build_netlist", "run_ngspice",
    "NgspiceNotFoundError", "analyze", "suggest_snubber", "run_case",
]

__version__ = "0.1.0"
