"""Generate the native AEDT scripts for Tools > Run Script (single-element designs).

Outputs: one file per element, in hfss/build/<DESIGN>/claude_aedt_native_<DESIGN>_ch9.py, for every design of
claude_pyaedt_ch9.DESIGNS (P01_MS1, P01_MS2, US3_MS3, US3_PS4, US3_PS6, US3_PS4_2_1, US3_PS6_4). Same body in all of them; only the
DESIGNS_TO_BUILD default (the element of the folder, no editing needed) and a header note differ. The former multi-design
file claude_aedt_native_ch9.py (default US3_PS6) was removed in the 2026-11-17 reorganisation.

The native script needs nothing installed on the HFSS computer. Its argument
arrays (boundaries, port, setup, sweeps, far-field sphere, material) are built
here with PyAEDT's own templates and its dict-to-native converter
(ansys.aedt.core.generic.data_handlers._dict2arg, pyaedt 1.9.0), using the same
property dictionaries PyAEDT's Hfss methods build. Geometry calls follow
PyAEDT's CreateBox / CreateRectangle / CreatePolyline / Unite / Subtract
argument layouts. Dimensions come from claude_pyaedt_ch9.DESIGNS, whose
--check proves they reproduce variants/P01_MS1.json, US3_MS3.json, US3_PS4.json, US3_PS6.json, US3_PS4_2_1.json and US3_PS6_4.json.

Run (needs pyaedt only here, not on the HFSS computer):
  python antenna_design/hfss/build/make_aedt_native_script.py
"""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import pprint
from pathlib import Path

from ansys.aedt.core.generic.data_handlers import _dict2arg
from ansys.aedt.core.modules import setup_templates as st
import importlib.metadata as md

HERE = Path(__file__).resolve().parent   # antenna_design/hfss/build


def outputs():
    """(file, default DESIGNS_TO_BUILD, header note) per element: build/<DESIGN>/claude_aedt_native_<DESIGN>_ch9.py."""
    c = load_module()
    return [(HERE / d / f"claude_aedt_native_{d}_ch9.py", [d],
             f"# Fichero por elemento: construye {d} (valor por defecto fijo, no hace falta editarlo).")
            for d in c.DESIGNS]


