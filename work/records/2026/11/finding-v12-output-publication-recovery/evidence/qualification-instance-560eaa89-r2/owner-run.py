#!/usr/bin/env python3
"""Install and run scripted publication qualification r2; no live provider."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-instance-560eaa89-r2')
OLD=Path('/home/sl/baton-qualification/w385695-560eaa89-images-1')
E=Path('/home/sl/baton-qualification/w385695-560eaa89-recovery-2')
assert hashlib.sha256((P/'files.json').read_bytes()).hexdigest()=='cf0e527f80f11fd80883f42f5777a5a5b0a8bed73855d5824e38bbf74f357438'
for name,want in json.loads((P/'files.json').read_text()).items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==want,name
assert not E.exists() and not E.is_symlink(),'r2 evidence already exists; inspect before retrying'
subprocess.run([sys.executable,str(P/'owner-bootstrap.py'),'--check'],check=True)
if sys.argv[1:]==['--check']:
    print('Fresh r2 destination, corrected runtime and prepared helpers verified. Nothing installed or started.')
    raise SystemExit(0)
assert not sys.argv[1:],'usage: script [--check]'
# Prove each retained tag still names the recorded image before installation.
for line in (OLD/'images.owned').read_text().splitlines():
    name,tag,want=line.split()
    assert subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip()==want,name
E.mkdir()
(E/'images.owned').write_bytes((OLD/'images.owned').read_bytes())
(E/'run-id').write_text((OLD/'run-id').read_text().strip()+'-r2\n')
(E/'image-provenance.json').write_text(json.dumps({'qualified_images_from':str(OLD),'images_sha256':hashlib.sha256((OLD/'images.owned').read_bytes()).hexdigest()},indent=2)+'\n')
for name in ('owner-bootstrap.py','owner-setup.py','owner-failures.py'):
    subprocess.run([sys.executable,str(P/name)],check=True)
print('r2 producer setup and recovery preflight complete. Evidence: '+str(E))
