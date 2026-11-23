"""Synthetic fixtures only: never load solver or campaign output files."""
import cmath
import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analysis.metrics import BAND_HZ,read_complex_csv,s11_metrics,band_coverage,radiated_group_delay


class TestPort(unittest.TestCase):
    def test_matched_open_short_and_active(self):
        matched,opened,shorted,active=s11_metrics([0,1,-1,1.1])
        self.assertEqual(matched['impedance_ohm'],50)
        self.assertEqual(matched['vswr'],1)
        self.assertEqual(matched['s11_db'],-math.inf)
        self.assertIsNone(opened['impedance_ohm'])
        self.assertEqual(opened['vswr'],math.inf)
        self.assertEqual(shorted['impedance_ohm'],0)
        self.assertTrue(active['passivity_violation'])
        self.assertIsNone(active['vswr'])

    def test_complex_impedance_round_trip(self):
        z=75+20j; g=(z-50)/(z+50)
        self.assertAlmostEqual(abs(s11_metrics([g])[0]['impedance_ohm']-z),0)

    def test_invalid_z0_and_nonfinite(self):
        for z in [0,-1,math.inf]:
            with self.assertRaises(ValueError): s11_metrics([0],z)
        with self.assertRaises(ValueError): s11_metrics([complex(math.nan,0)])

    def test_csv_read_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'synthetic.csv'
            p.write_text('frequency_hz,s11_real,s11_imag\n7.5e9,0.1,0.2\n8.5e9,0.2,0.3\n')
            f,v=read_complex_csv(p);self.assertEqual(v[0],.1+.2j)
            p.write_text('frequency_hz,s11_real,s11_imag\n8e9,0,0\n8e9,0,0\n')
            with self.assertRaises(ValueError): read_complex_csv(p)


class TestBand(unittest.TestCase):
    def test_full_band_conditional_pass(self):
        lo,hi=BAND_HZ
        r=band_coverage([lo,(lo+hi)/2,hi],[.1,.1,.1])
        self.assertTrue(r['data_spans_band'])
        self.assertFalse(r['continuous_band_verified'])
        self.assertTrue(all(x=='PASS_INTERPOLATED' for x in r['thresholds_db'].values()))

    def test_minimum_does_not_establish_coverage(self):
        lo,hi=BAND_HZ
        r=band_coverage([lo,(lo+hi)/2,hi],[.8,.01,.8])
        self.assertTrue(all(x=='FAIL' for x in r['thresholds_db'].values()))

    def test_missing_band_edges_never_pass(self):
        r=band_coverage([7.8e9,8.1e9],[.01,.01])
        self.assertFalse(r['data_spans_band'])
        self.assertTrue(all(x=='INSUFFICIENT_DATA' for x in r['thresholds_db'].values()))

    def test_complex_interpolated_edges(self):
        r=band_coverage([7.5e9,8.5e9],[.1j,-.1j])
        self.assertEqual(r['exact_edges_present'],[False,False])
        self.assertEqual(r['thresholds_db']['-10.0'],'PASS_INTERPOLATED')
        r=band_coverage([7.5e9,8.5e9],[.1,.1],max_gap_hz=10e6)
        self.assertEqual(r['thresholds_db']['-6.0'],'INSUFFICIENT_DATA')

    def test_threshold_equality(self):
        for threshold in [-6.,-10.]:
            r=band_coverage(BAND_HZ,[10**(threshold/20)]*2,thresholds=[threshold])
            self.assertEqual(r['thresholds_db'][str(threshold)],'PASS_INTERPOLATED')

    def test_bad_grids(self):
        for f in [[8e9,7e9],[8e9,8e9],[7e9,math.nan]]:
            with self.assertRaises(ValueError): band_coverage(f,[.1,.1])


class TestRadiated(unittest.TestCase):
    def test_known_delay_unwrap_nonuniform_grid(self):
        f=[7.5e9,7.55e9,7.7e9,7.9e9,8.1e9,8.3e9,8.5e9]
        tau=1e-9;h=[cmath.exp(-2j*math.pi*x*tau) for x in f]
        r=radiated_group_delay(f,h,field_kind='radiated_transfer',reference='synthetic exp(-j2pi f tau)')
        for t in r['delay_s']: self.assertAlmostEqual(t,tau,places=20)
        self.assertLess(r['ripple_peak_to_peak_s'],1e-20)

    def test_dispersive_phase_interior_derivative(self):
        f=[7.5e9+i*1e7 for i in range(101)]
        center=8e9; tau=1e-9; slope=1e-18
        h=[cmath.exp(-2j*math.pi*(tau*(x-center)+.5*slope*(x-center)**2)) for x in f]
        r=radiated_group_delay(f,h,field_kind='radiated_transfer',reference='synthetic quadratic phase')
        for x,t in zip(f[1:-1],r['delay_s'][1:-1]):
            self.assertAlmostEqual(t,tau+slope*(x-center),places=20)
        self.assertGreater(r['ripple_peak_to_peak_s'],0)

    def test_reject_s11_nulls_and_missing_reference(self):
        f=[7.5e9,8e9,8.5e9]
        for kw,values in [({'field_kind':'s11','reference':'port'},[1,1,1]),
                           ({'field_kind':'radiated_transfer','reference':''},[1,1,1]),
                           ({'field_kind':'radiated_transfer','reference':'synthetic'},[1,0,1])]:
            with self.assertRaises(ValueError): radiated_group_delay(f,values,**kw)

    def test_band_ripple_uses_guard_samples_and_exact_edges(self):
        lo,hi=BAND_HZ;center=(lo+hi)/2
        f=[lo-1e7,lo,lo+1e7,center,hi-1e7,hi,hi+1e7]
        tau=1e-10;slope=1e-19
        h=[cmath.exp(-2j*math.pi*(tau*(x-center)+.5*slope*(x-center)**2)) for x in f]
        r=radiated_group_delay(f,h,field_kind='radiated_transfer',reference='synthetic',band=BAND_HZ)
        self.assertEqual(r['evaluation_band_hz'],list(BAND_HZ))
        self.assertEqual(len(r['delay_s']),5)
        self.assertAlmostEqual(r['ripple_peak_to_peak_s'],slope*(hi-lo),places=20)
        self.assertAlmostEqual(r['frequency_weighted_mean_delay_s'],tau,places=20)
        for x,t in zip(r['frequency_hz'],r['delay_s']):
            self.assertAlmostEqual(t,tau+slope*(x-center),places=20)

    def test_delay_band_missing_edges_rejected(self):
        for band in [BAND_HZ,(8.5e9,7.5e9),(7.5e9,math.nan)]:
            with self.assertRaises(ValueError):
                radiated_group_delay([7.5e9,8e9,8.5e9],[1,1,1],
                    field_kind='radiated_transfer',reference='synthetic',band=band)

    def test_ambiguous_phase_increment(self):
        with self.assertRaises(ValueError):
            radiated_group_delay([1,2,3],[1,-1,1],field_kind='radiated_transfer',reference='synthetic')

if __name__=='__main__': unittest.main()
