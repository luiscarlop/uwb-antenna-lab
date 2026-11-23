import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from designs import F0_HZ,BW_HZ,BOARD_MM,candidates,rectangular_patch_dimensions,export_all

def point_in_poly(point,poly):
    x,y=point;inside=False
    for j,(x1,y1) in enumerate(poly):
        x2,y2=poly[j-1]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:
            inside=not inside
    return inside

class TestDesigns(unittest.TestCase):
    def test_band(self):
        self.assertEqual(F0_HZ-BW_HZ/2,7_737_600_000)
        self.assertEqual(F0_HZ+BW_HZ/2,8_236_800_000)
    def test_rect_estimate(self):
        w,l,e=rectangular_patch_dimensions()
        self.assertTrue(10<w<13)
        self.assertTrue(7<l<10)
        self.assertTrue(1<e<4.4)
    def test_geometry(self):
        designs=candidates();self.assertEqual(len(designs),3)
        for name,d in designs.items():
            for pt in [*d["patch"],*[q for poly in d["slots"] for q in poly]]:
                self.assertTrue(all(abs(v)<BOARD_MM/2 for v in pt),name)
            self.assertTrue(point_in_poly(d["feed"],d["patch"]),name)
            for poly in d["slots"]:
                self.assertFalse(point_in_poly(d["feed"],poly),name)
    def test_exports(self):
        import ezdxf
        with tempfile.TemporaryDirectory() as tmp:
            m=export_all(tmp)
            self.assertEqual(m["evidence"],"GEOMETRY_ONLY")
            self.assertFalse(m["em_simulated"])
            self.assertEqual(len(list(Path(tmp).glob("*.dxf"))),3)
            self.assertEqual(len(list(Path(tmp).glob("*.svg"))),3)
            for path in Path(tmp).glob("*.dxf"):
                self.assertEqual(ezdxf.readfile(path).units,4)
            self.assertEqual(len(json.loads((Path(tmp)/"manifest.json").read_text())["designs"]),3)

if __name__=="__main__":unittest.main()
