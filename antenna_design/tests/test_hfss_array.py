import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

from hfss_paths import ANALYSIS, EXPORT, build_path, set_design


def load(name):
    spec = importlib.util.spec_from_file_location(name, ANALYSIS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ArrayScript(unittest.TestCase):
    def test_native_array_script_compiles_and_has_four_ports(self):
        src = (build_path("claude_aedt_array1x4_ch9.py")).read_text()
        compile(src, "claude_aedt_array1x4_ch9.py", "exec")
        self.assertIn("N_ELEM = 4", src)
        self.assertIn("PITCHES_MM = [13.5, 15.5, 17.0, 18.2]", src)
        for d in ("P01_MS2", "P01_MS1", "US3_MS3"):
            for q in ("13p5", "15p5", "17", "18p2"):
                self.assertIn(f"ARR1x4_{d}_d{q}mm", src)
        self.assertIn("('tr_l', '7.1mm')", src)  # P01_MS2 element

    def test_five_element_parametric_script(self):
        src = (build_path("claude_aedt_array1x5_P01_MS2_param_ch9.py")).read_text()
        compile(src, "claude_aedt_array1x5_P01_MS2_param_ch9.py", "exec")
        self.assertIn("N_ELEM = 5", src)
        self.assertIn("PARAMETRIC_PITCH = True", src)
        self.assertIn("ARR1x5_P01_MS2_dparam", src)

    def test_parametric_port_falls_back_to_numbers(self):
        """Run the 5-element script against a fake AEDT whose AssignLumpedPort rejects expressions."""
        import sys
        import types
        calls = []

        class Rec:
            def __init__(self, n):
                self.n = n

            def __getattr__(self, a):
                def f(*args):
                    calls.append((self.n, a, args))
                    if a == "AssignLumpedPort" and "arr_d" in repr(args):
                        raise RuntimeError("expression rejected")
                    if a in ("SetActiveDesign", "InsertDesign"):
                        return Rec("Design")
                    if a == "SetActiveEditor":
                        return Rec("Editor")
                    if a == "GetModule":
                        return Rec(args[0])
                    if a in ("GetActiveProject", "GetDefinitionManager"):
                        return Rec(a)
                    return "Project1" if a == "GetName" else None
                return f
        sys.modules["ScriptEnv"] = types.SimpleNamespace(Initialize=lambda *a: None)
        src = (build_path("claude_aedt_array1x5_P01_MS2_param_ch9.py")).read_text()
        src = src.replace("ARR_D_MM = [13.5 + 0.5 * i for i in range(15)] + [18.2]", "ARR_D_MM = [13.5, 17.0, 20.5]")
        src = src.replace("FIELDS_ARR_D_MM = [13.5]", "FIELDS_ARR_D_MM = [13.5, 17.0]")
        exec(compile(src, "x", "exec"), {"oDesktop": Rec("Desktop")})
        ok = [c for c in calls if c[1] == "AssignLumpedPort" and "arr_d" not in repr(c[2])]
        self.assertEqual(len(ok), 5)
        self.assertIn("'-34.0mm'", repr(ok[0][2]))  # P1 at -2 * 17 mm
        self.assertEqual(sum(1 for c in calls if c[1] == "AddMessage"), 5)

    def test_place_port_moves_only_the_integration_line(self):
        src = (build_path("claude_aedt_array1x4_ch9.py")).read_text()
        ns = {}
        start = src.index("def place_port")
        end = src.index("mat_name =")
        exec(src[start:end], ns)
        args = ["NAME:P1", "Objects:=", ["PortSheet_1"],
                ["NAME:Modes", ["NAME:Mode1", "UseIntLine:=", True,
                                ["NAME:IntLine", "Start:=", ["0mm", "-13.0mm", "0mm"],
                                 "End:=", ["0mm", "-13.0mm", "2.07mm"]]]]]
        out = ns["place_port"](args, -20.25)
        il = out[3][1][3]
        self.assertEqual(il[2], ["-20.25mm", "-13.0mm", "0mm"])
        self.assertEqual(il[4], ["-20.25mm", "-13.0mm", "2.07mm"])
        self.assertEqual(out[2], ["PortSheet_1"])
        self.assertEqual(args[3][1][3][2][0], "0mm")  # input untouched


class MimoMetrics(unittest.TestCase):
    def setUp(self):
        self.m = load("array_mimo_metrics")

    def write_s4p(self, f_ghz, s, fmt="MA"):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".s4p", delete=False)
        tmp.write(f"! test\n# GHZ S {fmt} R 50\n")
        for fk, sk in zip(f_ghz, s):
            vals = []
            for v in sk.reshape(-1):
                vals += [abs(v), np.degrees(np.angle(v))] if fmt == "MA" else [v.real, v.imag]
            tmp.write(f"{fk} " + " ".join(f"{x:.12g}" for x in vals[:8]) + "\n")
            for i in range(8, len(vals), 8):
                tmp.write(" ".join(f"{x:.12g}" for x in vals[i:i + 8]) + "\n")
        tmp.close()
        return Path(tmp.name)

    def test_roundtrip_and_uncoupled_array(self):
        f = np.array([7.7, 7.7376, 8.0, 8.2368, 8.3])
        s = np.zeros((5, 4, 4), complex)
        for i in range(4):
            s[:, i, i] = 0.2 * np.exp(1j * 0.3 * i)
        for fmt in ("MA", "RI"):
            fr, sr, z0 = self.m.read_touchstone(self.write_s4p(f, s, fmt))
            self.assertEqual(z0, 50.0)
            np.testing.assert_allclose(fr, f * 1e9)
            np.testing.assert_allclose(sr, s, atol=1e-9)
        out = self.m.metrics(f * 1e9, s, 13.5, [0, 30])
        self.assertEqual(out["channel_samples"], 3)
        self.assertAlmostEqual(out["ecc_s_param_channel_max"]["12"], 0.0)
        for th in ("theta0_0deg", "theta0_30deg"):  # no coupling: active = passive
            self.assertEqual(out["active"][th]["active_s_db_channel_worst_per_port"], [round(20 * np.log10(0.2), 2)] * 4)

    def test_active_reflection_with_coupling(self):
        f = np.array([8.0e9])
        s = np.zeros((1, 2, 2), complex)
        s[0] = [[0.1, 0.3], [0.3, 0.1]]
        g, tarc = self.m.active_gamma(s, self.m.steering(f, 2, 0.0135, 0.0))
        np.testing.assert_allclose(g[0], [0.4, 0.4])  # broadside: S11 + S12
        np.testing.assert_allclose(tarc, [0.4])
        ecc = self.m.ecc_from_s(s)[0, 0, 1]
        exp = abs(0.1 * 0.3 + 0.3 * 0.1) ** 2 / ((1 - 0.01 - 0.09) * (1 - 0.09 - 0.01))
        self.assertAlmostEqual(ecc, exp)



