"""Generate the native AEDT array scripts (Tools > Run Script) that build
1 x N linear arrays of the channel-9 elements with ONE 50 ohm lumped port PER ELEMENT
(multiport / MIMO: HFSS solves the full N x N S-matrix and every embedded element pattern).

Reuses the argument builders of make_aedt_native_script.py (same material, finite
conductivity, lumped port, radiation, setup, sweeps and far-field sphere as the
element designs that the owner already solved). Element dimensions come from
claude_pyaedt_ch9.DESIGNS (checked against variants/*.json) plus P01_MS2
(P01_MS1 with tr_l 7.1 mm, checked against variants/P01_MS2.json here).

Array layout (default, EuCAP article): N = 4 elements along x, pitch 13.5 mm,
element centres at x_i = (i - (N-1)/2) * pitch, all feeds toward -y, one shared
substrate and ground. board_y as in the element (26 mm); board_x =
(N-1)*pitch + 2*board_m (board_m = 13 mm, the element half-board).

Outputs (one call writes all of them, each in hfss/build/<element>/):
  P01_MS2/claude_aedt_array1x4_ch9.py   N = 4, one design per pitch in PITCHES_MM (numeric positions)
  US3_PS4/claude_aedt_array1x5_US3_PS4_param_ch9.py / US3_PS6/claude_aedt_array1x5_US3_PS6_param_ch9.py /
  US3_PS4_2_1/claude_aedt_array1x5_US3_PS4_2_1_param_ch9.py / US3_PS6_4/claude_aedt_array1x5_US3_PS6_4_param_ch9.py
                                     N = 5 as the previous one, default element US3_PS4 / US3_PS6 / US3_PS4_2_1 / US3_PS6_4
  P01_MS2/claude_aedt_array1x5_P01_MS2_param_ch9.py  N = 5, ONE design per element with the pitch as design variable
                                     arr_d (Optimetrics can sweep it); element centres (i-2)*arr_d, the
                                     port integration lines are written as expressions of arr_d, with a
                                     numeric fallback if AEDT rejects the expression (then arr_d is NOT
                                     sweepable: the script prints a warning in the Message Manager).

Run (needs pyaedt 1.9.0 only here, not on the HFSS computer):
  python antenna_design/hfss/build/make_aedt_array_script.py
"""
from __future__ import annotations

import importlib.util
import json
import pprint
from pathlib import Path

import importlib.metadata as md

