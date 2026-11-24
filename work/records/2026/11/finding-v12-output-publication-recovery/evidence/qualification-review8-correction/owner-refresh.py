#!/usr/bin/env python3
"""Refresh the host bundle and two worker images. No Job or live model is run."""
import hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-review8-correction')
CONTEXT=P/'image-context'
BASE='sha256:0ad2c553865ebb6a95c6014686f61dd97e69f0bee617af005a2ace8f83ab89e7'
assert hashlib.sha256((CONTEXT/'files.json').read_bytes()).hexdigest()=='db67aaf1f40a7170908ffe591859c4f4d166de90e3cfa1602559ec66d77945e7'
for name,want in json.loads((CONTEXT/'files.json').read_text()).items():
    assert hashlib.sha256((CONTEXT/name).read_bytes()).hexdigest()==want,name
subprocess.run([sys.executable,str(P/'owner-rebuild.py'),'--check'],check=True)
if sys.argv[1:]==['--check']:
    print('Source and image inputs verified. No build or execution.')
    raise SystemExit(0)
assert not sys.argv[1:],'usage: script [--check]'
subprocess.run([sys.executable,str(P/'owner-rebuild.py')],check=True)
E=Path('/home/sl/baton-qualification')/('w385695-review-refresh-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()))
E.mkdir()
suffix=E.name.removeprefix('w385695-review-refresh-').lower()
assert subprocess.check_output(['docker','image','inspect',BASE,'--format','{{.Id}}'],text=True).strip()==BASE
images={}
for role in ('provider','fixture'):
    tag='baton-v12-'+role+':w385695-review-'+suffix
    assert subprocess.run(['docker','image','inspect',tag],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0,'tag already exists'
    argv=['docker','build','-f',str(CONTEXT/('Dockerfile.'+role)),'-t',tag]
    if role=='fixture':argv+=['--build-arg','PROVIDER_BASE='+images['provider']['id']]
    argv+=[str(CONTEXT)]
    print('Building '+role+'; log '+str(E/(role+'.log')),flush=True)
    with (E/(role+'.log')).open('x') as log:
        subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    image=json.loads(subprocess.check_output(['docker','image','inspect',tag]))[0]
    images[role]={'tag':tag,'id':image['Id']}
    (E/(role+'-inspect.json')).write_text(json.dumps(image,indent=2)+'\n')
    assert image['Config']['User']=='65532:65532'
    want=hashlib.sha256((CONTEXT/'claude_agent.py').read_bytes()).hexdigest()
    argv=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--entrypoint','python3',image['Id'],'-c',"import hashlib; print(hashlib.sha256(open('/opt/baton/claude_agent.py','rb').read()).hexdigest())"]
    actual=subprocess.check_output(argv,text=True,timeout=30).strip()
    assert actual==want,(role,actual,want)
    print(role+': '+image['Id']+'; corrected adapter bytes verified',flush=True)
# Reproduce a >32 MiB verification copy in the built fixture, without an overlay.
scratch=Path(tempfile.mkdtemp(prefix='baton-695-disk-gate-',dir='/var/tmp'))
probe=P/'disk-probe.py'
assert hashlib.sha256(probe.read_bytes()).hexdigest()=='5639899ead0afd3a8519fe853a409fb2ea0e68dae1ff8e34342dbfcfebedbfde'
argv=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777','--mount','type=bind,src='+str(probe)+',dst=/probe.py,readonly','--mount','type=bind,src='+str(scratch)+',dst=/scratch','--entrypoint','python3',images['fixture']['id'],'/probe.py']
with (E/'disk-gate.log').open('x') as log:
    subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
(E/'images.json').write_text(json.dumps(images,indent=2)+'\n')
print((E/'disk-gate.log').read_text(),end='')
print('Refresh complete. No Job or live provider call. Evidence: '+str(E))
