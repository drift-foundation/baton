#!/usr/bin/env python3
"""Owner checkpoint for the W385830 N4a join (candidate e9e9c84f).

Run by Slawomir. `--check` verifies and changes nothing. Without arguments it
stages exactly the 17 reviewed product paths, two reviews and the N4a evidence
directories, verifies the staged bytes, and commits. No push. The W386057
isolation edits are a separate candidate and are refused if staged."""
import hashlib,subprocess,sys,os
from pathlib import Path
R=Path('/home/sl/src/baton')
BASE='ac034bc1c9fae525b94a1a5f21d9721c677dc39e'
CANDIDATE='sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f'
MESSAGE='Join deterministic Codex adapter, entry and recipe candidate under provider selection (N4a)'
PRODUCT={'v12/PROVIDER-SELECTION.md': '20023627cc76192990fcd4e5bf1967f9e8910f0304be7dcc5380ca6a79c8e1d8', 'v12/python/src/baton_v12/provider_policy/__init__.py': '45927d92848cb19999bfa7af9c2539bd0dac0763590efb8f0c00e466e14cbc37', 'v12/python/tests/manager/codex_fixtures.py': '0e7204b90f4f3cc5efc0b4c35888152637dbe85bdcccbeea8974529c64acd04a', 'v12/python/tests/manager/fixtures/codex-0.169.0/exec-help.txt': 'b7bbe3ad07a91a11393c9a83d97873e0bca1d1766e4d7cd9013da2c374d34f51', 'v12/python/tests/manager/fixtures/codex-0.169.0/provenance.json': 'b4eb5c5a58ab5a8538807660e137b96d4660907b7934dd5d319a6dd2f6f72510', 'v12/python/tests/manager/fixtures/codex-0.169.0/version.txt': 'f3807264176de3c20897352ed66cf258503bb4d52bf8428b5e8a3ac21c22cdcb', 'v12/python/tests/manager/test_codex_draft.py': 'd271a8d8de51865a6138ca4be13340c5277f1fb577f8a32b0263358b46cf6066', 'v12/python/tests/manager/test_worker_packaging.py': 'f05c38f501f9b97a4ff9f600dfdfcbe75f4d66838992ca82708c4220915e1811', 'v12/python/tests/tools/test_codex_selection.py': '6a2a2929ba3cea414b58d353f1cf5849a0094f204384b54b5cceb4d01ab17b0d', 'v12/python/tests/tools/test_provider_selection.py': '11ba573bffe0f889af4156e12c7a1081d0511dc9fab8bea7cfbecf0f0f422921', 'v12/python/tools/parallel_test.py': '4180281ef3402d793bf30ed887ec90af4b306f75252a846a1cfe54e8f1a5f856', 'v12/python/tools/pool.py': '3517c905e0f674c4cb611f9167c10300c228e340dee50324c2e823dfdf2a0d57', 'v12/python/tools/single_worker.py': '70d5d19eea1bad436d79d3d00c5247f65fc32495c450b58fdbe7fa2b686dbdda', 'v12/worker/Dockerfile.codex': '0c81e45ff858f96bbac78daadc6c0c03ffce4e241ff38e0d28bbf5e620fcdf0e', 'v12/worker/claude_agent.py': 'ef3a641b168319fabefbd9329fc96515440ec36ab2d7b783acf7175d335184a6', 'v12/worker/codex_agent.py': 'e78f6425de6dceb875cc408a7634793accf53df12f3ad4cc8ce22519b226ceea', 'v12/worker/codex_entry.py': 'd08ebfb6812e5c1458f79136ce73ad0f3a110ca87643f42dfc56822c1fa3f86d'}
RECORDS={'work/records/2026/11/finding-v12-native-provider-selection/review-2026-11-24T21-10-45Z.md': 'e632a4d3a03f0fda3eb2a528209969f470408e75b8f3744562180f7ea3aa973d', 'work/records/2026/11/finding-v12-native-provider-selection/review-2026-11-24T23-40-10Z.md': 'd38fa34d330765cd093bb0381e88a699b9dc89f8ed570b514b92086b1454230d', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/n4a-join-386051/candidate-manifest.json': '80ebd37f4031cb31fcb047c4e1ec73407dea4c62af9b76d7d5b504e51f5b4e3e', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/n4a-join-386051/candidate-files.tar.gz': '713112419c0e76c48788308ceefdc94c3146043bbf130468e7a6ae22254822f0', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-e9e9c84f/IMPORT.md': 'c8031ab4f0d00b3985d3022438309977a0e57f83670b174532ed276a32965afe', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-e9e9c84f/import-reviewed.py': '0e69f95bf22e2297449eeb68d4b043fc7033a729d7e22c46530d75259a223fca', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-e9e9c84f/preflight.json': '603da35ddd3e30a3dd070d2a1dca82ffdc112eb7a32147bdab64f5b2d963ddff', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-e9e9c84f/postflight.json': 'b57d5650372243d3d2f6236b69d5e2e851f3e5b6ff4b0f0c19cc535f7ed4853a', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/review-K-386054/packet.sha256': 'ffe0dae346bbc0238df4eaa2d8306b68d6ba03ce7a35810d8faad31f1cee69ec'}
DIRS=['work/records/2026/11/finding-v12-native-provider-selection/evidence/n4a-preparation-386020/', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/n4a-draft-386029/', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/n4a-join-386051/', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/review-K-386054/', 'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-e9e9c84f/']
REVIEWS=['work/records/2026/11/finding-v12-native-provider-selection/review-2026-11-24T21-10-45Z.md', 'work/records/2026/11/finding-v12-native-provider-selection/review-2026-11-24T23-40-10Z.md']
EXCLUDED=['v12/python/TESTING.md', 'v12/python/tests/__init__.py', 'v12/python/tests/git_isolation.py', 'v12/python/tests/manager/disk_roots.py', 'v12/python/tests/tools/test_environment.py']
EXCLUDED_PREFIX='work/records/2026/11/finding-v12-git-fixture-isolation/'
SELF='work/records/2026/11/finding-v12-native-provider-selection/evidence/import-e9e9c84f/owner-checkpoint.py'
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
require(not (set(PRODUCT)&set(EXCLUDED)),'product overlaps the isolation candidate')
require(Path(__file__).read_bytes()==(R/SELF).read_bytes(),'temporary/durable script mismatch')
print('Verified',len(PRODUCT),'reviewed product paths of',CANDIDATE,'and',len(RECORDS),'pinned records.',flush=True)
if '--check' in sys.argv:
 print('No Git mutation.');sys.exit(0)
subprocess.run(['git','add','--',*sorted(PRODUCT),*REVIEWS,*DIRS],cwd=R,check=True)
staged=set(git('diff','--cached','--name-only').splitlines())
allowed=lambda p:p in PRODUCT or p in REVIEWS or any(p.startswith(d) for d in DIRS)
require(all(allowed(p) for p in staged),'unexpected staged path; inspect index: '+', '.join(sorted(p for p in staged if not allowed(p))[:5]))
require(set(PRODUCT)<=staged and set(RECORDS)<=staged and SELF in staged,'expected path not staged; inspect index')
require(not any(p in EXCLUDED or p.startswith(EXCLUDED_PREFIX) for p in staged),'isolation candidate staged')
require({p for p in staged if p.startswith('v12/')}==set(PRODUCT),'staged product set differs from the 17 reviewed paths')
for name,digest in {**PRODUCT,**RECORDS}.items():
 require(sha(subprocess.check_output(['git','show',':'+name],cwd=R))==digest,'staged bytes differ: '+name)
# The retained Codex help fixture keeps the vendor's exact bytes, trailing blanks included.
subprocess.run(['git','diff','--cached','--check','--',*sorted(p for p in PRODUCT if '/fixtures/codex-0.169.0/' not in p)],cwd=R,check=True)
subprocess.run(['git','diff','--cached','--stat','--',*sorted(PRODUCT)],cwd=R,check=True)
print(len(staged)-len(PRODUCT),'record and evidence files staged.')
subprocess.run(['git','commit','-m',MESSAGE],cwd=R,check=True)
print('Checkpoint:',git('rev-parse','HEAD'))
print('Left unstaged: W386057 isolation edits and dossier, v12/DESIGN.md, FINDING/PLAN/PROGRESS, other evidence. No push.')
print('Next: K records this commit; J1, N4b and qualification stay gated.')
