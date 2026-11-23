import json, csv, sys, numpy as np
import os
A = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/'  # antenna_design/
sys.path.insert(0, A + 'hfss/analysis')
from array_mimo_metrics import read_touchstone
import os
# Output folder for the generated data (*.js): $SUMMARY_OUT, default this script's folder.
OUT = os.environ.get('SUMMARY_OUT', os.path.dirname(os.path.abspath(__file__))) + '/'
r2 = lambda a, n=3: [round(float(v), n) for v in a]

# --- geometry of the candidates
GEOM = {}
for v, lab in [("P01_MS2", "Parche simple, línea + transformador λ/4"), ("US3_MS3", "Parche con ranura en U"),
               ("US3_PS4", "U-slot + parásito enterrado (Wp 11)"), ("US3_PS4_2_1", "U-slot + parásito Wp 10, patch_L 6,222"),
               ("US3_PS6", "U-slot + parásito recentrado (patch_L 6,29)"),
               ("US3_PS6_4", "U-slot + parásito, parche ancho W 14 (US3_PS6_4)")]:
    d = json.load(open(A + f'variants/{v}.json'))
    GEOM[v] = {"label": lab, "h": d["substrate"]["h_mm"], "board": d["substrate"]["size_mm"], "eps": d["substrate"]["eps_r"],
               "tand": d["substrate"]["tan_delta"], "patch": d["patch_polygon_mm"], "slots": d.get("slots_polygon_mm") or [],
               "feed": d["feed"]["feed_polygons_mm"], "par": [{"z": p["z_mm"], "poly": p["polygon_mm"]} for p in d.get("parasitic_patches", [])]}

# --- candidates: openEMS (base mesh) + HFSS where available
def oe(run, fine_grid=False):
    # fine_grid: rejilla de 1 MHz (s11_complex.csv, 7,5-8,5 GHz), la de las cifras auditadas; por defecto 5 MHz (s11_wideband.csv)
    if fine_grid: w = np.loadtxt(A + f'em/{run}/s11_complex.csv', delimiter=',', skiprows=1, usecols=(0, 1, 2, 3, 4))
    else: w = np.loadtxt(A + f'em/{run}/s11_wideband.csv', delimiter=',', skiprows=1)
    f = w[:, 0]; m = (f >= 7.0e9) & (f <= 9.0e9)
    s = w[:, 1] + 1j * w[:, 2]
    sm = json.load(open(A + f'em/{run}/nf2ff_summary.json'))['summary']
    gd = list(csv.DictReader(open(A + f'em/{run}/nf2ff_group_delay_broadside.csv')))
    return {"f": r2(f[m] / 1e9, 4), "db": r2(20 * np.log10(abs(s[m])), 2), "zr": r2(w[m, 3], 2), "zi": r2(w[m, 4], 2),
            "ff_f": [round(x['frequency_hz'] / 1e9, 4) for x in sm], "eta": [round(x['radiation_efficiency_Prad_over_Pacc'], 4) for x in sm],
            "grb": [round(x['realized_gain_broadside_dBi'], 3) for x in sm],
            "gd_f": [round(float(x['frequency_hz']) / 1e9, 4) for x in gd], "gd": [round(float(x['tau_g_y_s']) * 1e12, 1) for x in gd]}

def hf(folder, name):
    D = A + f'hfss/results/{folder}/'
    f, s, z0 = read_touchstone(D + name + '.s1p'); s = s[:, 0, 0]
    z = 50 * (1 + s) / (1 - s)
    ap = list(csv.DictReader(open(D + 'antenna_params.csv')))
    j = json.load(open(D + 'element_patterns_gd.json'))
    grb = []
    for fg in j['freqs_ghz']:
        c = j['per_freq'][f'{fg:g}']['xz']; grb.append(round(c['realized_gain_dbi'][c['theta_deg'].index(0.0)], 3))
    return {"f": r2(f / 1e9, 4), "db": r2(20 * np.log10(abs(s)), 4), "zr": r2(z.real, 2), "zi": r2(z.imag, 2),
            "ff_f": j['freqs_ghz'], "eta": [round(float(x['RadiationEfficiency []']), 4) for x in ap], "grb": grb,
            "gd_f": j['freqs_ghz'], "gd": j['group_delay']['broadside']['tau_ps']}

