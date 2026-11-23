"""The HFSS builder's parameters must reproduce the simulated variant geometry (no AEDT needed)."""
import importlib.util
import unittest

from hfss_paths import BUILD

SCRIPT = BUILD / "claude_pyaedt_ch9.py"


def load():
    spec = importlib.util.spec_from_file_location("claude_pyaedt_ch9", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestHfssBuilderParameters(unittest.TestCase):
    def test_parameters_match_variants(self):
        mod = load()
        for design in mod.DESIGNS:
            self.assertEqual(mod.check(design), [], design)

    def test_mismatch_is_detected(self):
        mod = load()
        mod.DESIGNS["US3_MS3"] = dict(mod.DESIGNS["US3_MS3"], Lu=mod.DESIGNS["US3_MS3"]["Lu"] + 0.05)
        self.assertTrue(mod.check("US3_MS3"))


if __name__ == "__main__":
    unittest.main()


class TestNativeAedtScript(unittest.TestCase):
    """The generated native AEDT scripts (one per design, in build/<design>/) must carry the same variable values."""

    def test_native_variables_match(self):
        import ast
        mod = load()
        for design, p in mod.DESIGNS.items():
            native = SCRIPT.parent / design / f"claude_aedt_native_{design}_ch9.py"
            self.assertTrue(native.is_file(), native)
            tree = ast.parse(native.read_text())
            values = None
            for node in tree.body:
                if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "VARIABLES":
                    values = ast.literal_eval(node.value)
            self.assertIsNotNone(values, design)
            self.assertIn('DESIGNS_TO_BUILD = ["%s"]' % design, native.read_text())
            got = dict(values[design])
            for k, v in p.items():
                self.assertEqual(got[mod.VARNAME[k]], f"{v}mm", (design, k))

    def test_one_build_folder_per_design(self):
        mod = load()
        self.assertEqual(sorted(p.name for p in SCRIPT.parent.iterdir() if p.is_dir() and p.name != "__pycache__"),
                         sorted(mod.DESIGNS))
