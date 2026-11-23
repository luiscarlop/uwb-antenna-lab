#!/usr/bin/env python3
"""Generador parametrico de la serie U-slot sobre parche con sonda (familia USLOT_PROBE_H207).

Funcion pura: no importa openEMS ni numpy. Dados los parametros del parche, de la sonda y de la U genera el JSON de variante
con el esquema de P01_R2.json (patch_polygon_mm, slots_polygon_mm, feed probe_lumped_vertical) y valida la geometria.

Estado de todo lo generado: GEOMETRY_ONLY. Las formulas (Hammerstad, longitud de la U) son estimaciones geometricas; no
dan S11, ganancia, eficiencia, fase, retardo ni ancho de banda.

Uso:
  python variants/uslot_family.py --preset US0 --out variants/US0.json
  python variants/uslot_family.py --preset US1 --out variants/US1.json
  python variants/uslot_family.py --base variants/US1.json --set Lu=3.4 --id US2 --out variants/US2.json
  python variants/uslot_family.py --verify variants/US1.json      # regenera desde uslot_params y compara

--set cambia UNA sola dimension por llamada (claves: L, W, s_over_L, Wu, Lu, t, y0, open). Material, h, cobre y placa son
comunes a toda la serie y no se pueden cambiar desde aqui.
"""
import argparse
import json
import math
import sys
from pathlib import Path

FAMILY = "USLOT_PROBE_H207"
C_GHZ_MM = 299.792458  # c / (1 GHz * 1 mm)

# --- Decisiones comunes de la serie (orquestador, ronda Claude 12). Todas las variantes las comparten. ---
SUBSTRATE = {"name": "FR4_homogeneous_PROVISIONAL_h2p07", "eps_r": 4.4, "tan_delta": 0.017, "h_mm": 2.07,
             "size_mm": [26.0, 26.0]}
METAL = {"conductivity_S_m": 58000000.0, "thickness_m": 3.5e-05}
F0_GHZ = 7.9872
BAND_GHZ = (7.7376, 8.2368)

# --- Margenes de validacion (criterio declarado, no cifras de fabricante: no se han consultado reglas de ningun fabricante) ---
MIN_SLOT_WIDTH_MM = 0.5       # minimo exigido; preferible 0.7-1.0 por malla
MIN_COPPER_TO_EDGE_MM = 0.7   # cobre entre ranura y borde del parche
MIN_ISLAND_MM = 0.7           # anchura minima de cobre entre brazos de la U
MIN_PROBE_SLOT_MM = 1.0       # distancia sonda-ranura exigida
MIN_PROBE_EDGE_MM = 1.0       # distancia sonda-borde del parche (aviso, el parche R2 usaba 1.272)
BOARD_MARGIN_MM = 1.0

# --- Calibracion EM de P01_R2 (h = 1.6 mm): fr de ajuste circuital sobre EM_SIMULATED, malla fina (005) ---
P01_R2_REF = {"h_mm": 1.6, "L_mm": 7.95, "W_mm": 11.42126651368023, "s_over_L": 0.34, "fr_fit_GHz_fine_005": 7.723,
              "fr_fit_GHz_base_004": 7.721, "source": "em/circuit_fits/P01_R2_FINE_OPENEMS_005_fit.json"}

# --- Claves de uslot_params y alias de la CLI ---
PARAM_KEYS = ["L_mm", "W_mm", "s_over_L", "Wu_mm", "Lu_mm", "t_mm", "y0_mm", "open_toward"]
ALIASES = {"L": "L_mm", "W": "W_mm", "s_over_L": "s_over_L", "s": "s_over_L", "Wu": "Wu_mm", "Lu": "Lu_mm", "t": "t_mm",
           "y0": "y0_mm", "open": "open_toward", "open_toward": "open_toward"}
U_KEYS = ("Wu_mm", "Lu_mm", "t_mm", "y0_mm", "open_toward")

PRESETS = {
    "US0": {"L_mm": 7.67, "W_mm": 11.421266, "s_over_L": 0.34, "Wu_mm": None, "Lu_mm": None, "t_mm": None,
            "y0_mm": None, "open_toward": None},
    "US1": {"L_mm": 7.67, "W_mm": 11.421266, "s_over_L": 0.34, "Wu_mm": 4.4, "Lu_mm": 3.2, "t_mm": 0.8,
            "y0_mm": -0.7, "open_toward": "+y"},
}


