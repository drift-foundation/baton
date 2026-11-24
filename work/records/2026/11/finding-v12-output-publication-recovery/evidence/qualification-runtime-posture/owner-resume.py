#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,shlex,subprocess,sys
ROOT=Path('/home/sl/src/baton')
P=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-runtime-posture'
PREP=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-status-review-run'
E=Path('/home/sl/baton-qualification/w385695-recovery-7')
D=Path('/home/sl/baton-instances/qualify-w385695-recovery-7')
assert sys.argv[1:] in ([],['--check'])
for name,want in json.loads((P/'files.json').read_text()).items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==want,name
subprocess.run([sys.executable,str(PREP/'recovery/owner-failures.py'),'--check'],check=True)
raw=(E/'option-a.env').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d4fe8c563e5d544c1bd13c6f548fb1b5ef7c82cce4cadc4895bfa9b0f97d30e3'
words=shlex.split(raw.decode());assert words.pop(0)=='export';selected=dict(x.split('=',1) for x in words)
assert set(selected)=={'JOB','STAGE','EPISODE','DECISION'}
status=json.loads(subprocess.check_output([str(D/'distro/baton-v12-stack'),'manager','publication-status','--store',str(D/'db/jobs.sqlite3'),'--authority-uuid',json.loads((D/'instance.json').read_text())['authority_uuid'],'--incarnation','qualification-resume-read','--control',str(D/'db/control.sqlite3'),'--decision-id',selected['DECISION']],text=True))
assert status['recovery']['handed_off'] and status['recovery']['outcome']=='published',status['recovery']
attempt=status['publication_attempt']['attempt_id']
capture=E/('recovery.container-'+attempt+'.json')
assert hashlib.sha256(capture.read_bytes()).hexdigest()=='ce301e25661b86742065c624dd81347f1b80b1291160ab6d7b8da32e0b9fd9ac','original capture changed'
subprocess.run([sys.executable,str(P/'verify-publisher.py'),str(capture),str(D/'instance.json'),attempt],check=True)
assert not list(E.glob('resume.*')),'resume already attempted; inspect before repeating'
if sys.argv[1:]==['--check']:
    print('Existing admitted recovery and retained publisher evidence checked. Nothing started.')
    raise SystemExit(0)
for name,data in [('resume.container-'+attempt+'.json',capture.read_bytes()),('resume.publisher-seen',(E/'recovery.publisher-seen').read_bytes())]:
    with (E/name).open('xb') as out:out.write(data)
(E/'resume.provenance.json').write_text(json.dumps({'publisher_capture_from':str(capture),'same_attempt':attempt,'no_new_decision':True,'no_producer_or_publication_redispatch':True},indent=2)+'\n')
env=os.environ.copy()
for key in list(env):
    if key.startswith('BATON_V12_') or key=='PYTHONPATH':env.pop(key)
env.update(selected,TREE=str(ROOT),EVIDENCE=str(E),INSTANCE=str(D/'instance.json'),OWNER='baton.slaw',ENGINE='docker')
print('Resuming the manager for the existing recovery; no new approval or producer run.',flush=True)
raise SystemExit(subprocess.run(['bash',str(P/'qualify-resume.sh'),'resume'],env=env).returncode)
