"""Beam direction vs frequency from the owner's HFSS 3D gain exports (2026-11-13).

Input: antenna_design/hfss/results/results_<D>/'Gain <D> 3D 3freq.csv' (owner upload,
commit 6648401, moved there from the repository root): Phi, Theta every
5 deg and three unlabelled columns GainTotal, GainTotal_1, GainTotal_2.
Column-frequency mapping (confirmed by the owner 2026-11-13): GainTotal = 7.9872 GHz,
GainTotal_1 = 7.7376 GHz, GainTotal_2 = 8.2368 GHz. GainTotal is gain (not realized), linear.
Peak angle: 3-point parabolic fit in dB on the 5 deg grid (about +-1 deg).
E-plane = yz (phi 90/270, positive theta toward +y); H-plane = xz (phi 0/180).
Output: antenna_design/hfss/results/results_<D>/hfss_beam_squint.json, one file per design (refuses to overwrite).
"""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]   # repository root (this file lives in antenna_design/hfss/analysis/)
RESULTS = Path(__file__).resolve().parents[1] / "results"
DESIGNS = ("P01_MS1", "US3_MS3")
MAPPING = "GainTotal 7.9872, GainTotal_1 7.7376, GainTotal_2 8.2368 GHz (owner-confirmed)"


def out_path(d):
    return RESULTS / f"results_{d}" / "hfss_beam_squint.json"
COLS = {"GainTotal": 7.9872, "GainTotal_1": 7.7376, "GainTotal_2": 8.2368}


def cut(r, j, p_pos, p_neg):
    ph, th, g = r[:, 0], r[:, 1], r[:, j]
    t = np.r_[-th[ph == p_neg][::-1], th[ph == p_pos][1:]]
    G = np.r_[g[ph == p_neg][::-1], g[ph == p_pos][1:]]
    o = np.argsort(t)
    return t[o], G[o]


def peak(t, G):
    k = int(np.argmax(G))
    y0, y1, y2 = 10 * np.log10(G[k - 1:k + 2])
    d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    return float(t[k] + d * (t[1] - t[0])), float(y1 - 0.25 * (y0 - y2) * d)


def half_power(t, G):
    k = int(np.argmax(G))
    h = G[k] / 2
    i = k
    while i > 0 and G[i] >= h:
        i -= 1
    j = k
    while j < len(G) - 1 and G[j] >= h:
        j += 1
    return float(np.interp(h, [G[i], G[i + 1]], [t[i], t[i + 1]])), float(np.interp(h, [G[j], G[j - 1]], [t[j], t[j - 1]]))


def main():
    for d in DESIGNS:
        if out_path(d).exists():
            raise SystemExit(f"refusing to overwrite {out_path(d)}")
    for d in DESIGNS:
        out = {"column_frequency_mapping": MAPPING, "designs": {}}
        rows = list(csv.reader(open(RESULTS / f"results_{d}" / f"Gain {d} 3D 3freq.csv")))
        assert rows[0][2:] == list(COLS)
        r = np.array([[float(x) for x in row] for row in rows[1:]])
        per = []
        for j, name in enumerate(COLS, start=2):
            tE, GE = cut(r, j, 90, 270)
            tH, GH = cut(r, j, 0, 180)
            pE, vE = peak(tE, GE)
            pH, _ = peak(tH, GH)
            per.append({"frequency_ghz": COLS[name], "column": name,
                        "broadside_gain_dbi": float(10 * np.log10(r[r[:, 1] == 0][0, j])),
                        "e_plane_peak_deg": pE, "e_plane_peak_gain_dbi": vE,
                        "e_plane_minus3db_deg": half_power(tE, GE),
                        "h_plane_peak_deg": pH, "h_plane_minus3db_deg": half_power(tH, GH)})
        per.sort(key=lambda x: x["frequency_ghz"])
        out["designs"][d] = {"per_frequency": per,
                             "e_plane_squint_deg_over_channel": per[-1]["e_plane_peak_deg"] - per[0]["e_plane_peak_deg"],
                             "h_plane_squint_deg_over_channel": per[-1]["h_plane_peak_deg"] - per[0]["h_plane_peak_deg"]}
        out_path(d).write_text(json.dumps(out, indent=2) + "\n")
        print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