# ---------------------------------------------------------------- geometria pura
def _r(x, nd=6):
    v = round(float(x), nd)
    return 0.0 if v == 0 else v


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _seg_intersect(p1, p2, p3, p4):
    d1, d2, d3, d4 = _cross(p3, p4, p1), _cross(p3, p4, p2), _cross(p1, p2, p3), _cross(p1, p2, p4)
    if ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4)):
        return True

    def on(a, b, p):
        return min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12 and min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12
    return ((abs(d1) < 1e-12 and on(p3, p4, p1)) or (abs(d2) < 1e-12 and on(p3, p4, p2))
            or (abs(d3) < 1e-12 and on(p1, p2, p3)) or (abs(d4) < 1e-12 and on(p1, p2, p4)))


def _pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    u = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n))
    return math.hypot(p[0] - (a[0] + u * dx), p[1] - (a[1] + u * dy))


def _seg_seg(a, b, c, d):
    if _seg_intersect(a, b, c, d):
        return 0.0
    return min(_pt_seg(a, c, d), _pt_seg(b, c, d), _pt_seg(c, a, b), _pt_seg(d, a, b))


def _edges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def is_simple(poly):
    e = _edges(poly)
    n = len(e)
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if _seg_intersect(*e[i], *e[j]):
                return False
    return True


def signed_area(poly):
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in _edges(poly))


def point_in_polygon(pt, poly):
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in _edges(poly):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def poly_poly_distance(p, q):
    return min(_seg_seg(*a, *b) for a in _edges(p) for b in _edges(q))


def point_poly_boundary_distance(pt, poly):
    return min(_pt_seg(pt, a, b) for a, b in _edges(poly))


def rectangle(W, L):
    return [(_r(-W / 2), _r(-L / 2)), (_r(W / 2), _r(-L / 2)), (_r(W / 2), _r(L / 2)), (_r(-W / 2), _r(L / 2))]


def u_polygon(Wu, Lu, t, y0, open_toward):
    """Poligono (8 vertices, antihorario) de la ranura en U, centrada en x = 0.
    y0 = coordenada y del borde EXTERIOR de la base (extremo cerrado). Los brazos se extienden Lu desde y0 hacia el lado
    indicado por open_toward ('+y' abre hacia +y, es decir, hacia el borde opuesto a la sonda; '-y' abre hacia la sonda)."""
    xl, xr = -Wu / 2, Wu / 2
    base = [(xl, 0.0), (xr, 0.0), (xr, Lu), (xr - t, Lu), (xr - t, t), (xl + t, t), (xl + t, Lu), (xl, Lu)]
    if open_toward == "+y":
        pts = [(x, y0 + y) for x, y in base]
    elif open_toward == "-y":
        pts = [(x, y0 - y) for x, y in reversed(base)]  # espejo en y e inversion de orden para mantener el sentido antihorario
    else:
        raise ValueError("open_toward debe ser '+y' o '-y'")
    return [(_r(x), _r(y)) for x, y in pts]


def u_mean_length(Wu, Lu, t):
    """Longitud de la linea media de la U: base (Wu - t) + 2 brazos de (Lu - t/2) = Wu + 2 Lu - 2 t."""
    return Wu + 2 * Lu - 2 * t


# ---------------------------------------------------------------- formulas (estimaciones geometricas)
def hammerstad(er, h, W):
    eeff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * h / W) ** -0.5
    dl = 0.412 * h * (eeff + 0.3) * (W / h + 0.264) / ((eeff - 0.258) * (W / h + 0.8))
    return eeff, dl


def k_cal():
    """Cociente (fr de ajuste EM de P01_R2) / (fr Hammerstad de P01_R2). Absorbe el sesgo del modelo y de la sonda a h = 1.6."""
    r = P01_R2_REF
    eeff, dl = hammerstad(SUBSTRATE["eps_r"], r["h_mm"], r["W_mm"])
    return r["fr_fit_GHz_fine_005"] / (C_GHZ_MM / (2 * math.sqrt(eeff) * (r["L_mm"] + 2 * dl)))


