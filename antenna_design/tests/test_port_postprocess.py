"""Synthetic fixtures only (numpy): MSL port post-processing of em/port_postprocess.py and the pure helpers of
em/patch_openems.py. No openEMS/CSXCAD, no solver or campaign output files."""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

EM = Path(__file__).resolve().parents[1] / "em"
sys.path.insert(0, str(EM))
import port_postprocess as pp  # noqa: E402
import patch_openems as po  # noqa: E402

W_MM, H_MM, ER = 3.02, 1.6, 4.4
Z0 = 50.0
DELTA = 0.48895e-3          # probe spacing (m), as in P02_MS1_OPENEMS_006
LENGTH = 4.8895e-3          # measurement plane to launch plane (m)


def synthetic_line(freq, gamma, eeff, scale=None, delta=DELTA, length=LENGTH, z0=Z0):
    """Probe spectra of an ideal lossless line, forward wave of unit amplitude at the LAUNCH plane and reflection coefficient
    gamma(f) there: U(s) = a (e^{-j b s} + G e^{+j b s}), I(s) = a (e^{-j b s} - G e^{+j b s}) / z0, s = distance from the launch plane.
    Voltage probes at s = L - D, L, L + D; current probes at s = L -+ D / 2 (as in openEMS MSLPort)."""
    f = np.asarray(freq, float)
    b = 2 * np.pi * f * np.sqrt(eeff) / pp.C0
    a = np.ones(len(f), complex) if scale is None else scale

    def u(s):
        return a * (np.exp(-1j * b * s) + gamma * np.exp(1j * b * s))

    def i(s):
        return a * (np.exp(-1j * b * s) - gamma * np.exp(1j * b * s)) / z0
    return {"U_A": u(length - delta), "U_B": u(length), "U_C": u(length + delta),
            "I_A": i(length - delta / 2), "I_B": i(length + delta / 2)}, b


