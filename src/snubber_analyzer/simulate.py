"""
Runs ngspice as a subprocess and reads its output back in.

No numerical integration of the circuit happens in this file -- ngspice's own
.tran solver does that. This module only writes the netlist to disk, invokes
the ngspice binary, and parses the resulting data file.
"""

import os
import shutil
import subprocess
import numpy as np


class NgspiceNotFoundError(RuntimeError):
    pass


def run_ngspice(netlist_text: str, workdir: str, n_uniform: int = 8192) -> dict:
    if shutil.which("ngspice") is None:
        raise NgspiceNotFoundError(
            "ngspice is not installed or not on PATH. Install it with "
            "'sudo apt-get install ngspice' (Debian/Ubuntu), 'brew install ngspice' "
            "(macOS), or see https://ngspice.sourceforge.io for other platforms."
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
        ["ngspice", "-b", cir_path, "-o", log_path],
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
