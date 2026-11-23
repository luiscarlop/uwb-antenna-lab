"""Probe-fed (vertical lumped 50 ohm port) U-slot series, round 12: NF2FF with the lumped port, PORT_INVALID gate, radiated group
delay unwrap criterion, h != 1.6 mm and the polygon-path mesh (port lines, ratio, cells across the slot).

Pure-numpy tests run everywhere; the build tests need openEMS/CSXCAD (source em/runtime_env.sh) and are skipped otherwise.
No FDTD is ever run here."""
import json
import math
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "em"))
import patch_openems as po  # noqa: E402

try:  # the build needs the solver bindings
    import CSXCAD  # noqa: F401
    import openEMS  # noqa: F401
    HAVE_SOLVER = True
except Exception:  # pragma: no cover
    HAVE_SOLVER = False


def uslot_variant(h=2.07, slot_w=0.8, patch=(10.0, 7.3), s_over_l=0.34, u_outer=6.0, arm=4.0, y_base=-1.4):
    """Probe-fed rectangular patch with one U-slot (same family as the round 12 scratch variant)."""
    w, l_ = patch
    hw = u_outer / 2
    slot = [(-hw, y_base), (hw, y_base), (hw, y_base + arm), (hw - slot_w, y_base + arm), (hw - slot_w, y_base + slot_w),
            (-hw + slot_w, y_base + slot_w), (-hw + slot_w, y_base + arm), (-hw, y_base + arm)]
    return {"id": "TEST_USLOT", "substrate": {"name": "FR4_test", "eps_r": 4.4, "tan_delta": 0.017, "h_mm": h, "size_mm": [26.0, 26.0]},
            "metal": {"conductivity_S_m": 5.8e7, "thickness_m": 3.5e-5},
            "patch_polygon_mm": [[-w / 2, -l_ / 2], [w / 2, -l_ / 2], [w / 2, l_ / 2], [-w / 2, l_ / 2]],
            "slots_polygon_mm": [[list(p) for p in slot]],
            "feed": {"type": "probe_lumped_vertical", "x_mm": 0.0, "y_mm": round(-s_over_l * l_, 4), "z0_ohm": 50}}


class FakePort:
    """Stands in for the openEMS LumpedPort: CalcPort fills the same attributes (uf_inc/uf_ref/uf_tot/if_tot/P_inc/P_acc)."""

    def __init__(self, gamma, z0=50.0):
        self.gamma, self.z0 = gamma, z0

    def CalcPort(self, path, freq, **kw):
        f = np.atleast_1d(np.asarray(freq, dtype=float))
        a = np.exp(-2.25 * (f - po.F0_HZ) ** 2 / 1e18) * np.exp(1j * 0.3 * f / 1e9)   # Gaussian incident spectrum with some phase
        g = self.gamma(f) if callable(self.gamma) else self.gamma * np.ones_like(f)
        self.uf_inc, self.uf_ref = a, g * a
        self.uf_tot = a * (1 + g)
        self.if_tot = a * (1 - g) / self.z0
        self.P_inc = 0.5 * np.abs(a) ** 2 / self.z0
        self.P_acc = self.P_inc * (1 - np.abs(g) ** 2)


def lumped_metadata(prad_out=None):
    return {"id": "TEST", "port": {"reference_ohm": 50.0, "type": "ideal vertical lumped line"}, "excitation": {"corner_offset_hz": 1e9},
            "native_xml_sha256": "x", "variant_sha256": "y",
            "far_field": {"frequencies_hz": [float(f) for f in po.NF2FF_BAND_POINTS[11]], "theta_deg": po.NF2FF_THETA_DEG,
                          "phi_deg": po.NF2FF_PHI_DEG, "radius_m": 1.0, "phase_center_m": [0.0, 0.0, 0.0]}}


