"""Element exporter (claude_aedt_export_element_ch9.py) and the optional convergence step of the array exporter,
against the fake AEDT of test_hfss_us3_ps4.py. No AEDT needed: this checks calls, file names, the variation used
and that one failing step does not abort the others. It does NOT prove the calls work in a real AEDT.
"""
import tempfile
import unittest
from pathlib import Path

from hfss_paths import EXPORT, set_design
from test_hfss_us3_ps4 import FakeAedt, kv

ELEMENT = EXPORT / "claude_aedt_export_element_ch9.py"
ARRAY = EXPORT / "claude_aedt_export_array_ch9.py"
VAR = "patch_L='6.222mm' sub_h='1.6mm' board_x='30mm'"
ANT = ["RadiationEfficiency", "RadiatedPower", "AcceptedPower", "IncidentPower",
       "PeakRealizedGain", "PeakGain", "PeakDirectivity"]


class FaultyAedt(FakeAedt):
    """FakeAedt that writes the files AEDT would write and raises where `fail(name, method, args)` is true."""

    def __init__(self, fail=None, **kw):
        FakeAedt.__init__(self, **kw)
        self.fail = fail or (lambda n, a, args: False)

    def rec(self, n):
        outer, inner = self, FakeAedt.rec(self, n)

        class Wrap:
            def __getattr__(self, a):
                f = getattr(inner, a)

                def g(*args):
                    res = f(*args)  # records the call (and writes ExportToFile)
                    if outer.fail(n, a, args):
                        raise RuntimeError("fallo simulado en " + a)
                    path = {"ExportConvergence": 2, "ExportProfile": 2, "ExportNetworkData": 3}.get(a)
                    if path is not None:
                        Path(args[path]).write_text("x")
                    return res
                return g
        return Wrap()


def reports_of(fake):
    return [c[2] for c in fake.calls if c[1] == "CreateReport"]


def ycomp(args):
    return kv(args[6], "Y Component:=")


