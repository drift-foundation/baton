"""Bind independent C2 receipts and reconstruct the reviewed patch."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

R = Path(__file__).resolve().parent
ROOT = R.parents[4]
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
    return {'path': str(p.relative_to(ROOT)), 'sha256': sha(p)}
c = json.loads((R / 'CANDIDATE-182279.json').read_text())
start = time.monotonic()
with tempfile.TemporaryDirectory(prefix='baton-c2-review-182379-') as directory:
    for row in c['files']:
        p = Path(directory) / row['path']
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / row['base_snapshot']).read_bytes())
    process = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(ROOT / c['patch']['path'])], cwd=directory, capture_output=True, text=True, timeout=10)
    assert process.returncode == 0, process.stderr
    assert 'offset' not in process.stdout and 'fuzz' not in process.stdout
    assert all(sha(Path(directory) / row['path']) == row['sha256'] for row in c['files'])
audit_seconds = time.monotonic() - start
runs = []
for selector in ('CountedReopen', 'CountedReopenInvalidEvidence', 'UsefulCorrection', 'UsefulCorrectionInvalidEvidence'):
    p = R / ('review-182379-' + selector + '.json')
    receipt = json.loads(p.read_text())
    trace = R / ('review-182379-' + selector + '-trace.json')
    assert sha(trace) == receipt['trace_sha256']
    assert receipt['status'] == 0 and receipt['source_stable'] and receipt['group_gone'] and not receipt['timeout']
    runs.append({'receipt': ref(p), 'trace': ref(trace), 'log': ref(R / ('review-182379-' + selector + '.log')), 'selector': selector, 'seconds': receipt['seconds'], 'provenance_checks': len(receipt['provenance'])})
observed = json.loads((R / 'review-182379-CountedReopen-trace.json').read_text())
boundary = observed['reopen']
first, second = (observed[key]['binding']['attempt_id'] for key in ('initial', 'revised'))
counts = {}
for name in ('provider', 'engine'):
    counts[name] = {key: len([x for x in boundary[key][name] if x['attempt_id'] == first]) for key in ('before', 'after', 'observed')}
    counts[name].update(final_old=len([x for x in observed['final_counters'][name] if x['attempt_id'] == first]), final_new=len([x for x in observed['final_counters'][name] if x['attempt_id'] == second]))
    assert set(counts[name].values()) == {1}
negative = json.loads((R / 'review-182379-CountedReopenInvalidEvidence-trace.json').read_text())
assert len(negative['rejections']) == 15
c1negative = json.loads((R / 'review-182379-UsefulCorrectionInvalidEvidence-trace.json').read_text())
assert len(c1negative['rejections']) == 13
seconds = sum(r['seconds'] for r in runs)
result = {'work': 'W180252', 'claim': 182379, 'candidate': ref(R / 'CANDIDATE-182279.json'), 'author_evidence': ref(R / 'EVIDENCE-182279.json'), 'review_scripts': [ref(Path(__file__)), ref(R / 'review-run-182379.py')], 'runs': runs, 'tests_passed': 15, 'C2_invalid_copies': 15, 'C1_invalid_copies': 13, 'patch_reconstructed': True, 'patch_audit_seconds': audit_seconds, 'patch_stdout': process.stdout, 'reviewer_seconds': seconds, 'prior_reviewer_seconds': 104.8836736070516, 'cumulative_reviewer_seconds': 104.8836736070516 + seconds, 'author_seconds_separate': 234.30053109725122, 'counts': counts, 'ticks': observed['ticks'], 'boundary_ticks': [boundary['before_tick'], boundary['after_tick']], 'incarnations': boundary['incarnations'], 'runtime_before': boundary['runtime_before'], 'final_state': observed['final']['state'], 'managed_state': observed['managed']['state'], 'target_revision': observed['target']['revision'], 'limit': 'Manager recomposition in one process after durable result; deterministic provider child, simulated OCI. No host/power-loss or live provider qualification.'}
with (R / 'REVIEW-EVIDENCE-182379.json').open('x') as out:
    json.dump(result, out, indent=2)
    out.write('\n')
print(json.dumps(result, indent=2))
print('evidence_sha256=' + sha(R / 'REVIEW-EVIDENCE-182379.json'))