class FakeRes:
    """Synthetic NF2FF result (theta x phi arrays). Broadside y-polarised field = c * a_inc(f) * exp(-j omega tau0) * exp(-jkr)/r."""

    def __init__(self, uf_inc, tau0_s=0.35e-9, jump_at=None, null_at=None):
        freqs = np.array(po.NF2FF_BAND_POINTS[11], dtype=float)
        self.freq, self.r = freqs, np.array([1.0])
        self.theta, self.phi = np.deg2rad(po.NF2FF_THETA_DEG), np.deg2rad(po.NF2FF_PHI_DEG)
        k = 2 * np.pi * freqs / po.C0
        self.E_theta, self.E_phi, self.P_rad = [], [], []
        pattern = np.cos(self.theta / 2)[:, None] ** 2 * np.ones((1, len(self.phi)))
        for n, f in enumerate(freqs):
            h = 0.02 * uf_inc[n] * np.exp(-1j * 2 * np.pi * f * tau0_s) * np.exp(-1j * k[n] * 1.0)
            if jump_at is not None and n >= jump_at:
                h = -h                                  # pi phase jump between two adjacent points
            if null_at is not None and n == null_at:
                h = h * 1e-3                            # broadside null
            self.E_phi.append(h * pattern)
            self.E_theta.append(0.05 * h * pattern)
            self.P_rad.append(np.abs(self.E_phi[-1]) ** 2 / (2 * 376.730313668))
        self.Prad = np.array([0.5 * 0.5 * abs(u) ** 2 / 50.0 * 0.5 for u in uf_inc])
        self.Dmax = np.array([3.0] * len(freqs))


class TestRadiatedGroupDelayCriterion(unittest.TestCase):
    def setUp(self):
        self.port = FakePort(0.3)
        self.freqs = np.array(po.NF2FF_BAND_POINTS[11], dtype=float)
        self.port.CalcPort("", self.freqs)
        self.resp = po.PortResponse(s11=self.port.uf_ref / self.port.uf_inc, zin=self.port.uf_tot / self.port.if_tot,
                                    uf_inc=self.port.uf_inc, uf_ref=self.port.uf_ref, uf_tot=self.port.uf_tot,
                                    if_tot=self.port.if_tot, p_inc=np.real(self.port.P_inc), p_acc=np.real(self.port.P_acc),
                                    z_line=None, s11_zline=None)
        self.plan = lumped_metadata()["far_field"]

    def test_pure_delay_is_recovered_and_reliable(self):
        res = FakeRes(self.resp.uf_inc, tau0_s=0.35e-9)
        table, gd = po.radiated_group_delay(res, self.resp, self.plan)
        self.assertEqual(table.shape, (11, 11))                      # 7 original columns + 2 x (phase step, reliable)
        self.assertEqual(gd["dominant_component"], "y_Ephi_phi0")
        y = gd["y_Ephi_phi0"]
        self.assertEqual(y["phase_unwrap"], "RELIABLE")
        self.assertAlmostEqual(y["tau_mean_ns"], 0.35, places=6)
        self.assertLess(y["tau_ripple_pp_ps"], 1e-3)
        self.assertEqual(y["tau_ripple_status"], "DIAGNOSTIC")
        self.assertEqual(gd["status"], "DIAGNOSTIC_NOT_VALIDATED")
        self.assertTrue(np.all(table[:, 8] == 1.0) and np.all(table[:, 10] == 1.0))

    def test_phase_jump_is_flagged_unreliable(self):
        res = FakeRes(self.resp.uf_inc, jump_at=6)                   # H -> -H at point 6: wrapped step ~ pi
        table, gd = po.radiated_group_delay(res, self.resp, self.plan)
        y = gd["y_Ephi_phi0"]
        self.assertEqual(y["phase_unwrap"], "UNRELIABLE")
        self.assertEqual(y["tau_ripple_status"], "UNRELIABLE_DO_NOT_USE")
        self.assertGreater(y["max_abs_phase_step_rad"], math.pi / 2)
        self.assertEqual(gd["status"], "DIAGNOSTIC_UNRELIABLE_PHASE_UNWRAP")
        self.assertLess(table[5:8, 10].min(), 1.0)                   # the points next to the jump are marked 0

    def test_broadside_null_is_flagged_unreliable(self):
        res = FakeRes(self.resp.uf_inc, null_at=4)
        _, gd = po.radiated_group_delay(res, self.resp, self.plan)
        y = gd["y_Ephi_phi0"]
        self.assertEqual(y["phase_unwrap"], "UNRELIABLE")
        self.assertLess(y["min_abs_H_rel_to_max_db"], -20.0)

    def test_csv_header_documents_the_criterion(self):
        self.assertIn("reliable_y_step_lt_pi_over_2_and_absH_gt_m20dB", po.GROUP_DELAY_CSV_HEADER)
        self.assertEqual(len(po.GROUP_DELAY_CSV_HEADER.split(",")), 11)
        self.assertIn("pi/2", po.GROUP_DELAY_CRITERION)

    def test_phase_step_limit_boundary(self):
        base = np.ones(11, dtype=complex)
        ok = base * np.exp(1j * np.arange(11) * (math.pi / 2 - 0.05))     # steps just below pi/2
        bad = base * np.exp(1j * np.arange(11) * (math.pi / 2 + 0.05))
        self.assertEqual(po.phase_unwrap_check(ok)["status"], "RELIABLE")
        self.assertEqual(po.phase_unwrap_check(bad)["status"], "UNRELIABLE")


