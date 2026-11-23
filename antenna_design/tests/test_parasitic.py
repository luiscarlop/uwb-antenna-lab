"""Buried parasitic patches (variant key "parasitic_patches") in em/patch_openems.py, round 24.

Pure-python tests (validation of z, polygons, warnings, substrate z lines, fixed_mesh_lines layers) run everywhere; the build tests
need openEMS/CSXCAD (source em/runtime_env.sh) and are skipped otherwise. No FDTD is ever run here."""
import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "em"))
import patch_openems as po  # noqa: E402

try:
    import CSXCAD  # noqa: F401
    import openEMS  # noqa: F401
    HAVE_SOLVER = True
except Exception:  # pragma: no cover
    HAVE_SOLVER = False

RECT = [[-5.7, -3.9], [5.7, -3.9], [5.7, 3.9], [-5.7, 3.9]]


def qw_variant(parasitics=None):
    """US3_MS3 (microstrip_edge_qw feed, U-slot patch, h = 2.07) read from the repository, optionally with parasitic patches."""
    data = json.loads((HERE / "variants" / "US3_MS3.json").read_text())
    data.pop("parasitic_patches", None)
    if parasitics is not None:
        data["parasitic_patches"] = parasitics
    return data


def probe_variant(parasitics=None, h=1.6):
    data = {"id": "TEST_PROBE", "substrate": {"name": "FR4_test", "eps_r": 4.4, "tan_delta": 0.017, "h_mm": h, "size_mm": [26.0, 26.0]},
            "metal": {"conductivity_S_m": 5.8e7, "thickness_m": 3.5e-5},
            "patch_polygon_mm": [[-5.0, -3.5], [5.0, -3.5], [5.0, 3.5], [-5.0, 3.5]],
            "feed": {"type": "probe_lumped_vertical", "x_mm": 0.0, "y_mm": -1.0, "z0_ohm": 50}}
    if parasitics is not None:
        data["parasitic_patches"] = parasitics
    return data


def strip_colors(xml_text):
    """CSXCAD draws a random fill/edge colour per property: not part of the model."""
    return re.sub(r'(FillColor|EdgeColor) R="\d+" G="\d+" B="\d+"', r"\1", xml_text)


def parse(data):
    poly = [tuple(map(float, p)) for p in data["patch_polygon_mm"]]
    slots = [[tuple(map(float, p)) for p in s] for s in data.get("slots_polygon_mm", [])]
    return po.parse_parasitics(data, poly, slots)


def par(z=1.035, polygon=RECT, name="par1", **kw):
    return {"name": name, "z_mm": z, "polygon_mm": polygon, **kw}