class VirtualArray(unittest.TestCase):
    def setUp(self):
        self.v = load("virtual_array_pattern")

    def test_default_sequence_and_virtual_positions(self):
        seq = self.v.default_sequence(4)
        self.assertEqual(len(seq), 12)
        self.assertIn((0, (1, 2)), seq)
        x = (np.arange(4) - 1.5) * 13.5e-3
        pos = {round(k * 1e3, 6): m for k, m in self.v.virtual_positions(seq, x).items()}
        self.assertEqual(pos, {-27.0: 4, -13.5: 4, 0.0: 8, 13.5: 4, 27.0: 4})
        self.assertEqual(self.v.parse_sequence("1:2,3 2:1,4"), [(0, (1, 2)), (1, (0, 3))])

    def test_default_sequence_is_tfg_rf_configs(self):
        # copy of RF_CONFIGS in src/main/uwb_cir_walk/config.py (TFG code, configs 1-12, 0-based)
        rf = ((0, (1, 2)), (0, (1, 3)), (0, (2, 3)), (1, (0, 2)), (1, (0, 3)), (1, (2, 3)),
              (2, (0, 1)), (2, (0, 3)), (2, (1, 3)), (3, (0, 1)), (3, (0, 2)), (3, (1, 2)))
        self.assertEqual(tuple(self.v.default_sequence(4)), rf)

    def test_loaded_fields(self):
        F = np.array([[1.0 + 0j, 2.0], [3.0, 4.0j]])  # 2 ports x 2 directions
        s12, g = 0.2 - 0.1j, 0.9
        S = np.array([[0, s12], [s12, 0]])
        np.testing.assert_allclose(self.v.loaded_fields(F, S, np.zeros(2)), F)
        out = self.v.loaded_fields(F, S, np.array([0, g]))
        np.testing.assert_allclose(out[0], F[0] + g * s12 * F[1])  # port 1 driven, port 2 reflects g

    def test_virtual_beam_isotropic_matches_sum(self):
        k, x = 2 * np.pi * 8e9 / self.v.C0, (np.arange(4) - 1.5) * 13.5e-3
        th = np.radians(np.arange(0, 91, 5.0))[:, None]
        F = np.array([np.exp(1j * k * xi * np.sin(th)) * np.ones((1, 1)) for xi in x])  # scalar, phi = 0 cut
        seq = self.v.default_sequence(4)
        B = self.v.virtual_beam(F, x, k, seq, 0.0)
        ref = sum(np.exp(1j * k * (x[t] + x[r]) * np.sin(th)) for t, rx in seq for r in rx)
        np.testing.assert_allclose(B, ref)
        self.assertAlmostEqual(abs(B[0, 0]), 24.0)

    def test_read_ff_csv(self):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        tmp.write('"Freq [GHz]","Phi [deg]","Theta [deg]","re(rETheta) [V]","im(rETheta) [V]","re(rEPhi) [V]","im(rEPhi) [V]"\n')
        for fr in (7.9872, 8.2368):
            for p in (0, 90):
                for t in (0, 5):
                    tmp.write(f"{fr},{p},{t},{p + t},{fr},{-t},1\n")
        tmp.close()
        th, ph, F = self.v.read_ff_csv(tmp.name, 7.9872)
        np.testing.assert_allclose(th, [0, 5])
        np.testing.assert_allclose(ph, [0, 90])
        self.assertEqual(F[0, 1, 1], 95 + 7.9872j)
        self.assertEqual(F[1, 1, 0], -5 + 1j)



