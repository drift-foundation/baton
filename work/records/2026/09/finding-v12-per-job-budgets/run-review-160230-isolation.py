import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent;root=pathlib.Path('/home/sl/src/baton')
ledger=json.loads((record/'review-160230.json').read_text())
names=list(ledger['candidate_before'])
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
argv=['/usr/bin/python3','-B',str(record/'repro-160230.py')];log=record/'review-160230-isolation.log';start=time.monotonic()
with log.open('w') as out:
    try:rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=20).returncode
    except subprocess.TimeoutExpired:rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name})
ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(one['elapsed_seconds'] for one in ledger['runs'])
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after']
(record/'review-160230.json').write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({name:ledger[name] for name in ('runs','review_spent_seconds','author_spent_seconds','author_measured_runs','candidate_unchanged')},indent=2))