class TestBetaAndS11(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.f = np.linspace(6.5e9, 9.0e9, 101)
        self.eeff = pp.getsinger_eeff(self.f, W_MM, H_MM, ER)
        self.gamma = 0.92 * np.exp(1j * rng.uniform(-np.pi, np.pi, len(self.f)))
        self.scale = 3.7e-3 * np.exp(1j * rng.uniform(-np.pi, np.pi, len(self.f)))
        self.spectra, self.beta = synthetic_line(self.f, self.gamma, self.eeff, self.scale)

    def run_planes(self, **kw):
        return pp.msl_planes(self.spectra, DELTA, LENGTH, self.f, pp.getsinger_eeff(self.f, W_MM, H_MM, ER) * 1.1, ER, **kw)

    def test_recovers_eeff_and_both_planes_under_strong_standing_wave(self):
        pl = self.run_planes()
        self.assertFalse(pl.beta_fallback.any())
        self.assertLess(np.max(np.abs(pl.eeff - self.eeff)), 1e-6)
        self.assertLess(np.max(np.abs(pl.beta - self.beta) / self.beta), 1e-6)
        self.assertLess(np.max(np.abs(pl.s11_launch - self.gamma)), 1e-6)
        self.assertLess(np.max(np.abs(pl.s11_meas - self.gamma * np.exp(2j * self.beta * LENGTH))), 1e-6)
        zin = Z0 * (1 + self.gamma) / (1 - self.gamma)
        self.assertLess(np.max(np.abs(pl.zin_launch - zin) / np.abs(zin)), 1e-6)
        self.assertLess(np.max(np.abs(np.abs(pl.s11_meas) - 0.92)), 1e-6)       # the shift does not change the modulus
        self.assertLess(np.max(np.abs(np.abs(pl.s11_launch) - np.abs(pl.s11_meas))), 1e-12)

    def test_power_quantities_at_measurement_plane(self):
        pl = self.run_planes()
        a = self.scale * np.exp(-1j * self.beta * LENGTH)                       # forward wave at the measurement plane
        p_inc = np.abs(a) ** 2 / (2 * Z0)
        self.assertLess(np.max(np.abs(pl.p_inc / p_inc - 1)), 1e-6)
        self.assertLess(np.max(np.abs(pl.p_acc / (p_inc * (1 - 0.92 ** 2)) - 1)), 1e-6)
        self.assertTrue(np.all(pl.p_acc > 0))

    def test_current_average_correction_matters(self):
        err_on = np.max(np.abs(self.run_planes(current_correction=True).s11_launch - self.gamma))
        err_off = np.max(np.abs(self.run_planes(current_correction=False).s11_launch - self.gamma))
        self.assertLess(err_on, 1e-6)
        self.assertGreater(err_off, 1e-4)        # mean(I_A, I_B) is cos(beta D / 2) ~ 0.997 of the current at B

    def test_node_and_out_of_range_fall_back_to_analytic_eeff(self):
        spectra = {k: v.copy() for k, v in self.spectra.items()}
        spectra["U_B"][10] = 0.0                                   # no signal / exact node
        spectra["U_A"][20] = spectra["U_C"][20] = 1.5 * spectra["U_B"][20]   # |cos| > 1
        fallback = self.eeff * 1.1
        pl = pp.msl_planes(spectra, DELTA, LENGTH, self.f, fallback, ER)
        self.assertTrue(pl.beta_fallback[10] and pl.beta_fallback[20])
        self.assertEqual(pl.beta_reason[10], 2)
        self.assertEqual(pl.beta_reason[20], 1)
        self.assertAlmostEqual(pl.eeff[10], fallback[10], places=12)
        self.assertAlmostEqual(pl.eeff[20], fallback[20], places=12)
        self.assertEqual(int(pl.beta_fallback.sum()), 2)
        ok = ~pl.beta_fallback
        self.assertLess(np.max(np.abs(pl.eeff[ok] - self.eeff[ok])), 1e-6)

    def test_continuity_flags_isolated_outlier(self):
        spectra = {k: v.copy() for k, v in self.spectra.items()}
        # corrupt one sample so that its eps_eff is 40 % off but |cos| < 1 and eps_eff in [1, eps_r]
        theta = 2 * np.pi * self.f[50] * np.sqrt(self.eeff[50] * 0.6) / pp.C0 * DELTA
        spectra["U_A"][50] = spectra["U_C"][50] = np.cos(theta) * spectra["U_B"][50]
        pl = pp.msl_planes(spectra, DELTA, LENGTH, self.f, self.eeff, ER)
        self.assertEqual(pl.beta_reason[50], 4)

    def test_loss_free_shift_is_unitary(self):
        u = np.array([1 + 2j]); i = np.array([0.01 - 0.003j])
        u2, i2 = pp.shift_to_launch(u, i, np.array([300.0]), 3e-3)
        p1 = 0.5 * np.real(u * np.conj(i)); p2 = 0.5 * np.real(u2 * np.conj(i2))
        self.assertAlmostEqual(float(p1[0]), float(p2[0]), places=12)


class TestGate(unittest.TestCase):
    def test_s11_above_limit_is_invalid(self):
        gate = pp.port_gate({"measurement": np.array([0.5, 1.1 * np.exp(0.3j)]), "launch": np.array([0.4])}, np.array([1e-3, 2e-3]))
        self.assertEqual(gate["port_validity"], "PORT_INVALID")
        self.assertTrue(any("measurement" in r for r in gate["reasons"]))

    def test_negative_p_acc_is_invalid_even_if_passive_looking(self):
        gate = pp.port_gate({"measurement": np.array([0.9])}, np.array([1e-3, -1e-9]))
        self.assertEqual(gate["port_validity"], "PORT_INVALID")

    def test_active_synthetic_line_trips_both_conditions(self):
        f = np.linspace(7.5e9, 8.5e9, 11)
        eeff = pp.getsinger_eeff(f, W_MM, H_MM, ER)
        spectra, _ = synthetic_line(f, np.full(len(f), 1.1 * np.exp(0.7j)), eeff)
        pl = pp.msl_planes(spectra, DELTA, LENGTH, f, eeff, ER)
        gate = pp.port_gate({"measurement": pl.s11_meas, "launch": pl.s11_launch}, pl.p_acc)
        self.assertEqual(gate["port_validity"], "PORT_INVALID")
        self.assertEqual(len(gate["reasons"]), 3)       # both planes + P_acc

    def test_passive_line_is_ok_and_limit_is_1p02(self):
        f = np.linspace(7.5e9, 8.5e9, 11)
        eeff = pp.getsinger_eeff(f, W_MM, H_MM, ER)
        spectra, _ = synthetic_line(f, np.full(len(f), 0.92 * np.exp(0.7j)), eeff)
        pl = pp.msl_planes(spectra, DELTA, LENGTH, f, eeff, ER)
        self.assertEqual(pp.port_gate({"measurement": pl.s11_meas, "launch": pl.s11_launch}, pl.p_acc)["port_validity"], "OK")
        self.assertEqual(pp.S11_PASSIVITY_LIMIT, 1.02)
        self.assertEqual(pp.port_gate({"p": np.array([1.02])}, np.array([1.0]))["port_validity"], "OK")


class TestHelpers(unittest.TestCase):
    def test_hammerstad_jensen_50_ohm_fr4(self):
        eeff, z0 = pp.hammerstad_jensen(W_MM, H_MM, ER)
        self.assertAlmostEqual(eeff, 3.33, delta=0.02)
        self.assertAlmostEqual(z0, 50.0, delta=1.0)
        self.assertGreater(float(pp.getsinger_eeff(8e9, W_MM, H_MM, ER)), eeff)    # dispersion raises eps_eff

    def test_dft_convention_matches_openems_single_sided(self):
        t = np.arange(0, 2e-9, 1e-12); t0, sig = 1e-9, 1e-10
        v = np.exp(-((t - t0) / sig) ** 2)
        f = np.array([0.0, 2e9, 8e9])
        exact = 2 * sig * np.sqrt(np.pi) * np.exp(-(np.pi * f * sig) ** 2) * np.exp(-2j * np.pi * f * t0)
        self.assertLess(np.max(np.abs(pp.dft_probe(t, v, f) - exact)), 1e-6 * np.abs(exact).max())

    def test_read_probe_header_and_probe_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name, y in zip(pp.PROBE_FILES.values(), (-0.0086, -0.0081, -0.0076, -0.0086, -0.0081)):
                lines = ["% time-domain voltage integration by openEMS", f"% start-coordinates: (0,{y},0.0016) m -> [1,2,3]",
                         f"% stop-coordinates: (0,{y},0) m -> [1,2,3]"]
                lines += [f"{k * 1e-11:.6e} {np.sin(k):.6e}" for k in range(20)]
                (tmp / name).write_text("\n".join(lines) + "\n")
            probes = pp.MslProbes(tmp)
            self.assertAlmostEqual(probes.delta_m, 0.5e-3, places=12)
            self.assertAlmostEqual(probes.delta_nonuniformity, 0.0, places=9)
            self.assertEqual(probes.spectra(np.array([1e9, 2e9]))["U_B"].shape, (2,))
            with self.assertRaises(ValueError):
                pp.MslProbes(tmp, [-8.6, -8.1, -7.7])             # prepared.json lines disagree with the headers

    def test_wideband_grid_default_is_the_pre_round7_grid(self):
        old = np.arange(6.98e9, 9.0e9 + 2.5e6, 5e6)
        new = po.wideband_grid(1e9)
        self.assertEqual(new.shape, old.shape)
        self.assertTrue(np.array_equal(new, old))

    def test_wideband_grid_follows_excitation(self):
        grid = po.wideband_grid(2.5e9)
        self.assertLessEqual(grid[0], 5.5e9)
        self.assertGreaterEqual(grid[-1], 9.5e9)
        lo, hi = po.nominal_valid_range_hz(2.5e9)
        self.assertAlmostEqual(lo, po.F0_HZ - 1.0116 * 2.5e9, delta=1e6)
        self.assertAlmostEqual(hi, po.F0_HZ + 1.0116 * 2.5e9, delta=1e6)


class TestQwFeedVariant(unittest.TestCase):
    """microstrip_edge_qw validation of variants/P03_MS2.json (pure python, no solver)."""
    path = Path(__file__).resolve().parents[1] / "variants" / "P03_MS2.json"

    def load(self, mutate=None):
        import copy
        import json
        data = json.loads(self.path.read_text())
        if mutate:
            mutate(data)
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "v.json"
            f.write_text(json.dumps(copy.deepcopy(data)))
            return po.load_variant(f)

    def test_p03_ms2_loads_and_has_two_feed_rectangles(self):
        data, poly, slots = self.load()
        self.assertEqual(data["feed"]["type"], po.EDGE_QW_FEED)
        rects = po.feed_rectangles(data["feed"])
        self.assertEqual(len(rects), 2)
        self.assertEqual(len(slots), 1)

    def test_inconsistent_transformer_is_rejected(self):
        with self.assertRaises(ValueError):
            self.load(lambda d: d["feed"].update(transformer_length_mm=5.0))
        with self.assertRaises(ValueError):
            self.load(lambda d: d["feed"].update(transformer_start_y_mm=-6.0))

    def test_qw_mesh_extras(self):
        data, poly, slots = self.load()
        hard, plain = po.qw_mesh_extras(data["feed"], po.feed_rectangles(data["feed"]), slots, {})
        self.assertIn(-6.076922, hard["y"]); self.assertIn(-0.856922, hard["y"]); self.assertIn(0.0, hard["x"])
        self.assertGreaterEqual(len(plain["y"]) + 1, 6)


if __name__ == "__main__":
    unittest.main()
