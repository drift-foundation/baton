import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent;root=pathlib.Path('/home/sl/src/baton')
previous=json.loads((record/'review-157602.json').read_text());names=list(previous['candidate_after'])
author=json.loads((record/'ledger-156316.json').read_text())
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
ledger={'work':'W156162','claim':157715,'author_spent_seconds':author['spent_seconds'],'author_measured_runs':len(author['runs']),'author_unmeasured_activities':previous['author_unmeasured_activities'],'prior_review_seconds':previous['review_spent_seconds'],'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(run['elapsed_seconds'] for run in ledger['runs'])
    (record/'review-157715.json').write_text(json.dumps(ledger,indent=2)+'\n')
prefix='tests.tools.test_execution_limits.'
selectors=[prefix+name for name in ['TheHostSideVerificationCarriesTheSameCeiling','TheComposedHostVerificationUsesTheJobsCeiling']]
for label,argv in [('focused',['/usr/bin/python3','-B','-m','unittest','-v',*selectors]),('memo',['/usr/bin/python3','-B',str(record/'repro-157715-memo.py')]),('readonly',['/usr/bin/python3','-B',str(record/'repro-157715-readonly.py')])]:
    ledger['pending']=argv;save();log=record/('review-157715-'+label+'.log');start=time.monotonic()
    with log.open('w') as out:
        try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=30).returncode
        except subprocess.TimeoutExpired: rc=124
    ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending');save()
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after'];save()
print(json.dumps({key:ledger[key] for key in ('runs','author_spent_seconds','author_measured_runs','review_spent_seconds','candidate_unchanged')},indent=2))
