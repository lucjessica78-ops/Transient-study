"""Top-level driver: config dict in, full result dict out."""

import math

from .cable import cable_equivalents
from .transformer import transformer_equivalents
from .netlist import build_netlist
from .simulate import run_ngspice
from .analyze import analyze


def run_case(cfg: dict, workdir: str = "./run") -> dict:
    cab = cable_equivalents(
        cfg["cable_size"], cfg.get("material", "cu"), cfg.get("stranded", True),
        cfg["length_ft"], cfg.get("temp_c", 75.0), cfg.get("config", "single"),
        cfg.get("spacing_in", 6.0), cfg.get("eps_r", 2.3)
    )
    xf = transformer_equivalents(
        cfg.get("xfmr_enable", False), cfg.get("xfmr_kind", "dist"),
        cfg.get("xfmr_kva", 75.0), cfg.get("xfmr_kv", 12.47),
        cfg.get("xfmr_pct_z", 2.5), cfg.get("xfmr_xr", 3.0),
        cfg.get("pt_L_henry", 5.0), cfg.get("pt_R_ohm", 500.0),
        cfg.get("xfmr_c_pf", 3000.0)
    )

    L_total = cab["L_henry"] + xf["L_henry"]
    C_total = cab["C_farad"] + xf["C_farad"] + cfg.get("c_extra_pf", 50.0) * 1e-12
    R_series_total = cab["R_ohm"] + xf["R_ohm"]

    scenario = cfg.get("scenario", "interrupt")
    I0 = cfg.get("I0_amps", 50.0) if scenario == "interrupt" else 0.0
    V0 = cfg.get("V0_volts", 500.0) if scenario == "stepon" else 0.0
    R_load = cfg.get("R_load_ohm", 10000.0)
    Rsnub = cfg.get("Rsnub_ohm", 100.0)
    Csnub = cfg.get("Csnub_pf", 400.0) * 1e-12
    snub_on = cfg.get("snub_on", True)
    fsw = cfg.get("fsw_hz", 20000.0)

    f0_est = 1.0 / (2 * math.pi * math.sqrt(L_total * C_total))
    tmax = cfg.get("tmax_s", 15.0 / f0_est)

    netlist = build_netlist(scenario, L_total, C_total, R_load, R_series_total,
                             I0, V0, Rsnub, Csnub, snub_on, tmax)
    spice = run_ngspice(netlist, workdir)
    res = analyze(spice["t"], spice["vNode"], spice["iL"], L_total, C_total,
                  R_load, I0, V0, scenario, snub_on, Rsnub, Csnub, fsw)

    return {
        "cable": cab, "xfmr": xf, "L_total": L_total, "C_total": C_total,
        "R_series_total": R_series_total, "netlist": netlist, "spice": spice,
        "metrics": res, "cir_path": spice["cir_path"],
    }