HERE = Path(__file__).resolve().parent   # antenna_design/hfss/build
EDGES_COUNT_DEFAULT = 3   # points of Edges_and_f0 in the arrays (7.7376 / 7.9872 / 8.2368 GHz)
OUTPUTS = [  # (file, N, parametric pitch, pitches, default element[, Edges_and_f0 points])
    (HERE / "P01_MS2" / "claude_aedt_array1x4_ch9.py", 4, False, [13.5, 15.5, 17.0, 18.2], "P01_MS2"),
    (HERE / "P01_MS2" / "claude_aedt_array1x5_P01_MS2_param_ch9.py", 5, True, [17.0], "P01_MS2"),
    # 1x4 P01_MS2 with parametric arr_d (owner request 2026-11-17): same element, nominal 17 mm and the same
    # Optimetrics grid as the 1x5 P01_MS2 (13.5..20.5 every 0.5 and 18.2), to compare 1x4 and 1x5 on equal terms
    (HERE / "P01_MS2" / "claude_aedt_array1x4_P01_MS2_param_ch9.py", 4, True, [17.0], "P01_MS2"),
    # US3_PS4 (U-slot + buried parasitic): arr_d starts at 18.2 mm, the P01_MS2 sweep's recommended pitch
    (HERE / "US3_PS4" / "claude_aedt_array1x5_US3_PS4_param_ch9.py", 5, True, [18.2], "US3_PS4"),
    # US3_PS6 (round 041): same scheme as US3_PS4, arr_d nominal 18.2 mm (Optimetrics 16.5..19.5 every 0.5 and 18.2)
    (HERE / "US3_PS6" / "claude_aedt_array1x5_US3_PS6_param_ch9.py", 5, True, [18.2], "US3_PS6"),
    # US3_PS4_2_1 (round 045): same scheme, arr_d nominal 18.2 mm (Optimetrics 16.5..19.5 every 0.5 and 18.2)
    # Edges_and_f0 with 5 points (7.7376 / 7.8624 / 7.9872 / 8.1120 / 8.2368 GHz): the embedded fields also sample the
    # eta valley (openEMS 045: eta min 0.273 at 8.137 GHz); the other arrays keep 3 points.
    (HERE / "US3_PS4_2_1" / "claude_aedt_array1x5_US3_PS4_2_1_param_ch9.py", 5, True, [18.2], "US3_PS4_2_1", 5),
    # US3_PS6_4 (owner request 2026-11-19): same scheme, arr_d nominal 18.2 mm. The patch is 14.0 mm wide, so the pitch cannot go
    # down to 13.5 mm (patches overlap by 0.5 mm): physical minimum pitch 14.0 mm (copper touching), practical 14.5 mm (0.5 mm gap).
    # Optimetrics 16.5..20.5 every 0.5 and 18.2 (10 steps; design-reviewer E3, 2026-11-19: the closer pitches 14.5..16.0 are dropped,
    # run 18.2 first to measure passes, time, RAM and disk; see CLAUDE_PYAEDT.md). Edges_and_f0 with 3 points (openEMS 051: eta
    # 0.65-0.71, no valley). Setup: MaximumPasses 25 (SETUP_OVERRIDES in claude_pyaedt_ch9.py).
    (HERE / "US3_PS6_4" / "claude_aedt_array1x5_US3_PS6_4_param_ch9.py", 5, True, [18.2], "US3_PS6_4"),
]
BOARD_M_MM = 13.0
MIN_GAP_MM = 0.5   # smallest copper gap between neighbouring patches that the pitch must leave (fabrication/mesh): pitch >= patch_W + MIN_GAP_MM


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def element_designs(c):
    designs = {k: dict(v) for k, v in c.DESIGNS.items()}
    for d in designs:
        assert c.check(d) == [], d
    p = dict(designs["P01_MS1"], tr_l=7.1)
    v = json.loads((HERE.parent.parent / "variants" / "P01_MS2.json").read_text())
    assert abs(v["feed"]["transformer_length_mm"] - 7.1) < 1e-9
    assert abs(v["feed"]["transformer_width_mm"] - p["tr_w"]) < 1e-9
    pw = v["patch_polygon_mm"]
    assert abs((max(q[1] for q in pw) - min(q[1] for q in pw)) - p["L"]) < 1e-6
    assert abs((max(q[0] for q in pw) - min(q[0] for q in pw)) - p["W"]) < 1e-6
    designs["P01_MS2"] = p
    return designs


def check_pitches(designs, pitches, elem):
    """Refuse a nominal pitch at which neighbouring patches (width patch_W) would touch or leave < MIN_GAP_MM of copper gap."""
    w = designs[elem]["W"]
    for q in pitches:
        assert q >= w + MIN_GAP_MM - 1e-9, f"{elem}: pitch {q} mm leaves a gap {q - w:.3f} mm < {MIN_GAP_MM} mm (patch_W {w} mm)"


def array_name(n, elem, pitch_mm, parametric):
    return f"ARR1x{n}_{elem}_d" + ("param" if parametric else f"{pitch_mm:g}".replace(".", "p") + "mm")


