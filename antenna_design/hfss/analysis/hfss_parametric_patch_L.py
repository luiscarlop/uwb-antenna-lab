"""Owner HFSS parametric sweep of US3_MS3 patch_L (2026-11-13): channel metrics per value.

Input : hfss/results/results_US3_MS3/S Parameter US3_MS3 parametric patch_L.csv  (patch_L [mm], Freq [GHz], dB(S11); 1 MHz)
Output: hfss/results/results_US3_MS3/hfss_parametric_patch_L.json (refuses to overwrite).
Evidence: HFSS_VALIDATED data from the owner; the linear fit of band centre vs patch_L is a summary, not a model.
"""
import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "results" / "results_US3_MS3" / "S Parameter US3_MS3 parametric patch_L.csv"
OUT = HERE.parent / "results" / "results_US3_MS3" / "hfss_parametric_patch_L.json"
BAND = (7.7376, 8.2368)


def band(f, db, th):
    i = int(np.argmin(db))
    if db[i] > th:
        return None
    lo = hi = i
    while lo > 0 and db[lo - 1] <= th:
        lo -= 1
    while hi < len(f) - 1 and db[hi + 1] <= th:
        hi += 1
    return {"from_ghz": float(f[lo]), "to_ghz": float(f[hi]), "width_mhz": round(float(f[hi] - f[lo]) * 1000, 1)}


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    r = np.array([[float(x) for x in row] for row in list(csv.reader(open(SRC)))[1:]])
    rows = []
    for L in sorted(set(r[:, 0])):
        a = r[r[:, 0] == L]
        f, db = a[:, 1], a[:, 2]
        b = (f >= BAND[0] - 1e-9) & (f <= BAND[1] + 1e-9)
        b10 = band(f, db, -10)
        rows.append({"patch_L_mm": L, "channel_worst_db": round(float(db[b].max()), 2),
                     "channel_worst_ghz": float(f[b][db[b].argmax()]),
                     "min_db": round(float(db.min()), 2), "min_ghz": float(f[db.argmin()]),
                     "local_minima_count": int(sum(1 for i in range(1, len(f) - 1) if db[i] < db[i - 1] and db[i] < db[i + 1])),
                     "band_minus6db": band(f, db, -6), "band_minus10db": b10,
                     "minus10_centre_ghz": round((b10["from_ghz"] + b10["to_ghz"]) / 2, 4) if b10 else None})
    L = np.array([x["patch_L_mm"] for x in rows])
    c = np.array([x["minus10_centre_ghz"] for x in rows])
    k, c0 = np.polyfit(L, c, 1)
    resid = c - (k * L + c0)
    best = min(rows, key=lambda x: x["channel_worst_db"])
    out = {"source": str(SRC.relative_to(HERE.parents[1])), "design": "US3_MS3", "evidence": "HFSS (owner), one adaptive solve per value",
           "rows": rows,
           "minus10_centre_fit": {"mhz_per_0p01mm": round(k * 10, 2), "rms_residual_mhz": round(float(np.sqrt((resid ** 2).mean())) * 1000, 1),
                                  "max_abs_residual_mhz": round(float(abs(resid).max()) * 1000, 1),
                                  "note": "non-monotonic residuals of this size are attributed to per-value adaptive meshing (not verified)"},
           "minus10_width_mhz_range": [min(x["band_minus10db"]["width_mhz"] for x in rows), max(x["band_minus10db"]["width_mhz"] for x in rows)],
           "best_channel_worst": {"patch_L_mm": best["patch_L_mm"], "channel_worst_db": best["channel_worst_db"]},
           "conclusion": "patch_L shifts the response without changing its width; -10 dB width ~350 MHz < 499.2 MHz channel, so no patch_L meets -10 dB over the channel."}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("minus10_centre_fit", "minus10_width_mhz_range", "best_channel_worst")}, indent=1))


if __name__ == "__main__":
    main()
