#!/usr/bin/env python3
"""Selected short worker deadline component; no Job/profile/store changes."""
import hashlib,json,os,subprocess,sys,tempfile,time,uuid
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-short-deadline')
IMAGE='sha256:43482aa6d8777fc02a0a64ba20ea3a830a7b84a93ec584b25bbc7a3f527bf215'
assert hashlib.sha256((P/'probe.py').read_bytes()).hexdigest()=='fe56955bae822ba304740e1b367adf595f1119e8d993efae4a179335dfb4d0ac'
if sys.argv[1:]==['--check']:
    compile((P/'probe.py').read_text(),str(P/'probe.py'),'exec')
    print('Short worker probe prepared. No execution.');raise SystemExit(0)
assert not sys.argv[1:]
assert subprocess.check_output(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],text=True,timeout=20).strip()==IMAGE
E=Path(tempfile.mkdtemp(prefix='engine-',dir=P));cid=None
try:
    argv=['docker','create','--name','baton-695-deadline-'+uuid.uuid4().hex,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777','--mount','type=bind,src='+str(P/'probe.py')+',dst=/probe.py,readonly','--entrypoint','python3',IMAGE,'/probe.py']
    cid=subprocess.check_output(argv,text=True,timeout=20).strip();(E/'container-id').write_text(cid+'\n')
    with (E/'probe.log').open('x') as log:
        result=subprocess.run(['docker','start','-a',cid],stdout=log,stderr=subprocess.STDOUT,timeout=25)
    inspect=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=20))[0]
    (E/'inspect.json').write_text(json.dumps(inspect,indent=2)+'\n')
    assert result.returncode==0 and inspect['State']['ExitCode']==0,(result.returncode,inspect['State'])
    r=json.loads((E/'probe.log').read_text())
    assert r['publication_entry_sha256']=='7136bc7a779520d68f814d58ebf3bb18aa158d905cfeaec002b7a01aaecfdd2b','image entry bytes differ'
    print((E/'probe.log').read_text(),end='')
finally:
    if cid:
        state=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=20))[0]['State']
        if state['Running']:subprocess.run(['docker','stop','--time','1',cid],check=True,timeout=20)
        subprocess.run(['docker','rm',cid],check=True,stdout=subprocess.DEVNULL,timeout=20)
        left=subprocess.check_output(['docker','ps','-aq','--no-trunc','--filter','id='+cid],text=True,timeout=20)
        assert not left.strip(),'container cleanup unresolved'
        (E/'cleanup.json').write_text(json.dumps({'id':cid,'absent':True})+'\n')
print('Worker component passed; container removed. Host-clock evidence is separate. Evidence: '+str(E))
