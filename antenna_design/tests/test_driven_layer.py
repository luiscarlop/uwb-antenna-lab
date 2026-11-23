"""Inverted stack (variant key "driven_z_mm", em/patch_openems.py round 32): the driven patch + microstrip feed on an inner layer z_d < h,
parasitics above (z_d < z <= h) or below it, vertical edge lumped port 0 -> z_d.

Pure-python tests run everywhere; the build tests need openEMS/CSXCAD (source em/runtime_env.sh) and are skipped otherwise.
No FDTD is ever run here."""
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

H = 2.07
CELL = H / (po.SUBSTRATE_LINES - 1)   # 0.25875 mm
RECT = [[-5.7, -4.0], [5.7, -4.0], [5.7, 4.0], [-5.7, 4.0]]
HINT_Y = [-3.6, -0.215]   # 11.4 x 8.0 parasitic edge at y = -4.0 next to the patch edge -3.251: needs a hint (same behaviour in the classic stack)


def qw_variant(zd=None, parasitics=None, hints=True):
    data = json.loads((HERE / "variants" / "US3_MS3.json").read_text())
    for k in ("parasitic_patches", "driven_z_mm"):
        data.pop(k, None)
    if zd is not None:
        data["driven_z_mm"] = zd
    if parasitics is not None:
        data["parasitic_patches"] = parasitics
    if hints:
        data["mesh_hint_lines_mm"] = {"y": HINT_Y}
    return data


def probe_variant(zd=None):
    data = {"id": "TEST_PROBE", "substrate": {"name": "FR4_test", "eps_r": 4.4, "tan_delta": 0.017, "h_mm": 1.6, "size_mm": [26.0, 26.0]},
            "metal": {"conductivity_S_m": 5.8e7, "thickness_m": 3.5e-5},
            "patch_polygon_mm": [[-5.0, -3.5], [5.0, -3.5], [5.0, 3.5], [-5.0, 3.5]],
            "feed": {"type": "probe_lumped_vertical", "x_mm": 0.0, "y_mm": -1.0, "z0_ohm": 50}}
    if zd is not None:
        data["driven_z_mm"] = zd
    return data


def par(z, name="top1", polygon=RECT, **kw):
    return {"name": name, "z_mm": z, "polygon_mm": polygon, **kw}


def parse(data):
    poly = [tuple(map(float, p)) for p in data["patch_polygon_mm"]]
    slots = [[tuple(map(float, p)) for p in s] for s in data.get("slots_polygon_mm", [])]
    return po.parse_parasitics(data, poly, slots)


def strip_colors(xml_text):
    return re.sub(r'(FillColor|EdgeColor) R="\d+" G="\d+" B="\d+"', r"\1", xml_text)


class DrivenLayerValidation(unittest.TestCase):
    def test_absent_key_is_the_classic_stack(self):
        d = po.parse_driven_layer(qw_variant())
        self.assertFalse(d["inverted"])
        self.assertFalse(d["key_present"])
        self.assertEqual(d["z_mm"], H)

    def test_key_equal_to_h_is_the_classic_stack(self):
        d = po.parse_driven_layer(qw_variant(H))
        self.assertFalse(d["inverted"])
        self.assertTrue(d["key_present"])
        self.assertEqual(d["z_mm"], H)

    def test_valid_inner_layer(self):
        d = po.parse_driven_layer(qw_variant(1.035))
        self.assertTrue(d["inverted"])
        self.assertAlmostEqual(d["z_mm"], 1.035)
        self.assertAlmostEqual(d["cell_mm"], CELL)

    def test_out_of_range_is_an_error(self):
        for z in (0.0, -0.5, H + 0.01, 5.0):
            with self.assertRaisesRegex(ValueError, "0 < driven_z_mm <= h_mm"):
                po.parse_driven_layer(qw_variant(z))
        for z in ("1.0", True, None, float("nan")):
            with self.assertRaises(ValueError):
                po.parse_driven_layer(qw_variant(z) if z is not None else {**qw_variant(), "driven_z_mm": None})

    def test_margin_of_one_substrate_cell_to_ground_and_top(self):
        for z in (0.5 * CELL, CELL - 1e-3, H - CELL + 1e-3, H - 0.5 * CELL):
            with self.assertRaisesRegex(ValueError, "closer than one substrate mesh cell"):
                po.parse_driven_layer(qw_variant(z))
        for z in (CELL, H - CELL, 1.035):
            self.assertTrue(po.parse_driven_layer(qw_variant(z))["inverted"])

    def test_probe_feed_is_rejected_when_inverted(self):
        with self.assertRaisesRegex(ValueError, "edge feeds"):
            po.parse_driven_layer(probe_variant(0.8))
        self.assertFalse(po.parse_driven_layer(probe_variant(1.6))["inverted"])   # == h is fine
        self.assertFalse(po.parse_driven_layer(probe_variant())["inverted"])


