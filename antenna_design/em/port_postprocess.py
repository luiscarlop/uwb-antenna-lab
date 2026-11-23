"""Post-processing of the openEMS MSL edge port (Claude round 7). numpy only: no CSXCAD/openEMS import.

Why this module exists
----------------------
In P02_MS1_OPENEMS_006 the openEMS MSLPort extraction of Z_line and beta (MSLPort.ReadUIData: beta =
sqrt(-dE dH / (E H)), Z_line = sqrt(E dE / (H dH))) was ill-conditioned under a strong standing wave
(|Gamma| ~ 0.92) and CalcPort(ref_plane_shift) re-used that beta, giving |S11| up to 1.26 at the launch
plane (validator, reports/claude_run_006.md). This module replaces it by:

  U = U_B (voltage probe at the middle line), I = mean(I_A, I_B) (the two current probes sit half a cell
  either side of B), reference impedance FIXED at 50 ohm (S11 = (U - a) / a, a = (U + 50 I) / 2, Zin = U / I).

  beta from the three equispaced voltage probes only:  cos(beta*D) = (U_A + U_C) / (2 U_B).
  Proof: for any mixture of a forward and a backward wave U(y) = F e^{-j beta y} + R e^{+j beta y}, so
  U(y - D) + U(y + D) = 2 cos(beta D) U(y). It needs no current, no Z_line and is exact for any |Gamma|.
  Branch: arccos gives beta*D in [0, pi]; the physical value is ~0.1-0.25 rad (D ~ 0.49 mm), far from the
  ambiguity at pi, so the principal branch is the real one and continuity in frequency is automatic; it is
  still checked (see FALLBACK_REASONS). When the estimate is unusable (|Re cos| > 1, |U_B| negligible,
  eps_eff outside [1, eps_r], outlier against the running median of the neighbouring estimates, non-finite)
  the analytic eps_eff(f) (Hammerstad-Jensen static + Getsinger dispersion) is used instead and the fact is
  recorded per frequency.

  Current-average correction (default ON, exact for any wave mixture): I(y_B - D/2) + I(y_B + D/2) =
  2 cos(beta D/2) I(y_B), hence I_B = mean(I_A, I_B) / cos(beta D / 2) (a 0.3 % amplitude effect at 8 GHz).

  Plane shift from the measurement plane (y_B) to the launch plane (y = -sy/2): ideal lossless line of
  Z0 = 50 ohm (the reference) with the same beta, U_l = U cos(th) + j 50 I sin(th), I_l = I cos(th) +
  j (U / 50) sin(th), th = beta L. Line loss is NEGLECTED (|S11| does not change in the shift) and a numerical
  line impedance different from 50 ohm is NOT calibrated: the result is S11 against a 50 ohm port placed at
  the launch plane behind an ideal 50 ohm line of the measured length.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

C0 = 299_792_458.0
MU0 = 4e-7 * np.pi
ETA0 = 376.730313668
Z_REF_OHM = 50.0
S11_PASSIVITY_LIMIT = 1.02          # PORT_INVALID if max|S11| above this on any plane
VALID_REL_DB = -20.0                # |u_inc| within 20 dB of the peak
LOW_ENERGY_REL = 1e-3               # |U_B| below this fraction of its maximum is a voltage node/noise -> fallback
CONTINUITY_WINDOW = 21
CONTINUITY_REL_TOL = 0.15
FALLBACK_REASONS = {0: "estimator", 1: "abs(Re cos(beta D)) > 1", 2: "abs(U_B) negligible (voltage node / no signal)",
                    3: "eps_eff outside [1, eps_r]", 4: "outlier against the running median (continuity)",
                    5: "non-finite"}
PROBE_FILES = {"U_A": "port_ut_1A", "U_B": "port_ut_1B", "U_C": "port_ut_1C", "I_A": "port_it_1A", "I_B": "port_it_1B"}

POSTPROCESS_MODEL = (
    "MSL edge port post-processing (em/port_postprocess.py): U = U_B, I = mean(I_A, I_B) / cos(beta D / 2); beta from "
    "cos(beta D) = (U_A + U_C) / (2 U_B) (three equispaced voltage probes, valid for any mixture of waves, no current needed; "
    "analytic Hammerstad-Jensen + Getsinger eps_eff fallback recorded per frequency); fixed 50 ohm reference "
    "(a = (U + 50 I) / 2, S11 = (U - a) / a, Zin = U / I) at the measurement plane (s11_measplane.csv, the primary S11); "
    "the launch-plane S11 (s11_complex.csv) moves U, I to y = -sy/2 over an ideal lossless 50 ohm line with that beta. "
    "Line loss is neglected and a numerical Z_line different from 50 ohm is not calibrated. The openEMS Z_line/beta extraction "
    "(MSLPort.ReadUIData + CalcPort ref_plane_shift) is available only as a flagged diagnostic.")


# ---- microstrip analytics -------------------------------------------------------------------------
def hammerstad_jensen(w_mm, h_mm, er):
    """Static eps_eff and Z0 (ohm) of a microstrip of width w on a substrate of height h (Hammerstad-Jensen)."""
    u = float(w_mm) / float(h_mm)
    a = 1 + np.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + np.log(1 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    eeff = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    f_u = 6 + (2 * np.pi - 6) * np.exp(-(30.666 / u) ** 0.7528)
    z0 = ETA0 / (2 * np.pi * np.sqrt(eeff)) * np.log(f_u / u + np.sqrt(1 + (2 / u) ** 2))
    return float(eeff), float(z0)


def getsinger_eeff(freq_hz, w_mm, h_mm, er):
    """Dispersive eps_eff(f) = eps_r - (eps_r - eps_eff0) / (1 + G (f / fp)^2), G = 0.6 + 0.009 Z0, fp = Z0 / (2 mu0 h)."""
    eeff0, z0 = hammerstad_jensen(w_mm, h_mm, er)
    g = 0.6 + 0.009 * z0
    fp = z0 / (2 * MU0 * h_mm * 1e-3)
    f = np.asarray(freq_hz, dtype=float)
    return er - (er - eeff0) / (1 + g * (f / fp) ** 2)


# ---- probe files ----------------------------------------------------------------------------------
def dft_probe(t, v, freq):
    """openEMS DFT_time2freq (pulse, single sided): 2 dt sum v exp(-j 2 pi f t)."""
    t, v, f = np.asarray(t, float), np.asarray(v, float), np.asarray(freq, float)
    return 2 * (t[1] - t[0]) * (np.exp(-2j * np.pi * np.outer(f, t)) @ v)


def read_probe(path):
    """Returns (t, v, header_y_m or None) of an openEMS probe file (time-domain, first two columns)."""
    path = Path(path)
    data = np.loadtxt(path, comments="%", ndmin=2)
    y = None
    for line in path.read_text().splitlines()[:6]:
        m = re.match(r"%\s*start-coordinates:\s*\(([^)]*)\)", line)
        if m:
            y = float(m.group(1).split(",")[1])
            break
    return data[:, 0], data[:, 1], y


class MslProbes:
    """The five time-domain probe signals of an MSL port plus the geometry needed to analyse them."""

    def __init__(self, run_dir, probe_lines_y_mm=None):
        self.run_dir = Path(run_dir)
        self.t, self.v, ys = {}, {}, {}
        for key, name in PROBE_FILES.items():
            self.t[key], self.v[key], ys[key] = read_probe(self.run_dir / name)
        self.header_y_m = ys
        if probe_lines_y_mm is not None:           # full-precision grid lines from prepared.json
            y_mm = [float(v) for v in probe_lines_y_mm]
            for key, y in zip(("U_A", "U_B", "U_C"), y_mm):
                if ys[key] is not None and abs(ys[key] - y * 1e-3) > 2e-8:
                    raise ValueError(f"probe header y ({ys[key]} m) disagrees with prepared.json ({y} mm) for {key}")
        else:
            y_mm = [ys[k] * 1e3 for k in ("U_A", "U_B", "U_C")]
        self.y_mm = y_mm
        self.delta_ab_m, self.delta_bc_m = (y_mm[1] - y_mm[0]) * 1e-3, (y_mm[2] - y_mm[1]) * 1e-3
        if not (self.delta_ab_m > 0 and self.delta_bc_m > 0):
            raise ValueError("voltage probe lines must be increasing along +y")
        self.delta_m = 0.5 * (self.delta_ab_m + self.delta_bc_m)
        self.delta_nonuniformity = abs(self.delta_ab_m - self.delta_bc_m) / self.delta_m
        self.sha256 = {name: _sha(self.run_dir / name) for name in PROBE_FILES.values()}

    def spectra(self, freq):
        return {k: dft_probe(self.t[k], self.v[k], freq) for k in PROBE_FILES}


def _sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- beta estimator -------------------------------------------------------------------------------
def estimate_beta(u_a, u_b, u_c, delta_m, freq, eeff_fallback, er):
    """beta from cos(beta D) = (U_A + U_C) / (2 U_B). Returns a dict (arrays over freq):
    eeff_estimate (nan where unusable), reason (int codes, FALLBACK_REASONS), fallback (bool), eeff, beta (rad/m, real)."""
    f = np.asarray(freq, float)
    u_a, u_b, u_c = (np.asarray(x, complex) for x in (u_a, u_b, u_c))
    with np.errstate(all="ignore"):
        cosv = (u_a + u_c) / (2 * u_b)
        c = cosv.real
        theta = np.arccos(np.clip(c, -1.0, 1.0))          # beta*D in [0, pi]
        eeff_raw = (theta * C0 / (2 * np.pi * f * delta_m)) ** 2
    reason = np.zeros(len(f), int)
    nonfinite = ~(np.isfinite(cosv) & np.isfinite(eeff_raw))
    ub = np.abs(u_b)
    small = ub < LOW_ENERGY_REL * np.nanmax(ub) if np.any(np.isfinite(ub)) and np.nanmax(ub) > 0 else np.ones(len(f), bool)
    over = np.abs(c) > 1.0
    outside = (eeff_raw < 1.0) | (eeff_raw > er)
    reason[nonfinite] = 5
    reason[outside] = 3
    reason[over] = 1
    reason[small] = 2
    est = np.where(reason == 0, eeff_raw, np.nan)
    # continuity: compare with the running median of the usable neighbours (only if enough samples)
    n = len(f)
    if n >= 7:
        half = min(CONTINUITY_WINDOW, n if n % 2 else n - 1) // 2
        for k in range(n):
            if reason[k] != 0:
                continue
            win = est[max(0, k - half):k + half + 1]
            win = win[np.isfinite(win)]
            if len(win) >= 5 and abs(est[k] - np.median(win)) > CONTINUITY_REL_TOL * np.median(win):
                reason[k] = 4
        est = np.where(reason == 0, eeff_raw, np.nan)
    fallback = reason != 0
    eeff = np.where(fallback, np.asarray(eeff_fallback, float), est)
    beta = 2 * np.pi * f * np.sqrt(eeff) / C0
    return {"eeff_estimate": est, "reason": reason, "fallback": fallback, "eeff": eeff, "beta": beta,
            "imag_cos_max": float(np.nanmax(np.abs(cosv.imag))) if np.any(np.isfinite(cosv)) else float("nan")}


# ---- wave quantities ------------------------------------------------------------------------------
def waves(u, i, z=Z_REF_OHM):
    """Fixed-reference decomposition: a = (U + Z I) / 2, b = U - a. Returns (inc, ref, s11, zin)."""
    inc = 0.5 * (u + z * i)
    ref = u - inc
    with np.errstate(all="ignore"):
        return inc, ref, ref / inc, u / i


def shift_to_launch(u, i, beta, length_m, z=Z_REF_OHM):
    """Move (U, I) by length_m towards the source over an ideal lossless line (impedance z, propagation constant j beta)."""
    th = np.real(beta) * length_m
    return u * np.cos(th) + 1j * z * i * np.sin(th), i * np.cos(th) + 1j * u / z * np.sin(th)


class PortPlanes:
    """Port quantities at the measurement plane (primary) and the launch plane (ideal-line shift)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def msl_planes(spectra, delta_m, length_m, freq, eeff_fallback, er, z=Z_REF_OHM, current_correction=True):
    """Pure function: probe spectra (dict U_A, U_B, U_C, I_A, I_B at the same frequencies) -> PortPlanes."""
    f = np.asarray(freq, float)
    est = estimate_beta(spectra["U_A"], spectra["U_B"], spectra["U_C"], delta_m, f, eeff_fallback, er)
    i_mean = 0.5 * (np.asarray(spectra["I_A"], complex) + np.asarray(spectra["I_B"], complex))
    i_b = i_mean / np.cos(0.5 * est["beta"] * delta_m) if current_correction else i_mean
    u_b = np.asarray(spectra["U_B"], complex)
    inc_m, ref_m, s_m, z_m = waves(u_b, i_b, z)
    u_l, i_l = shift_to_launch(u_b, i_b, est["beta"], length_m, z)
    inc_l, ref_l, s_l, z_l = waves(u_l, i_l, z)
    return PortPlanes(
        freq=f, eeff=est["eeff"], beta=est["beta"], beta_fallback=est["fallback"], beta_reason=est["reason"],
        eeff_estimate=est["eeff_estimate"], imag_cos_max=est["imag_cos_max"], length_m=length_m, reference_ohm=z,
        u_meas=u_b, i_meas=i_b, inc_meas=inc_m, ref_meas=ref_m, s11_meas=s_m, zin_meas=z_m,
        u_launch=u_l, i_launch=i_l, inc_launch=inc_l, ref_launch=ref_l, s11_launch=s_l, zin_launch=z_l,
        p_inc=np.abs(inc_m) ** 2 / (2 * z), p_acc=0.5 * np.real(u_b * np.conj(i_b)))