TEMPLATE = r'''# -*- coding: utf-8 -*-
# =============================================================================
# Antenas IR-UWB canal 9 (7,7376-8,2368 GHz): ARRAY LINEAL 1x{n} en HFSS,
# un puerto concentrado de 50 ohm POR ELEMENTO (multipuerto / MIMO).
# Script NATIVO de AEDT: Tools > Run Script... (no hace falta instalar nada).
# GENERADO por antenna_design/hfss/build/make_aedt_array_script.py (pyaedt {pyaedt_version}):
# no editar a mano salvo las constantes DESIGNS_TO_BUILD, LOSS_MODEL y PITCHES_MM.
#
# Estado: GEOMETRY_ONLY. El ARR1x5 de P01_MS2 ya se simulo en HFSS (hfss/results/results_P01_MS2/ARR1x5_P01_MS2_dparam);
# los arrays NO simulados son ARR1x5_US3_PS4, ARR1x5_US3_PS6, ARR1x5_US3_PS4_2_1 y ARR1x5_US3_PS6_4 (U-slot + parasito enterrado; setup mas estricto:
# 2 pasadas convergidas, DeltaS 0,01, adaptativo multifrecuencia 7,7376/7,9872/8,2368 GHz).
# Este script NO se ha ejecutado en AEDT por Claude: revisa objetos, puertos y frontera.
#
# Disenos (nombre ARR1x{n}_<elemento>_d<paso>mm, o _dparam con paso variable):
{design_list}
# Geometria: {n} elementos en x, {geom_pitch}, centros x_i = (i-{half})*paso,
#   i = 0..{nm1}; puertos P1..P{n} de izquierda (-x) a derecha (+x), todos en
#   el borde y = -board_y/2. Sustrato y masa compartidos.
#   board_x = ({nm1}*paso)mm + 2*board_m (board_m = 13 mm, medio tablero del elemento).
# Variables de diseno (Design Properties): las del elemento (patch_L, patch_W,
#   tr_l, tr_w, line_w, sub_h, cu_t, board_y, U-slot u_*, parasito par_L, par_W,
#   par_yc, par_z en US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4) + board_m + pad_* y, en el array parametrico, arr_d
#   (paso, mm; board_x = {nm1}*arr_d + 2*board_m).
#   Las dimensiones del elemento son comunes a los {n} elementos.
# Paso minimo FISICO (hueco de cobre entre parches vecinos = arr_d - patch_W): {min_pitch_note}
# Fijados al construir: las lineas de integracion en y y z (y = -board_y/2, z 0 -> sub_h) y cu_t.
#   Paso: con PARAMETRIC_PITCH = False es un numero por diseno (un diseno por
#   valor de PITCHES_MM). Con PARAMETRIC_PITCH = True es la variable arr_d y se
#   puede barrer con Optimetrics, SOLO si AEDT acepta la expresion en la linea de
#   integracion (si no, el script avisa en Message Manager). Comprueba tras
#   construir: cambia arr_d y mira que la linea de integracion de P1 se mueve.
# Resultado: matriz S {n}x{n} (acoplo Sij) y diagramas embebidos. Para el
#   diagrama del array con fases: HFSS > Edit Sources (ver antenna_design/hfss/CLAUDE_PYAEDT.md).
# =============================================================================

DESIGNS_TO_BUILD = {default_build}   # elementos disponibles: {available}
LOSS_MODEL = "tand"                   # "tand" (tan_d 0,017) o "sigma" (como openEMS)
PITCHES_MM = {pitches}   # {pitch_comment}
PARAMETRIC_PITCH = {parametric}   # True: paso = variable arr_d (barrible con Optimetrics)

import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oProject = oDesktop.GetActiveProject()
if oProject is None:
    oProject = oDesktop.NewProject()

N_ELEM = {n}
ARRAY_PREFIX = "ARR1x%d_" % N_ELEM
VARIABLES = {variables}
MATERIAL_ARGS = {material_args}
FINITE_COND_ARGS = {finite_cond_args}
LUMPED_PORT_ARGS = {lumped_port_args}
RADIATION_ARGS = {radiation_args}
SETUP_ARGS = {setup_args}   # por elemento (US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4: setup mas estricto)
SWEEP_ARGS = {sweep_args}   # {edges_comment}
SPHERE_ARGS = {sphere_args}

COPPER = "(184 115 51)"


def attrs(name, material, solve_inside, color="(143 175 143)", transparency=0.2):
    return ["NAME:Attributes", "Name:=", name, "Flags:=", "", "Color:=", color,
            "Transparency:=", transparency, "PartCoordinateSystem:=", "Global", "SolveInside:=", solve_inside,
            "MaterialValue:=", chr(34) + material + chr(34), "UDMId:=", "",
            "SurfaceMaterialValue:=", chr(34) + "Steel-oxidised-surface" + chr(34)]


def box(ed, name, pos, size, material, solve_inside=True, color="(143 175 143)", transparency=0.2):
    return ed.CreateBox(["NAME:BoxParameters", "XPosition:=", pos[0], "YPosition:=", pos[1],
                         "ZPosition:=", pos[2], "XSize:=", size[0], "YSize:=", size[1], "ZSize:=", size[2]],
                        attrs(name, material, solve_inside, color, transparency))


def rect_xy(ed, name, start, w, h, color="(143 175 143)", transparency=0.2):
    return ed.CreateRectangle(["NAME:RectangleParameters", "IsCovered:=", True, "XStart:=", start[0],
                               "YStart:=", start[1], "ZStart:=", start[2], "Width:=", w, "Height:=", h,
                               "WhichAxis:=", "Z"], attrs(name, "vacuum", True, color, transparency))


def closed_polyline(ed, name, pts):
    points = ["NAME:PolylinePoints"]
    for p in pts + [pts[0]]:
        points.append(["NAME:PLPoint", "X:=", p[0], "Y:=", p[1], "Z:=", p[2]])
    segs = ["NAME:PolylineSegments"]
    for i in range(len(pts)):
        segs.append(["NAME:PLSegment", "SegmentType:=", "Line", "StartIndex:=", i, "NoOfPoints:=", 2])
    xsec = ["NAME:PolylineXSection", "XSectionType:=", "None", "XSectionOrient:=", "Auto",
            "XSectionWidth:=", "0mm", "XSectionTopWidth:=", "0mm", "XSectionHeight:=", "0mm",
            "XSectionNumSegments:=", "0", "XSectionBendType:=", "Corner"]
    return ed.CreatePolyline(["NAME:PolylineParameters", "IsPolylineCovered:=", True,
                              "IsPolylineClosed:=", True, points, segs, xsec], attrs(name, "vacuum", True))


def set_variables(oDesign, values):
    props = ["NAME:NewProps"]
    for k, v in values:
        props.append(["NAME:" + k, "PropType:=", "VariableProp", "UserDef:=", True, "Value:=", v,
                      "Description:=", "", "ReadOnly:=", False, "Hidden:=", False, "Sweep:=", True])
    oDesign.ChangeProperty(["NAME:AllTabs", ["NAME:LocalVariableTab",
                                             ["NAME:PropServers", "LocalVariables"], props]])


def insert_design(name):
    errors = []
    for sol in ("HFSS Modal Network", "DrivenModal", "Modal"):
        try:
            d = oProject.InsertDesign("HFSS", name, sol, "")
            if d is not None:
                return d
        except Exception as e:
            errors.append("%s: %s" % (sol, e))
    try:
        return oProject.SetActiveDesign(name)
    except Exception:
        raise RuntimeError("No se pudo crear el diseno %s (InsertDesign fallo con: %s). Causas habituales: hay "
                           "una simulacion en marcha en este proyecto (espera a que termine o usa otro proyecto), "
                           "el proyecto esta abierto en solo lectura / bloqueado (.lock) tras un cierre de AEDT, "
                           "o no hay proyecto activo. Guarda, cierra AEDT, borra el .lock si existe y relanza."
                           % (name, "; ".join(errors)))


def place_port(args, x):
    # copy of the element lumped-port arguments with the integration line (Start/End) moved to x
    # (x: number in mm or an expression string such as "(-2)*arr_d")
    out = []
    for k, a in enumerate(args):
        if isinstance(a, list):
            if k > 0 and args[k - 1] in ("Start:=", "End:="):
                a = [x if isinstance(x, str) else mm(x)] + list(a[1:])
            else:
                a = place_port(a, x)
        out.append(a)
    return out


def mm(x):
    return repr(round(x, 6)) + "mm"


def design_exists(name):
    # GetTopDesignList devuelve entradas "<tipo>;<nombre>" (asi la lee PyAEDT 1.9.0); se compara el nombre
    try:
        return name in [str(e).split(";")[-1] for e in oProject.GetTopDesignList()]
    except Exception:
        return False


mat_name = "FR4_prov_ch9_" + LOSS_MODEL
try:
    oProject.GetDefinitionManager().AddMaterial(MATERIAL_ARGS[LOSS_MODEL])
except Exception:
    pass  # ya existe en el proyecto

for PITCH_MM in (PITCHES_MM[:1] if PARAMETRIC_PITCH else PITCHES_MM):
    X_MM = [round((i - (N_ELEM - 1) / 2.0) * PITCH_MM, 6) for i in range(N_ELEM)]
    if PARAMETRIC_PITCH:
        XS = ["(%g)*arr_d" % (i - (N_ELEM - 1) / 2.0) for i in range(N_ELEM)]
        PITCH_TAG = "param"
    else:
        XS = [mm(x) for x in X_MM]
        PITCH_TAG = ("%g" % PITCH_MM).replace(".", "p") + "mm"
    for elem in DESIGNS_TO_BUILD:
        name = ARRAY_PREFIX + elem + "_d" + PITCH_TAG
        if design_exists(name):  # proteccion ante reejecucion: no duplica ni renombra disenos existentes
            oDesktop.AddMessage(oProject.GetName(), name, 1,
                                "el diseno %s ya existe en el proyecto: se omite (borralo o usa otro proyecto para reconstruirlo)" % name)
            continue
        oDesign = insert_design(name)
        oDesign = oProject.SetActiveDesign(name)
        if PARAMETRIC_PITCH:
            variables = [("arr_d", mm(PITCH_MM))] + [
                (k, "%d*arr_d+2*board_m" % (N_ELEM - 1) if k == "board_x" else v) for k, v in VARIABLES[elem]]
        else:
            variables = [(k, mm((N_ELEM - 1) * PITCH_MM) + "+2*board_m" if k == "board_x" else v)
                         for k, v in VARIABLES[elem]]
        set_variables(oDesign, variables)
        ed = oDesign.SetActiveEditor("3D Modeler")
        box(ed, "Substrate", ["-board_x/2", "-board_y/2", "0mm"], ["board_x", "board_y", "sub_h"], mat_name)
        rect_xy(ed, "Ground", ["-board_x/2", "-board_y/2", "0mm"], "board_x", "board_y", COPPER, 0)
        for i, xs in enumerate(XS, start=1):
            rect_xy(ed, "Patch_%d" % i, [xs + "-patch_W/2", "-patch_L/2", "sub_h"], "patch_W", "patch_L", COPPER, 0)
            rect_xy(ed, "Transformer_%d" % i, [xs + "-tr_w/2", "-patch_L/2-tr_l", "sub_h"], "tr_w", "tr_l", COPPER, 0)
            rect_xy(ed, "Line50_%d" % i, [xs + "-line_w/2", "-board_y/2", "sub_h"], "line_w",
                    "board_y/2-patch_L/2-tr_l", COPPER, 0)
            ed.Unite(["NAME:Selections", "Selections:=", "Patch_%d,Transformer_%d,Line50_%d" % (i, i, i)],
                     ["NAME:UniteParameters", "KeepOriginals:=", False])
            if "u_Wu" in dict(VARIABLES[elem]):
                rect_xy(ed, "Slot_base_%d" % i, [xs + "-u_Wu/2", "u_y0", "sub_h"], "u_Wu", "u_t")
                rect_xy(ed, "Slot_arm_r_%d" % i, [xs + "+u_Wu/2-u_t", "u_y0+u_t", "sub_h"], "u_t", "u_Lu-u_t")
                rect_xy(ed, "Slot_arm_l_%d" % i, [xs + "-u_Wu/2", "u_y0+u_t", "sub_h"], "u_t", "u_Lu-u_t")
                ed.Subtract(["NAME:Selections", "Blank Parts:=", "Patch_%d" % i,
                             "Tool Parts:=", "Slot_base_%d,Slot_arm_r_%d,Slot_arm_l_%d" % (i, i, i)],
                            ["NAME:SubtractParameters", "KeepOriginals:=", False])
            if "par_L" in dict(VARIABLES[elem]):  # buried floating parasitic sheet of element i
                rect_xy(ed, "Parasitic_%d" % i, [xs + "-par_W/2", "par_yc-par_L/2", "par_z"], "par_W", "par_L", COPPER, 0)
            closed_polyline(ed, "PortSheet_%d" % i, [[xs + "-line_w/2", "-board_y/2", "0mm"],
                                                     [xs + "+line_w/2", "-board_y/2", "0mm"],
                                                     [xs + "+line_w/2", "-board_y/2", "sub_h"],
                                                     [xs + "-line_w/2", "-board_y/2", "sub_h"]])
        box(ed, "AirBox", ["-board_x/2-pad_xy", "-board_y/2-pad_xy", "-pad_zn"],
            ["board_x+2*pad_xy", "board_y+2*pad_xy", "pad_zn+sub_h+pad_zp"], "vacuum", True, "(143 175 143)", 0.99)
        bnd = oDesign.GetModule("BoundarySetup")
        for args in FINITE_COND_ARGS[elem]:
            bnd.AssignFiniteCond(args)
        for i, (xs, x) in enumerate(zip(XS, X_MM), start=1):
            args = place_port(LUMPED_PORT_ARGS[elem], xs)
            args[0] = "NAME:P%d" % i
            args[2] = ["PortSheet_%d" % i]
            try:
                bnd.AssignLumpedPort(args)
            except Exception:
                if not PARAMETRIC_PITCH:
                    raise
                args = place_port(LUMPED_PORT_ARGS[elem], x)
                args[0] = "NAME:P%d" % i
                args[2] = ["PortSheet_%d" % i]
                bnd.AssignLumpedPort(args)
                oDesktop.AddMessage(oProject.GetName(), name, 1,
                                    "P%d: integration line written with numbers (arr_d = %g mm); do NOT sweep arr_d" % (i, PITCH_MM))
        bnd.AssignRadiation(RADIATION_ARGS)
        ana = oDesign.GetModule("AnalysisSetup")
        ana.InsertSetup("HfssDriven", SETUP_ARGS[elem])
        for args in SWEEP_ARGS:
            ana.InsertFrequencySweep("Setup_ch9", args)
        oDesign.GetModule("RadField").InsertInfiniteSphereSetup(SPHERE_ARGS)
        ed.FitAll()

oProject.Save()
'''