def fr_calibrated_ghz(L, W, h=None):
    h = SUBSTRATE["h_mm"] if h is None else h
    eeff, dl = hammerstad(SUBSTRATE["eps_r"], h, W)
    return k_cal() * C_GHZ_MM / (2 * math.sqrt(eeff) * (L + 2 * dl))


def L_for_fr_mm(fr_ghz, W, h=None):
    h = SUBSTRATE["h_mm"] if h is None else h
    eeff, dl = hammerstad(SUBSTRATE["eps_r"], h, W)
    return k_cal() * C_GHZ_MM / (2 * math.sqrt(eeff) * fr_ghz) - 2 * dl


def slot_resonance_estimate_ghz(Wu, Lu, t, W, h=None):
    """f = c / (2 sqrt(eeff) l) con l = longitud media de la U y eeff de Hammerstad del parche (hipotesis: la ranura ve la misma
    permitividad efectiva que el parche). Estimacion de ordenacion, no un resultado."""
    h = SUBSTRATE["h_mm"] if h is None else h
    eeff, _ = hammerstad(SUBSTRATE["eps_r"], h, W)
    return C_GHZ_MM / (2 * math.sqrt(eeff) * u_mean_length(Wu, Lu, t))


# ---------------------------------------------------------------- validacion
def has_slot(p):
    return all(p[k] is not None for k in U_KEYS)


def validate_params(p):
    if set(p) != set(PARAM_KEYS):
        raise ValueError(f"uslot_params debe tener exactamente las claves {PARAM_KEYS}")
    if any(p[k] is None for k in ("L_mm", "W_mm", "s_over_L")):
        raise ValueError("L_mm, W_mm y s_over_L son obligatorios")
    if any(p[k] is None for k in U_KEYS) and any(p[k] is not None for k in U_KEYS):
        raise ValueError("Los cinco parametros de la U van todos o ninguno (US0 = sin ranura)")
    if not (p["L_mm"] > 0 and p["W_mm"] > 0 and 0 < p["s_over_L"] < 0.5):
        raise ValueError("L, W > 0 y 0 < s/L < 0.5")


def build_geometry(p):
    """Devuelve (patch, slots, feed_xy). Lanza ValueError si falla alguna comprobacion de la serie."""
    validate_params(p)
    L, W = p["L_mm"], p["W_mm"]
    patch = rectangle(W, L)
    feed = (0.0, _r(-p["s_over_L"] * L, 3))
    slots = []
    if has_slot(p):
        slots = [u_polygon(p["Wu_mm"], p["Lu_mm"], p["t_mm"], p["y0_mm"], p["open_toward"])]
    check_geometry(p, patch, slots, feed)
    return patch, slots, feed


def check_geometry(p, patch, slots, feed):
    sx, sy = SUBSTRATE["size_mm"]
    errs = []
    if not is_simple(patch) or signed_area(patch) <= 0:
        errs.append("parche: poligono no simple o no antihorario")
    xs, ys = zip(*patch)
    if min(xs) < -sx / 2 + BOARD_MARGIN_MM or max(xs) > sx / 2 - BOARD_MARGIN_MM or min(ys) < -sy / 2 + BOARD_MARGIN_MM or max(ys) > sy / 2 - BOARD_MARGIN_MM:
        errs.append("parche: menos de %.1f mm de margen a la placa" % BOARD_MARGIN_MM)
    if not point_in_polygon(feed, patch):
        errs.append("sonda fuera del parche")
    if point_poly_boundary_distance(feed, patch) < MIN_PROBE_EDGE_MM:
        errs.append("sonda a menos de %.1f mm del borde del parche" % MIN_PROBE_EDGE_MM)
    for s in slots:
        if not is_simple(s) or signed_area(s) <= 0:
            errs.append("ranura: poligono no simple o no antihorario")
        if p["t_mm"] < MIN_SLOT_WIDTH_MM - 1e-9:
            errs.append("ranura: t < %.2f mm" % MIN_SLOT_WIDTH_MM)
        if p["Wu_mm"] - 2 * p["t_mm"] < MIN_ISLAND_MM - 1e-9:
            errs.append("isla entre brazos < %.2f mm de cobre" % MIN_ISLAND_MM)
        if p["Lu_mm"] <= p["t_mm"]:
            errs.append("Lu debe ser mayor que t")
        if not all(point_in_polygon(v, patch) for v in s):
            errs.append("ranura: algun vertice fuera del parche")
        if poly_poly_distance(s, patch) < MIN_COPPER_TO_EDGE_MM - 1e-9:
            errs.append("ranura a menos de %.1f mm de cobre hasta el borde" % MIN_COPPER_TO_EDGE_MM)
        if point_in_polygon(feed, s):
            errs.append("sonda dentro de la ranura")
        if point_poly_boundary_distance(feed, s) < MIN_PROBE_SLOT_MM - 1e-9:
            errs.append("sonda a menos de %.1f mm de la ranura" % MIN_PROBE_SLOT_MM)
    if errs:
        raise ValueError("; ".join(errs))


