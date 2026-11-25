"""One real local qualification Authority, Job, manager and exchange. No live v11 store."""
import json,os
from pathlib import Path
from datetime import datetime,timezone
UUID='386214aa000000000000000000000001'
WORK='386214aa-W1'
WHO='qualification.codex'
JOB='q2-386214'
IMAGE=None # Set only by validated, separately reviewed rebuilt-image evidence.
SELECTED=dict(provider='codex',requested_model='gpt-6-astra',reported_identity='gpt-6-astra',cli_build='0.169.0')
def now():return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def compose(root,source_login,run):
    assert isinstance(IMAGE,str) and IMAGE.startswith('sha256:'),'reviewed rebuilt image required'
    from baton_v12.authority import Authority
    from baton_v12 import provider_policy as policy
    from baton_v12.contracts import digest,job_input_identity
    from baton_v12.job_manager import JobStore,submit
    from baton_v12.worker_manager import ControlStore,source_boundary
    from tools import single_worker as sw,next_run_bindings as bindings
    root=Path(root);source=root/'fixture';source.mkdir(mode=0o700)
    (source/'message.txt').write_bytes(b'before\n')
    # Only this fresh, canonical, private directory is mutated by Git.
    for args in (['init','--initial-branch=q2'],['config','user.name','Q2 qualification'],['config','user.email','q2@invalid'],['add','message.txt'],['commit','-m','Q2 disposable baseline']):
        run.required(['git','-C',str(source),*args],seconds=15)
    base=run.required(['git','-C',str(source),'rev-parse','HEAD'],seconds=15)['stdout'].strip()
    authority=Authority.create(str(root/'authority.sqlite3'),authority_uuid=UUID,clock=now)
    authority.create_work(WORK,'qualification.impl',contract='v12-assignment-1',operation_id='q2-create')
    authority.add_route_handler('qualification.impl',WHO)
    ids=bindings.deployment_identities(image_reference=IMAGE,image_digest=IMAGE,cli_build='0.169.0',provider_network='bridge',runtime_uid=1000,turn_seconds=180,verification_seconds=15,implementer_invocations=1,contextual=False,provider_selection=SELECTED)
    instructions='Change only message.txt from exactly before followed by a newline to exactly after followed by a newline. Do not change any other file. Do not make network requests or inspect credentials. Run the stated verification, then finish. Do not commit.'
    verification=['python3','-I','-c',"from pathlib import Path; assert Path('message.txt').read_bytes()==b'after\\n'"]
    task=dict(schema='baton.dogfood-task/2',task_id='q2-edit',instructions=instructions,source_root='source',source_profile='generic',declared_base=None,verification=verification)
    raw=json.dumps(task,sort_keys=True).encode();(root/'task.json').write_bytes(raw)
    manifest=bindings.input_manifest(None,authority_uuid=UUID,work_id=WORK,policy_digest=ids['policy_digest'],profile_digest=ids['profile_digest'],image_digest=IMAGE,task_bytes=raw,artifact_id='q2-edit',contextual=False)
    manifest['sources'][0]['consumption']=source_boundary.source_consumption('generic')
    manifest['tool_policy_digest']=digest(policy.POLICY);manifest.pop('manifest_digest');manifest['manifest_digest']=digest(manifest)
    registry=root/'credential-sources.json'
    save(registry,dict(schema='baton.user-credential-sources/1',sources=[dict(provider='operator-file',reference='codex-pushcoin-subscription',path=str(source_login))]));registry.chmod(0o600)
    storage=root/'workspaces';storage.mkdir(mode=0o700)
    config=dict(schema=sw.PROVIDER_CONFIG_SCHEMA,authority_store=str(root/'authority.sqlite3'),authority_uuid=UUID,participant=WHO,principal=authority.principal_of(WHO),profile_name='q2-codex',profile_digest=ids['profile_digest'],policy_digest=ids['policy_digest'],adapter_name='docker-single-worker',adapter_digest=ids['adapter_digest'],engine='docker',image_digest=IMAGE,network='bridge',workspace_storage=str(storage),workspace_group=1000,launch_home=str(root/'launch'),credential_home=str(root/'credentials'),credential_sources=str(registry),credential_slots=['codex'],credential_profile={'codex':dict(provider='operator-file',reference='codex-pushcoin-subscription')},nominated_source=str(source),workspace_capacity=dict(max_bytes=source_boundary.MIN_WORKSPACE_BYTES+1),input_manifest=manifest,task_document=str(root/'task.json'),launch_contract='v12-assignment-1',launch_role='implementation',review_route='qualification.review-held',retention_policy_digest=digest(dict(q2='retain-private')),retention_disposition='retain',provider_context=None,verifier_layout=None,provider_contract=dict(selection=SELECTED,adapter=ids['adapter'],runtime_profile=ids['runtime_profile']),provider_home_root=str(root/'job-work'))
    given=sw._held(config)
    job=JobStore.open(str(root/'jobs.sqlite3'),authority_uuid=UUID,incarnation='q2-owner',clock=now)
    control=ControlStore.open(str(root/'control.sqlite3'),incarnation='q2-owner',clock=now)
    provider=sw.worker_preflight(given,control,engine_run=run)
    ops=sw.worker_operations(given,control,authority,provider,engine_run=run,clock=now,dispose=authority.dispose,execution_context=sw.job_execution_reader(job),job_task=sw.job_task_reader(job),worker_id='q2-codex')
    document=dict(schema='baton.v12.job-submission/2',submission_id='q2-386214',jobs=[dict(job_id=JOB,input_digest=job_input_identity(manifest),policy_digest=ids['policy_digest'],test_scope=['message.txt'],terminal_policy='report-and-hold',execution_limits=dict(provider_turn_seconds=180,verification_command_seconds=15),stages=[dict(kind='implementation',work_id=WORK,profile_name='q2-codex',profile_digest=ids['profile_digest'],depends_on=[])])])
    submit(job,document)
    save(root/'deployment.json',config);save(root/'submission.json',document)
    return job,control,ops,config

def drive(job,control,ops):
    from baton_v12.job_manager import reconcile,status
    reconcile(job,ops,now=now())
    return status(job,ops,observed_at=now())

def receipt(control,attempt):
    from baton_v12.worker_manager import image_receipts,model_attribution
    value,cause=image_receipts.evidence(control,attempt,model_attribution.selection_of(control,attempt))
    return dict(receipt=value,cause=cause)