class ParasiticValidation(unittest.TestCase):
    def test_absent_key_gives_no_parasitics(self):
        self.assertEqual(parse(qw_variant()), [])
        self.assertEqual(parse(qw_variant([])), [])

    def test_valid_parasitic_normalised(self):
        (q,) = parse(qw_variant([par()]))
        self.assertEqual(q["name"], "par1")
        self.assertAlmostEqual(q["z_mm"], 1.035)
        self.assertAlmostEqual(q["area_mm2"], 11.4 * 7.8)
        self.assertEqual(q["bbox"], [-5.7, -3.9, 5.7, 3.9])

    def test_z_must_be_strictly_inside_the_substrate(self):
        h = 2.07
        for z in (0.0, h, -0.1, h + 0.1):
            with self.assertRaisesRegex(ValueError, "0 < z_mm < h_mm"):
                parse(qw_variant([par(z=z)]))

    def test_z_margin_of_one_substrate_cell(self):
        cell = 2.07 / (po.SUBSTRATE_LINES - 1)
        for z in (0.5 * cell, cell - 1e-3, 2.07 - cell + 1e-3, 2.07 - 0.5 * cell):
            with self.assertRaisesRegex(ValueError, "closer than one substrate mesh cell"):
                parse(qw_variant([par(z=z)]))
        for z in (cell, 2.07 - cell, 1.035):   # exactly one cell away is allowed
            self.assertEqual(len(parse(qw_variant([par(z=z)]))), 1)

    def test_margin_follows_the_mesh_profile(self):
        saved = po.SUBSTRATE_LINES
        try:
            po.SUBSTRATE_LINES = 15   # xfine: cell 0.148 mm
            self.assertEqual(len(parse(qw_variant([par(z=0.16)]))), 1)
            po.SUBSTRATE_LINES = 5    # cell 0.5175 mm
            with self.assertRaises(ValueError):
                parse(qw_variant([par(z=0.16)]))
        finally:
            po.SUBSTRATE_LINES = saved

    def test_polygon_checks(self):
        with self.assertRaisesRegex(ValueError, "exceeds the board"):
            parse(qw_variant([par(polygon=[[-14, -1], [14, -1], [14, 1], [-14, 1]])]))
        with self.assertRaisesRegex(ValueError, "simple"):   # bow tie
            parse(qw_variant([par(polygon=[[-1, -1], [1, 1], [1, -1], [-1, 1]])]))
        with self.assertRaisesRegex(ValueError, ">= 3"):
            parse(qw_variant([par(polygon=[[-1, -1], [1, 1]])]))
        with self.assertRaisesRegex(ValueError, "lacks 'z_mm'"):
            parse(qw_variant([{"name": "x", "polygon_mm": RECT}]))
        with self.assertRaisesRegex(ValueError, "unique"):
            parse(qw_variant([par(), par()]))

    def test_slot_must_lie_in_the_parasitic_bbox(self):
        ok = par(slots_polygon_mm=[[[-1, -1], [1, -1], [1, 1], [-1, 1]]])
        self.assertEqual(len(parse(qw_variant([ok]))[0]["slots"]), 1)
        bad = par(slots_polygon_mm=[[[-9, -1], [1, -1], [1, 1], [-9, 1]]])
        with self.assertRaisesRegex(ValueError, "bounding box"):
            parse(qw_variant([bad]))

    def test_warning_when_not_under_the_patch(self):
        under = parse(qw_variant([par(polygon=[[-3, -2], [3, -2], [3, 2], [-3, 2]])]))[0]
        self.assertEqual(under["warnings"], [])
        self.assertAlmostEqual(under["fraction_under_patch_outline"], 1.0, places=6)
        partly = parse(qw_variant([par()]))[0]    # 7.8 mm in y over a 6.502 mm patch
        self.assertEqual(len(partly["warnings"]), 1)
        self.assertAlmostEqual(partly["fraction_under_patch_outline"], 6.502 / 7.8, delta=0.01)
        away = parse(qw_variant([par(polygon=[[-5, 6], [5, 6], [5, 9], [-5, 9]])]))[0]
        self.assertEqual(away["fraction_under_patch_outline"], 0.0)
        self.assertIn("NOT under", away["warnings"][0])   # warning, not an error

    def test_parasitic_under_the_microstrip_line_is_allowed(self):
        # same projection as the transformer but z < h: not a short (the feed copper is at z = h)
        under_line = par(polygon=[[-1, -9], [1, -9], [1, -4], [-1, -4]])
        self.assertEqual(len(parse(qw_variant([under_line]))), 1)

    def test_parasitic_cannot_touch_the_launch_plane_port(self):
        with self.assertRaisesRegex(ValueError, "launch plane"):
            parse(qw_variant([par(polygon=[[-1, -13], [1, -13], [1, -4], [-1, -4]])]))

    def test_probe_through_the_parasitic_is_rejected_unless_slotted(self):
        with self.assertRaisesRegex(ValueError, "probe"):
            parse(probe_variant([par(z=0.8, polygon=[[-4, -2.5], [4, -2.5], [4, 2.5], [-4, 2.5]])]))
        slotted = par(z=0.8, polygon=[[-4, -2.5], [4, -2.5], [4, 2.5], [-4, 2.5]],
                      slots_polygon_mm=[[[-0.5, -1.5], [0.5, -1.5], [0.5, -0.5], [-0.5, -0.5]]])
        self.assertEqual(len(parse(probe_variant([slotted]))), 1)

    def test_same_z_overlap_and_close_z_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "share z_mm"):
            parse(qw_variant([par(name="a"), par(name="b")]))
        with self.assertRaisesRegex(ValueError, "closer than one substrate mesh cell"):
            parse(qw_variant([par(name="a", z=1.0), par(name="b", z=1.1)]))
        self.assertEqual(len(parse(qw_variant([par(name="a", z=0.7), par(name="b", z=1.4)]))), 2)

    def test_load_variant_ignores_the_new_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v.json"
            path.write_text(json.dumps(qw_variant([par()])))
            data, poly, slots = po.load_variant(path)
        self.assertEqual(len(data["parasitic_patches"]), 1)


