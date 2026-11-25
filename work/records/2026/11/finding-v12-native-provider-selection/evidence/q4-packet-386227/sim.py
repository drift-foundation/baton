"""Preparation-only mount translation for both roles; real adapters, simulated provider.

Implementation: the real CodexAgent; the provider seam makes one labelled edit and emits four
synthetic framing records. Review: the real ClaudeAgent; the provider seam writes the review
report selected by the scenario and a synthetic terminal whose modelUsage names the selected
identity plus one extra contributor. Neither is provider evidence.

Verifier layout: the real marker/selection agreement runs against the image marker bytes and
the document the manager delivered. The four tmpfs roots are private host directories whose
mount facts come only from the --tmpfs operands the manager composed; the image-scaffolding
ancestor proof is not exercised here.
"""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from unittest import mock
FRAMING=b''.join(json.dumps(x,separators=(',',':')).encode()+b'\n' for x in (
    {'type':'thread.started','thread_id':'synthetic-framing-only'},{'type':'turn.started'},
    {'type':'item.completed','item':{'id':'synthetic','type':'synthetic_opaque_activity'}},
    {'type':'turn.completed','usage':{'input_tokens':0,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':0,'reasoning_output_tokens':0}}))
IMAGE_FILES=['python/src/baton_v12/attempt_log_format.py','python/src/baton_v12/verification_context.py','worker/baton_worker.py','worker/adapter_refusal.py','worker/claude_agent.py','worker/bounded_command.py','worker/dogfood_entry.py','worker/worker-control-1.0.schema.json','worker/verifier-layout-marker.json']
def expected_image_files(source):
    """What Dockerfile.claude copies to /opt/baton, as target -> sha256 of the frozen source."""
    v12=Path(source)/'v12';answer={}
    for rel in IMAGE_FILES:answer['/opt/baton/'+Path(rel).name]=hashlib.sha256((v12/rel).read_bytes()).hexdigest()
    for tree in ('source_profiles','provider_policy'):
        for path in sorted((v12/'python/src/baton_v12'/tree).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:answer['/opt/baton/'+tree+'/'+str(path.relative_to(v12/'python/src/baton_v12'/tree))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return answer
def image_files(root,tamper=False):
    answer=expected_image_files(Path(root)/'source')
    if tamper:answer['/opt/baton/claude_agent.py']='0'*64
    return answer
def tmpfs_facts(tmpfs,selection,place):
    asked={one.split(':',1)[0]:one.split(':',1)[1].split(',') for one in tmpfs if ':' in one};facts={};checked={}
    for index,(name,target) in enumerate(sorted(selection['roots'].items())):
        options=asked.get(target)
        if options is None:continue
        pairs=dict(x.split('=',1) for x in options if '=' in x)
        assert int(pairs['uid'])==selection['uid'] and int(pairs['gid'])==selection['gid'] and int(pairs['mode'],8)==selection['mode'],(name,options)
        facts[place[name]]=dict(mount_id=str(900+index),parent_id='1',device='0:'+str(900+index),root='/',point=place[name],options={x for x in options if '=' not in x},filesystem='tmpfs',super_options={'rw'})
        checked[name]=dict(target=target,operand=options)
    return facts,checked
def run(root,mounts,seen,tmpfs=(),*,role,scenario,packet):
    root=Path(root)
    sys.path[:0]=[str(root/'source/v12/python/src'),str(root/'source/v12/worker'),str(root/'source/v12/python/src/baton_v12')]
    import baton_worker,claude_agent,codex_agent,provider_policy
    import provider_policy.home as home
    from baton_v12.worker_manager import launch
    payload=launch.payload_of(seen);attempt=payload.get('attempt_id') or hashlib.sha256(json.dumps(seen,sort_keys=True).encode()).hexdigest()
    room=root/'simulated'/(role+'-'+str(attempt)[-12:]);room.mkdir(parents=True)
    inputs=Path(mounts['/input']);source=inputs/'source'
    source.chmod(0o700);shutil.copytree(mounts['/input/source'],source,dirs_exist_ok=True)
    homepath=mounts['/run/baton/provider-home'];realcheck,realprepare=home.checked_home,home.prepare;calls=[]
    Agent=codex_agent.CodexAgent if role=='implementation' else claude_agent.ClaudeAgent
    marker_place=root/'source/v12/worker/verifier-layout-marker.json'
    delivered=mounts.get('/run/baton/verifier-layout.json',str(room/'no-layout-delivered.json'))
    place={name:str(room/'verifier'/leaf) for name,leaf in (('HOME','home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('PYTHONPYCACHEPREFIX','pycache'))}
    for one in place.values():Path(one).mkdir(mode=0o700,parents=True)
    real_selected=Agent._selected_layout;layout=dict(selected=None,facts=None,preflights=0)
    def selected(self,*a,**k):
        real=real_selected(self,*a,**k)
        if real is None:return None
        layout['selected']=real;layout['preflights']+=1
        return dict(real,roots=dict(place))
    def facts(*a,**k):
        held,checked=tmpfs_facts(tmpfs,layout['selected'],place);layout['facts']=checked
        return held
    def record(argv,kw,**more):
        (room/'provider-seam.json').write_text(json.dumps(dict(simulation=True,role=role,invocations=len(calls),argv=argv,environment=kw['env'],mount_targets=sorted(mounts),instruction_sha256=hashlib.sha256(provider_policy.worker_instructions()).hexdigest(),layout=dict(delivered_document=json.loads(Path(delivered).read_text()),composed_tmpfs=layout['facts'],preflights_before_provider=layout['preflights']),**more)))
    def provider(argv,**kw):
        if argv[0]=='codex':
            assert role=='implementation'
            if argv[1:]==['--version']:
                os.write(kw['stdout'],b'codex-cli 0.169.0\n');return subprocess.CompletedProcess(argv,0,None,None)
            calls.append(argv)
            assert len(calls)==1 and argv[argv.index('--model')+1]=='gpt-6-astra' and Path(kw['cwd'],'.git').exists()
            assert kw['env']['CODEX_HOME']==str(Path(homepath)/'codex')
            assert layout['selected'] is not None and sorted(layout['facts'])==sorted(place)
            Path(kw['cwd'],'message.txt').write_bytes(b'before\n' if scenario=='no-edit' else b'after\n')
            record(argv,kw)
            os.write(kw['stdout'],FRAMING);return subprocess.CompletedProcess(argv,0,None,None)
        if argv[0]=='claude':
            assert role=='review'
            if argv[1:]==['--version']:
                os.write(kw['stdout'],b'2.1.247 (Claude Code)\n');return subprocess.CompletedProcess(argv,0,None,None)
            calls.append(argv)
            assert len(calls)==1 and argv[argv.index('--model')+1]=='claude-fable-5[1m]'
            assert 'ANTHROPIC_API_KEY' not in kw['env'] and layout['selected'] is not None
            # What the reviewer was given: the frozen checkpoint bound read-only at /input/source.
            given=Path(mounts['/input/source'],'message.txt');candidate=given.read_bytes() if given.is_file() else None
            report=dict(schema='baton.review-uncertainty/1',findings='SIMULATED: cannot substantiate a verdict.') if scenario=='uncertain' else dict(schema='baton.review-report/1',verdict='accepted',findings='SIMULATED: message.txt is after plus newline.')
            # The report path is the one the real review prompt names; never guessed here.
            prompt=argv[-1];target=next((word.rstrip('.,') for word in prompt.split() if word.rstrip('.,').endswith('review-report.json')),None)
            assert target,'review prompt names no report path'
            target=target if os.path.isabs(target) else os.path.join(kw['cwd'],target)
            if scenario!='no-report':Path(target).write_text(json.dumps(report))
            record(argv,kw,candidate_seen=None if candidate is None else candidate.decode(),provider_cwd=kw['cwd'],report_path=target)
            contributors=['unrelated-synthetic-model'] if scenario=='wrong-contributor' else ['claude-fable-5','synthetic-additional-contributor']
            os.write(kw['stdout'],json.dumps(dict(type='result',subtype='success',is_error=False,modelUsage={name:{'outputTokens':1} for name in contributors})).encode())
            return subprocess.CompletedProcess(argv,0,None,None)
        assert argv[0] in ('git','python3'),argv
        return subprocess.run(argv,**kw)
    patches=[mock.patch.object(home,'checked_home',side_effect=lambda path:realcheck(homepath)),mock.patch.object(home,'prepare',side_effect=lambda path,**kw:realprepare(homepath,**kw)),
        mock.patch.dict(os.environ,{'BATON_ATTEMPT_LOG_ROOM':mounts['/run/baton/attempt-logs']}),
        mock.patch.object(Agent,'LAYOUT_MARKER',str(marker_place)),mock.patch.object(Agent,'LAYOUT_DOCUMENT',delivered),mock.patch.object(Agent,'_selected_layout',selected),mock.patch.object(Agent,'_mount_facts',facts),mock.patch.object(Agent,'_proved_ancestors',lambda self,place,facts:None)]
    values=[(baton_worker,'INPUT_ROOT',str(inputs)),(baton_worker,'OUTPUT_ROOT',mounts['/output']),(claude_agent,'INPUT_ROOT',str(inputs)),(claude_agent,'OUTPUT_ROOT',mounts['/output'])]
    if role=='review':
        # The delivered slot is one read-only file bind; give the adapter the directory it expects around it.
        slot=claude_agent.CREDENTIAL_ROOT+'/claude';assert slot in mounts,'no delivered Claude credential mount'
        (room/'credentials').mkdir();os.symlink(mounts[slot],room/'credentials/claude')
        values.append((claude_agent,'CREDENTIAL_ROOT',str(room/'credentials')))
    for module,name,value in values:patches.append(mock.patch.object(module,name,value))
    for one in patches:one.start()
    try:
        agent=Agent(run=provider,home=mounts['/scratch']);original=agent.work
        def traced(*a,**k):
            try:return original(*a,**k)
            except BaseException:
                import traceback;(room/'worker-error.txt').write_text(traceback.format_exc());raise
        agent.work=traced
        status=baton_worker.serve_exchange(agent,payload,payload['session'],mounts['/run/baton/exchange/command'],mounts['/run/baton/exchange/events'])
    finally:
        for one in reversed(patches):one.stop()
    (room/'worker-result.json').write_text(json.dumps(dict(status=status,provider_seam_calls=len(calls),role=role)))
