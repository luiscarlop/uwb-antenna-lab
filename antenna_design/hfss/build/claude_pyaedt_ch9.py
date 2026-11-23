"""Build the channel-9 candidates in Ansys HFSS with parametric dimensions (PyAEDT).

Designs (EM_SIMULATED in openEMS; P01_MS1 and US3_MS3 also solved in HFSS by the owner; the elements US3_PS6 and
US3_PS4_2_1 were solved in HFSS on 17-11 (US3_PS4_2_1 also as a 1x5 array); US3_PS4 and US3_PS6_4 not yet in HFSS):
  P01_MS1  rectangular patch            (variants/P01_MS1.json, runs 025/026)
  P01_MS2  P01_MS1 with a 7.1 mm lambda/4 transformer (variants/P01_MS2.json; solved in HFSS only as the 1x5 array)
  US3_MS3  rectangular patch + U-slot   (variants/US3_MS3.json, runs 023/024)
  US3_PS4  U-slot patch + buried floating parasitic sheet (variants/US3_PS4.json, round 036)
  US3_PS6  U-slot patch (patch_L 6.29 mm) + buried parasitic 11.0 x 7.05 mm, centre y 0.615 (variants/US3_PS6.json,
           openEMS rounds 038 base / 039 fine)
  US3_PS4_2_1  U-slot patch (patch_L 6.222 mm) + buried parasitic 10.0 x 7.46 mm, centre y 0.75 (variants/US3_PS4_2_1.json,
           openEMS base round 045; fine mesh round 047 done, see reports/claude_run_047.md)
  US3_PS6_4  US3_PS6 with a WIDER patch: patch 14.0 x 6.29 mm (U-slot as US3_PS6), buried parasitic 13.58 x 7.05 mm (centre y
           0.615, z 1.035), lambda/4 transformer 1.0 x 7.25 mm (Zt 94.9 ohm, y -10.395...-3.145) and 50 ohm line of only
           2.605 mm (y -13...-10.395); variants/US3_PS6_4.json, openEMS rounds 050 base and 051 fine mesh
Common: FR4 provisional eps_r 4.4, tan_d 0.017, h 2.07 mm (homogeneous), board
26 x 26 mm, full ground, copper sheets 35 um / 5.8e7 S/m; feed = 50 ohm
microstrip (w 3.92 mm) from the board edge (y = -board_y/2) + lambda/4
transformer (0.80 x 6.60 mm; US3_PS6_4: 1.00 x 7.25 mm) touching the radiating edge; 50 ohm lumped port
on a vertical sheet at the line start (same plane as the openEMS runs; no SMA,
no de-embedding).

Every dimension is an HFSS design variable (Design Properties), so it can be
edited or swept with Optimetrics. Variables: board_x, board_y, sub_h, cu_t,
patch_W, patch_L, line_w, tr_w, tr_l and, for the U-slot, u_Wu, u_Lu, u_t,
u_y0 (all mm), plus pad_xy/pad_zp/pad_zn for the air region. Geometry is
built from rectangles whose corners are expressions of those variables:
  patch       x in [-patch_W/2, patch_W/2], y in [-patch_L/2, patch_L/2]
  transformer x in [-tr_w/2, tr_w/2],       y in [-patch_L/2 - tr_l, -patch_L/2]
  line        x in [-line_w/2, line_w/2],   y in [-board_y/2, -patch_L/2 - tr_l]
  U-slot      base x in [-u_Wu/2, u_Wu/2], y in [u_y0, u_y0 + u_t];
              arms x in [u_Wu/2 - u_t, u_Wu/2] and [-u_Wu/2, -u_Wu/2 + u_t],
              y in [u_y0 + u_t, u_y0 + u_Lu]
US3_PS4, US3_PS6, US3_PS4_2_1 and US3_PS6_4 use a stricter setup (see SETUP_OVERRIDES) and an Edges_and_f0 sweep of 11 points.
Two values are fixed at build time and need a new run of the script if they
change: the lumped-port integration line (z from 0 to sub_h at x = 0) and the
copper sheet thickness of the finite-conductivity boundary (cu_t).

Usage
  python claude_pyaedt_ch9.py --check
      No AEDT needed: rebuilds the polygons from the parameters and compares
      them with variants/<ID>.json (exit code 1 on mismatch).
  python claude_pyaedt_ch9.py --design US3_MS3 [--design P01_MS1] \
      [--project ch9_candidates.aedt] [--version 2025.1] [--non-graphical] \
      [--loss-model tand|sigma] [--solve --cores 2]
      Needs Ansys Electronics Desktop with HFSS and PyAEDT. API checked against
      pyaedt 1.9.0 (module ansys.aedt.core) signatures only; this script has
      NOT been run inside AEDT by Claude. Check every object, boundary, port
      and setup in the GUI before solving.

Material loss models
  tand  (default): constant tan_delta 0.017 (usual HFSS model).
  sigma: tan_delta 0 and bulk conductivity 2*pi*f0*eps0*eps_r*0.017 S/m, the
         model used in openEMS (tan_delta ~ 1/f). Use it to compare with openEMS.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANTS = HERE.parent.parent / "variants"   # antenna_design/variants (this file lives in hfss/build/)
F0_HZ = 7.9872e9
EPS0 = 8.8541878128e-12

COMMON = {
    "board_x": 26.0, "board_y": 26.0, "h": 2.07, "cu_t": 0.035,
    "line_w": 3.92, "tr_w": 0.80, "tr_l": 6.60, "W": 11.421266,
}
DESIGNS = {
    "P01_MS1": {**COMMON, "L": 7.322},
    # P01_MS2 (variants/P01_MS2.json): P01_MS1 with a 7.1 mm transformer (tr_l); solved in HFSS as ARR1x5_P01_MS2
    "P01_MS2": {**COMMON, "L": 7.322, "tr_l": 7.1},
    "US3_MS3": {**COMMON, "L": 6.502, "Wu": 4.4, "Lu": 2.65, "t": 0.8, "y0": -0.7},
    # U-slot + buried parasitic sheet (variants/US3_PS4.json, openEMS round 036): parasitic pL x pW centred at
    # (0, pyc), at height pz inside the homogeneous substrate (floating copper, no vias)
    "US3_PS4": {**COMMON, "L": 6.302, "Wu": 4.4, "Lu": 2.65, "t": 0.8, "y0": -0.7,
                "pL": 7.46, "pW": 11.0, "pyc": 0.75, "pz": 1.035},
    # US3_PS6 (variants/US3_PS6.json, openEMS rounds 038/039): same stack as US3_PS4 but patch_L 6.29 mm (radiating edge
    # y = -3.145, transformer 0.8 x 6.6 mm from y = -9.745) and parasitic 11.0 x 7.05 mm (y -2.91...4.14, centre 0.615)
    "US3_PS6": {**COMMON, "L": 6.29, "Wu": 4.4, "Lu": 2.65, "t": 0.8, "y0": -0.7,
                "pL": 7.05, "pW": 11.0, "pyc": 0.615, "pz": 1.035},
    # US3_PS4_2_1 (variants/US3_PS4_2_1.json, openEMS base round 045): US3_PS4 stack, parasitic 10.0 x 7.46 mm (pW 10.0, NOT 11.0)
    # centred at y = 0.75 (y -2.98...4.48), z 1.035 and patch_L 6.222 mm (radiating edge y = -3.111, transformer 0.8 x 6.6 mm
    # from y = -9.711, 50 ohm line from y = -13)
    "US3_PS4_2_1": {**COMMON, "L": 6.222, "Wu": 4.4, "Lu": 2.65, "t": 0.8, "y0": -0.7,
                    "pL": 7.46, "pW": 10.0, "pyc": 0.75, "pz": 1.035},
    # US3_PS6_4 (variants/US3_PS6_4.json, openEMS rounds 050 base and 051 fine): US3_PS6 with patch W 11.421266 -> 14.0 mm, parasitic pW 11.0 -> 13.58
    # (same 0.21 mm x inset), transformer retuned to 1.0 x 7.25 mm (Zt 94.9 ohm) so the 50 ohm line is 13 - 3.145 - 7.25 = 2.605 mm
    # (y -13 -> -10.395). patch_L 6.29, pL 7.05, pyc 0.615 (y -2.91...4.14), pz 1.035, U-slot and board 26 x 26 mm as US3_PS6
    "US3_PS6_4": {**COMMON, "L": 6.29, "W": 14.0, "tr_w": 1.0, "tr_l": 7.25, "Wu": 4.4, "Lu": 2.65, "t": 0.8, "y0": -0.7,
                  "pL": 7.05, "pW": 13.58, "pyc": 0.615, "pz": 1.035},
}


# ---------------------------------------------------------------- geometry ---
def rects(p):
    """Numeric rectangles (xmin, ymin, xmax, ymax) built from the parameters."""
    L, W, by = p["L"], p["W"], p["board_y"]
    out = {
        "patch": (-W / 2, -L / 2, W / 2, L / 2),
        "transformer": (-p["tr_w"] / 2, -L / 2 - p["tr_l"], p["tr_w"] / 2, -L / 2),
        "line": (-p["line_w"] / 2, -by / 2, p["line_w"] / 2, -L / 2 - p["tr_l"]),
    }
    if "Wu" in p:
        Wu, Lu, t, y0 = p["Wu"], p["Lu"], p["t"], p["y0"]
        out["slot_base"] = (-Wu / 2, y0, Wu / 2, y0 + t)
        out["slot_arm_r"] = (Wu / 2 - t, y0 + t, Wu / 2, y0 + Lu)
        out["slot_arm_l"] = (-Wu / 2, y0 + t, -Wu / 2 + t, y0 + Lu)
    if "pL" in p:
        out["parasitic"] = (-p["pW"] / 2, p["pyc"] - p["pL"] / 2, p["pW"] / 2, p["pyc"] + p["pL"] / 2)
    return out


def bbox(poly):
    xs, ys = [q[0] for q in poly], [q[1] for q in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def u_outline(r):
    """U polygon (CCW, as uslot_family.py writes it) from the three rectangles."""
    bx0, by0, bx1, by1 = r["slot_base"]
    ax0, _, ax1, ay1 = r["slot_arm_r"]
    lx0, _, lx1, _ = r["slot_arm_l"]
    return [[bx0, by0], [bx1, by0], [bx1, ay1], [ax0, ay1], [ax0, by1],
            [lx1, by1], [lx1, ay1], [lx0, ay1]]


def check(design_id, tol=1e-6):
    p = DESIGNS[design_id]
    v = json.loads((VARIANTS / f"{design_id}.json").read_text())
    r = rects(p)
    errs = []

    def cmp(name, a, b):
        d = max(abs(x - y) for x, y in zip(a, b))
        if d > tol:
            errs.append(f"{name}: {a} vs {b} (max diff {d:.3g} mm)")

    sub = v["substrate"]
    for key, val in (("eps_r", 4.4), ("tan_delta", 0.017), ("h_mm", p["h"])):
        if abs(sub[key] - val) > 1e-12:
            errs.append(f"substrate {key}: {sub[key]} vs {val}")
    if list(sub["size_mm"]) != [p["board_x"], p["board_y"]]:
        errs.append(f"board size {sub['size_mm']}")
    if abs(v["metal"]["thickness_m"] * 1e3 - p["cu_t"]) > 1e-12:
        errs.append("copper thickness")
    cmp("patch", r["patch"], bbox(v["patch_polygon_mm"]))
    if len(v["patch_polygon_mm"]) != 4:
        errs.append("patch is not a rectangle")
    fp = v["feed"].get("feed_polygons_mm") or v.get("feed_polygons_mm")
    cmp("line", r["line"], bbox(fp[0]))
    cmp("transformer", r["transformer"], bbox(fp[1]))
    f = v["feed"]
    if abs(f["line_start_y_mm"] + p["board_y"] / 2) > tol or abs(f["line_width_mm"] - p["line_w"]) > tol:
        errs.append("feed line start/width")
    slots = v["slots_polygon_mm"]
    if "Wu" in p:
        if len(slots) != 1:
            errs.append("expected one U-slot")
        else:
            got, ref = u_outline(r), slots[0]
            if len(got) != len(ref):
                errs.append("U vertex count")
            else:
                for i, (a, b) in enumerate(zip(got, ref)):
                    cmp(f"U vertex {i}", a, b)
    elif slots:
        errs.append("unexpected slot")
    par = v.get("parasitic_patches", [])
    if "pL" in p:
        if len(par) != 1:
            errs.append("expected one parasitic patch")
        else:
            cmp("parasitic", r["parasitic"], bbox(par[0]["polygon_mm"]))
            if len(par[0]["polygon_mm"]) != 4 or par[0].get("slots_polygon_mm"):
                errs.append("parasitic is not a plain rectangle")
            if abs(par[0]["z_mm"] - p["pz"]) > tol:
                errs.append(f"parasitic z: {par[0]['z_mm']} vs {p['pz']}")
    elif par:
        errs.append("unexpected parasitic patch")
    if abs(v.get("driven_z_mm", p["h"]) - p["h"]) > tol:
        errs.append("driven layer is not on the top face")
    return errs


# --------------------------------------------------------------------- HFSS ---
# HFSS design-variable names (prefixed to avoid clashes with AEDT built-ins).
VARNAME = {"board_x": "board_x", "board_y": "board_y", "h": "sub_h", "cu_t": "cu_t",
           "line_w": "line_w", "tr_w": "tr_w", "tr_l": "tr_l", "W": "patch_W", "L": "patch_L",
           "Wu": "u_Wu", "Lu": "u_Lu", "t": "u_t", "y0": "u_y0",
           "pL": "par_L", "pW": "par_W", "pyc": "par_yc", "pz": "par_z"}


# Per-design solver settings. Default (P01_MS1, US3_MS3, P01_MS2): single-frequency adaptive at 7.9872 GHz,
# MaxDeltaS 0.02, MaximumPasses 15 (already solved this way). US3_PS4, US3_PS6, US3_PS4_2_1 and US3_PS6_4 (buried sheet): stricter
# (design-reviewer correction): 2 consecutive converged passes, MaxDeltaS 0.01 and multi-frequency adaptive
# meshing at the band edges and centre. US3_PS6_4 (design-reviewer E1, 2026-11-19): MaximumPasses 25 (the wide patch needs more
# passes to reach two converged ones; watch RAM, ~400k tetrahedra around pass 22, and disk). Keys verified in ansys.aedt.core.modules.setup_templates (pyaedt 1.9.0):
# MinimumConvergedPasses, MaxDeltaS, SolveType = "MultiFrequency" and MultipleAdaptiveFreqsSetup {freq: delta_s}.
SETUP_DEFAULT = {"Frequency": "7.9872GHz", "MaxDeltaS": 0.02, "MaximumPasses": 15}
SETUP_OVERRIDES = {
    "US3_PS4": {"MinimumConvergedPasses": 2, "MaxDeltaS": 0.01, "SolveType": "MultiFrequency",
                "MultipleAdaptiveFreqsSetup": {"7.7376GHz": 0.01, "7.9872GHz": 0.01, "8.2368GHz": 0.01}},
    "US3_PS6": {"MinimumConvergedPasses": 2, "MaxDeltaS": 0.01, "SolveType": "MultiFrequency",
                "MultipleAdaptiveFreqsSetup": {"7.7376GHz": 0.01, "7.9872GHz": 0.01, "8.2368GHz": 0.01}},
    "US3_PS4_2_1": {"MinimumConvergedPasses": 2, "MaxDeltaS": 0.01, "SolveType": "MultiFrequency",
                    "MultipleAdaptiveFreqsSetup": {"7.7376GHz": 0.01, "7.9872GHz": 0.01, "8.2368GHz": 0.01}},
    "US3_PS6_4": {"MinimumConvergedPasses": 2, "MaxDeltaS": 0.01, "MaximumPasses": 25, "SolveType": "MultiFrequency",
                  "MultipleAdaptiveFreqsSetup": {"7.7376GHz": 0.01, "7.9872GHz": 0.01, "8.2368GHz": 0.01}},
}
# Points of the discrete sweep Edges_and_f0 (fields + far field saved) over 7.7376-8.2368 GHz. Default 3 (edges and
# f0); US3_PS4, US3_PS6, US3_PS4_2_1 and US3_PS6_4 elements: 11 points (step 49.92 MHz, the 11 NF2FF frequencies of openEMS). Arrays keep 3.
EDGES_COUNT_DEFAULT = 3
EDGES_COUNT = {"US3_PS4": 11, "US3_PS6": 11, "US3_PS4_2_1": 11, "US3_PS6_4": 11}


def setup_props(design_id):
    props = dict(SETUP_DEFAULT)
    props.update(SETUP_OVERRIDES.get(design_id, {}))
    return props


def build(hfss, design_id, p, loss_model):
    for k, val in p.items():
        hfss[VARNAME[k]] = f"{val}mm"
    hfss["pad_xy"] = "22mm"   # board edge to radiation boundary (openEMS box +-35 mm)
    hfss["pad_zp"] = "33mm"   # above the board
    hfss["pad_zn"] = "25mm"   # below the ground

    mat_name = "FR4_prov_ch9_" + loss_model
    mat = hfss.materials.exists_material(mat_name) or hfss.materials.add_material(mat_name)
    mat.permittivity = 4.4
    if loss_model == "sigma":
        mat.dielectric_loss_tangent = 0.0
        mat.conductivity = 2 * math.pi * F0_HZ * EPS0 * 4.4 * 0.017
    else:
        mat.dielectric_loss_tangent = 0.017

    m = hfss.modeler
    m.model_units = "mm"
    sub = m.create_box(["-board_x/2", "-board_y/2", "0mm"], ["board_x", "board_y", "sub_h"],
                       name="Substrate", material=mat_name)
    gnd = m.create_rectangle("XY", ["-board_x/2", "-board_y/2", "0mm"], ["board_x", "board_y"],
                             name="Ground")
    patch = m.create_rectangle("XY", ["-patch_W/2", "-patch_L/2", "sub_h"], ["patch_W", "patch_L"],
                               name="Patch")
    tr = m.create_rectangle("XY", ["-tr_w/2", "-patch_L/2-tr_l", "sub_h"], ["tr_w", "tr_l"],
                            name="Transformer")
    line = m.create_rectangle("XY", ["-line_w/2", "-board_y/2", "sub_h"],
                              ["line_w", "board_y/2-patch_L/2-tr_l"], name="Line50")
    top_name = m.unite([patch.name, tr.name, line.name])  # returns the first name: "Patch"
    if "Wu" in p:
        base = m.create_rectangle("XY", ["-u_Wu/2", "u_y0", "sub_h"], ["u_Wu", "u_t"], name="Slot_base")
        arm_r = m.create_rectangle("XY", ["u_Wu/2-u_t", "u_y0+u_t", "sub_h"], ["u_t", "u_Lu-u_t"],
                                   name="Slot_arm_r")
        arm_l = m.create_rectangle("XY", ["-u_Wu/2", "u_y0+u_t", "sub_h"], ["u_t", "u_Lu-u_t"],
                                   name="Slot_arm_l")
        m.subtract(top_name, [base.name, arm_r.name, arm_l.name], keep_originals=False)
    sheets = [gnd.name, top_name]
    if "pL" in p:  # buried floating parasitic sheet inside the substrate box
        par = m.create_rectangle("XY", ["-par_W/2", "par_yc-par_L/2", "par_z"], ["par_W", "par_L"], name="Parasitic")
        sheets.append(par.name)
    for sheet in sheets:
        hfss.assign_finite_conductivity(sheet, conductivity=58000000, use_thickness=True,
                                        thickness=f"{p['cu_t']}mm", name="Cu_" + sheet)

    port_sheet = m.create_polyline(
        [["-line_w/2", "-board_y/2", "0mm"], ["line_w/2", "-board_y/2", "0mm"],
         ["line_w/2", "-board_y/2", "sub_h"], ["-line_w/2", "-board_y/2", "sub_h"]],
        close_surface=True, cover_surface=True, name="PortSheet")
    y_edge, h = -p["board_y"] / 2, p["h"]
    # integration line: ground (z=0) to strip (z=h) at x=0, value of sub_h at build time
    hfss.lumped_port(port_sheet.name, integration_line=[[0, y_edge, 0], [0, y_edge, h]],
                     impedance=50, name="P1", renormalize=True, deembed=False)

    region = m.create_region(pad_value=["pad_xy", "pad_xy", "pad_xy", "pad_xy", "pad_zp", "pad_zn"],
                             pad_type="Absolute Offset", name="AirRegion")
    hfss.assign_radiation_boundary_to_objects(region.name, name="Rad")

    setup = hfss.create_setup(name="Setup_ch9", setup_type="HFSSDriven", **setup_props(design_id))
    hfss.create_linear_count_sweep(setup.name, "GHz", 7.5, 8.5, 1001, name="Sweep_7p5_8p5",
                                   save_fields=False, sweep_type="Interpolating")
    hfss.create_linear_count_sweep(setup.name, "GHz", 7.7376, 8.2368, EDGES_COUNT.get(design_id, EDGES_COUNT_DEFAULT),
                                   name="Edges_and_f0",
                                   save_fields=True, save_rad_fields=True, sweep_type="Discrete")
    hfss.insert_infinite_sphere(phi_start=0, phi_stop=360, phi_step=5, theta_start=0,
                                theta_stop=180, theta_step=5, name="FF_sphere")
    return {"substrate": sub.name, "top_copper": top_name, "ground": gnd.name,
            "port": "P1", "setup": setup.name, "variables": {VARNAME[k]: v for k, v in p.items()}}


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("--check", action="store_true", help="compare parameters with variants/*.json; no AEDT")
    cli.add_argument("--design", action="append", choices=sorted(DESIGNS), help="design(s) to build")
    cli.add_argument("--project", default="ch9_candidates_claude.aedt")
    cli.add_argument("--version", default=None, help="AEDT version, e.g. 2025.1 (default: latest installed)")
    cli.add_argument("--non-graphical", action="store_true")
    cli.add_argument("--loss-model", choices=["tand", "sigma"], default="tand")
    cli.add_argument("--solve", action="store_true", help="run the adaptive setup and sweeps (off by default)")
    cli.add_argument("--cores", type=int, default=2)
    args = cli.parse_args()

    if args.check:
        bad = 0
        for d in sorted(DESIGNS):
            errs = check(d)
            print(f"{d}: {'OK, parameters reproduce the variant geometry' if not errs else 'MISMATCH'}")
            for e in errs:
                print("   ", e)
            bad += bool(errs)
        sys.exit(1 if bad else 0)

    if not args.design:
        cli.error("give --design (or --check)")
    from ansys.aedt.core import Hfss  # PyAEDT >= 1.0 (pip install pyaedt)

    for d in args.design:
        errs = check(d)
        if errs:
            sys.exit(f"{d}: parameters do not match variants/{d}.json: {errs}")
    hfss = None
    for d in args.design:
        hfss = Hfss(project=args.project, design=d, solution_type="Modal", version=args.version,
                    non_graphical=args.non_graphical)
        info = build(hfss, d, DESIGNS[d], args.loss_model)
        print(d, info)
        hfss.save_project()
        if args.solve:
            hfss.analyze(setup=info["setup"], cores=args.cores)
            hfss.save_project()
    if hfss is not None:
        hfss.release_desktop(close_projects=False, close_desktop=False)


if __name__ == "__main__":
    main()
