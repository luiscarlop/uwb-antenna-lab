"""P01_MS1 geometry guide (round 25). GUIDE_MODEL / GEOMETRY_ONLY: no S11 is claimed.

L: EM-calibrated L*fr scaling. US0 (plain rectangle, h 2.07 mm, ideal probe, fine mesh) fit fr 7.625 GHz at L 7.67 mm.
The same L*fr scaling took US3 (probe, L 6.85, fr 7.581 GHz) to US3_MS2 (edge feed, L 6.502): EM patch-edge fit fr 7.935 GHz
(-0.65 % vs f0) and port-plane fit 8.043 GHz (+0.70 %); with the lambda/4 (US3_MS3) the channel minimum landed at 7.98 GHz.
R_edge: transmission-line model (Balanis G1, G12 by numerical integration) for the plain rectangle, compared with the EM
edge fit of the U-slot (US3_MS2, 243-296 ohm). Feed: identical to US3_MS3 (single-variable comparison: the patch).
"""
import json, math
import numpy as np


def quad(fn, a, b, n=20001):
    t = np.linspace(a, b, n)
    return (np.trapezoid(fn(t), t),)


def j0(x):
    tau = np.linspace(0, np.pi, 2001)
    return np.trapezoid(np.cos(np.multiply.outer(x, np.sin(tau))), tau, axis=-1) / np.pi

f0 = 7.9872e9; c = 299792458.0
L_US0, fr_US0 = 7.67, 7.625e9
L = L_US0 * fr_US0 / f0
L_chosen = round(L, 3)
W = 11.421266e-3; h = 2.07e-3
k0 = 2 * math.pi * f0 / c
G1 = quad(lambda t: (np.sin(k0 * W / 2 * np.cos(t)) / np.cos(t)) ** 2 * np.sin(t) ** 3, 1e-9, math.pi - 1e-9)[0] / (120 * math.pi ** 2)
Lm = L_chosen * 1e-3
G12 = quad(lambda t: (np.sin(k0 * W / 2 * np.cos(t)) / np.cos(t)) ** 2 * j0(k0 * Lm * np.sin(t)) * np.sin(t) ** 3, 1e-9, math.pi - 1e-9)[0] / (120 * math.pi ** 2)
R_edge_tl = 1 / (2 * (G1 + G12))
Zt = 102.5
out = {
    "evidence": "GUIDE_MODEL (not EM)",
    "L_scaled_mm": L, "L_chosen_mm": L_chosen,
    "L_uncertainty": "+-0.7 % in fr (US3 -> US3_MS2 scaling check), ~+-55 MHz",
    "G1_S": G1, "G12_S": G12, "R_edge_TL_model_ohm": R_edge_tl,
    "R_edge_EM_uslot_US3_MS2_ohm": [243, 296],
    "R_matched_by_Zt_102p5_ohm": Zt ** 2 / 50,
    "transformer": "unchanged from US3_MS3 (w 0.80 mm, l 6.60 mm, Zt ~102.5 ohm)",
    "note": "TL model ignores substrate thickness k0h~0.35 and fringing reactance; R_edge uncertainty order +-30 %.",
}
print(json.dumps(out, indent=1))
json.dump(out, open(__file__.replace('.py', '.json'), 'w'), indent=1)
