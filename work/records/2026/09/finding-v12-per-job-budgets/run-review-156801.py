import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).parent
root=pathlib.Path('/home/sl/src/baton/v12/python')
names=list(json.loads((record/'review-156751.json').read_text())['candidate_after'])+['tools/stage_execution.py','tests/tools/test_single_worker.py']
def hashes():
    return {n:{'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest(),'bytes':(root/n).stat().st_size} for n in names}
ledger={'work':'W156162','claim':156801,'author_spent_seconds':76.93585512199752,'prior_review_seconds':2.9007430729961925,'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(r['elapsed_seconds'] for r in ledger['runs'])
    (record/'review-156801.json').write_text(json.dumps(ledger,indent=2)+'\n')
argv=['/usr/bin/python3','-B',str(record/'repro-156801.py')]
ledger['pending']=argv;save()
log=record/'review-156801-proposed-fixture.log';start=time.monotonic()
with log.open('w') as out:
    try: rc=subprocess.run(argv,cwd=root,env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=45).returncode
    except subprocess.TimeoutExpired: rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending')
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_after']==ledger['candidate_before'];save()
print(json.dumps({'runs':ledger['runs'],'review_spent_seconds':ledger['review_spent_seconds'],'candidate_unchanged':ledger['candidate_unchanged']},indent=2))
