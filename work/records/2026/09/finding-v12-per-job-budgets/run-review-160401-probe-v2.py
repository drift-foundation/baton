import hashlib, json, os, pathlib, subprocess, time
record = pathlib.Path(__file__).resolve().parent
root = pathlib.Path('/home/sl/src/baton')
ledger = json.loads((record / 'review-160401.json').read_text())
argv = ['/usr/bin/python3', '-B', str(record / 'repro-160401-v2.py')]
log = record / 'review-160401-probe-v2.log'
start = time.monotonic()
with log.open('w') as out:
    try:
        rc = subprocess.run(argv, cwd=root / 'v12/python', env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1'), stdout=out, stderr=subprocess.STDOUT, timeout=20).returncode
    except subprocess.TimeoutExpired:
        rc = 124
ledger['runs'].append({'argv': argv, 'exit': rc, 'elapsed_seconds': time.monotonic() - start, 'log': log.name})
ledger['review_spent_seconds'] = ledger['prior_review_seconds'] + sum(run['elapsed_seconds'] for run in ledger['runs'])
ledger['candidate_after'] = {name: {'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest(), 'bytes': (root / name).stat().st_size} for name in ledger['candidate_before']}
ledger['candidate_unchanged'] = ledger['candidate_before'] == ledger['candidate_after']
(record / 'review-160401.json').write_text(json.dumps(ledger, indent=2) + '\n')
print(json.dumps({key: ledger[key] for key in ('runs', 'review_spent_seconds', 'candidate_unchanged')}, indent=2))
