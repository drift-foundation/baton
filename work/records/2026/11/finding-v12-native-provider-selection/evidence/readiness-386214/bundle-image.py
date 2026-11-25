"""Verify retained Q1 evidence and prepare a reduced bundle for owner review.

This does not approve evidence. The reviewer supplies its review locator and the
full manifest hash; the resulting exact bundle/hash still needs owner selection.
"""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--review',required=True)
    parser.add_argument('--finalized-q2',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();assert not a.output.exists() and a.output.is_absolute()
    assert a.evidence.is_absolute() and not a.evidence.is_symlink()
    raw=(a.evidence/'evidence-manifest.json').read_bytes();assert sha(raw)==a.manifest_sha256
    files=json.loads(raw)
    for name,digest in files.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        p=a.evidence/path;assert p.resolve().is_relative_to(a.evidence.resolve()) and not p.is_symlink()
        assert sha(p.read_bytes())==digest
    names=('RESULT.json','image-inspect.json','launched-image.json','receipt-after-removal.json','worker-observation.json')
    assert all(name in files for name in names)
    bundle=dict(review=a.review,manifest_files_verified=len(files),manifest_sha256=a.manifest_sha256,
        retained={name:json.loads((a.evidence/name).read_text()) for name in names})
    identity=json.loads((a.finalized_q2/'q1-build.json').read_text())
    assert bundle['retained']['worker-observation.json']['identity']==identity,'final checkpoint/source/image identity differs'
    a.output.write_text(json.dumps(bundle,sort_keys=True,indent=2)+'\n')
    sys.path.insert(0,str(a.finalized_q2))
    from image_gate import qualify
    digest=sha(a.output.read_bytes())
    qualify(a.output,digest)
    print(json.dumps(dict(bundle_sha256=digest,review=a.review,approval='pending-owner-selection')))
if __name__=='__main__':main()
