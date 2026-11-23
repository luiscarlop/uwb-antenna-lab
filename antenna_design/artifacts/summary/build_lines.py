import json, csv, sys, os, numpy as np
import os
A = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/'  # antenna_design/
sys.path.insert(0, A + 'hfss/analysis')
from array_mimo_metrics import read_touchstone
import os
# Output folder for the generated data (*.js): $SUMMARY_OUT, default this script's folder.
OUT = os.environ.get('SUMMARY_OUT', os.path.dirname(os.path.abspath(__file__))) + '/'
r2 = lambda a, n=3: [round(float(v), n) for v in a]
CS = {r['id']: r for r in json.load(open(A + 'campaign_state.json'))['em_runs']}
missing = []

def oe(run):
    out = {}
    p = A + f'em/{run}/'
    if os.path.exists(p + 's11_complex.csv'):   # rejilla de 1 MHz (7,5-8,5 GHz): es la que usan las cifras de campaign_state
        w = np.loadtxt(p + 's11_complex.csv', delimiter=',', skiprows=1, usecols=(0, 1, 2, 3, 4)); f = w[:, 0]; m = (f >= 7.5e9) & (f <= 8.5e9)
        s = w[:, 1] + 1j * w[:, 2]
        out.update(f=r2(f[m] / 1e9, 4), db=r2(20 * np.log10(abs(s[m])), 4), zr=r2(w[m, 3], 2), zi=r2(w[m, 4], 2), grid='1 MHz')
    elif os.path.exists(p + 's11_wideband.csv'):
        w = np.loadtxt(p + 's11_wideband.csv', delimiter=',', skiprows=1); f = w[:, 0]; m = (f >= 7.0e9) & (f <= 9.0e9)
        s = w[:, 1] + 1j * w[:, 2]
        out.update(f=r2(f[m] / 1e9, 4), db=r2(20 * np.log10(abs(s[m])), 4), zr=r2(w[m, 3], 2), zi=r2(w[m, 4], 2), grid='5 MHz')
    else: missing.append((run, 's11'))
    if os.path.exists(p + 'nf2ff_summary.json'):
        sm = json.load(open(p + 'nf2ff_summary.json'))['summary']
        out.update(ff_f=[round(x['frequency_hz'] / 1e9, 4) for x in sm], eta=[round(x['radiation_efficiency_Prad_over_Pacc'], 4) for x in sm],
                   grb=[round(x['realized_gain_broadside_dBi'], 3) for x in sm])
    else: missing.append((run, 'eta/ganancia'))
    if os.path.exists(p + 'nf2ff_group_delay_broadside.csv'):
        gd = list(csv.DictReader(open(p + 'nf2ff_group_delay_broadside.csv')))
        out.update(gd_f=[round(float(x['frequency_hz']) / 1e9, 4) for x in gd], gd=[round(float(x['tau_g_y_s']) * 1e12, 1) for x in gd])
    else: missing.append((run, 'tau_g'))
    return out

def hf(folder, name):
    D = A + f'hfss/results/{folder}/'
    f, s, z0 = read_touchstone(D + name + '.s1p'); s = s[:, 0, 0]
    m = (f >= 7.5e9) & (f <= 8.5e9); f = f[m]; s = s[m]
    z = 50 * (1 + s) / (1 - s)
    ap = list(csv.DictReader(open(D + 'antenna_params.csv')))
    j = json.load(open(D + 'element_patterns_gd.json'))
    grb = []
    for fg in j['freqs_ghz']:
        c = j['per_freq'][f'{fg:g}']['xz']; grb.append(round(c['realized_gain_dbi'][c['theta_deg'].index(0.0)], 3))
    return {"f": r2(f / 1e9, 4), "db": r2(20 * np.log10(abs(s)), 4), "zr": r2(z.real, 2), "zi": r2(z.imag, 2),
            "ff_f": j['freqs_ghz'], "eta": [round(float(x['RadiationEfficiency []']), 4) for x in ap], "grb": grb,
            "gd_f": j['freqs_ghz'], "gd": j['group_delay']['broadside']['tau_ps']}

# (run, etiqueta, grupo-de-color, tipo)  tipo: base | fine | hfss
def V(run, lab, grp, kind='base', change=None):
    return dict(run=run, lab=lab, grp=grp, kind=kind, change=change)
