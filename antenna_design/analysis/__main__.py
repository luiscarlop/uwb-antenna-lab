"""Explicit user-invoked postprocessing. No default real-data input."""
import argparse
import json
import math
from pathlib import Path
from .metrics import read_complex_csv, s11_metrics, band_coverage, radiated_group_delay


def serial(value):
    if isinstance(value, complex):
        return {'real': value.real, 'imag': value.imag}
    if isinstance(value, float) and not math.isfinite(value):
        return '-Infinity' if value < 0 else 'Infinity'
    if isinstance(value, dict):
        return {k: serial(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    return value


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('kind', choices=['s11','radiated'])
    cli.add_argument('csv',type=Path)
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--z0',type=float,default=50)
    cli.add_argument('--max-gap-hz',type=float)
    cli.add_argument('--reference',default='')
    cli.add_argument('--band-hz',nargs=2,type=float,metavar=('LOW','HIGH'),
                     help='Radiated delay interval with exact sampled endpoints')
    args=cli.parse_args()
    if args.kind=='s11' and args.band_hz is not None:
        cli.error('--band-hz is for radiated delay; S11 uses channel 9')
    if args.kind=='s11':
        f,v=read_complex_csv(args.csv)
        result={'frequency_hz': f,'reference_ohm': args.z0,'metrics':s11_metrics(v,args.z0),
                'coverage':band_coverage(f,v,max_gap_hz=args.max_gap_hz)}
    else:
        f,v=read_complex_csv(args.csv,'field_real','field_imag')
        result=radiated_group_delay(f,v,field_kind='radiated_transfer',reference=args.reference,band=args.band_hz)
    # Refuse overwriting input or another result.
    with args.out.open('x') as stream:
        json.dump(serial(result),stream,indent=2,allow_nan=False)
        stream.write('\n')

if __name__=='__main__':
    main()
