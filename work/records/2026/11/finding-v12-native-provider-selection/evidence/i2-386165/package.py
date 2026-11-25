"""Retain isolated I2 candidate; shared targets and protected Git remain untouched."""
from pathlib import Path
import subprocess,tarfile,io,hashlib,json,difflib
root=Path('/home/sl/src/baton');source=root/'work/scratch/i2-386165/source';e=Path(__file__).resolve().parent
base='2d9a1f5afd84bfdcef461798d2418be3e6d65a9d'
reserved={'v12/DESIGN.md','v12/python/TESTING.md','v12/python/tests/__init__.py','v12/python/tests/git_isolation.py','v12/python/tests/manager/disk_roots.py','v12/python/tests/tools/test_environment.py'}
changed=subprocess.check_output(['git','diff','--name-only','HEAD','--','v12'],cwd=source,text=True).splitlines()
paths=sorted(set(changed)-reserved)
sha=lambda x:hashlib.sha256(x).hexdigest()
manifest={'base':base,'claim':'E386173','ownership':'M386168 / M386172','files':{},'baseline':{},'shared_target_matches_baseline':{},'excluded_reserved_paths':sorted(reserved)}
patch=[]
with tarfile.open(e/'candidate.tar','w',format=tarfile.USTAR_FORMAT) as archive:
 for rel in paths:
  after=(source/rel).read_bytes();result=subprocess.run(['git','show',base+':'+rel],cwd=root,capture_output=True)
  before=result.stdout if result.returncode==0 else None
  manifest['files'][rel]=sha(after);manifest['baseline'][rel]=sha(before) if before is not None else None
  shared=(root/rel).read_bytes() if (root/rel).exists() else None
  manifest['shared_target_matches_baseline'][rel]=shared==before
  info=tarfile.TarInfo(rel);info.size=len(after);info.mode=0o644;info.mtime=0;archive.addfile(info,io.BytesIO(after))
  patch.extend(difflib.unified_diff((before or b'').decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel if before is not None else '/dev/null',tofile='b/'+rel))
manifest['archive_sha256']=sha((e/'candidate.tar').read_bytes())
manifest['verification_prerequisites']={rel:sha((source/rel).read_bytes()) for rel in sorted(reserved-{'v12/DESIGN.md'})}
manifest['prerequisites_match_retained']={rel:(source/rel).read_bytes()==(e/'verification-prerequisites'/rel).read_bytes() for rel in manifest['verification_prerequisites']}
(e/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(e/'candidate.patch').write_text(''.join(patch))
assert all(manifest['shared_target_matches_baseline'].values())
assert all(manifest['prerequisites_match_retained'].values())
print(json.dumps({'candidate':manifest['archive_sha256'],'paths':len(paths),'shared_targets_unchanged':True}))