class ParasiticsWithDrivenLayer(unittest.TestCase):
    def test_parasitic_on_the_driven_layer_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "driven layer plane"):
            parse(qw_variant(1.035, [par(1.035)]))

    def test_parasitic_closer_than_a_cell_to_the_driven_layer_is_an_error(self):
        for z in (1.035 + 0.5 * CELL, 1.035 - 0.5 * CELL):
            with self.assertRaisesRegex(ValueError, "driven layer"):
                parse(qw_variant(1.035, [par(z)]))

    def test_parasitic_on_the_top_face_is_allowed_when_inverted(self):
        (q,) = parse(qw_variant(1.035, [par(H)]))
        self.assertEqual(q["z_mm"], H)
        # an overlap with the feed projection is only a warning above the driven layer
        self.assertTrue(any("loads the line" in w for w in q["warnings"]))

    def test_parasitic_between_driven_layer_and_top_or_below(self):
        zs = [1.035 + CELL, H - CELL, 1.035 - CELL, CELL]
        for z in zs:
            (q,) = parse(qw_variant(1.035, [par(z)]))
            self.assertAlmostEqual(q["z_mm"], z)

    def test_top_margin_still_applies_below_h(self):
        with self.assertRaisesRegex(ValueError, "closer than one substrate mesh cell"):
            parse(qw_variant(1.035, [par(H - 0.5 * CELL)]))
        with self.assertRaisesRegex(ValueError, "0 < z_mm <= h_mm"):
            parse(qw_variant(1.035, [par(H + 0.1)]))

    def test_classic_stack_still_rejects_z_equal_h(self):
        with self.assertRaisesRegex(ValueError, "0 < z_mm < h_mm"):
            parse(qw_variant(None, [par(H)]))
        with self.assertRaisesRegex(ValueError, "0 < z_mm < h_mm"):
            parse(qw_variant(H, [par(H)]))   # key == h: not inverted

    def test_parasitic_below_reaching_the_launch_plane_is_still_a_short(self):
        short = par(0.5175, polygon=[[-1, -13.0], [1, -13.0], [1, -8.0], [-1, -8.0]])
        with self.assertRaisesRegex(ValueError, "launch plane"):
            parse(qw_variant(1.035, [short]))


