"""S-parameter metrics of the owner's HFSS 1x5 array pitch sweep (Optimetrics on arr_d), one row per pitch.

Input : <export_dir>/<design>_d<pitch>mm/ARR1x<N>_d<pitch>mm.s<N>p (claude_aedt_export_array_ch9.py export)
Output: JSON with, per pitch, the channel worst values of: passive port match |Sii|, neighbour and
        non-neighbour coupling, active reflection (uniform 1 W, progressive phase for theta0 in xz) and TARC,
        and the S-parameter ECC (lossless assumption, indicative only).
Evidence: EM_SIMULATED (HFSS, owner). Adaptive convergence only where convergence.conv is exported; lumped ports.
Usage: python antenna_design/hfss/analysis/array_pitch_sweep_hfss.py <export_dir> --out <json>
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np

from array_mimo_metrics import BAND_HZ, active_gamma, db, ecc_from_s, read_touchstone, steering

STEERS = [0, 15, 30, 45]


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("export_dir", type=Path)
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    rows = []
    for snp in sorted(a.export_dir.glob("*/*.s[0-9]p")):  # .s4p (1x4) or .s5p (1x5)
        m = re.search(r"_d(\d+)(?:p(\d+))?mm\.s\dp$", snp.name)
        pitch = float(m.group(1) + ("." + m.group(2) if m.group(2) else ""))
        f, s, z0 = read_touchstone(snp)
        assert abs(z0 - 50) < 1e-9
        n = s.shape[1]
        b = (f >= BAND_HZ[0] - 1) & (f <= BAND_HZ[1] + 1)
        sdb = db(s)
        nb = [(i, i + 1) for i in range(n - 1)]
        far = [(i, j) for i in range(n) for j in range(i + 2, n)]
        ecc = ecc_from_s(s)
        row = {"pitch_mm": pitch, "file": str(snp.relative_to(a.export_dir)),
               "port_match_worst_db": round(float(sdb[b][:, range(n), range(n)].max()), 2),
               "port_match_worst_by_port_db": [round(float(sdb[b, i, i].max()), 2) for i in range(n)],
               "neighbour_coupling_worst_db": round(float(max(sdb[b, i, j].max() for i, j in nb)), 2),
               "non_neighbour_coupling_worst_db": round(float(max(sdb[b, i, j].max() for i, j in far)), 2),
               "ecc_s_param_max": round(float(max(ecc[b, i, j].max() for i, j in nb + far)), 4),
               "reciprocity_max_abs": float(abs(s - s.transpose(0, 2, 1)).max()), "active": {}}
        for th in STEERS:
            g, tarc = active_gamma(s, steering(f, n, pitch * 1e-3, th))
            gdb = db(g)[b]
            k = np.unravel_index(int(np.argmax(gdb)), gdb.shape)
            row["active"][str(th)] = {"worst_db": round(float(gdb.max()), 2), "worst_port": int(k[1]) + 1,
                                      "worst_ghz": round(float(f[b][k[0]] / 1e9), 4),
                                      "tarc_worst_db": round(float(db(tarc)[b].max()), 2)}
        rows.append(row)
    rows.sort(key=lambda r: r["pitch_mm"])
    vers = sorted({next((l.split("HFSS")[-1].strip() for l in open(a.export_dir / r["file"]) if "exported from HFSS" in l), "?")
                   for r in rows})
    convs = [(a.export_dir / r["file"]).parent / "convergence.conv" for r in rows]
    out = {"evidence": "EM_SIMULATED (HFSS, owner Optimetrics on arr_d; Touchstone exported with HFSS "
                       + ", ".join(vers) + "; solving version not confirmed); adaptive convergence.conv exported for "
                       + f"{sum(c.exists() for c in convs)} of {len(rows)} pitches, "
                       + f"{sum(c.exists() and 'Converged : Yes' in c.read_text(errors='replace') for c in convs)} of them converged"
                       + "; lumped port, no wave-port check, so not HFSS_VALIDATED",
           "design": re.sub(r"_d[0-9p]+mm$", "", a.export_dir.resolve().name) if re.search(r"ARR1x\d_", a.export_dir.resolve().name) else a.export_dir.resolve().name, "channel_hz": BAND_HZ, "steer_deg": STEERS,
           "notes": ["channel grid of the 1 MHz sweep (7.738-8.236 GHz)", "ECC from S assumes lossless antennas",
                     "active reflection: uniform amplitude, progressive phase, all ports 50 ohm"],
           "rows": rows}
    a.out.write_text(json.dumps(out, indent=2) + "\n")
    print(f"{'d mm':>6} {'Sii':>7} {'nb':>7} {'far':>7} {'ECC':>6} | " + " | ".join(f"act{t:>2} TARC" for t in STEERS))
    for r in rows:
        print(f"{r['pitch_mm']:6.1f} {r['port_match_worst_db']:7.2f} {r['neighbour_coupling_worst_db']:7.2f} "
              f"{r['non_neighbour_coupling_worst_db']:7.2f} {r['ecc_s_param_max']:6.3f} | "
              + " | ".join(f"{r['active'][str(t)]['worst_db']:6.2f} {r['active'][str(t)]['tarc_worst_db']:6.2f}" for t in STEERS))


if __name__ == "__main__":
    main()