class TestLumpedNf2ffOutputs(unittest.TestCase):
    """solve_outputs path with the lumped (probe) port: valid port -> NF2FF tables, invalid port -> channel metrics gated, no NF2FF."""

    class FakeBox:
        def __init__(self, port):
            self.port = port

        def CalcNF2FF(self, path, freqs, theta, phi, radius=1.0, center=None, read_cached=False, verbose=0):
            self.port.CalcPort("", freqs)
            return FakeRes(self.port.uf_inc)

    def run_solve(self, gamma):
        port = FakePort(gamma)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                po.solve_outputs(out, port, lumped_metadata(), 0.0, self.FakeBox(port))
            result = json.loads((out / "run_numeric.json").read_text())
            names = sorted(p.name for p in out.iterdir())
            summary = json.loads((out / "nf2ff_summary.json").read_text()) if (out / "nf2ff_summary.json").exists() else None
            gd_header = (out / "nf2ff_group_delay_broadside.csv").read_text().splitlines()[0] \
                if (out / "nf2ff_group_delay_broadside.csv").exists() else None
        return result, names, summary, gd_header

    def test_valid_lumped_port_gives_far_field_and_group_delay(self):
        result, names, summary, gd_header = self.run_solve(0.3)
        self.assertEqual(result["port_validity"], "OK")
        self.assertIn("channel_worst_s11_db", result)
        self.assertAlmostEqual(result["channel_worst_s11_db"], 20 * math.log10(0.3), places=6)
        self.assertEqual(result["far_field"]["status"], "EM_SIMULATED_FAR_FIELD")
        self.assertIn("nf2ff_group_delay_broadside.csv", names)
        self.assertIn("s11_complex.csv", names)
        self.assertNotIn("s11_measplane.csv", names)                 # no MSL planes for a lumped port
        self.assertEqual(gd_header, po.GROUP_DELAY_CSV_HEADER)
        row = summary["summary"][5]
        self.assertIn("s11_db_lumped_port_50ohm", row)
        self.assertNotIn("s11_db_launch_plane_50ohm", row)
        self.assertAlmostEqual(row["s11_db_lumped_port_50ohm"], 20 * math.log10(0.3), places=6)
        # P_inc / P_acc of the 50 ohm lumped port: P_acc = P_inc (1 - |S11|^2)
        self.assertAlmostEqual(row["P_acc_W"] / row["P_inc_W"], 1 - 0.3 ** 2, places=9)
        self.assertAlmostEqual(row["radiation_efficiency_Prad_over_Pacc"] / row["total_efficiency_Prad_over_Pinc"], 1 / (1 - 0.3 ** 2), places=9)
        self.assertAlmostEqual(row["mismatch_loss_db"], -10 * math.log10(1 - 0.09), places=9)
        self.assertIn("lumped port", summary["power_reference"])
        self.assertEqual(summary["radiated_group_delay"]["dominant_phase_unwrap"], "RELIABLE")

    def test_port_invalid_gate_applies_to_the_lumped_port(self):
        result, names, summary, _ = self.run_solve(1.1)                # |S11| = 1.1 > 1.02 and P_acc < 0
        self.assertEqual(result["port_validity"], "PORT_INVALID")
        self.assertNotIn("channel_worst_s11_db", result)
        self.assertIn("invalid_channel_worst_s11_db", result)
        self.assertEqual(result["far_field"]["status"], "SKIPPED_PORT_INVALID")
        self.assertNotIn("nf2ff_summary.json", names)
        self.assertNotIn("nf2ff_group_delay_broadside.csv", names)

    def test_gate_trips_on_negative_p_acc_alone(self):
        # |S11| 1.01 is below the 1.02 limit but P_acc < 0: still invalid
        result, _, _, _ = self.run_solve(1.01)
        self.assertEqual(result["port_validity"], "PORT_INVALID")
        reasons = result["port_validity_detail"]["reasons"]
        self.assertTrue(any("P_acc" in r for r in reasons))
        self.assertFalse(any("max|S11|" in r for r in reasons))

    def test_gate_limit_passive_port_with_s11_just_below_one(self):
        result, _, _, _ = self.run_solve(0.999)
        self.assertEqual(result["port_validity"], "OK")


