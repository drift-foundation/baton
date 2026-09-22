"""Read-only private-evidence assessment; outputs closed facts and digests only."""
import importlib.util, json, os, time
from pathlib import Path
start = time.monotonic()
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('isolated', here/'diagnostic-235602/isolated_canary.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
approved = 'a9e1c97bd20c5cb85b556e91488f3c0e6ecc07fd6a2636d330666c144bee918e'
q.audit(approved)
r = q.ROOT
def doc(name): return q.decoded(q.read(r/name))
def check(value, reason): q.require(value, reason)
b = doc('binding.json'); completion = doc('completion.json')
check(b['work']=='W177936' and b['run']==q.RUN and b['manifest']==approved and b['identity_kind']=='qualification-fixture' and b['attempts']==[q.RUN+'-turn-1',q.RUN+'-turn-2'], 'binding')
check(completion['outcome']=='failed' and completion['manifest']==approved and completion['interrupted'] is False and completion['elapsed_seconds']<600, 'completion')
check(completion['cleanup']==[{'attempt':q.RUN+'-turn-'+str(t),'confirmed':True} for t in (1,2)], 'cleanup')
check(doc('failure.json')=={'outcome':'failed','code':'mixed-model-set'}, 'failure')
session=b['session']; requests=[doc('request-'+str(t)+'.json') for t in (1,2)]
token=requests[0]['prompt'].split(': ',1)[1].split('.',1)[0]
check(requests[0]['prompt']==q.prompt(1,token) and requests[1]['prompt']==q.prompt(2) and token not in requests[1]['prompt'], 'prompt')
state=q.read(r/'selected-session.jsonl',q.STATE_LIMIT)
check(doc('transfer.json')=={'path':q.session_path(session),'sha256':q.sha(state),'bytes':len(state),'source_attempt':q.RUN+'-turn-1','target_attempt':q.RUN+'-turn-2','only_session_copied':True}, 'transfer')
check(q.session_bytes(r/'turn-1/home',session)==state,'source-state')
rows=[]; runtimes=[]; ids=[]
for turn,request in enumerate(requests,1):
    check(request['run']==q.RUN and request['session']==session and request['turn']==turn and request['attempt']==q.RUN+'-turn-'+str(turn),'request')
    before=doc('runtime-before-'+str(turn)+'.json'); after=doc('runtime-after-'+str(turn)+'.json'); intent=doc('intent-'+str(turn)+'.json'); place=r/('turn-'+str(turn))
    home={'.claude':'directory','.claude/.credentials.json':'credential-slot'}
    if turn==2: home.update({'.claude/projects':'directory','.claude/projects/-output':'directory',q.session_path(session):q.sha(state)})
    check(doc('initial-home-'+str(turn)+'.json')==home,'initial-home')
    args,mounts=q.vector(place,r/('request-'+str(turn)+'.json'),q.SLOTS/('slot-'+str(turn)),turn,os.getuid(),os.getgid())
    check(intent['argv_digest']==q.sha(q.encoded(args)) and intent['mounts']==[[str(p),t,v] for p,t,v in mounts],'intent')
    q.validate_runtime(before,before['Id'],mounts,turn,os.getuid(),os.getgid()); q.validate_runtime(after,before['Id'],mounts,turn,os.getuid(),os.getgid()); q.stopped(after)
    check(before['State']['Status']=='created' and before['State']['Running'] is False and before['State']['Pid']==0,'initial-runtime')
    ids.append(before['Id']); runtimes.append(after)
    wire=q.read(r/('worker-wire-'+str(turn)+'.json'),q.TRANSPORT_LIMIT)
    envelope,streams=q.worker_records(wire,turn,session)
    check(q.decoded(q.read(r/('worker-output-'+str(turn)+'.json'),q.TRANSPORT_LIMIT),q.TRANSPORT_LIMIT)==envelope,'worker-envelope')
    check(len(envelope['processes'])==2 and all(p['reason']=='ok' and p['exit_code']==0 for p in envelope['processes']),'process-status')
    check(streams[0][0].strip()==(q.CLI+' (Claude Code)').encode(),'version')
    raw=q.read(r/('provider-'+str(turn)+'.json'))
    check(raw==streams[1][0]==q.read(r/('provider-'+str(turn)+'.stdout')) and streams[1][1]==q.read(r/('provider-'+str(turn)+'.stderr')),'retained-streams')
    value=q.decoded(raw); c=q.contract(); projection=c.projection(raw,session)
    check(c.valid_terminal(projection,session) and c.success(projection),'successful-session')
    if turn==1: q.terminal(raw,session,'READY')
    else: check(value.get('result')=='RECALL: '+token,'meaningful-recall-single-space')
    for name in ('input','source','workspace'): check(not list((place/name).iterdir()),'task-roots')
    check(not os.path.lexists(q.SLOTS/('slot-'+str(turn))),'slot-present')
    rows.append({'turn':turn,'successful_matching_session':True,'provider_sha256':q.sha(raw),'exit_code':0,'usage_exact_original_pair':set(value.get('modelUsage',{}))==set(q.MODEL_ACCEPTANCE['usage_models']),'usage_opus_only':set(value.get('modelUsage',{}))=={q.MODEL},'direct_model_absent':'model' not in value})
check(ids[0]!=ids[1],'worker-reuse')
check(runtimes[0]['State']['FinishedAt']<runtimes[1]['State']['StartedAt'],'execution-overlap')
try: q.review(r,approved)
except q.Refusal as e: check(str(e)=='incomplete-run','original-review-reason')
else: raise RuntimeError('original-review-unexpected-pass')
result={'schema':'baton.independent-resume-assessment/1','work':'W177936','claim':235998,'manifest':approved,'original_outcome':'failed','original_failure':'mixed-model-set','original_reviewer_still_refuses':'incomplete-run','live_elapsed_seconds':completion['elapsed_seconds'],'turns':rows,'actual_canary_recalled':True,'second_prompt_excludes_canary':True,'exact_original_answer_format':False,'format_deviation':'one ASCII space after RECALL:; no other extra text','session_only_initial_transfer_verified':True,'distinct_isolated_workers':True,'first_stopped_before_second_started':True,'retained_both_stopped_exit0':True,'recorded_cleanup_both_confirmed':True,'credential_slots_currently_absent':True,'current_engine_absence_independently_queried':False,'production_certification':False,'state_sha256':q.sha(state),'private_evidence_hashes':{p.name:q.sha(q.read(p,q.TRANSPORT_LIMIT)) for p in sorted(r.glob('*.json'))},'offline_elapsed_seconds':time.monotonic()-start}
print(json.dumps(result,indent=2,sort_keys=True))
