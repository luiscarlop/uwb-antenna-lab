# -*- coding: utf-8 -*-
# =============================================================================
# EXPORTADOR del ELEMENTO UNITARIO ya resuelto (canal 9). Script NATIVO de AEDT:
# Tools > Run Script... con el proyecto abierto y el diseno del elemento resuelto
# (P01_MS1, P01_MS2, US3_MS3, US3_PS4, US3_PS6, US3_PS4_2_1, US3_PS6_4: comenta/descomenta DESIGN). Sin dependencias
# externas; mismo estilo que claude_aedt_export_array_ch9.py (log linea a linea,
# try/except por paso, guarda el proyecto al empezar).
#
# Exporta, en OUT_DIR/<DESIGN>/ (OUT_DIR vacio = carpeta del proyecto +
# "/ch9_element_export"):
#   <DESIGN>.s1p            S11 de Setup_ch9 : Sweep_7p5_8p5 (Touchstone, 50 ohm,
#                           magnitud/fase), con la variacion nominal exacta de
#                           GetAvailableVariations
#   ff_P1.csv               campo lejano con 1 W en P1: re/im(rETheta), re/im(rEPhi)
#                           en FF_sphere, todo theta y phi, todas las frecuencias de
#                           Edges_and_f0 (formato largo, columna Freq, como el array)
#   antenna_params.csv      informe Far Fields "Antenna Parameters" (Data Table), Freq en
#                           X: RadiationEfficiency, RadiatedPower, AcceptedPower,
#                           IncidentPower, PeakRealizedGain, PeakGain, PeakDirectivity.
#                           Si el informe conjunto falla, se prueba cantidad a cantidad y
#                           salen antenna_params_<cantidad>.csv de las que existan.
#   realized_gain_cuts.csv  OPCIONAL (EXPORT_GAIN_CUTS): dB(GainTotal) y
#                           dB(RealizedGainTotal) en FF_sphere (mismo recorrido que
#                           ff_P1.csv). Mismo fallback por cantidad. ff_P1.csv ya
#                           permite calcular la ganancia.
#   convergence.conv        perfil de convergencia adaptativa (ExportConvergence), y
#   profile.prof            tabla de perfil (ExportProfile), si existe
#   export_log.txt          lo que se hizo y la variacion usada (se escribe linea a
#                           linea: si AEDT se cierra, dice hasta donde llego)
# Un fallo en un paso se anota en el log (ERR) y no aborta los demas.
# Al terminar deja Edit Sources con 1 W en P1.
#
# LLAMADAS AEDT
#   Verificadas en PyAEDT 1.9.0: GetNominalVariation, GetAvailableVariations,
#   ExportNetworkData (misma lista de argumentos que export_touchstone),
#   EditSources, CreateReport/ExportToFile/DeleteReports ("Far Fields"/"Data Table"),
#   oDesign.ExportConvergence(setup, variaciones, fichero) con setup SIN " : barrido" y
#   variaciones "nombre=valor,nombre=valor" (analysis.export_convergence),
#   oDesign.ExportProfile(setup, variaciones, fichero) con fallback a 4 argumentos
#   (design.export_profile), categoria de informe "Antenna Parameters" con contexto
#   ["Context:=", esfera] y las cantidades IncidentPower, RadiatedPower, AcceptedPower
#   (farfield_exporter.py) y GainTotal (ejemplos de la documentacion).
#   NO verificadas en PyAEDT 1.9.0 (nombres tomados del Report Editor de AEDT; si
#   alguno no existe, solo falla su paso o su cantidad y el log lo dice):
#   RadiationEfficiency, PeakRealizedGain, PeakGain, PeakDirectivity,
#   dB(GainTotal) con la categoria "Far Fields" y dB(RealizedGainTotal); el formato
#   de la variacion que acepta ExportConvergence/ExportProfile en un diseno concreto
#   (se prueban dos candidatos y el log dice cual funciono); que el contexto de la
#   esfera sea necesario/valido en "Antenna Parameters" (PyAEDT lo pasa asi).
# NO se ha ejecutado en AEDT real: probado solo con un AEDT simulado (tests).
# =============================================================================

# --- Elemento a exportar: deja descomentada UNA sola linea DESIGN (comenta las demas) ---
# DESIGN = "P01_MS1"
# DESIGN = "P01_MS2"
# DESIGN = "US3_MS3"
# DESIGN = "US3_PS4"
# DESIGN = "US3_PS6"
# DESIGN = "US3_PS6_4"
DESIGN = "US3_PS4_2_1"             # nombre del diseno en el arbol del proyecto
OUT_DIR = ""                        # vacio = carpeta del proyecto + "/ch9_element_export"
SETUP = "Setup_ch9"
SWEEP = "Sweep_7p5_8p5"             # barrido interpolado con S11
FF_SWEEP = "Edges_and_f0"           # barrido discreto con campos guardados
SPHERE = "FF_sphere"
PORT = "P1"
QUANTITIES = ["re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)"]
ANTENNA_QUANTITIES = ["RadiationEfficiency", "RadiatedPower", "AcceptedPower", "IncidentPower",
                      "PeakRealizedGain", "PeakGain", "PeakDirectivity"]
