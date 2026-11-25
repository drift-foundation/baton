#!/usr/bin/env python3
"""Owner checkpoint for the reviewed .dockerignore build-context correction.

Run by Slawomir. `--check` verifies and changes nothing. Without arguments it
stages v12/.dockerignore, the accepting review and two evidence directories,
verifies the staged bytes, and commits. No push."""
import hashlib,subprocess,sys,os
from pathlib import Path
R=Path('/home/sl/src/baton')
BASE='ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402'
MESSAGE='Allow provider_policy into the worker image build context'
PRODUCT={'v12/.dockerignore':'04e364e4dbc1fdf8cf9fa7a76d81473563e1f129608df6fde2a6688548907da7'}
RECORDS={'work/records/2026/11/finding-v12-native-provider-selection/review-2026-11-25T01-12-48Z.md': '3b0010ceb1dbb96ece7d5f5d576cbb48f7a57aceb3698a8cfb6d0246c53d33fb', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-dockerignore-04e364e4/IMPORT.md': '2d8b552cc51924303b20f9f45aae249031370c8be7c2759851cf2a8365e13122', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-dockerignore-04e364e4/import-reviewed.py': '245df4103fdc26b41b7997d7c4bc38fbdac33b4e47388061686218e95f337f9f', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-dockerignore-04e364e4/import.json': '7a63ed2d09b761a2f83471d4596cbfbcf595dc4210ddfdd88c949f56805746ff', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2/context-correction.patch': '0c570f985ceee8253149134b82bd20f3078803d3620a1873921981d67521bf3f', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2/results/context-correction.json': 'd12aa61bca94b03a9b1b57a0034eb800f7de4efd7dd227395587ff6aa7c2aa55', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2/results/offline-checks.json': 'c1d35cf637500f1062aa1656fda6c85eac48540fe08e8db71d89c81d5c789d73', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2/results/RESULT.json': '67ec8460fddce709e32d3a4096d7d3fd0d6a3fcb9cb93cfcde10408e70c660b7'}
DIRS=['work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2/', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-dockerignore-04e364e4/']
REVIEW='work/records/2026/11/finding-v12-native-provider-selection/review-2026-11-25T01-12-48Z.md'
SELF='work/records/2026/11/finding-v12-native-provider-selection/evidence/import-dockerignore-04e364e4/owner-checkpoint.py'
def git(*args):return subprocess.check_output(['git',*args],cwd=R,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}).decode().strip()
def require(ok,msg):
 if not ok:raise SystemExit('Refused: '+msg)
sha=lambda b:hashlib.sha256(b).hexdigest()
require(sys.argv[1:] in ([],['--check']),'use no arguments or --check')
require(git('rev-parse','HEAD')==BASE,'HEAD changed')
require(not git('diff','--cached','--name-only'),'index already has staged content; preserve and inspect it')
for name,digest in {**PRODUCT,**RECORDS}.items():
 f=R/name;require(f.is_file() and not f.is_symlink() and sha(f.read_bytes())==digest,'input changed: '+name)
for d in DIRS:
 require((R/d).is_dir() and not (R/d).is_symlink() and not any(p.is_symlink() for p in (R/d).rglob('*')),'evidence directory unusable: '+d)
require(git('diff','--numstat','--','v12/.dockerignore').split()[:2]==['1','0'],'correction is not exactly one added line')
require(Path(__file__).read_bytes()==(R/SELF).read_bytes(),'temporary/durable script mismatch')
print('Verified v12/.dockerignore and',len(RECORDS),'pinned records.',flush=True)
if '--check' in sys.argv:
 print('No Git mutation.');sys.exit(0)
subprocess.run(['git','add','--',*PRODUCT,REVIEW,*DIRS],cwd=R,check=True)
staged=set(git('diff','--cached','--name-only').splitlines())
allowed=lambda p:p in PRODUCT or p==REVIEW or any(p.startswith(d) for d in DIRS)
require(all(allowed(p) for p in staged),'unexpected staged path; inspect index: '+', '.join(sorted(p for p in staged if not allowed(p))[:5]))
require(set(PRODUCT)<=staged and set(RECORDS)<=staged and SELF in staged,'expected path not staged; inspect index')
require({p for p in staged if p.startswith('v12/')}==set(PRODUCT),'staged product set is not exactly v12/.dockerignore')
for name,digest in {**PRODUCT,**RECORDS}.items():
 require(sha(subprocess.check_output(['git','show',':'+name],cwd=R))==digest,'staged bytes differ: '+name)
subprocess.run(['git','diff','--cached','--check','--',*PRODUCT],cwd=R,check=True)
subprocess.run(['git','diff','--cached','--stat','--',*PRODUCT],cwd=R,check=True)
subprocess.run(['git','commit','-m',MESSAGE],cwd=R,check=True)
print('Checkpoint:',git('rev-parse','HEAD'))
print('Left unstaged: W386057 isolation edits, v12/DESIGN.md, FINDING/PLAN/PROGRESS, other evidence. No push.')
