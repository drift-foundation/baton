"""Q4: Codex implementation -> Claude review, offline first. Default is a read-only check.

  --check                       hashes and syntax only (default)
  --offline  (selection A)      one Claude image build, offline inventory, instance, two
                                workers, routing, one empty composition. No credential, no provider.
  --live     (selection B)      one Job: one Codex turn, one Claude review turn. 20-minute bound.

Provisioning uses the product's own bootstrap, pool and job-creation code from the frozen
source; serving is the product's stage-execution composition driven in this process, so the
whole run is bounded and cleaned up here. Completion never means acceptance.
"""
import argparse,ast,contextlib,hashlib,io,json,os,re,signal,sys,time,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
PACKET='q4-386227'
ROOT=Path('/var/tmp/baton-q4-386227')
DEST=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/q4-execution-386227')
BASE='b5abf7983fb07eb3a8268f2d4559a04de9c0f1bd'
SOURCE_TAR=P.parent/'q4-preparation-386225/q2-launcher/source.tar'
SOURCE_TAR_SHA256='62d16e54faeab1678e1ceed5a78ec760c04e8e76c9940e435de435717a5059f7'
CODEX_IMAGE='sha256:2c982530412d6811cfa6aa2e28181f859cc2a9fb2e4372f29d88784763dbe693'
NODE_BASE='node@sha256:f0960f8dc047f358e3fb428f36ccba21732194fa5f0cac849f401e63e62fb9e6'
CODEX=dict(provider='codex',requested_model='gpt-6-astra',reported_identity='gpt-6-astra',cli_build='0.169.0',reference='codex-pushcoin-subscription',slot='codex')
CLAUDE=dict(provider='claude',requested_model='claude-fable-5[1m]',reported_identity='claude-fable-5',cli_build='2.1.247',reference='claude-primary-subscription',slot='claude')
CODEX_LOGIN='/home/sl/.codex-pushcoin/auth.json'      # recorded as text; opened only by the manager in --live
CLAUDE_LOGIN='/home/sl/.claude/.credentials.json'     # recorded as text; opened only by the manager in --live
TEMPLATE='baton.v12.job-template.implementation-review/3'
ROUTING=dict(reviewer='qualification.claude',decision_recipient='baton.slaw')
TURN_SECONDS=600;VERIFY_SECONDS=15;LIVE_SECONDS=1200;OFFLINE_SECONDS=1500;CLEANUP_SECONDS=150
VERIFICATION=['python3','-I','-c',"from pathlib import Path; assert Path('message.txt').read_bytes()==b'after'+bytes([10])"]
STATEMENT='Change only message.txt from exactly before followed by a newline to exactly after followed by a newline. Do not change any other file. Do not commit.'
IMAGE_FILES=['python/src/baton_v12/attempt_log_format.py','python/src/baton_v12/verification_context.py','worker/baton_worker.py','worker/adapter_refusal.py','worker/claude_agent.py','worker/bounded_command.py','worker/dogfood_entry.py','worker/worker-control-1.0.schema.json','worker/verifier-layout-marker.json']
IMAGE_TREES=['source_profiles','provider_policy']
HASHER="import hashlib,json,os;print(json.dumps({os.path.join(d,f):hashlib.sha256(open(os.path.join(d,f),'rb').read()).hexdigest() for d,_,fs in os.walk('/opt/baton') if '__pycache__' not in d for f in fs},sort_keys=True))"
sys.path.insert(0,str(P))
from runner import Commands,cleanup_all,extract,safe_root,sha,save

def now():
    from datetime import datetime,timezone
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')