class ElementExporter(unittest.TestCase):
    def run_script(self, fail=None, variations=(VAR,), nominal=VAR, design=None, replace=()):
        out = tempfile.mkdtemp()
        fake = FaultyAedt(fail=fail, out=out, nominal=nominal, variations=variations)
        src = ELEMENT.read_text()
        if design:
            src = src.replace('DESIGN = "US3_PS4_2_1"', 'DESIGN = "%s"' % design)
        for a, b in replace:
            self.assertIn(a, src)
            src = src.replace(a, b)
        fake.run(src)
        name = design or "US3_PS4_2_1"
        folder = Path(out) / "ch9_element_export" / name
        return fake, folder, (folder / "export_log.txt").read_text()

    def test_defaults_and_all_files(self):
        src = ELEMENT.read_text()
        compile(src, "x", "exec")
        for s in ('DESIGN = "US3_PS4_2_1"', 'OUT_DIR = ""', 'SETUP = "Setup_ch9"', 'SWEEP = "Sweep_7p5_8p5"',
                  'FF_SWEEP = "Edges_and_f0"', 'SPHERE = "FF_sphere"', 'PORT = "P1"'):
            self.assertIn(s, src)
        self.assertIn("NO se ha ejecutado en AEDT real", src)
        fake, folder, log = self.run_script(design="US3_PS6")
        for f in ("US3_PS6.s1p", "ff_P1.csv", "antenna_params.csv", "realized_gain_cuts.csv",
                  "convergence.conv", "profile.prof", "export_log.txt"):
            self.assertTrue((folder / f).is_file(), f)
        self.assertEqual(fake.of("SetActiveDesign")[0], ("US3_PS6",))
        self.assertEqual(fake.of("Save"), [()])
        self.assertLess([c[1] for c in fake.calls].index("Save"), [c[1] for c in fake.calls].index("ExportNetworkData"))
        self.assertIn("variacion usada: " + VAR, log)
        self.assertIn("sin errores", log)

    def test_calls_and_arguments(self):
        fake, folder, log = self.run_script()
        net = fake.of("ExportNetworkData")
        self.assertEqual(len(net), 1)
        self.assertEqual(net[0][0], VAR)  # exact string of GetAvailableVariations
        self.assertEqual(net[0][1], ["Setup_ch9:Sweep_7p5_8p5"])
        self.assertEqual(net[0][2], 3)
        self.assertEqual(net[0][3], str(folder / "US3_PS4_2_1.s1p"))
        self.assertEqual(net[0][4:10], (["all"], True, 50, "S", -1, 0))
        self.assertEqual(fake.of("GetAvailableVariations")[0], ("Setup_ch9 : Sweep_7p5_8p5",))
        # Edit Sources: 1 W in P1 before the fields and again at the end
        srcs = fake.of("EditSources")
        self.assertEqual(len(srcs), 2)
        for s in srcs:
            self.assertEqual(s[0][1], ["Name:=", "P1:1", "Magnitude:=", "1W", "Phase:=", "0deg"])
        names = [c[1] for c in fake.calls]
        self.assertLess(names.index("EditSources"), names.index("CreateReport"))
        last = len(names) - 1 - names[::-1].index("EditSources")
        self.assertGreater(last, max(i for i, n in enumerate(names) if n in ("ExportProfile", "ExportConvergence")))
        # three reports: far field, antenna parameters, gain cuts
        reps = reports_of(fake)
        self.assertEqual([r[1] for r in reps], ["Far Fields", "Antenna Parameters", "Far Fields"])
        self.assertTrue(all(r[2] == "Data Table" and r[3] == "Setup_ch9 : Edges_and_f0" for r in reps))
        self.assertTrue(all(r[4] == ["Context:=", "FF_sphere"] for r in reps))
        ff = reps[0]
        self.assertEqual(ycomp(ff), ["re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)"])
        self.assertEqual(kv(ff[6], "X Component:="), "Phi")
        self.assertEqual(kv(ff[5], "Phi:="), ["All"])
        self.assertEqual(kv(ff[5], "Theta:="), ["All"])
        self.assertEqual(kv(ff[5], "Freq:="), ["All"])
        self.assertEqual(kv(ff[5], "patch_L:="), ["6.222mm"])
        self.assertEqual(kv(ff[5], "board_x:="), ["30mm"])
        ap = reps[1]
        self.assertEqual(kv(ap[6], "X Component:="), "Freq")
        self.assertEqual(ycomp(ap), ANT)
        self.assertEqual(kv(ap[5], "Freq:="), ["All"])
        self.assertEqual(kv(ap[5], "patch_L:="), ["6.222mm"])
        self.assertIsNone(kv(ap[5], "Theta:="))
        self.assertEqual(ycomp(reps[2]), ["dB(GainTotal)", "dB(RealizedGainTotal)"])
        exports = [a[1] for a in fake.of("ExportToFile")]
        self.assertEqual(exports, [str(folder / f) for f in ("ff_P1.csv", "antenna_params.csv", "realized_gain_cuts.csv")])
        self.assertEqual(len(fake.of("DeleteReports")), 3)
        # convergence and profile: setup without sweep, "name=value,name=value"
        conv = fake.of("ExportConvergence")
        self.assertEqual(conv, [("Setup_ch9", "patch_L=6.222mm,sub_h=1.6mm,board_x=30mm", str(folder / "convergence.conv"))])
        prof = fake.of("ExportProfile")
        self.assertEqual(prof, [("Setup_ch9", "patch_L=6.222mm,sub_h=1.6mm,board_x=30mm", str(folder / "profile.prof"))])

    def test_variation_is_the_exact_available_string(self):
        avail = ["sub_h='1.6mm' patch_L='6mm' board_x='30mm'", "sub_h='1.6mm' board_x='30mm' patch_L='6.222mm'"]
        fake, folder, log = self.run_script(variations=avail, nominal=VAR)
        self.assertEqual(fake.of("ExportNetworkData")[0][0], avail[1])  # same values, other key order
        self.assertIn("variacion usada: " + avail[1], log)

    def test_unmatched_nominal_with_several_variations_exports_nothing(self):
        avail = ["patch_L='6mm'", "patch_L='7mm'"]
        fake, folder, log = self.run_script(variations=avail, nominal="patch_L='6.222mm'")
        self.assertEqual(fake.of("ExportNetworkData"), [])
        self.assertEqual(fake.of("CreateReport"), [])
        self.assertIn("ERR variacion", log)

    def test_failure_in_one_step_does_not_abort_the_others(self):
        fake, folder, log = self.run_script(fail=lambda n, a, args: a == "ExportNetworkData")
        self.assertFalse((folder / "US3_PS4_2_1.s1p").exists())
        for f in ("ff_P1.csv", "antenna_params.csv", "realized_gain_cuts.csv", "convergence.conv", "profile.prof"):
            self.assertTrue((folder / f).is_file(), f)
        self.assertEqual(len(fake.of("EditSources")), 2)
        self.assertIn("ERR Touchstone", log)
        self.assertIn("pasos fallidos: Touchstone", log)

    def test_antenna_params_falls_back_to_one_quantity_at_a_time(self):
        def fail(n, a, args):
            if a != "CreateReport" or args[1] != "Antenna Parameters":
                return False
            y = ycomp(args)
            return len(y) > 1 or y == ["PeakGain"]  # combined report rejected; PeakGain unknown
        fake, folder, log = self.run_script(fail=fail)
        self.assertFalse((folder / "antenna_params.csv").exists())
        for q in ANT:
            self.assertEqual((folder / ("antenna_params_%s.csv" % q)).is_file(), q != "PeakGain", q)
        self.assertTrue((folder / "ff_P1.csv").is_file())
        self.assertTrue((folder / "realized_gain_cuts.csv").is_file())
        self.assertTrue((folder / "convergence.conv").is_file())
        self.assertIn("6 de 7 cantidades", log)
        self.assertIn("antenna params PeakGain", log)
        # the temporary report is deleted after every attempt, failed or not
        self.assertEqual(len(fake.of("DeleteReports")), len(reports_of(fake)))

    def test_far_field_failure_keeps_the_rest(self):
        fake, folder, log = self.run_script(fail=lambda n, a, args: a == "CreateReport" and args[1] == "Far Fields"
                                            and len(ycomp(args)) == 4)
        self.assertFalse((folder / "ff_P1.csv").exists())
        self.assertTrue((folder / "antenna_params.csv").is_file())
        self.assertTrue((folder / "US3_PS4_2_1.s1p").is_file())
        self.assertIn("far field", log.split("pasos fallidos:")[1])

    def test_convergence_variation_candidates_and_optional_flags(self):
        # first candidate rejected -> second (empty = nominal) is tried and logged
        fake, folder, log = self.run_script(fail=lambda n, a, args: a == "ExportConvergence" and args[1] != "")
        self.assertEqual([c[1] for c in fake.of("ExportConvergence")], ["patch_L=6.222mm,sub_h=1.6mm,board_x=30mm", ""])
        self.assertTrue((folder / "convergence.conv").is_file())
        # ExportProfile with 3 arguments rejected -> the 4-argument form is used
        fake, folder, log = self.run_script(fail=lambda n, a, args: a == "ExportProfile" and len(args) == 3)
        self.assertEqual([len(c) for c in fake.of("ExportProfile")], [3, 4])
        # flags off
        fake, folder, log = self.run_script(replace=[("EXPORT_GAIN_CUTS = True", "EXPORT_GAIN_CUTS = False"),
                                                      ("EXPORT_CONVERGENCE = True", "EXPORT_CONVERGENCE = False")])
        self.assertEqual(len(reports_of(fake)), 2)
        self.assertEqual(fake.of("ExportConvergence"), [])
        self.assertFalse((folder / "realized_gain_cuts.csv").exists())

    def test_explicit_out_dir(self):
        out = tempfile.mkdtemp()
        other = tempfile.mkdtemp()
        fake = FaultyAedt(out=out, nominal=VAR, variations=[VAR])
        fake.run(ELEMENT.read_text().replace('OUT_DIR = ""', 'OUT_DIR = %r' % other))
        self.assertTrue((Path(other) / "US3_PS4_2_1" / "US3_PS4_2_1.s1p").is_file())
        self.assertFalse((Path(out) / "ch9_element_export").exists())