class WideCsvAndCuts(unittest.TestCase):
    def setUp(self):
        self.v = load("virtual_array_pattern")

    def test_read_wide_csv_suffix_and_units(self):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        tmp.write("Phi[deg],Theta[deg],re(rETheta)[mV],re(rEPhi)[mV],im(rETheta)[mV],im(rEPhi)[mV],"
                  "re(rETheta)_1[mV],re(rETheta)_2[V],im(rETheta)_1[mV],im(rETheta)_2[V],"
                  "re(rEPhi)_1[mV],re(rEPhi)_2[V],im(rEPhi)_1[mV],im(rEPhi)_2[V]\n")
        tmp.write("0,0,1000,2000,3000,4000,5000,6,7000,8,9000,10,11000,12\n")
        tmp.close()
        _, _, F0 = self.v.read_ff_csv(tmp.name, 0, "")
        _, _, F1 = self.v.read_ff_csv(tmp.name, 0, "_1")
        _, _, F2 = self.v.read_ff_csv(tmp.name, 0, "_2")
        self.assertEqual((F0[0, 0, 0], F0[1, 0, 0]), (1 + 3j, 2 + 4j))
        self.assertEqual((F1[0, 0, 0], F1[1, 0, 0]), (5 + 7j, 9 + 11j))
        self.assertEqual((F2[0, 0, 0], F2[1, 0, 0]), (6 + 8j, 10 + 12j))

    def test_cut_metrics_interpolates_minus3db(self):
        t = np.arange(-90, 90.01, 5.0)
        db = -3 * (t / 11.0) ** 2  # exact -3 dB at +-11 deg, HPBW 22 deg
        m = self.v.cut_metrics(t, db)
        self.assertAlmostEqual(m["hpbw_deg"], 22.0, delta=0.6)
        self.assertEqual(m["peak_deg"], 0.0)

