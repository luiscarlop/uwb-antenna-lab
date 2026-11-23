# -*- coding: utf-8 -*-
# =============================================================================
# EXPORTADOR de resultados del array multipuerto (canal 9). Script NATIVO de AEDT:
# Tools > Run Script... con el proyecto abierto y el diseno del array ya resuelto
# (por ejemplo, el barrido Optimetrics de arr_d de ARR1x5_P01_MS2_dparam). Elige el
# diseno comentando/descomentando las lineas DESIGN de abajo (ARR1x4_P01_MS2_dparam,
# ARR1x5_P01_MS2_dparam, ARR1x5_US3_PS4_dparam, ARR1x5_US3_PS6_dparam,
# ARR1x5_US3_PS4_2_1_dparam y ARR1x5_US3_PS6_4_dparam); N_PORTS se deduce del nombre. Copia luego lo exportado a
# antenna_design/hfss/results/results_<elemento>/<diseno>/ (ver CLAUDE_PYAEDT.md).
#
# Exporta, en OUT_DIR/<diseno>_d<paso>mm/, el .s5p de cada paso de ARR_D_MM y los
# campos de los pasos de FIELDS_ARR_D_MM (las claves de variacion se toman tal
# cual de GetAvailableVariations, con board_x y demas variables dependientes):
#   ARR1x<N>_d<paso>mm.s<N>p      matriz S completa de Setup_ch9 : Sweep_7p5_8p5
#                                  (Touchstone, 50 ohm, magnitud/fase)
#   convergence.conv               (opcional, EXPORT_CONVERGENCE = True) perfil de
#                                  convergencia adaptativa de cada paso de ARR_D_MM
#   ff_P<i>.csv                    campo lejano embebido de cada puerto (1 W en Pi,
#                                  0 W en el resto, todos cargados con 50 ohm), en
#                                  FF_sphere, con las frecuencias de Edges_and_f0 (3;
#                                  5 en ARR1x5_US3_PS4_2_1) en la columna Freq:
#                                  re/im(rETheta), re/im(rEPhi)
#   OUT_DIR/export_log.txt         se escribe linea a linea: si AEDT se cierra,
#                                  dice hasta donde llego
# Consejos: guarda el proyecto (Ctrl+S) despues de resolver y antes de ejecutar
# este script; el script tambien lo guarda al empezar. Si AEDT se cierra, exporta
# por tandas: pon en FIELDS_ARR_D_MM solo 1-2 pasos por ejecucion (los .s5p son
# ligeros y se pueden repetir; FIELDS_ARR_D_MM = [] exporta solo los .s5p).
# Al terminar deja Edit Sources con 1 W en P1 y 0 W en el resto.
#
# Llamadas AEDT tomadas de PyAEDT 1.9.0 (GetNominalVariation, ExportNetworkData,
# EditSources, CreateReport "Far Fields"/"Data Table", ExportToFile,
# DeleteReports, oDesign.ExportConvergence(setup sin " : barrido", "nombre=valor,..",
# fichero) de analysis.export_convergence). NO se ha ejecutado en AEDT por Claude: si algo falla, el
# log dice en que paso; manda el log.
# =============================================================================

