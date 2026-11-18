#!/usr/bin/env python3
"""Owner closure helper; default checks only. --close closes accepted children then parent. No Git writes."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
BASE = ['/home/sl/opt/baton/v11/0650c61/bin/baton', '--config', '/home/sl/baton-v11.14aecfb/baton.json', '--participant', 'baton.slaw']
WORKS = ['W384944', 'W385124', 'W384870']
HEAD = 'f896bab03925ff1eb520adc3283da265137d5130'
def call(*args):
    return json.loads(subprocess.check_output(BASE + list(args), text=True))
def detail(work):
    return call('detail', 'work='+work)['result']
if sys.argv[1:] not in ([], ['--close']):
    raise SystemExit('usage: owner-close-w384870.py [--close]')
if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip() != HEAD:
    raise SystemExit('Refusing changed checkpoint')
if subprocess.check_output(['git', 'status', '--porcelain', '--', 'v12'], cwd=REPO, text=True).strip():
    raise SystemExit('Refusing dirty v12 source')
ledger = json.loads((HERE/'evidence/final-suite-20261118-r4/test-all.summary.json').read_text())
if ledger.get('ok') is not True or len(ledger['collected']) != 11277:
    raise SystemExit('Refusing missing accepted full-suite ledger')
for work in WORKS:
    state = detail(work)
    if state['status'] == 'closed':
        print(work, 'already closed'); continue
    handler = state.get('handler') or {}
    if state['route']['endpoint'] != 'baton.decide' or handler.get('participant') not in (None, 'baton.slaw') or state['open_blockers']:
        raise SystemExit('Refusing changed owner/route/blockers: '+work)
    children = {x['id'].split('-')[-1] for x in state['links']['contains'] if x['status'] == 'open'}
    if not children.issubset(set(WORKS)-{work}):
        raise SystemExit('Refusing additional unfinished child: '+work)
    print(work, state['phase'], handler.get('participant'))
if not sys.argv[1:]:
    print('Checks passed. Owner may run with --close.'); raise SystemExit(0)
receipts = []
for work in WORKS:
    state = detail(work)
    if state['status'] == 'closed':
        receipts.append({'work': work, 'readback': state}); continue
    if state.get('handler') is None:
        receipts.append(call('claim', 'work='+work))
    receipts.append(call('close', 'work='+work, 'outcome=satisfying', 'rationale=Independently accepted W384870 delivery: final r4 at f896bab0 accounts for11277 tests,11275 passed and2 approved optional skips,zero adverse outcomes,stable source,zero residue. B4 and signal-order review delivered; durable parent final acceptance review records evidence.', 'op-id=owner-final-close-'+work+'-f896bab0'))
    state = detail(work)
    if state['status'] != 'closed' or state.get('handler') is not None:
        raise SystemExit('Closure readback failed: '+work)
    receipts.append({'work': work, 'readback': state})
    (HERE/'OWNER-CLOSURE-RECEIPTS.json').write_text(json.dumps(receipts, indent=2)+'\n')
print('Both children and W384870 closed. Commit final dossier evidence and receipts.')
