"""Read-only consistency check of HFSS tables against their geometry manifest.

No AEDT calls, simulation or writing to the source/handoff directories.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from export_handoff import export


def verify(manifest, handoff):
    manifest=Path(manifest);handoff=Path(handoff)
    source=json.loads((handoff/'source.json').read_text())
    current=hashlib.sha256(manifest.read_bytes()).hexdigest()
    errors=[]
    if source.get('manifest_sha256')!=current:
        errors.append('Manifest hash differs: handoff is stale or references another manifest')
    with tempfile.TemporaryDirectory() as folder:
        expected=Path(folder)/'expected';export(manifest,expected)
        for name in ['parameters.csv','vertices.csv']:
            if (handoff/name).read_bytes()!=(expected/name).read_bytes():
                errors.append(f'{name} differs from the manifest-derived handoff')
        metadata=json.loads((expected/'source.json').read_text())
        for key in ['design_ids','evidence','HFSS_executed','warning','instructions']:
            if source.get(key)!=metadata[key]:
                errors.append(f'Metadata mismatch: {key}')
    return {'consistent':not errors,'errors':errors,'manifest_sha256':current,
            'scope':'table/source consistency only; not HFSS execution or EM validation'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--handoff',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.manifest,args.handoff)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['consistent'] else 1)