# --- Diseno a exportar: deja descomentada UNA sola linea DESIGN (comenta las demas) ---
# DESIGN = "ARR1x5_P01_MS2_dparam"
# DESIGN = "ARR1x4_P01_MS2_dparam"
# DESIGN = "ARR1x5_US3_PS4_dparam"
# DESIGN = "ARR1x5_US3_PS6_dparam"
# DESIGN = "ARR1x5_US3_PS6_4_dparam"
DESIGN = "ARR1x5_US3_PS4_2_1_dparam"   # nombre del diseno en el arbol del proyecto
N_PORTS = None                      # P1..PN. None = se deduce del nombre (ARR1x4 -> 4, ARR1x5 -> 5); pon un numero para fijarlo a mano
OUT_DIR = ""                        # vacio = carpeta del proyecto + "/ch9_array_export"
# Rejilla de pasos del .s5p: deja descomentada UNA (la que resolviste en Optimetrics).
# ARR_D_MM = [13.5 + 0.5 * i for i in range(15)] + [18.2]   # rejilla larga: 13.5..20.5 cada 0.5 y 18.2 (P01_MS2, 1x4 y 1x5)
ARR_D_MM = [16.5 + 0.5 * i for i in range(7)] + [18.2]   # rejilla corta: 16.5..19.5 cada 0.5 y 18.2 (US3_PS4/US3_PS6/US3_PS4_2_1)
# ARR_D_MM = [16.5 + 0.5 * i for i in range(9)] + [18.2]   # ARR1x5_US3_PS6_4: 16.5..20.5 cada 0.5 y 18.2 (10 pasos; parche de 14 mm: arr_d <= 14.0 solapa o toca los parches, 13.5 NO es valido)
FIELDS_ARR_D_MM = [18.2]            # pasos de los que exportar tambien los campos (pocos por ejecucion: 1-2)
SETUP = "Setup_ch9"
SWEEP = "Sweep_7p5_8p5"             # barrido con la matriz S
FF_SWEEP = "Edges_and_f0"           # barrido discreto con campos guardados
SPHERE = "FF_sphere"
EXPORT_CONVERGENCE = True           # convergence.conv de cada paso de ARR_D_MM (opcional)
QUANTITIES = ["re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)"]

import os
import re

if N_PORTS is None:
    _m = re.match(r"ARR1x(\d+)_", DESIGN)
    if _m is None:
        raise ValueError("N_PORTS = None pero DESIGN no empieza por ARR1x<N>_: pon N_PORTS a mano")
    N_PORTS = int(_m.group(1))

import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign(DESIGN)
oSolutions = oDesign.GetModule("Solutions")
oReports = oDesign.GetModule("ReportSetup")
if not OUT_DIR:
    OUT_DIR = os.path.join(oProject.GetPath(), "ch9_array_export")
if not os.path.isdir(OUT_DIR):
    os.makedirs(OUT_DIR)
PORTS = ["P%d" % i for i in range(1, N_PORTS + 1)]
LOG = open(os.path.join(OUT_DIR, "export_log.txt"), "a")


def log(msg, level=0):
    LOG.write(msg + "\n")
    LOG.flush()
    try:
        oDesktop.AddMessage(oProject.GetName(), DESIGN, level, msg)
    except Exception:
        pass


def parse_variation(var):
    # "arr_d='13.5mm' board_m='13mm'" -> [("arr_d", "13.5mm"), ("board_m", "13mm")]
    out = []
    for item in var.split():
        k, _, v = item.partition("=")
        out.append((k, v.replace("'", "")))
    return out


def edit_sources(active):
    args = [["IncludePortPostProcessing:=", True, "SpecifySystemPower:=", False]]
    for p in PORTS:
        args.append(["Name:=", p + ":1", "Magnitude:=", "1W" if p == active else "0W", "Phase:=", "0deg"])
    oSolutions.EditSources(args)


def set_arr_d(value):
    oDesign.ChangeProperty(["NAME:AllTabs", ["NAME:LocalVariableTab", ["NAME:PropServers", "LocalVariables"],
                                             ["NAME:ChangedProps", ["NAME:arr_d", "Value:=", value]]]])


def arr_d_of(var):
    for k, v in parse_variation(var):
        if k == "arr_d":
            return float(v.replace("mm", ""))
    return None


log("==== inicio: %s, .s5p de %d pasos, campos de %s" % (DESIGN, len(ARR_D_MM), FIELDS_ARR_D_MM))
try:
    oProject.Save()
    log("proyecto guardado")
except Exception as e:
    log("aviso: no se pudo guardar el proyecto (%s)" % e, 1)
nominal_arr_d = None
try:
    nominal_arr_d = dict(parse_variation(str(oDesign.GetNominalVariation()))).get("arr_d")
except Exception as e:
    log("aviso: GetNominalVariation no disponible (%s)" % e, 1)
# exact variation keys of the solved variations (dependent variables such as board_x included)
solved = {}
for v in oSolutions.GetAvailableVariations(SETUP + " : " + SWEEP):
    d = arr_d_of(str(v))
    if d is not None:
        solved[round(d, 6)] = str(v)
