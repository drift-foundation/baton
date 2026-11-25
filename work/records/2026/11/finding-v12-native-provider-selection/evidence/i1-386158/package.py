"""Retain exact isolated candidate; never imports or mutates protected Git."""
from pathlib import Path
import subprocess,tarfile,io,hashlib,json,difflib
root=Path('/home/sl/src/baton');source=root/'work/scratch/i1-386158/source';e=Path(__file__).resolve().parent
base='d0760de6acdf9cd1e055d1f08137757adb223cc0'
paths=['v12/PROVIDER-SELECTION.md','v12/python/src/baton_v12/provider_policy/attribution.py','v12/python/src/baton_v12/worker_manager/attempts.py','v12/python/src/baton_v12/worker_manager/image_receipts.py','v12/python/src/baton_v12/worker_manager/model_attribution.py','v12/python/src/baton_v12/worker_manager/oci.py','v12/python/tests/job_manager/test_provider_attribution_recovery.py','v12/python/tests/manager/test_model_attribution.py','v12/python/tests/manager/test_oci.py','v12/python/tests/tools/test_codex_selection.py','v12/python/tests/tools/test_provider_selection.py']
sha=lambda x:hashlib.sha256(x).hexdigest()
manifest={'base':base,'files':{},'baseline':{},'shared_target_matches_baseline':{}}
patch=[]
with tarfile.open(e/'candidate.tar','w',format=tarfile.USTAR_FORMAT) as archive:
 for rel in sorted(paths):
  after=(source/rel).read_bytes();result=subprocess.run(['git','show',base+':'+rel],cwd=root,capture_output=True)
  before=result.stdout if result.returncode==0 else None
  manifest['files'][rel]=sha(after);manifest['baseline'][rel]=sha(before) if before is not None else None
  shared=(root/rel).read_bytes() if (root/rel).exists() else None
  manifest['shared_target_matches_baseline'][rel]=shared==before
  info=tarfile.TarInfo(rel);info.size=len(after);info.mode=0o644;info.mtime=0;archive.addfile(info,io.BytesIO(after))
  patch.extend(difflib.unified_diff((before or b'').decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel if before is not None else '/dev/null',tofile='b/'+rel))
manifest['archive_sha256']=sha((e/'candidate.tar').read_bytes())
(e/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(e/'candidate.patch').write_text(''.join(patch))
assert all(manifest['shared_target_matches_baseline'].values())
print(json.dumps({'candidate':manifest['archive_sha256'],'paths':len(paths),'shared_targets_unchanged':True}))