EXPORT_GAIN_CUTS = True             # realized_gain_cuts.csv (opcional)
GAIN_QUANTITIES = ["dB(GainTotal)", "dB(RealizedGainTotal)"]
EXPORT_CONVERGENCE = True           # convergence.conv y profile.prof

import os

import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign(DESIGN)
oSolutions = oDesign.GetModule("Solutions")
oReports = oDesign.GetModule("ReportSetup")
if not OUT_DIR:
    OUT_DIR = os.path.join(oProject.GetPath(), "ch9_element_export")
FOLDER = os.path.join(OUT_DIR, DESIGN)
if not os.path.isdir(FOLDER):
    os.makedirs(FOLDER)
LOG = open(os.path.join(FOLDER, "export_log.txt"), "a")
FAILED = []


def log(msg, level=0):
    LOG.write(msg + "\n")
    LOG.flush()
    try:
        oDesktop.AddMessage(oProject.GetName(), DESIGN, level, msg)
    except Exception:
        pass


def parse_variation(var):
    # "L='11.4mm' W='6.3mm'" -> [("L", "11.4mm"), ("W", "6.3mm")]
    out = []
    for item in var.split():
        k, _, v = item.partition("=")
        out.append((k, v.replace("'", "")))
    return out


def edit_sources(active):
    args = [["IncludePortPostProcessing:=", True, "SpecifySystemPower:=", False]]
    args.append(["Name:=", active + ":1", "Magnitude:=", "1W", "Phase:=", "0deg"])
    oSolutions.EditSources(args)


def safe(name):
    out = ""
    for ch in name:
        out += ch if ch.isalnum() else "_"
    return out.strip("_")


def fail(step, e):
    FAILED.append(step)
    log("ERR %s: %s" % (step, e), 2)


def one_report(category, quantities, sweeps, x_component, path, step):
    # one Data Table over FF_SWEEP on SPHERE, exported to CSV; the temporary report is always deleted
    name = "ch9_el_tmp"
    try:
        oReports.CreateReport(name, category, "Data Table", SETUP + " : " + FF_SWEEP,
                              ["Context:=", SPHERE], sweeps,
                              ["X Component:=", x_component, "Y Component:=", quantities])
        oReports.ExportToFile(name, path, False)
        log("OK  " + path)
        ok = True
    except Exception as e:
        log("ERR %s %s: %s" % (step, quantities, e), 2)
        ok = False
    try:
        oReports.DeleteReports([name])
    except Exception:
        pass
    return ok


def report_with_fallback(category, quantities, sweeps, x_component, path, step):
    # all quantities in one report; if AEDT rejects it, one report per quantity so that a single
    # wrong name does not lose the others (files <path>_<quantity>.csv)
    if one_report(category, quantities, sweeps, x_component, path, step):
        return
    log("aviso: %s conjunto fallo; se prueba cantidad a cantidad" % step, 1)
    done = 0
    base = path[:-4] if path.lower().endswith(".csv") else path
    for q in quantities:
        if one_report(category, [q], sweeps, x_component, base + "_" + safe(q) + ".csv", step + " " + q):
            done += 1
        else:
            FAILED.append(step + " " + q)
    log("%s: %d de %d cantidades exportadas por separado" % (step, done, len(quantities)))


def variation_candidates(var):
    # ExportConvergence/ExportProfile take "name=value,name=value" (PyAEDT export_convergence)
    pairs = parse_variation(var)
    out = []
    if pairs:
        out.append(",".join(["%s=%s" % (k, v) for k, v in pairs]))
    out.append("")
    return out


log("==== inicio elemento: %s -> %s" % (DESIGN, FOLDER))
log("setup %s, barrido %s, campos %s sobre %s, puerto %s" % (SETUP, SWEEP, FF_SWEEP, SPHERE, PORT))
try:
    oProject.Save()
    log("proyecto guardado")
except Exception as e:
    log("aviso: no se pudo guardar el proyecto (%s)" % e, 1)

