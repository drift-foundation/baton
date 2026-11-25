"""Q1 harness: synthetic Authority assignment, real manager/OCI owners.

No Job command or provider turn is sent. The production image entry waits on
its framed channel; one explicit offline exec runs only worker_probe.py.
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

ATTEMPT='q1-386214-offline'
JOB='q1-386214-synthetic-job'
WHO='qualification.offline'
WORK={'authority_uuid':'43c55d4b1234567890abcdef12345678','work_id':'43c55d4b-W1'}
def now(): return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def save(path,value): Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def prepare(root, image, run):
    from baton_v12 import provider_policy as policy
    from baton_v12.contracts import digest
    from baton_v12.worker_manager import ControlStore, AuthorityPort, certify_profile, issue_offer, accept_offer, submit_claim, activate_assignment, record_attempt, configure_workspace_group, configured_workspace_group
    from baton_v12.worker_manager import workspaces, launch, provider_home, model_attribution, attempts
    from baton_v12.worker_manager.oci import OciAdapter, EnginePort
    from baton_v12.job_manager import execution_limits
    from tools.next_run_bindings import deployment_identities
    from tests.manager import input_roots, test_offers
    root=Path(root)
    selected=dict(provider='codex',requested_model='gpt-6-astra',reported_identity='gpt-6-astra',cli_build='0.169.0')
    ids=deployment_identities(image_reference='q1-local-built-image',image_digest=image,cli_build='0.169.0',provider_network='none',runtime_uid=1000,turn_seconds=30,verification_seconds=30,implementer_invocations=1,contextual=False,provider_selection=selected)
    contract=dict(selection=selected,adapter=ids['adapter'],runtime_profile=ids['runtime_profile'])
    policy_digest=digest(policy.POLICY)
    control=ControlStore.open(str(root/'control.sqlite3'),incarnation='q1-offline',clock=now)
    configure_workspace_group(control,1000);group=configured_workspace_group(control)
    storage=root/'workspace-storage';storage.mkdir(mode=0o700)
    workspaces.configure_workspace_storage(control,str(storage))
    certify_profile(control,'runtime','q1-offline',ids['profile_digest'])
    live=dict(work_ref=WORK,participant=WHO,generation=1)
    session=test_offers.FakeSession(participant=WHO)
    session._work=dict(status='open',phase='queued',handler=None,gate=None,authority_uuid=WORK['authority_uuid'],scope=test_offers.SCOPE,route=test_offers.ROUTE)
    session.claim_answer=dict(assignment=live,claim_event=1,decision=test_offers.decision(participant=WHO))
    session.live_assignment=live
    port=AuthorityPort(session,test_offers.fake_claim_signature)
    given,assignment=input_roots.documents(work_ref=WORK,participant=WHO,generation=1,runtime_attempt_id=ATTEMPT,policy_digest=policy_digest,profile_digest=ids['profile_digest'])
    stamp=now()
    issue_offer(control,port,offer_id='q1-offer',work_id=WORK['work_id'],runtime_attempt_id=ATTEMPT,input_digest=given['manifest_digest'],policy_digest=policy_digest,profile_digest=ids['profile_digest'],profile_name='q1-offline',mint_bearer=lambda:'q1-synthetic-offer-bearer')
    accept_offer(control,port,offer_id='q1-offer',decision='accept',bearer='q1-synthetic-offer-bearer',now=stamp,runtime_attempt_id=ATTEMPT,work_ref=WORK)
    record_attempt(control,attempt_id=ATTEMPT,adapter_name='docker',adapter_digest=ids['adapter_digest'],profile_digest=ids['profile_digest'],input_digest=given['manifest_digest'],policy_digest=policy_digest)
    submit_claim(control,port,offer_id='q1-offer');activate_assignment(control,port,attempt_id=ATTEMPT,expect=live)
    roots=workspaces.assignment_workspace(group,str(storage),ATTEMPT)
    workspaces.compose_input_root(roots['inputs'],given,assignment,assignment=assignment['assignment_ref'],runtime_attempt_id=ATTEMPT)
    home_root=str(root/'homes')
    home_identity=dict(authority_uuid=WORK['authority_uuid'],job_id=JOB,worker_id='q1-offline-worker')
    held=provider_home.acquire(home_root,**home_identity,attempt_id=ATTEMPT)
    mount=provider_home.HomeMount(home_root,**home_identity,attempt_id=ATTEMPT)
    seed=root/'synthetic-login';seed.write_bytes(b'{"q1_synthetic_only":true}\n');seed.chmod(0o600)
    from baton_v12.provider_policy.home import prepare as home_prepare
    mount.initialize_credential('codex/auth.json',lambda:home_prepare(held['home'],credential_path='codex/auth.json',delivered=str(seed),mode='seeded-retained'))
    home_prepare(held['home'],credential_path='codex/auth.json',delivered=None,mode='seeded-retained',managed=policy.managed_payloads(ids['adapter']))
    seed.unlink()  # Retained validation must not depend on a source copy.
    mount.initialize_credential('codex/auth.json',lambda:(_ for _ in ()).throw(AssertionError('restart reseeded')))
    delivery=policy.delivery(contract,adapter_digest=ids['adapter_digest'],profile_digest=ids['profile_digest'],tool_policy_digest=policy_digest,**home_identity,attempt_id=ATTEMPT)
    model_attribution.select(control,delivery,phase='implementation',logs_root=str(root/'logs'),home_root=home_root)
    limits=execution_limits.resolved({},1)
    job_execution=dict(job_id=JOB,attempt_id=ATTEMPT,job_input_digest=given['manifest_digest'],job_policy_digest=policy_digest,runtime_input_digest=given['manifest_digest'],runtime_policy_digest=policy_digest,execution_limits=limits,execution_limits_digest=digest(limits))
    launch_home=root/'launch';launch_home.mkdir(mode=0o700)
    launched=launch.materialize(str(launch_home),attempt_id=ATTEMPT,session='q1-offline-session',contract='offline diagnostics only; no provider command',role='implementation',transport=None,job_execution=job_execution,workspace_group=group,provider_selection=delivery)
    def engine(argv,seconds=None):
        assert not control._connection.in_transaction, 'engine I/O inside transaction'
        return run(argv,seconds=seconds)
    adapter=OciAdapter('docker',EnginePort(engine),identity=dict(image_digest=image,profile_digest=ids['profile_digest'],policy_digest=policy_digest,adapter_digest=ids['adapter_digest']),assignment_roots=roots,posture='execution',mounts=[dict(source=roots['inputs'],target='/input',writable=False),dict(source=roots['workspace'],target='/output',writable=True)],workspace_group=group,launch_delivery=launched,provider_home_delivery=mount,network='none',interactive=True)
    assert adapter.codex_image_receipt
    save(root/'selection.json',dict(synthetic_authority=True,provider_call_selected=False,delivery=delivery,job_execution=job_execution,roots=dict(roots),home=held['home']))
    return control,adapter,roots,delivery

def start(control,adapter,roots):
    from baton_v12.worker_manager import attempts, image_receipts, model_attribution
    answer=attempts.request_runtime_start(control,adapter,attempt_id=ATTEMPT,inputs=roots['inputs'])
    assert answer['decision']=='attached', answer
    row=attempts.attempt_runtime_of(control,ATTEMPT);runtime=row['runtime_id'];assert runtime
    state=attempts._observed(adapter,runtime,store=control,attempt_id=ATTEMPT)
    assert state[0]=='running', state
    receipt,cause=image_receipts.evidence(control,ATTEMPT,model_attribution.selection_of(control,ATTEMPT))
    assert cause is None, cause
    return runtime,receipt

def retained(control):
    from baton_v12.worker_manager import image_receipts,model_attribution
    receipt,cause=image_receipts.evidence(control,ATTEMPT,model_attribution.selection_of(control,ATTEMPT))
    assert cause is None, cause
    return receipt
