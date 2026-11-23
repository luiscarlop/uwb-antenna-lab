"""Virtual 1xN array with BISTATIC + MONOSTATIC pairs (SoC with 2 RF ports) against the current bistatic scheme.

Question: what changes in the patterns of the HFSS 1xN array if, besides the bistatic pairs, the monostatic ones
(element t on the TX/RX port, receiving its own echo) are also used?

Hardware model (owner's brief, 2026-11-18): the SoC has 2 RF ports, one TX/RX and one RX only. In each acquisition
an element t is connected to the TX/RX port (it transmits and receives) and another element r to the RX-only port.
Every ordered pair (t, r), t != r, is therefore one acquisition that gives TWO channels:
  * monostatic  t -> t : E_t . E_t, virtual element at 2 x_t   (phase k 2 x_t sin(theta));
  * bistatic    t -> r : E_t . E_r, virtual element at x_t + x_r.
For N = 5: N (N-1) = 20 acquisitions, 40 channels. The monostatic channel needs the TX/RX port switched to the SAME
element that transmits (the TX element listens too); the round-trip delay is the same two-way model as in the
bistatic channel (transmit with t, receive with t or r), so no new propagation model is introduced.

Schemes (all on the full sphere, 5 deg grid, per frequency, normalised to their own maximum, uniform channel weights,
coherent complex sum with w = exp(-j k x_v sin(theta0)), xz steering theta0 = 0, 15, 30 deg, co-polar Ludwig-3 y):
  a) "bistatic_current": virtual_array_pattern.default_sequence (1 TX + 2 RX, N C(N-1,2) = 30 acquisitions, 60 channels),
     computed with virtual_array_pattern.virtual_beam. Virtual positions -3d..3d (for N = 5).
  b) "bistatic_plus_monostatic": the 20 ordered pairs, 40 channels (per acquisition one monostatic t->t and one
     bistatic t->r). Positions -4d..4d, with 2 x_t at -4d, -2d, 0, 2d, 4d. (t, r) and (r, t) give the same ideal
     bistatic channel (reciprocity), so each bistatic position carries a doubled weight, and the monostatic channel of
     element t appears N-1 = 4 times (once per acquisition where t is the TX/RX element). Uniform weights per CHANNEL.
  c) "monostatic_only" (reference, optional --mono-only): the N monostatic channels E_t . E_t at 2 x_t, spacing 2 d.
Per scheme the JSON lists the virtual positions with their multiplicity, the xz and yz metrics (HPBW interpolated at
-3 dB on the 5 deg grid, highest sidelobe with its angle), and the grating lobes predicted by the virtual spacing
(sin(theta) = sin(theta0) + m lambda / d_v, m != 0, with the pattern level found within +-3 deg of each predicted
angle, flagged as present when it is >= -10 dB). Scheme b also reports "quasi_grating_lobes_2d_subset": the positions
of the monostatic channels (even multiples of d) and the multiplicities (4,2,6,4,8,4,6,2,4 for N = 5) make the
weight distribution 2d-periodic, so a lobe at sin(theta) = sin(theta0) + m lambda / (2 d) appears although the
virtual spacing is d (no true grating lobe, but a high sidelobe when steering). Plus the normalised 3D grid (broadside, dB) for the artifact.

Warnings (what this model does NOT include):
  * the real monostatic channel carries the TX -> RX leakage/coupling of the TX/RX port itself and the reflection of
    that port (S_tt, the element's own mismatch) which are NOT in the radiated field: here only the ideal radiated
    channel E_t . E_t is modelled. In practice that leakage can dominate over the target echo and needs
    cancellation/range gating; the monostatic channels are the most exposed to it.
  * the monostatic channel requires switching the TX/RX port to the same element that transmits (yes, an RF
    switch matrix on the TX/RX port feeding each of the 5 elements; the RX-only port needs its own switch).
  * narrow-band far-field point-target model, as virtual_array_pattern.py: GUIDE_MODEL with HFSS-embedded fields
    (Gamma_off = 0). It is a derived pattern, not a measurement, and no absolute gain is computed.
  * 5 deg grid: HPBW and sidelobe angles are quantised (HPBW interpolated linearly in dB between samples).

Input : <dir>/ff_P1.csv ... ff_PN.csv (long format with Freq column, or AEDT wide format; see array_virtual_3d.py).
Usage : python antenna_design/hfss/analysis/array_virtual_monostatic.py <dir> --pitch-mm 18.2 --out <json> [--mono-only]
Evidence: inherits the HFSS evidence of its inputs for the embedded fields; derived pattern = GUIDE_MODEL.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from array_virtual_3d import cut, freqs_of
from virtual_array_pattern import C0, co_pol_y, cut_metrics, default_sequence, read_ff_csv, virtual_beam

STEERS_DEG = (0.0, 15.0, 30.0)
GRATING_WINDOW_DEG = 3.0
GRATING_PRESENT_DB = -10.0


# ----------------------------------------------------------- channel sets ---
def channels_bistatic_current(n):
    """(t, r) channels of default_sequence (1 TX + 2 RX): N C(N-1, 2) acquisitions, 2 channels each."""
    return [(t, r) for t, rx in default_sequence(n) for r in rx]


def channels_bi_plus_mono(n):
    """Ordered pairs (t, r), t != r: each acquisition gives the monostatic (t, t) and the bistatic (t, r) channel."""
    chans = []
    for t, r in itertools.permutations(range(n), 2):
        chans += [(t, t), (t, r)]
    return chans


def channels_mono_only(n):
    return [(t, t) for t in range(n)]


def n_acquisitions(scheme, n):
    return {"bistatic_current": len(default_sequence(n)), "bistatic_plus_monostatic": n * (n - 1),
            "monostatic_only": n}[scheme]


def channel_positions(chans, x):
    """Virtual element positions x_t + x_r (m) with the multiplicity (number of channels) at each one."""
    pos = {}
    for t, r in chans:
        key = round(x[t] + x[r], 9)
        pos[key] = pos.get(key, 0) + 1
    return dict(sorted(pos.items()))


def channel_beam(H, x, k, chans, theta0_deg=0.0):
    """Coherent uniform-weight beam of the channels (t, r). H[t][r] = E_t . E_r (T x P complex)."""
    s0 = np.sin(np.radians(theta0_deg))
    beam = 0
    for t, r in chans:
        beam = beam + np.exp(-1j * k * (x[t] + x[r]) * s0) * H[t][r]
    return beam


def pair_products(Fco):
    """H[t][r] = E_t E_r for the co-polar scalar fields Fco (N x T x P)."""
    n = len(Fco)
    return [[Fco[t] * Fco[r] for r in range(n)] for t in range(n)]


# ----------------------------------------------------------- cut metrics ---
def cut_lobes(theta, db):
    """cut_metrics plus the angle of the highest sidelobe (outside the first nulls of the main lobe)."""
    m = cut_metrics(theta, db)
    k = int(np.argmax(db))
    lo = hi = k
    while lo > 0 and db[lo - 1] >= db[k] - 3:
        lo -= 1
    while hi < len(db) - 1 and db[hi + 1] >= db[k] - 3:
        hi += 1
    l, h = lo, hi
    while l > 0 and db[l - 1] < db[l]:
        l -= 1
    while h < len(db) - 1 and db[h + 1] < db[h]:
        h += 1
    idx = list(range(0, l)) + list(range(h + 1, len(db)))
    if idx:
        i = max(idx, key=lambda j: db[j])
        m["max_sidelobe_deg"] = float(theta[i])
    else:
        m["max_sidelobe_deg"] = None
    return m


def grating_lobes(theta, db, freq_ghz, spacing_m, theta0_deg, window_deg=GRATING_WINDOW_DEG):
    """Grating lobes predicted by a uniform virtual spacing: sin(theta) = sin(theta0) + m lambda / spacing, m != 0,
    |sin| < 1. For each one the pattern level (max within +-window_deg on the xz cut, dB) and a presence flag."""
    lam = C0 / (freq_ghz * 1e9)
    s0 = np.sin(np.radians(theta0_deg))
    out = []
    mmax = int(np.ceil(2 * spacing_m / lam)) + 1
    for m in range(-mmax, mmax + 1):
        if m == 0:
            continue
        s = s0 + m * lam / spacing_m
        if abs(s) >= 1:
            continue
        ang = float(np.degrees(np.arcsin(s)))
        sel = np.abs(theta - ang) <= window_deg
        lvl = float(db[sel].max()) if sel.any() else None
        out.append({"m": m, "theta_deg": round(ang, 2), "level_db": None if lvl is None else round(lvl, 2),
                    "present": bool(lvl is not None and lvl >= GRATING_PRESENT_DB)})
    return out


def scheme_record(B, th, ph, freq_ghz, spacing_m, steer, quasi_spacing_m=None):
    """Metrics of one beam B (T x P complex): normalised to its sphere maximum, xz/yz cuts."""
    p = abs(B) ** 2
    db = 10 * np.log10(np.maximum(p / p.max(), 1e-12))
    rec = {"peak_theta_phi_deg": [float(th[np.unravel_index(p.argmax(), p.shape)[0]]),
                                  float(ph[np.unravel_index(p.argmax(), p.shape)[1]])]}
    for name, (pa, pb) in {"xz": (0, 180), "yz": (90, 270)}.items():
        t, v = cut(th, ph, db, pa, pb)
        fw = (t >= -90) & (t <= 90)
        v = v[fw] - v[fw].max()
        rec[name] = cut_lobes(t[fw], v)
        if name == "xz":
            rec["xz"]["grating_lobes"] = grating_lobes(t[fw], v, freq_ghz, spacing_m, steer)
            rec["xz"]["grating_lobe_present"] = any(g["present"] for g in rec["xz"]["grating_lobes"])
            if quasi_spacing_m is not None:  # lobes of a sub-array with a larger spacing (2 x_t of the monostatic channels)
                rec["xz"]["quasi_grating_lobes_2d_subset"] = grating_lobes(t[fw], v, freq_ghz, quasi_spacing_m, steer)
            rec["xz_cut"] = {"theta_deg": t[fw].tolist(), "db": np.round(v, 2).tolist()}
        else:
            rec["yz_cut"] = {"theta_deg": t[fw].tolist(), "db": np.round(v, 2).tolist()}
    return rec, db


def analyse(Fco, th, ph, x, freq_ghz, pitch_m, mono_only=False, grid=True, steers=STEERS_DEG):
    """All schemes, all steers for one frequency. Fco: N x T x P co-polar fields."""
    n = len(Fco)
    k = 2 * np.pi * freq_ghz * 1e9 / C0
    H = pair_products(Fco)
    schemes = {"bistatic_current": (channels_bistatic_current(n), pitch_m),
               "bistatic_plus_monostatic": (channels_bi_plus_mono(n), pitch_m)}
    if mono_only:
        schemes["monostatic_only"] = (channels_mono_only(n), 2 * pitch_m)
    seq = default_sequence(n)
    res = {}
    for name, (chans, spacing) in schemes.items():
        pos = channel_positions(chans, x)
        res[name] = {"acquisitions": n_acquisitions(name, n), "channels": len(chans), "virtual_spacing_mm": spacing * 1e3,
                     "virtual_positions_mm_multiplicity": {f"{q * 1e3:g}": m for q, m in pos.items()},
                     "virtual_positions_in_pitch_multiplicity": {f"{q / pitch_m:g}": m for q, m in pos.items()},
                     "beams": {}}
        for st in steers:
            if name == "bistatic_current":
                B = virtual_beam(Fco, x, k, seq, st)  # same function as array_virtual_3d.py
            else:
                B = channel_beam(H, x, k, chans, st)
            quasi = 2 * pitch_m if name == "bistatic_plus_monostatic" else None
            rec, db = scheme_record(B, th, ph, freq_ghz, spacing, st, quasi)
            res[name]["beams"][f"theta0_{st:g}deg"] = rec
            if grid and st == 0.0:
                res[name]["grid_db_broadside"] = np.round(db, 1).tolist()
    return res


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("dir", type=Path)
    cli.add_argument("--pitch-mm", type=float, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--mono-only", action="store_true", help="also the monostatic-only reference (N channels, 2 x_t)")
    cli.add_argument("--no-grid", action="store_true", help="omit the 3D grid (smaller JSON)")
    a = cli.parse_args()
    files = sorted(a.dir.glob("ff_P*.csv"), key=lambda p: int(p.stem[4:]))
    n = len(files)
    pitch = a.pitch_mm * 1e-3
    x = (np.arange(n) - (n - 1) / 2) * pitch
    suf = freqs_of(files[0])
    out = {"source_dir": str(a.dir), "pitch_mm": a.pitch_mm, "n_ports": n, "freqs_ghz": list(suf),
           "evidence": "GUIDE_MODEL on HFSS embedded fields (1 W on P_i, others 50 ohm); ideal radiated channel only",
           "pol": "co_y (Ludwig-3)", "weights": "uniform per channel, coherent complex sum",
           "steer_deg_xz": list(STEERS_DEG), "theta_grid_step_deg": 5,
           "warnings": ["monostatic channel real = radiated E_t.E_t + TX->RX leakage/coupling of the TX/RX port + "
                        "reflection S_tt of that port (not modelled)",
                        "monostatic needs the TX/RX port switched to the same element that transmits; the round-trip "
                        "delay is the same two-way model"],
           "per_freq": {}}
    for fg in suf:
        fields = [read_ff_csv(f, fg, suf[fg]) for f in files]
        th, ph = fields[0][0], fields[0][1]
        F = np.array([q[2] for q in fields])
        _, P = np.meshgrid(np.radians(th), np.radians(ph), indexing="ij")
        Fco = co_pol_y(F[:, 0], F[:, 1], P[None])
        rec = analyse(Fco, th, ph, x, fg, pitch, a.mono_only, not a.no_grid)
        rec["theta_deg"], rec["phi_deg"] = th.tolist(), ph.tolist()
        out["per_freq"][f"{fg:g}"] = rec
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out) + "\n")
    summ = {f: {s: {st: (b["xz"]["hpbw_deg"], None if b["xz"]["max_sidelobe_db"] is None else round(b["xz"]["max_sidelobe_db"], 1), b["xz"]["grating_lobe_present"])
                    for st, b in r[s]["beams"].items()}
                for s in r if isinstance(r[s], dict) and "beams" in r[s]} for f, r in out["per_freq"].items()}
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
