#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-deadline-final')
OLD=Path('/home/sl/baton-qualification/w385695-560eaa89-images-1')
scenario='deadline'
check=sys.argv[1:]==['--check']
assert not sys.argv[1:] or check,'usage: script [--check]'
Q=P/scenario
E=Path('/home/sl/baton-qualification/w385695-'+scenario+'-9')
assert not E.is_symlink(), 'evidence path is a link'
refreshed = json.loads(Path('/home/sl/baton-qualification/w385695-review-refresh-20261124T080916Z/images.json').read_text())
fixed = refreshed['fixture']
assert fixed['id']=='sha256:84b37a82090093d627f711d2c51d761885b59fe037cee20babee8e3442fce44a'
image_lines=[]
for line in (OLD/'images.owned').read_text().splitlines():
    name,tag,identity=line.split()
    if name in refreshed: tag,identity=refreshed[name]['tag'],refreshed[name]['id']
    image_lines.append(' '.join((name,tag,identity)))
images=('\n'.join(image_lines)+'\n').encode()
seed = {
    'images.owned': images,
    'run-id': ((OLD/'run-id').read_text().strip()+'-'+scenario+'-9\n').encode(),
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
print('Independent '+scenario+' original ready.',flush=True)
import os,shlex
words=shlex.split((E/'option-a.env').read_text());assert words.pop(0)=='export'
selected=dict(word.split('=',1) for word in words)
assert set(selected)=={'JOB','STAGE','EPISODE','DECISION'}
assert selected['STAGE']==selected['JOB']+'/implementation' and selected['EPISODE']=='1'
assert not list(E.glob('deadline.*')),'deadline gate already attempted'
env=os.environ.copy()
for key in list(env):
    if key.startswith('BATON_V12_') or key=='PYTHONPATH':env.pop(key)
env.update({key+'2':value for key,value in selected.items()})
env.update(TREE='/home/sl/src/baton',EVIDENCE=str(E),INSTANCE='/home/sl/baton-instances/qualify-w385695-deadline-9/instance.json',OWNER='baton.slaw',ENGINE='docker')
print('Starting deadline gate: publisher deliberately paused until its real 900-second deadline. Expect about 15 minutes plus setup/cleanup; no live model.',flush=True)
os.execve(sys.executable,[sys.executable,str(P/'scripts/run-phase.py'),'bash',str(P/'scripts/qualify-w385695.sh'),'deadline'],env)
