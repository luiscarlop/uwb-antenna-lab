"""US3_PS6_4 (US3_PS6 with a 14.0 mm wide patch, parasitic 13.58 x 7.05 mm, transformer 1.0 x 7.25 mm) HFSS scripts, against a fake AEDT.

Parallel to test_hfss_us3_ps6.py (same helpers): generated element and 1x5 array scripts, per-design setup overrides (same
stricter setup as US3_PS6 but MaximumPasses 25, design-reviewer E1), the 11-point Edges_and_f0 sweep of the element, the other designs unchanged, the minimum
physical array pitch (the 14.0 mm patches overlap at the 13.5 mm pitch of the P01_MS2 grid) and both exporters with
DESIGN = "ARR1x5_US3_PS6_4_dparam". No AEDT or pyaedt needed.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

from hfss_paths import BUILD, EXPORT, RESULTS, build_path, set_design
from test_hfss_us3_ps4 import FakeAedt, kv, literal, rect_name, rect_z

VARIANT = json.loads((Path(__file__).resolve().parents[1] / "variants" / "US3_PS6_4.json").read_text())
NAME = "ARR1x5_US3_PS6_4_dparam"
PS6_4_GRID = [16.5 + 0.5 * i for i in range(9)] + [18.2]   # Optimetrics grid of the array (E3): 16.5..20.5 every 0.5 and 18.2 (10 steps)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pyaedt_module():
    return load_module(BUILD / "claude_pyaedt_ch9.py", "c_ps6_4")


def variables_of(path, design):
    return dict(literal(path, "VARIABLES")[design])


def build_only(src, designs):
    return re.sub(r"DESIGNS_TO_BUILD = \[[^\]]*\]", "DESIGNS_TO_BUILD = %r" % (list(designs),), src, count=1)


class DesignsAndCheck(unittest.TestCase):
    def test_check_passes_against_variant_json(self):
        mod = load_pyaedt_module()
        self.assertEqual(mod.check("US3_PS6_4"), [])
        for d in mod.DESIGNS:
            self.assertEqual(mod.check(d), [], d)

    def test_dimensions_match_json(self):
        p = load_pyaedt_module().DESIGNS["US3_PS6_4"]
        self.assertEqual((p["W"], p["L"], p["pW"], p["pL"], p["pyc"], p["pz"]), (14.0, 6.29, 13.58, 7.05, 0.615, 1.035))
        self.assertEqual((p["tr_w"], p["tr_l"], p["line_w"]), (1.0, 7.25, 3.92))
        self.assertEqual((p["Wu"], p["Lu"], p["t"], p["y0"]), (4.4, 2.65, 0.8, -0.7))
        u = VARIANT["uslot_params"]
        self.assertEqual((u["L_mm"], u["W_mm"], u["Wu_mm"], u["Lu_mm"], u["t_mm"], u["y0_mm"]),
                         (p["L"], p["W"], p["Wu"], p["Lu"], p["t"], p["y0"]))
        par = VARIANT["parasitic_params"]
        self.assertEqual((par["Lp_mm"], par["Wp_mm"], par["y_centre_mm"], par["z_mm"]), (p["pL"], p["pW"], p["pyc"], p["pz"]))
        f = VARIANT["feed"]
        self.assertEqual((f["transformer_width_mm"], f["transformer_length_mm"]), (p["tr_w"], p["tr_l"]))
        self.assertAlmostEqual(f["patch_edge_y_mm"], -p["L"] / 2)
        self.assertAlmostEqual(f["transformer_start_y_mm"], -p["L"] / 2 - p["tr_l"])
        self.assertAlmostEqual(f["transformer_start_y_mm"], -10.395)
        # the 50 ohm section is only 2.605 mm long (y -13 -> -10.395): board_y/2 - patch_L/2 - tr_l
        self.assertAlmostEqual(f["line_end_y_mm"] - f["line_start_y_mm"], 2.605)
        self.assertAlmostEqual(p["board_y"] / 2 - p["L"] / 2 - p["tr_l"], 2.605)
        self.assertEqual(f["line_start_y_mm"], -p["board_y"] / 2)
        # parasitic y -2.91...4.14 (0.235 mm above the patch edge in y, same as US3_PS6) and 0.21 mm x inset each side
        self.assertAlmostEqual(p["pyc"] - p["pL"] / 2, -2.91)
        self.assertAlmostEqual((p["pyc"] - p["pL"] / 2) - (-p["L"] / 2), 0.235)
        self.assertAlmostEqual((p["W"] - p["pW"]) / 2, 0.21)

    def test_only_width_and_transformer_differ_from_us3_ps6(self):
        ds = load_pyaedt_module().DESIGNS
        a, b = ds["US3_PS6"], ds["US3_PS6_4"]
        self.assertEqual({k for k in a if a[k] != b[k]}, {"W", "pW", "tr_w", "tr_l"})
        self.assertEqual(VARIANT["base_design"], "US3_PS6")

    def test_setup_and_edges_overrides(self):
        mod = load_pyaedt_module()
        p = mod.setup_props("US3_PS6_4")
        self.assertEqual((p["MinimumConvergedPasses"], p["MaxDeltaS"], p["SolveType"]), (2, 0.01, "MultiFrequency"))
        self.assertEqual(p["MultipleAdaptiveFreqsSetup"], {"7.7376GHz": 0.01, "7.9872GHz": 0.01, "8.2368GHz": 0.01})
        # E1: US3_PS6_4 gets 25 passes (the wide patch needs more to reach two converged ones); everything else equals US3_PS6
        self.assertEqual(p["MaximumPasses"], 25)
        ps6 = mod.setup_props("US3_PS6")
        self.assertEqual(ps6["MaximumPasses"], 15)
        self.assertEqual({**p, "MaximumPasses": 15}, ps6)
        for d in ("P01_MS1", "P01_MS2", "US3_MS3", "US3_PS4", "US3_PS6", "US3_PS4_2_1"):
            self.assertEqual(mod.setup_props(d)["MaximumPasses"], 15, d)
        for d in ("US3_PS4", "US3_PS6", "US3_PS4_2_1", "US3_PS6_4"):
            self.assertEqual(mod.EDGES_COUNT.get(d), 11, d)
        self.assertEqual(mod.setup_props("P01_MS1"), {"Frequency": "7.9872GHz", "MaxDeltaS": 0.02, "MaximumPasses": 15})

    def test_rect_geometry_is_consistent(self):
        r = load_pyaedt_module().rects(load_pyaedt_module().DESIGNS["US3_PS6_4"])
        self.assertEqual(r["patch"], (-7.0, -3.145, 7.0, 3.145))
        self.assertAlmostEqual(r["transformer"][1], -10.395)
        self.assertEqual((r["transformer"][0], r["transformer"][2]), (-0.5, 0.5))
        self.assertEqual((r["line"][1], r["line"][3]), (-13.0, r["transformer"][1]))
        px0, py0, px1, py1 = r["parasitic"]
        self.assertEqual((px0, px1), (-6.79, 6.79))
        self.assertAlmostEqual(py0, -2.91)
        self.assertAlmostEqual(py1, 4.14)
        self.assertLess(r["patch"][2], 13.0)  # patch inside the 26 mm board (6.0 mm margin in x)


class ElementScript(unittest.TestCase):
    def setUp(self):
        self.path = build_path("claude_aedt_native_US3_PS6_4_ch9.py")  # per-element file (build/US3_PS6_4/)
        self.src = self.path.read_text()

    def test_default_build_and_every_design_available(self):
        self.assertEqual(self.path.parent.name, "US3_PS6_4")
        self.assertIn('DESIGNS_TO_BUILD = ["US3_PS6_4"]', self.src)
        self.assertEqual(sorted(literal(self.path, "VARIABLES")),
                         ["P01_MS1", "P01_MS2", "US3_MS3", "US3_PS4", "US3_PS4_2_1", "US3_PS6", "US3_PS6_4"])

    def test_variables_us3_ps6_4(self):
        v = variables_of(self.path, "US3_PS6_4")
        self.assertEqual((v["patch_W"], v["patch_L"], v["par_W"], v["par_L"], v["par_yc"], v["par_z"]),
                         ("14.0mm", "6.29mm", "13.58mm", "7.05mm", "0.615mm", "1.035mm"))
        self.assertEqual((v["tr_w"], v["tr_l"], v["line_w"]), ("1.0mm", "7.25mm", "3.92mm"))
        self.assertEqual((v["u_Wu"], v["u_Lu"], v["u_t"], v["u_y0"]), ("4.4mm", "2.65mm", "0.8mm", "-0.7mm"))
        ps6 = variables_of(self.path, "US3_PS6")  # unchanged
        self.assertEqual((ps6["patch_W"], ps6["par_W"], ps6["tr_w"], ps6["tr_l"]), ("11.421266mm", "11.0mm", "0.8mm", "6.6mm"))

    def test_built_with_parasitic_one_port(self):
        fake = FakeAedt()
        fake.run(self.src)
        rects = {rect_name(a): rect_z(a) for a in fake.of("CreateRectangle")}
        self.assertEqual(rects["Parasitic"], "par_z")
        self.assertEqual(rects["Patch"], "sub_h")
        self.assertEqual([a[0][0] for a in fake.of("AssignFiniteCond")], ["NAME:Cu_Ground", "NAME:Cu_Patch", "NAME:Cu_Parasitic"])
        self.assertEqual(len(fake.of("AssignLumpedPort")), 1)
        self.assertEqual(len(fake.of("InsertSetup")), 1)
        var_values = {}
        for a in fake.of("ChangeProperty"):
            for prop in a[0][1][2][1:]:
                var_values[prop[0][5:]] = kv(prop, "Value:=")
        self.assertEqual((var_values["patch_W"], var_values["tr_w"], var_values["tr_l"], var_values["par_W"]),
                         ("14.0mm", "1.0mm", "7.25mm", "13.58mm"))
        info = [a[3] for a in fake.of("AddMessage") if a[2] == 0]
        self.assertEqual(info, ["construido US3_PS6_4: patch_L 6.29mm, par_W 13.58mm"])
        # the lumped port stays at the board edge y = -13 on the strip width (same as the other designs)
        port = fake.of("AssignLumpedPort")[0][0]
        self.assertEqual(kv(port, "Objects:="), ["PortSheet"])

    def test_setup_and_sweeps(self):
        fake = FakeAedt()
        fake.run(self.src)
        setup = fake.of("InsertSetup")[0][1]
        self.assertEqual((kv(setup, "MinimumConvergedPasses:="), kv(setup, "MaxDeltaS:="), kv(setup, "SolveType:=")),
                         (2, 0.01, "MultiFrequency"))
        self.assertEqual(kv(setup, "MaximumPasses:="), 25)   # E1: not equal to US3_PS6 (15) any more
        multi = [a for a in setup if isinstance(a, list) and a[0] == "NAME:MultipleAdaptiveFreqsSetup"][0]
        self.assertEqual(multi[1:], ["7.7376GHz:=", [0.01], "7.9872GHz:=", [0.01], "8.2368GHz:=", [0.01]])
        sweeps = {a[1][0]: kv(a[1], "RangeCount:=") for a in fake.of("InsertFrequencySweep")}
        self.assertEqual(sweeps, {"NAME:Sweep_7p5_8p5": 1001, "NAME:Edges_and_f0": 11})
        main = [a[1] for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Sweep_7p5_8p5"][0]
        self.assertEqual((kv(main, "RangeStart:="), kv(main, "RangeEnd:=")), ("7.5GHz", "8.5GHz"))

    def test_same_setup_and_sweeps_as_us3_ps6(self):
        ps6 = build_path("claude_aedt_native_US3_PS6_ch9.py")
        mine = literal(self.path, "SETUP_ARGS")["US3_PS6_4"]
        ref = literal(ps6, "SETUP_ARGS")["US3_PS6"]
        self.assertEqual(kv(mine, "MaximumPasses:="), 25)
        self.assertEqual(kv(ref, "MaximumPasses:="), 15)
        # the only difference with the US3_PS6 setup is MaximumPasses
        self.assertEqual(repr(mine).replace("'MaximumPasses:=', 25", "'MaximumPasses:=', 15"), repr(ref))
        self.assertEqual(literal(self.path, "SWEEP_ARGS")["US3_PS6_4"], literal(ps6, "SWEEP_ARGS")["US3_PS6"])
        self.assertEqual(literal(self.path, "LUMPED_PORT_ARGS")["US3_PS6_4"], literal(ps6, "LUMPED_PORT_ARGS")["US3_PS6"])

    def test_existing_designs_unchanged_in_all_element_files(self):
        expected = {"P01_MS1": ("7.322mm", "11.421266mm", "0.8mm", "6.6mm"), "US3_MS3": ("6.502mm", "11.421266mm", "0.8mm", "6.6mm"),
                    "US3_PS4": ("6.302mm", "11.421266mm", "0.8mm", "6.6mm"), "US3_PS6": ("6.29mm", "11.421266mm", "0.8mm", "6.6mm"),
                    "US3_PS4_2_1": ("6.222mm", "11.421266mm", "0.8mm", "6.6mm")}
        for elem, vals in expected.items():
            v = variables_of(build_path(f"claude_aedt_native_{elem}_ch9.py"), elem)
            self.assertEqual((v["patch_L"], v["patch_W"], v["tr_w"], v["tr_l"]), vals, elem)
        for d, count, strict, has_par in (("P01_MS1", 3, False, False), ("US3_MS3", 3, False, False),
                                          ("US3_PS4", 11, True, True), ("US3_PS6", 11, True, True), ("US3_PS6_4", 11, True, True)):
            fake = FakeAedt()
            fake.run(build_only(self.src, [d]))
            setup = fake.of("InsertSetup")[0][1]
            self.assertEqual(kv(setup, "MinimumConvergedPasses:="), 2 if strict else 1, d)
            self.assertEqual(kv(setup, "MaxDeltaS:="), 0.01 if strict else 0.02, d)
            self.assertEqual(kv(setup, "MaximumPasses:="), 25 if d == "US3_PS6_4" else 15, d)
            edges = [a[1] for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Edges_and_f0"]
            self.assertEqual([kv(e, "RangeCount:=") for e in edges], [count], d)
            self.assertEqual(any(rect_name(a) == "Parasitic" for a in fake.of("CreateRectangle")), has_par, d)

    def test_rerun_guard_skips_existing_design(self):
        fake = FakeAedt(top_designs=["HFSSDesign;US3_PS6_4"])
        fake.run(self.src)
        self.assertEqual(fake.of("InsertDesign"), [])
        self.assertEqual(fake.of("InsertSetup"), [])


class ArrayScript(unittest.TestCase):
    def setUp(self):
        self.path = build_path("claude_aedt_array1x5_US3_PS6_4_param_ch9.py")
        self.src = self.path.read_text()

    def test_defaults(self):
        self.assertEqual(self.path.parent.name, "US3_PS6_4")
        self.assertIn("DESIGNS_TO_BUILD = ['US3_PS6_4']", self.src)
        self.assertIn("PITCHES_MM = [18.2]", self.src)
        self.assertIn("PARAMETRIC_PITCH = True", self.src)
        self.assertIn(NAME, self.src)
        v = variables_of(self.path, "US3_PS6_4")
        self.assertEqual((v["patch_W"], v["par_W"], v["tr_w"], v["tr_l"], v["patch_L"]), ("14.0mm", "13.58mm", "1.0mm", "7.25mm", "6.29mm"))
        self.assertIn("DESIGNS_TO_BUILD = ['US3_PS6']", build_path("claude_aedt_array1x5_US3_PS6_param_ch9.py").read_text())

    def test_five_parasitics_eleven_boundaries_five_ports(self):
        fake = FakeAedt()
        fake.run(self.src)
        par = {rect_name(a): rect_z(a) for a in fake.of("CreateRectangle") if rect_name(a).startswith("Parasitic_")}
        self.assertEqual(par, {f"Parasitic_{i}": "par_z" for i in range(1, 6)})
        self.assertEqual(len(fake.of("AssignFiniteCond")), 11)  # Ground + 5 patches + 5 parasitics
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
        self.assertEqual(kv(setup, "MaximumPasses:="), 25)   # E1: the array of the wide patch also gets 25 passes
        edges = [a[1] for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Edges_and_f0"]
        # 3 points (E4; 5 would only show a possible eta valley in the embedded fields and cost disk) like US3_PS6 (openEMS 051: eta 0.65-0.71, no valley in the channel; only US3_PS4_2_1 uses 5)
        self.assertEqual([kv(e, "RangeCount:=") for e in edges], [3])
        main = [a[1] for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Sweep_7p5_8p5"]
        self.assertEqual([kv(m, "RangeCount:=") for m in main], [1001])

    def test_other_arrays_keep_fifteen_passes(self):
        for name in ("US3_PS6/claude_aedt_array1x5_US3_PS6_param_ch9.py", "US3_PS4_2_1/claude_aedt_array1x5_US3_PS4_2_1_param_ch9.py",
                     "US3_PS4/claude_aedt_array1x5_US3_PS4_param_ch9.py"):
            fake = FakeAedt()
            fake.run(build_path(name.split("/")[1]).read_text())
            self.assertEqual(kv(fake.of("InsertSetup")[0][1], "MaximumPasses:="), 15, name)

    def test_array_same_scheme_as_us3_ps6(self):
        mine = FakeAedt()
        mine.run(self.src)
        ref = FakeAedt()
        ref.run(build_path("claude_aedt_array1x5_US3_PS6_param_ch9.py").read_text())
        for m in ("CreateRectangle", "AssignFiniteCond", "AssignLumpedPort", "InsertSetup", "InsertFrequencySweep"):
            self.assertEqual(len(ref.of(m)), len(mine.of(m)), m)

    def test_minimum_physical_pitch(self):
        p = load_pyaedt_module().DESIGNS["US3_PS6_4"]
        w = p["W"]
        gap = lambda d: d - w   # copper gap between neighbouring patches
        self.assertAlmostEqual(gap(13.5), -0.5)         # the P01_MS2 grid minimum would overlap the patches by 0.5 mm
        self.assertLess(gap(13.5), 0)
        self.assertAlmostEqual(gap(14.0), 0.0)          # touching copper: not a valid design either
        self.assertGreaterEqual(gap(14.5), 0.5 - 1e-9)  # 14.5 mm: 0.5 mm gap is the practical minimum (not in the E3 grid)
        self.assertGreaterEqual(gap(min(PS6_4_GRID)), 0.5 - 1e-9)
        # E3: Optimetrics grid 16.5..20.5 every 0.5 plus 18.2 = 10 steps (the closer pitches 14.5..16.0 are not swept)
        self.assertEqual(min(PS6_4_GRID), 16.5)
        self.assertEqual(max(PS6_4_GRID), 20.5)
        self.assertEqual(len(PS6_4_GRID), 10)
        self.assertEqual(sorted(PS6_4_GRID), [16.5, 17.0, 17.5, 18.0, 18.2, 18.5, 19.0, 19.5, 20.0, 20.5])
        self.assertIn(18.2, PS6_4_GRID)                 # nominal pitch of the script
        self.assertGreater(gap(18.2), 0.5)
        # the parasitics (13.58 mm) still clear each other at the minimum of the grid
        self.assertGreater(14.5 - p["pW"], 0.9)
        self.assertGreater(min(PS6_4_GRID) - p["pW"], 0.9)
        # board edge: board_x = 4*arr_d + 2*board_m; patch edge to board edge is 6.0 mm in x whatever the pitch
        self.assertAlmostEqual(13.0 - w / 2, 6.0)
        self.assertIn("Paso minimo FISICO", self.src)
        self.assertIn("patch_W 14 mm (US3_PS6_4): arr_d > 14 mm", self.src)

    def test_generator_refuses_overlapping_nominal_pitch(self):
        gen = load_module(BUILD / "make_aedt_array_script.py", "gen_arr")   # imports without pyaedt
        designs = {"US3_PS6_4": {"W": 14.0}, "P01_MS2": {"W": 11.421266}}
        gen.check_pitches(designs, [18.2, 14.5], "US3_PS6_4")
        with self.assertRaises(AssertionError):
            gen.check_pitches(designs, [13.5], "US3_PS6_4")
        with self.assertRaises(AssertionError):
            gen.check_pitches(designs, [14.0], "US3_PS6_4")
        gen.check_pitches(designs, [13.5], "P01_MS2")   # the older elements keep the 13.5 mm pitch


class ExportersWithUs3Ps6_4(unittest.TestCase):
    VARS = ["arr_d='%gmm' board_x='%gmm'" % (d, 4 * d + 26) for d in (16.5, 17, 17.5, 18, 18.2, 18.5, 19, 19.5)]
    VARS_LONG = ["arr_d='%gmm' board_x='%gmm'" % (d, 4 * d + 26) for d in PS6_4_GRID]

    def test_headers_and_design_lines(self):
        for f in ("claude_aedt_export_array_ch9.py", "claude_aedt_export_fields_ch9.py"):
            src = (EXPORT / f).read_text()
            self.assertIn(NAME, src, f)
            self.assertIn('# DESIGN = "%s"' % NAME, src, f)         # commented option (the default stays US3_PS4_2_1)
            self.assertEqual(len(re.findall(r'(?m)^DESIGN = ".*?"', src)), 1, f)
        el = (EXPORT / "claude_aedt_export_element_ch9.py").read_text()
        self.assertIn('# DESIGN = "US3_PS6_4"', el)
        self.assertEqual(len(re.findall(r'(?m)^DESIGN = ".*?"', el)), 1)
        self.assertIn("[16.5 + 0.5 * i for i in range(9)] + [18.2]", (EXPORT / "claude_aedt_export_array_ch9.py").read_text())
        self.assertIn("[18.2, 16.5, 20.5]", (EXPORT / "claude_aedt_export_fields_ch9.py").read_text())

    def test_pitch_grid_snippet_matches_test_grid(self):
        self.assertEqual([16.5 + 0.5 * i for i in range(9)] + [18.2], PS6_4_GRID)

    def test_array_exporter_default_grid_with_ps6_4(self):
        import tempfile
        out = tempfile.mkdtemp()
        fake = FakeAedt(out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS)
        src = set_design((EXPORT / "claude_aedt_export_array_ch9.py").read_text(), NAME)
        fake.run(src)
        self.assertEqual(len(fake.of("ExportNetworkData")), 8)  # short grid 16.5..19.5 + 18.2 (default)
        self.assertTrue((Path(out) / "ch9_array_export" / (NAME + "_d18p2mm") / "ff_P1.csv").is_file())

    def test_array_exporter_long_ps6_4_grid_uncommented(self):
        import tempfile
        out = tempfile.mkdtemp()
        fake = FakeAedt(out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS_LONG)
        src = set_design((EXPORT / "claude_aedt_export_array_ch9.py").read_text(), NAME)
        src = re.sub(r"(?m)^ARR_D_MM = .*$", "", src).replace("# ARR_D_MM = [16.5 + 0.5 * i for i in range(9)]", "ARR_D_MM = [16.5 + 0.5 * i for i in range(9)]")
        fake.run(src)
        nets = fake.of("ExportNetworkData")
        self.assertEqual(len(nets), 10)  # 16.5..20.5 every 0.5 (9) + 18.2
        self.assertFalse(any(n[3].endswith("ARR1x5_d13p5mm.s5p") for n in nets))   # 13.5 mm (overlap) is not exported
        self.assertFalse(any(n[3].endswith("ARR1x5_d14p5mm.s5p") for n in nets))   # nor 14.5 (not in the E3 grid)
        self.assertTrue(any(n[3].endswith("ARR1x5_d20p5mm.s5p") for n in nets))

    def test_fields_exporter_with_ps6_4(self):
        import tempfile
        out = tempfile.mkdtemp()
        fake = FakeAedt(out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS)
        src = set_design((EXPORT / "claude_aedt_export_fields_ch9.py").read_text(), NAME).replace(
            "MIN_CSV_BYTES = 1000", "MIN_CSV_BYTES = 1")
        fake.run(src)
        changes = [c[2][0][1][2][1][2] for c in fake.calls if c[1] == "ChangeProperty"]
        self.assertEqual(changes, ["18.2mm", "16.5mm", "17mm"])


class ResultsFolder(unittest.TestCase):
    def test_results_folder_placeholders(self):
        base = RESULTS / "results_US3_PS6_4"
        self.assertTrue((base / "README.md").is_file())
        self.assertTrue((base / "preregistro_hfss.md").is_file())  # hypotheses registered before the results
        # Element and array exported by the owner from HFSS: every pitch folder carries its S matrix and convergence.
        self.assertTrue((base / "US3_PS6_4" / "US3_PS6_4.s1p").is_file())
        self.assertTrue((base / "US3_PS6_4" / "convergence.conv").is_file())
        pitches = sorted((base / "ARR1x5_US3_PS6_4_dparam").glob("ARR1x5_US3_PS6_4_dparam_d*mm"))
        self.assertGreaterEqual(len(pitches), 10)
        for d in pitches:
            self.assertTrue(any(d.glob("*.s5p")), d)
            self.assertTrue((d / "convergence.conv").is_file(), d)


if __name__ == "__main__":
    unittest.main()