class SubstrateZLines(unittest.TestCase):
    def test_without_parasitics_identical_to_linspace(self):
        for h, n in ((2.07, 9), (1.6, 11), (2.07, 15)):
            self.assertTrue(np.array_equal(po.substrate_z_lines(h, n), np.linspace(0, h, n)))

    def test_z_on_an_existing_line_keeps_all_other_lines(self):
        base = np.linspace(0, 2.07, 9)
        lines = po.substrate_z_lines(2.07, 9, [1.035])
        self.assertEqual(len(lines), 9)
        self.assertIn(1.035, lines.tolist())
        self.assertTrue(np.allclose(lines, base, atol=1e-12))

    def test_off_grid_z_gets_a_hard_line_and_a_smooth_split(self):
        lines = po.substrate_z_lines(1.6, 9, [1.035])
        self.assertEqual(len(lines), 9)
        self.assertEqual(lines[0], 0.0)
        self.assertEqual(lines[-1], 1.6)
        self.assertTrue(np.any(np.isclose(lines, 1.035, atol=1e-12, rtol=0)))
        g = np.diff(lines)
        self.assertTrue(np.all(g > 0))
        self.assertLess(float(np.max(g[1:] / g[:-1])), 1.3)
        self.assertLess(float(np.max(g[:-1] / g[1:])), 1.3)
        # two parasitics
        two = po.substrate_z_lines(2.07, 9, [0.7, 1.4])
        self.assertEqual(len(two), 9)
        for z in (0.7, 1.4):
            self.assertTrue(np.any(np.isclose(two, z, atol=1e-12, rtol=0)))


class MeshLayers(unittest.TestCase):
    def test_layer_edges_are_evaluated_against_their_own_metal(self):
        patch = [(-5.0, -3.0), (5.0, -3.0), (5.0, 3.0), (-5.0, 3.0)]
        small = [(-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0)]
        base, _ = po.fixed_mesh_lines(patch, [], None, (13, 13), 0.25, 35)
        lay, rep = po.fixed_mesh_lines(patch, [], None, (13, 13), 0.25, 35, layers=[(small, [])])
        self.assertEqual(base["x"], po.fixed_mesh_lines(patch, [], None, (13, 13), 0.25, 35, layers=None)[0]["x"])
        # the parasitic edge x = -2 (metal on the + side) gets the thirds rule: -2 + 0.25/3 inside, -2 - 0.5/3 outside
        for axis, c in (("x", -2.0), ("x", 2.0), ("y", -1.0), ("y", 1.0)):
            near = [v for v in lay[axis] if abs(v - c) < 0.3]
            self.assertGreaterEqual(len(near), 2, (axis, c, near))
        self.assertTrue(any(abs(v - (-2.0 + 0.25 / 3)) < 1e-6 for v in lay["x"]))
        self.assertTrue(any(abs(v - (-2.0 - 0.5 / 3)) < 1e-6 for v in lay["x"]))
        self.assertGreater(len(lay["x"]), len(base["x"]))
        self.assertGreater(rep["rule_edges"]["x"], 0)