class ExportScript(unittest.TestCase):
    def test_export_script_against_fake_aedt(self):
        import sys
        import types
        calls = []
        out = tempfile.mkdtemp()
        header = '"Phi [deg]","Theta [deg]","re(rETheta) [mV]","im(rETheta) [V]","re(rEPhi) [V]","im(rEPhi) [V]"\n'

        class Rec:
            def __init__(self, n):
                self.n = n

            def __getattr__(self, a):
                def f(*args):
                    calls.append((self.n, a, args))
                    if a == "SetActiveDesign":
                        return Rec("Design")
                    if a == "GetModule":
                        return Rec(args[0])
                    if a == "GetActiveProject":
                        return Rec("Project")
                    if a == "GetPath":
                        return out
                    if a == "GetNominalVariation":
                        return "arr_d='17mm' board_m='13mm' board_x='94mm'"
                    if a == "GetAvailableVariations":
                        return ["arr_d='17mm' board_m='13mm' board_x='94mm'",
                                "arr_d='13.5mm' board_m='13mm' board_x='80mm'"]
                    if a == "ExportToFile":
                        Path(args[1]).write_text(header + "0,0,1000,1,0,0\n90,0,1,2,3,4\n")
                    return "Project1" if a == "GetName" else None
                return f
        sys.modules["ScriptEnv"] = types.SimpleNamespace(Initialize=lambda *a: None)
        src = set_design((EXPORT / "claude_aedt_export_array_ch9.py").read_text(), "ARR1x5_P01_MS2_dparam")
        self.assertIn("ARR_D_MM = [16.5 + 0.5 * i for i in range(7)] + [18.2]", src)  # US3_PS4 grid
        self.assertIn("FIELDS_ARR_D_MM = [18.2]", src)
        src = src.replace("ARR_D_MM = [16.5 + 0.5 * i for i in range(7)] + [18.2]", "ARR_D_MM = [13.5, 17.0, 20.5]")
        src = src.replace("FIELDS_ARR_D_MM = [18.2]", "FIELDS_ARR_D_MM = [13.5, 17.0]")
        exec(compile(src, "x", "exec"), {"oDesktop": Rec("Desktop")})
        nets = [c[2] for c in calls if c[1] == "ExportNetworkData"]
        self.assertEqual(len(nets), 2)
        self.assertTrue(nets[1][3].endswith("ARR1x5_d17mm.s5p"))
        reports = [c[2] for c in calls if c[1] == "CreateReport"]
        self.assertEqual(len(reports), 2 * 5)
        self.assertEqual(nets[0][0], "arr_d='13.5mm' board_m='13mm' board_x='80mm'")  # exact key, 20.5 skipped
        self.assertIn("board_x:=", reports[0][5])
        self.assertIn("80mm", repr(reports[0][5]))
        self.assertIn("Freq:=", reports[0][5])
        self.assertIn("arr_d:=", reports[0][5])
        srcs = [c[2][0] for c in calls if c[1] == "EditSources"]
        self.assertEqual([r[3] for r in srcs[1][1:]], ["0W", "1W", "0W", "0W", "0W"])  # second export: P2 active
        f = Path(out) / "ch9_array_export" / "ARR1x5_P01_MS2_dparam_d13p5mm" / "ff_P1.csv"
        th, ph, F = load("virtual_array_pattern").read_ff_csv(str(f), 7.9872)
        self.assertIn("==== fin", (Path(out) / "ch9_array_export" / "export_log.txt").read_text())
        self.assertAlmostEqual(F[0, 0, 0], 1 + 1j)  # 1000 mV -> 1 V



