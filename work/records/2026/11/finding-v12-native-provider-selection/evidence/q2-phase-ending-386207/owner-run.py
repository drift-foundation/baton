"""Q2 preparation/default check. --execute needs separate owner selection."""
import argparse,ast,hashlib,importlib,json,os,signal,sys,time,shutil,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=Path('/var/tmp/baton-codex-q2-386207')
DEST=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-execution-386207')
LOGIN=Path('/home/sl/.codex-pushcoin/auth.json') # Reference only until selected production materialization.
BASE='42da148f1b845474e5fa6db870132fcf214073f6'
sys.path.insert(0,str(P))
from runner import Commands,cleanup,extract,safe_root,sha,save

def check():
    if not __debug__:raise RuntimeError('optimized Python refused')
    files=json.loads((P/'payload.json').read_text())
    for name,digest in files.items():
        assert Path(name).name==name and not (P/name).is_symlink()
        assert sha((P/name).read_bytes())==digest,name
    for name in ('owner-run.py','native.py','runner.py','check_execute.py','fake_engine.py'):ast.parse((P/name).read_text())
    with tarfile.open(P/'source.tar') as t:
        observed={}
        for member in t:
            assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts
            observed[member.name]=dict(sha256=sha(t.extractfile(member).read()),mode=member.mode)
        assert observed==json.loads((P/'source-files.json').read_text())
    return dict(payload_sha256=sha((P/'payload.json').read_bytes()),source=BASE,read_only=True,engine_operations=0,credential_access=False)