class TestSlotMeshCheck(unittest.TestCase):
    def test_polygon_chords_of_the_u(self):
        v = uslot_variant()
        slot = [tuple(p) for p in v["slots_polygon_mm"][0]]
        arms = po.polygon_chords(slot, "x", 1.0)                     # above the base: the two 0.8 mm arms
        self.assertEqual(len(arms), 2)
        self.assertAlmostEqual(arms[0][1] - arms[0][0], 0.8, places=9)
        base = po.polygon_chords(slot, "x", -1.2)                    # inside the 0.8 mm base: one 6 mm chord
        self.assertEqual(len(base), 1)
        self.assertAlmostEqual(base[0][1] - base[0][0], 6.0, places=9)

    def test_cells_across_counts_centres_inside(self):
        slot = [tuple(p) for p in uslot_variant()["slots_polygon_mm"][0]]
        coarse = {"x": np.arange(-10, 10.01, 0.5), "y": np.arange(-10, 10.01, 0.5)}     # 0.5 mm cells: 0.8 mm slot -> 1-2 cells
        fine = {"x": np.arange(-10, 10.01, 0.1), "y": np.arange(-10, 10.01, 0.1)}
        self.assertEqual(po.slot_mesh_check([slot], coarse)["status"], "WARN_FEWER_THAN_3_CELLS_ACROSS_SLOT")
        rep = po.slot_mesh_check([slot], fine)
        self.assertEqual(rep["status"], "OK")
        self.assertGreaterEqual(rep["slots"][0]["min_cells_across"], 7)


