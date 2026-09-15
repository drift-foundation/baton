import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/sl/src/baton');record=pathlib.Path(__file__).resolve().parent
names=['v12/python/tests/tools/scheduler_trace.py','v12/python/tests/tools/test_scheduler_trace.py']
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
author=json.loads((record/'ledger-153769.json').read_text())
ledger={'work':'W103525','claim':157568,'prior_review_seconds':69.43512828399685,'review_cap_seconds':300,'author_spent_seconds':author['author_spent_seconds'],'author_cap_seconds':600,'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(run['elapsed_seconds'] for run in ledger['runs'])
    ledger['review_remaining_seconds']=300-ledger['review_spent_seconds']
    (record/'review-157568.json').write_text(json.dumps(ledger,indent=2)+'\n')
prefix='tests.tools.test_scheduler_trace.TheComposedOwnersSupplyAuthorizedTransitions.'
selectors=[prefix+name for name in ['test_three_jobs_code_and_are_reviewed_and_the_edge_then_opens','test_the_alternate_schedule_reaches_the_same_completions','test_the_opened_edge_and_one_integrator_serialize_four_jobs']]
for name,argv in [('focused',['/usr/bin/python3','-B','-m','unittest','-v',*selectors]),('probe',['/usr/bin/python3','-B',str(record/'repro-157568.py')])]:
    ledger['pending']={'name':name,'argv':argv};save();log=record/('review-157568-'+name+'.log');start=time.monotonic()
    with log.open('w') as out:
        try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=min(30,ledger['review_remaining_seconds'])).returncode
        except subprocess.TimeoutExpired: rc=124
    ledger['runs'].append({'name':name,'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending');save()
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after'];save()
print(json.dumps({key:ledger[key] for key in ['runs','author_spent_seconds','review_spent_seconds','review_remaining_seconds','candidate_unchanged']},indent=2))
