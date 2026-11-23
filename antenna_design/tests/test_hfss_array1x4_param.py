"""Parametric 1x4 P01_MS2 array (owner request 2026-11-17): same element and arr_d scheme as the 1x5 P01_MS2."""
import unittest
from pathlib import Path

from hfss_paths import build_path
from test_hfss_us3_ps4 import FakeAedt, kv


class Array1x4Param(unittest.TestCase):
    def setUp(self):
        self.src = (build_path("claude_aedt_array1x4_P01_MS2_param_ch9.py")).read_text()

    def test_defaults(self):
        self.assertIn("DESIGNS_TO_BUILD = ['P01_MS2']", self.src)
        self.assertIn("PITCHES_MM = [17.0]", self.src)
        self.assertIn("PARAMETRIC_PITCH = True", self.src)
        self.assertIn("N_ELEM = 4", self.src)
        self.assertIn("ARR1x4_P01_MS2_dparam", self.src)

    def test_four_ports_parametric_positions(self):
        fake = FakeAedt()
        fake.run(self.src)
        self.assertEqual(len(fake.of("AssignFiniteCond")), 5)  # Ground + 4 patches (P01_MS2 has no parasitic)
        ports = fake.of("AssignLumpedPort")
        self.assertEqual(len(ports), 4)
        for i, a in enumerate(ports):
            self.assertEqual(a[0][0], f"NAME:P{i + 1}")
            self.assertEqual(kv(a[0], "Start:=")[0], f"({i - 1.5})*arr_d")
            self.assertEqual(kv(a[0], "Objects:="), [f"PortSheet_{i + 1}"])

    def test_setup_and_sweeps_match_the_1x5_p01_ms2(self):
        mine, ref = FakeAedt(), FakeAedt()
        mine.run(self.src)
        ref.run((build_path("claude_aedt_array1x5_P01_MS2_param_ch9.py")).read_text())
        self.assertEqual(mine.of("InsertSetup"), ref.of("InsertSetup"))
        self.assertEqual(mine.of("InsertFrequencySweep"), ref.of("InsertFrequencySweep"))


if __name__ == "__main__":
    unittest.main()
