#!/usr/bin/env python3
"""Run the selected installed publication/review qualification; no live model."""
from pathlib import Path
import hashlib,json,os,shlex,subprocess,sys
ROOT=Path('/home/sl/src/baton')
P=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-inherited-links-run'
E=Path('/home/sl/baton-qualification/w385695-recovery-6')
D=Path('/home/sl/baton-instances/qualify-w385695-recovery-6')
assert sys.argv[1:] in ([],['--check']),'usage: script [--check]'
for name,want in json.loads((P/'recovery/files.json').read_text()).items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==want,name
subprocess.run([sys.executable,str(P/'recovery/owner-failures.py'),'--check'],check=True)
raw=(E/'option-a.env').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='ff5673f0c98702674212f3f04f118393f154e80afe9bfba17200f1439b655687','prepared Job selectors changed'
words=shlex.split(raw.decode());assert words.pop(0)=='export'
selected=dict(word.split('=',1) for word in words)
assert set(selected)=={'JOB','STAGE','EPISODE','DECISION'}
assert selected['STAGE']==selected['JOB']+'/implementation' and selected['EPISODE']=='1'
assert not list(E.glob('recovery.*')),'recovery phase already attempted; inspect before repeating'
env=os.environ.copy()
for key in list(env):
    if key.startswith(('BATON_V12_', 'PYTHONPATH')):env.pop(key)
env.update(selected,TREE=str(ROOT),EVIDENCE=str(E),INSTANCE=str(D/'instance.json'),OWNER='baton.slaw',ENGINE='docker')
if sys.argv[1:]==['--check']:
    print('Exact runtime, images/configuration, scripts and failed Job selectors checked. Recovery not admitted.')
    raise SystemExit(0)
print('Starting installed scripted publication -> custody -> review qualification. Evidence: '+str(E),flush=True)
result=subprocess.run(['bash',str(P/'scripts/qualify-w385695.sh'),'recovery'],env=env)
raise SystemExit(result.returncode)
