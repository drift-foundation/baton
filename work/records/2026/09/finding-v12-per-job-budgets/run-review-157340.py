import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent
root=pathlib.Path('/home/sl/src/baton')
names=list(json.loads((record/'review-157207.json').read_text())['candidate_after'])
author=json.loads((record/'ledger-156316.json').read_text())
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
ledger={'work':'W156162','claim':157340,'author_spent_seconds':author['spent_seconds'],'author_measured_runs':len(author['runs']),'author_unmeasured_activities':['original baseline','golden generation','isolated-copy attribution attempt','in-place injection-removal attribution experiment'],'prior_review_seconds':8.404963404997034,'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(run['elapsed_seconds'] for run in ledger['runs'])
    (record/'review-157340.json').write_text(json.dumps(ledger,indent=2)+'\n')
for label,argv in [('focused',['/usr/bin/python3','-B','-m','unittest','-v','tests.tools.test_execution_limits']),('probe',['/usr/bin/python3','-B',str(record/'repro-157340.py')])]:
    ledger['pending']=argv;save()
    log=record/('review-157340-'+label+'.log');start=time.monotonic()
    with log.open('w') as out:
        try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=30).returncode
        except subprocess.TimeoutExpired: rc=124
    ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending');save()
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after'];save()
print(json.dumps({key:ledger[key] for key in ('runs','author_spent_seconds','review_spent_seconds','candidate_unchanged')},indent=2))