CAND = {
  "P01_MS2 · openEMS (027)": {"d": oe("P01_MS2_OPENEMS_027"), "c": "--s1", "dash": "solid", "geo": "P01_MS2"},
  "P01_MS2 · HFSS": {"d": hf("results_P01_MS2/P01_MS2", "P01_MS2"), "c": "--s1", "dash": "dash", "geo": "P01_MS2"},
  "US3_MS3 · openEMS (023)": {"d": oe("US3_MS3_OPENEMS_023"), "c": "--s4", "dash": "solid", "geo": "US3_MS3"},
  "US3_PS4 · openEMS (036)": {"d": oe("US3_PS4_OPENEMS_036"), "c": "--s5", "dash": "solid", "geo": "US3_PS4"},
  "US3_PS4_2_1 · openEMS (045)": {"d": oe("US3_PS4_2_1_OPENEMS_045"), "c": "--w1", "dash": "solid", "geo": "US3_PS4_2_1"},
  "US3_PS4_2_1 · HFSS": {"d": hf("results_US3_PS4_2_1/US3_PS4_2_1", "US3_PS4_2_1"), "c": "--w1", "dash": "dash", "geo": "US3_PS4_2_1"},
  "US3_PS6 · openEMS (038)": {"d": oe("US3_PS6_OPENEMS_038"), "c": "--s3", "dash": "solid", "geo": "US3_PS6"},
  "US3_PS6 · HFSS": {"d": hf("results_US3_PS6/US3_PS6", "US3_PS6"), "c": "--s3", "dash": "dash", "geo": "US3_PS6"},
  "US3_PS6_4 · openEMS (050)": {"d": oe("US3_PS6_4_OPENEMS_050", True), "c": "--s2", "dash": "solid", "geo": "US3_PS6_4"},
  "US3_PS6_4 · openEMS fina (051)": {"d": oe("US3_PS6_4_FINE_OPENEMS_051", True), "c": "--s2", "dash": "dash", "geo": "US3_PS6_4"},
  "US3_PS6_4 · HFSS": {"d": hf("results_US3_PS6_4/US3_PS6_4", "US3_PS6_4"), "c": "--s2", "dash": "dash", "geo": "US3_PS6_4"},
}

# --- S11 of variant families (openEMS, wideband 5 MHz)
def s11(run):
    w = np.loadtxt(A + f'em/{run}/s11_wideband.csv', delimiter=',', skiprows=1)
    f = w[:, 0]; m = (f >= 7.0e9) & (f <= 9.0e9)
    return [r2(f[m] / 1e9, 4), r2(20 * np.log10(abs(w[m, 1] + 1j * w[m, 2])), 2)]
FAM = {
  "U-slot + parásito enterrado (PS1 → PS6)": [("US3_MS3 sin parásito (023)", "US3_MS3_OPENEMS_023"), ("US3_PS1 (032)", "US3_PS1_OPENEMS_032"),
      ("US3_PS4 (036)", "US3_PS4_OPENEMS_036"), ("US3_PS5, propuesta Fable (037)", "US3_PS5_OPENEMS_037"), ("US3_PS6 (038)", "US3_PS6_OPENEMS_038"),
      ("US3_PS6 malla fina (039)", "US3_PS6_FINE_OPENEMS_039")],
  "Barrido del ancho del parásito Wp (US3_PS4)": [("Wp 11 mm · US3_PS4 (036)", "US3_PS4_OPENEMS_036"), ("Wp 10 mm · US3_PS4_2 (042)", "US3_PS4_2_OPENEMS_042"),
      ("Wp 9 mm · US3_PS4_3 (043)", "US3_PS4_3_OPENEMS_043"), ("Wp 8 mm · US3_PS4_4 (044)", "US3_PS4_4_OPENEMS_044"), ("Wp 7 mm · US3_PS4_1 (040)", "US3_PS4_1_OPENEMS_040")],
  "Ajuste fino de patch_L": [("US3_PS4_2 · Wp 10 (042)", "US3_PS4_2_OPENEMS_042"), ("US3_PS4_2_1 · patch_L 6,222 (045)", "US3_PS4_2_1_OPENEMS_045"),
      ("US3_PS4_2_1 malla fina (047)", "US3_PS4_2_1_FINE_OPENEMS_047"), ("US3_PS6 · 6,29 (038)", "US3_PS6_OPENEMS_038"),
      ("US3_PS6_1 · 6,32 (046)", "US3_PS6_1_OPENEMS_046"), ("US3_PS6_2 · 6,38 (048)", "US3_PS6_2_OPENEMS_048")],
}
VAR = {k: [[lab, *s11(r)] for lab, r in v] for k, v in FAM.items()}

