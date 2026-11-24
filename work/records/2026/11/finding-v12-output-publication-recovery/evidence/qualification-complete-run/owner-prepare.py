#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-complete-run')
OLD=Path('/home/sl/baton-qualification/w385695-560eaa89-images-1')
scenario=sys.argv[1] if len(sys.argv)>1 else 'recovery'
assert scenario in ('recovery','deadline'),'select recovery or deadline'
check=sys.argv[2:]==['--check']
assert not sys.argv[2:] or check,'usage: script [recovery|deadline] [--check]'
Q=P/scenario
E=Path('/home/sl/baton-qualification/w385695-'+scenario+'-8')
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
    'run-id': ((OLD/'run-id').read_text().strip()+'-'+scenario+'-8\n').encode(),
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
if scenario == 'recovery':
    import os,shlex
    words=shlex.split((E/'option-a.env').read_text()); assert words.pop(0)=='export'
    selected=dict(word.split('=',1) for word in words)
    assert set(selected)=={'JOB','STAGE','EPISODE','DECISION'}
    assert selected['STAGE']==selected['JOB']+'/implementation' and selected['EPISODE']=='1'
    assert not list(E.glob('recovery.*')),'recovery already attempted'
    env=os.environ.copy()
    for key in list(env):
        if key.startswith('BATON_V12_') or key=='PYTHONPATH':env.pop(key)
    env.update(selected,TREE='/home/sl/src/baton',EVIDENCE=str(E),INSTANCE='/home/sl/baton-instances/qualify-w385695-recovery-8/instance.json',OWNER='baton.slaw',ENGINE='docker')
    print('Starting selected scripted publication/custody/review gate.',flush=True)
    os.execve(sys.executable,[sys.executable,str(P/'scripts/run-phase.py'),'bash',str(P/'scripts/qualify-w385695.sh'),'recovery'],env)
else:
    print('Deadline gate not run; only its independent original prepared.')
