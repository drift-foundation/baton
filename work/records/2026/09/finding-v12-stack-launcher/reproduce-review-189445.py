import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path('/home/sl/src/baton')
D=ROOT/'work/records/2026/09/finding-v12-stack-launcher'
sys.path[:0]=[str(ROOT/'v12/python'),str(ROOT/'v12/python/src')]
from tools import build_stamp,instance
start=time.monotonic()
def run(argv,**kw):
 p=subprocess.run(argv,text=True,capture_output=True,timeout=30,**kw)
 return {'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
a=json.loads((D/'EVIDENCE-189383.json').read_text())
r={'candidate_mismatches':[p for p,h in a['candidates'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]}
# Read-only Git observations, with per-invocation configuration only.
source='v12/python/tests/tools/test_version.py'
r['untracked_default']=run(['git','-C',str(ROOT),'status','--porcelain','--',source])
r['untracked_hidden']=run(['git','-c','status.showUntrackedFiles=no','-C',str(ROOT),'status','--porcelain','--',source])
r['untracked_explicit']=run(['git','-c','status.showUntrackedFiles=no','-C',str(ROOT),'status','--porcelain','--untracked-files=all','--',source])
# Limit the real status read to this known untracked source to isolate the
# setting's effect from unrelated tracked changes already in this checkout.
def scoped(argv,cwd,timeout=30):
 argv=list(argv)
 if 'status' in argv:
  argv=[argv[0],'-c','status.showUntrackedFiles=no']+argv[1:]+['--',source]
 done=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,timeout=timeout)
 return done.stdout if done.returncode==0 else None
r['capture_with_status_scoped_to_hidden_untracked_source']=build_stamp.capture(ROOT,runner=scoped)
r['generated_paths']=run(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=normal','--','v12/python/build','v12/python/packaging/build-stamp.json'])
r['recipe_dry_runs']=[]
base=['just','--dry-run','--justfile',str(ROOT/'v12/justfile'),'bootstrap','/tmp/review-input.json','/tmp/review-destination']
for flags in [['--no-repositories'],['--repository-source','/other/checkout']]:
 r['recipe_dry_runs'].append(run(base+flags))
built=ROOT/'v12/python/build/out/distro'
installed=Path('/var/tmp/w183883-version-189383/deployment/distro')
r['bundle_manifest']=instance.manifest(str(built))
r['installed_manifest']=instance.manifest(str(installed))
r['version']=run([str(installed/'baton-v12-stack'),'--version'],cwd='/',env={'HOME':'/tmp','PATH':'/nonexistent'})
r['installed_stamp']=json.loads((installed/'_internal/build-stamp.json').read_text())
r['build_record_stamp']=json.loads((ROOT/'v12/python/packaging/build-stamp.json').read_text())
r['identity_record_stamp']=json.loads((D/'IDENTITY-189383.json').read_text())['build_stamp']
r['stamps_equal']=r['installed_stamp']==r['build_record_stamp']==r['identity_record_stamp']
r['manifest_equal']=r['bundle_manifest']['digest']==r['installed_manifest']['digest']
# Retain digest/count; full manifest remains in the actual instance.
for key in ['bundle_manifest','installed_manifest']:
 r[key]={k:v for k,v in r[key].items() if k!='entries'}
r['seconds']=time.monotonic()-start
assert not r['candidate_mismatches']
assert r['untracked_default']['stdout'].startswith('?? ')
assert not r['untracked_hidden']['stdout']
assert r['untracked_explicit']['stdout'].startswith('?? ')
assert r['capture_with_status_scoped_to_hidden_untracked_source']['dirty'] is False
assert '?? v12/python/packaging/build-stamp.json' in r['generated_paths']['stdout']
assert r['stamps_equal'] and r['manifest_equal']
assert r['version']['returncode']==0
(D/'REVIEW-EVIDENCE-189445.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='recipe_dry_runs'},indent=2))
