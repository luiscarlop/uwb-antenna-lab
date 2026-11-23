"""Re-evaluate an MSL-port run at its measurement plane with a FIXED 50 ohm reference.

Added Claude round 6 after P02_MS1_OPENEMS_006 showed |S11| > 1 with the
port's extracted line impedance/propagation constant. This script does not
use the extracted Z_line or beta: it takes the middle voltage probe
(port_ut_1B) and the mean of the two current probes (port_it_1A/B), computes
the same single-sided DFT as openEMS, and S11 = (U - a)/a with a = (U + 50 I)/2.
Optionally it moves Zin along an ideal lossless 50 ohm line to another plane
for a set of assumed effective permittivities (a sensitivity, NOT a result).

Caveat: the current probes sit on the A/B voltage-probe planes, so their mean
is about half a cell away from probe B; the line is not ideal. Runs no solver
and never overwrites its output.

Usage (from antenna_design/):
  python em/msl_measplane_reanalysis.py em/P02_MS1_OPENEMS_006 --out <new.json> \
      --shift-to-y -1.825 --eeff 3.33 3.5 3.65
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np

C0 = 299_792_458.0
BAND = (7.7376e9, 8.2368e9)


def load(run, name):
    return np.loadtxt(Path(run) / name, comments="%")


def probe_y_m(run, name):
    head = (Path(run) / name).read_text().splitlines()[1]
    return float(re.search(r"\(([^)]*)\)", head).group(1).split(",")[1])


def dft(a, f):
    t = a[:, 0]
    return 2 * (t[1] - t[0]) * np.exp(-2j * np.pi * np.outer(f, t)) @ a[:, 1]


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("run", type=Path)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--fmin", type=float, default=6.98e9)
    cli.add_argument("--fmax", type=float, default=9.0e9)
    cli.add_argument("--step", type=float, default=5e6)
    cli.add_argument("--shift-to-y", type=float, help="plane (mm) to move Zin to along an ideal 50 ohm line")
    cli.add_argument("--eeff", type=float, nargs="*", default=[3.33, 3.5, 3.65])
    args = cli.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing to overwrite " + str(args.out))
    f = np.arange(args.fmin, args.fmax + args.step / 2, args.step)
    u = dft(load(args.run, "port_ut_1B"), f)
    i = 0.5 * (dft(load(args.run, "port_it_1A"), f) + dft(load(args.run, "port_it_1B"), f))
    z = u / i
    s = (z - 50) / (z + 50)
    band = (f >= BAND[0]) & (f <= BAND[1])
    db = 20 * np.log10(np.abs(s))
    y_meas_mm = probe_y_m(args.run, "port_ut_1B") * 1e3
    out = {"run": str(args.run), "method": __doc__.split("\n")[0], "reference_ohm": 50.0,
           "measurement_plane_y_mm": y_meas_mm, "grid_hz": [args.fmin, args.fmax, args.step],
           "max_abs_s11": float(np.abs(s).max()), "passive": bool(np.abs(s).max() <= 1.0),
           "channel_worst_s11_db": float(db[band].max()), "channel_best_s11_db": float(db[band].min()),
           "min_s11_db": float(db.min()), "min_s11_hz": float(f[db.argmin()]),
           "zin_at_f0_meas_plane_ohm": [float(z[np.argmin(abs(f - 7.9872e9))].real), float(z[np.argmin(abs(f - 7.9872e9))].imag)],
           "evidence": "re-analysis of EM_SIMULATED port signals; no new solve"}
    if args.shift_to_y is not None:
        length_m = (args.shift_to_y - y_meas_mm) * 1e-3
        sens = []
        for ee in args.eeff:
            t = np.tan(2 * np.pi * f * np.sqrt(ee) / C0 * length_m)
            zf = 50 * (z - 1j * 50 * t) / (50 - 1j * z * t)
            k = int(np.argmax(zf.real))
            j = int(np.argmin(abs(f - 7.9872e9)))
            sens.append({"eeff_assumed": ee, "re_peak_ohm": float(zf.real[k]), "re_peak_hz": float(f[k]),
                         "x_at_re_peak_ohm": float(zf.imag[k]), "z_at_f0_ohm": [float(zf[j].real), float(zf[j].imag)]})
        out["shifted_to_y_mm"] = args.shift_to_y
        out["shift_model"] = "ideal lossless 50 ohm line, assumed eeff (sensitivity only, not a result)"
        out["shift_sensitivity"] = sens
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
