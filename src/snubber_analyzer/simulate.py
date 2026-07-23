"""
Runs ngspice as a subprocess and reads its output back in.

No numerical integration of the circuit happens in this file -- ngspice's own
.tran solver does that. This module only writes the netlist to disk, invokes
the ngspice binary, and parses the resulting data file.
"""

import os
import sys
import shutil
import subprocess
import numpy as np


class NgspiceNotFoundError(RuntimeError):
    pass


def _find_ngspice_binary():
    """
    Locate the ngspice executable.

    Checked in order:
      1. PATH (normal install: apt/brew/the official Windows installer)
      2. A Spice64/bin folder sitting next to a frozen executable -- this is
         how the "Build Windows EXE" CI workflow ships ngspice alongside a
         PyInstaller-built .exe, since PyInstaller only bundles the Python
         code, not the separate ngspice program.
    """
    for name in ("ngspice_con", "ngspice_con.exe", "ngspice", "ngspice.exe"):
        found = shutil.which(name)
        if found:
            return found

    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        for candidate in ("Spice64/bin/ngspice_con.exe", "Spice64/bin/ngspice.exe"):
            p = os.path.join(base, candidate)
            if os.path.exists(p):
                return p

    return None


def run_ngspice(netlist_text: str, workdir: str, n_uniform: int = 8192) -> dict:
    ngspice_bin = _find_ngspice_binary()
    if ngspice_bin is None:
        raise NgspiceNotFoundError(
            "ngspice was not found on PATH, and no bundled Spice64/bin folder "
            "was found next to this executable. Install it with "
            "'sudo apt-get install ngspice' (Debian/Ubuntu), 'brew install ngspice' "
            "(macOS), the official installer (Windows), or make sure the "
            "Spice64 folder shipped with this build sits in the same folder "
            "as the .exe. See https://ngspice.sourceforge.io for details."
        )

    workdir_abs = os.path.abspath(workdir)
    os.makedirs(workdir_abs, exist_ok=True)
    cir_path = os.path.join(workdir_abs, "snubber.cir")
    log_path = os.path.join(workdir_abs, "ngspice.log")
    dat_path = os.path.join(workdir_abs, "spice_out.dat")

    with open(cir_path, "w") as f:
        f.write(netlist_text)

    # The netlist's own "wrdata spice_out.dat ..." command writes to
    # whatever directory the ngspice *process* is running in, so cwd must be
    # set to workdir_abs. The -b/-o arguments must then be absolute paths --
    # passing a workdir-relative path for those while cwd is also set to
    # workdir double-prefixes the path (e.g. ./run/ngspice.log under
    # cwd=./run resolves to ./run/run/ngspice.log and silently isn't
    # created). Using absolute paths throughout avoids both failure modes.
    result = subprocess.run(
        [ngspice_bin, "-b", cir_path, "-o", log_path],
        cwd=workdir_abs, capture_output=True, text=True, timeout=120
    )
    if not os.path.exists(dat_path):
        raise RuntimeError(
            "ngspice did not produce output.\n--- stdout ---\n" + result.stdout +
            "\n--- stderr ---\n" + result.stderr
        )

    raw = np.loadtxt(dat_path)
    t_raw = raw[:, 0]
    v_raw = raw[:, 1]
    i_raw = raw[:, 3]

    # ngspice uses adaptive time-stepping internally, so its reported
    # timepoints are NOT uniformly spaced. A raw FFT over non-uniform samples
    # is meaningless -- resample onto a uniform grid before any FFT.
    t_uniform = np.linspace(t_raw[0], t_raw[-1], n_uniform)
    v_uniform = np.interp(t_uniform, t_raw, v_raw)
    i_uniform = np.interp(t_uniform, t_raw, i_raw)

    return {
        "t": t_uniform, "vNode": v_uniform, "iL": i_uniform,
        "t_raw": t_raw, "vNode_raw": v_raw, "iL_raw": i_raw,
        "cir_path": cir_path, "log_path": log_path,
    }
