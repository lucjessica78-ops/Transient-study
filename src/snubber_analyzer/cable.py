"""
Cable equivalent R, L, C from American wire gauge / kcmil size.

Formulas (not "physics" -- plain conductor geometry and resistivity):
  - AWG diameter: d(mils) = 5 * 92^((36-n)/39), the standard AWG formula
  - kcmil diameter: d(mils) = sqrt(kcmil * 1000), since 1 kcmil = 1000
    circular mils by definition
  - DC resistance: R = rho / area, rho in ohm-cmil/ft, temperature corrected
  - L, C: two-conductor (or GMD, for three-phase) transmission-line formulas
    from conductor spacing, GMR (=0.7788r for a solid-equivalent round
    conductor), and insulation relative permittivity

These are standard textbook formulas (e.g. Grainger & Stevenson, "Power
System Analysis"), reimplemented here rather than pulled from a library --
verify against NEC Chapter 9 Table 8 and manufacturer cable-data sheets
before using in a real design.
"""

import math

AWG_TABLE = {
    "14 AWG": ("awg", 14), "12 AWG": ("awg", 12), "10 AWG": ("awg", 10),
    "8 AWG": ("awg", 8), "6 AWG": ("awg", 6), "4 AWG": ("awg", 4),
    "3 AWG": ("awg", 3), "2 AWG": ("awg", 2), "1 AWG": ("awg", 1),
    "1/0 AWG": ("awg", 0), "2/0 AWG": ("awg", -1), "3/0 AWG": ("awg", -2),
    "4/0 AWG": ("awg", -3),
    "250 kcmil": ("kcmil", 250), "300 kcmil": ("kcmil", 300),
    "350 kcmil": ("kcmil", 350), "400 kcmil": ("kcmil", 400),
    "500 kcmil": ("kcmil", 500), "600 kcmil": ("kcmil", 600),
    "700 kcmil": ("kcmil", 700), "750 kcmil": ("kcmil", 750),
    "900 kcmil": ("kcmil", 900), "1000 kcmil": ("kcmil", 1000),
}


def conductor_diameter_mils(size_label: str) -> float:
    """Solid-equivalent conductor diameter in mils for a standard AWG/kcmil size."""
    kind, n = AWG_TABLE[size_label]
    if kind == "awg":
        return 5.0 * 92.0 ** ((36 - n) / 39.0)
    return math.sqrt(n * 1000.0)


def cable_equivalents(size_label: str, material: str = "cu", stranded: bool = True,
                       length_ft: float = 150.0, temp_c: float = 75.0,
                       config: str = "single", spacing_in: float = 6.0,
                       eps_r: float = 2.3) -> dict:
    """
    Compute equivalent series R (ohm), series L (H), and shunt C (F) for a
    cable run.

    config: "single" (2-wire single-phase, loop L/C), "three_flat"
            (three-phase flat spaced), "three_tref" (three-phase trefoil,
            touching / equal spacing)
    """
    if size_label not in AWG_TABLE:
        raise ValueError(f"Unknown cable size '{size_label}'. Options: {list(AWG_TABLE)}")
    if material not in ("cu", "al"):
        raise ValueError("material must be 'cu' or 'al'")
    if config not in ("single", "three_flat", "three_tref"):
        raise ValueError("config must be 'single', 'three_flat', or 'three_tref'")

    d_mils = conductor_diameter_mils(size_label)
    area_cmil = d_mils ** 2

    rho20 = 10.371 if material == "cu" else 17.0      # ohm-cmil/ft @ 20C
    alpha = 0.00393 if material == "cu" else 0.00403   # temp coeff /C
    r_per_kft = 1000.0 * rho20 / area_cmil
    r_per_kft *= (1 + alpha * (temp_c - 20))
    if stranded:
        r_per_kft *= 1.02   # small stranding lay-length correction
    R_cable = r_per_kft * (length_ft / 1000.0)

    r_in = (d_mils / 1000.0) / 2.0
    gmr_in = 0.7788 * r_in
    eff_d = spacing_in * (2 ** (1 / 3)) if config == "three_flat" else spacing_in
    length_m = length_ft * 0.3048
    eps0 = 8.854e-12

    if config == "single":
        L_per_m = 4e-7 * math.log(eff_d / gmr_in)
        C_per_m = math.pi * eps0 * eps_r / math.log(eff_d / r_in)
    else:
        L_per_m = 2e-7 * math.log(eff_d / gmr_in)
        C_per_m = 2 * math.pi * eps0 * eps_r / math.log(eff_d / r_in)

    return {
        "R_ohm": R_cable,
        "L_henry": max(L_per_m, 0.0) * length_m,
        "C_farad": max(C_per_m, 0.0) * length_m,
        "diameter_mils": d_mils,
        "area_cmil": area_cmil,
    }