def geometry_report(p, patch, slots, feed):
    rep = {"patch_mm": [p["W_mm"], p["L_mm"]], "probe_xy_mm": list(feed),
           "probe_to_patch_edge_mm": _r(point_poly_boundary_distance(feed, patch)),
           "probe_to_nearest_radiating_edge_mm": _r(p["L_mm"] / 2 - abs(feed[1])),
           "patch_to_board_edge_mm": {"x": _r(SUBSTRATE["size_mm"][0] / 2 - p["W_mm"] / 2), "y": _r(SUBSTRATE["size_mm"][1] / 2 - p["L_mm"] / 2)}}
    if slots:
        s = slots[0]
        rep.update({"slot_to_patch_edge_min_mm": _r(poly_poly_distance(s, patch)),
                    "probe_to_slot_min_mm": _r(point_poly_boundary_distance(feed, s)),
                    "slot_width_mm": p["t_mm"], "island_between_arms_mm": _r(p["Wu_mm"] - 2 * p["t_mm"]),
                    "copper_side_strip_each_mm": _r((p["W_mm"] - p["Wu_mm"]) / 2),
                    "u_y_extent_mm": [_r(min(y for _, y in s)), _r(max(y for _, y in s))],
                    "u_mean_length_mm": _r(u_mean_length(p["Wu_mm"], p["Lu_mm"], p["t_mm"]), 4)})
    return rep


def computation_block(p, patch, slots, feed):
    eeff, dl = hammerstad(SUBSTRATE["eps_r"], SUBSTRATE["h_mm"], p["W_mm"])
    eeff16, dl16 = hammerstad(SUBSTRATE["eps_r"], P01_R2_REF["h_mm"], P01_R2_REF["W_mm"])
    comp = {
        "method": "Hammerstad (eeff, dL) con escalado de P01_R2 por k_cal = fr_ajuste_EM / fr_Hammerstad (h = 1.6 mm) aplicado a h = 2.07 mm; "
                  "longitud media de la U = Wu + 2 Lu - 2 t. Solo estimacion geometrica (GEOMETRY_ONLY).",
        "inputs": {"eps_r": SUBSTRATE["eps_r"], "h_mm": SUBSTRATE["h_mm"], "W_mm": p["W_mm"], "P01_R2_reference": P01_R2_REF,
                   "hammerstad_h2p07": {"eps_eff": _r(eeff, 5), "delta_L_mm": _r(dl, 5)},
                   "hammerstad_h1p6_R2": {"eps_eff": _r(eeff16, 5), "delta_L_mm": _r(dl16, 5)},
                   "k_cal": _r(k_cal(), 5)},
        "patch_resonance_estimate": {
            "fr_calibrated_GHz": _r(fr_calibrated_ghz(p["L_mm"], p["W_mm"]), 4),
            "L_for_fr_7p723_GHz_mm": _r(L_for_fr_mm(P01_R2_REF["fr_fit_GHz_fine_005"], p["W_mm"]), 4),
            "uncertainty": "k_cal varia 0.932-0.935 entre P01 (L 8.28), P01_R1 (7.65) y P01_R2 (7.95) a h = 1.6 mm (+-0.2 %, ~+-15 MHz); "
                           "la extrapolacion a h = 2.07 mm (mayor Ls de sonda, otro campo de borde, FR4 homogeneo) no esta verificada: "
                           "orden de magnitud +-2-3 % en fr (~+-200 MHz). Con una ranura en U el valor no aplica (la U perturba el modo).",
            "evidence": "GEOMETRY_ONLY"},
        "geometry_checks": geometry_report(p, patch, slots, feed),
        "series_margins_mm": {"min_slot_width": MIN_SLOT_WIDTH_MM, "min_copper_slot_to_edge": MIN_COPPER_TO_EDGE_MM,
                              "min_island": MIN_ISLAND_MM, "min_probe_to_slot": MIN_PROBE_SLOT_MM,
                              "min_probe_to_patch_edge": MIN_PROBE_EDGE_MM, "board_margin": BOARD_MARGIN_MM,
                              "note": "criterios de diseno declarados; ninguna regla de fabricante consultada"},
    }
    if slots:
        comp["slot_resonance_estimate"] = {
            "f_half_wave_GHz": _r(slot_resonance_estimate_ghz(p["Wu_mm"], p["Lu_mm"], p["t_mm"], p["W_mm"]), 4),
            "formula": "f = c / (2 sqrt(eps_eff) * l), l = longitud media de la U, eps_eff de Hammerstad del parche",
            "status": "HIPOTESIS de ordenacion: no hay regla verificada que relacione l con la resonancia real de la U; la "
                      "frecuencia real depende del acoplo con el parche y solo la dara la simulacion EM."}
    return comp


