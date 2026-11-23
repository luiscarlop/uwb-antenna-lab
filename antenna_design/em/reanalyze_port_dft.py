"""Re-evaluate a finished openEMS lumped-port run on a new frequency grid.

Reads the stored time-domain port voltage/current (port_ut_1, port_it_1) of an
existing run directory and computes the same DFT openEMS uses
(2*dt*sum x(t) exp(-j2pi f t)); u_inc = (U + Z0 I)/2, S11 = (U - u_inc)/u_inc,
Zin = U/I. It runs no solver and does not modify the run directory.

Validity: only frequencies where |u_inc| is within --min-inc-db of its peak are
kept (the Gaussian excitation carries little energy elsewhere). The record is
finite; DFT spacing is not physical resolution.

Usage (from antenna_design/):
  python em/reanalyze_port_dft.py em/P01_OPENEMS_001 --out <new.csv> \
      --fmin 6e9 --fmax 10e9 --step 5e6 --check em/P01_OPENEMS_001/s11_complex.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def dft(t, x, f):
    return 2 * (t[1] - t[0]) * np.exp(-2j * np.pi * np.outer(f, t)) @ x


def port_spectra(run, f, z0=50.0):
    u = np.loadtxt(Path(run) / "port_ut_1", comments="%")
    i = np.loadtxt(Path(run) / "port_it_1", comments="%")
    U, I = dft(u[:, 0], u[:, 1], f), dft(i[:, 0], i[:, 1], f)
    inc = 0.5 * (U + z0 * I)
    return U, I, inc, (U - inc) / inc


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("run", type=Path)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--fmin", type=float, default=6e9)
    cli.add_argument("--fmax", type=float, default=10e9)
    cli.add_argument("--step", type=float, default=5e6)
    cli.add_argument("--min-inc-db", type=float, default=-20.0)
    cli.add_argument("--z0", type=float, default=50.0)
    cli.add_argument("--check", type=Path, help="original s11_complex.csv to reproduce")
    args = cli.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing to overwrite " + str(args.out))
    summary = {"run": str(args.run), "z0_ohm": args.z0, "min_inc_db": args.min_inc_db,
               "method": "DFT of stored port_ut_1/port_it_1 (no new solve)"}
    if args.check:
        ref = np.loadtxt(args.check, delimiter=",", skiprows=1)
        _, _, _, s = port_spectra(args.run, ref[:, 0], args.z0)
        summary["reproduction_max_abs_delta_s11"] = float(np.abs(s - (ref[:, 1] + 1j * ref[:, 2])).max())
    f = np.arange(args.fmin, args.fmax + args.step / 2, args.step)
    U, I, inc, s = port_spectra(args.run, f, args.z0)
    inc_db = 20 * np.log10(np.abs(inc) / np.abs(inc).max())
    keep = inc_db > args.min_inc_db
    f, U, I, inc, s, inc_db = f[keep], U[keep], I[keep], inc[keep], s[keep], inc_db[keep]
    z = U / I
    data = np.column_stack([f, s.real, s.imag, z.real, z.imag, inc_db])
    if not np.all(np.isfinite(data)):
        raise SystemExit("Non-finite output")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.out, data, delimiter=",", comments="", fmt="%.12e",
               header="frequency_hz,s11_real,s11_imag,zin_real_ohm,zin_imag_ohm,u_inc_rel_db")
    k = int(np.argmax(z.real))
    m = int(np.argmin(np.abs(s)))
    summary.update({
        "valid_range_hz": [float(f[0]), float(f[-1])], "samples": int(len(f)), "step_hz": args.step,
        "re_zin_peak_ohm": float(z.real[k]), "re_zin_peak_hz": float(f[k]), "im_zin_at_re_peak_ohm": float(z.imag[k]),
        "min_s11_db": float(20 * np.log10(np.abs(s[m]))), "min_s11_hz": float(f[m]),
        "caveat": "Re(Zin) peak used as parallel-resonance indicator of the probe-fed patch; finite record, no far field",
    })
    args.out.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
