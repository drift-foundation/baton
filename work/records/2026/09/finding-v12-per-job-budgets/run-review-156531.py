import hashlib, json, os, subprocess, time
from pathlib import Path
root = Path('/home/sl/src/baton')
record = Path(__file__).parent
prior = json.loads((record / 'review-156469.json').read_text())
names = list(prior['candidate_after']) + ['src/baton_v12/worker_manager/launch.py', 'tests/manager/test_execution_limits.py']
def hashes():
    return {n: {'sha256': hashlib.sha256((root / 'v12/python' / n).read_bytes()).hexdigest(), 'bytes': (root / 'v12/python' / n).stat().st_size} for n in names}
ledger = {'work': 'W156162', 'claim': 156531, 'author_spent_seconds': 31.34681991099751, 'author_unmeasured_runs': ['original baseline', 'golden generation'], 'prior_review_seconds': 0.8545903619979072, 'candidate_before': hashes(), 'runs': []}
file = record / 'review-156531.json'
def save():
    ledger['review_spent_seconds'] = ledger['prior_review_seconds'] + sum(r['elapsed_seconds'] for r in ledger['runs'])
    file.write_text(json.dumps(ledger, indent=2) + '\n')
env = dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1')
selectors = ['tests.job_manager.test_execution_limits', 'tests.manager.test_execution_limits', 'tests.manager.test_launch']
for name, argv in [('focused', ['/usr/bin/python3', '-B', '-m', 'unittest', '-v', *selectors]), ('probe', ['/usr/bin/python3', '-B', str(record / 'repro-156531.py')])]:
    ledger['pending'] = {'name': name, 'argv': argv}
    save()
    log = record / ('review-156531-' + name + '.log')
    start = time.monotonic()
    with log.open('w') as out:
        try:
            rc = subprocess.run(argv, cwd=root / 'v12/python', env=env, stdout=out, stderr=subprocess.STDOUT, timeout=30).returncode
        except subprocess.TimeoutExpired:
            rc = 124
    ledger['runs'].append({'name': name, 'argv': argv, 'exit': rc, 'elapsed_seconds': time.monotonic() - start, 'log': log.name})
    ledger.pop('pending')
    save()
ledger['candidate_after'] = hashes()
ledger['candidate_unchanged'] = ledger['candidate_after'] == ledger['candidate_before']
ledger['golden_sha256'] = hashlib.sha256((record / 'golden-schema4-156492.sqlite3').read_bytes()).hexdigest()
save()
print(json.dumps({'runs': ledger['runs'], 'review_spent_seconds': ledger['review_spent_seconds'], 'candidate_unchanged': ledger['candidate_unchanged'], 'golden_sha256': ledger['golden_sha256']}, indent=2))