def series_common():
    return {"declared_by": "orquestador, ronda Claude 12",
            "feed": "sonda vertical concentrada de 50 ohm (probe_lumped_vertical), x = 0, s/L comun a la serie (cambia con L solo si L es la variable)",
            "material": "FR4 homogeneo eps_r 4.4, tan_delta 0.017, h = 2.07 mm (espesor total del articulo EuCAP 2027; el homogeneo es una "
                        "aproximacion de su pila S1000H de seis capas), cobre 35 um, 5.8e7 S/m",
            "board": "26 x 26 mm centrada, masa completa (la del laboratorio, NO la del articulo: 17.4 x 21 mm)",
            "origin": "El articulo solo da: parche excitado por sonda, resonancia a lo largo de y, S1000H 2.07 mm, eps_r 4.4-4.7, tan_delta 0.017. "
                      "NO da dimensiones de parche, ranuras ni posicion de sonda: ninguna dimension de esta serie procede del articulo, "
                      "y las que salgan de optimizacion tampoco se le atribuyen. Un U-slot simple es una aproximacion de investigacion, "
                      "no una reproduccion de su parche apilado con cavidad, parasito y peine de ranuras.",
            "rule": "una sola dimension de la U cambia por variante; parche, sonda y material fijos al comparar"}


# ---------------------------------------------------------------- construccion del JSON
PRESET_TEXT = {
    "US0": {
        "base_design": "P01_rectangular_patch",
        "changed_vs_previous": {"P01_R2": {
            "h_mm": [1.6, 2.07], "L_mm": [7.95, 7.67], "W_mm": [11.42126651368023, 11.421266], "feed_y_mm": [-2.703, -2.608],
            "feed_s_over_L": [0.34, 0.34],
            "note": "No es un refinamiento: es el parche P01_R2 re-escalado a h = 2.07 mm para conservar su posicion de resonancia (fr de "
                    "ajuste EM 7.723 GHz) con W y s/L iguales. Cambia h (impuesto por la serie), L (consecuencia) y la sonda (consecuencia de s/L)."}},
        "rationale": "US0 es la REFERENCIA sin ranura de la serie U-slot a h = 2.07 mm; no se optimiza. Se parte de la unica evidencia EM de un parche "
                     "con sonda (P01_R2, h 1.6: fr de ajuste 7.723 GHz, minimo de S11 en ~8.05 GHz, Re(Zin) maximo 107.8 ohm, cumple -6 dB en las "
                     "muestras de dos mallas con 0.29 dB de margen). Al subir h a 2.07 mm, eps_eff de Hammerstad baja de 3.738 a 3.654 y dL sube de "
                     "0.713 a 0.909 mm: ambos efectos casi se compensan y L solo cambia de 7.95 a 7.67 mm para la misma fr, calibrada con k_cal = "
                     "fr_EM/fr_Hammerstad = 0.934 (a h = 1.6). Se conservan W (11.4213 mm: fija R_edge y el ancho de la cavidad) y s/L = 0.34 "
                     "porque la R de entrada del modo es R_edge sin^2(pi s/L) y R_edge ~ Q h/(eps W L): con h 29 % mayor y Q algo menor, R_edge "
                     "queda del mismo orden (hipotesis, sin verificar). RIESGO PRINCIPAL: la inductancia serie de la sonda crece con h (hipotesis Ls ~ h: de "
                     "~1.3 a ~1.7 nH, X ~ 65 -> ~85 ohm a f0); el modelo de guia, con esa Ls y Q 10.6-13, da un peor caso en banda de -4 a -5 dB "
                     "(GUIDE_MODEL, no resultado EM), asi que US0 puede NO cumplir -6 dB. Es aceptable: es la referencia de la serie. Estado GEOMETRY_ONLY."},
    "US1": {
        "base_design": "P02_u_slot_patch",
        "changed_vs_previous": {"US0": {
            "slot": ["none", "U-slot: Wu 4.4, Lu 3.2, t 0.8, base en y0 -0.7, abierta hacia +y"],
            "note": "Unica variacion: se anade la U. Parche (11.4213 x 7.67), sonda (0, -2.608) y material identicos a US0."}},
        "rationale": "Primera variante con U-slot (aproximacion de investigacion, no reproduccion del articulo ni de ninguna cifra suya). Base "
                     "perpendicular a y y brazos paralelos a y (eje de resonancia), abierta hacia +y, es decir, hacia el borde opuesto a la sonda; "
                     "la sonda queda fuera de la U, por debajo de la base, a 1.9 mm de ella. Dimension por criterio fisico declarado: longitud media "
                     "de la U l = Wu + 2 Lu - 2 t = 9.2 mm ~ media longitud de onda guiada a ~8.5 GHz con eps_eff 3.654 (hipotesis de ordenacion), "
                     "buscando una segunda resonancia por encima de la del parche (~7.72 GHz en US0) para que ambas rodeen la banda 7.7376-8.2368 "
                     "GHz; no hay garantia de que la resonancia real de la U coincida con esa estimacion. t = 0.8 mm (>= 0.5 exigido, 0.7-1.0 "
                     "preferible por malla); cobre >= 1.3 mm entre ranura y bordes, isla entre brazos 2.8 mm, sonda >= 1.9 mm de la ranura. "
                     "Sobre la orientacion (abierta hacia +y con la base cerca de la sonda): es una HIPOTESIS de partida; no tengo una regla "
                     "verificada que decida entre abrir hacia la sonda o en sentido opuesto, y la orientacion es un parametro (open) para probarla "
                     "mas adelante. Se eligio +y porque deja cobre continuo en el camino sonda-borde radiante cercano y una distancia sonda-ranura "
                     "holgada. Estado GEOMETRY_ONLY: sin S11, ganancia, eficiencia ni retardo."},
}


