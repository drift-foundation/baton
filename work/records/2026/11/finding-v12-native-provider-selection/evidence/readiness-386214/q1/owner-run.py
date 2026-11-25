#!/usr/bin/env python3
"""Q1 owner-run packet. Default/check is read-only and has NO engine calls."""
import argparse, ast, hashlib, json, os, re, selectors, shutil, signal, subprocess, sys, tarfile, time
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=Path('/var/tmp/baton-codex-q1-386214')
DEST=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/q1-execution-386214')
BASE='PENDING-HUMAN-CHECKPOINT'
IMAGE=re.compile(r'sha256:[0-9a-f]{64}')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def check():
    if not __debug__:raise RuntimeError('optimized Python disables packet validation; refused')
    manifest=json.loads((P/'packet-files.json').read_text())
    for name,expected in manifest.items():
        assert '/' not in name and (P/name).is_file() and not (P/name).is_symlink(),name
        assert sha((P/name).read_bytes())==expected,name
    inputs=json.loads((P/'inputs.json').read_text());assert inputs['source_commit']==BASE
    for name,key in [('source.tar','source_tar_sha256'),('context.tar','context_tar_sha256'),('Dockerfile.q1','recipe_sha256'),('source-files.json','source_manifest_sha256')]:assert sha((P/name).read_bytes())==inputs[key],name
    for name in ('owner-run.py','manager_probe.py','worker_probe.py','check_preparation.py'):ast.parse((P/name).read_text(),filename=name)
    with tarfile.open(P/'source.tar') as t:
        expected=json.loads((P/'source-files.json').read_text());seen={}
        for item in t:
            assert item.isfile() and not item.name.startswith('/') and '..' not in Path(item.name).parts
            assert item.name not in seen
            seen[item.name]={'sha256':sha(t.extractfile(item).read()),'mode':item.mode}
        assert seen==expected
    with tarfile.open(P/'context.tar') as t:
        context={}
        for item in t:
            assert item.isfile() and not item.name.startswith('/') and '..' not in Path(item.name).parts
            assert item.name not in context
            context[item.name]=t.extractfile(item).read()
    assert context.pop('worker/Dockerfile.codex')==(P/'Dockerfile.q1').read_bytes()
    assert context.pop('q1-build.json')==(P/'q1-build.json').read_bytes()
    for name,raw in context.items():assert sha(raw)==expected['v12/'+name]['sha256'],name
    identity=json.loads((P/'q1-build.json').read_text())
    assert identity['source_commit']==BASE and identity['source_manifest_sha256']==inputs['source_manifest_sha256']
    assert len(context)==len(identity['image_files'])
    for name,raw in context.items():
        target='/opt/baton/'+(name.split('baton_v12/',1)[1] if 'baton_v12/' in name else Path(name).name)
        assert identity['image_files'][target]==sha(raw),name
    return dict(packet_manifest_sha256=sha((P/'packet-files.json').read_bytes()),source_commit=BASE,read_only=True,engine_calls=0,builds=0,credential_reads=0,root=str(ROOT),evidence_destination=str(DEST))

def safe_root(path):
    assert path.is_absolute() and path==Path(os.path.realpath(path))
    for parent in (path,*path.parents):
        assert not (parent/'.git').exists() and not ((parent/'HEAD').exists() and (parent/'objects').is_dir())

def extract(archive,target):
    target.mkdir(mode=0o700)
    with tarfile.open(archive) as t:
        for item in t:
            assert item.isfile() and not item.name.startswith('/') and '..' not in Path(item.name).parts
        t.extractall(target,filter='data')