LINES_DEF = [
 ("p01", "P01 · parche simple", [
   V("P01_MS1_OPENEMS_025", "P01_MS1 (025)", "MS1"), V("P01_MS1_FINE_OPENEMS_026", "P01_MS1 (026)", "MS1", "fine"),
   V("P01_MS2_OPENEMS_027", "P01_MS2 (027)", "MS2"), V("P01_MS2_FINE_OPENEMS_028", "P01_MS2 (028)", "MS2", "fine", "P01_MS2_OPENEMS_027: solo malla (fina)"),
   V("HFSS:results_P01_MS2/P01_MS2|P01_MS2", "P01_MS2 HFSS", "MS2", "hfss", "Mismo diseño P01_MS2 simulado en HFSS (elemento aislado, puerto lumped, criterio ΔS 0,02): EM_SIMULATED"),
   V("P01_IN1_OPENEMS_030", "P01_IN1 inset (030)", "IN1")]),
 ("us3", "US3 · U-slot sin parásito", [
   V("US3_MS1_OPENEMS_021", "US3_MS1 (021)", "MS1"), V("US3_MS2_OPENEMS_022", "US3_MS2 (022)", "MS2"),
   V("US3_MS3_OPENEMS_023", "US3_MS3 (023)", "MS3"), V("US3_MS3_FINE_OPENEMS_024", "US3_MS3 (024)", "MS3", "fine"),
   V("US3_MS4_OPENEMS_029", "US3_MS4 (029)", "MS4")]),
 ("ps4", "U-slot + parásito · rama PS4", [
   V("US3_PS1_OPENEMS_032", "US3_PS1 (032)", "PS1"), V("US3_PS4_OPENEMS_036", "US3_PS4 (036)", "PS4"),
   V("US3_PS4_1_OPENEMS_040", "PS4_1 · Wp 7 (040)", "PS4_1"), V("US3_PS4_2_OPENEMS_042", "PS4_2 · Wp 10 (042)", "PS4_2"),
   V("US3_PS4_3_OPENEMS_043", "PS4_3 · Wp 9 (043)", "PS4_3"), V("US3_PS4_4_OPENEMS_044", "PS4_4 · Wp 8 (044)", "PS4_4"),
   V("US3_PS4_2_1_OPENEMS_045", "PS4_2_1 (045)", "PS4_2_1"), V("US3_PS4_2_1_FINE_OPENEMS_047", "PS4_2_1 (047)", "PS4_2_1", "fine"),
   V("HFSS:results_US3_PS4_2_1/US3_PS4_2_1|US3_PS4_2_1", "PS4_2_1 HFSS", "PS4_2_1", "hfss", "Mismo diseño US3_PS4_2_1 simulado en HFSS (elemento aislado)")]),
 ("ps6", "U-slot + parásito · rama PS6", [
   V("US3_PS5_OPENEMS_037", "US3_PS5 (037)", "PS5"), V("US3_PS6_OPENEMS_038", "US3_PS6 (038)", "PS6"),
   V("US3_PS6_FINE_OPENEMS_039", "US3_PS6 (039)", "PS6", "fine"),
   V("HFSS:results_US3_PS6/US3_PS6|US3_PS6", "US3_PS6 HFSS", "PS6", "hfss", "Mismo diseño US3_PS6 simulado en HFSS (elemento aislado)"),
   V("US3_PS6_1_OPENEMS_046", "US3_PS6_1 (046)", "PS6_1"), V("US3_PS6_2_OPENEMS_048", "US3_PS6_2 (048)", "PS6_2"),
   V("US3_PS6_3_OPENEMS_049", "US3_PS6_3 (049)", "PS6_3"), V("US3_PS6_4_OPENEMS_050", "US3_PS6_4 (050)", "PS6_4"),
   V("US3_PS6_4_FINE_OPENEMS_051", "US3_PS6_4 (051)", "PS6_4", "fine", "US3_PS6_4_OPENEMS_050: same geometry, fine mesh (two-mesh check)"),
   V("HFSS:results_US3_PS6_4/US3_PS6_4|US3_PS6_4", "US3_PS6_4 HFSS", "PS6_4", "hfss", "Mismo diseño US3_PS6_4 simulado en HFSS (elemento aislado)")]),
 ("ini", "Exploración inicial P02/P03", [
   V("P02_MS1_OPENEMS_006", "P02_MS1 (006)", "P02"), V("P03_MS2_OPENEMS_007", "P03_MS2 (007)", "P03a"),
   V("P03_MS3_OPENEMS_008", "P03_MS3 (008)", "P03b"), V("P03_MS4_OPENEMS_009", "P03_MS4 (009)", "P03c"),
   V("P03_MS5_OPENEMS_010", "P03_MS5 (010)", "P03d")]),
]
LINES = {"order": [], "lines": {}}
for key, title, vs in LINES_DEF:
    out = []
    for v in vs:
        if v['run'].startswith('HFSS:'):
            fo, nm = v['run'][5:].split('|'); d = hf(fo + '/' + nm if False else fo, nm) if False else hf(fo.rsplit('/', 1)[0] + '/' + fo.rsplit('/', 1)[1], nm)
            mesh = 'HFSS'; change = v['change']
        else:
            d = oe(v['run']); c = CS.get(v['run'], {})
            mesh = c.get('mesh', 'base'); mesh = {'base': 'base', 'fine': 'fina'}.get(mesh.split(' ')[0], mesh)
            change = v['change'] or c.get('change_vs') or '(sin descripción en campaign_state.json)'
        out.append(dict(id=v['run'], lab=v['lab'], grp=v['grp'], kind=v['kind'], mesh=mesh, change=change, **d))
    LINES["order"].append(key); LINES["lines"][key] = {"title": title, "v": out}
s = "const LINES=" + json.dumps(LINES, separators=(',', ':')) + ";\n"
open(OUT + 'lines_data.js', 'w').write(s)
print(len(s), 'bytes; missing:', missing)