def build_variant(vid, p, base_design, changed_vs_previous, rationale):
    patch, slots, feed = build_geometry(p)
    out = {
        "id": vid,
        "family": FAMILY,
        "base_design": base_design,
        "evidence": "GEOMETRY_ONLY",
        "substrate": json.loads(json.dumps(SUBSTRATE)),
        "metal": dict(METAL),
        "patch_polygon_mm": [list(v) for v in patch],
        "slots_polygon_mm": [[list(v) for v in s] for s in slots],
        "feed": {"type": "probe_lumped_vertical", "x_mm": 0.0, "y_mm": feed[1], "z0_ohm": 50},
        "uslot_params": dict(p),
        "series_common": series_common(),
        "changed_vs_previous": changed_vs_previous,
        "rationale": rationale,
        "computation": computation_block(p, patch, slots, feed),
    }
    return out


def build_preset(name):
    t = PRESET_TEXT[name]
    return build_variant(name, dict(PRESETS[name]), t["base_design"], t["changed_vs_previous"], t["rationale"])


def derive(base_json, key, value, new_id):
    """Nueva variante a partir de otra cambiando UNA sola clave de uslot_params. Si la base no tiene U (US0), no se puede
    cambiar una dimension de la U: primero hay que partir de una variante con U."""
    p = dict(base_json["uslot_params"])
    if key not in p:
        raise ValueError(f"clave desconocida {key}")
    if key in U_KEYS and not has_slot(p):
        raise ValueError(f"la base {base_json['id']} no tiene U; no se puede cambiar {key}")
    old = p[key]
    if old == value:
        raise ValueError(f"{key} ya vale {value}: no hay cambio")
    p[key] = value
    pb, sb, fb = build_geometry(dict(base_json["uslot_params"]))
    derived = {}
    for k, vold, vnew in (("feed_y_mm", fb[1], build_geometry(p)[2][1]),):
        if vold != vnew:
            derived[k] = [vold, vnew]
    chg = {base_json["id"]: {key: [old, value]}}
    if derived:
        chg[base_json["id"]].update({"derived": derived})
    chg[base_json["id"]]["note"] = (f"Variable unica: {key} {old} -> {value}. El resto de parametros de uslot_params, el material, h y la placa no cambian."
                                    + (" La posicion de la sonda se recalcula porque s/L es fijo (consecuencia, no una segunda variable)." if derived else ""))
    rationale = (f"{new_id}: variante de {base_json['id']} que cambia solo {key} ({old} -> {value}). Parche, sonda (salvo lo derivado de s/L) y "
                 f"material fijos para poder atribuir cualquier diferencia de la simulacion a esta dimension. Generada por variants/uslot_family.py; "
                 f"la dimension nueva NO proviene del articulo EuCAP ni de ninguna optimizacion hasta que exista un resultado EM que la respalde. "
                 f"Estado GEOMETRY_ONLY.")
    return build_variant(new_id, p, base_json["base_design"], chg, rationale)


