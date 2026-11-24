#!/usr/bin/env python3
"""Build only the scripted fixture image with a non-reserved metadata label."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-fixture-label-correction')
E=Path('/home/sl/baton-qualification/w385695-fixture-label-fixed-1')
TAG='baton-v12-qualification-fixture:w385695-label-fixed-1'
BASE='sha256:0ad2c553865ebb6a95c6014686f61dd97e69f0bee617af005a2ace8f83ab89e7'
assert hashlib.sha256((P/'claude').read_bytes()).hexdigest()=='ee65fa11f580a5560dfeee14781e78425f5fd58cef52c9c9c2c848b1e40d84a4'
assert hashlib.sha256((P/'Dockerfile').read_bytes()).hexdigest()=='e2b75c01b56fab02c005717fa4775a13758658a715ab77f7d77611602a538b81'
assert not E.exists() and not E.is_symlink(),'build evidence exists; inspect before retrying'
if sys.argv[1:]==['--check']:
    print('Fixture bytes unchanged; only label namespace corrected. No build run.')
    raise SystemExit(0)
assert not sys.argv[1:]
assert subprocess.check_output(['docker','image','inspect',BASE,'--format','{{.Id}}'],text=True).strip()==BASE
probe=subprocess.run(['docker','image','inspect',TAG],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
assert probe.returncode!=0,'tag already exists; not overwriting'
E.mkdir()
with (E/'build.log').open('x') as log:
    rc=subprocess.run(['docker','build','-t',TAG,str(P)],stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
assert rc==0,'fixture build failed; see '+str(E/'build.log')
d=json.loads(subprocess.check_output(['docker','image','inspect',TAG]))[0]
labels=d['Config'].get('Labels') or {}
assert labels.get('org.baton.qualification-fixture')=='scripted-provider'
assert not any(k.startswith('baton.v12.') for k in labels),labels
assert d['Config']['User']=='65532:65532'
(E/'image-inspect.json').write_text(json.dumps(d,indent=2)+'\n')
(E/'image.json').write_text(json.dumps({'role':'fixture','tag':TAG,'id':d['Id'],'base':BASE,'scope':'metadata-label correction; scripted CLI bytes unchanged'},indent=2)+'\n')
print('Corrected fixture image: '+d['Id'])
print('No containers or providers launched. Evidence: '+str(E))
