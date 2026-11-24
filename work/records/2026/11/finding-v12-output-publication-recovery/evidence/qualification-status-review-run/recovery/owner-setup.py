#!/usr/bin/env python3
"""Owner-run Option A workers + one Job; no services or containers started."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/home/sl/src/baton')
R=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery'
P=R/'evidence/qualification-status-review-run/recovery'
S=R/'evidence/qualification-status-review-run/scripts'
E=Path('/home/sl/baton-qualification/w385695-recovery-7')
D=Path('/home/sl/baton-instances/qualify-w385695-recovery-7')
subprocess.run([sys.executable,'/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-observation-binding/owner-rebuild.py','--check'],check=True)
for name,want in json.loads((S/'files.json').read_text()).items():
    assert hashlib.sha256((S/name).read_bytes()).hexdigest()==want,name
assert hashlib.sha256((P/'installed-task.json').read_bytes()).hexdigest()=='cd54150326936199325186d747b9fcbfb4f20d5ff66ee2a5830c03070b29339f','task changed'
assert json.loads((D/'instance.json').read_text())['destination']==str(D)
assert json.loads((D/'install-inputs.json').read_text())['line_declared_base']=='560eaa895236ae28bcf204f308b82679f32abbbd'
expected=json.loads((P/'runtime-manifest.json').read_text()); actual={}
for f in sorted((D/'distro').rglob('*')):
    if f.is_symlink():
        assert f.exists() and f.resolve().is_relative_to((D/'distro').resolve()),f
        actual[str(f.relative_to(D/'distro'))]='link:'+os.readlink(f)
    elif f.is_file():actual[str(f.relative_to(D/'distro'))]=hashlib.sha256(f.read_bytes()).hexdigest()
assert actual==expected,'installed runtime changed'
assert not json.loads((D/'deployment.json').read_text()).get('workers'),'workers already installed; inspect before repeating'
for name,want in [('fixture','sha256:b7d1543c9ae60f1ed4e4f724a3b99f51b23dac34909d08c3583b150b6c485924'),('publication','sha256:43482aa6d8777fc02a0a64ba20ea3a830a7b84a93ec584b25bbc7a3f527bf215')]:
    entries=[line.split() for line in (E/'images.owned').read_text().splitlines() if line.split()[0]==name]
    assert len(entries)==1 and entries[0][2]==want,(name,entries)
assert 1001 in os.getgroups(),'workspace group missing'
env=os.environ.copy(); env.update(EVIDENCE=str(E),INSTANCE=str(D/'instance.json'),REPOSITORY_SOURCE=str(ROOT),CHECKOUT=str(ROOT),RECORD=str(R.relative_to(ROOT)),TASK_DOCUMENT=str(D/'state/task/qualification.json'),WORKSPACE_GROUP='1001',NETWORK='none',CREDENTIAL_SOURCES=str(E/'private/registry.json'),CREDENTIAL='claude=operator-file:w385695-dummy',VERIFIER_LAYOUT=str(ROOT/'v12/worker/verifier-layout-marker.json'),CLI_BUILD='2.1.247',IMPLEMENTER='baton.claude-native',REVIEWER='baton.reviewer-native',PUBLISHER='baton.publisher-qualification',OWNER='baton.slaw',WORK_SCOPE='big.txt')
if sys.argv[1:]==['--check']:
    for step in ('compose-implementation','compose-review','compose-publication','repeat','create-1'):
        subprocess.run(['bash',str(S/'option-a-setup.sh'),'argv',step],env=env,check=True,stdout=subprocess.DEVNULL)
    print('Installed runtime, script identities and five prepared command vectors checked. No workers or Jobs created.')
    raise SystemExit(0)
assert not sys.argv[1:],'usage: script [--check]'
assert not (E/'private').exists(),'setup already attempted; inspect before repeating'
(E/'private').mkdir(mode=0o700)
for name,value in [('dummy.json','qualification-only-' + hashlib.sha256(str(D).encode()).hexdigest() + '\n'),('registry.json',json.dumps({'schema':'baton.user-credential-sources/1','sources':[{'provider':'operator-file','reference':'w385695-dummy','path':str(E/'private/dummy.json')}]})+'\n')]:
    fd=os.open(E/'private'/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:f.write(value)
(D/'state/task').mkdir(parents=True,exist_ok=True)
with (D/'state/task/qualification.json').open('xb') as f:f.write((P/'installed-task.json').read_bytes())
for phase in ('workers','jobs'):
    subprocess.run(['bash',str(S/'option-a-setup.sh'),phase],env=env,check=True)
    if phase == 'workers':
        workers=json.loads((D/'deployment.json').read_text())['workers']
        for worker in workers:
            if worker['role'] not in ('implementation','review'): continue
            outputs=worker['deployment']['input_manifest']['outputs']
            by={x['name']:x for x in outputs}
            assert {'proposal','findings','logs'} <= set(by),'missing role outputs'
            assert all(not x['required'] for x in outputs),'shared outputs must be optional'
            assert by['proposal']['constraints']['max_bytes']==1048576,'proposal ceiling changed'
        print('Both provider roles declare proposal/findings/logs; 1 MiB ceiling verified.',flush=True)
(E/'setup-environment.json').write_text(json.dumps({k:env[k] for k in ('EVIDENCE','INSTANCE','OWNER')},indent=2)+'\n')
print('Workers and one scripted qualification Job prepared. Services remain stopped; no provider was called.')