class ZLines(unittest.TestCase):
    def test_top_face_parasitic_adds_no_extra_line(self):
        lines = po.substrate_z_lines(H, po.SUBSTRATE_LINES, [H])
        np.testing.assert_allclose(lines, np.linspace(0, H, po.SUBSTRATE_LINES))

    def test_driven_layer_snaps_to_existing_line(self):
        lines = po.substrate_z_lines(H, po.SUBSTRATE_LINES, [1.035, H])
        self.assertEqual(len(lines), po.SUBSTRATE_LINES)
        self.assertTrue(np.any(np.isclose(lines, 1.035, atol=1e-12, rtol=0)))

    def test_off_grid_layers_get_hard_lines_and_shared_cells(self):
        lines = po.substrate_z_lines(H, po.SUBSTRATE_LINES, [0.8, 1.55, H])
        self.assertEqual(len(lines), po.SUBSTRATE_LINES)
        for z in (0.0, 0.8, 1.55, H):
            self.assertTrue(np.any(np.isclose(lines, z, atol=1e-12, rtol=0)), z)
        self.assertTrue(np.all(np.diff(lines) > 0))

    def test_duplicate_levels_collapse(self):
        lines = po.substrate_z_lines(H, po.SUBSTRATE_LINES, [0.8, 0.8, H])
        self.assertTrue(np.all(np.diff(lines) > 0))
        self.assertEqual(len(lines), po.SUBSTRATE_LINES)

    def test_no_levels_is_the_classic_linspace(self):
        np.testing.assert_array_equal(po.substrate_z_lines(H, po.SUBSTRATE_LINES), np.linspace(0, H, po.SUBSTRATE_LINES))


