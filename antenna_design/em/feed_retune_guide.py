"""Guide model (NOT an EM result) for retuning the quarter-wave microstrip feed.

From a finished openEMS run of a microstrip_edge_qw variant with a lumped port at
the line start, it removes the 50 ohm line and the transformer analytically
(ideal lossless TEM lines, Hammerstad-Jensen Z0 + Getsinger dispersion; junction
step and open-end effects ignored) to recover Z_patch(f) at the radiating edge,
then re-applies a transformer of other width/length and reports channel S11.
Use it only to choose the next single-variable FDTD; confirm with openEMS/HFSS.

Validation (round 27, validator): on P01_MS2 (transformer 7.1 mm) it predicted
-9.18 dB worst / 7.78-8.43 GHz at -10 dB; openEMS gave -10.42 dB / 7.724-8.306 GHz
(mean in-channel error 2.9 dB, up to 5.9 dB; upper-edge trend wrong). The
de-embedded Z_patch differs by ~20 ohm reactive between runs 025 and 027: the
junction step (3.92 -> w mm), open-end and losses are not modelled. Qualitative
guide only; do not use it to extrapolate a width (Z0) change. Re-applied 50 ohm
line length is kept at the source variant's value (harmless for |S11|, not for phase).

Usage (from antenna_design/):
  python em/feed_retune_guide.py em/P01_MS1_FINE_OPENEMS_026 --variant variants/P01_MS1.json \
      --out <new.json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from port_postprocess import getsinger_eeff, hammerstad_jensen

C0 = 299_792_458.0
BAND = (7.7376e9, 8.2368e9)


def line(z_load, z0, beta, length_m, toward_load=False):
    t = np.tan(beta * length_m)
    if toward_load:  # impedance seen at the far end, given the input impedance
        return z0 * (z_load - 1j * z0 * t) / (z0 - 1j * z_load * t)
    return z0 * (z_load + 1j * z0 * t) / (z0 + 1j * z_load * t)


def section(f, w_mm, h_mm, er):
    _, z0 = hammerstad_jensen(w_mm, h_mm, er)
    beta = 2 * np.pi * f * np.sqrt(getsinger_eeff(f, w_mm, h_mm, er)) / C0
    return z0, beta


def channel_metrics(f, s):
    db = 20 * np.log10(np.abs(s))
    b = (f >= BAND[0]) & (f <= BAND[1])
    m10 = db <= -10
    i = int(np.argmin(np.where(b, db, 9)))
    lo = hi = i
    while lo > 0 and m10[lo - 1]:
        lo -= 1
    while hi < len(f) - 1 and m10[hi + 1]:
        hi += 1
    return {"worst_db": float(db[b].max()), "best_db": float(db[b].min()),
            "minus10_band_ghz": [float(f[lo] / 1e9), float(f[hi] / 1e9)] if m10[i] else None,
            "minus10_width_mhz": float((f[hi] - f[lo]) / 1e6) if m10[i] else 0.0}


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("run", type=Path)
    cli.add_argument("--variant", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    if args.out.exists():
        raise SystemExit("refusing to overwrite " + str(args.out))
    v = json.loads(args.variant.read_text())
    sub, fd = v["substrate"], v["feed"]
    er, h = sub["eps_r"], sub["h_mm"]
    w_line, w_tr, l_tr = fd["line_width_mm"], fd.get("transformer_width_mm", v.get("transformer_width_mm")), fd.get("transformer_length_mm", v.get("transformer_length_mm"))
    l_line = abs(fd["line_end_y_mm"] - fd["line_start_y_mm"])
    d = np.loadtxt(args.run / "s11_wideband.csv", delimiter=",", skiprows=1)
    d = d[(d[:, 0] >= 7.3e9) & (d[:, 0] <= 8.7e9)]
    f, z_in = d[:, 0], d[:, 3] + 1j * d[:, 4]
    zl, bl = section(f, w_line, h, er)
    zt, bt = section(f, w_tr, h, er)
    z_patch = line(line(z_in, zl, bl, l_line * 1e-3, True), zt, bt, l_tr * 1e-3, True)

    def s11(w, l):
        z2, b2 = section(f, w, h, er)
        z = line(line(z_patch, z2, b2, l * 1e-3), zl, bl, l_line * 1e-3)
        return (z - 50) / (z + 50)

    base = channel_metrics(f, s11(w_tr, l_tr))
    ref = channel_metrics(f, (z_in - 50) / (z_in + 50))
    grid = []
    for w in np.round(np.arange(0.40, 1.61, 0.05), 3):
        for l in np.round(np.arange(5.0, 8.01, 0.1), 3):
            m = channel_metrics(f, s11(w, l))
            grid.append({"tr_w_mm": float(w), "tr_l_mm": float(l), "z0_ohm": section(np.array([8e9]), w, h, er)[0], **m})
    best_worst = min(grid, key=lambda g: g["worst_db"])
    only_w = min((g for g in grid if abs(g["tr_l_mm"] - l_tr) < 1e-9), key=lambda g: g["worst_db"])
    only_l = min((g for g in grid if abs(g["tr_w_mm"] - w_tr) < 1e-9), key=lambda g: g["worst_db"])
    out = {"run": str(args.run), "variant": str(args.variant), "evidence": "GUIDE_MODEL (not EM)",
           "model": "ideal lossless TEM lines, Hammerstad-Jensen Z0 + Getsinger eeff; junction/open-end effects ignored",
           "reproduces_run_channel_worst_db": [ref["worst_db"], base["worst_db"]],
           "current": {"tr_w_mm": w_tr, "tr_l_mm": l_tr, **base},
           "best_single_variable_tr_w": only_w, "best_single_variable_tr_l": only_l,
           "best_two_variables": best_worst, "grid_points": len(grid)}
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("reproduces_run_channel_worst_db", "current", "best_single_variable_tr_w",
                                          "best_single_variable_tr_l", "best_two_variables")}, indent=1))


if __name__ == "__main__":
    main()