class ArrayConvergenceStep(unittest.TestCase):
    NAME = "ARR1x5_US3_PS4_2_1_dparam"
    VARS = ["arr_d='%gmm' board_x='%gmm'" % (d, 4 * d + 26) for d in (16.5, 17, 17.5, 18, 18.2, 18.5, 19, 19.5)]

    def run_script(self, fail=None, replace=()):
        out = tempfile.mkdtemp()
        fake = FaultyAedt(fail=fail, out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS)
        src = set_design(ARRAY.read_text(), self.NAME)
        for a, b in replace:
            self.assertIn(a, src)
            src = src.replace(a, b)
        fake.run(src)
        return fake, Path(out) / "ch9_array_export"

    def test_convergence_of_every_variation(self):
        self.assertIn("EXPORT_CONVERGENCE = True", ARRAY.read_text())
        fake, root = self.run_script()
        conv = fake.of("ExportConvergence")
        self.assertEqual(len(conv), 8)
        self.assertEqual(conv[0][:2], ("Setup_ch9", "arr_d=16.5mm,board_x=92mm"))
        self.assertEqual(conv[0][2], str(root / (self.NAME + "_d16p5mm") / "convergence.conv"))
        self.assertEqual(sorted(c[2] for c in conv), sorted(
            str(root / (self.NAME + "_d%smm" % t) / "convergence.conv")
            for t in ("16p5", "17", "17p5", "18", "18p2", "18p5", "19", "19p5")))
        for t in ("16p5", "18p2", "19p5"):
            self.assertTrue((root / (self.NAME + "_d%smm" % t) / "convergence.conv").is_file())
        self.assertEqual(len(fake.of("ExportNetworkData")), 8)  # the rest of the logic is unchanged
        self.assertEqual(len(fake.of("CreateReport")), 5)

    def test_flag_off_and_failure_does_not_abort(self):
        fake, root = self.run_script(replace=[("EXPORT_CONVERGENCE = True", "EXPORT_CONVERGENCE = False")])
        self.assertEqual(fake.of("ExportConvergence"), [])
        self.assertEqual(len(fake.of("ExportNetworkData")), 8)
        fake, root = self.run_script(fail=lambda n, a, args: a == "ExportConvergence")
        self.assertEqual(len(fake.of("ExportConvergence")), 16)  # two candidates per step, both rejected
        self.assertEqual(len(fake.of("ExportNetworkData")), 8)
        self.assertEqual(len(fake.of("CreateReport")), 5)
        self.assertTrue((root / (self.NAME + "_d18p2mm") / "ff_P1.csv").is_file())
        self.assertIn("ERR convergencia", (root / "export_log.txt").read_text())


