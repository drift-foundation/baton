import hashlib, json, os, subprocess, time
from pathlib import Path
root = Path('/home/sl/src/baton')
record = Path(__file__).parent
names = list(json.loads((record / 'review-156643.json').read_text())['candidate_after']) + ['tools/single_worker.py']
def hashes():
    return {n: {'sha256': hashlib.sha256((root / 'v12/python' / n).read_bytes()).hexdigest(), 'bytes': (root / 'v12/python' / n).stat().st_size} for n in names}
ledger = {'work': 'W156162', 'claim': 156751, 'author_spent_seconds': 54.22697624999637, 'author_unmeasured_runs': ['original baseline', 'golden generation'], 'prior_review_seconds': 1.9866033189973678, 'candidate_before': hashes(), 'runs': []}
def save():
    ledger['review_spent_seconds'] = ledger['prior_review_seconds'] + sum(r['elapsed_seconds'] for r in ledger['runs'])
    (record / 'review-156751.json').write_text(json.dumps(ledger, indent=2) + '\n')
env = dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1')
argv = ['/usr/bin/python3', '-B', str(record / 'repro-156751.py')]
ledger['pending'] = {'name': 'proposed-fixture', 'argv': argv}
save()
log = record / 'review-156751-proposed-fixture.log'
start = time.monotonic()
with log.open('w') as out:
    try:
        rc = subprocess.run(argv, cwd=root / 'v12/python', env=env, stdout=out, stderr=subprocess.STDOUT, timeout=30).returncode
    except subprocess.TimeoutExpired:
        rc = 124
ledger['runs'].append({'name': 'proposed-fixture', 'argv': argv, 'exit': rc, 'elapsed_seconds': time.monotonic() - start, 'log': log.name})
ledger.pop('pending')
ledger['candidate_after'] = hashes()
ledger['candidate_unchanged'] = ledger['candidate_after'] == ledger['candidate_before']
save()
print(json.dumps({'runs': ledger['runs'], 'review_spent_seconds': ledger['review_spent_seconds'], 'candidate_unchanged': ledger['candidate_unchanged']}, indent=2))