def legacy_openems_zline(spectra, delta_m, length_m, freq=None, z_ref=Z_REF_OHM):
    """DIAGNOSTIC ONLY: the extraction of openEMS MSLPort.ReadUIData + Port.CalcPort(ref_plane_shift=0) + renormalisation to
    z_ref, re-implemented in numpy (this is the method that gave |S11| up to 1.26 in P02_MS1_OPENEMS_006)."""
    et = np.asarray(spectra["U_B"], complex)
    d_et = (np.asarray(spectra["U_C"], complex) - np.asarray(spectra["U_A"], complex)) / (2 * delta_m)
    ht = 0.5 * (np.asarray(spectra["I_A"], complex) + np.asarray(spectra["I_B"], complex))
    d_ht = (np.asarray(spectra["I_B"], complex) - np.asarray(spectra["I_A"], complex)) / delta_m
    with np.errstate(all="ignore"):
        beta = np.sqrt(-d_et * d_ht / (ht * et))
        beta = np.where(beta.real < 0, -beta, beta)
        z_line = np.sqrt(et * d_et / (ht * d_ht))
        th = beta.real * length_m
        u = et * np.cos(th) + 1j * ht * z_line * np.sin(th)
        i = ht * np.cos(th) + 1j * et / z_line * np.sin(th)
        inc, ref, s11, zin = waves(u, i, z_ref)
        eeff = None if freq is None else (beta.real * C0 / (2 * np.pi * np.asarray(freq, float))) ** 2
    return {"beta": beta, "z_line": z_line, "u": u, "i": i, "inc": inc, "ref": ref, "s11": s11, "zin": zin, "eeff": eeff}


