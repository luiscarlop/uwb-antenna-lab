"""Fit a guide circuit to a simulated probe-fed patch input impedance.

Model: Zin(f) = R0 + j*2*pi*f*Ls + R / (1 + j*Q*(f/fr - fr/f))
(series probe/port inductance Ls and loss R0, parallel RLC patch resonance).
(fr, Q) by grid search; (R0, Ls, R) by linear least squares. Uses only
numpy. It reads a wideband CSV written by patch_openems.py or
reanalyze_port_dft.py (rows with u_inc_rel_db <= -20 are ignored).

This is a GUIDE MODEL fitted to EM data, not an EM result: what-if numbers
from it (other R, fr, Ls) must be confirmed with a new FDTD before use.

Usage (from antenna_design/):
  python em/fit_patch_circuit.py em/<RUN>/s11_wideband.csv --out <new.json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

BAND = (7.7376e9, 8.2368e9)


def model(f, R0, Ls, R, fr, Q):
    return R0 + 1j * 2 * np.pi * f * Ls + R / (1 + 1j * Q * (f / fr - fr / f))


def fit(f, z, fr_grid, q_grid):
    best = None
    b = np.r_[z.real, z.imag]
    n = len(f)
    for fr in fr_grid:
        for q in q_grid:
            h = 1 / (1 + 1j * q * (f / fr - fr / f))
            a = np.column_stack([np.r_[np.ones(n), np.zeros(n)], np.r_[np.zeros(n), 2 * np.pi * f],
                                 np.r_[h.real, h.imag]])
            x, *_ = np.linalg.lstsq(a, b, rcond=None)
            err = float(np.linalg.norm(a @ x - b))
            if best is None or err < best[0]:
                best = (err, fr, q, x)
    err, fr, q, (r0, ls, r) = best
    return {"fr_hz": float(fr), "Q": float(q), "R_ohm": float(r), "Ls_H": float(ls), "R0_ohm": float(r0),
            "rms_error_ohm": err / np.sqrt(2 * n)}


def worst_in_band_db(p, f):
    z = model(f, p["R0_ohm"], p["Ls_H"], p["R_ohm"], p["fr_hz"], p["Q"])
    return float(20 * np.log10(np.abs((z - 50) / (z + 50)).max()))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("csv", type=Path)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--fmin", type=float, default=7.3e9)
    cli.add_argument("--fmax", type=float, default=8.7e9)
    args = cli.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing to overwrite " + str(args.out))
    d = np.loadtxt(args.csv, delimiter=",", skiprows=1)
    d = d[d[:, 5] > -20.0]
    m = (d[:, 0] > args.fmin) & (d[:, 0] < args.fmax)
    f, z = d[m, 0], d[m, 3] + 1j * d[m, 4]
    p = fit(f, z, np.arange(f.min() + 0.1e9, f.max() - 0.1e9, 2e6), np.arange(3, 60, 0.25))
    fb = np.linspace(*BAND, 300)
    p["fitted_model_worst_in_band_s11_db"] = worst_in_band_db(p, fb)
    what_if = []
    for ls_scale in (1.0, 0.5, 0.0):
        best = min((worst_in_band_db({**p, "R_ohm": r, "fr_hz": fr, "Ls_H": p["Ls_H"] * ls_scale}, fb), r, fr)
                   for r in range(30, 205, 5) for fr in np.arange(7.3e9, 8.6e9, 0.01e9))
        what_if.append({"Ls_scale": ls_scale, "best_worst_in_band_s11_db": best[0],
                        "R_ohm": best[1], "fr_hz": float(best[2])})
    out = {"source_csv": str(args.csv), "fit_range_hz": [args.fmin, args.fmax], "samples": int(m.sum()),
           "model": "Zin = R0 + j w Ls + R/(1 + jQ(f/fr - fr/f))", "fit": p,
           "what_if_best_over_R_and_fr_same_Q": what_if,
           "evidence": "GUIDE_MODEL fitted to EM_SIMULATED data; what-if values are not EM results"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
