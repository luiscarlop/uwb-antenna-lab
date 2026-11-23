"""Layout of antenna_design/hfss/ after the 2026-11-17 reorganisation: build/, export/, analysis/, results/, legacy/."""
import re
import unittest

from hfss_paths import ANALYSIS, BUILD, EXPORT, HFSS, RESULTS

DESIGNS = ["P01_MS1", "P01_MS2", "US3_MS3", "US3_PS4", "US3_PS6", "US3_PS4_2_1", "US3_PS6_4"]


class HfssLayout(unittest.TestCase):
    def test_build_has_one_folder_per_design_with_its_native_script(self):
        for d in DESIGNS:
            self.assertTrue((BUILD / d / f"claude_aedt_native_{d}_ch9.py").is_file(), d)
        for f in ("claude_pyaedt_ch9.py", "make_aedt_native_script.py", "make_aedt_array_script.py"):
            self.assertTrue((BUILD / f).is_file(), f)

    def test_array_scripts_live_in_their_element_folder(self):
        for d, names in {"P01_MS2": ["claude_aedt_array1x4_ch9.py", "claude_aedt_array1x4_P01_MS2_param_ch9.py",
                                     "claude_aedt_array1x5_P01_MS2_param_ch9.py"],
                         "US3_PS4": ["claude_aedt_array1x5_US3_PS4_param_ch9.py"],
                         "US3_PS6": ["claude_aedt_array1x5_US3_PS6_param_ch9.py"],
                         "US3_PS4_2_1": ["claude_aedt_array1x5_US3_PS4_2_1_param_ch9.py"],
                         "US3_PS6_4": ["claude_aedt_array1x5_US3_PS6_4_param_ch9.py"]}.items():
            for n in names:
                self.assertTrue((BUILD / d / n).is_file(), (d, n))

    def test_exporters_and_analysis_scripts(self):
        self.assertEqual(sorted(p.name for p in EXPORT.glob("*.py")),
                         ["claude_aedt_export_array_ch9.py", "claude_aedt_export_element_ch9.py",
                          "claude_aedt_export_fields_ch9.py"])
        self.assertEqual(sorted(p.name for p in ANALYSIS.glob("*.py")),
                         ["array_hfss_analysis.py", "array_mimo_metrics.py", "array_pitch_sweep_hfss.py",
                          "array_virtual_3d.py", "array_virtual_monostatic.py", "compare_hfss_openems.py", "element_hfss_patterns.py", "hfss_beam_squint.py", "hfss_parametric_patch_L.py",
                          "virtual_array_pattern.py", "virtual_array_pitch_sweep.py"])

    def test_results_folders_are_per_design_and_undated(self):
        self.assertEqual(sorted(p.name for p in RESULTS.iterdir() if p.is_dir()), sorted("results_" + d for d in DESIGNS))
        for p in HFSS.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                self.assertIsNone(re.search(r"20\d\d-\d\d-\d\d", p.name), f"dated file name: {p}")
        for p in HFSS.iterdir():
            self.assertIsNone(re.match(r"results_20\d\d", p.name), p.name)

    def test_nothing_left_loose_in_the_root(self):
        self.assertEqual(sorted(p.name for p in HFSS.iterdir() if p.is_file()), ["CLAUDE_PYAEDT.md"])


if __name__ == "__main__":
    unittest.main()