log("resueltos (arr_d mm): %s" % sorted(solved))


def folder_of(d_mm):
    tag = "d" + ("%g" % d_mm).replace(".", "p") + "mm"
    folder = os.path.join(OUT_DIR, DESIGN + "_" + tag)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return tag, folder


# pass 1: Touchstone of every requested pitch (light)
for d_mm in ARR_D_MM:
    var = solved.get(round(d_mm, 6))
    if var is None:
        log("ERR arr_d = %g mm no esta resuelto; se salta" % d_mm, 2)
        continue
    tag, folder = folder_of(d_mm)
    sname = os.path.join(folder, "ARR1x%d_%s.s%dp" % (N_PORTS, tag, N_PORTS))
    log("... Touchstone %s" % tag)
    try:
        # same argument list as PyAEDT export_touchstone: Touchstone, all freqs, renormalized to 50 ohm,
        # S, last pass, magnitude/phase, 15 digits
        oSolutions.ExportNetworkData(var, [SETUP + ":" + SWEEP], 3, sname, ["all"], True, 50, "S", -1, 0, 15,
                                     False, False, False)
        log("OK  " + sname)
    except Exception as e:
        log("ERR Touchstone %s: %s" % (tag, e), 2)
    if EXPORT_CONVERGENCE:
        # ExportConvergence takes the setup name without the sweep and "name=value,name=value" variations
        # (PyAEDT export_convergence); full variation first, then only arr_d
        cpath = os.path.join(folder, "convergence.conv")
        log("... convergencia %s" % tag)
        pairs = parse_variation(var)
        cands = [",".join(["%s=%s" % (k, v) for k, v in pairs]), "arr_d=%s" % dict(pairs)["arr_d"]]
        done = False
        for cand in cands:
            try:
                oDesign.ExportConvergence(SETUP, cand, cpath)
                log("OK  %s (variaciones: '%s')" % (cpath, cand))
                done = True
                break
            except Exception as e:
                log("ERR ExportConvergence %s con '%s': %s" % (tag, cand, e), 2)
        if not done:
            log("ERR convergencia %s no exportada" % tag, 2)

# pass 2: embedded fields of a few pitches. arr_d is set as the design value first, so the far-field
# report reads that solved variation as the nominal one (the usual way to view a parametric result)
for d_mm in FIELDS_ARR_D_MM:
    var = solved.get(round(d_mm, 6))
    if var is None:
        log("ERR campos: arr_d = %g mm no esta resuelto" % d_mm, 2)
        continue
    tag, folder = folder_of(d_mm)
    value = dict(parse_variation(var))["arr_d"]
    log("... arr_d = %s como valor del diseno" % value)
    set_arr_d(value)
    for p in PORTS:
        log("... Edit Sources %s %s" % (tag, p))
        try:
            edit_sources(p)
        except Exception as e:
            log("ERR EditSources %s %s: %s" % (tag, p, e), 2)
            continue
        name = "ch9_ff_tmp"
        path = os.path.join(folder, "ff_%s.csv" % p)
        sweeps = ["Phi:=", ["All"], "Theta:=", ["All"], "Freq:=", ["All"]]
        for k, v in parse_variation(var):
            sweeps += [k + ":=", [v]]
        log("... far field %s %s" % (tag, p))
        try:
            oReports.CreateReport(name, "Far Fields", "Data Table", SETUP + " : " + FF_SWEEP,
                                  ["Context:=", SPHERE], sweeps,
                                  ["X Component:=", "Phi", "Y Component:=", QUANTITIES])
            oReports.ExportToFile(name, path, False)
            log("OK  " + path)
        except Exception as e:
            log("ERR far field %s %s: %s" % (tag, p, e), 2)
        try:
            oReports.DeleteReports([name])
        except Exception:
            pass

try:
    edit_sources("P1")
    if nominal_arr_d:
        set_arr_d(nominal_arr_d)
        log("arr_d restaurado a " + nominal_arr_d)
except Exception:
    pass
log("==== fin en " + OUT_DIR)
LOG.close()
