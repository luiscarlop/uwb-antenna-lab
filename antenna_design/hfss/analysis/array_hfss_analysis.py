"""Analysis of an owner HFSS multiport array solve: S-matrix metrics, embedded patterns, physical array beam and
MIMO virtual-array beam (all from the exported data, no model).

Inputs (owner exports, read only): <dir>/ARR1x<N>_d<pitch>mm.s<N>p and <dir>/ff_P1.csv ... ff_PN.csv
(AEDT wide CSV: re/im(rETheta), re/im(rEPhi) in mV, one column family per frequency).
Frequency of each column family (no suffix, _1, _2): the mapping the owner confirmed for the element exports
(7.9872, 7.7376, 8.2368 GHz). It is checked here from the far-field PHASE (`frequency_mapping_check`): for the
outer ports, arg(E_phi(theta, phi=0) / E_phi(theta, phi=180)) is linear in sin(theta) with slope 2 k x_p, so the
fitted slopes must order like the assigned frequencies. Radiated/accepted power (`efficiency_check`) is only an
order-of-magnitude check: every permutation of the columns gives plausible efficiencies (validator, 2026-11-15).

Gains: Edit Sources at 1 W (incident) per active port, so U = |rE|^2 / (2 eta0) and
realized gain = 4 pi U / P_incident_total (includes mismatch and coupling losses).
Physical array beam: superposition sum_p w_p F_p (uniform 1 W per port, progressive phase for theta0 in xz).
Virtual beam: virtual_array_pattern.virtual_beam (co-polar Ludwig-3 y, default 1 TX + 2 RX sequence, off ports
50 ohm). Two-way beams are reported normalised to their peak (no dBi).

Usage: python antenna_design/hfss/analysis/array_hfss_analysis.py <dir> --pitch-mm 17 --out <json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from array_mimo_metrics import metrics, read_touchstone
from virtual_array_pattern import C0, co_pol_y, cut_metrics, default_sequence, read_ff_csv, virtual_beam

ETA0 = 376.730313668
SUFFIX_FREQ = {"": 7.9872, "_1": 7.7376, "_2": 8.2368}


def cut(theta, phi, val_db, pa, pb):
    ja, jb = int(np.argmin(abs(phi - pa))), int(np.argmin(abs(phi - pb)))
    t = np.r_[-theta[::-1][:-1], theta]
    v = np.r_[val_db[::-1, jb][:-1], val_db[:, ja]]
    return t, v


def beam_summary(theta, phi, p_lin, absolute):
    db = 10 * np.log10(np.maximum(p_lin, 1e-30))
    i, j = np.unravel_index(int(np.argmax(db)), db.shape)
    out = {"peak_db" if not absolute else "peak_dbi": round(float(db[i, j]), 2),
           "peak_theta_phi_deg": [float(theta[i]), float(phi[j])]}
    rel = db - db.max()
    for name, (pa, pb) in {"xz": (0, 180), "yz": (90, 270)}.items():
        t, v = cut(theta, phi, rel, pa, pb)
        fw = (t >= -90) & (t <= 90)
        out[f"{name}_cut"] = cut_metrics(t[fw], v[fw])
    out["front_to_back_db"] = round(float(rel[0, 0] - rel[-1, 0]), 2) if theta[-1] == 180 else None
    return out



def conv_text(path):
    """Summary of an HFSS convergence.conv, or a note that it was not exported."""
    if not path.exists():
        return "adaptive convergence data not provided"
    t = {}
    for line in path.read_text(errors="replace").splitlines():
        k, _, v = line.partition(":")
        t.setdefault(k.strip(), v.strip())
    if "Converged" not in t:
        return "convergence.conv unparsable"
    return (f"adaptive {'converged' if t['Converged'] == 'Yes' else 'NOT converged'}: "
            f"{t.get('Criterion', '?')} {t.get('Current', '?')} (target {t.get('Target', '?')}, "
            f"{t.get('Current Consecutive Passes', '?')}/{t.get('Target Consecutive Passes', '?')} consecutive passes), "
            f"{t.get('Completed', '?')} of {t.get('Maximum', '?')} passes")


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("dir", type=Path)
    cli.add_argument("--pitch-mm", type=float, required=True)
    cli.add_argument("--steer", type=float, nargs="*", default=[0.0, 15.0, 30.0])
    cli.add_argument("--out", type=Path, required=True)
    a = cli.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    snp = sorted(a.dir.glob("*.s*p"))
    assert len(snp) == 1, snp
    f, s, z0 = read_touchstone(snp[0])
    n = s.shape[1]
    x = (np.arange(n) - (n - 1) / 2) * a.pitch_mm * 1e-3
    out = {"source_dir": str(a.dir), "touchstone": snp[0].name, "pitch_mm": a.pitch_mm, "n_ports": n,
           "evidence": "EM_SIMULATED (HFSS, owner export; Touchstone exported with HFSS "
                       + next((l.split("HFSS")[-1].strip() for l in open(snp[0]) if "exported from HFSS" in l), "?")
                       + "; solving version not confirmed; " + conv_text(a.dir / "convergence.conv")
                       + "; lumped port, no wave-port check, so not HFSS_VALIDATED); analysis by array_hfss_analysis.py",
           "s_parameters": metrics(f, s, a.pitch_mm, a.steer), "frequencies": {}}
    eff, slopes = {}, {}
    long_format = "freq" in open(a.dir / "ff_P1.csv").readline().lower()  # script export: Freq column
    for suf, fghz in SUFFIX_FREQ.items():
        fields = [read_ff_csv(a.dir / f"ff_P{p}.csv", fghz, None if long_format else suf) for p in range(1, n + 1)]
        th, ph = fields[0][0], fields[0][1]
        F = np.array([fl[2] for fl in fields])                  # n x 2 x T x P, volts
        T, P = np.meshgrid(np.radians(th), np.radians(ph), indexing="ij")
        w = np.sin(T) * np.radians(th[1] - th[0]) * np.radians(ph[1] - ph[0])
        w[:, -1] = 0 if ph[-1] - ph[0] >= 360 - 1e-9 else w[:, -1]
        w[[0, -1], :] *= 0.5
        k = 2 * np.pi * fghz * 1e9 / C0
        i0 = int(np.argmin(abs(f - fghz * 1e9)))
        rec = {"column_suffix": None if long_format else suf, "embedded": {}, "physical": {}, "virtual": {}}
        j0, j180 = int(np.argmin(abs(ph - 0))), int(np.argmin(abs(ph - 180)))
        sel = (th > 0) & (th <= 40)
        slopes[fghz] = {}
        for p in (0, n - 1):
            r = np.unwrap(np.angle(F[p, 1, sel, j0] / F[p, 1, sel, j180]))
            slopes[fghz][f"P{p + 1}"] = {"observed": round(float(np.polyfit(np.sin(np.radians(th[sel])), r, 1)[0]), 3),
                                         "expected_2kx": round(float(2 * k * x[p]), 3)}
        eff[fghz] = []
        for p in range(n):
            U = (abs(F[p]) ** 2).sum(0) / (2 * ETA0)
            prad = float((U * w).sum())
            pacc = float(1 - (abs(s[i0, :, p]) ** 2).sum())
            eff[fghz].append(round(prad / pacc, 3))
            rec["embedded"][f"P{p + 1}"] = {**beam_summary(th, ph, 4 * np.pi * U, True),
                                            "radiated_power_w_per_1w_incident": round(prad, 4)}
        for st in a.steer:
            wgt = np.exp(-1j * k * x * np.sin(np.radians(st)))
            E = np.tensordot(wgt, F, axes=(0, 0))
            U = (abs(E) ** 2).sum(0) / (2 * ETA0)
            rec["physical"][f"theta0_{st:g}deg"] = beam_summary(th, ph, 4 * np.pi * U / n, True)
            Fco = co_pol_y(F[:, 0], F[:, 1], P[None])
            B = virtual_beam(Fco, x, k, default_sequence(n), st)
            pv = abs(B) ** 2
            rec["virtual"][f"theta0_{st:g}deg"] = beam_summary(th, ph, pv / pv.max(), False)
        out["frequencies"][f"{fghz}"] = rec
    out["efficiency_check"] = {"radiated_over_accepted_per_port": {str(k): v for k, v in eff.items()},
                               "note": "order of magnitude only; does not discriminate the column mapping"}
    order_obs = sorted(slopes, key=lambda q: abs(slopes[q][f"P{n}"]["observed"]))
    out["frequency_mapping_check"] = {"mapping": "Freq column (long format)" if long_format else
                                      "no suffix 7.9872, _1 7.7376, _2 8.2368 GHz",
                                      "phase_slopes_rad": {str(q): v for q, v in slopes.items()},
                                      "observed_order_matches_frequency_order": order_obs == sorted(slopes)}
    out["notes"] = ["HPBW from cuts at phi = 0/180 (xz) and 90/270 (yz), 5 deg grid, -3 dB crossing interpolated "
                    "linearly in dB (about +-0.5 deg, slight underestimate); global peaks lie ~5 deg off the xz plane "
                    "(tilt toward -y).", "front_to_back_db = G(theta=0) - G(theta=180), not peak-to-back.",
                    "Virtual array: off ports on 50 ohm (owner hardware decision), co-polar Ludwig-3 y.",
                    "ECC from S assumes lossless antennas; pattern-based ECC not computed yet."]
    out["virtual_sequence"] = f"default 1 TX + 2 RX, {len(default_sequence(n))} configurations"
    a.out.write_text(json.dumps(out, indent=2) + "\n")
    q = out["frequencies"]["7.9872"]
    print(json.dumps({"mapping": out["frequency_mapping_check"], "eff": out["efficiency_check"], "embedded_P1": q["embedded"]["P1"], "embedded_P3": q["embedded"]["P3"],
                      "physical": q["physical"], "virtual": q["virtual"]}, indent=1))


if __name__ == "__main__":
    main()
