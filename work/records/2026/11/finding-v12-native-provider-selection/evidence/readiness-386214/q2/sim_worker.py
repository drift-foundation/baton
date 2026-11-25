"""Preparation-only mount translation; real Codex adapter, refusal at provider seam."""
import json,os,shutil,subprocess,sys
from pathlib import Path
from unittest import mock

def run(root,mounts,seen):
    sys.path[:0]=[str(root/'source/v12/python/src'),str(root/'source/v12/worker'),str(root/'source/v12/python/src/baton_v12')]
    import baton_worker,claude_agent,codex_agent,provider_policy
    import provider_policy.home as home
    from baton_v12.worker_manager import launch
    seen=launch.payload_of(seen)
    inputs=Path(mounts['/input']);source=inputs/'source'
    source.chmod(0o700)
    shutil.copytree(mounts['/input/source'],source,dirs_exist_ok=True)
    homepath=mounts['/run/baton/provider-home']
    realcheck,realprepare=home.checked_home,home.prepare
    calls=[]
    def translated(path):
        assert path==provider_policy.HOME
        return homepath
    def provider(argv,**kw):
        if argv[0]=='codex':
            if argv[1:]==['--version']:
                os.write(kw['stdout'],b'codex-cli 0.169.0\n')
                return subprocess.CompletedProcess(argv,0,None,None)
            calls.append(argv)
            assert len(calls)==1 and '--model' in argv and argv[argv.index('--model')+1]=='gpt-6-astra'
            assert '--ignore-user-config' in argv and '-c' not in argv
            assert Path(kw['cwd'],'.git').is_dir()
            assert kw['env']['CODEX_HOME']==str(Path(homepath)/'codex')
            assert Path(homepath,'instructions/WORKER.md').read_bytes()==provider_policy.worker_instructions()
            # Synthetic filesystem effect only; no claimed successful output stream.
            Path(kw['cwd'],'message.txt').write_bytes(b'after\n')
            (root/'simulated-provider-seam.json').write_text(json.dumps(dict(simulation=True,invocations=1,argv=argv,environment=kw['env'],instruction_sha256=__import__('hashlib').sha256(provider_policy.worker_instructions()).hexdigest())))
            raise RuntimeError('preparation stops at provider seam; no provider output invented')
        assert argv[0] in ('git','python3'),argv
        return subprocess.run(argv,**kw)
    for module in (baton_worker,claude_agent):
        module.INPUT_ROOT=str(inputs);module.OUTPUT_ROOT=mounts['/output']
    with mock.patch.object(home,'checked_home',side_effect=lambda path:realcheck(translated(path))),mock.patch.object(home,'prepare',side_effect=lambda path,**kw:realprepare(translated(path),**kw)),mock.patch.dict(os.environ,{'BATON_ATTEMPT_LOG_ROOM':mounts['/run/baton/attempt-logs']}):
        agent=codex_agent.CodexAgent(run=provider,home=mounts['/scratch'])
        original_work=agent.work
        def traced(*a,**k):
            try:return original_work(*a,**k)
            except BaseException:
                import traceback
                (root/'simulated-worker-error.txt').write_text(traceback.format_exc())
                raise
        agent.work=traced
        result=baton_worker.serve_exchange(agent,seen,launch.payload_of(seen)['session'],mounts['/run/baton/exchange/command'],mounts['/run/baton/exchange/events'])
    (root/'simulated-worker-result.json').write_text(json.dumps(dict(status=result,provider_seam_calls=len(calls))))
