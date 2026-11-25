"""Preparation-only mount translation; real Codex adapter, refusal at provider seam.

Verifier layout: the real marker/selection agreement runs unchanged against the
image marker bytes and the document the manager actually delivered. Only what a
host process cannot have is simulated, and it is labelled: the four tmpfs roots
are private host directories whose mount facts are derived from the --tmpfs
operands the manager composed (no operand, no fact, real refusal), and the
image-scaffolding ancestor proof is not exercised here.
"""
import json,os,shutil,subprocess,sys
from pathlib import Path
from unittest import mock

def tmpfs_facts(tmpfs,selection,place):
    """Synthetic mount facts for translated roots, from the composed engine operands only."""
    asked={one.split(':',1)[0]:one.split(':',1)[1].split(',') for one in tmpfs if ':' in one}
    facts={};checked={}
    for index,(name,target) in enumerate(sorted(selection['roots'].items())):
        options=asked.get(target)
        if options is None:continue
        pairs=dict(x.split('=',1) for x in options if '=' in x)
        assert int(pairs['uid'])==selection['uid'] and int(pairs['gid'])==selection['gid'] and int(pairs['mode'],8)==selection['mode'],(name,options)
        flags={x for x in options if '=' not in x}
        facts[place[name]]=dict(mount_id=str(900+index),parent_id='1',device='0:'+str(900+index),root='/',point=place[name],options=flags,filesystem='tmpfs',super_options={'rw'})
        checked[name]=dict(target=target,operand=options)
    return facts,checked

SYNTHETIC_STREAM=b''.join(json.dumps(x,separators=(',',':')).encode()+b'\n' for x in (
    {'type':'thread.started','thread_id':'synthetic-framing-only'},{'type':'turn.started'},
    {'type':'item.completed','item':{'id':'synthetic','type':'synthetic_opaque_activity'}},
    {'type':'turn.completed','usage':{'input_tokens':0,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':0,'reasoning_output_tokens':0}}))

def run(root,mounts,seen,tmpfs=(),complete=False):
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
    # Layout translation (simulation label above). Marker: frozen source bytes, hash-held to the image record.
    marker_place=root/'source/v12/worker/verifier-layout-marker.json'
    assert __import__('hashlib').sha256(marker_place.read_bytes()).hexdigest()==json.loads((Path(__file__).resolve().parent/'q1-build.json').read_text())['image_files']['/opt/baton/verifier-layout-marker.json']
    delivered=mounts.get('/run/baton/verifier-layout.json',str(root/'no-layout-delivered.json'))
    place={name:str(root/'simulated-verifier'/leaf) for name,leaf in (('HOME','home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('PYTHONPYCACHEPREFIX','pycache'))}
    for one in place.values():Path(one).mkdir(mode=0o700,parents=True)
    real_selected=codex_agent.CodexAgent._selected_layout;layout=dict(selected=None,facts=None,preflights=0)
    def selected(self,*a,**k):
        real=real_selected(self,*a,**k)
        if real is None:return None
        layout['selected']=real;layout['preflights']+=1
        return dict(real,roots=dict(place))
    def facts(*a,**k):
        held,checked=tmpfs_facts(tmpfs,layout['selected'],place);layout['facts']=checked
        return held
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
            assert layout['selected'] is not None and sorted(layout['facts'])==sorted(place),'provider boundary reached without a proved layout'
            (root/'simulated-provider-seam.json').write_text(json.dumps(dict(simulation=True,invocations=1,argv=argv,environment=kw['env'],instruction_sha256=__import__('hashlib').sha256(provider_policy.worker_instructions()).hexdigest(),layout=dict(simulation='tmpfs roots translated to private host directories; mount facts derived from composed --tmpfs operands; ancestor proof not exercised',delivered_document=json.loads(Path(delivered).read_text()),delivered_document_readonly_bind=True,composed_tmpfs=layout['facts'],preflights_before_provider=layout['preflights']))))
            if complete:
                # LABELLED SYNTHETIC FRAMING ONLY: the four structural records the adapter requires
                # of any invocation, with opaque activity. Not provider evidence and not a model answer.
                os.write(kw['stdout'],SYNTHETIC_STREAM)
                return subprocess.CompletedProcess(argv,0,None,None)
            raise RuntimeError('preparation stops at provider seam; no provider output invented')
        assert argv[0] in ('git','python3'),argv
        return subprocess.run(argv,**kw)
    for module in (baton_worker,claude_agent):
        module.INPUT_ROOT=str(inputs);module.OUTPUT_ROOT=mounts['/output']
    with mock.patch.object(home,'checked_home',side_effect=lambda path:realcheck(translated(path))),mock.patch.object(home,'prepare',side_effect=lambda path,**kw:realprepare(translated(path),**kw)),mock.patch.dict(os.environ,{'BATON_ATTEMPT_LOG_ROOM':mounts['/run/baton/attempt-logs']}),mock.patch.object(codex_agent.CodexAgent,'LAYOUT_MARKER',str(marker_place)),mock.patch.object(codex_agent.CodexAgent,'LAYOUT_DOCUMENT',delivered),mock.patch.object(codex_agent.CodexAgent,'_selected_layout',selected),mock.patch.object(codex_agent.CodexAgent,'_mount_facts',facts),mock.patch.object(codex_agent.CodexAgent,'_proved_ancestors',lambda self,place,facts:None):
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
