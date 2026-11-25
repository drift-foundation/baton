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
    binding=temporary/'synthetic-image-evidence.json';binding.write_text(json.dumps(synthetic()))
    real=subprocess.Popen;state=temporary/'fake-state.json';calls=[]
    def popen(argv,*args,**kw):
        calls.append(list(argv))
        if argv[0]=='docker':return real([sys.executable,'-B',str(P/'fake_engine.py'),str(state),scenario,*argv[1:]],*args,**kw)
        assert argv[0]=='git' and argv[1]=='-C' and Path(argv[2])==owner.ROOT/'native/fixture',argv
        return real(argv,*args,**kw)
    with mock.patch.dict(os.environ,{k:v for k,v in os.environ.items() if not k.startswith('GIT_')},clear=True), mock.patch('subprocess.Popen',side_effect=popen):
        result=owner.execute('SIMULATION-ONLY',hashlib.sha256((P/'payload.json').read_bytes()).hexdigest(),binding,hashlib.sha256(binding.read_bytes()).hexdigest())
    verdict=json.loads((owner.ROOT/'RESULT.json').read_text())
    assert owner.LOGIN.read_bytes()==original_login
    assert verdict['acceptance']=='held-for-private-evidence-review' and not verdict['native_job_success']
    if scenario in ('fault-terminal','provider-seam'):
        assert result==0 and verdict['capture_terminal'] and verdict['ceased'] and verdict['removed'] and verdict['image_receipt_retained'] and verdict['volatile_credential_withdrawn'],verdict
    else:
        assert result==1 and not verdict['capture_terminal'] and verdict['ceased'] and verdict['removed'],verdict
    if scenario=='launch-fail':assert verdict['container_launches']==1
    if scenario=='oversize':assert verdict['container_launches']==0
    if scenario=='provider-seam':
        assert verdict['edit_verified']
        assert json.loads((owner.ROOT/'simulated-worker-result.json').read_text())['provider_seam_calls']==1
    if '--evidence' in sys.argv:
        retained=Path(sys.argv[sys.argv.index('--evidence')+1])
        assert not retained.exists(),'fresh preparation evidence required'
        retained.mkdir(parents=True)
        for name in ('RESULT.json','private-error.json','image-receipt.json','receipt-after-reopen.json','volatile-credential-withdrawal.json','cleanup.json','simulated-provider-seam.json','simulated-worker-result.json','simulated-worker-error.txt','exchange.json','capture-inventory.json'):
            if (owner.ROOT/name).is_file():shutil.copyfile(owner.ROOT/name,retained/name)
        shutil.copyfile(state,retained/'fake-engine-state.json')
    print(json.dumps(dict(scenario=scenario,exit=result,private_preparation_root=str(temporary),commands=len(calls),real_engine_calls=0,real_credential_reads=0)))
    for here,dirs,files in os.walk(temporary):
        os.chmod(here,0o700)
    shutil.rmtree(temporary)
    assert not temporary.exists()
    print(json.dumps(dict(assertions_passed=True,temporary_root_removed=True)))
if __name__=='__main__':main()
