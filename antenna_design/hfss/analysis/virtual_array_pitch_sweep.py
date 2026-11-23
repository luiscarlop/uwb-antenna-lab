"""Pitch sweep of the 1x4 MIMO virtual array (TFG RF_CONFIGS, off ports on 50 ohm) in the array plane (xz).

GUIDE_MODEL, not EM: identical elements with the owner's HFSS element pattern (GainTotal magnitude,
no phase, isolated 26 x 26 mm board), NO mutual coupling. Coupling falls with pitch and is the part this
model cannot see: it needs the HFSS array solves (build/P01_MS2/claude_aedt_array1x4_ch9.py with several PITCHES_MM).

Per pitch d, frequency f and steering angle theta0 (xz plane, uniform weights, coherent sum of the 24
channels, two-way pattern |E_t E_r|):
  hpbw_deg            -3 dB width of the two-way virtual beam
  pointing_error_deg  peak position - theta0 (the element pattern, counted twice, pulls toward broadside)
  max_sidelobe_db     highest secondary maximum in -90..90 deg relative to the peak (two-way)
  grating_lobe        analytic: |sin(theta0) - lambda/d| <= 1 (a second full main lobe in visible space)
Element pattern: xz cut of the HFSS file, interpolated linearly in dB to 0.25 deg (5 deg source grid).

Usage: python antenna_design/hfss/analysis/virtual_array_pitch_sweep.py [--element P01_MS1] --out antenna_design/hfss/results/results_P01_MS1/virtual_array_pitch_sweep.json
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from virtual_array_pattern import C0, default_sequence

HERE = Path(__file__).resolve().parent   # antenna_design/hfss/analysis
RESULTS = HERE.parent / "results"
COLS = {"7.9872": 2, "7.7376": 3, "8.2368": 4}
PATCH_W_MM = 11.421266


def element_xz(elem, col):
    r = np.array([[float(x) for x in row] for row in list(csv.reader(open(RESULTS / f"results_{elem}" / f"Gain {elem} 3D 3freq.csv")))[1:]])
    ph, th, g = r[:, 0], r[:, 1], r[:, col]
    t = np.r_[-th[ph == 180][::-1], th[ph == 0][1:]]
    G = np.r_[g[ph == 180][::-1], g[ph == 0][1:]]
    o = np.argsort(t)
    return t[o], G[o]


def beam(theta_deg, g_el, d_m, f_hz, theta0_deg, seq):
    k = 2 * np.pi * f_hz / C0
    x = (np.arange(4) - 1.5) * d_m
    u = np.sin(np.radians(theta_deg)) - np.sin(np.radians(theta0_deg))
    af = sum(np.exp(1j * k * (x[t] + x[r]) * u) for t, rx in seq for r in rx)
    p = (g_el ** 2) * np.abs(af) ** 2           # two-way: |E_t E_r|^2 ~ G^2 for identical elements
    return 10 * np.log10(p / p.max())


def lobe_metrics(t, db, theta0):
    fw = (t >= -90) & (t <= 90)
    t, db = t[fw], db[fw]
    k = int(np.argmax(db))
    lo = hi = k
    while lo > 0 and db[lo - 1] >= db[k] - 3:
        lo -= 1
    while hi < len(db) - 1 and db[hi + 1] >= db[k] - 3:
        hi += 1
    l, h = lo, hi
    while l > 0 and db[l - 1] < db[l]:
        l -= 1
    while h < len(db) - 1 and db[h + 1] < db[h]:
        h += 1
    peaks = [i for i in range(1, len(db) - 1) if (i < l or i > h) and db[i] >= db[i - 1] and db[i] >= db[i + 1]]
    for edge in (0, len(db) - 1):  # rising toward +-90 deg counts as a lobe edge
        if edge < l or edge > h:
            peaks.append(edge)
    return {"hpbw_deg": round(float(t[hi] - t[lo]), 2), "pointing_error_deg": round(float(t[k] - theta0), 2),
            "max_sidelobe_db": round(float(max(db[i] for i in peaks)), 2) if peaks else None}


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("--element", default="P01_MS1", choices=["P01_MS1", "US3_MS3"])
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    seq = default_sequence(4)
    t = np.arange(-90, 90.001, 0.25)
    pitches = np.round(np.arange(12.0, 25.01, 0.5), 2).tolist() + [13.5, round(C0 / 8.2368e9 / 2 * 1e3, 3), round(C0 / 7.9872e9 / 2 * 1e3, 3)]
    pitches = sorted(set(pitches))
    steers = [0, 15, 30, 45, 60]
    rows = []
    for d in pitches:
        row = {"pitch_mm": d, "gap_between_patches_mm": round(d - PATCH_W_MM, 3), "freq": {}}
        for fs, col in COLS.items():
            te, ge = element_xz(a.element, col)
            g = 10 ** (np.interp(t, te, 10 * np.log10(ge)) / 10)
            f = float(fs) * 1e9
            lam = C0 / f
            row["freq"][fs] = {"d_over_lambda": round(d * 1e-3 / lam, 4),
                               "max_steer_without_grating_deg": round(float(np.degrees(np.arcsin(min(1.0, lam / (d * 1e-3) - 1)))) if lam / (d * 1e-3) > 1 else 0.0, 1),
                               "steer": {str(s): {**lobe_metrics(t, beam(t, g, d * 1e-3, f, s, seq), s),
                                                  "grating_lobe": bool(abs(np.sin(np.radians(s)) - lam / (d * 1e-3)) <= 1)}
                                         for s in steers}}
        rows.append(row)
    out = {"evidence": "GUIDE_MODEL (not EM): HFSS element GainTotal magnitude, identical elements, no coupling",
           "element_pattern": f"hfss/results/results_{a.element}/Gain {a.element} 3D 3freq.csv (xz cut, 5 deg, interpolated)",
           "sequence": "TFG RF_CONFIGS (12 configs, 24 channels), off ports 50 ohm", "rows": rows}
    a.out.write_text(json.dumps(out, indent=2) + "\n")
    hdr = f"{'d mm':>7} {'gap':>5} {'d/lam':>6} {'maxscan':>7} | " + " | ".join(f"th0={s:>2}: bw err sll" for s in steers)
    print(hdr)
    for r in rows:
        q = r["freq"]["7.9872"]
        cells = " | ".join(f"{q['steer'][str(s)]['hpbw_deg']:5.1f} {q['steer'][str(s)]['pointing_error_deg']:+5.1f} "
                           f"{q['steer'][str(s)]['max_sidelobe_db'] if q['steer'][str(s)]['max_sidelobe_db'] is not None else 0:6.1f}"
                           for s in steers)
        print(f"{r['pitch_mm']:7.2f} {r['gap_between_patches_mm']:5.2f} {q['d_over_lambda']:6.3f} {q['max_steer_without_grating_deg']:7.1f} | {cells}")


if __name__ == "__main__":
    main()
