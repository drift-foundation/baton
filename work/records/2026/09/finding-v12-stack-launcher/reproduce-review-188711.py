"""W183883 remaining installation boundaries; no actual repository command."""
import contextlib,hashlib,io,json,os,subprocess,sys,tempfile,time
from pathlib import Path
from unittest import mock
D=Path(__file__).resolve().parent; ROOT=D.parents[4]
sys.path[:0]=[str(ROOT/'v12/python'),str(ROOT/'v12/python/src')]
sys.dont_write_bytecode=True
from tools import bootstrap,instance
from tests.tools.test_instance import TheBootstrapPreparesTheRepositories

def main():
    began=time.monotonic(); root=Path(tempfile.mkdtemp(prefix='w183883-review188711-',dir='/tmp'))
    author=json.loads((D/'EVIDENCE-188671.json').read_text())
    hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in author['candidates']};assert hashes==author['candidates']
    result={'claim':188711,'candidate_hashes':hashes,'scratch_retained':str(root),'cases':{}}
    def fixture(name):
        f=TheBootstrapPreparesTheRepositories(); f.root=root/name; f.destination=str(f.root/'deployment'); f.places=instance.layout(f.destination); f.bootstrap=bootstrap; f.issued=[];f.answers={};f.common={};return f
    f=fixture('lock'); real_lock=bootstrap.serialized
    @contextlib.contextmanager
    def after_wait(places,wait):
        with real_lock(places,wait) as held:
            Path(places['distro']).mkdir();Path(places['justfile']).write_text('foreign');Path(places['instance']).write_text('foreign')
            yield held
    try:
        with mock.patch.object(bootstrap,'serialized',after_wait):bootstrap.prepare_repositories(f.document(),f.places,runner=f.runner,stream=io.StringIO())
    except bootstrap.BootstrapRefusal as e: refusal=str(e)
    else:raise AssertionError('custody accepted')
    assert not f.issued and Path(f.places['justfile']).read_text()=='foreign'
    result['cases']['custody_after_lock']={'refusal':refusal,'calls':f.issued,'foreign_preserved':True}
    for mode in ('absent','shared-local','external','symlink-external'):
        f=fixture(mode);given=f.document()
        for w in given['workers']:
            if mode=='shared-local': w['deployment']['workspace_storage']=str(Path(f.destination)/'workers/shared')
            if mode=='external':w['deployment']['workspace_storage']=str(root/'external')
            if mode=='symlink-external':
                Path(f.destination).mkdir(parents=True,exist_ok=True)
                link=Path(f.destination)/'linked'
                if not link.is_symlink():link.symlink_to(root/'external',target_is_directory=True)
                w['deployment']['workspace_storage']=str(link/'storage')
        try:bound=bootstrap.storage_bound(given,f.places)
        except bootstrap.BootstrapRefusal as e:
            assert mode in ('external','symlink-external');result['cases']['storage_'+mode]={'refusal':str(e)}
        else:
            assert mode in ('absent','shared-local')
            paths=[w['deployment']['workspace_storage'] for w in bound['workers']]
            assert all(Path(x).is_relative_to(f.destination) for x in paths)
            if mode=='shared-local':assert len(set(paths))==1
            result['cases']['storage_'+mode]={'paths':paths}
    runtime=root/'runtime';(runtime/'_internal/rpds').mkdir(parents=True);(runtime/'baton-v12-stack').write_text('inert');(runtime/'_internal/rpds/rpds.so').write_text('inert')
    identity={'command':'baton-v12-stack','frozen':True,'python':'3.13.7','platform':'Linux','machine':'x86_64','schema_assets':{'agent-session-1.0':10,'worker-control-1.0':20},'native_rpds':str(runtime/'_internal/rpds/rpds.so')}
    def install(f,out):
        with mock.patch.object(bootstrap,'_identity_of',return_value=identity):return bootstrap.install(f.destination,str(runtime),{'authority_uuid':'a'*32},stream=out)
    f=fixture('normal-retry');out=io.StringIO()
    with mock.patch.object(instance,'create',side_effect=OSError('transient publication failure')):
        try:install(f,out)
        except OSError:pass
        else:raise AssertionError('no injection')
    assert not Path(f.places['justfile']).exists() and not Path(f.places['distro']).exists()
    install(f,out);assert Path(f.places['instance']).exists()
    result['cases']['publication_retry']={'retry_succeeded':True,'output':out.getvalue()}
    # Fail during writing, after exclusive creation but before the bool is set.
    f=fixture('partial-write');real_fdopen=os.fdopen;out=io.StringIO()
    class Partial:
        def __init__(self,fd,*a,**kw):self.file=real_fdopen(fd,*a,**kw)
        def __enter__(self):return self
        def write(self,data):self.file.write(data[:24]);self.file.flush();raise OSError('injected full disk during justfile write')
        def __exit__(self,*a):self.file.close()
    with mock.patch.object(os,'fdopen',Partial):
        try:install(f,out)
        except OSError as e:error=str(e)
        else:raise AssertionError('no partial error')
    left=Path(f.places['justfile']).read_text()
    try:install(f,out)
    except bootstrap.BootstrapRefusal as e:retry=str(e)
    else:raise AssertionError('partial write unexpectedly retried')
    result['cases']['partial_write_blocks_retry']={'error':error,'partial_bytes':left,'retry_refusal':retry,'output':out.getvalue()}
    assert len(left)==24
    # A pathname replaced after exclusive creation is no longer our file.
    f=fixture('replacement');out=io.StringIO()
    def replaced(place,selector):
        replacement=Path(f.destination)/'replacement'
        replacement.write_text('foreign replacement')
        os.replace(replacement,f.places['justfile'])
        raise instance.InstanceRefusal('simulated publication refusal after replacement')
    with mock.patch.object(instance,'create',side_effect=replaced):
        try:install(f,out)
        except bootstrap.BootstrapRefusal as e:error=str(e)
        else:raise AssertionError('no replacement refusal')
    result['cases']['replacement_deleted']={'refusal':error,'foreign_file_exists':Path(f.places['justfile']).exists(),'output':out.getvalue()}
    assert not Path(f.places['justfile']).exists()
    result['seconds']=time.monotonic()-began
    result['limits']='Actual installer and binding functions, inert runtime identity, simulated repository runner and deterministic publication/write boundary injections. No actual Git, store/Authority open, credential read, provider/engine/Job or live stack operation. Replacement is a deterministic boundary case, not a claim of adversarial filesystem protection.'
    (D/'REVIEW-EVIDENCE-188711.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'seconds':result['seconds'],'scratch':str(root),'cases':list(result['cases'])},indent=2))
if __name__=='__main__':main()
