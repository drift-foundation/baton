import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent;root=pathlib.Path('/home/sl/src/baton')
path=record/'review-157661.json';ledger=json.loads(path.read_text())
argv=['/usr/bin/python3','-B',str(record/'repro-157661-v2.py')]
ledger['pending']={'name':'probe-v2','argv':argv};path.write_text(json.dumps(ledger,indent=2)+'\n')
start=time.monotonic();log=record/'review-157661-probe-v2.log'
with log.open('w') as out:
    try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=10).returncode
    except subprocess.TimeoutExpired: rc=124
ledger['runs'].append({'name':'probe-v2','argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending')
ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(run['elapsed_seconds'] for run in ledger['runs'])
ledger['review_remaining_seconds']=300-ledger['review_spent_seconds']
ledger['candidate_after']={name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in ledger['candidate_before']}
ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after']
path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({key:ledger[key] for key in ('runs','review_spent_seconds','review_remaining_seconds','candidate_unchanged')},indent=2))
