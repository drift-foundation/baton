#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-inherited-links-run')
OLD=Path('/home/sl/baton-qualification/w385695-560eaa89-images-1')
scenario=sys.argv[1] if len(sys.argv)>1 else 'recovery'
assert scenario in ('recovery','deadline'),'select recovery or deadline'
check=sys.argv[2:]==['--check']
assert not sys.argv[2:] or check,'usage: script [recovery|deadline] [--check]'
Q=P/scenario
E=Path('/home/sl/baton-qualification/w385695-'+scenario+'-6')
assert not E.is_symlink(), 'evidence path is a link'
fixed = json.loads(Path('/home/sl/baton-qualification/w385695-fixture-label-fixed-1/image.json').read_text())
assert fixed['id']=='sha256:b7d1543c9ae60f1ed4e4f724a3b99f51b23dac34909d08c3583b150b6c485924'
image_lines=[]
for line in (OLD/'images.owned').read_text().splitlines():
    name,tag,identity=line.split()
    if name=='fixture': tag,identity=fixed['tag'],fixed['id']
    image_lines.append(' '.join((name,tag,identity)))
images=('\n'.join(image_lines)+'\n').encode()
seed = {
    'images.owned': images,
    'run-id': ((OLD/'run-id').read_text().strip()+'-'+scenario+'-6\n').encode(),
    'image-provenance.json': (json.dumps({'qualified_images_from':str(OLD),'shared_images_do_not_remove':True,'corrected_fixture':fixed},indent=2)+'\n').encode(),
}
if E.exists():
    assert E.is_dir() and {x.name for x in E.iterdir()} == set(seed), 'scenario progressed beyond pre-install metadata; inspect before repeating'
    for name, data in seed.items():
        assert not (E/name).is_symlink() and (E/name).read_bytes()==data, 'pre-install metadata changed: '+name
for name,want in json.loads((Q/'files.json').read_text()).items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==want,name
subprocess.run([sys.executable,str(Q/'owner-bootstrap.py'),'--check'],check=True)
if check:
    print('Prepared independent '+scenario+' scenario verified. Nothing started.')
    raise SystemExit(0)
for line in images.decode().splitlines():
    name,tag,want=line.split()
    assert subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip()==want,name
if not E.exists():
    E.mkdir()
    for name,data in seed.items():
        with (E/name).open('xb') as out: out.write(data)
for name in ('owner-bootstrap.py','owner-setup.py','owner-failures.py'):
    subprocess.run([sys.executable,str(Q/name)],check=True)
print('Independent '+scenario+' original ready. Actual recovery/deadline gate has not run.')
