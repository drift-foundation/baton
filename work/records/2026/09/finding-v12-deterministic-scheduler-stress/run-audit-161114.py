"""Append one bounded artifact audit to the current cumulative review ledger."""
import json
import os
from pathlib import Path
import subprocess
import time

record = Path(__file__).resolve().parent
path = record/'review-161114.json'
ledger = json.loads(path.read_text())
assert not ledger.get('pending')
assert not any(r.get('name') == 'artifact-audit' for r in ledger['runs'])
spent = ledger['prior_review_seconds'] + sum(r['elapsed_seconds'] for r in ledger['runs'])
remaining = ledger['review_cap_seconds'] - spent
budget = dict(cap_seconds=300, starting_spent_seconds=spent, starting_remaining_seconds=remaining, expected_seconds=1, margin_seconds=2, timeout_seconds=5)
assert 3 < remaining and 5 < remaining
argv = ['/usr/bin/python3', '-B', str(record/'audit-161114.py')]
ledger['pending'] = dict(name='artifact-audit', argv=argv, budget=budget)
path.write_text(json.dumps(ledger,indent=2)+'\n')
start = time.monotonic()
with (record/'audit-161114.log').open('w') as out:
    try:
        rc = subprocess.run(argv, cwd='/home/sl/src/baton/v12/python', env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'), stdout=out, stderr=subprocess.STDOUT, timeout=5).returncode
    except subprocess.TimeoutExpired:
        rc = 124
ledger['runs'].append(dict(name='artifact-audit', argv=argv,budget=budget,exit=rc,elapsed_seconds=time.monotonic()-start,log='audit-161114.log'))
del ledger['pending']
ledger['review_spent_seconds'] = ledger['prior_review_seconds'] + sum(r['elapsed_seconds'] for r in ledger['runs'])
ledger['review_remaining_seconds'] = 300-ledger['review_spent_seconds']
path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({k:ledger[k] for k in ['runs','review_spent_seconds','review_remaining_seconds']},indent=2))
