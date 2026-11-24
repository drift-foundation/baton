#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-independent-scenarios')
OLD=Path('/home/sl/baton-qualification/w385695-560eaa89-images-1')
scenario=sys.argv[1] if len(sys.argv)>1 else 'recovery'
assert scenario in ('recovery','deadline'),'select recovery or deadline'
check=sys.argv[2:]==['--check']
assert not sys.argv[2:] or check,'usage: script [recovery|deadline] [--check]'
Q=P/scenario
E=Path('/home/sl/baton-qualification/w385695-'+scenario+'-3')
assert not E.exists() and not E.is_symlink(),'scenario already attempted; inspect before repeating'
for name,want in json.loads((Q/'files.json').read_text()).items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==want,name
subprocess.run([sys.executable,str(Q/'owner-bootstrap.py'),'--check'],check=True)
if check:
    print('Prepared independent '+scenario+' scenario verified. Nothing started.')
    raise SystemExit(0)
for line in (OLD/'images.owned').read_text().splitlines():
    name,tag,want=line.split()
    assert subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip()==want,name
E.mkdir()
(E/'images.owned').write_bytes((OLD/'images.owned').read_bytes())
(E/'run-id').write_text((OLD/'run-id').read_text().strip()+'-'+scenario+'-3\n')
(E/'image-provenance.json').write_text(json.dumps({'qualified_images_from':str(OLD),'shared_images_do_not_remove':True},indent=2)+'\n')
for name in ('owner-bootstrap.py','owner-setup.py','owner-failures.py'):
    subprocess.run([sys.executable,str(Q/name)],check=True)
print('Independent '+scenario+' original ready. Actual recovery/deadline gate has not run.')
