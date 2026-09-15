"""Bounded independent review, preserving all prior W103525 spending."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/sl/src/baton')
RECORD = Path(__file__).resolve().parent
OUT = RECORD / 'review-161114.json'
assert not OUT.exists(), 'never overwrite review evidence'
prior = json.loads((RECORD / 'review-160031.json').read_text())
author = json.loads((RECORD / 'ledger-153769.json').read_text())
names = ['v12/python/tests/tools/scheduler_trace.py', 'v12/python/tests/tools/test_scheduler_trace.py']
def hashes():
    return {name: {'sha256': hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), 'bytes': (ROOT / name).stat().st_size} for name in names}
ledger = dict(work='W103525', claim=161114, prior_review_seconds=prior['review_spent_seconds'], review_cap_seconds=300, author_cap_seconds=1200, author_spent_seconds=author['author_spent_seconds'], candidate_before=hashes(), runs=[])
def save():
    ledger['review_spent_seconds'] = ledger['prior_review_seconds'] + sum(r['elapsed_seconds'] for r in ledger['runs'])
    ledger['review_remaining_seconds'] = 300 - ledger['review_spent_seconds']
    OUT.write_text(json.dumps(ledger, indent=2) + '\n')

# Reuse the prior observer wrapper, but independently demand every terminal
# Job in the current candidate. This only writes a NEW reviewer probe.
probe = (RECORD / 'repro-160031.py').read_text().replace('160031', '161114').replace('len(terminals)==2', 'len(terminals)==4')
(RECORD / 'repro-161114.py').write_text(probe)
argv = ['/usr/bin/python3', '-B', str(RECORD / 'repro-161114.py')]
save()
fresh = json.loads(OUT.read_text())
spent = fresh['prior_review_seconds'] + sum(r['elapsed_seconds'] for r in fresh['runs'])
remaining = 300 - spent
expected, margin, timeout = 14, 4, min(25, remaining - 4)
assert expected + margin < remaining and expected < timeout < remaining
operands = dict(cap_seconds=300, starting_spent_seconds=spent, starting_remaining_seconds=remaining, expected_seconds=expected, margin_seconds=margin, timeout_seconds=timeout)
ledger['pending'] = dict(argv=argv, budget=operands)
save()  # Persist operands BEFORE starting the child.
start = time.monotonic()
with (RECORD / 'review-161114-probe.log').open('w') as out:
    try:
        rc = subprocess.run(argv, cwd=ROOT / 'v12/python', env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1'), stdout=out, stderr=subprocess.STDOUT, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        rc = 124
ledger['runs'].append(dict(argv=argv, budget=operands, exit=rc, elapsed_seconds=time.monotonic() - start, log='review-161114-probe.log'))
del ledger['pending']
ledger['candidate_after'] = hashes()
ledger['candidate_unchanged'] = ledger['candidate_before'] == ledger['candidate_after']
save()
print(json.dumps(ledger, indent=2))
