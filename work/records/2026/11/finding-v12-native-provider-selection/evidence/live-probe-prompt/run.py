import os,sys,json,subprocess,pathlib,time,tarfile,io,hashlib,shutil
sys.dont_write_bytecode=True
os.umask(0o077)
P=pathlib.Path
REPO=P('/home/sl/src/baton')
COMMIT='f875ed01b51b6b7541ad169b560004e47731ad34'
ROOT=P('/var/tmp/baton-codex-q1-live-386097')
IMAGE='sha256:46a46ee4ae3dcfdb23951fc8651b28c9ab50ad03e3422d96e53f615ac0eaaa63'
NAME='baton-codex-q1-live-386097'
NET=NAME+'-net'
DOS=REPO/'work/records/2026/11/finding-v12-native-provider-selection'
AUTH='Owner explicitly selected run here after M386099: one probe, source/model/settings, no retry, fast unset'
assert os.getuid()==1000 and os.getgid()==1000
assert not ROOT.exists(),'root already exists; no replay'
for p in (ROOT,*ROOT.parents):
    assert not p.is_symlink() and not (p/'.git').exists()
assert not any(os.environ.get(k) for k in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','DOCKER_HOST','DOCKER_CONTEXT'))
ROOT.mkdir(mode=0o700)
(ROOT/'control').mkdir()
(ROOT/'docker-config').mkdir()
env={'PATH':os.environ['PATH'],'HOME':str(ROOT),'DOCKER_CONFIG':str(ROOT/'docker-config'),'LANG':'C.UTF-8'}
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
n=0
def cmd(label,argv,timeout=20,ok=(0,)):
    global n
    n+=1;p=ROOT/'control'/f'{n:02d}-{label}'; start=time.monotonic()
    with p.with_suffix('.stdout').open('xb') as out,p.with_suffix('.stderr').open('xb') as err:
        try:r=subprocess.run(argv,env=env,stdout=out,stderr=err,timeout=timeout)
        except BaseException:
            save(p.with_suffix('.json'),{'argv':argv,'seconds':time.monotonic()-start,'outcome':'interrupted-or-timeout'});raise
    save(p.with_suffix('.json'),{'argv':argv,'seconds':time.monotonic()-start,'status':r.returncode})
    assert r.returncode in ok,label+' refused; inspect PRIVATE log, no retry'
    return p.with_suffix('.stdout').read_bytes()
assert not cmd('name-check',['docker','ps','-aq','--filter','name=^/'+NAME+'$']).strip()
assert not cmd('network-check',['docker','network','ls','-q','--filter','name=^'+NET+'$']).strip()
image=json.loads(cmd('image',['docker','image','inspect',IMAGE]))[0]
assert image['Id']==IMAGE and image['Config']['Entrypoint']==['python3','/opt/baton/codex_entry.py']
raw=subprocess.check_output(['git','-C',str(REPO),'archive',COMMIT,'v12'])
source=ROOT/'source';source.mkdir()
with tarfile.open(fileobj=io.BytesIO(raw)) as t:t.extractall(source,filter='data')
sys.path[:0]=[str(source/'v12/worker'),str(source/'v12/python'),str(source/'v12/python/src'),str(source/'v12/python/src/baton_v12')]
import provider_policy as policy
from codex_agent import CodexAgent
from tools.qualification_credentials import prepare_selected
packet=ROOT/'packet';packet.mkdir()
capture=DOS/'evidence/qualification-tier-386092/capture.py'
shutil.copyfile(capture,packet/'capture.py')
selection={'authorization_credential_copy':AUTH,'credential_source_reference':'codex-pushcoin-subscription','credential_path_evidence':'Stage A M386075: CODEX_HOME/auth.json ENOENT','credential_storage_mode_evidence':'B1 option1 staging only; successful subscription authentication not yet proved','private_retention_and_cleanup_owner':'Slawomir, retain private evidence/home pending classification','refresh_copy_disposition':'keep refreshed private copy; never write back to source','uid':1000,'gid':1000,'execution_root':str(ROOT),'codex_home_relative_to_home':'codex','credential_relative_path':'auth.json','instruction_relative_to_home':'instructions/WORKER.md','explicit_model':'gpt-6-astra','service_tier':None,'image':IMAGE,'source_checkpoint':COMMIT,'authorization_live':AUTH,'live_network':NET}
save(ROOT/'selection.json',selection)
registry=P('/home/sl/baton-qualification/codex-q1-live-386097-source.json')
assert not registry.exists(),'source registry already exists'
registry.parent.mkdir(exist_ok=True)
save(registry,{'reference':'codex-pushcoin-subscription','path':'/home/sl/.codex-pushcoin/auth.json'})
# Metadata only for unchanged-source check. Never publish credential bytes/digests.
auth=P('/home/sl/.codex-pushcoin/auth.json');st=auth.stat();before=(st.st_ino,st.st_size,st.st_mtime_ns,st.st_mode)
prepare_selected(selection,str(registry))
raw_instructions=policy.worker_instructions();sha='sha256:'+hashlib.sha256(raw_instructions).hexdigest()
home=ROOT/'live/home';(home/'instructions').mkdir();(home/'instructions/WORKER.md').write_bytes(raw_instructions)
doc={'provider':'codex','home':'/run/baton/provider-home','context_label':policy._context_label('codex'),'managed_entries':[{'path':'instructions/WORKER.md','kind':policy.INSTRUCTIONS_KIND,'sha256':sha,'bytes':len(raw_instructions)}]}
task=('Qualification-only task, no product repository and no native Job acceptance. Act only as implementation. '
'Read the delivered worker instruction file named above. Use a local read/hash tool to compute its SHA-256. '
'Do not inspect auth, session stores, environment values, other home files, or any network resource. '
'Do not delegate or edit files. Reply once with qualification_probe=complete, your assigned role, and the computed '
'worker_instructions_sha256, its byte length, and its exact first line. Compute these from the delivered file, not from the label. '
'State any inability honestly. Do not claim a model identity.')
prompt=policy.labelled(doc,'implementation',task)
argv=CodexAgent.__new__(CodexAgent).provider_argv(prompt,model='gpt-6-astra',service_tier=None)
assert len(argv)==9 and argv[6:8]==['--model','gpt-6-astra']
save(packet/'live-context.json',{'qualification_only':True,'authorization':AUTH,'source_checkpoint':COMMIT,'service_tier':{'requested':None,'observed':None},'login_status_help_evidence':'Stage A retained exact 0.169.0 help','tool_inventory_evidence':'product-image-preparation-r2/results/offline-checks.json','image_tool_decision':'Owner selected retained image46a46ee4 for detached harness only','codex_home':'/run/baton/provider-home/codex','instruction_relative_to_home':'instructions/WORKER.md','argv':argv,'context_record':policy.context_record(doc,'implementation')})
cmd('workspace-init',['git','init','--quiet',str(ROOT/'live/workspace')])
# Record only nonsecret source/probe hashes, not credentials or home state.
save(ROOT/'packet-identity.json',{'source_archive_sha256':hashlib.sha256(raw).hexdigest(),'capture_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),'context_sha256':hashlib.sha256((packet/'live-context.json').read_bytes()).hexdigest(),'instruction_sha256':sha,'image':IMAGE,'source_checkpoint':COMMIT})
created=False; network=False;ceased=False;removed=False;turn_status=None
try:
    cmd('network-create',['docker','network','create','--label','baton.qualification='+NAME,NET]);network=True
    create=['docker','create','--name',NAME,'--label','baton.qualification='+NAME,'--network',NET,'--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--user','1000:1000','--pids-limit','128','--memory','1g','--cpus','1','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--workdir','/workspace']
    for src,dst,ro in [(packet,'/packet',True),(home,'/run/baton/provider-home',False),(ROOT/'live/workspace','/workspace',False),(ROOT/'live/private-output','/private-output',False)]:
        create+=['--mount',f'type=bind,src={src},dst={dst}'+(',readonly' if ro else '')]
    create+=['--entrypoint','python3',IMAGE,'/packet/capture.py','live']
    cmd('create',create);created=True
    cmd('start',['docker','start',NAME]);started=time.monotonic()
    print('One selected container started; raw output stays private.',flush=True)
    while True:
        info=json.loads(cmd('poll',['docker','inspect',NAME]))[0]
        if not info['State']['Running']:
            ceased=True;turn_status=info['State']['ExitCode'];break
        if time.monotonic()-started>255:raise TimeoutError('outer bound reached')
        time.sleep(10)
finally:
    if created:
        info=json.loads(cmd('cleanup-inspect',['docker','inspect',NAME]))[0]
        if info['State']['Running']:
            cmd('stop',['docker','stop','--time','15',NAME],30)
        info=json.loads(cmd('settled',['docker','inspect',NAME]))[0]
        if info['State']['Running']:
            cmd('kill',['docker','kill',NAME]);info=json.loads(cmd('after-kill',['docker','inspect',NAME]))[0]
        assert not info['State']['Running'],'cessation unresolved'
        ceased=True
        cmd('private-container-logs',['docker','logs',NAME])
        cmd('remove',['docker','rm',NAME])
        assert not cmd('absence',['docker','ps','-aq','--filter','label=baton.qualification='+NAME]).strip()
        removed=True
    if network and (removed or not created):cmd('network-remove',['docker','network','rm',NET])
    st=auth.stat();unchanged=before==(st.st_ino,st.st_size,st.st_mtime_ns,st.st_mode)
    result={'container_exit':turn_status,'ceased':ceased,'container_removed':removed,'source_metadata_unchanged':unchanged,'raw_output_private':True,'native_qualification':False,'no_retry':True}
    save(ROOT/'EXECUTION.json',result)
    print(json.dumps(result),flush=True)
