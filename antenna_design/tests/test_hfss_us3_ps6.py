"""US3_PS6 (U-slot patch_L 6.29 mm + buried floating parasitic 11.0 x 7.05 mm) HFSS scripts, run against a fake AEDT.

Parallel to test_hfss_us3_ps4.py (same helpers): generated element and 1x5 array scripts, per-design setup
overrides (same stricter setup as US3_PS4), the 11-point Edges_and_f0 sweep of the element, the other designs
still buildable, and both exporters with DESIGN = "ARR1x5_US3_PS6_dparam". No AEDT or pyaedt needed.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

from hfss_paths import BUILD, EXPORT, build_path, set_design
from test_hfss_us3_ps4 import FakeAedt, kv, literal, rect_name, rect_z

VARIANT = json.loads((Path(__file__).resolve().parents[1] / "variants" / "US3_PS6.json").read_text())


def load_pyaedt_module():
    spec = importlib.util.spec_from_file_location("c_ps6", BUILD / "claude_pyaedt_ch9.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def variables_of(path, design):
    return dict(literal(path, "VARIABLES")[design])


def build_only(src, designs):
    """Native script text with DESIGNS_TO_BUILD replaced (its default moved to US3_PS4_2_1)."""
    return re.sub(r"DESIGNS_TO_BUILD = \[[^\]]*\]", "DESIGNS_TO_BUILD = %r" % (list(designs),), src, count=1)


class DesignsAndCheck(unittest.TestCase):
    def test_check_passes_against_variant_json(self):
        mod = load_pyaedt_module()
        self.assertEqual(mod.check("US3_PS6"), [])
        for d in mod.DESIGNS:
            self.assertEqual(mod.check(d), [], d)

    def test_dimensions_match_json(self):
        p = load_pyaedt_module().DESIGNS["US3_PS6"]
        self.assertEqual((p["L"], p["pL"], p["pW"], p["pyc"], p["pz"]), (6.29, 7.05, 11.0, 0.615, 1.035))
        self.assertEqual((p["Wu"], p["Lu"], p["t"], p["y0"]), (4.4, 2.65, 0.8, -0.7))
        u = VARIANT["uslot_params"]
        self.assertEqual((u["L_mm"], u["Wu_mm"], u["Lu_mm"], u["t_mm"], u["y0_mm"]), (p["L"], p["Wu"], p["Lu"], p["t"], p["y0"]))
        par = VARIANT["parasitic_params"]
        self.assertEqual((par["Lp_mm"], par["Wp_mm"], par["y_centre_mm"], par["z_mm"]), (p["pL"], p["pW"], p["pyc"], p["pz"]))
        self.assertAlmostEqual(VARIANT["feed"]["patch_edge_y_mm"], -p["L"] / 2)
        self.assertAlmostEqual(VARIANT["feed"]["transformer_start_y_mm"], -p["L"] / 2 - p["tr_l"])
        self.assertEqual((p["tr_w"], p["tr_l"]), (0.8, 6.6))
        # parasitic stays inside y >= -2.91 (does not lie over the transformer) and 0.235 mm clear in y
        self.assertAlmostEqual(p["pyc"] - p["pL"] / 2, -2.91)
        self.assertAlmostEqual((p["pyc"] - p["pL"] / 2) - (-p["L"] / 2), 0.235)  # y clearance to the patch edge

    def test_setup_and_edges_overrides(self):
        mod = load_pyaedt_module()
        p = mod.setup_props("US3_PS6")
        self.assertEqual((p["MinimumConvergedPasses"], p["MaxDeltaS"], p["SolveType"]), (2, 0.01, "MultiFrequency"))
        self.assertEqual(p["MultipleAdaptiveFreqsSetup"], {"7.7376GHz": 0.01, "7.9872GHz": 0.01, "8.2368GHz": 0.01})
        self.assertEqual(mod.setup_props("US3_PS6"), mod.setup_props("US3_PS4"))
        self.assertEqual(mod.EDGES_COUNT.get("US3_PS6"), 11)
        self.assertEqual(mod.EDGES_COUNT.get("US3_PS4"), 11)
        self.assertNotIn("P01_MS1", mod.EDGES_COUNT)
        self.assertEqual(mod.setup_props("P01_MS1"), {"Frequency": "7.9872GHz", "MaxDeltaS": 0.02, "MaximumPasses": 15})


class ElementScript(unittest.TestCase):
    def setUp(self):
        self.path = build_path("claude_aedt_native_US3_PS6_ch9.py")  # per-element file (build/US3_PS6/)
        self.src = self.path.read_text()

    def test_us3_ps6_still_buildable(self):
        self.assertTrue(set(["P01_MS1", "US3_MS3", "US3_PS4", "US3_PS6"]) <= set(literal(self.path, "VARIABLES")))
        self.assertIn("US3_PS6", re.search(r"DESIGNS_TO_BUILD = \[[^\]]*\]\s*# disponibles: (.*)", self.src).group(1))

    def test_variables_us3_ps6(self):
        v = variables_of(self.path, "US3_PS6")
        self.assertEqual((v["patch_L"], v["par_L"], v["par_W"], v["par_yc"], v["par_z"]),
                         ("6.29mm", "7.05mm", "11.0mm", "0.615mm", "1.035mm"))
        self.assertEqual((v["tr_w"], v["tr_l"], v["line_w"], v["patch_W"]), ("0.8mm", "6.6mm", "3.92mm", "11.421266mm"))
        self.assertEqual((v["u_Wu"], v["u_Lu"], v["u_t"], v["u_y0"]), ("4.4mm", "2.65mm", "0.8mm", "-0.7mm"))
        self.assertEqual(variables_of(self.path, "US3_PS4")["patch_L"], "6.302mm")  # PS4 unchanged

    def test_us3_ps6_built_with_parasitic_one_port(self):
        fake = FakeAedt()
        fake.run(build_only(self.src, ["US3_PS6"]))
        rects = {rect_name(a): rect_z(a) for a in fake.of("CreateRectangle")}
        self.assertEqual(rects["Parasitic"], "par_z")
        self.assertEqual(rects["Patch"], "sub_h")
        self.assertEqual([a[0][0] for a in fake.of("AssignFiniteCond")], ["NAME:Cu_Ground", "NAME:Cu_Patch", "NAME:Cu_Parasitic"])
        self.assertEqual(len(fake.of("AssignLumpedPort")), 1)
        self.assertEqual(len(fake.of("InsertSetup")), 1)
        var_values = {}
        for a in fake.of("ChangeProperty"):  # design variables written by set_variables
            for prop in a[0][1][2][1:]:  # NewProps = ["NAME:NewProps", ["NAME:<var>", ...], ...]
                var_values[prop[0][5:]] = kv(prop, "Value:=")
        self.assertEqual(var_values["patch_L"], "6.29mm")
        self.assertEqual(var_values["par_yc"], "0.615mm")

    def test_us3_ps6_setup_and_sweeps(self):
        fake = FakeAedt()
        fake.run(build_only(self.src, ["US3_PS6"]))
        setup = fake.of("InsertSetup")[0][1]
        self.assertEqual(kv(setup, "MinimumConvergedPasses:="), 2)
        self.assertEqual(kv(setup, "MaxDeltaS:="), 0.01)
        self.assertEqual(kv(setup, "SolveType:="), "MultiFrequency")
        multi = [a for a in setup if isinstance(a, list) and a[0] == "NAME:MultipleAdaptiveFreqsSetup"][0]
        self.assertEqual(multi[1:], ["7.7376GHz:=", [0.01], "7.9872GHz:=", [0.01], "8.2368GHz:=", [0.01]])
        sweeps = {a[1][0]: kv(a[1], "RangeCount:=") for a in fake.of("InsertFrequencySweep")}
        self.assertEqual(sweeps, {"NAME:Sweep_7p5_8p5": 1001, "NAME:Edges_and_f0": 11})

    def test_other_designs_still_buildable_and_unchanged(self):
        for d, count, strict in (("P01_MS1", 3, False), ("US3_MS3", 3, False), ("US3_PS4", 11, True)):
            fake = FakeAedt()
            fake.run(build_only(self.src, [d]))
            setup = fake.of("InsertSetup")[0][1]
            self.assertEqual(kv(setup, "MinimumConvergedPasses:="), 2 if strict else 1, d)
            self.assertEqual(kv(setup, "MaxDeltaS:="), 0.01 if strict else 0.02, d)
            edges = [a[1] for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Edges_and_f0"]
            self.assertEqual([kv(e, "RangeCount:=") for e in edges], [count], d)
            has_par = any(rect_name(a) == "Parasitic" for a in fake.of("CreateRectangle"))
            self.assertEqual(has_par, d == "US3_PS4", d)
        multi = FakeAedt()
        multi.run(build_only(self.src, ["US3_PS4", "US3_PS6"]))
        self.assertEqual(len(multi.of("InsertSetup")), 2)


class ArrayScript(unittest.TestCase):
    def setUp(self):
        self.path = build_path("claude_aedt_array1x5_US3_PS6_param_ch9.py")
        self.src = self.path.read_text()

    def test_defaults(self):
        self.assertIn("DESIGNS_TO_BUILD = ['US3_PS6']", self.src)
        self.assertIn("PITCHES_MM = [18.2]", self.src)
        self.assertIn("PARAMETRIC_PITCH = True", self.src)
        self.assertIn("ARR1x5_US3_PS6_dparam", self.src)
        self.assertEqual(variables_of(self.path, "US3_PS6")["patch_L"], "6.29mm")
        self.assertEqual(variables_of(self.path, "US3_PS6")["par_yc"], "0.615mm")
        # the PS4 array script keeps PS4 as default element
        self.assertIn("DESIGNS_TO_BUILD = ['US3_PS4']", (build_path("claude_aedt_array1x5_US3_PS4_param_ch9.py")).read_text())

    def test_five_parasitics_eleven_boundaries_five_ports(self):
        fake = FakeAedt()
        fake.run(self.src)
        par = {rect_name(a): rect_z(a) for a in fake.of("CreateRectangle") if rect_name(a).startswith("Parasitic_")}
        self.assertEqual(par, {f"Parasitic_{i}": "par_z" for i in range(1, 6)})
        fc = fake.of("AssignFiniteCond")
        self.assertEqual(len(fc), 11)  # Ground + 5 patches + 5 parasitics
        ports = fake.of("AssignLumpedPort")
        self.assertEqual(len(ports), 5)
        for i, a in enumerate(ports):
            self.assertEqual(a[0][0], f"NAME:P{i + 1}")
            self.assertEqual(kv(a[0], "Start:=")[0], f"({i - 2})*arr_d")
            self.assertEqual(kv(a[0], "End:=")[0], f"({i - 2})*arr_d")
            self.assertEqual(kv(a[0], "Objects:="), [f"PortSheet_{i + 1}"])

    def test_array_setup_strict_and_edges_three(self):
        fake = FakeAedt()
        fake.run(self.src)
        setup = fake.of("InsertSetup")[0][1]
        self.assertEqual((kv(setup, "MinimumConvergedPasses:="), kv(setup, "MaxDeltaS:="), kv(setup, "SolveType:=")),
                         (2, 0.01, "MultiFrequency"))
        edges = [a[1] for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Edges_and_f0"]
        self.assertEqual([kv(e, "RangeCount:=") for e in edges], [3])

    def test_ps6_array_same_scheme_as_ps4(self):
        ps4 = FakeAedt()
        ps4.run((build_path("claude_aedt_array1x5_US3_PS4_param_ch9.py")).read_text())
        ps6 = FakeAedt()
        ps6.run(self.src)
        for m in ("CreateRectangle", "AssignFiniteCond", "AssignLumpedPort", "InsertSetup", "InsertFrequencySweep"):
            self.assertEqual(len(ps4.of(m)), len(ps6.of(m)), m)


class ExportersWithUs3Ps6(unittest.TestCase):
    NAME = "ARR1x5_US3_PS6_dparam"
    VARS = ["arr_d='%gmm' board_x='%gmm'" % (d, 4 * d + 26) for d in (16.5, 17, 17.5, 18, 18.2, 18.5, 19, 19.5)]

    def test_headers_mention_ps6_and_logic_unchanged(self):
        for f in ("claude_aedt_export_array_ch9.py", "claude_aedt_export_fields_ch9.py"):
            self.assertIn(self.NAME, (EXPORT / f).read_text(), f)
        # every array is listed as a DESIGN line of the array exporter (commented, or active when it is the default)
        self.assertIn('DESIGN = "%s"' % self.NAME, (EXPORT / "claude_aedt_export_array_ch9.py").read_text())
        self.assertIn('FIELDS_ARR_D_MM = [18.2, 16.5, 19.5]', (EXPORT / "claude_aedt_export_fields_ch9.py").read_text())

    def test_array_exporter_default_grid_and_restore_nominal(self):
        import tempfile
        out = tempfile.mkdtemp()
        fake = FakeAedt(out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS)
        src = set_design((EXPORT / "claude_aedt_export_array_ch9.py").read_text(), self.NAME)
        fake.run(src)
        nets = fake.of("ExportNetworkData")
        self.assertEqual(len(nets), 8)  # 16.5..19.5 every 0.5 (7) + 18.2
        self.assertTrue(any(n[3].endswith("ARR1x5_d18p2mm.s5p") for n in nets))
        self.assertTrue((Path(out) / "ch9_array_export" / (self.NAME + "_d18p2mm") / "ff_P1.csv").is_file())
        changes = [c[2][0][1][2][1][2] for c in fake.calls if c[1] == "ChangeProperty"]
        self.assertEqual(changes, ["18.2mm", "17mm"])

    def test_fields_exporter_default_batch(self):
        import tempfile
        out = tempfile.mkdtemp()
        fake = FakeAedt(out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS)
        src = set_design((EXPORT / "claude_aedt_export_fields_ch9.py").read_text(), self.NAME).replace(
            "MIN_CSV_BYTES = 1000", "MIN_CSV_BYTES = 1")  # the fake AEDT writes 1-byte CSVs
        fake.run(src)
        changes = [c[2][0][1][2][1][2] for c in fake.calls if c[1] == "ChangeProperty"]
        self.assertEqual(changes, ["18.2mm", "16.5mm", "17mm"])  # stops cleanly at MAX_REPORTS_PER_RUN = 10
        self.assertEqual(len(fake.of("CreateReport")), 10)
        fake.calls.clear()
        fake.run(src)  # relaunch after restarting AEDT: continues with 19.5 mm only
        self.assertEqual([c[2][0][1][2][1][2] for c in fake.calls if c[1] == "ChangeProperty"], ["19.5mm", "17mm"])
        self.assertEqual(len(fake.of("CreateReport")), 5)


if __name__ == "__main__":
    unittest.main()
