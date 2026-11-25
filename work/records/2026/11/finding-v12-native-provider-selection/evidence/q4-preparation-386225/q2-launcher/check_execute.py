"""Exercise actual execute with substituted Docker subprocess; real disposable Git only."""
import importlib.util,json,os,subprocess,sys,tempfile,hashlib,shutil,stat
from pathlib import Path
from unittest import mock
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('q2owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
def main():
    scenario=sys.argv[1] if len(sys.argv)>1 else 'launch-fail'
    # Retain failing preparation evidence privately; never delete uncertain files.
    temporary=Path(tempfile.mkdtemp(prefix='baton-q2-prep-'+scenario+'-',dir='/var/tmp'))
    owner.ROOT=temporary/'run';owner.DEST=temporary/'public';owner.LOGIN=temporary/'synthetic-login'
    owner.LOGIN.write_bytes(b'{"synthetic_q2_only":true}\n');owner.LOGIN.chmod(0o600)
    if scenario=='oversize':owner.LOGIN.write_bytes(b'x'*(1048576+1))
    original_login=owner.LOGIN.read_bytes()
    from check_image_gate import synthetic
    if scenario=='layout-missing':
        # REGRESSION ONLY: reproduce the 386214 composition (no layout delivered) through the same path.
        import native;native.marker=lambda root:None
    binding=temporary/'synthetic-image-evidence.json';binding.write_text(json.dumps(synthetic()))
    real=subprocess.Popen;state=temporary/'fake-state.json';calls=[]
    def popen(argv,*args,**kw):
        calls.append(list(argv))
        if argv[0]=='docker':return real([sys.executable,'-B',str(P/'fake_engine.py'),str(state),scenario,*argv[1:]],*args,**kw)
        assert argv[0]=='git' and argv[1]=='-C' and Path(argv[2])==owner.ROOT/'native/fixture',argv
        return real(argv,*args,**kw)
    with mock.patch.dict(os.environ,{k:v for k,v in os.environ.items() if not k.startswith('GIT_')},clear=True), mock.patch('subprocess.Popen',side_effect=popen):
        started=__import__('time').monotonic()
        result=owner.execute('SIMULATION-ONLY',hashlib.sha256((P/'payload.json').read_bytes()).hexdigest(),binding,hashlib.sha256(binding.read_bytes()).hexdigest())
    verdict=json.loads((owner.ROOT/'RESULT.json').read_text());elapsed=__import__('time').monotonic()-started
    assert owner.LOGIN.read_bytes()==original_login
    assert verdict['acceptance']=='held-for-private-evidence-review' and not verdict['native_job_success']
    if scenario in ('fault-terminal','provider-seam','layout-missing','completed'):
        assert result==0 and verdict['capture_terminal'] and verdict['ceased'] and verdict['removed'] and verdict['image_receipt_retained'] and verdict['volatile_credential_withdrawn'],verdict
    else:
        assert result==1 and not verdict['capture_terminal'] and verdict['ceased'] and verdict['removed'],verdict
    if scenario=='launch-fail':assert verdict['container_launches']==1
    if scenario=='oversize':assert verdict['container_launches']==0
    configuration=json.loads((owner.ROOT/'native/deployment.json').read_text()) if (owner.ROOT/'native/deployment.json').is_file() else None
    if scenario=='provider-seam':
        assert verdict['edit_verified']
        assert json.loads((owner.ROOT/'simulated-worker-result.json').read_text())['provider_seam_calls']==1
        seam=json.loads((owner.ROOT/'simulated-provider-seam.json').read_text())['layout']
        marker=json.loads((owner.ROOT/'source/v12/worker/verifier-layout-marker.json').read_text())
        assert configuration['verifier_layout']==marker
        document=seam['delivered_document']
        assert document['layout_digest']==marker['layout_digest'] and document['roots']==marker['roots'] and (document['uid'],document['gid'])==(1000,1000)
        assert all(document[name]==configuration[name] for name in ('image_digest','profile_digest','policy_digest','adapter_digest'))
        assert sorted(seam['composed_tmpfs'])==sorted(marker['roots']) and seam['preflights_before_provider']>=1
        engine=json.loads(state.read_text())['log'];create=next(x for x in engine if x[0] in ('create','run'))
        binds=[x for x in create if 'target=/run/baton/verifier-layout.json' in x]
        assert len(binds)==1 and 'readonly=true' in binds[0].split(','),binds
        # The task the composed run actually wrote: run its exact argv, no shell, as the worker does.
        argv=json.loads((owner.ROOT/'native/task.json').read_text())['verification'];matrix={}
        for label,body in (('after-newline',b'after\n'),('before-newline',b'before\n'),('after-no-newline',b'after'),('after-backslash-n',b'after\\n')):
            cell=temporary/('verify-'+label);cell.mkdir();(cell/'message.txt').write_bytes(body)
            matrix[label]=real(argv,cwd=cell,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).wait()
        assert matrix=={'after-newline':0,'before-newline':1,'after-no-newline':1,'after-backslash-n':1},matrix
        (owner.ROOT/'verification-matrix.json').write_text(json.dumps(dict(argv=argv,exit_status=matrix)))
    if scenario in ('fault-terminal','provider-seam','layout-missing'):assert verdict['completion_observation']=='exchange',verdict
    if scenario=='completed':
        # The 386221 shape: the manager settles the stage and clears the exchange between polls.
        assert verdict['completion_observation']=='custody' and verdict['edit_verified'] and verdict['error_type'] is None,verdict
        assert elapsed<60,'completed stage was waited on: %.1fs'%elapsed
        seen=json.loads((owner.ROOT/'completion.json').read_text());status=json.loads((owner.ROOT/'status.json').read_text())['jobs'][0]['stages'][0]
        assert status['state']=='completed' and status['exchange'] is None and seen['attempt_id']==status['attempt_id'] and 'proposal' in seen['artifacts']
        assert json.loads((owner.ROOT/'simulated-worker-result.json').read_text())['provider_seam_calls']==1
        (owner.ROOT/'completion-check.json').write_text(json.dumps(dict(elapsed_seconds=round(elapsed,3),capture_bound_seconds=240,stage_state=status['state'],exchange=status['exchange'],completion=seen,synthetic_provider_framing=True)))
    if scenario=='layout-missing':
        assert configuration['verifier_layout'] is None and not verdict['edit_verified']
        assert json.loads((owner.ROOT/'simulated-worker-result.json').read_text())['provider_seam_calls']==0
        assert not (owner.ROOT/'simulated-provider-seam.json').exists()
        assert 'no trusted layout selection was delivered' in (owner.ROOT/'simulated-worker-error.txt').read_text()
    if '--evidence' in sys.argv:
        retained=Path(sys.argv[sys.argv.index('--evidence')+1])
        assert not retained.exists(),'fresh preparation evidence required'
        retained.mkdir(parents=True)
        for name in ('RESULT.json','private-error.json','image-receipt.json','receipt-after-reopen.json','volatile-credential-withdrawal.json','cleanup.json','simulated-provider-seam.json','simulated-worker-result.json','simulated-worker-error.txt','exchange.json','capture-inventory.json','verification-matrix.json','completion.json','completion-check.json'):
            if (owner.ROOT/name).is_file():shutil.copyfile(owner.ROOT/name,retained/name)
        shutil.copyfile(state,retained/'fake-engine-state.json')
    print(json.dumps(dict(scenario=scenario,exit=result,private_preparation_root=str(temporary),commands=len(calls),real_engine_calls=0,real_credential_reads=0)))
    for here,dirs,files in os.walk(temporary):
        os.chmod(here,0o700)
    shutil.rmtree(temporary)
    assert not temporary.exists()
    print(json.dumps(dict(assertions_passed=True,temporary_root_removed=True)))
if __name__=='__main__':main()
