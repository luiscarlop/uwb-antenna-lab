"""Radiation patterns (3D and xz/yz cuts) and radiated group delay of an HFSS element export.

Input : <dir>/ff_P1.csv (claude_aedt_export_element_ch9.py: long format with a Freq column; re/im rETheta, rEPhi
        with 1 W incident on P1) and, as a cross-check, <dir>/antenna_params.csv (PeakRealizedGain, linear).
Output: JSON with, per frequency, realized gain on the full sphere (dBi, 5 deg grid), the xz (phi 0/180) and yz
        (phi 90/270) cuts of the realized gain and of the co-polar Ludwig-3 y component, and the radiated group
        delay tau_g = -d(arg E_co)/d(omega) of the co-polar far field (broadside and +-30 deg in each plane).
Notes : realized gain = 4 pi U / P_inc, U = |rE|^2 / (2 eta0), P_inc = 1 W (Edit Sources 1 W on P1).
        The phase of rE is referred to the HFSS origin and to the port incident wave, so tau_g includes the feed
        line, the transformer and the antenna; its ripple across the channel is what matters, not its absolute
        value. Group delay from 11 points (49.92 MHz step): central differences inside, one-sided at the edges.
        Evidence: HFSS_VALIDATED only if the adaptive solution converged (see convergence.conv).
Usage : python antenna_design/hfss/analysis/element_hfss_patterns.py <dir> --out <json>
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from virtual_array_pattern import co_pol_y, read_ff_csv

ETA0 = 376.730313668


def frequencies(path):
    with open(path, newline="") as fh:
        rows = csv.reader(fh)
        head = [h.lower() for h in next(rows)]
        jf = next(i for i, h in enumerate(head) if h.startswith('"freq') or h.startswith("freq"))
        return sorted({round(float(r[jf]), 6) for r in rows if r})


def cut(theta, phi, val, pa, pb):
    ja, jb = int(np.argmin(abs(phi - pa))), int(np.argmin(abs(phi - pb)))
    t = np.r_[-theta[::-1][:-1], theta]
    v = np.r_[val[::-1, jb][:-1], val[:, ja]]
    return t, v


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("dir", type=Path)
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    ff = a.dir / "ff_P1.csv"
    freqs = frequencies(ff)
    out = {"source_dir": str(a.dir), "freqs_ghz": freqs, "per_freq": {}, "notes": __doc__.split("Notes : ")[1].split("Usage")[0].strip()}
    co_phase = {}
    check = {}
    pk = {}
    ap = a.dir / "antenna_params.csv"
    if ap.is_file():
        for r in csv.DictReader(open(ap, newline="")):
            pk[round(float(r["Freq [GHz]"]), 6)] = 10 * np.log10(float(r["PeakRealizedGain []"]))
    for fg in freqs:
        th, ph, F = read_ff_csv(ff, fg)
        T, P = np.meshgrid(np.radians(th), np.radians(ph), indexing="ij")
        U = (abs(F[0]) ** 2 + abs(F[1]) ** 2) / (2 * ETA0)
        g = 10 * np.log10(np.maximum(4 * np.pi * U, 1e-12))
        co = co_pol_y(F[0], F[1], P)
        gco = 10 * np.log10(np.maximum(4 * np.pi * abs(co) ** 2 / (2 * ETA0), 1e-12))
        rec = {"theta_deg": th.tolist(), "phi_deg": ph.tolist(), "realized_gain_dbi": np.round(g, 2).tolist(),
               "peak_dbi": round(float(g.max()), 2),
               "peak_theta_phi_deg": [float(th[np.unravel_index(g.argmax(), g.shape)[0]]), float(ph[np.unravel_index(g.argmax(), g.shape)[1]])]}
        for name, (pa, pb) in {"xz": (0, 180), "yz": (90, 270)}.items():
            t, v = cut(th, ph, g, pa, pb)
            _, vc = cut(th, ph, gco, pa, pb)
            rec[name] = {"theta_deg": t.tolist(), "realized_gain_dbi": np.round(v, 2).tolist(), "copol_y_dbi": np.round(vc, 2).tolist()}
            tc, cc = cut(th, ph, co, pa, pb)
            co_phase[(fg, name)] = (tc, cc)
        out["per_freq"][f"{fg:g}"] = rec
        if fg in pk:
            check[f"{fg:g}"] = {"peak_from_ff_dbi": rec["peak_dbi"], "PeakRealizedGain_aedt_dbi": round(float(pk[fg]), 2)}
    w = 2 * np.pi * np.array(freqs) * 1e9
    gd = {}
    for name in ("xz", "yz"):
        for ang in (0.0, -30.0, 30.0):
            ph_list = []
            for fg in freqs:
                tc, cc = co_phase[(fg, name)]
                ph_list.append(np.angle(cc[int(np.argmin(abs(tc - ang)))]))
            phs = np.unwrap(np.array(ph_list))
            tau = -np.gradient(phs, w) * 1e12
            key = "broadside" if ang == 0 else f"{name}_{ang:+g}deg"
            if ang == 0 and "broadside" in gd:
                continue
            gd[key] = {"tau_ps": np.round(tau, 2).tolist(), "ripple_pp_ps": round(float(tau.max() - tau.min()), 2),
                       "phase_steps_rad": np.round(np.diff(phs), 3).tolist()}
    out["group_delay"] = {"freqs_ghz": freqs, **gd}
    out["peak_check"] = check
    a.out.write_text(json.dumps(out) + "\n")
    print(json.dumps({"peak_check": check, "group_delay": {k: (v["ripple_pp_ps"], v["tau_ps"]) for k, v in gd.items()}}, indent=1))


if __name__ == "__main__":
    main()