class ExporterDesignBlock(unittest.TestCase):
    """Each exporter lists every design (one per line, one active) and N_PORTS is deduced from the array name."""
    ARRAYS = ["ARR1x5_P01_MS2_dparam", "ARR1x4_P01_MS2_dparam", "ARR1x5_US3_PS4_dparam", "ARR1x5_US3_PS6_dparam",
              "ARR1x5_US3_PS4_2_1_dparam", "ARR1x5_US3_PS6_4_dparam"]
    ELEMENTS = ["P01_MS1", "P01_MS2", "US3_MS3", "US3_PS4", "US3_PS6", "US3_PS4_2_1", "US3_PS6_4"]
    VARS = ["arr_d='%gmm' board_x='%gmm'" % (d, 3 * d + 26) for d in (16.5, 17, 17.5, 18, 18.2, 18.5, 19, 19.5)]

    def test_one_active_design_and_all_options_listed(self):
        fields = EXPORT / "claude_aedt_export_fields_ch9.py"
        for path, options in ((ARRAY, self.ARRAYS), (fields, self.ARRAYS), (ELEMENT, self.ELEMENTS)):
            lines = path.read_text().splitlines()
            active = [l for l in lines if l.startswith("DESIGN = ")]
            self.assertEqual(len(active), 1, path.name)
            for d in options:
                self.assertTrue(any(l.startswith(("DESIGN = ", "# DESIGN = ")) and '"%s"' % d in l for l in lines), (path.name, d))

    def test_long_pitch_grid_is_listed_commented_next_to_the_short_one(self):
        src = ARRAY.read_text()
        self.assertIn("# ARR_D_MM = [13.5 + 0.5 * i for i in range(15)] + [18.2]", src)
        self.assertIn("\nARR_D_MM = [16.5 + 0.5 * i for i in range(7)] + [18.2]", src)

    def run_array(self, design, replace=()):
        out = tempfile.mkdtemp()
        fake = FaultyAedt(out=out, nominal="arr_d='17mm' board_x='77mm'", variations=self.VARS)
        src = set_design(ARRAY.read_text(), design)
        for a, b in replace:
            self.assertIn(a, src)
            src = src.replace(a, b)
        fake.run(src)
        return fake, Path(out) / "ch9_array_export"

    def test_n_ports_deduced_from_the_name(self):
        for design, n in (("ARR1x4_P01_MS2_dparam", 4), ("ARR1x5_P01_MS2_dparam", 5)):
            fake, root = self.run_array(design)
            self.assertIn("N_PORTS = None", ARRAY.read_text())
            nets = fake.of("ExportNetworkData")
            self.assertTrue(all(c[3].endswith(".s%dp" % n) for c in nets), design)
            self.assertTrue(nets[0][3].endswith("ARR1x%d_d16p5mm.s%dp" % (n, n)), design)
            self.assertEqual(len(fake.of("CreateReport")), n, design)  # FIELDS_ARR_D_MM = [18.2]: one report per port
            self.assertEqual(fake.of("EditSources")[-1][0][1][3], "1W")  # ends with P1 active
            self.assertEqual(len(fake.of("EditSources")[0][0]) - 1, n, design)

    def test_n_ports_can_still_be_fixed_by_hand(self):
        fake, root = self.run_array("ARR1x5_P01_MS2_dparam", replace=[("N_PORTS = None", "N_PORTS = 3")])
        self.assertTrue(fake.of("ExportNetworkData")[0][3].endswith("ARR1x3_d16p5mm.s3p"))
        self.assertEqual(len(fake.of("CreateReport")), 3)

    def test_n_ports_none_with_a_name_without_arr1xn_is_an_error(self):
        with self.assertRaises(ValueError):
            self.run_array("US3_PS4_2_1")


if __name__ == "__main__":
    unittest.main()
