"""Bind reviewed preparation to a real human checkpoint; no engine capability.

Writes a fresh successor packet, preserving the reviewed draft. Git operations
are read-only. The checkpoint must exactly export the candidate input manifest.
"""
import argparse,hashlib,io,json,re,shutil,subprocess,sys,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent
VECTOR='work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def seal(p,name):
    (p/name).write_text(json.dumps({f.name:sha(f.read_bytes()) for f in sorted(p.iterdir()) if f.is_file() and f.suffix in ('.py','.json','.tar') and f.name!=name},sort_keys=True,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--checkpoint',required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.checkpoint),'full human checkpoint required'
    assert a.repository.is_absolute() and a.output.is_absolute() and not a.output.exists()
    assert not a.output.is_relative_to(P),'fresh successor outside the draft required'
    for f,digest in json.loads((P/'packet-manifest.json').read_text()).items():assert sha((P/f).read_bytes())==digest,f
    raw=subprocess.check_output(['git','-C',str(a.repository),'archive',a.checkpoint,'v12',VECTOR])
    seen={}
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        for member in t:
            if member.isdir():continue
            assert member.isfile() and member.name not in seen
            seen[member.name]=dict(sha256=sha(t.extractfile(member).read()),mode=0o755 if member.mode & 0o111 else 0o644)
    assert seen==json.loads((P/'expected-source.json').read_text()),'checkpoint differs from reviewed candidate source; no silent rebinding'
    a.output.mkdir(mode=0o700)
    for sub in ('q1','q2'):
        shutil.copytree(P/sub,a.output/sub)
        p=a.output/sub/'owner-run.py'
        p.write_text(p.read_text().replace("BASE='PENDING-HUMAN-CHECKPOINT'",'BASE='+repr(a.checkpoint)))
    subprocess.run([sys.executable,'-B',str(P/'generate-context.py'),str(a.output/'q1'),a.checkpoint],check=True)
    shutil.copyfile(a.output/'q1/q1-build.json',a.output/'q2/q1-build.json')
    seal(a.output/'q1','packet-files.json');seal(a.output/'q2','payload.json')
    binding=dict(checkpoint=a.checkpoint,source_manifest_sha256=sha((P/'expected-source.json').read_bytes()),
                 preparation_manifest_sha256=sha((P/'packet-manifest.json').read_bytes()),
                 q1_manifest_sha256=sha((a.output/'q1/packet-files.json').read_bytes()),
                 q2_payload_sha256=sha((a.output/'q2/payload.json').read_bytes()),engine_operations=0,credential_access=False)
    (a.output/'FINALIZATION.json').write_text(json.dumps(binding,sort_keys=True,indent=2)+'\n')
    print(json.dumps(binding))
if __name__=='__main__':main()
