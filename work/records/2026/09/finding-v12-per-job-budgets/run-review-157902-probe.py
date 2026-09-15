import json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent
ledger=json.loads((record/'review-157902.json').read_text())
argv=['/usr/bin/python3','-B',str(record/'repro-157902.py')]
log=record/'repro-157902.log'
start=time.monotonic()
with log.open('w') as out:
    try:
        rc=subprocess.run(argv,cwd='/home/sl/src/baton/v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=15).returncode
    except subprocess.TimeoutExpired:
        rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name})
ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(one['elapsed_seconds'] for one in ledger['runs'])
(record/'review-157902.json').write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'run':ledger['runs'][-1],'review_spent_seconds':ledger['review_spent_seconds']},indent=2))
