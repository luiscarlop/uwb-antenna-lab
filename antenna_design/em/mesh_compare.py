"""Two-mesh comparison of S11 (complex) between two finished openEMS runs.

Usage (no openEMS needed):
    python em/mesh_compare.py --coarse em/<RUN_A> --fine em/<RUN_B> --out em/<RUN_B>/mesh_comparison.json

Applies the pre-registered rule of reports/claude_run_016.md (series rule, two meshes):
  1. worst |S11| in channel on the finer mesh <= -6.0 dB and change of the worst case <= 0.5 dB
  2. max |Gamma_fine - Gamma_coarse| <= 0.03 over the channel, -6 dB edges move <= 10 MHz
  4. worst-case change 0.5..1 dB -> MESH_SENSITIVE; > 1 dB -> NOT_CONVERGED
  5. two meshes -> "bounded sensitivity", never "convergence".
Energy / port validity / |S11| <= 1.02 (item 3) are read from each run_numeric.json.
Added in Claude round 24; item-2 edges = contiguous -6 dB region around f0 since round 26.
No action on import.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

BAND = (7.7376e9, 8.2368e9)
# -6 dB edges are taken only in this window (the matched band around the channel); a second
# resonance outside it (e.g. ~10.3 GHz in US3_MS3) is not a channel edge.
EDGE_WINDOW_HZ = (7.0e9, 9.0e9)


def load(run: Path, name: str):
    with open(run / name, newline="") as fh:
        rows = list(csv.DictReader(fh))
    f = np.array([float(r["frequency_hz"]) for r in rows])
    g = np.array([float(r["s11_real"]) + 1j * float(r["s11_imag"]) for r in rows])
    return f, g


def edges(f, g, level_db=-6.0):
    keep = (f >= EDGE_WINDOW_HZ[0]) & (f <= EDGE_WINDOW_HZ[1])
    f, g = f[keep], g[keep]
    db = 20 * np.log10(np.abs(g))
    below = db <= level_db
    out = []
    for i in range(1, len(f)):
        if below[i] != below[i - 1]:
            t = (level_db - db[i - 1]) / (db[i] - db[i - 1])
            out.append(float(f[i - 1] + t * (f[i] - f[i - 1])))
    return out


def contiguous_edges(f, g, level_db=-6.0, f_ref=7.9872e9):
    """Edges of the contiguous |S11| <= level region that contains f_ref (round 26, pre-registered
    before the P01_MS1 fine run). Returns [lo, hi] interpolated, or None if f_ref is not below level."""
    db = 20 * np.log10(np.abs(g))
    k = int(np.argmin(np.abs(f - f_ref)))
    if db[k] > level_db:
        return None
    i = k
    while i > 0 and db[i - 1] <= level_db:
        i -= 1
    j = k
    while j < len(f) - 1 and db[j + 1] <= level_db:
        j += 1
    def interp(a, b):
        t = (level_db - db[a]) / (db[b] - db[a])
        return float(f[a] + t * (f[b] - f[a]))
    lo = interp(i - 1, i) if i > 0 else None
    hi = interp(j, j + 1) if j < len(f) - 1 else None
    return [lo, hi]


def channel_stats(f, g):
    m = (f >= BAND[0] - 1) & (f <= BAND[1] + 1)
    db = 20 * np.log10(np.abs(g[m]))
    i = int(np.argmax(db))
    j = int(np.argmin(db))
    return {"samples": int(m.sum()), "worst_db": float(db[i]), "worst_hz": float(f[m][i]),
            "best_db": float(db[j]), "best_hz": float(f[m][j]),
            "n_above_minus6": int((db > -6).sum()), "n_le_minus10": int((db <= -10).sum()),
            "max_abs_s11": float(np.abs(g[m]).max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coarse", type=Path, required=True)
    ap.add_argument("--fine", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    fa, ga = load(a.coarse, "s11_complex.csv")
    fb, gb = load(a.fine, "s11_complex.csv")
    if not np.allclose(fa, fb):
        raise SystemExit("frequency grids differ")
    sa, sb = channel_stats(fa, ga), channel_stats(fb, gb)
    m = (fa >= BAND[0] - 1) & (fa <= BAND[1] + 1)
    dgam = np.abs(gb[m] - ga[m])
    wa, wb = load(a.coarse, "s11_wideband.csv"), load(a.fine, "s11_wideband.csv")
    ea, eb = edges(*wa), edges(*wb)
    edge_shift = [abs(x - y) for x, y in zip(ea, eb)] if len(ea) == len(eb) else None
    # Round 26 (validator recommendation of round 24, fixed before the P01_MS1 fine data existed):
    # item 2 edges = edges of the contiguous -6 dB region containing f0, paired lo/hi.
    ca, cb = contiguous_edges(*wa), contiguous_edges(*wb)
    if ca and cb and None not in ca + cb:
        contig_shift = [abs(ca[0] - cb[0]), abs(ca[1] - cb[1])]
    else:
        contig_shift = None
    na = json.loads((a.coarse / "run_numeric.json").read_text())
    nb = json.loads((a.fine / "run_numeric.json").read_text())
    dworst = abs(sb["worst_db"] - sa["worst_db"])
    checks = {
        "1_fine_worst_le_minus6": sb["worst_db"] <= -6.0,
        "1_worst_change_le_0p5dB": dworst <= 0.5,
        "2_max_dGamma_le_0p03": float(dgam.max()) <= 0.03,
        "2_minus6_edges_shift_le_10MHz": contig_shift is not None and max(contig_shift) <= 10e6,
        "3_port_validity_ok": na.get("port_validity") == "OK" and nb.get("port_validity") == "OK",
        "3_abs_s11_le_1p02": max(sa["max_abs_s11"], sb["max_abs_s11"]) <= 1.02,
    }
    if all(checks.values()):
        verdict = "BOUNDED_SENSITIVITY_PASS"
    elif dworst > 1.0:
        verdict = "NOT_CONVERGED"
    elif dworst > 0.5:
        verdict = "MESH_SENSITIVE"
    else:
        verdict = "RULE_FAILED"
    res = {"coarse": str(a.coarse), "fine": str(a.fine), "rule": "reports/claude_run_016.md (two meshes)",
           "channel_coarse": sa, "channel_fine": sb, "worst_change_db": dworst,
           "max_abs_dGamma_channel": float(dgam.max()),
           "max_abs_dGamma_hz": float(fa[m][int(np.argmax(dgam))]),
           "minus6_edges_coarse_hz": ea, "minus6_edges_fine_hz": eb, "edge_shift_hz": edge_shift, "edge_window_hz": list(EDGE_WINDOW_HZ),
           "minus6_contiguous_coarse_hz": ca, "minus6_contiguous_fine_hz": cb, "contiguous_edge_shift_hz": contig_shift,
           "edge_rule": "item 2 uses contiguous -6 dB region containing f0 (round 26); window edges kept for reference",
           "checks": checks, "verdict": verdict,
           "note": "energy criterion (item 3) is checked from the solver logs by the orchestrator"}
    a.out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