class Commands:
    def __init__(self,root):
        self.root=root;self.n=0;self.deadline=time.monotonic()+1200;self.created=None;self.launches=0;self.builds=0;self.expected_labels={}
        self.env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(root/'client-home'),'DOCKER_CONFIG':str(root/'docker-config'),'DOCKER_HOST':'unix:///var/run/docker.sock','DOCKER_BUILDKIT':'0','TMPDIR':str(root/'tmp'),'LANG':'C.UTF-8'}
    def __call__(self,argv,seconds=None,cap=2*1024*1024):
        assert seconds is None or seconds>0,'nonpositive command bound'
        seconds=min(30 if seconds is None else seconds,max(0,self.deadline-time.monotonic()));assert seconds>0,'outer deadline exceeded'
        if argv[0]=='docker' and argv[1]=='build':
            assert self.builds==0,'second build refused'
            self.builds+=1
        if argv[0]=='docker' and argv[1] in ('run','create'):
            assert self.launches==0,'retry or second container refused'
            name=argv[argv.index('--name')+1]
            absent=self.required(['docker','ps','--all','--filter','name=^/'+name+'$','--format','{{.Names}}'],seconds=15)
            assert not absent['stdout'].strip(),'pre-existing name; no takeover'
            self.created=name;self.launches+=1
            self.expected_labels=dict(argv[i+1].split('=',1) for i,x in enumerate(argv[:-1]) if x=='--label')
            save(self.root/'container-intent.json',dict(name=self.created,argv=argv))
        self.n+=1;stem=self.root/'commands'/f'{self.n:03d}';start=time.monotonic()
        save(str(stem)+'.command.json',dict(argv=argv,bound_seconds=seconds,output_cap_bytes=cap,environment=self.env))
        proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=self.env,cwd=self.root,start_new_session=True)
        streams={};buffers={'stdout':bytearray(),'stderr':bytearray()};failure=None
        selector=selectors.DefaultSelector()
        for key,pipe in [('stdout',proc.stdout),('stderr',proc.stderr)]:
            os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,key);streams[key]=open(str(stem)+'.'+key,'wb')
        try:
            while selector.get_map():
                if time.monotonic()-start>seconds:raise TimeoutError('command bound exceeded')
                for key,_ in selector.select(.1):
                    raw=os.read(key.fd,65536)
                    if not raw:selector.unregister(key.fileobj);continue
                    remaining=cap-sum(map(len,buffers.values()))
                    kept=raw[:remaining];buffers[key.data].extend(kept);streams[key.data].write(kept)
                    if len(raw)>remaining:raise RuntimeError('output bound exceeded')
            proc.wait(timeout=max(.1,seconds-(time.monotonic()-start)))
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
            # Reap every member still holding a pipe in this owned process group.
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        finally:
            selector.close()
            for stream in streams.values():stream.close()
            proc.stdout.close();proc.stderr.close()
            save(str(stem)+'.result.json',dict(status=proc.returncode,duration_seconds=time.monotonic()-start,failure=failure,pid=proc.pid,pgid=proc.pid,stdout_bytes=len(buffers['stdout']),stderr_bytes=len(buffers['stderr'])))
        if failure:raise RuntimeError(failure)
        return dict(status=proc.returncode,stdout=buffers['stdout'].decode('utf-8','replace'),stderr=buffers['stderr'].decode('utf-8','replace'))
    def required(self,argv,seconds=30,cap=2*1024*1024):
        result=self(argv,seconds=seconds,cap=cap)
        assert result['status']==0,(argv[:4],result['status'])
        return result


def cleanup(run,root):
    """Only this packet's exact persisted runtime name. No prune or image removal."""
    run.deadline=time.monotonic()+90
    answer=dict(container_name=run.created,ceased=None,removed=None)
    if run.created is None:
        answer.update(ceased=True,removed=True,reason='no qualification create/run attempted')
        save(root/'cleanup.json',answer);return answer
    try:
        from baton_v12.worker_manager.oci import _absent_prose
        observed=run(['docker','inspect','--type','container',run.created])
        if observed['status']==0:
            obj=json.loads(observed['stdout'])[0]
            assert run.expected_labels and all(obj['Config']['Labels'].get(k)==v for k,v in run.expected_labels.items()),'foreign container; do not remove'
            answer['runtime_id']=obj['Id']
            if obj['State']['Running']:run.required(['docker','stop','--time','5',obj['Id']],seconds=15)
            obj=json.loads(run.required(['docker','inspect','--type','container',obj['Id']])['stdout'])[0]
            assert obj['State']['Running'] is False
            answer.update(ceased=True,exit_code=obj['State']['ExitCode'],state=obj['State'])
            run.required(['docker','rm',obj['Id']],seconds=15)
        else:
            assert _absent_prose('docker',observed['stderr'],run.created),'inspect failed without exact positive absence'
        absent=run(['docker','inspect','--type','container',run.created],seconds=15)
        listing=run.required(['docker','ps','--all','--filter','name=^/'+run.created+'$','--format','{{.Names}}'],seconds=15)
        assert absent['status']!=0 and _absent_prose('docker',absent['stderr'],run.created) and not listing['stdout'].strip()
        answer.update(ceased=True,removed=True)
    except BaseException as exc:answer['error']=type(exc).__name__+': '+str(exc)
    save(root/'cleanup.json',answer);return answer


