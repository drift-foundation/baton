#!/usr/bin/env python3
"""Owner-run qualification bootstrap only; no services or Jobs launched."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path('/home/sl/src/baton')
P=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-status-review-run/deadline'
D=ROOT/'v12/python/build/out/distro'
DEST=Path('/home/sl/baton-instances/qualify-w385695-deadline-7')
subprocess.run([sys.executable,'/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-observation-binding/owner-rebuild.py','--check'],check=True)
expected=json.loads((P/'runtime-manifest.json').read_text())
actual={}
for f in sorted(D.rglob('*')):
    if f.is_symlink():
        assert f.exists() and f.resolve().is_relative_to(D.resolve()),f
        actual[str(f.relative_to(D))]='link:'+os.readlink(f)
    elif f.is_file():actual[str(f.relative_to(D))]=hashlib.sha256(f.read_bytes()).hexdigest()
assert actual==expected,'built runtime changed'
assert hashlib.sha256((P/'bootstrap-inputs.json').read_bytes()).hexdigest()=='60f4f126d98a48c8523e4be95eaeec6134889f6b1f5592a538f82091e1dc1bf9','bootstrap inputs changed'
assert not DEST.exists() and not DEST.is_symlink(),'destination already exists; inspect before repeating'
assert not (P/'bootstrap-current.log').exists(), 'current bootstrap log exists; inspect before repeating'
if sys.argv[1:]==['--check']:
    print('Bootstrap inputs and runtime verified; destination absent. No installation run.')
    raise SystemExit(0)
assert not sys.argv[1:],'usage: script [--check]'
argv=[str(D/'baton-v12-stack'),'bootstrap','--inputs',str(P/'bootstrap-inputs.json'),'--destination',str(DEST),'--distro',str(D),'--repository-source',str(ROOT)]
with (P/'bootstrap-current.log').open('x') as log:
    result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,text=True)
print((P/'bootstrap-current.log').read_text(),end='')
raise SystemExit(result.returncode)