@unittest.skipUnless(HAVE_SOLVER, "openEMS/CSXCAD not importable (source antenna_design/em/runtime_env.sh)")
class TestProbeUslotBuild(unittest.TestCase):
    """build() of a probe-fed U-slot patch, h = 2.07 mm; no FDTD run."""

    def build(self, variant, nf2ff=False):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            vp = tmp / "v.json"
            vp.write_text(json.dumps(variant))
            out = tmp / "run"
            _, port, meta, box = po.build(vp, out, {"nf2ff": nf2ff, "nf2ff_points": 11})
            root = ET.parse(out / po.XML_NAME).getroot()
            native = np.genfromtxt(out / "native_mesh.csv", delimiter=",", skip_header=1, dtype=None, encoding=None)
            axes = {a: np.array([c for ax, c in native if ax == a], dtype=float) for a in "xyz"}
        return meta, root, axes, box

    def test_h_207_is_applied_everywhere(self):
        h = 2.07
        meta, root, axes, _ = self.build(uslot_variant(h=h))
        self.assertEqual(meta["materials"]["h_mm"], h)
        z = axes["z"]
        for v in (0.0, h):
            self.assertTrue(np.any(np.isclose(z, v, atol=1e-12, rtol=0)), f"z line {v}")
        sub = z[(z >= -1e-12) & (z <= h + 1e-12)]
        self.assertEqual(len(sub), po.SUBSTRATE_LINES)
        self.assertTrue(np.allclose(np.diff(sub), h / (po.SUBSTRATE_LINES - 1)))
        self.assertEqual(meta["port"]["start_mm"][2], 0)
        self.assertEqual(meta["port"]["stop_mm"][2], h)
        zs = set()
        for el in root.iter("LumpedElement"):
            for p in el.iter("P2"):
                zs.add(round(float(p.get("Z")), 9))
        self.assertEqual(zs, {h})
        elev = {round(float(pg.get("Elevation")), 9) for pg in root.iter("Polygon")}
        self.assertEqual(elev, {h})                                  # patch and slot polygons at z = h
        sub_box = [b for m in root.iter("Material") if m.get("Name") == "FR4_test" for b in m.iter("P2")]
        self.assertEqual(round(float(sub_box[0].get("Z")), 9), h)
        kappa = 2 * math.pi * po.F0_HZ * po.EPS0 * 4.4 * 0.017
        self.assertAlmostEqual(meta["materials"]["dielectric_conductivity_S_m"], kappa, places=12)   # independent of h

    def test_port_lines_ratio_and_slot_cells(self):
        meta, _, axes, _ = self.build(uslot_variant())
        feed = (0.0, -0.34 * 7.3)
        for a, v in zip("xy", feed):
            self.assertTrue(np.any(np.isclose(axes[a], v, atol=1e-12, rtol=0)))
        for a in "xyz":
            self.assertLessEqual(meta["mesh"][a]["max_neighbor_ratio"], 1.4 + 1e-6, a)
        self.assertEqual(meta["geometry"]["slot_mesh_check"]["status"], "OK")
        self.assertGreaterEqual(meta["geometry"]["slot_mesh_check"]["slots"][0]["min_cells_across"], 3)
        self.assertEqual(meta["geometry"]["polygon_mesh_report"]["probe_hard_lines_mm"], {"x": 0.0, "y": -2.482})
        self.assertIn("grid_lines_at_port", meta["port"])
        self.assertEqual(meta["geometry"]["patch_primitive"], "AddPolygon")

    def test_wide_slot_gap_is_infilled_to_the_ratio_target(self):
        # slot 1.0 mm, base at -1.2: arm tip 0.85 mm from the patch edge; without infill the y grading is 1.54 (> 1.5, RuntimeError)
        meta, _, _, _ = self.build(uslot_variant(slot_w=1.0, y_base=-1.2))
        self.assertLessEqual(meta["mesh"]["y"]["max_neighbor_ratio"], 1.4 + 1e-6)
        self.assertTrue(meta["geometry"]["smoothing_infill_lines_mm"]["y"])

    def test_h_16_changes_only_the_z_axis(self):
        m1, _, a1, _ = self.build(uslot_variant(h=1.6))
        m2, _, a2, _ = self.build(uslot_variant(h=2.07))
        self.assertAlmostEqual(m1["port"]["stop_mm"][2], 1.6)
        self.assertAlmostEqual(m2["port"]["stop_mm"][2], 2.07)
        self.assertNotAlmostEqual(m1["mesh"]["z"]["min_step_mm"], m2["mesh"]["z"]["min_step_mm"], places=3)
        self.assertAlmostEqual(m1["mesh"]["z"]["min_step_mm"], 1.6 / (po.SUBSTRATE_LINES - 1), places=9)
        self.assertAlmostEqual(m2["mesh"]["z"]["min_step_mm"], 2.07 / (po.SUBSTRATE_LINES - 1), places=9)
        self.assertEqual(m1["mesh"]["x"]["cells"], m2["mesh"]["x"]["cells"])

    def test_nf2ff_box_with_probe_feed(self):
        meta, root, _, box = self.build(uslot_variant(), nf2ff=True)
        ff = meta["far_field"]
        self.assertTrue(ff["enabled"])
        self.assertEqual(ff["frequency_points"], 11)
        self.assertEqual(ff["phase_center_m"], [0.0, 0.0, 0.0])
        self.assertIn("radiated_group_delay", ff)
        self.assertTrue(ff["radiated_group_delay"].startswith("ENABLED_DIAGNOSTIC"))
        self.assertEqual(len(list(root.iter("DumpBox"))), 2)
        # the box lies in air outside the 26 mm board and the 2.07 mm substrate
        self.assertGreater(ff["box_stop_mm"][2], 2.07)
        self.assertLess(ff["box_start_mm"][2], 0.0)
        self.assertGreater(ff["box_stop_mm"][0], 13.0)
        self.assertGreater(meta["budget_before_solve"]["nf2ff_overhead"]["added_cell_equivalents_per_step"], 0)


if __name__ == "__main__":
    unittest.main()