def execute(selection,expected_packet):
    assert __import__('re').fullmatch('[0-9a-f]{40}',BASE),'human checkpoint finalization required'
    checked=check();assert expected_packet==checked['packet_manifest_sha256'],'reviewed packet digest disagrees'
    assert selection and selection not in ('OWNER_MESSAGE_ID','pending','unselected')
    assert (os.getuid(),os.getgid())==(1000,1000),'selected shared UID:GID required'
    assert not any(k.startswith('GIT_') for k in os.environ),'inherited Git overrides refused'
    safe_root(ROOT);assert not ROOT.exists(),'fresh root required; no retries'
    assert not DEST.exists(),'evidence destination already exists'
    assert shutil.disk_usage(ROOT.parent).free>=8*1024**3,'need 8GiB free disk'
    ROOT.mkdir(mode=0o700)
    for name in ('commands','client-home','docker-config','tmp','manager'): (ROOT/name).mkdir(mode=0o700)
    (ROOT/'docker-config/config.json').write_text('{"auths":{}}\n')
    extract(P/'source.tar',ROOT/'source');extract(P/'context.tar',ROOT/'context')
    shutil.copytree(P,ROOT/'packet')
    run=Commands(ROOT);control=None;receipt=None;failure=None;runtime=None
    def interrupted(signum,frame):raise InterruptedError('Q1 owner-run interrupted; cleanup required')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGALRM,interrupted);signal.alarm(1200)
    save(ROOT/'selection.json',dict(**checked,owner_selection=selection,execution_selected_by_caller=True,network='none for qualification; default for public build dependencies',selected_builds=1,containers=1,provider_calls=0,credentials='synthetic only'))
    try:
        version=run.required(['docker','version','--format','{{json .}}'],seconds=20)
        versions=json.loads(version['stdout']);assert versions.get('Server',{}).get('Version')
        save(ROOT/'engine-version.json',versions)
        absent=run.required(['docker','ps','--all','--filter','label=baton.v12.runtime_attempt_id=q1-386214-offline','--format','{{.ID}}'],seconds=15)
        assert not absent['stdout'].strip(),'pre-existing attempt; no reattach or retry'
        # Classic builder is deliberately selected for effective memory/CPU flags.
        # Unsupported classic builder refuses; no BuildKit fallback or second build.
        run.required(['docker','build','--no-cache','--pull=false','--rm','--force-rm','--network','default','--memory','4g','--cpu-period','100000','--cpu-quota','200000','--iidfile',str(ROOT/'image.id'),'-f',str(ROOT/'context/worker/Dockerfile.codex'),str(ROOT/'context')],seconds=900,cap=16*1024*1024)
        image=(ROOT/'image.id').read_text().strip();assert IMAGE.fullmatch(image)
        inspected=json.loads(run.required(['docker','image','inspect',image])['stdout'])[0]
        assert inspected['Id']==image and inspected['Os']=='linux' and inspected['Architecture']=='amd64'
        assert inspected['Config']['Entrypoint']==['python3','/opt/baton/codex_entry.py']
        identity=json.loads((P/'q1-build.json').read_text());labels=inspected['Config']['Labels']
        assert labels['org.opencontainers.image.revision']==BASE and labels['io.baton.q1.source']==identity['source_manifest_sha256'] and labels['io.baton.q1.packet']=='q1-386214'
        save(ROOT/'image-inspect.json',inspected)
        os.environ['TMPDIR']=str(ROOT/'tmp');os.environ['BATON_V12_DISK_ROOT']=str(ROOT/'tmp')
        sys.path[:0]=[str(ROOT/'source/v12/python/src'),str(ROOT/'source/v12/python'),str(P)]
        import manager_probe
        control,adapter,roots,delivery=manager_probe.prepare(ROOT/'manager',image,run)
        runtime,receipt=manager_probe.start(control,adapter,roots)
        save(ROOT/'launched-image.json',receipt)
        save(ROOT/'digest-kind.json',dict(admitted=image,observed=receipt['observation']['image_id'],resolution=receipt['observation']['resolution'],branch='engine-config-id-equality' if image==receipt['observation']['image_id'] else 'engine-resolution',registry_digest_resolution_qualified=receipt['observation']['resolution'] is not None))
        actual=json.loads(run.required(['docker','inspect','--type','container',runtime])['stdout'])[0]
        assert actual['HostConfig']['NetworkMode']=='none' and actual['Config']['User']=='1000:1000'
        assert actual['HostConfig']['ReadonlyRootfs'] is True
        assert actual['Path']=='python3' and actual['Args'][0]=='/opt/baton/codex_entry.py'
        # Safe image/entrypoint/source/tool report in the same bound container.
        probe=run.required(['docker','exec','--user','1000:1000','--env','HOME=/run/baton/provider-home','--env','CODEX_HOME=/run/baton/provider-home/codex','--env','PYTHONPATH=/opt/baton',runtime,'python3','-c',(P/'worker_probe.py').read_text()],seconds=70,cap=1024*1024)
        observed=json.loads(probe['stdout']);assert observed['identity']==identity
        save(ROOT/'worker-observation.json',observed)
        assert manager_probe.retained(control)==receipt
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    finally:
        signal.alarm(90);run.deadline=time.monotonic()+90
        stopped=cleanup(run,ROOT)
        if control is not None:
            try:
                from baton_v12.worker_manager import ControlStore, attempts
                if runtime is not None and stopped.get('removed') is True:
                    answer=attempts.reconcile_runtime(control,adapter,attempt_id=manager_probe.ATTEMPT)
                    save(ROOT/'manager-after-removal.json',answer)
                    assert attempts.attempt_runtime_of(control,manager_probe.ATTEMPT)['execution_runtime']=='destroyed'
                control.close();control=None
                with ControlStore.open(str(ROOT/'manager/control.sqlite3'),incarnation='q1-after-removal',clock=manager_probe.now) as reopened:
                    retained=manager_probe.retained(reopened)
                    assert retained==receipt
                    save(ROOT/'receipt-after-removal.json',retained)
            except BaseException as exc:failure=(failure or '')+'; receipt reopen: '+type(exc).__name__+': '+str(exc)
        verdict=dict(passed=failure is None and stopped.get('ceased') is True and stopped.get('removed') is True,error=failure,cleanup=stopped,qualification_scope='offline source/image/home/tools/F1 only',provider_calls=0,build_attempts=run.builds,qualification_launch_attempts=run.launches,actual_contributors='unknown',native_job_qualified=False,build_cache_and_image_retained=True,build_cancellation_verified=False if failure and receipt is None else None)
        save(ROOT/'RESULT.json',verdict)
        # Only an explicit allowlist leaves the private execution root. No homes,
        # SQLite, source paths containing future credentials, or Docker config.
        DEST.mkdir(mode=0o700)
        shutil.copytree(ROOT/'commands',DEST/'commands')
        for name in ('selection.json','engine-version.json','image-inspect.json','image.id','launched-image.json','digest-kind.json','worker-observation.json','cleanup.json','receipt-after-removal.json','RESULT.json','container-intent.json','manager-after-removal.json'):
            if (ROOT/name).is_file():shutil.copyfile(ROOT/name,DEST/name)
        save(DEST/'evidence-manifest.json',{str(p.relative_to(DEST)):sha(p.read_bytes()) for p in sorted(DEST.rglob('*')) if p.is_file()})
    signal.alarm(0)
    print(json.dumps(verdict));return 0 if verdict['passed'] else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');parser.add_argument('--execute',action='store_true')
    parser.add_argument('--selection');parser.add_argument('--packet-digest')
    args=parser.parse_args()
    if not args.execute:print(json.dumps(check(),indent=2))
    else:
        if args.check or not args.selection or not args.packet_digest:parser.error('execution requires --selection and --packet-digest, without --check')
        sys.exit(execute(args.selection,args.packet_digest))
