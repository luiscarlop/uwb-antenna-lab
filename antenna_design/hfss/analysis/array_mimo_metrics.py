"""Multiport (MIMO) metrics of a 1 x N linear array from an HFSS Touchstone export (.sNp).

Input : Touchstone v1 file exported from HFSS (Results > Solution Data > Export, or right-click the
        sweep > Export > Touchstone), N ports P1..PN ordered along +x, 50 ohm, formats MA, DB or RI.
Output: JSON with, per frequency and summarised over the channel 7.7376-8.2368 GHz:
  - |Sij| in dB (reflection and mutual coupling);
  - ECC_ij from S-parameters (Blanch et al. 2003, N-port form): assumes LOSSLESS antennas, so with
    eta_rad ~0.7-0.85 it is only indicative; pattern-based ECC is the correct metric;
  - active reflection coefficient of each port for uniform amplitude and progressive phase that
    steers the beam to theta0 in the xz plane: Gamma_n = sum_m S_nm w_m / w_n,
    w_m = exp(-j k x_m sin theta0), x_m = (m - (N-1)/2) * pitch;
  - TARC for the same excitation: sqrt(sum |b|^2 / sum |a|^2), b = S a.
Evidence: whatever the Touchstone is (HFSS_VALIDATED only if it comes from a converged HFSS run).
Usage:
  python antenna_design/hfss/analysis/array_mimo_metrics.py <file.s4p> --pitch-mm 13.5 --out <out.json> [--steer 0 15 30]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

C0 = 299_792_458.0
BAND_HZ = (7.7376e9, 8.2368e9)
UNIT = {"HZ": 1.0, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}


def read_touchstone(path, n_ports=None):
    """Return f (Hz), S (F x N x N) and the reference impedance from a Touchstone v1 file."""
    path = Path(path)
    if n_ports is None:
        n_ports = int(path.suffix.lower().strip(".sp"))
    unit, fmt, z0, nums = "GHZ", "MA", 50.0, []
    for line in path.read_text().splitlines():
        line = line.split("!")[0].strip()
        if not line:
            continue
        if line.startswith("#"):
            tok = line[1:].upper().split()
            for i, t in enumerate(tok):
                if t in UNIT:
                    unit = t
                elif t in ("MA", "DB", "RI"):
                    fmt = t
                elif t == "R":
                    z0 = float(tok[i + 1])
            if "S" not in tok:
                raise ValueError("only S-parameter files are supported")
            continue
        nums.extend(float(x) for x in line.split())
    per = 1 + 2 * n_ports * n_ports
    if len(nums) % per:
        raise ValueError(f"{len(nums)} numbers is not a multiple of {per} (N = {n_ports})")
    a = np.array(nums).reshape(-1, per)
    f = a[:, 0] * UNIT[unit]
    p, q = a[:, 1::2], a[:, 2::2]
    if fmt == "RI":
        s = p + 1j * q
    elif fmt == "MA":
        s = p * np.exp(1j * np.radians(q))
    else:
        s = 10 ** (p / 20) * np.exp(1j * np.radians(q))
    s = s.reshape(-1, n_ports, n_ports)
    if n_ports == 2:  # Touchstone v1 two-port order is S11 S21 S12 S22
        s = s.transpose(0, 2, 1)
    return f, s, z0


def ecc_from_s(s):
    """N-port S-parameter ECC (lossless-antenna assumption). s: F x N x N -> F x N x N."""
    gram = np.einsum("fki,fkj->fij", s.conj(), s)          # sum_k S_ki* S_kj
    d = 1 - np.real(np.einsum("fii->fi", gram))              # 1 - sum_k |S_ki|^2
    den = np.sqrt(np.clip(d[:, :, None] * d[:, None, :], 1e-30, None))
    return np.abs(gram) ** 2 / den ** 2


def steering(f, n, pitch_m, theta0_deg):
    x = (np.arange(n) - (n - 1) / 2) * pitch_m
    k = 2 * np.pi * f / C0
    return np.exp(-1j * k[:, None] * x[None, :] * np.sin(np.radians(theta0_deg)))


def active_gamma(s, w):
    b = np.einsum("fnm,fm->fn", s, w)
    return b / w, np.sqrt((np.abs(b) ** 2).sum(1) / (np.abs(w) ** 2).sum(1))


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-15))


def metrics(f, s, pitch_mm, steer_deg):
    n = s.shape[1]
    b = (f >= BAND_HZ[0] - 1) & (f <= BAND_HZ[1] + 1)
    if not b.any():
        raise ValueError("no samples inside the channel")
    sdb = db(s)
    ecc = ecc_from_s(s)
    out = {"n_ports": n, "pitch_mm": pitch_mm, "channel_samples": int(b.sum()),
           "channel_first_last_ghz": [float(f[b][0] / 1e9), float(f[b][-1] / 1e9)],
           "s_db_channel_worst": {}, "ecc_s_param_channel_max": {}, "active": {}}
    for i in range(n):
        for j in range(n):
            key = f"S{i + 1}{j + 1}"
            out["s_db_channel_worst"][key] = round(float(sdb[b, i, j].max()), 2)
            if j > i:
                out["ecc_s_param_channel_max"][f"{i + 1}{j + 1}"] = float(ecc[b, i, j].max())
    for th in steer_deg:
        g, tarc = active_gamma(s, steering(f, n, pitch_mm * 1e-3, th))
        gdb = db(g)
        out["active"][f"theta0_{th:g}deg"] = {
            "active_s_db_channel_worst_per_port": [round(float(gdb[b, i].max()), 2) for i in range(n)],
            "tarc_db_channel_worst": round(float(db(tarc)[b].max()), 2),
            "all_ports_le_minus10db": bool((gdb[b] <= -10).all()),
            "all_ports_le_minus6db": bool((gdb[b] <= -6).all())}
    out["notes"] = ["ECC from S assumes lossless antennas (indicative only).",
                    "Active S assumes uniform amplitude, progressive phase, all ports 50 ohm; x of port i = (i-(N-1)/2)*pitch.",
                    "Worst values are over the sampled channel grid only."]
    return out


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("touchstone", type=Path)
    cli.add_argument("--pitch-mm", type=float, default=13.5)
    cli.add_argument("--steer", type=float, nargs="*", default=[0.0, 15.0, 30.0])
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite {args.out}")
    f, s, z0 = read_touchstone(args.touchstone)
    if abs(z0 - 50) > 1e-9:
        raise SystemExit(f"reference impedance {z0} ohm, expected 50")
    out = {"source": str(args.touchstone), **metrics(f, s, args.pitch_mm, args.steer)}
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