@unittest.skipUnless(HAVE_SOLVER, "openEMS/CSXCAD not available (source em/runtime_env.sh)")
class ParasiticBuild(unittest.TestCase):
    """Prepare-only builds (no FDTD; about 0.3 s each)."""
    OPTS = {"edge_port": "lumped", "nf2ff": True, "nf2ff_points": 11}

    def build(self, data, tmp, name):
        variant = Path(tmp) / f"{name}.json"
        variant.write_text(json.dumps(data))
        out = Path(tmp) / name
        _, _, meta, _ = po.build(variant, out, self.OPTS)
        return meta, out

    def test_qw_with_parasitic_mesh_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta, out = self.build(qw_variant([par()]), tmp, "ps")
            zl = np.asarray(json.loads(json.dumps(meta["geometry"]["substrate_z_lines_mm"])))
            mesh_z = [float(r.split(",")[1]) for r in (out / "native_mesh.csv").read_text().splitlines()[1:] if r.startswith("z,")]
            self.assertTrue(any(abs(v - 1.035) < 1e-9 for v in mesh_z))
            self.assertTrue(all(any(abs(v - w) < 1e-9 for v in mesh_z) for w in (0.0, 2.07)))
            (pm,) = meta["geometry"]["parasitic_patches"]
            self.assertEqual(pm["z_mm"], 1.035)
            self.assertEqual(pm["z_cells"]["ground_to_parasitic"] + pm["z_cells"]["parasitic_to_patch"], po.SUBSTRATE_LINES - 1)
            self.assertEqual(pm["z_cells"]["ground_to_parasitic"], 4)
            self.assertEqual(pm["z_cells"]["parasitic_to_patch"], 4)
            self.assertEqual(len(zl), po.SUBSTRATE_LINES)
            self.assertEqual(len(meta["warnings"]), 1)   # parasitic 7.8 mm wide in y over a 6.5 mm patch
            self.assertTrue(meta["parasitic_summary"])
            for axis in "xyz":   # grading limit of the polygon path
                self.assertLessEqual(meta["mesh"][axis]["max_neighbor_ratio"], po.POLY_GRADING_LIMIT + 1e-8)
            # x/y: the thirds rule puts a line on each side of every parasitic edge (edge itself falls inside a cell, as for the patch)
            for axis, c in (("x", -5.7), ("x", 5.7), ("y", -3.9), ("y", 3.9)):
                vals = [float(r.split(",")[1]) for r in (out / "native_mesh.csv").read_text().splitlines()[1:] if r.startswith(axis + ",")]
                self.assertTrue(any(0 < c - v < 0.25 for v in vals) and any(0 < v - c < 0.25 for v in vals), (axis, c))
            xml = (out / po.XML_NAME).read_text()
            self.assertIn("parasitic_par1_copper", xml)
            self.assertIn('Elevation="1.035000e+00"', xml)
            self.assertEqual(meta["materials"]["conductivity_S_m"], 58000000.0)

    def test_off_grid_z_has_a_hard_line_and_the_cells_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = probe_variant([par(z=0.9, polygon=[[-4, -2.5], [4, -2.5], [4, 2.5], [-4, 2.5]],
                                      slots_polygon_mm=[[[-0.6, -1.6], [0.6, -1.6], [0.6, -0.4], [-0.6, -0.4]]])])
            meta, out = self.build(data, tmp, "probe_ps")
            (pm,) = meta["geometry"]["parasitic_patches"]
            self.assertTrue(any(abs(v - 0.9) < 1e-9 for v in meta["geometry"]["substrate_z_lines_mm"]))
            self.assertEqual(pm["z_cells"]["ground_to_parasitic"] + pm["z_cells"]["parasitic_to_patch"], po.SUBSTRATE_LINES - 1)
            self.assertIsNotNone(pm["slot_mesh_check"])
            self.assertEqual(meta["geometry"]["patch_primitive"], "AddPolygon")
            xml = (out / po.XML_NAME).read_text()
            self.assertIn("parasitic_par1_slot_substrate", xml)

    def test_variant_without_the_key_is_unchanged(self):
        """No parasitic key: no parasitic content anywhere, and the XML/mesh of the existing variants do not depend on the new code
        (same prepared layout; compared against a variant that carries an empty list)."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("US3_MS3", "P01_MS2"):
                plain = json.loads((HERE / "variants" / f"{name}.json").read_text())
                plain.pop("parasitic_patches", None)
                empty = copy.deepcopy(plain)
                empty["parasitic_patches"] = []
                m_plain, o_plain = self.build(plain, tmp, f"{name}_plain")
                m_empty, o_empty = self.build(empty, tmp, f"{name}_empty")
                self.assertEqual(strip_colors((o_plain / po.XML_NAME).read_text()), strip_colors((o_empty / po.XML_NAME).read_text()))
                self.assertEqual((o_plain / "native_mesh.csv").read_bytes(), (o_empty / "native_mesh.csv").read_bytes())
                self.assertNotIn("parasitic", (o_plain / po.XML_NAME).read_text())
                for key in ("warnings", "parasitic_summary"):
                    self.assertNotIn(key, m_plain)
                self.assertNotIn("parasitic_patches", m_plain["geometry"])
                self.assertEqual(m_plain["mesh"], m_empty["mesh"])
                self.assertEqual(m_plain["budget_before_solve"], m_empty["budget_before_solve"])
                self.assertEqual(m_plain["total_cells"], m_empty["total_cells"])


if __name__ == "__main__":
    unittest.main()