# --- arrays (HFSS embedded fields)
ARR = {}
for arr, geo, folder, pitches in [("ARR1x5_US3_PS4_2_1_dparam", "US3_PS4_2_1", "results_US3_PS4_2_1/ARR1x5_US3_PS4_2_1_dparam/virtual_3d", ["13p5", "17", "18p2", "20p5"]),
                                  ("ARR1x4_P01_MS2_dparam", "P01_MS2", "results_P01_MS2/ARR1x4_P01_MS2_dparam/virtual_3d", ["13p5", "17", "18p2", "20p5"]),
                                  ("ARR1x5_P01_MS2_dparam", "P01_MS2", "results_P01_MS2/ARR1x5_P01_MS2_dparam/virtual_3d", ["13p5", "17", "18p2", "20p5"]),
                                  ("ARR1x5_US3_PS6_dparam", "US3_PS6", "results_US3_PS6/ARR1x5_US3_PS6_dparam/virtual_3d", ["18p2"]),
                                  ("ARR1x5_US3_PS6_4_dparam", "US3_PS6_4", "results_US3_PS6_4/ARR1x5_US3_PS6_4_dparam/virtual_3d", ["18p2"])]:
    rec = {"geo": geo, "n": int(arr[5]), "pitches": {}}
    for p in pitches:
        j = json.load(open(A + f'hfss/results/{folder}/array_virtual_3d_d{p}.json'))
        q = {"freqs": j["freqs_ghz"], "gd": {k: v["tau_ps"] for k, v in j["group_delay_broadside"].items()}, "pf": {}}
        for f, r in j["per_freq"].items():
            q["pf"][f] = {"th": r["theta_deg"], "ph": r["phi_deg"], "P": [[round(v, 1) for v in row] for row in r["physical_dbi"]],
                          "V": [[round(max(v, -40), 1) for v in row] for row in r["virtual_db"]],
                          "xz": [r["xz"]["theta_deg"], r["xz"]["physical_dbi"], r["xz"]["virtual_db"]],
                          "yz": [r["yz"]["theta_deg"], r["yz"]["physical_dbi"], r["yz"]["virtual_db"]], "pk": r["physical_peak_dbi"]}
        rec["pitches"][p.replace("p", ",")] = q
        # monostáticos (virtual_mono): solo cortes xz y métricas; (a) = bistatic_current, (b) = bistatic_plus_monostatic
        mp = A + f'hfss/results/{folder.replace("virtual_3d", "virtual_mono")}/array_virtual_monostatic_d{p}.json'
        if os.path.exists(mp):
            jm = json.load(open(mp)); mo = {"th": None, "pf": {}}
            for f, r in jm["per_freq"].items():
                e = {}
                for key, bk in (("a", "bistatic_current"), ("b", "bistatic_plus_monostatic")):
                    b = r[bk]; bm = {}
                    for st, bb in b["beams"].items():
                        x = bb["xz"]; th = bb["xz_cut"]["theta_deg"]
                        if mo["th"] is None: mo["th"] = th
                        assert th == mo["th"]
                        bm[st.replace("theta0_", "").replace("deg", "")] = {"c": bb["xz_cut"]["db"], "pk": x["peak_deg"], "hp": x["hpbw_deg"], "sl": x["max_sidelobe_db"],
                                                                           "qg": x.get("quasi_grating_lobes_2d_subset", []), "gl": x["grating_lobe_present"]}
                    e[key] = {"acq": b["acquisitions"], "pos": b["virtual_positions_mm_multiplicity"], "s": bm}
                mo["pf"][f] = e
            mo["ev"] = jm["evidence"]; q["mono"] = mo
    ARR[arr] = rec
open(OUT + 'summary_data.js', 'w').write("const GEOM=" + json.dumps(GEOM) + ";\nconst CAND=" + json.dumps(CAND, separators=(',', ':')) +
    ";\nconst VAR=" + json.dumps(VAR, separators=(',', ':')) + ";\nconst ARR=" + json.dumps(ARR, separators=(',', ':')) + ";\n")
print({k: len(v["d"]["f"]) for k, v in CAND.items()}, list(ARR), [list(v["pitches"]) for v in ARR.values()])