class ExportFieldsScript(unittest.TestCase):
    def run_script(self, out, calls, nominal="arr_d='17mm' board_x='94mm'", design=None):
        import sys
        import types

        class Rec:
            def __init__(self, n):
                self.n = n
                self.nominal = nominal

            def __getattr__(self, a):
                def f(*args):
                    calls.append((self.n, a, args))
                    if a == "SetActiveDesign":
                        return Rec("Design")
                    if a == "GetModule":
                        return Rec(args[0])
                    if a == "GetActiveProject":
                        return Rec("Project")
                    if a == "GetPath":
                        return out
                    if a == "GetNominalVariation":
                        return self.nominal
                    if a == "GetAvailableVariations":
                        return ["arr_d='18.2mm' board_x='98.8mm'", "arr_d='16.5mm' board_x='92mm'",
                                "arr_d='19.5mm' board_x='104mm'", "arr_d='15.5mm' board_x='88mm'"]
                    if a == "ExportToFile":
                        Path(args[1]).write_text("x")
                    return "Project1" if a == "GetName" else None
                return f
        sys.modules["ScriptEnv"] = types.SimpleNamespace(Initialize=lambda *a: None)
        src = (EXPORT / "claude_aedt_export_fields_ch9.py").read_text()
        src = set_design(src, design or "ARR1x5_P01_MS2_dparam")
        src = src.replace("MIN_CSV_BYTES = 1000", "MIN_CSV_BYTES = 1")  # fake AEDT writes 1-byte CSVs
        exec(compile(src, "x", "exec"), {"oDesktop": Rec("Desktop")})

    def test_fields_only_restores_nominal_and_resumes(self):
        src = (EXPORT / "claude_aedt_export_fields_ch9.py").read_text()
        self.assertIn("FIELDS_ARR_D_MM = [18.2, 16.5, 19.5]", src)
        self.assertNotIn("RESTORE_ARR_D", src)
        out, calls = tempfile.mkdtemp(), []
        self.run_script(out, calls, design="ARR1x5_US3_PS4_dparam")
        values = [c[2][0][1][2][1][2] for c in calls if c[1] == "ChangeProperty"]
        self.assertEqual(values, ["18.2mm", "16.5mm", "17mm"])  # stops at MAX_REPORTS_PER_RUN = 10, restores nominal
        self.assertEqual(sum(1 for c in calls if c[1] == "CreateReport"), 10)
        self.assertFalse(any(c[1] == "ExportNetworkData" for c in calls))
        calls1 = []
        self.run_script(out, calls1, design="ARR1x5_US3_PS4_dparam")  # relaunch: only 19.5 mm left
        self.assertEqual([c[2][0][1][2][1][2] for c in calls1 if c[1] == "ChangeProperty"], ["19.5mm", "17mm"])
        self.assertEqual(sum(1 for c in calls1 if c[1] == "CreateReport"), 5)
        self.assertTrue((Path(out) / "ch9_array_export" / "ARR1x5_US3_PS4_dparam_d19p5mm" / "ff_P5.csv").is_file())
        calls2 = []
        self.run_script(out, calls2, design="ARR1x5_US3_PS4_dparam")  # files exist: nothing re-exported, arr_d restored
        self.assertEqual(sum(1 for c in calls2 if c[1] == "CreateReport"), 0)
        self.assertEqual([c[2][0][1][2][1][2] for c in calls2 if c[1] == "ChangeProperty"], ["17mm"])

    def test_fields_restore_follows_nominal_not_a_fixed_value(self):
        out, calls = tempfile.mkdtemp(), []
        self.run_script(out, calls, nominal="arr_d='18.2mm' board_x='98.8mm'")
        values = [c[2][0][1][2][1][2] for c in calls if c[1] == "ChangeProperty"]
        self.assertEqual(values[-1], "18.2mm")

    def test_fields_without_nominal_does_not_invent_a_restore(self):
        out, calls = tempfile.mkdtemp(), []
        self.run_script(out, calls, nominal=None)
        values = [c[2][0][1][2][1][2] for c in calls if c[1] == "ChangeProperty"]
        self.assertEqual(values, ["18.2mm", "16.5mm"])  # stops at 10 reports; no fixed restore value
        log = (Path(out) / "ch9_array_export" / "export_fields_log.txt").read_text()
        self.assertIn("arr_d nominal desconocido", log)


class ConvergenceText(unittest.TestCase):
    BODY = ("DesignVariation : arr_d='18.2mm'\r\nSetup : S\r\n\r\n"
            "Completed : 16\r\nMaximum   : 25\r\nCriterion : Max Mag. Delta S\r\n"
            "Target    : 0.02\r\nCurrent   : 0.0094681\r\n"
            "Target Consecutive Passes  : 2\r\nCurrent Consecutive Passes : 2\r\n"
            "Converged : Yes\r\n          1|           4831|             N/A|\r\n")

    def test_conv_text(self):
        conv_text = load("array_hfss_analysis").conv_text
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "convergence.conv"
            p.write_bytes(self.BODY.encode())
            self.assertEqual(conv_text(p), "adaptive converged: Max Mag. Delta S 0.0094681 (target 0.02, "
                                           "2/2 consecutive passes), 16 of 25 passes")
            p.write_bytes(self.BODY.replace("Converged : Yes", "Converged : No").encode())
            self.assertIn("NOT converged", conv_text(p))
            p.write_text("garbage")
            self.assertEqual(conv_text(p), "convergence.conv unparsable")
            self.assertEqual(conv_text(Path(d) / "missing.conv"), "adaptive convergence data not provided")


if __name__ == "__main__":
    unittest.main()
