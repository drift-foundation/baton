from pathlib import Path
import sys,json,hashlib,shutil,stat
sys.path.insert(0,str(Path.cwd()/'v12/python/src'))
from baton_v12.worker_manager.workspaces import directory_manifest
root=Path('/home/sl/baton-instances/native-w385695-publication-2/state')
out=Path(__file__).resolve().parent
raw=(root/'status.json').read_bytes(); snapshot=json.loads(raw)
job=next(j for j in snapshot['jobs'] if j['job_id']=='w385695-native-publication-2')
stage=next(s for s in job['stages'] if s['kind']=='implementation')
assert stage['runtime']['execution_runtime']=='destroyed'
assert stage['attempt_diagnostics']['token']['returned']['value'] is True
assert stage['attempt_diagnostics']['execution']['cleanup']['value']=='retained'
assert snapshot['observed_at']>='2026-11-23T16:45:00'
(out/'observed-status.json').write_bytes(raw)
verified=[]
for art in stage['artifacts']:
 p=Path(art['locator'].removeprefix('file://'))
 measured=directory_manifest(str(p))
 assert measured['tree_digest']==art['content_digest'],(p,measured,art)
 assert measured['total_bytes']==art['bytes']
 dest=out/'original'/art['output_name']
 assert not dest.exists()
 shutil.copytree(p,dest,copy_function=shutil.copyfile)
 assert directory_manifest(str(dest))==measured
 assert directory_manifest(str(p))==measured
 verified.append({'artifact':art,'measured':measured,'copy':str(dest.relative_to(out))})
result=json.loads((out/'original/proposal/result.json').read_text())
assert result['head']=='4e8fbe1c3b596f2f5db9f03b6c63572c9b198df7'
assert result['base']=='6079ad78345aa87b7148db302d48fb9b1867f940'
assert result['provider']['failure_reason']=='timeout' and result['verification'] is None
(out/'custody-verification.json').write_text(json.dumps({'snapshot_observed_at':snapshot['observed_at'],'verified':verified,'result':result},indent=2)+'\n')
print('Verified both original artifact tree digests, sizes, exact preservation copies and original rereads; runtime destroyed/token returned.')
