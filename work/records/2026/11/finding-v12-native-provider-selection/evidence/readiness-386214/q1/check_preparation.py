"""Deterministic harness validation. NO subprocess engine capability is supplied."""
import importlib.util,json,os,sys,tempfile,tarfile,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
class FakeEngine:
    def __init__(self):self.calls=[];self.runtime=None;self.running=False;self.labels={};self.mounts=[];self.created=None;self.expected_labels={};self.deadline=0
    def __call__(self,argv,seconds=None):
        self.calls.append(argv);out=''
        if argv[1] in ('run','create'):
            assert self.runtime is None
            self.created=argv[argv.index('--name')+1]
            self.runtime='a'*64;self.running=argv[1]=='run';self.image=argv[-1]
            for i,arg in enumerate(argv):
                if arg=='--label':k,v=argv[i+1].split('=',1);self.labels[k]=v
                if arg=='--mount':
                    parts=dict(x.split('=',1) for x in argv[i+1].split(',') if '=' in x)
                    self.mounts.append(dict(Type='bind',Source=parts['source'],Destination=parts['target'],RW=parts['readonly']=='false'))
            self.expected_labels=dict(self.labels)
            out=self.runtime+'\n'
        elif argv[1]=='start':self.running=True
        elif argv[1]=='stop':self.running=False
        elif argv[1]=='rm':self.runtime=None
        elif argv[1]=='ps':
            if self.runtime:out=(self.created if '{{.Names}}' in argv else json.dumps(dict(ID=self.runtime,Image=self.image,Labels=self.labels)))+'\n'
        elif argv[1]=='inspect':
            if self.runtime is None:return dict(status=1,stdout='',stderr='Error: No such container: '+argv[-1])
            doc=dict(Id=self.runtime,Image=self.image,Config=dict(Labels=self.labels),State=dict(Running=self.running,StartedAt='2026-11-25T00:00:00Z',ExitCode=0),Mounts=self.mounts)
            out=json.dumps(doc if '--format' in argv else [doc])
        else:raise AssertionError('Unexpected simulated engine operation '+repr(argv))
        return dict(status=0,stdout=out,stderr='')

    def required(self,argv,seconds=30,cap=None):
        result=self(argv,seconds=seconds);assert result['status']==0;return result

def main():
    assert (os.getuid(),os.getgid())==(1000,1000)
    with tempfile.TemporaryDirectory(prefix='baton-q1-preparation-386214-',dir='/var/tmp') as temp:
        root=Path(temp);src=root/'source';src.mkdir();run=root/'run';run.mkdir(mode=0o700)
        with tarfile.open(P/'source.tar') as t:t.extractall(src,filter='data')
        os.environ['TMPDIR']=str(root);os.environ['BATON_V12_DISK_ROOT']=str(root);os.environ['PYTHONDONTWRITEBYTECODE']='1'
        sys.path[:0]=[str(src/'v12/python/src'),str(src/'v12/python'),str(src/'v12/worker'),str(src/'v12/python/src/baton_v12'),str(P)]
        import manager_probe
        fake=FakeEngine();control,adapter,roots,delivery=manager_probe.prepare(run,'sha256:'+'b'*64,fake)
        try:
            runtime,receipt=manager_probe.start(control,adapter,roots)
            assert receipt['observation']['runtime_id']==runtime
            assert manager_probe.retained(control)==receipt
            launches=[x for x in fake.calls if x[1] in ('run','create')]
            assert len(launches)==1
            vector=launches[0]
            for key,value in [('--network','none'),('--user','1000:1000'),('--memory','2g'),('--cpus','2'),('--pids-limit','512')]:assert vector[vector.index(key)+1]==value,(key,vector)
            assert '--interactive' in vector
            # Entry accepts the prepared launch on EOF without any provider act.
            import io
            import baton_worker, codex_agent
            from unittest import mock
            with mock.patch('subprocess.Popen',side_effect=AssertionError('no process may start during entry validation')):
                status=baton_worker.main(argv=[],stdin=io.StringIO(''),stdout=io.StringIO(),agent=codex_agent.CodexAgent(),place=adapter.launch_delivery.place)
            assert status==0,status
            spec=importlib.util.spec_from_file_location('q1_owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
            original_labels=dict(fake.labels)
            fake.labels['baton.v12.generation']='999'
            refused=owner.cleanup(fake,run);assert refused.get('removed') is not True and fake.runtime is not None
            fake.labels=original_labels
            clean=owner.cleanup(fake,run);assert clean['ceased'] and clean['removed'],clean
            from baton_v12.worker_manager import attempts,ControlStore
            attempts.reconcile_runtime(control,adapter,attempt_id=manager_probe.ATTEMPT)
            assert attempts.attempt_runtime_of(control,manager_probe.ATTEMPT)['execution_runtime']=='destroyed', attempts.attempt_runtime_of(control,manager_probe.ATTEMPT)
            with ControlStore.open(control.database,incarnation='q1-simulated-reopen',clock=manager_probe.now) as reopened:assert manager_probe.retained(reopened)==receipt
            result=dict(simulation=True,engine_processes=0,provider_calls=0,source_commit=json.loads((P/'q1-build.json').read_text())['source_commit'],manager_launches=len(launches),prepared_harness=True,checks=['real manager claim/activation/input/launch composition','automatic synthetic home seed and source-independent restart','real OCI vector restrictions','normal image receipt path enabled from launch selection','real receipt persistence against synthetic engine facts','entry EOF with subprocess spawning prohibited','foreign-container cleanup refusal','positive cleanup then manager reconciliation and receipt reopen with fake engine'],engine_vectors=fake.calls)
            if '--evidence' in sys.argv:
                Path(sys.argv[sys.argv.index('--evidence')+1]).write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({k:v for k,v in result.items() if k!='engine_vectors'}))
        finally:control.close()
    assert not root.exists()
if __name__=='__main__':main()