# ---- validity gate --------------------------------------------------------------------------------
def port_gate(s11_by_plane, p_acc, limit=S11_PASSIVITY_LIMIT):
    """PORT_INVALID if max|S11| > limit on any plane or P_acc < 0 at any evaluated frequency.

    s11_by_plane: {plane name: complex array}; p_acc: real array (all evaluated frequencies, already restricted by the
    caller to the channel grid plus the wideband rows inside the valid excitation range)."""
    max_s = {k: float(np.max(np.abs(v))) for k, v in s11_by_plane.items()}
    min_p = float(np.min(p_acc))
    reasons = [f"max|S11| on {k} = {v:.4f} > {limit}" for k, v in max_s.items() if not v <= limit]
    if not min_p >= 0:
        reasons.append(f"P_acc = {min_p:.3e} W < 0")
    if not np.all(np.isfinite(p_acc)):
        reasons.append("non-finite P_acc")
    return {"port_validity": "PORT_INVALID" if reasons else "OK", "s11_abs_limit": limit, "max_abs_s11_by_plane": max_s,
            "min_p_acc_W": min_p, "reasons": reasons,
            "rule": "PORT_INVALID if max|S11| > 1.02 on any plane or P_acc < 0 at any evaluated frequency "
                    "(channel grid + wideband rows inside the valid excitation range)"}
