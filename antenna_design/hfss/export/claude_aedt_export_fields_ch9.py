# -*- coding: utf-8 -*-
# =============================================================================
# EXPORTADOR SOLO DE CAMPOS del array multipuerto (canal 9). Script NATIVO de AEDT:
# Tools > Run Script... con el proyecto abierto y el barrido Optimetrics de arr_d
# ya resuelto (array a elegir en DESIGN). No exporta .s5p (para eso,
# claude_aedt_export_array_ch9.py).
#
# Para cada paso de FIELDS_ARR_D_MM (tanda pequena, p. ej. 3 pasos):
#   1. guarda el arr_d nominal del diseno (GetNominalVariation) y pone arr_d a ese valor
#      como valor del diseno (lee asi la variacion resuelta);
#   2. exporta OUT_DIR/<diseno>_d<paso>mm/ff_P<i>.csv: campo lejano embebido de cada
#      puerto (1 W en Pi, 0 W en el resto, 50 ohm) en FF_sphere, con las
#      frecuencias de Edges_and_f0 (3; 5 en ARR1x5_US3_PS4_2_1; columna Freq), re/im(rETheta), re/im(rEPhi).
# Al terminar (o si algo falla dentro de Python) restaura arr_d al valor que tenia el
# diseno al empezar (GetNominalVariation, como claude_aedt_export_array_ch9.py) y
# deja Edit Sources con P1 a 1 W. Si AEDT se cierra, el proyecto guardado al empezar
# conserva el arr_d original. Si GetNominalVariation no esta disponible, no se
# restaura nada y el log lo avisa (ponlo a mano).
# Rejilla de arr_d resuelta: P01_MS2 13.5..20.5 cada 0.5 y 18.2; ARR1x5_US3_PS4_dparam,
# ARR1x5_US3_PS6_dparam y ARR1x5_US3_PS4_2_1_dparam: 16.5..19.5 cada 0.5 mas 18.2 (anadelo a la tabla parametrica, ver CLAUDE_PYAEDT.md);
# ARR1x5_US3_PS6_4_dparam: 16.5..20.5 cada 0.5 mas 18.2 (10 pasos; parche de 14 mm: arr_d <= 14.0 mm solapa o toca los parches).
# Elige el diseno comentando/descomentando las lineas DESIGN de abajo (ARR1x4_P01_MS2_dparam,
# ARR1x5_P01_MS2_dparam, ARR1x5_US3_PS4_dparam, ARR1x5_US3_PS6_dparam, ARR1x5_US3_PS4_2_1_dparam,
# ARR1x5_US3_PS6_4_dparam);
# N_PORTS se deduce del nombre (la logica es la misma para todos).
# SKIP_EXISTING = True salta los ff_P<i>.csv que ya existen: se puede relanzar con
# la misma lista y sigue donde se quedo.
# OUT_DIR/export_fields_log.txt se escribe linea a linea ("..." antes de cada paso).
# Llamadas AEDT como en claude_aedt_export_array_ch9.py (PyAEDT 1.9.0). NO se ha
# ejecutado en AEDT por Claude; probado con un AEDT simulado.
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
FIELDS_ARR_D_MM = [18.2, 16.5, 19.5]   # tanda de pasos (mm); 16.5..19.5 cada 0.5 y 18.2 (rejilla de US3_PS4, US3_PS6 y US3_PS4_2_1)
# FIELDS_ARR_D_MM = [18.2, 16.5, 20.5]   # ARR1x5_US3_PS6_4 (rejilla 16.5..20.5 cada 0.5 y 18.2; paso minimo fisico 14.0 mm)
SKIP_EXISTING = True
MAX_REPORTS_PER_RUN = 10           # AEDT se ha cerrado tras ~14-15 informes de campo lejano en una sesion:
                                    # se para limpio tras este numero; cierra AEDT, vuelve a abrir y relanza
MIN_CSV_BYTES = 1000                # un ff_P<i>.csv mas pequeno se considera incompleto y se repite
SETUP = "Setup_ch9"
SWEEP = "Sweep_7p5_8p5"             # solo para leer las claves de variacion resueltas
FF_SWEEP = "Edges_and_f0"           # barrido discreto con campos guardados
SPHERE = "FF_sphere"
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
LOG = open(os.path.join(OUT_DIR, "export_fields_log.txt"), "a")


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


log("==== inicio campos: %s, pasos %s" % (DESIGN, FIELDS_ARR_D_MM))
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
if nominal_arr_d:
    log("arr_d nominal del diseno: " + nominal_arr_d)
solved = {}
for v in oSolutions.GetAvailableVariations(SETUP + " : " + SWEEP):
    d = arr_d_of(str(v))
    if d is not None:
        solved[round(d, 6)] = str(v)
log("resueltos (arr_d mm): %s" % sorted(solved))

n_reports = 0
try:
    for d_mm in FIELDS_ARR_D_MM:
        var = solved.get(round(d_mm, 6))
        if var is None:
            log("ERR arr_d = %g mm no esta resuelto; se salta" % d_mm, 2)
            continue
        tag = "d" + ("%g" % d_mm).replace(".", "p") + "mm"
        folder = os.path.join(OUT_DIR, DESIGN + "_" + tag)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        todo = [p for p in PORTS if not (SKIP_EXISTING and os.path.isfile(os.path.join(folder, "ff_%s.csv" % p))
                                          and os.path.getsize(os.path.join(folder, "ff_%s.csv" % p)) >= MIN_CSV_BYTES)]
        if not todo:
            log("ya exportado %s; se salta" % tag)
            continue
        if n_reports >= MAX_REPORTS_PER_RUN:
            log("PARADA: %d informes en esta sesion (MAX_REPORTS_PER_RUN). Cierra AEDT, abre el proyecto y relanza con la misma lista" % n_reports, 1)
            break
        value = dict(parse_variation(var))["arr_d"]
        log("... arr_d = %s como valor del diseno" % value)
        set_arr_d(value)
        for p in todo:
            if n_reports >= MAX_REPORTS_PER_RUN:
                log("PARADA: %d informes en esta sesion (MAX_REPORTS_PER_RUN). Cierra AEDT, abre el proyecto y relanza con la misma lista" % n_reports, 1)
                break
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
                n_reports += 1
                oReports.ExportToFile(name, path, False)
                log("OK  " + path)
            except Exception as e:
                log("ERR far field %s %s: %s" % (tag, p, e), 2)
            try:
                oReports.DeleteReports([name])
            except Exception:
                pass
finally:
    try:
        edit_sources("P1")
    except Exception:
        pass
    if nominal_arr_d:
        try:
            set_arr_d(nominal_arr_d)
            log("arr_d restaurado a " + nominal_arr_d)
        except Exception as e:
            log("ERR no se pudo restaurar arr_d (%s): ponlo a mano a %s" % (e, nominal_arr_d), 2)
    else:
        log("aviso: arr_d nominal desconocido; no se restaura, comprueba arr_d a mano", 1)
    log("==== fin en " + OUT_DIR)
    LOG.close()