def execute(selection,payload,image_evidence,image_evidence_sha256):
    before=check();assert payload==before['payload_sha256']
    from image_gate import qualify
    binding=qualify(Path(image_evidence),image_evidence_sha256)
    assert selection and selection not in ('OWNER_MESSAGE_ID','pending','unselected')
    assert os.getuid()==1000 and os.getgid()==1000
    assert not any(k.startswith('GIT_') for k in os.environ)
    safe_root(ROOT);assert not ROOT.exists() and not DEST.exists()
    assert shutil.disk_usage(ROOT.parent).free>=4*1024**3
    os.umask(0o077);ROOT.mkdir(mode=0o700)
    for name in ('commands','client-home','docker-config','tmp','native'):(ROOT/name).mkdir(mode=0o700)
    (ROOT/'docker-config/config.json').write_text('{"auths":{}}\n')
    run=Commands(ROOT);run.deadline=time.monotonic()+300
    job=control=ops=None;attempt=None;failure=None;terminal=None;image_before=None;configuration=None
    def interrupted(signum,frame):raise InterruptedError('selected Q2 deadline or signal')
    for sig in (signal.SIGTERM,signal.SIGALRM,signal.SIGHUP):signal.signal(sig,interrupted)
    signal.alarm(300)
    try:
        extract(P/'source.tar',ROOT/'source')
        os.environ.update(HOME=str(ROOT/'client-home'),TMPDIR=str(ROOT/'tmp'),BATON_V12_DISK_ROOT=str(ROOT/'tmp'),PYTHONDONTWRITEBYTECODE='1')
        sys.path[:0]=[str(ROOT/'source/v12/python/src'),str(ROOT/'source/v12/python')]
        import native
        native.IMAGE=binding['image']
        save(ROOT/'image-evidence.json',binding)
        save(ROOT/'selection.json',dict(owner_selection=selection,payload_sha256=payload,image=native.IMAGE,source=BASE,model='gpt-6-astra',fast=None,call_cap=1,network='bridge',credential_reference='codex-pushcoin-subscription',source_writeback=False))
        save(ROOT/'engine-version.json',json.loads(run.required(['docker','version','--format','{{json .}}'],seconds=15)['stdout']))
        inspect=json.loads(run.required(['docker','image','inspect',native.IMAGE],seconds=15)['stdout'])[0]
        assert inspect['Id']==native.IMAGE and inspect['Config']['Entrypoint']==['python3','/opt/baton/codex_entry.py']
        assert inspect['Config']['Labels']==binding['labels']
        save(ROOT/'image.json',inspect)
        job,control,ops,configuration=native.compose(ROOT/'native',LOGIN,run)
        from baton_v12.worker_manager import attempt_runtime_of,exchange,model_attribution
        from baton_v12.job_manager import submission
        from tools import single_worker
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            state=native.drive(job,control,ops);save(ROOT/'status.json',state)
            stage=state['jobs'][0]['stages'][0];attempt=stage.get('attempt_id')
            if attempt:
                row=attempt_runtime_of(control,attempt)
                if row and row.get('runtime_id'):
                    image_before=native.receipt(control,attempt);save(ROOT/'image-receipt.json',image_before)
                    assert image_before['cause'] is None
                    if not (ROOT/'container-inspect.json').exists():
                        inspected=json.loads(run.required(['docker','inspect','--type','container',row['runtime_id']])['stdout'])[0]
                        assert inspected['Image']==native.IMAGE and inspected['Config']['User']=='1000:1000'
                        assert inspected['HostConfig']['NetworkMode']=='bridge' and inspected['HostConfig']['ReadonlyRootfs'] is True
                        save(ROOT/'container-inspect.json',inspected)
                # Read the actual manager observation; do not write worker events.
                rowstage=next(x for x in submission.stage_rows(job) if x['kind']=='implementation')
                observation=stage.get('exchange') or {};save(ROOT/'exchange.json',observation)
                if observation.get('state') in ('answered','faulted') and observation.get('terminal') is not None:
                    terminal=observation;break
            if stage['state'] in ('exceptional','failed','blocked','cancelled'):break
            time.sleep(.2)
        assert terminal is not None,'no terminal within capture bound'
        # Never sweep to acceptance: Q2 captures evidence for independent judgment; activity is not a verdict.
        if attempt:
            save(ROOT/'attribution.json',dict(selection=model_attribution.selection_of(control,attempt),assessment=model_attribution.assessment_of(control,attempt),note='capture only; no frozen producer or acceptance fabricated'))
    except BaseException as exc:
        failure=type(exc).__name__;save(ROOT/'private-error.json',dict(type=failure,diagnostic=str(exc)))
    finally:
        signal.alarm(90);run.deadline=time.monotonic()+90
        if ops is not None and attempt:
            try:save(ROOT/'cancellation.json',ops.cancel_attempt(attempt_id=attempt,reason='bounded Q2 capture ended'))
            except BaseException as exc:save(ROOT/'cancellation-error.json',dict(type=type(exc).__name__,diagnostic=str(exc)))
        stopped=cleanup(run,ROOT)
        retained=None;captured=dict(edit_verified=False,candidate_present=False)
        if stopped.get('removed') is True and attempt:
            try:
                from collect import collect
                captured=collect(ROOT,attempt)
            except BaseException as exc:
                failure=failure or type(exc).__name__
                save(ROOT/'capture-error.json',dict(type=type(exc).__name__,diagnostic=str(exc)))
        if control is not None and attempt:
            try:retained=native.receipt(control,attempt);save(ROOT/'receipt-after-removal.json',retained)
            except BaseException as exc:failure=failure or type(exc).__name__
        if ops is not None:ops.close()
        if control is not None:
            control.close()
            if attempt:
                from baton_v12.worker_manager import ControlStore
                with ControlStore.open(str(ROOT/'native/control.sqlite3'),incarnation='q2-after-removal',clock=native.now) as reopened:
                    retained=native.receipt(reopened,attempt)
                    save(ROOT/'receipt-after-reopen.json',retained)
        withdrawal=False
        if configuration and attempt and stopped.get('removed') is True:
            try:
                from baton_v12.worker_manager.credentials import CredentialHome
                held=CredentialHome(configuration['credential_home'])
                save(ROOT/'volatile-credential-withdrawal.json',held.tear_down_orphan(attempt))
                withdrawal=not Path(held.volatile_root(attempt)).exists()
            except BaseException as exc:failure=failure or type(exc).__name__
        if job is not None:job.close()
        # No raw stream, exchange content, candidate, login or database is promoted.
        # Strong cleanup and capture facts are separate from parser acceptance.
        verdict=dict(packet='q2-386207',payload_sha256=payload,source=BASE,image=binding['image'],capture_terminal=terminal is not None,error_type=failure,container_launches=run.launches,ceased=stopped.get('ceased') is True,removed=stopped.get('removed') is True,image_receipt_retained=image_before is not None and retained==image_before,acceptance='held-for-private-evidence-review',actual_contributors='unknown',configured_model='gpt-6-astra',source_writeback=False,private_root=str(ROOT),native_job_success=False,volatile_credential_withdrawn=withdrawal,retained_home_preserved=True,**captured)
        save(ROOT/'RESULT.json',verdict)
        if not DEST.exists():
            DEST.mkdir(mode=0o700);save(DEST/'RESULT.json',verdict)
        signal.alarm(0)
    print(json.dumps(verdict));return 0 if terminal is not None and verdict['ceased'] and verdict['removed'] and not failure else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--selection');parser.add_argument('--payload');parser.add_argument('--image-evidence');parser.add_argument('--image-evidence-sha256')
    args=parser.parse_args()
    if args.execute:
        if args.check or not args.selection or not args.payload or not args.image_evidence or not args.image_evidence_sha256:parser.error('execution needs owner selection and reviewed payload')
        sys.exit(execute(args.selection,args.payload,args.image_evidence,args.image_evidence_sha256))
    print(json.dumps(check(),indent=2))
