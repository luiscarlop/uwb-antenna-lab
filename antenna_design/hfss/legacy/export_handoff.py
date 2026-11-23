"""Read a geometry manifest and write a manual HFSS handoff. Never launches AEDT."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def export(manifest, out):
    raw=manifest.read_bytes(); data=json.loads(raw)
    if data['units']!='mm' or data['channel']!=9:
        raise ValueError('Expected channel 9 manifest in mm')
    if [data['frequency_hz'][k] for k in ('min','max')] != [7737600000,8236800000]:
        raise ValueError('Unexpected channel band')
    material=data['material_provisional'];h=float(material['h_mm'])
    bx,by=map(float,data['board_mm'])
    numbers=[h,bx,by,float(material['epsilon_r']),float(material['tan_delta']),float(data['reference_impedance_ohm'])]
    if not all(math.isfinite(x) and x>0 for x in numbers):
        raise ValueError('Invalid material/board/reference values')
    out.mkdir(parents=True,exist_ok=False)
    with (out/'parameters.csv').open('w',newline='') as file:
        w=csv.writer(file,lineterminator='\n');w.writerow(['scope','parameter','value','units','provenance'])
        for key,value,unit in [('board_x',bx,'mm'),('board_y',by,'mm'),('substrate_h',h,'mm'),
                               ('epsilon_r',material['epsilon_r'],'1'),('tan_delta',material['tan_delta'],'1'),
                               ('reference_impedance',data['reference_impedance_ohm'],'ohm'),
                               ('frequency_center',data['frequency_hz']['center'],'Hz')]:
            w.writerow(['all',key,value,unit,'manifest'])
        for key,value,unit in [('copper_thickness',.035,'mm'),('copper_conductivity',5.8e7,'S/m'),
                               ('port_sheet_width',.2,'mm')]:
            w.writerow(['all',key,value,unit,'proposed HFSS model assumption; not from manifest'])
        for name,d in data['designs'].items():
            w.writerow([name,'feed_x',d['feed'][0],'mm','manifest'])
            w.writerow([name,'feed_y',d['feed'][1],'mm','manifest'])
            w.writerow([name,'slot_count',len(d['slots']),'1','manifest'])
    with (out/'vertices.csv').open('w',newline='') as file:
        w=csv.writer(file,lineterminator='\n');w.writerow(['design','object','vertex','x_mm','y_mm','z_mm','operation'])
        for name,d in data['designs'].items():
            for obj,poly in [('PATCH',d['patch'])]+[(f'SLOT_{i+1}',p) for i,p in enumerate(d['slots'])]:
                if len(poly)<3: raise ValueError('Polygon requires at least three vertices')
                for i,(x,y) in enumerate(poly):
                    if not all(math.isfinite(v) for v in (x,y)) or abs(x)>bx/2 or abs(y)>by/2:
                        raise ValueError('Invalid polygon coordinates')
                    w.writerow([name,obj,i,x,y,h,'keep' if obj=='PATCH' else 'subtract_from_PATCH'])
    (out/'source.json').write_text(json.dumps({'manifest_sha256':hashlib.sha256(raw).hexdigest(),
        'source_manifest':str(manifest),'evidence':'GEOMETRY_ONLY','HFSS_executed':False,
        'design_ids':list(data['designs']), 'instructions':'../HFSS_STEPS.md',
        'warning':'Proposed 0.2 mm finite-width port is not identical to the openEMS line port; compare only after port sensitivity study.'},indent=2)+'\n')
    if manifest.read_bytes()!=raw: raise RuntimeError('Source manifest changed concurrently')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();export(args.manifest,args.out)