def check():
    if not __debug__:raise RuntimeError('optimized Python refused')
    files=json.loads((P/'payload.json').read_text())
    for name,digest in files.items():
        assert Path(name).name==name and not (P/name).is_symlink()
        assert sha((P/name).read_bytes())==digest,name
    for name in files:
        if name.endswith('.py'):ast.parse((P/name).read_text())
    assert not SOURCE_TAR.is_symlink() and sha(SOURCE_TAR.read_bytes())==SOURCE_TAR_SHA256,'frozen source archive differs'
    return dict(packet=PACKET,payload_sha256=sha((P/'payload.json').read_bytes()),source=BASE,source_tar_sha256=SOURCE_TAR_SHA256,codex_image=CODEX_IMAGE,read_only=True,engine_operations=0,credential_access=False)

def expected_image_files(source):
    v12=Path(source)/'v12';answer={}
    for rel in IMAGE_FILES:answer['/opt/baton/'+Path(rel).name]=sha((v12/rel).read_bytes())
    for tree in IMAGE_TREES:
        for path in sorted((v12/'python/src/baton_v12'/tree).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:answer['/opt/baton/'+tree+'/'+str(path.relative_to(v12/'python/src/baton_v12'/tree))]=sha(path.read_bytes())
    return answer

def guard(selection,packet):
    before=check();assert packet==before['payload_sha256'],'reviewed packet digest disagrees'
    assert selection and selection not in ('OWNER_MESSAGE_ID','pending','unselected','Q4_OFFLINE_SELECTION','Q4_LIVE_SELECTION')
    assert (os.getuid(),os.getgid())==(1000,1000),'selected shared UID:GID required'
    assert not any(k.startswith('GIT_') for k in os.environ),'inherited Git overrides refused'
    safe_root(ROOT);os.umask(0o077)
    return before

def source_path():
    os.environ.update(HOME=str(ROOT/'client-home'),TMPDIR=str(ROOT/'tmp'),BATON_V12_DISK_ROOT=str(ROOT/'tmp'),PYTHONDONTWRITEBYTECODE='1')
    for one in (str(ROOT/'source/v12/python'),str(ROOT/'source/v12/python/src')):
        if one not in sys.path:sys.path.insert(0,one)

def said(call,argv,log):
    """One product command run in this process; its text is retained, its status returned."""
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        try:status=call(argv,stream=stream) if 'stream' in __import__('inspect').signature(call).parameters else call(argv)
        except SystemExit as ended:status=ended.code
    Path(log).write_text(stream.getvalue())
    assert status in (0,None),(Path(log).name,status,stream.getvalue()[-600:])
    return stream.getvalue()

def interrupted(signum,frame):raise InterruptedError('selected Q4 deadline or signal')

# ---------------------------------------------------------------- selection A

def offline(selection,packet):
    before=guard(selection,packet)
    assert not ROOT.exists() and not DEST.exists(),'fresh private root and evidence destination required; no retries'
    assert shutil.disk_usage(ROOT.parent).free>=8*1024**3
    ROOT.mkdir(mode=0o700)
    for name in ('commands','client-home','docker-config','tmp','prep','prep/workers'):(ROOT/name).mkdir(mode=0o700)
    (ROOT/'docker-config/config.json').write_text('{"auths":{}}\n')
    run=Commands(ROOT,inventory_runs=3,builds=1,seconds=OFFLINE_SECONDS)
    for sig in (signal.SIGTERM,signal.SIGALRM,signal.SIGHUP):signal.signal(sig,interrupted)
    signal.alarm(OFFLINE_SECONDS);failure=None;facts=dict(image=None);ops=job=control=None
    try:
        extract(SOURCE_TAR,ROOT/'source');source_path()
        save(ROOT/'selection.json',dict(owner_selection=selection,phase='offline',payload_sha256=packet,source=BASE))
        save(ROOT/'engine-version.json',json.loads(run.required(['docker','version','--format','{{json .}}'],seconds=20)['stdout']))
        # 1. The accepted Codex image is present and is the reviewed one.
        codex=json.loads(run.required(['docker','image','inspect',CODEX_IMAGE],seconds=20)['stdout'])[0]
        assert codex['Id']==CODEX_IMAGE and codex['Config']['Entrypoint']==['python3','/opt/baton/codex_entry.py'] and codex['Config']['Labels'].get('org.opencontainers.image.revision')==BASE
        # 2. One Claude image, from the frozen source, base pinned by digest.
        context=ROOT/'claude-context';v12=ROOT/'source/v12'
        for rel in IMAGE_FILES:
            (context/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(v12/rel,context/rel)
        for tree in IMAGE_TREES:shutil.copytree(v12/'python/src/baton_v12'/tree,context/'python/src/baton_v12'/tree,ignore=shutil.ignore_patterns('__pycache__'))
        recipe=(v12/'worker/Dockerfile.claude').read_text();assert recipe.count('FROM node:22-trixie-slim')==1
        recipe=recipe.replace('FROM node:22-trixie-slim','FROM '+NODE_BASE);(context/'worker/Dockerfile.claude').write_text(recipe)
        labels={'org.opencontainers.image.revision':BASE,'io.baton.q4.packet':PACKET,'io.baton.q4.recipe':sha(recipe.encode())}
        build=['docker','build','--no-cache','--pull=false','--rm','--force-rm','--network','default','--memory','4g','--cpu-period','100000','--cpu-quota','200000','--iidfile',str(ROOT/'claude-image.id')]
        for key,value in sorted(labels.items()):build+=['--label',key+'='+value]
        run.required(build+['-f',str(context/'worker/Dockerfile.claude'),str(context)],seconds=900,cap=16*1024*1024)
        image=(ROOT/'claude-image.id').read_text().strip();assert re.fullmatch('sha256:[0-9a-f]{64}',image) and image!=CODEX_IMAGE
        facts['image']=image
        inspected=json.loads(run.required(['docker','image','inspect',image],seconds=20)['stdout'])[0]
        assert inspected['Id']==image and inspected['Config']['Entrypoint']==['python3','/opt/baton/dogfood_entry.py']
        assert all(inspected['Config']['Labels'].get(k)==v for k,v in labels.items());save(ROOT/'claude-image.json',inspected)
        # 3. Offline inventory: network none, no mounts, no credential, removed on exit.
        def inventory(index,entry,*tail):
            return run.required(['docker','run','--rm','--name',PACKET+'-inventory-'+str(index),'--label','io.baton.q4.inventory='+PACKET,'--network','none','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=16m','-e','HOME=/tmp','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--entrypoint',entry,image,*tail],seconds=60,cap=1024*1024)['stdout']
        version=inventory(1,'claude','--version');helped=inventory(2,'claude','--help');observed=json.loads(inventory(3,'python3','-I','-c',HASHER))
        expected=expected_image_files(ROOT/'source')
        facts.update(cli_version=version.strip(),help_flags={flag:flag in helped for flag in ('--print','--output-format','--model','--dangerously-skip-permissions')},image_files=len(observed),image_files_equal_source=observed==expected,
            image_file_differences=sorted(k for k in set(observed)|set(expected) if observed.get(k)!=expected.get(k))[:20])
        assert re.match(r'2\.1\.247\b',version.strip()),'Claude CLI is not exactly 2.1.247'
        assert all(facts['help_flags'].values()),'Claude help lacks a flag the adapter passes'
        assert observed==expected,'image files differ from the frozen source'
        left=run.required(['docker','ps','--all','--filter','label=io.baton.q4.inventory='+PACKET,'--format','{{.ID}}'],seconds=15)['stdout'].strip()
        assert not left,'an inventory container remains'
        # 4. Disposable fixture repository; the only Git this packet mutates.
        fixture=ROOT/'fixture';(fixture/'record').mkdir(parents=True,mode=0o700)
        (fixture/'message.txt').write_bytes(b'before\n')
        (fixture/'record/FINDING.md').write_text('# Q4 qualification record\n\n'+STATEMENT+'\n')
        (fixture/'record/PLAN.md').write_text('# Plan\n\nOne Codex implementation turn, one Claude review turn. No integration.\n')
        for args in (['init','--initial-branch=q4'],['config','user.name','Q4 qualification'],['config','user.email','q4@invalid'],['add','--all'],['commit','-m','Q4 disposable baseline']):
            run.required(['git','-C',str(fixture),*args],seconds=15)
        base=run.required(['git','-C',str(fixture),'rev-parse','HEAD'],seconds=15)['stdout'].strip();facts['fixture_base']=base
        # 5. Private registry for this run only: references and paths, never contents.
        import registry
        facts['registry']=registry.add(ROOT/'credential-sources.json',[('operator-file',CODEX['reference'],CODEX_LOGIN),('operator-file',CLAUDE['reference'],CLAUDE_LOGIN)])
        # 6. Instance, with the installer's own steps (no runtime bundle is built or needed).
        from tools import bootstrap,instance,pool
        inst=ROOT/'instance';places=instance.layout(str(inst))
        document=dict(schema='baton.v12.stack-bootstrap/1',checkpoint_profile='git',
            integration_profile=dict(profile_kind='git',profile_version=1,integrator_participant='qualification.integrator',instructions_digest='sha256:'+'0'*64),
            retention_policy_digest='sha256:'+sha(b'q4 retain-private'),retention_disposition='retain',pool_generation=1,policy_generation=1,
            receipt_participants=dict(verification='qualification.verifier',review='qualification.review-receipt',approval='qualification.approver'),
            line_declared_base=base,canonical_target_id='q4-target',state_root=places['destination'])
        text=io.StringIO()
        with contextlib.redirect_stdout(text):
            bootstrap._routing_preflight(document);source=bootstrap.repository_source(str(fixture))
            document=bootstrap.workspace_bound(document,places);document=bootstrap.repositories_bound(document,places,True);document=bootstrap.storage_bound(document,places,True)
            bootstrap.prepare_repositories(document,places,source=source,stream=text);prepared=bootstrap.prepare(document,installing=True,stream=text)
        (ROOT/'prep/install.log').write_text(text.getvalue());save(ROOT/'prep/install-document.json',document)
        task=dict(schema='baton.dogfood-task/2',task_id='q4-edit',instructions=STATEMENT,source_root='source',source_profile='git-line',declared_base=base,verification=VERIFICATION)
        (ROOT/'prep/task.json').write_text(json.dumps(task,sort_keys=True))
        marker=ROOT/'source/v12/worker/verifier-layout-marker.json'
        def compose(worker_id,role,participant,image_digest,selected):
            into=ROOT/'prep/workers'/(worker_id+'.json')
            said(pool.main,['compose-worker','--deployment',str(inst/'deployment.json'),'--worker-id',worker_id,'--role',role,'--participant',participant,'--image-reference',image_digest,'--image-digest',image_digest,
                '--cli-build',selected['cli_build'],'--provider',selected['provider'],'--requested-model',selected['requested_model'],'--reported-identity',selected['reported_identity'],'--network','bridge',
                '--credential-sources',str(ROOT/'credential-sources.json'),'--credential',selected['slot']+'=operator-file:'+selected['reference'],'--workspace-group','1000','--task-document',str(ROOT/'prep/task.json'),
                '--record','record','--checkout',str(fixture),'--template',TEMPLATE,'--verifier-layout',str(marker),'--into',str(into)],ROOT/'prep'/('compose-'+worker_id+'.log'))
            return json.loads(into.read_text())
        implementer=compose('impl-codex','implementation','qualification.codex',CODEX_IMAGE,CODEX)
        reviewer=compose('review-claude','review',ROUTING['reviewer'],image,CLAUDE)
        # Two images mean two verifier-layout selections, and one launch home holds exactly one.
        # The review worker therefore gets its own launch home; nothing else in its document changes.
        reviewer['deployment']['launch_home']=reviewer['deployment']['launch_home']+'-review-claude'
        assert implementer['deployment']['launch_home']!=reviewer['deployment']['launch_home']
        assert reviewer['deployment']['provider_contract']['selection']=={k:CLAUDE[k] for k in ('provider','requested_model','reported_identity','cli_build')}
        assert reviewer['deployment']['provider_contract']['adapter']['credential']['mode']=='delivered' and implementer['deployment']['provider_contract']['adapter']['credential']['mode']=='seeded-retained'
        assert reviewer['deployment']['network']==implementer['deployment']['network']=='bridge'
        updated=dict(document,workers=[implementer,reviewer],native_handoff_routing=ROUTING);save(ROOT/'prep/updated-inputs.json',updated)
        said(bootstrap.main,['--inputs',str(ROOT/'prep/updated-inputs.json'),'--repository-source',str(fixture)],ROOT/'prep/bootstrap-repeat.log')
        configuration=json.loads((inst/'deployment.json').read_text())
        assert sorted(one['role'] for one in configuration['workers'])==['implementation','review']
        # 7. One empty composition: sessions, profiles, pool, control store. No Job, no container.
        from baton_v12.authority import Authority
        from baton_v12.job_manager import JobStore,reconcile,status
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution
        launches=run.workers+run.inventories
        os.environ[stage_execution.CONFIG_ENV]=str(inst/'deployment.json');held=stage_execution._configuration()
        job=JobStore.open(str(inst/'db/jobs.sqlite3'),authority_uuid=configuration['authority_uuid'],incarnation='q4-offline',clock=now)
        control=ControlStore.open(str(inst/'db/control.sqlite3'),incarnation='q4-offline',clock=now)
        ops=stage_execution.operations_from(held,job,control,engine_run=run,lifetime_policy=stage_execution.native_lifetime_policy(held))
        reconcile(job,ops,now=now());idle=status(job,ops,observed_at=now())
        authority=Authority.open(str(inst/'db/authority.sqlite3'),expected_authority_uuid=configuration['authority_uuid'])
        try:routing=authority.native_routing()
        finally:authority.dispose()
        assert idle['jobs']==[] and run.workers+run.inventories==launches and routing is not None and (routing['reviewer'],routing['decision_recipient'])==(ROUTING['reviewer'],ROUTING['decision_recipient'])
        facts.update(authority_uuid=configuration['authority_uuid'],workers=sorted(one['worker_id'] for one in configuration['workers']),routing=ROUTING,idle_jobs=0,worker_containers=0,
            review_selection=reviewer['deployment']['provider_contract']['selection'],implementation_selection=implementer['deployment']['provider_contract']['selection'],
            deployment_sha256=sha((inst/'deployment.json').read_bytes()),separate_launch_homes=True)
    except BaseException as exc:
        failure=type(exc).__name__;save(ROOT/'private-error.json',dict(type=failure,diagnostic=str(exc)))
    finally:
        signal.alarm(CLEANUP_SECONDS)
        for one in (ops,control,job):
            try:
                if one is not None:one.close()
            except BaseException as exc:failure=failure or type(exc).__name__
        stopped=cleanup_all(run,ROOT,CLEANUP_SECONDS)
        verdict=dict(packet=PACKET,phase='offline',payload_sha256=packet,source=BASE,codex_image=CODEX_IMAGE,claude_image=facts.pop('image'),passed=failure is None and stopped['ceased'] and stopped['removed'],error_type=failure,
            builds=run.built,inventory_runs=run.inventories,provider_calls=0,credential_reads=0,ceased=stopped['ceased'],removed=stopped['removed'],private_root=str(ROOT),image_and_build_cache_retained=True,**facts)
        save(ROOT/'OFFLINE-RESULT.json',verdict)
        if not DEST.exists():
            DEST.mkdir(mode=0o700);save(DEST/'OFFLINE-RESULT.json',verdict)
        signal.alarm(0)
    print(json.dumps(verdict));return 0 if verdict['passed'] else 1

# ---------------------------------------------------------------- selection B

def live(selection,packet,offline_sha256):
    guard(selection,packet)
    proved=(ROOT/'OFFLINE-RESULT.json').read_bytes();assert sha(proved)==offline_sha256,'reviewed offline result differs'
    earlier=json.loads(proved);assert earlier['passed'] is True and earlier['packet']==PACKET and earlier['payload_sha256']==packet
    assert not (ROOT/'RESULT.json').exists() and not (DEST/'RESULT.json').exists() and not (ROOT/'live').exists(),'one live run only; no retries'
    image=earlier['claude_image'];inst=ROOT/'instance';out=ROOT/'live';out.mkdir(mode=0o700);(out/'commands').mkdir(mode=0o700)
    run=Commands(ROOT,worker_images=[CODEX_IMAGE,image],seconds=LIVE_SECONDS);run.root=out;run.env=dict(run.env,HOME=str(ROOT/'client-home'),DOCKER_CONFIG=str(ROOT/'docker-config'),TMPDIR=str(ROOT/'tmp'))
    for sig in (signal.SIGTERM,signal.SIGALRM,signal.SIGHUP):signal.signal(sig,interrupted)
    signal.alarm(LIVE_SECONDS);started=time.monotonic()
    failure=None;outcome='not-reached';ops=job=control=None;stages={};conclusions=[];completion={};items=[];configuration=None;inspected={}
    try:
        source_path()
        save(out/'selection.json',dict(owner_selection=selection,phase='live',payload_sha256=packet,offline_result_sha256=offline_sha256,codex=CODEX,claude=CLAUDE,turn_seconds=TURN_SECONDS,verification_seconds=VERIFY_SECONDS,overall_seconds=LIVE_SECONDS,network='bridge',retries=0,source_writeback=False))
        # Before any provider turn: both login sources are private ordinary files within the manager's
        # own bounds. Metadata only; the manager alone opens them, at delivery.
        for place,limit in ((CODEX_LOGIN,1048576),(CLAUDE_LOGIN,4096)):
            info=os.lstat(place);assert __import__('stat').S_ISREG(info.st_mode) and info.st_uid==os.getuid() and not info.st_mode&0o077 and 0<info.st_size<=limit,'a login source is not a private ordinary file within its delivery bound'
        for wanted in (CODEX_IMAGE,image):assert json.loads(run.required(['docker','image','inspect',wanted],seconds=20)['stdout'])[0]['Id']==wanted
        from baton_v12.job_manager import JobStore,reconcile,review_uncertainty,status,sweep
        from baton_v12.worker_manager import ControlStore,frozen_output_of,load_manifest
        from tools import job_manager,stage_execution
        import observe
        configuration=json.loads((inst/'deployment.json').read_text());uuid=configuration['authority_uuid']
        assert sha((inst/'deployment.json').read_bytes())==earlier['deployment_sha256'],'instance configuration changed since the reviewed offline run'
        created=said(job_manager.main,['--store',str(inst/'db/jobs.sqlite3'),'--incarnation','q4-create','--authority-uuid',uuid,'create','--template',TEMPLATE,'--instance',str(inst),'--control',str(inst/'db/control.sqlite3'),'--authority',str(inst/'db/authority.sqlite3'),
            '--task','q4-codex-claude','--statement',STATEMENT,'--acceptance','only message.txt changes, to exactly after followed by a newline','--work-scope','message.txt',
            '--provider-turn-seconds',str(TURN_SECONDS),'--verification-command-seconds',str(VERIFY_SECONDS),*[('--verification='+word) for word in VERIFICATION]],out/'create.log')
        made=json.loads(created[created.rindex('\n{\n')+1:]);job_id=made['binding']['job_id'];work=made['binding']['job_work_id']
        assert made['stages']==[job_id+'/implementation',job_id+'/review'],'the Job is not exactly implementation then review'
        os.environ[stage_execution.CONFIG_ENV]=str(inst/'deployment.json');held=stage_execution._configuration()
        job=JobStore.open(str(inst/'db/jobs.sqlite3'),authority_uuid=uuid,incarnation='q4-live',clock=now)
        control=ControlStore.open(str(inst/'db/control.sqlite3'),incarnation='q4-live',clock=now)
        ops=stage_execution.operations_from(held,job,control,engine_run=run,lifetime_policy=stage_execution.native_lifetime_policy(held))
        reclaim=getattr(ops,'reclaim',None) or job_manager._reclaiming(control,'docker',run,None)
        expected_image={'implementation':CODEX_IMAGE,'review':image}
        def custody(kind,stage,required):
            attempt=stage.get('attempt_id')
            return observe.completed_custody(stage,frozen_output_of(control,attempt),load_manifest(control,frozen_output_of(control,attempt)['manifest_digest'],'resultManifest'),attempt=attempt,stage_id=job_id+'/'+kind,work_id=work,authority_uuid=uuid,custody_root=inst/'state/workspaces',required=required)
        report=reconcile(job,ops,now=now());deadline=started+LIVE_SECONDS-30;outcome='wall-bound'
        while time.monotonic()<deadline:
            for one in report.get('spoken') or []:
                if one.get('act')=='conclude':conclusions.append(one);save(out/'conclusions.json',conclusions)
            state=status(job,ops,observed_at=now());save(out/'status.json',state)
            stages={one['kind']:one for one in state['jobs'][0]['stages']}
            # Bind each launched container to its role's pinned image while it still exists.
            for index,one in enumerate(run.containers):
                if index in inspected:continue
                seen=run(['docker','inspect','--type','container',one['name']],seconds=15)
                if seen['status']==0:
                    doc=json.loads(seen['stdout'])[0];kind=('implementation','review')[index]
                    assert doc['Image']==expected_image[kind] and doc['Config']['User']=='1000:1000' and doc['HostConfig']['NetworkMode']=='bridge' and doc['HostConfig']['ReadonlyRootfs'] is True,'container posture differs from the selection'
                    save(out/('container-inspect-'+kind+'.json'),doc);inspected[index]=kind
            implementation,review=stages['implementation'],stages['review']
            if implementation['state']=='completed' and 'implementation' not in completion:
                completion['implementation']=custody('implementation',implementation,'proposal');save(out/'completion.json',completion)
            items=review_uncertainty.items_of(job)
            if implementation['state'] in observe.ENDED_WITHOUT_RESULT:outcome='implementation-ended-without-result';break
            if review['state']=='completed':
                completion['review']=custody('review',review,'findings');save(out/'completion.json',completion);outcome='review-verdict-recorded';break
            if items:outcome='review-uncertain-owner-item';break
            if any(one['stage_id']==job_id+'/review' and (one.get('detail') or {}).get('outcome')=='held' for one in conclusions):outcome='review-held';break
            if review['state'] in observe.ENDED_WITHOUT_RESULT and implementation['state']=='completed':outcome='review-ended-without-result';break
            time.sleep(1)
            report=sweep(job,ops,now=now());reclaimed=reclaim(now=now())
            if reclaimed:save(out/'reclaimed.json',reclaimed)
        save(out/'owner-items.json',items)
    except BaseException as exc:
        failure=type(exc).__name__;save(out/'private-error.json',dict(type=failure,diagnostic=str(exc)));outcome='error' if outcome in ('not-reached','wall-bound') else outcome
    finally:
        signal.alarm(CLEANUP_SECONDS);elapsed=time.monotonic()-started
        for one in (ops,control,job):
            try:
                if one is not None:one.close()
            except BaseException as exc:failure=failure or type(exc).__name__
        stopped=cleanup_all(run,out,CLEANUP_SECONDS)
        withdrawn=None;edit=dict(edit_verified=False,changed_paths=None)
        try:
            if configuration and stopped['removed']:
                from baton_v12.worker_manager.credentials import CredentialHome
                attempts=[one.get('attempt_id') for one in stages.values() if one.get('attempt_id')];homes={one['deployment']['credential_home'] for one in configuration['workers']}
                for home in sorted(homes):
                    for attempt in attempts:
                        try:CredentialHome(home).tear_down_orphan(attempt)
                        except BaseException as exc:save(out/'credential-withdrawal-error.json',dict(type=type(exc).__name__,diagnostic=str(exc)))
                withdrawn=all(not Path(CredentialHome(home).volatile_root(attempt)).exists() for home in homes for attempt in attempts)
            # Trusted post-cessation comparison of the reviewed line; no candidate code is executed.
            lines=sorted((inst/'state/workspaces/.baton-review-lines').glob('line-*/checkout')) if stopped['removed'] else []
            if len(lines)==1 and not lines[0].is_symlink():
                base=earlier['fixture_base'];names=run.required(['git','-C',str(lines[0]),'diff','--name-only',base,'HEAD'],seconds=15)['stdout'].split()
                dirty=run.required(['git','-C',str(lines[0]),'status','--porcelain'],seconds=15)['stdout'].strip()
                body=(lines[0]/'message.txt').read_bytes() if (lines[0]/'message.txt').is_file() and not (lines[0]/'message.txt').is_symlink() else None
                edit=dict(edit_verified=names==['message.txt'] and body==b'after\n' and not dirty,changed_paths=names)
        except BaseException as exc:failure=failure or type(exc).__name__;save(out/'capture-error.json',dict(type=type(exc).__name__,diagnostic=str(exc)))
        def attribution(kind):
            return ((stages.get(kind) or {}).get('runtime') or {}).get('model_attribution') or ''
        verdicts=[(one.get('detail') or {}).get('verdict') for one in conclusions if one.get('stage_id','').endswith('/review')]
        verdict=dict(packet=PACKET,phase='live',payload_sha256=packet,source=BASE,codex_image=CODEX_IMAGE,claude_image=image,outcome=outcome,error_type=failure,elapsed_seconds=round(elapsed,1),overall_bound_seconds=LIVE_SECONDS,
            implementation_state=(stages.get('implementation') or {}).get('state'),review_state=(stages.get('review') or {}).get('state'),
            implementation_completion=(completion.get('implementation') or {}).get('kind'),review_completion=(completion.get('review') or {}).get('kind'),
            review_verdict_recorded=next((v for v in verdicts if v),None),owner_items=len(items),owner_item_destinations=sorted({one.get('destination') for one in items}),
            codex_configured_model_accepted='attribution: configured-model-accepted' in attribution('implementation'),claude_attribution_matched='attribution: matched' in attribution('review'),
            claude_requested_model_reported='Requested model reported: yes' in attribution('review'),containers_inspected=sorted(inspected.values()),
            worker_containers=run.workers,ceased=stopped['ceased'],removed=stopped['removed'],volatile_credentials_withdrawn=withdrawn,retained_homes_preserved=True,source_writeback=False,
            actual_codex_contributors='unknown',acceptance='held-for-private-evidence-review',native_job_success=False,private_root=str(ROOT),**edit)
        save(ROOT/'RESULT.json',verdict)
        if DEST.is_dir() and not (DEST/'RESULT.json').exists():save(DEST/'RESULT.json',verdict)
        signal.alarm(0)
    print(json.dumps(verdict))
    return 0 if failure is None and verdict['ceased'] and verdict['removed'] and outcome in ('review-verdict-recorded','review-uncertain-owner-item','review-held') else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('--check','--offline','--live'):parser.add_argument(name,action='store_true')
    parser.add_argument('--selection');parser.add_argument('--packet');parser.add_argument('--offline-result-sha256')
    args=parser.parse_args()
    if args.offline and args.live:parser.error('one phase per invocation')
    if args.offline:
        if not args.selection or not args.packet:parser.error('the offline phase needs an owner selection and the reviewed packet digest')
        sys.exit(offline(args.selection,args.packet))
    if args.live:
        if not args.selection or not args.packet or not args.offline_result_sha256:parser.error('the live phase needs an owner selection, the reviewed packet digest and the reviewed offline result digest')
        sys.exit(live(args.selection,args.packet,args.offline_result_sha256))
    print(json.dumps(check(),indent=2))