def main():
    for out, n, parametric, pitches, default, *rest in OUTPUTS:
        write(out, n, parametric, pitches, default, *rest)


def write(OUT, N_ELEM, parametric, pitches, default="P01_MS2", edges_count=EDGES_COUNT_DEFAULT):
    c = load("claude_pyaedt_ch9")
    nat = load("make_aedt_native_script")
    designs = element_designs(c)
    variables, fc, lp, names = {}, {}, {}, {}
    for d, p in designs.items():
        names[d] = array_name(N_ELEM, d, 0, True) if parametric else ", ".join(array_name(N_ELEM, d, q, False) for q in pitches)
        elem_vars = [(c.VARNAME[k], f"{v}mm") for k, v in p.items() if k != "board_x"]
        variables[d] = [("board_m", f"{BOARD_M_MM}mm"), ("board_x", "set_per_pitch_at_run_time")] + elem_vars + \
                       [("pad_xy", "22mm"), ("pad_zp", "33mm"), ("pad_zn", "25mm")]
        fc[d] = [nat.finite_cond_args("Cu_Ground", "Ground", p["cu_t"])] + \
                [nat.finite_cond_args(f"Cu_Patch_{i}", f"Patch_{i}", p["cu_t"]) for i in range(1, N_ELEM + 1)] + \
                ([nat.finite_cond_args(f"Cu_Parasitic_{i}", f"Parasitic_{i}", p["cu_t"]) for i in range(1, N_ELEM + 1)]
                 if "pL" in p else [])
        lp[d] = nat.lumped_port_args("P1", "PortSheet_1", -p["board_y"] / 2, p["h"])  # x moved per element at run time
    fmt = lambda x: pprint.pformat(x, width=110, sort_dicts=False)
    order = ["P01_MS2", "P01_MS1", "US3_MS3", "US3_PS4", "US3_PS6", "US3_PS4_2_1", "US3_PS6_4"]
    check_pitches(designs, pitches, default)
    text = TEMPLATE.format(
        n=N_ELEM, nm1=N_ELEM - 1, half=(N_ELEM - 1) / 2, pitch=", ".join(f"{q:g}" for q in pitches),
        pitches=repr(pitches), parametric=repr(parametric),
        geom_pitch=("paso = variable arr_d (inicial %g mm)" % pitches[0]) if parametric
        else "un diseno por paso de PITCHES_MM (por defecto %s mm)" % ", ".join(f"{q:g}" for q in pitches),
        pitch_comment=("con PARAMETRIC_PITCH solo se usa el primero, como valor inicial de arr_d (mm)" if parametric
                       else "pasos entre elementos (mm): un diseno por paso"),
        pyaedt_version=md.version("pyaedt"),
        min_pitch_note="; ".join("patch_W %g mm (%s): arr_d > %g mm (cobre en contacto), practico >= %g mm (hueco %g mm)" % (
            w, ", ".join(d for d in order if designs[d]["W"] == w), w, w + MIN_GAP_MM, MIN_GAP_MM)
            for w in sorted({designs[d]["W"] for d in order})),
        design_list="\n".join(f"#   elemento {d}: {names[d]}" for d in order),
        default_build=repr([default]), available=", ".join(order),
        variables=fmt({d: variables[d] for d in order}),
        material_args=fmt({m: nat.material_args("FR4_prov_ch9_" + m, m) for m in ("tand", "sigma")}),
        finite_cond_args=fmt({d: fc[d] for d in order}), lumped_port_args=fmt({d: lp[d] for d in order}),
        radiation_args=fmt(nat.radiation_args("Rad", "AirBox")),
        setup_args=fmt({d: nat.setup_args("Setup_ch9", d) for d in order}),
        sweep_args=fmt(nat.sweeps_args(None, edges_count=edges_count)),
        edges_comment=("Edges_and_f0 de 3 puntos (7,7376 / 7,9872 / 8,2368 GHz) en los arrays" if edges_count == 3 else
                       "Edges_and_f0 de %d puntos (7,7376 / 7,8624 / 7,9872 / 8,1120 / 8,2368 GHz) en este array "
                       "(el resto de arrays: 3 puntos)" % edges_count),
        sphere_args=fmt(nat.sphere_args("FF_sphere")),
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(text)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
