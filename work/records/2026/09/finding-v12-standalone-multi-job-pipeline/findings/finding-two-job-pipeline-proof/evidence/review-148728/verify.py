"""Verify acquisition proposal custody and preserve accepted runner; no provider reads."""
from pathlib import Path
import hashlib,json,stat,time
ROOT=Path('/home/sl/src/baton')
PROOF=ROOT/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
OUT=Path(__file__).resolve().parent
start=time.monotonic()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def check(p,expected): assert sha(p)==expected.removeprefix('sha256:'),str(p)
def manifest(p,expected):
 check(p,expected);files=read(p)['files']
 for name,row in files.items():
  path=ROOT/name
  assert path.is_file() and not path.is_symlink(),name
  check(path,row['sha256'])
  assert path.stat().st_size==row['bytes'],name
  assert oct(stat.S_IMODE(path.stat().st_mode))==row['mode'],name
 return len(files)
counts={'proposal':manifest(PROOF/'evidence/diagnostic-148686/proposal-manifest.json','9a829c5d43c6c4f8fbe0a614ad2fc082d5056a38ea83c585a7d40596ba24e602'),'accepted_runner':manifest(PROOF/'prepared-147109/candidate-manifest.json','94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2')}
bindings=read(PROOF/'evidence/diagnostic-148686/source-and-preservation.json')['source_bindings']
for name,row in bindings.items():
 check(ROOT/name,row['sha256']);assert (ROOT/name).stat().st_size==row['bytes']
destination=Path('/tmp/w71879-148686-provider-package.json')
assert not destination.exists() and not destination.is_symlink()
result={'claim':148728,'counts':counts,'source_bindings':len(bindings),'destination_absent':True,'destination':str(destination),'seconds':time.monotonic()-start,'scope':'Proposal/accepted-runner/source custody only. Exact installed provider metadata remains unavailable; no copying, provider execution, model calls or credential reads.'}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

