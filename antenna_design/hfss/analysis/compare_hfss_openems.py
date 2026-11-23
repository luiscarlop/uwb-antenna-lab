"""Compare HFSS exports (owner, 2026-11-13) with the openEMS runs of P01_MS1 and US3_MS3.

Inputs (read only):
  antenna_design/hfss/results/results_<D>/Re_Im <D>.csv        HFSS S(P1,P1) re/im, 7.5-8.5 GHz, 1 MHz
  antenna_design/hfss/results/results_<D>/S Parameter <D>.csv  HFSS dB(S(P1,P1)) (consistency check)
  antenna_design/hfss/results/results_<D>/Gain <D>.csv         HFSS GainTotal at 7.9872 GHz, theta/phi every 5 deg
                                          (column without units; treated as LINEAR gain)
  antenna_design/em/<RUN>/s11_complex.csv openEMS S11 at the same reference plane
                                          (50 ohm lumped port at the line start, board edge)
Output: antenna_design/hfss/results/results_<D>/hfss_vs_openems.json, one file per design (refuses to overwrite).
Usage (repository root): python antenna_design/hfss/analysis/compare_hfss_openems.py
"""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]   # repository root (this file lives in antenna_design/hfss/analysis/)
RESULTS = Path(__file__).resolve().parents[1] / "results"
NOTE = ("HFSS single run per design (owner); adaptive convergence data not provided. "
        "openEMS EM_SIMULATED. Same reference plane (lumped port at line start).")


def res(d):
    return RESULTS / f"results_{d}"


def out_path(d):
    return res(d) / "hfss_vs_openems.json"
BAND = (7.7376e9, 8.2368e9)
RUNS = {"P01_MS1": ["P01_MS1_OPENEMS_025", "P01_MS1_FINE_OPENEMS_026"],
        "US3_MS3": ["US3_MS3_OPENEMS_023", "US3_MS3_FINE_OPENEMS_024"]}


def rows(path):
    return np.array([[float(x) for x in r] for r in list(csv.reader(open(path)))[1:]])


def hfss_s11(d):
    a = rows(res(d) / f"Re_Im {d}.csv")
    f, s = a[:, 0] * 1e9, a[:, 2] + 1j * a[:, 1]
    db = rows(res(d) / f"S Parameter {d}.csv")
    assert np.allclose(db[:, 0] * 1e9, f) and np.allclose(20 * np.log10(abs(s)), db[:, 1], atol=1e-6)
    return f, s


def oems_s11(run):
    a = np.loadtxt(ROOT / "antenna_design" / "em" / run / "s11_complex.csv", delimiter=",", skiprows=1)
    return a[:, 0], a[:, 1] + 1j * a[:, 2]


def contiguous_band(f, db, th):
    i = int(np.argmin(np.where((f >= 7.5e9) & (f <= 8.5e9), db, 9)))
    if db[i] > th:
        return None
    lo = hi = i
    while lo > 0 and db[lo - 1] <= th:
        lo -= 1
    while hi < len(f) - 1 and db[hi + 1] <= th:
        hi += 1
    return {"from_ghz": f[lo] / 1e9, "to_ghz": f[hi] / 1e9, "width_mhz": (f[hi] - f[lo]) / 1e6,
            "hits_sweep_edge": bool(lo == 0 or hi == len(f) - 1)}


def metrics(f, s):
    db = 20 * np.log10(abs(s))
    b = (f >= BAND[0] - 1) & (f <= BAND[1] + 1)
    i = int(np.argmin(db))
    return {"channel_samples": int(b.sum()), "channel_first_last_ghz": [f[b][0] / 1e9, f[b][-1] / 1e9],
            "worst_db": float(db[b].max()), "worst_ghz": float(f[b][db[b].argmax()] / 1e9),
            "best_db": float(db[b].min()), "min_db": float(db[i]), "min_ghz": float(f[i] / 1e9),
            "samples_above_minus6db": int((db[b] > -6).sum()), "samples_above_minus10db": int((db[b] > -10).sum()),
            "band_minus6db": contiguous_band(f, db, -6), "band_minus10db": contiguous_band(f, db, -10)}


def pattern(d):
    r = rows(res(d) / f"Gain {d}.csv")
    ph, th, g = r[:, 1], r[:, 2], r[:, 3]
    i = int(np.argmax(g))
    t = np.r_[-th[ph == 270][::-1], th[ph == 90][1:]]
    G = np.r_[g[ph == 270][::-1], g[ph == 90][1:]]
    o = np.argsort(t)
    t, G = t[o], G[o]
    k = int(np.argmax(G))
    half = t[G >= G[k] / 2]
    return {"frequency_ghz": sorted(set(r[:, 0].tolist())), "quantity": "GainTotal (not realized), linear assumed",
            "broadside_dbi": float(10 * np.log10(g[th == 0][0])),
            "max_dbi": float(10 * np.log10(g[i])), "max_theta_deg": float(th[i]), "max_phi_deg": float(ph[i]),
            "yz_plane_peak_deg_positive_toward_plus_y": float(t[k]),
            "yz_plane_minus3db_deg": [float(half.min()), float(half.max())]}


def main():
    for d in RUNS:
        if out_path(d).exists():
            raise SystemExit(f"refusing to overwrite {out_path(d)}")
    for d, runs in RUNS.items():
        out = {"note": NOTE, "designs": {}}
        fh, sh = hfss_s11(d)
        rec = {"hfss": metrics(fh, sh), "hfss_pattern_f0": pattern(d), "openems": {}}
        b = (fh >= BAND[0]) & (fh <= BAND[1])
        for run in runs:
            fo, so = oems_s11(run)
            si = np.interp(fh, fo, so.real) + 1j * np.interp(fh, fo, so.imag)
            rec["openems"][run] = {**metrics(fo, so),
                                   "hfss_minus_openems_abs_dgamma_channel_max": float(abs(sh - si)[b].max()),
                                   "hfss_minus_openems_abs_dgamma_channel_mean": float(abs(sh - si)[b].mean())}
        out["designs"][d] = rec
        out_path(d).write_text(json.dumps(out, indent=2) + "\n")
        print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