@unittest.skipUnless(HAVE_SOLVER, "openEMS/CSXCAD not available (source em/runtime_env.sh)")
class DrivenLayerBuild(unittest.TestCase):
    """Prepare-only builds (no FDTD)."""
    LUMPED = {"edge_port": "lumped", "nf2ff": True, "nf2ff_points": 11}

    def build(self, data, tmp, name, opts=None):
        variant = Path(tmp) / f"{name}.json"
        variant.write_text(json.dumps(data))
        out = Path(tmp) / name
        _, _, meta, _ = po.build(variant, out, opts or self.LUMPED)
        return meta, out

    @staticmethod
    def comparable(meta, out):
        m = {k: v for k, v in meta.items() if k not in ("script_sha256", "native_xml_sha256", "variant_file", "variant_sha256")}
        return m, strip_colors((out / po.XML_NAME).read_text()), (out / "native_mesh.csv").read_text()

    def test_no_key_equals_key_h_equals_legacy_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            m0, o0 = self.build(qw_variant(None, None, hints=False), tmp, "nokey")
            m1, o1 = self.build(qw_variant(H, None, hints=False), tmp, "keyh")
            a, b = self.comparable(m0, o0), self.comparable(m1, o1)
            self.assertEqual(a[1], b[1])   # XML
            self.assertEqual(a[2], b[2])   # mesh
            self.assertNotIn("driven_layer", m0["geometry"])
            self.assertNotIn("warnings", m0)
            self.assertEqual(m1["geometry"]["driven_layer"]["inverted"], False)
            g0 = {k: v for k, v in m0["geometry"].items()}
            g1 = {k: v for k, v in m1["geometry"].items() if k not in ("driven_layer", "substrate_z_lines_mm")}
            self.assertEqual(g0, g1)
            self.assertEqual(m0["port"], m1["port"])
            self.assertEqual(m0["port"]["stop_mm"][2], H)

    def test_probe_variant_without_key_is_unchanged_in_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta, _ = self.build(probe_variant(), tmp, "probe", {"edge_port": "msl", "nf2ff": False, "nf2ff_points": 11})
            self.assertNotIn("driven_layer", meta["geometry"])
            self.assertEqual(meta["port"]["stop_mm"], [0.0, -1.0, 1.6])

    def test_msl_port_rejected_when_inverted(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "--edge-port lumped"):
                self.build(qw_variant(1.035, [par(H)]), tmp, "msl", {"edge_port": "msl", "nf2ff": False, "nf2ff_points": 11})

    def test_parasitic_on_the_driven_layer_is_rejected_in_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "driven layer plane"):
                self.build(qw_variant(1.035, [par(1.035)]), tmp, "same")

    def test_inverted_stack_geometry_mesh_and_port(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta, out = self.build(qw_variant(1.035, [par(H)]), tmp, "inv")
            xml = (out / po.XML_NAME).read_text()
            # driven polygon, slot polygon and both feed boxes at z_d
            self.assertEqual(len(re.findall(r'<Polygon Priority="10" Elevation="1.035000e\+00"', xml)), 1)
            self.assertEqual(len(re.findall(r'<Polygon Priority="20" Elevation="1.035000e\+00"', xml)), 1)   # U-slot
            self.assertEqual(len(re.findall(r'<Polygon Priority="10" Elevation="2.070000e\+00"', xml)), 1)   # parasitic on the top face
            self.assertNotIn("slot_air", xml)
            self.assertIn("driven_slot_substrate", xml)
            boxes = re.findall(r'<Box Priority="10">\s*<P1 X="[^"]*" Y="[^"]*" Z="([^"]*)" />\s*<P2 X="[^"]*" Y="[^"]*" Z="([^"]*)" />', xml)
            self.assertIn(("1.035000e+00", "1.035000e+00"), boxes)   # feed rectangles
            # port 0 -> z_d at the board edge
            self.assertEqual(meta["port"]["start_mm"], [-1.96, -13.0, 0])
            self.assertEqual(meta["port"]["stop_mm"], [1.96, -13.0, 1.035])
            self.assertEqual(meta["port"]["vertical_integration_mm"], [0.0, 1.035])
            lumped = re.search(r'<LumpedElement.*?<P1 X="[^"]*" Y="[^"]*" Z="([^"]*)" />\s*<P2 X="[^"]*" Y="[^"]*" Z="([^"]*)"', xml, re.S)
            self.assertEqual((float(lumped.group(1)), float(lumped.group(2))), (0.0, 1.035))
            # z lines at the metal layers
            lines = np.array([float(r.split(",")[1]) for r in (out / "native_mesh.csv").read_text().splitlines()[1:] if r.startswith("z,")])
            for zz in (0.0, 1.035, H):
                self.assertTrue(np.any(np.isclose(lines, zz, atol=1e-12, rtol=0)), zz)
            dl = meta["geometry"]["driven_layer"]
            self.assertTrue(dl["inverted"])
            self.assertEqual(dl["driven_z_mm"], 1.035)
            self.assertEqual([s["cells"] for s in dl["z_segments"]], [4, 4])
            self.assertEqual(dl["z_levels_mm"], [0.0, 1.035, H])
            self.assertEqual(dl["port_vertical_integration_mm"], [0.0, 1.035])
            self.assertTrue(any("embedded line" in w for w in meta["warnings"]))
            pm = meta["geometry"]["parasitic_patches"][0]
            self.assertEqual(pm["layer_relation"], "on the top face (z = h)")
            self.assertEqual(pm["z_cells"]["parasitic_to_top_face"], 0)
            self.assertEqual(pm["z_cells"]["ground_to_parasitic"], 8)
            self.assertTrue(any("driven layer" in ln for ln in meta["parasitic_summary"]))
            self.assertTrue(meta["budget_before_solve"]["launch_allowed_by_budget"])

    def test_off_grid_driven_layer_shares_cells_per_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta, out = self.build(qw_variant(0.8, [par(1.55, name="mid"), par(H, name="top")]), tmp, "offgrid")
            dl = meta["geometry"]["driven_layer"]
            self.assertEqual(dl["z_levels_mm"], [0.0, 0.8, 1.55, H])
            self.assertEqual(sum(s["cells"] for s in dl["z_segments"]), po.SUBSTRATE_LINES - 1)
            self.assertTrue(all(s["cells"] >= 1 for s in dl["z_segments"]))
            self.assertEqual(meta["port"]["stop_mm"][2], 0.8)

    def test_parasitic_below_the_driven_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            below = par(0.5175, name="below", polygon=[[-5.5, -3.0], [5.5, -3.0], [5.5, 4.6], [-5.5, 4.6]])
            meta, _ = self.build(qw_variant(1.035, [below]), tmp, "below")
            self.assertEqual(meta["geometry"]["parasitic_patches"][0]["layer_relation"], "below the driven layer")
            self.assertEqual([s["cells"] for s in meta["geometry"]["driven_layer"]["z_segments"]], [2, 2, 4])


if __name__ == "__main__":
    unittest.main()
