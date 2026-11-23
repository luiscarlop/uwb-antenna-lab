"""array_virtual_monostatic.py: positions/multiplicities of the bistatic and bistatic + monostatic schemes (N = 5),
consistency with virtual_array_pattern.virtual_beam and a synthetic isotropic case."""
import importlib.util
import sys
import unittest

import numpy as np

from hfss_paths import ANALYSIS

sys.path.insert(0, str(ANALYSIS))
spec = importlib.util.spec_from_file_location("array_virtual_monostatic", ANALYSIS / "array_virtual_monostatic.py")
avm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(avm)
import virtual_array_pattern as vap  # noqa: E402

D = 0.0182
N = 5
X = (np.arange(N) - (N - 1) / 2) * D


def in_pitch(pos):
    return {round(p / D): m for p, m in pos.items()}


def isotropic_fields(freq_ghz, th_step=5):
    th = np.arange(0, 181, th_step, dtype=float)
    ph = np.arange(0, 361, th_step, dtype=float)
    T, P = np.meshgrid(np.radians(th), np.radians(ph), indexing="ij")
    k = 2 * np.pi * freq_ghz * 1e9 / vap.C0
    return th, ph, np.array([np.exp(1j * k * x * np.sin(T) * np.cos(P)) for x in X]), k


class Schemes(unittest.TestCase):
    def test_counts(self):
        a, b, c = (avm.channels_bistatic_current(N), avm.channels_bi_plus_mono(N), avm.channels_mono_only(N))
        self.assertEqual((len(vap.default_sequence(N)), len(a)), (30, 60))
        self.assertEqual((avm.n_acquisitions("bistatic_plus_monostatic", N), len(b)), (20, 40))
        self.assertEqual(len(c), 5)
        self.assertEqual(sum(t == r for t, r in b), 20)  # one monostatic channel per acquisition

    def test_positions_and_multiplicity_bistatic_current(self):
        pos = in_pitch(avm.channel_positions(avm.channels_bistatic_current(N), X))
        self.assertEqual(pos, {-3: 6, -2: 6, -1: 12, 0: 12, 1: 12, 2: 6, 3: 6})

    def test_positions_and_multiplicity_bistatic_plus_monostatic(self):
        pos = in_pitch(avm.channel_positions(avm.channels_bi_plus_mono(N), X))
        self.assertEqual(pos, {-4: 4, -3: 2, -2: 6, -1: 4, 0: 8, 1: 4, 2: 6, 3: 2, 4: 4})
        self.assertEqual(sum(pos.values()), 40)
        mono = in_pitch(avm.channel_positions(avm.channels_mono_only(N), X))  # 2 x_t: -4d, -2d, 0, 2d, 4d
        self.assertEqual(mono, {-4: 1, -2: 1, 0: 1, 2: 1, 4: 1})

    def test_generic_beam_equals_virtual_beam(self):
        rng = np.random.default_rng(1)
        F = rng.normal(size=(N, 7, 9)) + 1j * rng.normal(size=(N, 7, 9))
        k = 2 * np.pi * 7.9872e9 / vap.C0
        H = avm.pair_products(F)
        for st in (0.0, 30.0):
            ref = vap.virtual_beam(F, X, k, vap.default_sequence(N), st)
            got = avm.channel_beam(H, X, k, avm.channels_bistatic_current(N), st)
            np.testing.assert_allclose(got, ref, atol=1e-9)


class IsotropicCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = 8.2368
        th, ph, F, k = isotropic_fields(cls.f)
        cls.res = avm.analyse(F, th, ph, X, cls.f, D, mono_only=True, grid=False)

    def test_hpbw_b_narrower_than_a(self):
        for st in ("theta0_0deg", "theta0_30deg"):
            a = self.res["bistatic_current"]["beams"][st]["xz"]
            b = self.res["bistatic_plus_monostatic"]["beams"][st]["xz"]
            self.assertLess(b["hpbw_deg"], a["hpbw_deg"])
        self.assertEqual(self.res["bistatic_current"]["beams"]["theta0_0deg"]["xz"]["peak_deg"], 0.0)

    def test_cut_lobes_hpbw_matches_cut_metrics(self):
        th = np.arange(-90, 91, 5.0)
        db = 20 * np.log10(np.maximum(np.abs(np.sinc(np.sin(np.radians(th)) * 2.0)), 1e-6))
        m, l = vap.cut_metrics(th, db), avm.cut_lobes(th, db)
        self.assertEqual(m["hpbw_deg"], l["hpbw_deg"])
        self.assertAlmostEqual(m["max_sidelobe_db"], l["max_sidelobe_db"])

    def test_no_true_grating_lobe_d18p2_at_30deg_for_a_and_b_but_yes_for_mono_only(self):
        for s in ("bistatic_current", "bistatic_plus_monostatic"):
            xz = self.res[s]["beams"]["theta0_30deg"]["xz"]
            self.assertEqual(xz["grating_lobes"], [], s)
            self.assertFalse(xz["grating_lobe_present"], s)
        m = self.res["monostatic_only"]["beams"]["theta0_30deg"]["xz"]
        self.assertTrue(m["grating_lobe_present"])
        self.assertAlmostEqual(m["grating_lobes"][0]["theta_deg"], -30.0, delta=0.1)
        # b has the quasi-grating of the 2d (monostatic) subset at the same angle, as a sidelobe
        q = self.res["bistatic_plus_monostatic"]["beams"]["theta0_30deg"]["xz"]["quasi_grating_lobes_2d_subset"]
        self.assertAlmostEqual(q[0]["theta_deg"], -30.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
