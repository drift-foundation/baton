"""Read existing owner failure facts and closed adapter diagnostics; never settle.

The exchange owner already validates the sequence, manifest and assignment.
Additional current-stage checks prevent stale or foreign evidence attribution.
Diagnostics are supplementary: published adapter reports cannot decide failure.
"""
import json
import os
from pathlib import Path
import stat
from urllib.parse import urlsplit

from baton_v12.worker_manager.exchange import FAULT_CODES


def first_failure(status, *, authority_uuid, incarnation, works):
    if not status or status.get('schema') != 'baton.v12.job-status/4' or status.get('canonical') is not True or status.get('incarnation') != incarnation:
        return None
    for job in status.get('jobs', []):
        name = {'job-a': 'a', 'job-b': 'b'}.get(job.get('job_id'))
        if name is None or job.get('submission_id') != incarnation:
            continue
        for stage in job.get('stages', []):
            kind = stage.get('kind')
            if kind not in ('implementation', 'review') or stage.get('job_id') != job['job_id'] or stage.get('stage_id') != job['job_id'] + '/' + kind or stage.get('work_id') != works[name]:
                continue
            attempt, episode = stage.get('attempt_id'), stage.get('episode')
            allocation = stage.get('allocation') or {}
            runtime = stage.get('runtime') or {}
            assignment = runtime.get('assignment') or {}
            reference = assignment.get('work_ref') or {}
            if not isinstance(attempt, str) or not attempt.startswith('attempt-') or type(episode) is not int or episode < 1:
                continue
            if allocation.get('assignment_id') != attempt or allocation.get('stage_id') != stage['stage_id'] or allocation.get('episode') != episode:
                continue
            if reference != {'authority_uuid': authority_uuid, 'work_id': works[name]} or assignment.get('participant') != allocation.get('participant'):
                continue
            # Allocation generation is configuration generation, not the
            # Authority assignment generation. Bind to the actual claim receipt.
            if not any(row.get('act') == 'claim' and row.get('state') == 'performed' and row.get('episode') == episode and row.get('stage_id') == stage['stage_id'] and ((row.get('detail') or {}).get('result') or {}).get('assignment') == assignment for row in stage.get('receipts', [])):
                continue
            if not any(row.get('attempt_id') == attempt and row.get('episode') == episode and row.get('incarnation') == incarnation and row.get('ended_at') is None for row in stage.get('episodes', [])):
                continue
            exchange = stage.get('exchange') or {}
            terminal = exchange.get('terminal') or {}
            command = exchange.get('command') or {}
            ending = terminal.get('ending')
            if exchange.get('foreign') or exchange.get('unreadable') or not exchange.get('receipt') or not exchange.get('sequence_id') or command.get('sequence_id') != exchange['sequence_id'] or command.get('operations') != ['describe', 'work'] or exchange.get('state') != ending:
                continue
            disposition, fault = terminal.get('disposition'), terminal.get('fault_code')
            answered_failure = ending == 'answered' and terminal.get('answered') == ['describe', 'work'] and disposition in ('unable', 'cancelled', 'plan-rejected') and not (kind == 'review' and disposition == 'plan-rejected')
            if not (answered_failure or ending == 'lost' or ending == 'faulted' and fault in FAULT_CODES):
                continue
            return {'job_id': job['job_id'], 'stage_id': stage['stage_id'], 'kind': kind,
                    'work_id': works[name], 'attempt_id': attempt, 'episode': episode,
                    'assignment': assignment, 'runtime_id': runtime.get('runtime_id'),
                    'sequence_id': exchange['sequence_id'], 'ending': ending,
                    'disposition': disposition if answered_failure else None,
                    'fault_code': fault if ending == 'faulted' else None,
                    'manifest_digest': terminal.get('manifest_digest'),
                    'observed_at': status.get('observed_at'),
                    'artifacts': stage.get('artifacts') or [],
                    'recovery': 'no automatic retry or repair authorized for this proof'}
    return None


def _document(path):
    """Bounded regular file, no symlinks at any component, no parser prose."""
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        child = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        try:
            if not stat.S_ISREG(os.fstat(child).st_mode):
                raise ValueError('not a regular report')
            with os.fdopen(child, 'rb', closefd=False) as stream:
                raw = stream.read(65537)
            if len(raw) > 65536:
                raise ValueError('oversized report')
        finally:
            os.close(child)
    finally:
        os.close(descriptor)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate report member')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('non-JSON constant')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid_constant)


def provider_diagnostic(failure, *, run_root, incarnation):
    result = {'availability': 'unavailable', 'provider_reason': 'unknown',
              'provider_exit_status': None, 'authentication_cause': 'unknown',
              'basis': 'supplementary published adapter report; never raw provider output',
              'next_action': 'Preserve this attempt and request owner diagnosis before another run; no credential diagnosis is established.'}
    output, filename, schema = ('proposal', 'result.json', 'baton.dogfood-proposal/2') if failure['kind'] == 'implementation' else ('logs', 'review.json', 'baton.review-log/1')
    matches = [row for row in failure['artifacts'] if row.get('output_name') == output and row.get('artifact_id') == failure['attempt_id'] + ':' + output]
    if len(matches) != 1:
        return result
    try:
        url = urlsplit(matches[0]['locator'])
        path = Path(url.path)
        if url.scheme != 'file' or url.netloc or url.query or url.fragment or '%' in url.path or '..' in path.parts:
            return result
        path.relative_to(run_root / 'storage')
        if path.parts[-3:] != ('custody', failure['attempt_id'], output):
            return result
        given = _document(path / filename)
        if given.get('schema') != schema or given.get('task_id') != incarnation + '-' + failure['job_id'][-1]:
            return result
        provider = given.get('provider') or {}
        reason = provider.get('failure_reason')
        # This is the adapter's existing closed vocabulary, not a classifier
        # over provider text. api-error does not establish authentication.
        if reason not in ('api-error', 'timeout', 'start-error', 'unclassified'):
            return result
        code = provider.get('status')
        if code is not None and (type(code) is not int or not -255 <= code <= 255):
            return result
        result.update(availability='available', provider_reason=reason, provider_exit_status=code)
        result['next_action'] = {
            'api-error': 'Provider reported api-error; authentication, account and network cause remain unknown. Obtain an approved structured diagnostic before retry.',
            'timeout': 'Adapter reported its provider deadline; retain evidence and diagnose without increasing the proof deadline.',
            'start-error': 'Adapter could not start the provider; inspect the approved executable/runtime boundary without reading credentials.',
            'unclassified': 'Adapter could not classify a complete supported terminal reason; retain unknown and request scoped diagnostic work.'}[reason]
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        pass
    return result
