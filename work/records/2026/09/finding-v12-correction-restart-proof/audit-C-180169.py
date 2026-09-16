"""Read-only triage of retained C failure and immutable input inventory."""
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
checks = []
def check(path, expected, mode=None):
    info = path.lstat()
    actual = sha(path)
    match = stat.S_ISREG(info.st_mode) and actual == expected and (mode is None or oct(stat.S_IMODE(info.st_mode)) == mode)
    checks.append({'path': str(path.relative_to(ROOT)), 'sha256': actual, 'match': match})
    assert match, path
check(HERE / 'EVIDENCE-C-180069.json', '6f25ed30f1bb28474465262795cf3165cc089a3b16101c6199f89ebb9b2f6e14')
evidence = json.loads((HERE / 'EVIDENCE-C-180069.json').read_bytes())
for path, expected in evidence['artifacts'].items():
    check(HERE / path, expected)
baseline = json.loads((HERE / 'BASE-C-180069.json').read_bytes())
for row in baseline['read_only_inputs']:
    check(ROOT / row['path'], row['sha256'], row['mode'])
for row in evidence['partial_files']:
    check(ROOT / row['path'], row['sha256'], row['mode'])
    check(ROOT / row['snapshot'], row['sha256'])
for path, expected in evidence['static_source_hashes_after_run'].items():
    check(ROOT / path, expected)
raw = json.loads((HERE / 'OBSERVATION-C-180069.json').read_bytes())['observation']
log = (HERE / 'run-C-180069-5.log').read_text()
start = log.index('AssertionError: ') + len('AssertionError: ')
parsed, end = json.JSONDecoder().raw_decode(log[start:])
assert parsed == raw
assert len(raw['retained']) == 1
retained = next(iter(raw['retained'].values()))
account = retained['prepared']['preparation']['report']
completed = {row['name']: row['status'] for row in account['completed']}
assert completed == {'combined': 0, 'base': 1, 'isolated': 0}
assert account['kind'] == 'measured' and account['status'] == 1 and account['not_run'] == []
assert retained['state'] == 'blocked' and retained['reason'] == 'the retained preparation did not pass its combined command'
report = {'work': 'W161234', 'claim': 180169, 'kind': 'static evidence/source triage; no test or provider execution', 'checks': checks, 'verbatim_log_observation_match': True, 'observed_completed': completed, 'observed_aggregate': account['status'], 'observed_state': retained['state'], 'observed_reason': retained['reason'], 'new_reviewer_runtime_seconds': 0, 'cumulative_reviewer_seconds': 93.48170357503113, 'cumulative_author_seconds': 162.0071183030086, 'current_source_findings': {'report_composer': 'v12/worker/reconciliation_task.py:compose_report', 'actual_adoption_symbol': 'v12/python/src/baton_v12/integration/reconciliation.py:adopt_prepared_candidate', 'aggregate_contract_test': 'v12/python/tests/manager/test_reconciliation_task.py:test_a_genuine_base_failure_is_a_real_integer'}, 'not_claimed': ['complete C candidate', 'managed target/final receipt', 'duplicate rejection', 'runtime reproduction by reviewer', 'source correction', 'whole Work acceptance']}
with (HERE / 'TRIAGE-C-180169.json').open('x') as out:
    json.dump(report, out, indent=2)
    out.write('\n')
print(json.dumps({'checks': len(checks), 'match': True, 'completed': completed, 'aggregate': account['status']}))
