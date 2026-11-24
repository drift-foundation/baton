#!/usr/bin/env python3
"""Owner-run reviewed qualification phases; no existing instance is selected."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/home/sl/src/baton')
DOSSIER=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery'
PACKET=DOSSIER/'evidence/correction-K-385951'
EVIDENCE=Path('/home/sl/baton-qualification/w385695-560eaa89-images-1')
phase=sys.argv[1] if len(sys.argv)==2 else 'images' if len(sys.argv)==1 else ''
if phase not in ('images','images-resume','cli-in-image','fixture-image','--check'):raise SystemExit('usage: script [images|cli-in-image|fixture-image|--check]')
subprocess.run([sys.executable,str(DOSSIER/'evidence/review-prompt-385955/owner-packaging.py'),'--check'],check=True)
index=PACKET/'packet.sha256'
if hashlib.sha256(index.read_bytes()).hexdigest()!='8ef13de9db43b69ec7c4f14cf978913a67e569a1a47957f82671655166195af7':raise SystemExit('packet index changed')
for line in index.read_text().splitlines():
    digest,name=line.split(maxsplit=1)
    path=PACKET/name.lstrip('*')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit('packet drift: '+name)
print('Qualified preparation identity verified. Evidence: '+str(EVIDENCE),flush=True)
if phase=='--check':raise SystemExit(0)
if phase=='images' and (EVIDENCE/'run-id').exists():raise SystemExit('existing image run: inspect it before retrying; no automatic rebuild')
EVIDENCE.mkdir(parents=True,exist_ok=True)
override=DOSSIER/'evidence/qualification-base-fix-385958'
for name,digest in json.loads((override/'files.json').read_text()).items():
    if hashlib.sha256((override/name).read_bytes()).hexdigest()!=digest:raise SystemExit('qualification correction drift: '+name)
env=os.environ.copy();env.update(TREE=str(ROOT),EVIDENCE=str(EVIDENCE),ENGINE='docker')
if phase=='images-resume':
    phase='images';env['RESUME_IMAGES']='1'
PACKET=override
raise SystemExit(subprocess.run(['bash',str(PACKET/'qualify-w385695.sh'),phase],cwd=ROOT,env=env).returncode)