# nominal variation, as the exact key string listed by GetAvailableVariations
var = None
try:
    nominal = None
    try:
        nominal = str(oDesign.GetNominalVariation())
    except Exception as e:
        log("aviso: GetNominalVariation no disponible (%s)" % e, 1)
    avail = [str(v) for v in oSolutions.GetAvailableVariations(SETUP + " : " + SWEEP)]
    log("variaciones disponibles: %s" % avail)
    log("variacion nominal: %s" % nominal)
    if not avail:
        var = ""
        log("aviso: sin variaciones (diseno sin variables); se usa la cadena vacia", 1)
    elif nominal in avail:
        var = nominal
    else:
        want = dict(parse_variation(nominal or ""))
        match = [v for v in avail if dict(parse_variation(v)) == want]
        if match:
            var = match[0]
        elif len(avail) == 1:
            var = avail[0]
            log("aviso: la nominal no coincide con la unica variacion disponible; se usa esta", 1)
        else:
            raise Exception("la variacion nominal no esta entre las %d disponibles" % len(avail))
    log("variacion usada: %s" % var)
except Exception as e:
    fail("variacion", e)

if var is None:
    log("ERR sin variacion no se exporta nada", 2)
else:
    pairs = parse_variation(var)

    # 1. Touchstone
    sname = os.path.join(FOLDER, DESIGN + ".s1p")
    log("... Touchstone")
    try:
        # same argument list as PyAEDT export_touchstone / the array exporter: Touchstone, all freqs,
        # renormalized to 50 ohm, S, last pass, magnitude/phase, 15 digits
        oSolutions.ExportNetworkData(var, [SETUP + ":" + SWEEP], 3, sname, ["all"], True, 50, "S", -1, 0, 15,
                                     False, False, False)
        log("OK  " + sname)
    except Exception as e:
        fail("Touchstone", e)

    # 2. far field of the 1 W excitation of P1
    log("... Edit Sources %s a 1 W" % PORT)
    try:
        edit_sources(PORT)
    except Exception as e:
        fail("EditSources", e)

    sweeps = ["Phi:=", ["All"], "Theta:=", ["All"], "Freq:=", ["All"]]
    for k, v in pairs:
        sweeps += [k + ":=", [v]]
    log("... campo lejano ff_%s.csv" % PORT)
    if not one_report("Far Fields", QUANTITIES, sweeps, "Phi", os.path.join(FOLDER, "ff_%s.csv" % PORT), "far field"):
        FAILED.append("far field")

    # 3. antenna parameters per frequency (Freq on X)
    asweeps = ["Freq:=", ["All"]]
    for k, v in pairs:
        asweeps += [k + ":=", [v]]
    log("... antenna_params.csv")
    report_with_fallback("Antenna Parameters", ANTENNA_QUANTITIES, asweeps, "Freq",
                         os.path.join(FOLDER, "antenna_params.csv"), "antenna params")

    # 4. optional gain cuts
    if EXPORT_GAIN_CUTS:
        log("... realized_gain_cuts.csv")
        report_with_fallback("Far Fields", GAIN_QUANTITIES, sweeps, "Phi",
                             os.path.join(FOLDER, "realized_gain_cuts.csv"), "gain cuts")

    # 5. convergence profile of the adaptive setup (+ profile table)
    if EXPORT_CONVERGENCE:
        cpath = os.path.join(FOLDER, "convergence.conv")
        log("... convergencia")
        done = False
        for cand in variation_candidates(var):
            try:
                oDesign.ExportConvergence(SETUP, cand, cpath)
                log("OK  %s (variaciones: '%s')" % (cpath, cand))
                if not os.path.isfile(cpath):
                    log("aviso: AEDT no ha creado %s" % cpath, 1)
                done = True
                break
            except Exception as e:
                log("ERR ExportConvergence con variaciones '%s': %s" % (cand, e), 2)
        if not done:
            FAILED.append("convergencia")
        ppath = os.path.join(FOLDER, "profile.prof")
        log("... perfil")
        done = False
        for cand in variation_candidates(var):
            try:
                try:
                    oDesign.ExportProfile(SETUP, cand, ppath)
                except Exception:
                    oDesign.ExportProfile(SETUP, cand, ppath, True)   # PyAEDT export_profile fallback
                log("OK  %s (variaciones: '%s')" % (ppath, cand))
                done = True
                break
            except Exception as e:
                log("ERR ExportProfile con variaciones '%s': %s" % (cand, e), 2)
        if not done:
            FAILED.append("perfil")

    # 6. leave 1 W on P1
    try:
        edit_sources(PORT)
        log("Edit Sources: 1 W en %s" % PORT)
    except Exception as e:
        fail("EditSources final", e)

if FAILED:
    log("==== fin en %s con pasos fallidos: %s" % (FOLDER, "; ".join(FAILED)), 2)
else:
    log("==== fin en %s sin errores" % FOLDER)
LOG.close()
