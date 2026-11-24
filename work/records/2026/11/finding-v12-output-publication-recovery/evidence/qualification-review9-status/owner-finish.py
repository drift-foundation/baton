#!/usr/bin/env python3
"""Package the completion reader, then check already-retained recovery. No Job runs."""
import json,subprocess,sys,time,hashlib
from pathlib import Path
ROOT=Path('/home/sl/src/baton')
P=ROOT/'work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-review9-status'
I=Path('/home/sl/baton-instances/qualify-w385695-recovery-9')
A='9cfe8b6af0c2434399e6d9a28ed69827'
subprocess.run([sys.executable,str(P/'owner-rebuild.py'),'--check'],check=True)
if sys.argv[1:]==['--check']:
    print('Completion source verified. No build or run.');raise SystemExit(0)
assert not sys.argv[1:]
subprocess.run([sys.executable,str(P/'owner-rebuild.py')],check=True)
E=P/('packaged-readback-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()));E.mkdir()
argv=[str(ROOT/'v12/python/build/out/distro/baton-v12-stack'),'manager','publication-status','--store',str(I/'db/jobs.sqlite3'),'--control',str(I/'db/control.sqlite3'),'--authority-uuid',A,'--incarnation','completion-readback','--decision-id','option-a-20261124T062254Z-1632328-recovery-9-D1']
s=subprocess.check_output(argv,timeout=60,text=True);(E/'status.json').write_text(s);r=json.loads(s)
assert r['review']['state']=='completed',r['review']
assert r['review']['ended_without_verdict'] is None
assert r['review']['verdict']['disposition']=='accepted'
assert r['review']['verdict']['candidate_is_the_approved_original'] is True
assert r['recovery']['handed_off'] and r['recovery']['custody']
assert r['publication_attempt']['recorded']['execution_runtime']=='destroyed'
left=subprocess.check_output(['docker','ps','-aq','--filter','label=baton.v12.authority_uuid='+A],text=True,timeout=30)
(E/'remaining-containers.txt').write_text(left);assert not left.strip(),'containers remain'
(E/'result.json').write_text(json.dumps({'state':'completed','verdict':'accepted','candidate_is_the_approved_original':True,'containers_remaining':False,'execution_repeated':False,'scope':'packaged readback of retained recovery-9; deadline gate separate'},indent=2)+'\n')
print('PASS: retained recovery-9 completed, exact candidate accepted, no containers remain.')
print('No Job, implementation, publication or review was rerun. Evidence: '+str(E))
