"""US3_PS4 (U-slot + buried floating parasitic) HFSS scripts, run against a fake AEDT (no AEDT needed).

Covers the generated element and 1x5 array scripts, the per-design setup overrides (stricter only for
US3_PS4), the 11-point Edges_and_f0 sweep of the element, and both exporters with
DESIGN = "ARR1x5_US3_PS4_dparam".
"""
import ast
import sys
import tempfile
import types
import unittest
from pathlib import Path

from hfss_paths import BUILD, EXPORT, build_path, set_design


def kv(args, key):
    """Value following `key` in a flat native argument list (searches nested lists too)."""
    for i, a in enumerate(args):
        if a == key:
            return args[i + 1]
        if isinstance(a, list):
            r = kv(a, key)
            if r is not None:
                return r
    return None


def literal(path, name):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
            return ast.literal_eval(node.value)
    raise KeyError(name)


class FakeAedt:
    """Records every AEDT call as (object name, method, args)."""

    def __init__(self, out=None, nominal=None, variations=(), top_designs=()):
        self.calls, self.out, self.nominal, self.variations = [], out, nominal, list(variations)
        self.top_designs = list(top_designs)  # what oProject.GetTopDesignList() returns ("<type>;<name>" entries)
        sys.modules["ScriptEnv"] = types.SimpleNamespace(Initialize=lambda *a: None)

    def rec(self, n):
        outer = self

        class Rec:
            def __getattr__(self, a):
                def f(*args):
                    outer.calls.append((n, a, args))
                    if a in ("SetActiveDesign", "InsertDesign"):
                        return outer.rec("Design")
                    if a == "SetActiveEditor":
                        return outer.rec("Editor")
                    if a == "GetModule":
                        return outer.rec(args[0])
                    if a in ("GetActiveProject", "GetDefinitionManager"):
                        return outer.rec(a)
                    if a == "GetPath":
                        return outer.out
                    if a == "GetNominalVariation":
                        return outer.nominal
                    if a == "GetAvailableVariations":
                        return outer.variations
                    if a == "GetTopDesignList":
                        return outer.top_designs
                    if a == "ExportToFile":
                        Path(args[1]).write_text("x")
                    return "Project1" if a == "GetName" else None
                return f
        return Rec()

    def run(self, src):
        exec(compile(src, "x", "exec"), {"oDesktop": self.rec("Desktop")})
        return self.calls

    def of(self, method):
        return [c[2] for c in self.calls if c[1] == method]


def rect_name(args):
    return kv(args[1], "Name:=")


def rect_z(args):
    return kv(args[0], "ZStart:=")


def walk_strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for y in x:
            yield from walk_strings(y)


class ElementScript(unittest.TestCase):
    def setUp(self):
        self.path = build_path("claude_aedt_native_US3_PS4_ch9.py")
        self.src = self.path.read_text()

    def test_us3_ps4_element_built_with_parasitic(self):
        fake = FakeAedt()
        fake.run(self.src)  # DESIGNS_TO_BUILD = ["US3_PS4"] (per-element file)
        rects = {rect_name(a): rect_z(a) for a in fake.of("CreateRectangle")}
        self.assertEqual(rects["Parasitic"], "par_z")
        self.assertEqual(rects["Patch"], "sub_h")
        fc = [a[0][0] for a in fake.of("AssignFiniteCond")]
        self.assertEqual(fc, ["NAME:Cu_Ground", "NAME:Cu_Patch", "NAME:Cu_Parasitic"])
        self.assertEqual(kv(fake.of("AssignFiniteCond")[2][0], "Objects:="), ["Parasitic"])
        self.assertEqual(len(fake.of("AssignLumpedPort")), 1)

    def test_us3_ps4_setup_overrides_applied(self):
        fake = FakeAedt()
        fake.run(self.src)
        setup = fake.of("InsertSetup")[0][1]
        self.assertEqual(kv(setup, "MinimumConvergedPasses:="), 2)
        self.assertEqual(kv(setup, "MaxDeltaS:="), 0.01)
        self.assertEqual(kv(setup, "SolveType:="), "MultiFrequency")
        multi = [a for a in setup if isinstance(a, list) and a[0] == "NAME:MultipleAdaptiveFreqsSetup"][0]
        self.assertEqual(multi[1:], ["7.7376GHz:=", [0.01], "7.9872GHz:=", [0.01], "8.2368GHz:=", [0.01]])
        sweeps = {kv(a[1], "RangeCount:=") for a in fake.of("InsertFrequencySweep") if a[1][0] == "NAME:Edges_and_f0"}
        self.assertEqual(sweeps, {11})
        names = [a[1][0] for a in fake.of("InsertFrequencySweep")]
        self.assertEqual(names, ["NAME:Sweep_7p5_8p5", "NAME:Edges_and_f0"])  # same sweep names

    def test_other_designs_keep_previous_setup_and_three_points(self):
        setups = literal(self.path, "SETUP_ARGS")
        sweeps = literal(self.path, "SWEEP_ARGS")
        for d in ("P01_MS1", "US3_MS3"):
            self.assertEqual(kv(setups[d], "MinimumConvergedPasses:="), 1, d)
            self.assertEqual(kv(setups[d], "MaxDeltaS:="), 0.02, d)
            self.assertEqual(kv(setups[d], "SolveType:="), "Single", d)
            self.assertEqual(kv(setups[d], "MaximumPasses:="), 15, d)
            edges = [s for s in sweeps[d] if s[0] == "NAME:Edges_and_f0"][0]
            self.assertEqual(kv(edges, "RangeCount:="), 3, d)
        self.assertEqual(kv(setups["US3_PS4"], "MaximumPasses:="), 15)

    def test_pyaedt_builder_setup_helpers(self):
        spec = __import__("importlib.util").util.spec_from_file_location("c", BUILD / "claude_pyaedt_ch9.py")
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.setup_props("P01_MS1"), {"Frequency": "7.9872GHz", "MaxDeltaS": 0.02, "MaximumPasses": 15})
        p = mod.setup_props("US3_PS4")
        self.assertEqual((p["MinimumConvergedPasses"], p["MaxDeltaS"], p["SolveType"]), (2, 0.01, "MultiFrequency"))
        self.assertEqual(sorted(p["MultipleAdaptiveFreqsSetup"]), ["7.7376GHz", "7.9872GHz", "8.2368GHz"])
        self.assertEqual(mod.EDGES_COUNT.get("US3_PS4"), 11)
        self.assertNotIn("P01_MS1", mod.EDGES_COUNT)


