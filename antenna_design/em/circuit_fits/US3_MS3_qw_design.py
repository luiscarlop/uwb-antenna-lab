"""US3_MS3 quarter-wave transformer guide design (Claude round 23). GUIDE_MODEL only, not an EM result.

Port-plane Zin of US3_MS2 (EM, round 22) is moved to the patch edge through 9.749 mm of 50 ohm line with a
dispersive eps_eff (Hammerstad-Jensen static + Kirschning-Jansen dispersion), then a lossless lambda/4 section
(w_t, l_t, dispersive eps_eff, static HJ Z0 of the narrow line) plus the remaining 50 ohm line give S11 at the port.
Sensitivity: the 50 ohm eps_eff used for de-embedding is scaled by 0.95..1.05 (the round-22 R_edge spread).
Step discontinuity and transformer radiation/coupling are NOT modelled.
Usage: python em/circuit_fits/US3_MS3_qw_design.py
"""
import csv, math, sys
from pathlib import Path
import numpy as np

ER, H, T = 4.4, 2.07e-3, 35e-6
C0 = 299792458.0
BAND = (7.7376e9, 8.2368e9)
L50 = 9.749e-3
ROOT = Path(__file__).resolve().parents[3]


def hj(w):
    """Hammerstad-Jensen static Z0, eps_eff with Wheeler thickness correction."""
    u = w / H
    du = T / math.pi / H * (1 + math.log(4 * math.e / (T / H * (1 / math.tanh(math.sqrt(6.517 * u)))**2)))
    du = du * 0.5 * (1 + 1 / math.cosh(math.sqrt(ER - 1)))
    u = u + du
    a = 1 + math.log((u**4 + (u / 52)**2) / (u**4 + 0.432)) / 49 + math.log(1 + (u / 18.1)**3) / 18.7
    b = 0.564 * ((ER - 0.9) / (ER + 3))**0.053
    ee = (ER + 1) / 2 + (ER - 1) / 2 * (1 + 10 / u)**(-a * b)
    fu = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u)**0.7528)
    z01 = 60 * math.log(fu / u + math.sqrt(1 + (2 / u)**2))
    return z01 / math.sqrt(ee), ee


def kj_eeff(w, f):
    """Kirschning-Jansen dispersion of eps_eff."""
    z, ee0 = hj(w)
    u = w / H
    fn = f * H / 1e6  # GHz*mm
    p1 = 0.27488 + (0.6315 + 0.525 / (1 + 0.0157 * fn)**20) * u - 0.065683 * math.exp(-8.7513 * u)
    p2 = 0.33622 * (1 - math.exp(-0.03442 * ER))
    p3 = 0.0363 * math.exp(-4.6 * u) * (1 - math.exp(-(fn / 38.7)**4.97))
    p4 = 1 + 2.751 * (1 - math.exp(-(ER / 15.916)**8))
    p = p1 * p2 * ((0.1844 + p3 * p4) * fn)**1.5763
    eef = ER - (ER - ee0) / (1 + p)
    return z, eef  # Z0 kept static (HJ); its dispersion (a few %) is inside the sensitivity spread


def line_abcd(z0, beta, l):
    c, s = np.cos(beta * l), np.sin(beta * l)
    return c, 1j * z0 * s, 1j * s / z0, c


def zin_through(zl, z0, beta, l):
    a, b, c, d = line_abcd(z0, beta, l)
    return (a * zl + b) / (c * zl + d)


def load_port_plane():
    p = ROOT / "antenna_design/em/US3_MS2_OPENEMS_022/s11_wideband.csv"
    f, z = [], []
    with open(p) as fh:
        for r in csv.DictReader(fh):
            ff = float(r["frequency_hz"])
            if 7.3e9 <= ff <= 8.7e9:
                f.append(ff); z.append(float(r["zin_real_ohm"]) + 1j * float(r["zin_imag_ohm"]))
    return np.array(f), np.array(z)


def evaluate(wt, lt, scale=1.0, f=None, zport=None):
    s = []
    for fi, zp in zip(f, zport):
        z50, e50 = kj_eeff(3.92e-3, fi)
        b50 = 2 * math.pi * fi / C0 * math.sqrt(e50 * scale)
        zedge = zin_through(zp, 50.0, b50, -L50)          # de-embed the round-22 50 ohm line (reference 50 ohm)
        zt, et = kj_eeff(wt, fi)
        bt = 2 * math.pi * fi / C0 * math.sqrt(et)
        z1 = zin_through(zedge, zt, bt, lt)
        z2 = zin_through(z1, 50.0, b50, L50 - lt)
        s.append((z2 - 50) / (z2 + 50))
    return np.array(s)


def main():
    f, zp = load_port_plane()
    band = (f >= BAND[0]) & (f <= BAND[1])
    out = []
    best = None
    for wt in np.arange(0.6, 1.41, 0.1) * 1e-3:
        zt, et = kj_eeff(wt, 7.9872e9)
        for lt in np.arange(4.8, 7.01, 0.05) * 1e-3:
            worst = [20 * np.log10(np.abs(evaluate(wt, lt, sc, f, zp)[band]).max()) for sc in (0.95, 1.0, 1.05)]
            row = (wt * 1e3, lt * 1e3, zt, et, *worst)
            out.append(row)
            key = max(worst)
            if best is None or key < best[0]:
                best = (key, row)
    print("w_t[mm] l_t[mm] Zt[ohm] eeff_t(f0)  worst_dB(scale .95) (1.00) (1.05)")
    for wt in sorted({round(r[0], 2) for r in out}):
        rows = [r for r in out if round(r[0], 2) == wt]
        r = min(rows, key=lambda r: max(r[4:]))
        print(f"{r[0]:.2f} {r[1]:.2f} {r[2]:.1f} {r[3]:.3f}  {r[4]:.2f} {r[5]:.2f} {r[6]:.2f}")
    print("best robust:", best)
    if len(sys.argv) > 2:
        wt, lt = float(sys.argv[1]) * 1e-3, float(sys.argv[2]) * 1e-3
        for sc in (0.95, 1.0, 1.05):
            s = evaluate(wt, lt, sc, f, zp)
            print(sc, "band worst", 20 * np.log10(np.abs(s[band]).max()), "best", 20 * np.log10(np.abs(s[band]).min()))


if __name__ == "__main__":
    main()
