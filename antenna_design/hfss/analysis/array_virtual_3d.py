"""3D and 2D patterns and broadside group delay of the physical and MIMO-virtual beams of an HFSS 1xN array.

Input : <dir>/ff_P1.csv ... ff_PN.csv (claude_aedt_export_*: long format with a Freq column; embedded fields, 1 W on
        P_i, the other ports loaded with 50 ohm) and the pitch in mm.
Output: JSON with, per frequency, on the full sphere (5 deg grid):
        - physical beam, uniform 1 W per port, broadside: realized gain 4 pi U / P_inc,total (dBi);
        - virtual beam: coherent sum over the default 1 TX + 2 RX sequence of the two-way co-polar (Ludwig-3 y)
          channels E_t E_r (virtual_array_pattern.virtual_beam), normalised to its peak (dB, no absolute gain);
        - xz (phi 0/180) and yz (phi 90/270) cuts of both, HPBW and sidelobe level of the xz cut;
        and the broadside group delay tau_g = -d(arg)/d(omega) of the physical co-polar beam (one way) and of the
        virtual beam (two way: transmit + receive, so about twice the one-way value).
Notes : the phase is referred to the HFSS origin and to the port incident waves: tau_g includes lines, transformers
        and antennas; its ripple across the channel matters, not its absolute value. Frequencies: those in the CSV
        (5 for ARR1x5_US3_PS4_2_1_dparam, 124.8 MHz step): the group delay is coarse.
Usage : python antenna_design/hfss/analysis/array_virtual_3d.py <dir> --pitch-mm 18.2 --out <json>
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from virtual_array_pattern import C0, co_pol_y, cut_metrics, default_sequence, read_ff_csv, virtual_beam

ETA0 = 376.730313668


SUFFIX_FREQ = {"": 7.9872, "_1": 7.7376, "_2": 8.2368}  # AEDT wide format (manual export), as in array_hfss_analysis.py


def freqs_of(path):
    """Frequencies in the CSV and the column suffix of each (None for the long format with a Freq column)."""
    with open(path, newline="") as fh:
        rows = csv.reader(fh)
        head = [h.lower().strip('"') for h in next(rows)]
        jf = next((i for i, h in enumerate(head) if h.startswith("freq")), None)
        if jf is None:
            return {f: s for s, f in sorted(SUFFIX_FREQ.items(), key=lambda kv: kv[1])}
        return {f: None for f in sorted({round(float(r[jf]), 6) for r in rows if r})}


def cut(theta, phi, val, pa, pb):
    ja, jb = int(np.argmin(abs(phi - pa))), int(np.argmin(abs(phi - pb)))
    return np.r_[-theta[::-1][:-1], theta], np.r_[val[::-1, jb][:-1], val[:, ja]]


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("dir", type=Path)
    cli.add_argument("--pitch-mm", type=float, required=True)
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    files = sorted(a.dir.glob("ff_P*.csv"), key=lambda p: int(p.stem[4:]))
    n = len(files)
    x = (np.arange(n) - (n - 1) / 2) * a.pitch_mm * 1e-3
    seq = default_sequence(n)
    suf = freqs_of(files[0])
    fl = list(suf)
    out = {"source_dir": str(a.dir), "pitch_mm": a.pitch_mm, "n_ports": n, "freqs_ghz": fl,
           "virtual_sequence": f"default 1 TX + 2 RX, {len(seq)} acquisitions", "per_freq": {}}
    ph_phys, ph_virt = [], []
    for fg in fl:
        fields = [read_ff_csv(f, fg, suf[fg]) for f in files]
        th, ph = fields[0][0], fields[0][1]
        F = np.array([q[2] for q in fields])
        T, P = np.meshgrid(np.radians(th), np.radians(ph), indexing="ij")
        k = 2 * np.pi * fg * 1e9 / C0
        E = F.sum(axis=0)
        U = (abs(E[0]) ** 2 + abs(E[1]) ** 2) / (2 * ETA0)
        gphys = 10 * np.log10(np.maximum(4 * np.pi * U / n, 1e-12))
        Fco = co_pol_y(F[:, 0], F[:, 1], P[None])
        B = virtual_beam(Fco, x, k, seq, 0.0)
        pv = abs(B) ** 2
        gvirt = 10 * np.log10(np.maximum(pv / pv.max(), 1e-12))
        i0 = int(np.argmin(abs(th)))
        ph_phys.append(np.angle(co_pol_y(E[0], E[1], P)[i0, 0]))
        ph_virt.append(np.angle(B[i0, 0]))
        rec = {"theta_deg": th.tolist(), "phi_deg": ph.tolist(),
               "physical_dbi": np.round(gphys, 2).tolist(), "virtual_db": np.round(gvirt, 2).tolist(),
               "physical_peak_dbi": round(float(gphys.max()), 2)}
        for name, (pa, pb) in {"xz": (0, 180), "yz": (90, 270)}.items():
            t, vp = cut(th, ph, gphys, pa, pb)
            _, vv = cut(th, ph, gvirt, pa, pb)
            fw = (t >= -90) & (t <= 90)
            rec[name] = {"theta_deg": t.tolist(), "physical_dbi": np.round(vp, 2).tolist(), "virtual_db": np.round(vv, 2).tolist(),
                         "physical_metrics": cut_metrics(t[fw], vp[fw] - vp[fw].max()),
                         "virtual_metrics": cut_metrics(t[fw], vv[fw] - vv[fw].max())}
        out["per_freq"][f"{fg:g}"] = rec
    w = 2 * np.pi * np.array(fl) * 1e9
    gd = {}
    for name, phs in (("physical_one_way", ph_phys), ("virtual_two_way", ph_virt)):
        u = np.unwrap(np.array(phs))
        tau = -np.gradient(u, w) * 1e12
        gd[name] = {"tau_ps": np.round(tau, 1).tolist(), "ripple_pp_ps": round(float(tau.max() - tau.min()), 1),
                    "phase_steps_rad": np.round(np.diff(u), 3).tolist()}
    out["group_delay_broadside"] = gd
    a.out.write_text(json.dumps(out) + "\n")
    print(json.dumps({"gd": gd, "cuts": {f: {p: (r[p]["physical_metrics"], r[p]["virtual_metrics"]) for p in ("xz", "yz")}
                                          for f, r in out["per_freq"].items()}}, indent=1)[:6000])


if __name__ == "__main__":
    main()