class ArrayScript(unittest.TestCase):
    def setUp(self):
        self.path = build_path("claude_aedt_array1x5_US3_PS4_param_ch9.py")
        self.src = self.path.read_text()

    def test_five_parasitics_eleven_boundaries_five_ports(self):
        fake = FakeAedt()
        fake.run(self.src)
        par = {rect_name(a): rect_z(a) for a in fake.of("CreateRectangle") if rect_name(a).startswith("Parasitic_")}
        self.assertEqual(par, {f"Parasitic_{i}": "par_z" for i in range(1, 6)})
        fc = fake.of("AssignFiniteCond")
        self.assertEqual(len(fc), 11)  # Ground + 5 patches + 5 parasitics
        self.assertEqual(sorted(kv(a[0], "Objects:=")[0] for a in fc if kv(a[0], "Objects:=")[0].startswith("Parasitic_")),
                         [f"Parasitic_{i}" for i in range(1, 6)])
        ports = fake.of("AssignLumpedPort")
        self.assertEqual(len(ports), 5)
        for i, a in enumerate(ports):
            self.assertEqual(a[0][0], f"NAME:P{i + 1}")
            start = kv(a[0], "Start:=")
            self.assertEqual(start[0], f"({i - 2})*arr_d")
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

    def test_p01_ms2_array_keeps_previous_setup(self):
        setups = literal(build_path("claude_aedt_array1x5_P01_MS2_param_ch9.py"), "SETUP_ARGS")
        self.assertEqual(kv(setups["P01_MS2"], "MinimumConvergedPasses:="), 1)
        self.assertEqual(kv(setups["P01_MS2"], "MaxDeltaS:="), 0.02)
        self.assertEqual(kv(setups["P01_MS2"], "SolveType:="), "Single")

    def test_header_states_which_array_is_simulated(self):
        self.assertNotIn("Ningun array se ha simulado", self.src)
        self.assertIn("ARR1x5 de P01_MS2 ya se simulo en HFSS", self.src)
        self.assertIn("par_L, par_W", self.src)
        self.assertIn("arr_d", self.src.split("import ScriptEnv")[0])


class ExportersWithUs3Ps4(unittest.TestCase):
    NAME = "ARR1x5_US3_PS4_dparam"
    VARS = ["arr_d='%gmm' board_x='%gmm'" % (d, 4 * d + 26) for d in (16.5, 17, 17.5, 18, 18.2, 18.5, 19, 19.5)]

    def test_array_exporter_default_grid_and_restore_nominal(self):
        out = tempfile.mkdtemp()
        fake = FakeAedt(out=out, nominal="arr_d='17mm' board_x='94mm'", variations=self.VARS)
        src = set_design((EXPORT / "claude_aedt_export_array_ch9.py").read_text(), self.NAME)
        fake.run(src)
        nets = fake.of("ExportNetworkData")
        self.assertEqual(len(nets), 8)  # 16.5..19.5 every 0.5 (7) + 18.2
        self.assertTrue(any(n[3].endswith("ARR1x5_d18p2mm.s5p") for n in nets))
        self.assertEqual(len(fake.of("CreateReport")), 5)  # FIELDS_ARR_D_MM = [18.2]
        self.assertTrue((Path(out) / "ch9_array_export" / (self.NAME + "_d18p2mm") / "ff_P1.csv").is_file())
        changes = [c[2][0][1][2][1][2] for c in fake.calls if c[1] == "ChangeProperty"]
        self.assertEqual(changes, ["18.2mm", "17mm"])

    def test_fields_exporter_default_batch(self):
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