def dumps(d):
    return json.dumps(d, indent=1) + "\n"


def geometry_view(d):
    return {k: d[k] for k in ("family", "substrate", "metal", "patch_polygon_mm", "slots_polygon_mm", "feed", "uslot_params")}


def verify(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    p = d["uslot_params"]
    re = build_variant(d["id"], p, d["base_design"], d["changed_vs_previous"], d["rationale"])
    same_full = dumps(re) == Path(path).read_text(encoding="utf-8")
    return geometry_view(re) == geometry_view(d), same_full


def parse_value(key, s):
    if key == "open_toward":
        if s not in ("+y", "-y"):
            raise ValueError("open debe ser +y o -y")
        return s
    return float(s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--base", help="JSON de variante de partida (con uslot_params)")
    ap.add_argument("--set", dest="sets", action="append", default=[], metavar="CLAVE=VALOR")
    ap.add_argument("--id", dest="new_id")
    ap.add_argument("--out")
    ap.add_argument("--verify")
    a = ap.parse_args(argv)
    if a.verify:
        geo, full = verify(a.verify)
        print(f"{a.verify}: geometria regenerada identica = {geo}; fichero completo identico byte a byte = {full}")
        return 0 if geo and full else 1
    if a.preset:
        d = build_preset(a.preset)
    elif a.base:
        if len(a.sets) != 1:
            ap.error("--set debe aparecer exactamente una vez (una sola dimension por variante)")
        if not (a.new_id and a.out):
            ap.error("--base requiere --id y --out")
        k, _, v = a.sets[0].partition("=")
        if k not in ALIASES or not v:
            ap.error(f"--set CLAVE=VALOR con CLAVE en {sorted(ALIASES)}")
        key = ALIASES[k]
        d = derive(json.loads(Path(a.base).read_text(encoding="utf-8")), key, parse_value(key, v), a.new_id)
    else:
        ap.error("usa --preset, --base/--set o --verify")
    text = dumps(d)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"escrito {a.out} ({d['id']}, {d['evidence']})")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
