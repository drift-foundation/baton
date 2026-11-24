#!/usr/bin/env python3
"""Owner-run scripted producer failures followed by read-only recovery preflight."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/home/sl/src/baton')
R=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery'
S=R/'evidence/qualification-complete-run/scripts'
E=Path('/home/sl/baton-qualification/w385695-deadline-8')
D=Path('/home/sl/baton-instances/qualify-w385695-deadline-8')
subprocess.run([sys.executable,'/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-observation-binding/owner-rebuild.py','--check'],check=True)
for name,want in json.loads((S/'files.json').read_text()).items():
    assert hashlib.sha256((S/name).read_bytes()).hexdigest()==want,name
expected=json.loads((R/'evidence/qualification-complete-run/deadline/runtime-manifest.json').read_text()); actual={}
for f in sorted((D/'distro').rglob('*')):
    if f.is_symlink():
        assert f.exists() and f.resolve().is_relative_to((D/'distro').resolve()),f
        actual[str(f.relative_to(D/'distro'))]='link:'+os.readlink(f)
    elif f.is_file():actual[str(f.relative_to(D/'distro'))]=hashlib.sha256(f.read_bytes()).hexdigest()
assert actual==expected,'installed runtime changed'
workers=json.loads((D/'deployment.json').read_text())['workers']
assert len(workers)==3
for w in workers:
    image='sha256:43482aa6d8777fc02a0a64ba20ea3a830a7b84a93ec584b25bbc7a3f527bf215' if w['role']=='publication' else 'sha256:b7d1543c9ae60f1ed4e4f724a3b99f51b23dac34909d08c3583b150b6c485924'
    assert w['deployment']['image_digest']==image,w['worker_id']
for n in (1,):
    job=json.loads((E/f'option-a.create-{n}.json').read_text())
    assert job['template']['version']=='baton.v12.job-template.implementation-review/3'
env=os.environ.copy();env.update(TREE=str(ROOT),EVIDENCE=str(E),INSTANCE=str(D/'instance.json'),OWNER='baton.slaw',ENGINE='docker')
if sys.argv[1:]==['--check']:
    print('Runtime, scripts, fixture worker images and the Job template checked. Nothing started.')
    raise SystemExit(0)
assert not sys.argv[1:],'usage: script [--check]'
subprocess.run(['bash',str(S/'option-a-setup.sh'),'failures'],env=env,check=True)
# Only the reviewed setup writes this shell-quoted environment; fixed paths are positional arguments.
subprocess.run(['bash','-c','set -euo pipefail; source "$1"; exec bash "$2" preflight','qualification',str(E/'option-a.env'),str(S/'qualify-w385695.sh')],env=env,check=True)
print('The scripted producer failed at the intended ceiling, were settled and removed, and recovery preflight passed.')