def load_module():
    spec = importlib.util.spec_from_file_location("c", HERE / "claude_pyaedt_ch9.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_designs():
    mod = load_module()
    for d in mod.DESIGNS:
        assert mod.check(d) == [], d
    return mod.DESIGNS, mod.VARNAME


def native(name, props):
    arg = ["NAME:" + name]
    _dict2arg(props, arg)
    return arg


def material_args(name, loss_model):
    props = {"CoordinateSystemType": "Cartesian", "BulkOrSurfaceType": 1,
             "PhysicsTypes": {"set": ["Electromagnetic"]}, "permittivity": "4.4"}
    if loss_model == "sigma":
        props["conductivity"] = repr(2 * math.pi * 7.9872e9 * 8.8541878128e-12 * 4.4 * 0.017)
        props["dielectric_loss_tangent"] = "0"
    else:
        props["dielectric_loss_tangent"] = "0.017"
    return native(name, props)


def finite_cond_args(name, obj, cu_t):
    # same keys/order as Hfss.assign_finite_conductivity (use_thickness=True, not two-sided)
    props = {"Objects": [obj], "UseMaterial": False, "Conductivity": "58000000", "Permeability": "1",
             "UseThickness": True, "Thickness": f"{cu_t}mm", "Roughness": "0um",
             "InfGroundPlane": False, "IsTwoSided": False, "IsInternal": True}
    return native(name, props)


def lumped_port_args(name, sheet, y_edge, h):
    # same dict as Hfss._create_lumped_driven (renormalize=True, deembed=False)
    start, stop = ["0mm", f"{y_edge}mm", "0mm"], ["0mm", f"{y_edge}mm", f"{h}mm"]
    props = {"Objects": [sheet], "DoDeembed": False, "RenormalizeAllTerminals": True,
             "Modes": {"Mode1": {"ModeNum": 1, "UseIntLine": True, "IntLine": {"Start": start, "End": stop},
                                 "AlignmentGroup": 0, "CharImp": "Zpi", "RenormImp": "50ohm"}},
             "ShowReporterFilter": False, "ReporterFilter": [True], "Impedance": "50ohm"}
    return native(name, props)


def radiation_args(name, obj):
    return native(name, {"Objects": [obj], "IsFssReference": False, "IsForPML": False})


def setup_args(name, design_id=None):
    # per-design values (US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4 stricter) live in claude_pyaedt_ch9.SETUP_DEFAULT / SETUP_OVERRIDES
    c = load_module()
    props = copy.deepcopy(st.HFSSDrivenDefault)
    props.update(c.setup_props(design_id))
    ov = props.get("MultipleAdaptiveFreqsSetup")
    if ov is not None:  # {freq: delta_s} -> {freq: [delta_s]} as the template and PyAEDT store it
        props["MultipleAdaptiveFreqsSetup"] = {f: (d if isinstance(d, list) else [d]) for f, d in ov.items()}
    return native(name, props)


def sweeps_args(design_id, edges_count=None):
    """[Sweep_7p5_8p5, Edges_and_f0] for one design (Edges_and_f0 points: claude_pyaedt_ch9.EDGES_COUNT)."""
    c = load_module()
    n = edges_count if edges_count is not None else c.EDGES_COUNT.get(design_id, c.EDGES_COUNT_DEFAULT)
    return [sweep_args("Sweep_7p5_8p5", 7.5, 8.5, 1001, "Interpolating", False, False),
            sweep_args("Edges_and_f0", 7.7376, 8.2368, n, "Discrete", True, True)]


def sweep_args(name, start_ghz, stop_ghz, count, sweep_type, save_fields, save_rad):
    props = copy.deepcopy(st.SweepHfss3D)
    props.update({"RangeType": "LinearCount", "RangeStart": f"{start_ghz}GHz", "RangeEnd": f"{stop_ghz}GHz",
                  "RangeCount": count, "Type": sweep_type, "SaveFields": save_fields, "SaveRadFields": save_rad})
    if sweep_type == "Interpolating":
        props.update({"InterpTolerance": 0.5, "InterpMaxSolns": 250, "InterpMinSolns": 0, "InterpMinSubranges": 1})
    return native(name, props)


def sphere_args(name):
    # same keys/order as Hfss.insert_infinite_sphere (Theta-Phi, linear polarization, global CS)
    props = {"UseCustomRadiationSurface": False, "CustomRadiationSurface": "", "CSDefinition": "Theta-Phi",
             "Polarization": "Linear", "SlantAngle": "45deg",
             "ThetaStart": "0deg", "ThetaStop": "180deg", "ThetaStep": "5deg",
             "PhiStart": "0deg", "PhiStop": "360deg", "PhiStep": "5deg",
             "UseLocalCS": False, "CoordSystem": ""}
    return native(name, props)


TEMPLATE = r'''# -*- coding: utf-8 -*-
# =============================================================================
# Antenas IR-UWB canal 9 (7,7376-8,2368 GHz): P01_MS1, P01_MS2, US3_MS3, US3_PS4, US3_PS6, US3_PS4_2_1 y US3_PS6_4 en HFSS.
# Script NATIVO de AEDT: Tools > Run Script... (no hace falta instalar nada).
# GENERADO por antenna_design/hfss/build/make_aedt_native_script.py (pyaedt {pyaedt_version}):
# no editar a mano; para cambiar valores, edita las variables del diseno en
# HFSS (Design Properties) o regenera el script.
{header_note}
#
# Estado: GEOMETRY_ONLY en HFSS salvo lo ya resuelto por el propietario (P01_MS1,
# US3_MS3 y, el 17-11, los elementos US3_PS6 y US3_PS4_2_1). Resultados previos
# de los demas: solo openEMS (EM_SIMULATED). Este script NO se ha ejecutado en AEDT
# por Claude: revisa objetos, hueco de la U, puerto y frontera antes de Analyze.
#
# Que construye (por diseno, todo parametrico en variables locales, mm):
#   Substrate (caja FR4 provisional h=sub_h), Ground y Patch (laminas de
#   cobre 35 um, Finite Conductivity), Patch = parche + transformador + linea
#   50 ohm unidos (U-slot: menos la U, tres rectangulos), US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4: lamina
#   Parasitic flotante enterrada a z = par_z dentro del sustrato (Finite
#   Conductivity interna), PortSheet + lumped
#   port 50 ohm en el borde de la placa, AirBox (vacuum) con Radiation,
#   Setup_ch9 a 7,9872 GHz (US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4: mas estricto, 2 pasadas convergidas,
#   DeltaS 0,01 y adaptativo multifrecuencia 7,7376/7,9872/8,2368 GHz; US3_PS6_4: ademas
#   MaximumPasses 25 en lugar de 15),
#   barridos 7,5-8,5 GHz y Edges_and_f0 discreto (3 puntos; US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4: 11 puntos
#   cada 49,92 MHz, las 11 frecuencias NF2FF de openEMS), esfera infinita
#   FF_sphere.
# Fijados al construir (cambiarlos exige regenerar o rehacer a mano):
#   linea de integracion del puerto (z 0 -> sub_h en x=0, y=-board_y/2)
#   y espesor de cobre de la condicion Finite Conductivity.
# =============================================================================

DESIGNS_TO_BUILD = {default_build}   # disponibles: "P01_MS1", "P01_MS2", "US3_MS3", "US3_PS4", "US3_PS6", "US3_PS4_2_1", "US3_PS6_4"
LOSS_MODEL = "tand"                          # "tand" (tan_d 0,017) o "sigma" (como openEMS)

import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oProject = oDesktop.GetActiveProject()
if oProject is None:
    oProject = oDesktop.NewProject()

VARIABLES = {variables}
MATERIAL_ARGS = {material_args}
FINITE_COND_ARGS = {finite_cond_args}
LUMPED_PORT_ARGS = {lumped_port_args}
RADIATION_ARGS = {radiation_args}
SETUP_ARGS = {setup_args}   # por diseno (US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4: setup mas estricto)
SWEEP_ARGS = {sweep_args}   # por diseno (US3_PS4/US3_PS6/US3_PS4_2_1/US3_PS6_4: Edges_and_f0 con 11 puntos)
SPHERE_ARGS = {sphere_args}


COPPER = "(184 115 51)"   # color cobre para Ground y Patch (parche + transformador + linea)


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

for design in DESIGNS_TO_BUILD:
    if design_exists(design):  # proteccion ante reejecucion: no duplica ni renombra disenos existentes
        oDesktop.AddMessage(oProject.GetName(), design, 1,
                            "el diseno %s ya existe en el proyecto: se omite (borralo o usa otro proyecto para reconstruirlo)" % design)
        continue
    oDesign = insert_design(design)
    oDesign = oProject.SetActiveDesign(design)
    set_variables(oDesign, VARIABLES[design])
    ed = oDesign.SetActiveEditor("3D Modeler")
    box(ed, "Substrate", ["-board_x/2", "-board_y/2", "0mm"], ["board_x", "board_y", "sub_h"], mat_name)
    rect_xy(ed, "Ground", ["-board_x/2", "-board_y/2", "0mm"], "board_x", "board_y", COPPER, 0)
    rect_xy(ed, "Patch", ["-patch_W/2", "-patch_L/2", "sub_h"], "patch_W", "patch_L", COPPER, 0)
    rect_xy(ed, "Transformer", ["-tr_w/2", "-patch_L/2-tr_l", "sub_h"], "tr_w", "tr_l", COPPER, 0)
    rect_xy(ed, "Line50", ["-line_w/2", "-board_y/2", "sub_h"], "line_w", "board_y/2-patch_L/2-tr_l", COPPER, 0)
    ed.Unite(["NAME:Selections", "Selections:=", "Patch,Transformer,Line50"],
             ["NAME:UniteParameters", "KeepOriginals:=", False])
    if "u_Wu" in dict(VARIABLES[design]):
        rect_xy(ed, "Slot_base", ["-u_Wu/2", "u_y0", "sub_h"], "u_Wu", "u_t")
        rect_xy(ed, "Slot_arm_r", ["u_Wu/2-u_t", "u_y0+u_t", "sub_h"], "u_t", "u_Lu-u_t")
        rect_xy(ed, "Slot_arm_l", ["-u_Wu/2", "u_y0+u_t", "sub_h"], "u_t", "u_Lu-u_t")
        ed.Subtract(["NAME:Selections", "Blank Parts:=", "Patch", "Tool Parts:=", "Slot_base,Slot_arm_r,Slot_arm_l"],
                    ["NAME:SubtractParameters", "KeepOriginals:=", False])
    if "par_L" in dict(VARIABLES[design]):  # buried floating parasitic sheet (inside the substrate box)
        rect_xy(ed, "Parasitic", ["-par_W/2", "par_yc-par_L/2", "par_z"], "par_W", "par_L", COPPER, 0)
    closed_polyline(ed, "PortSheet", [["-line_w/2", "-board_y/2", "0mm"], ["line_w/2", "-board_y/2", "0mm"],
                                      ["line_w/2", "-board_y/2", "sub_h"], ["-line_w/2", "-board_y/2", "sub_h"]])
    box(ed, "AirBox", ["-board_x/2-pad_xy", "-board_y/2-pad_xy", "-pad_zn"],
        ["board_x+2*pad_xy", "board_y+2*pad_xy", "pad_zn+sub_h+pad_zp"], "vacuum", True, "(143 175 143)", 0.99)
    bnd = oDesign.GetModule("BoundarySetup")
    for args in FINITE_COND_ARGS[design]:
        bnd.AssignFiniteCond(args)
    bnd.AssignLumpedPort(LUMPED_PORT_ARGS[design])
    bnd.AssignRadiation(RADIATION_ARGS)
    ana = oDesign.GetModule("AnalysisSetup")
    ana.InsertSetup("HfssDriven", SETUP_ARGS[design])
    for args in SWEEP_ARGS[design]:
        ana.InsertFrequencySweep("Setup_ch9", args)
    oDesign.GetModule("RadField").InsertInfiniteSphereSetup(SPHERE_ARGS)
    ed.FitAll()
    try:
        dims = dict(VARIABLES[design])
        oDesktop.AddMessage(oProject.GetName(), design, 0, "construido %s: patch_L %s, par_W %s" % (
            design, dims.get("patch_L", "-"), dims.get("par_W", "- (sin parasito)")))
    except Exception:
        pass

oProject.Save()
'''


def main():
    designs, varname = load_designs()
    variables, fc, lp = {}, {}, {}
    for d, p in designs.items():
        variables[d] = [(varname[k], f"{v}mm") for k, v in p.items()] + \
                       [("pad_xy", "22mm"), ("pad_zp", "33mm"), ("pad_zn", "25mm")]
        fc[d] = [finite_cond_args("Cu_Ground", "Ground", p["cu_t"]),
                 finite_cond_args("Cu_Patch", "Patch", p["cu_t"])] + \
                ([finite_cond_args("Cu_Parasitic", "Parasitic", p["cu_t"])] if "pL" in p else [])
        lp[d] = lumped_port_args("P1", "PortSheet", -p["board_y"] / 2, p["h"])
    for out, default, note in outputs():
        out.parent.mkdir(exist_ok=True)
        write(out, default, note, designs, variables, fc, lp)


def write(out, default, note, designs, variables, fc, lp):
    fmt = lambda x: pprint.pformat(x, width=110, sort_dicts=False)
    text = TEMPLATE.format(
        header_note=note, default_build=json.dumps(default),
        pyaedt_version=md.version("pyaedt"),
        variables=fmt(variables),
        material_args=fmt({m: material_args("FR4_prov_ch9_" + m, m) for m in ("tand", "sigma")}),
        finite_cond_args=fmt(fc), lumped_port_args=fmt(lp),
        radiation_args=fmt(radiation_args("Rad", "AirBox")),
        setup_args=fmt({d: setup_args("Setup_ch9", d) for d in designs}),
        sweep_args=fmt({d: sweeps_args(d) for d in designs}),
        sphere_args=fmt(sphere_args("FF_sphere")),
    )
    out.write_text(text)
    print("wrote", out)


if __name__ == "__main__":
    main()
