"""Independent local probes; no engine or installed-instance execution."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import time
from unittest import mock

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'v12/python'), str(ROOT / 'v12/python/src')]
from tools import bootstrap
from baton_v12.job_manager import manager
from baton_v12.source_profiles.checkout import ProfileRefusal


def main():
    started = time.monotonic()
    evidence = json.loads((HERE / 'EVIDENCE-200254.json').read_text())
    hashes = {p: {'expected': digest, 'actual': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()} for p, digest in evidence['candidate'].items()}
    document = json.loads((HERE / 'instance-200254/bootstrap_inputs.json').read_text())
    second = copy.deepcopy(document['jobs'][0])
    second.update(job_id='review-only-conflict', work_id='00000000-W2', line_declared_base='b' * 40)
    document['jobs'].append(second)
    with mock.patch.object(bootstrap, '_compose') as compose:
        opener = mock.Mock(side_effect=AssertionError('must not open'))
        try:
            bootstrap.prepare(document, opener=opener, stream=io.StringIO())
        except bootstrap.BootstrapRefusal as exc:
            preflight = {'refusal': str(exc), 'opener_calls': opener.call_count, 'compose_calls': compose.call_count}
        else:
            raise AssertionError('conflicting bases accepted')
    assert preflight['opener_calls'] == preflight['compose_calls'] == 0
    intent = {'stage_id': 'probe/review', 'episode': 1, 'attempt_id': 'prior-attempt', 'job_id': 'probe'}
    operations = mock.Mock()
    operations.conclude.side_effect = ProfileRefusal('review probe: checkpoint unavailable')
    with mock.patch.object(manager.ending, 'pending_endings', return_value=[intent]), mock.patch.object(manager.ending, 'attempt_of', return_value=intent), mock.patch.object(manager.submission, 'job_of', return_value={}), mock.patch.object(manager, '_defer') as defer:
        try:
            manager._recover_endings(None, operations, [])
        except ProfileRefusal as exc:
            recovery = {'escaped_type': type(exc).__name__, 'message': str(exc), 'defer_calls': defer.call_count}
        else:
            raise AssertionError('expected current recovery defect was not reproduced')
    dest = Path('/home/sl/baton-v12-lifecycle-200254')
    status_path = dest / 'state/status.json'
    snapshot = json.loads(status_path.read_text())
    job = next(j for j in snapshot['jobs'] if j['job_id'] == 'w197661-lifecycle')
    log = (dest / 'state/manager.log').read_text()
    report = json.loads(log[log.index('{'):])
    summary = {'observed_at': snapshot['observed_at'], 'canonical': snapshot['canonical'], 'submission_id': job['submission_id'], 'stages': [{k: stage[k] for k in ('kind', 'state', 'attempt_id', 'deferral')} for stage in job['stages']], 'started': report['started']}
    assert [s['state'] for s in job['stages']] == ['completed', 'completed', 'claimed']
    assert 'no verification command' in report['started'][0]['detail']['message']
    result = {'claim': 200453, 'participant': 'baton.rvpc', 'candidate_hashes': hashes, 'hashes_match': all(v['expected'] == v['actual'] for v in hashes.values()), 'bootstrap_preflight': preflight, 'recovered_profile_refusal': recovery, 'retained_status': summary, 'retained_files': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (status_path, dest / 'state/manager.log')}, 'seconds': time.monotonic() - started}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
