"""Two-way pattern of the MIMO VIRTUAL array (1 TX + 2 RX per acquisition) from a 4-port array solve.

Physics (narrow-band, far field, point target, reciprocity):
  * One N-port HFSS solve is enough. HFSS gives the embedded far field F_m(theta, phi) of each port m
    with the other ports on 50 ohm (Edit Sources: 1 W at port m, 0 elsewhere). Any other state of the
    switches is a linear combination of those fields (no new solve per combination):
        a = (I - Gamma S)^-1 e_p,   F_p^state = sum_m a_m F_m
    Gamma = diag(reflection of the load seen by each port): 0 for TX / RX ports (50 ohm transmitter or
    receiver), Gamma_off for ports switched off. Gamma_off = 0 (50 ohm, the article's embedded-pattern
    convention) makes every state identical and the S-matrix unnecessary.
  * Channel (t -> r) of acquisition q: H_q,tr(theta, phi) = F_t^q . F_r^q (co-polar components, Ludwig-3
    referred to y, as in the article; or the full vector dot product with --pol vector). Its phase carries
    k (x_t + x_r) sin(theta) cos(phi): the virtual element sits at x_t + x_r.
  * Virtual beam steered to theta0 in the xz plane: B(theta, phi) = sum_q sum_r w_q,tr H_q,tr with
    w = exp(-j k (x_t + x_r) sin theta0) (uniform amplitude). The sum is COHERENT (complex). Adding
    |H|^2 of every combination gives an average two-way pattern, not a beam.

Inputs: one CSV per port with complex far fields on a theta/phi grid exported from HFSS (Far Fields report,
quantities re(rETheta), im(rETheta), re(rEPhi), im(rEPhi); column names are matched by substring), the
.s4p (only needed when Gamma_off != 0) and the acquisition sequence.

Usage:
  python antenna_design/hfss/analysis/virtual_array_pattern.py --ff P1.csv P2.csv P3.csv P4.csv --freq-ghz 7.9872 \
      --pitch-mm 13.5 --steer 0 --out virtual.json [--s4p array.s4p --gamma-off 0.9+0j] \
      [--sequence "1:2,3 1:2,4 1:3,4 2:1,3 ..."]
Default sequence: every TX t = 1..N with every pair of the other ports as RX (N * C(N-1, 2) acquisitions).
For N = 4 it is, in the same order, RF_CONFIGS of the TFG code (src/main/uwb_cir_walk/config.py, configs 1-12;
pinned by tests/test_hfss_array.py).
Evidence: inherits the evidence of its inputs; with ideal identical elements it is a GUIDE_MODEL.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np

C0 = 299_792_458.0


# ---------------------------------------------------------------- sequence ---
def default_sequence(n, n_rx=2):
    return [(t, rx) for t in range(n) for rx in itertools.combinations([p for p in range(n) if p != t], n_rx)]


def parse_sequence(text):
    """'1:2,3 1:2,4' -> [(0, (1, 2)), (0, (1, 3))] (1-based in the text, 0-based out)."""
    seq = []
    for item in text.split():
        t, rx = item.split(":")
        seq.append((int(t) - 1, tuple(int(r) - 1 for r in rx.split(","))))
    return seq


def virtual_positions(seq, x):
    """Virtual element positions x_t + x_r with their multiplicity in the sequence."""
    pos = {}
    for t, rx in seq:
        for r in rx:
            key = round(x[t] + x[r], 9)
            pos[key] = pos.get(key, 0) + 1
    return dict(sorted(pos.items()))


# ----------------------------------------------------------------- fields ---
def loaded_fields(F, S, gamma):
    """Embedded fields with arbitrary loads. F: N x ... (complex, any trailing shape), S: N x N,
    gamma: N reflection coefficients. Returns N x ... : field of each port when driven with the others loaded."""
    n = S.shape[0]
    A = np.linalg.solve(np.eye(n) - np.diag(gamma) @ S, np.eye(n))  # column p = incident waves for drive at p
    return np.tensordot(A.T, F, axes=(1, 0))


def co_pol_y(eth, eph, phi_rad):
    """Ludwig-3 co-polar component referred to y."""
    return eth * np.sin(phi_rad) + eph * np.cos(phi_rad)


def virtual_beam(F, x, k, seq, theta0_deg=0.0, S=None, gamma_off=0.0):
    """F: N x 2 x T x P complex (E_theta, E_phi) or N x T x P scalar co-pol fields.
    Returns the complex beam (T x P) and the per-acquisition count of channels."""
    n = F.shape[0]
    beam = 0
    for t, rx in seq:
        if gamma_off != 0:
            if S is None:
                raise ValueError("gamma_off != 0 needs the S-matrix")
            g = np.full(n, complex(gamma_off))
            g[[t, *rx]] = 0
            Fq = loaded_fields(F, S, g)
        else:
            Fq = F
        for r in rx:
            h = (Fq[t] * Fq[r]).sum(axis=0) if Fq.ndim == 4 else Fq[t] * Fq[r]
            beam = beam + np.exp(-1j * k * (x[t] + x[r]) * np.sin(np.radians(theta0_deg))) * h
    return beam


def cut_metrics(theta_deg, values_db):
    k = int(np.argmax(values_db))
    lo = hi = k
    while lo > 0 and values_db[lo - 1] >= values_db[k] - 3:
        lo -= 1
    while hi < len(values_db) - 1 and values_db[hi + 1] >= values_db[k] - 3:
        hi += 1
    # highest local maximum outside the main lobe region (first nulls)
    l, h = lo, hi
    while l > 0 and values_db[l - 1] < values_db[l]:
        l -= 1
    while h < len(values_db) - 1 and values_db[h + 1] < values_db[h]:
        h += 1
    side = [values_db[i] for i in list(range(0, l)) + list(range(h + 1, len(values_db)))]
    def cross(i_in, i_out):  # linear interpolation in dB of the -3 dB crossing between two samples
        if i_out < 0 or i_out >= len(values_db):
            return float(theta_deg[i_in])
        y0, y1, ref = values_db[i_in], values_db[i_out], values_db[k] - 3
        return float(theta_deg[i_in] + (theta_deg[i_out] - theta_deg[i_in]) * (y0 - ref) / (y0 - y1))
    return {"peak_deg": float(theta_deg[k]), "hpbw_deg": round(cross(hi, hi + 1) - cross(lo, lo - 1), 2),
            "max_sidelobe_db": float(max(side) - values_db[k]) if side else None}


# -------------------------------------------------------------------- I/O ---
def _unit_scale(header):
    """Scale to volts from the unit in brackets of an AEDT column header ('re(rETheta) [mV]' -> 1e-3)."""
    if "[" not in header:
        return 1.0
    unit = header[header.index("[") + 1:header.index("]")].strip()
    pref = {"": 1.0, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9}
    if unit.endswith("V") and unit[:-1] in pref:
        return pref[unit[:-1]]
    raise ValueError(f"unknown field unit in column header {header!r}")


def read_ff_csv(path, freq_ghz, suffix=None):
    """Long format (one frequency per file or a Freq column) or, with `suffix`, the AEDT wide format where
    each frequency is a column family: 're(rETheta)[mV]', 're(rETheta)_1[mV]', ... (suffix '', '_1', '_2')."""
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    head = [h.strip() for h in rows[0]]

    def col(*keys):
        for i, h in enumerate(head):
            name = h.split("[")[0].strip().lower()
            if suffix is not None and keys[0].startswith(("re(", "im(")):
                if name == (keys[0] + ")" + suffix).lower():
                    return i
                continue
            if all(k.lower() in h.lower() for k in keys):
                return i
        raise KeyError(f"{path}: no column with {keys} (suffix {suffix!r}) in {head}")
    ip, it = col("phi", "deg"), col("theta", "deg")
    try:
        jf = col("freq")
    except KeyError:
        jf = None
    cols = [col("re(retheta"), col("im(retheta"), col("re(rephi"), col("im(rephi")]
    if suffix is not None:
        jf = None
    scale = [_unit_scale(head[c]) for c in cols]  # AEDT may give each column its own unit (V, mV, ...)
    data = np.array([[float(v) for v in r] for r in rows[1:] if r])
    for c, sc in zip(cols, scale):
        data[:, c] *= sc
    if jf is not None:
        data = data[np.isclose(data[:, jf], freq_ghz, atol=1e-6)]
    phis, ths = np.unique(data[:, ip]), np.unique(data[:, it])
    F = np.zeros((2, len(ths), len(phis)), complex)
    for r in data:
        i, j = np.searchsorted(ths, r[it]), np.searchsorted(phis, r[ip])
        F[0, i, j] = r[cols[0]] + 1j * r[cols[1]]
        F[1, i, j] = r[cols[2]] + 1j * r[cols[3]]
    return ths, phis, F


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("--ff", nargs="+", type=Path, required=True, help="one far-field CSV per port, P1..PN")
    cli.add_argument("--freq-ghz", type=float, required=True)
    cli.add_argument("--pitch-mm", type=float, default=13.5)
    cli.add_argument("--steer", type=float, nargs="*", default=[0.0])
    cli.add_argument("--sequence", default=None)
    cli.add_argument("--s4p", type=Path, default=None)
    cli.add_argument("--gamma-off", type=complex, default=0j)
    cli.add_argument("--pol", choices=["co_y", "vector"], default="co_y")
    cli.add_argument("--ff-suffix", default=None,
                     help="AEDT wide CSV: column suffix of this frequency ('' , '_1', '_2'); see the export notes")
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    fields = [read_ff_csv(p, a.freq_ghz, a.ff_suffix) for p in a.ff]
    th, ph = fields[0][0], fields[0][1]
    F = np.array([f[2] for f in fields])
    n = len(F)
    if a.pol == "co_y":
        F = co_pol_y(F[:, 0], F[:, 1], np.radians(ph)[None, None, :])
    S = None
    if a.s4p is not None:
        from array_mimo_metrics import read_touchstone
        f, s, _ = read_touchstone(a.s4p)
        S = s[int(np.argmin(abs(f - a.freq_ghz * 1e9)))]
    x = (np.arange(n) - (n - 1) / 2) * a.pitch_mm * 1e-3
    k = 2 * np.pi * a.freq_ghz * 1e9 / C0
    seq = parse_sequence(a.sequence) if a.sequence else default_sequence(n)
    out = {"inputs": [str(p) for p in a.ff], "freq_ghz": a.freq_ghz, "pitch_mm": a.pitch_mm, "pol": a.pol,
           "gamma_off": str(a.gamma_off), "sequence_1based": [[t + 1, [r + 1 for r in rx]] for t, rx in seq],
           "virtual_positions_mm_multiplicity": {f"{p * 1e3:g}": m for p, m in virtual_positions(seq, x).items()},
           "beams": {}}
    j0, j180 = int(np.argmin(abs(ph - 0))), int(np.argmin(abs(ph - 180)))
    for st in a.steer:
        B = virtual_beam(F, x, k, seq, st, S, a.gamma_off)
        p = np.abs(B) ** 2
        db = 10 * np.log10(np.maximum(p / p.max(), 1e-12))
        t_cut = np.r_[-th[::-1][:-1], th]
        v_cut = np.r_[db[::-1, j180][:-1], db[:, j0]]
        out["beams"][f"theta0_{st:g}deg"] = {"xz_cut": cut_metrics(t_cut, v_cut),
                                             "peak_theta_phi_deg": [float(th[np.unravel_index(p.argmax(), p.shape)[0]]),
                                                                    float(ph[np.unravel_index(p.argmax(), p.shape)[1]])]}
    a.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
