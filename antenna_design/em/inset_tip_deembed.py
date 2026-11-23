"""Guide model (NOT an EM result): impedance at the inset tip of a microstrip_inset_edge run.

Removes the 50 ohm line from the port plane (board edge) to the inset tip analytically (ideal lossless
TEM line, Hammerstad-Jensen Z0 + Getsinger dispersion, the same helpers as feed_retune_guide.py). Inside
the notch the line is flanked by the patch at notch_gap_mm, so it is not a plain microstrip there; that
part (inset_depth_mm long) and the step/open-end effects are NOT modelled. Use only to test a
pre-registered hypothesis about the order of magnitude of Re(Z_tip).

Usage (from antenna_design/):
  python em/inset_tip_deembed.py em/P01_IN1_OPENEMS_030 --variant variants/P01_IN1.json --out <json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from feed_retune_guide import line, section

BAND = (7.7376e9, 8.2368e9)
F0 = 7.9872e9


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("run", type=Path)
    cli.add_argument("--variant", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    v = json.loads(a.variant.read_text())
    fd, sub = v["feed"], v["substrate"]
    ys = [p[1] for p in v["patch_polygon_mm"]]
    tip_y = min(ys) + fd["inset_depth_mm"]
    port_y = -sub["size_mm"][1] / 2
    length_mm = tip_y - port_y
    d = np.loadtxt(a.run / "s11_wideband.csv", delimiter=",", skiprows=1)
    f, zin = d[:, 0], d[:, 3] + 1j * d[:, 4]
    z0, beta = section(f, fd["line_width_mm"], sub["h_mm"], sub["eps_r"])
    ztip = line(zin, z0, beta, length_mm * 1e-3, toward_load=True)
    b = (f >= BAND[0]) & (f <= BAND[1])
    i0 = int(np.argmin(abs(f - F0)))
    pk = int(np.argmax(np.where((f > 6.5e9) & (f < 9.5e9), ztip.real, -1)))
    out = {"run": str(a.run), "evidence": "GUIDE_MODEL (de-embedding of EM_SIMULATED Zin)",
           "line_removed_mm": round(length_mm, 4), "line_z0_ohm_static": float(np.atleast_1d(z0)[0]),
           "tip_y_mm": tip_y, "port_y_mm": port_y,
           "z_tip_at_f0_ohm": [float(ztip[i0].real), float(ztip[i0].imag)],
           "re_z_tip_channel_ohm": [float(ztip[b].real.min()), float(ztip[b].real.max())],
           "re_z_tip_peak": {"ohm": float(ztip[pk].real), "ghz": float(f[pk] / 1e9), "im_ohm": float(ztip[pk].imag)},
           "zin_port_at_f0_ohm": [float(zin[i0].real), float(zin[i0].imag)],
           "caveat": "notch section treated as plain microstrip; steps and open ends ignored"}
    a.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
