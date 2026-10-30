"""Post-run final-result collection for the EXTERNAL OPERATOR AND REVIEWER.

Read-only. Opens no store, writes nothing, starts nothing, and reads no
credential and no transcript or provider output.

WHY THIS PROGRAM EXISTS. `../execution-339421`'s TASK item 6 told the worker
inside the run to report the run's own three final results. It cannot: the
controller publishes its report after `supervise_process` returns and after
child cleanup (`authoring_enforcement.py:552-591`), and the supervisor publishes
`<outcome_path>` post-stop (`baseline.py:1450-1461`). Both land on the far side
of the worker's own termination, and a worker killed at lease expiry is simply
gone before either exists. `decisions/review-339623.md` item 1 required the
obligation to move to a party that can discharge it -- the operator and the
independent reviewer, after the run -- and item 2 required that an unavailable
report name no cause. This is that half of the acceptance, executable rather
than described, so "collect the final results" is a command and not a hope.

WHAT IT REFUSES TO CONCLUDE, which is the whole point:

  * absent, inaccessible, pending and unknown-cause are FOUR DIFFERENT facts.
    A path that is not there is `absent` only if its directory could actually be
    listed; a read that failed is `inaccessible` and NOT absent; a `.tmp`
    sibling or an uncomposed packet is `pending`; a report present but
    unparseable or uncorrelated is `unknown-cause`.
  * A PUBLICATION TIMEOUT IS NAMED ONLY ON CORRELATED POSITIVE EVIDENCE -- a
    `TimeoutError` fault in a controller report actually read, whose run id
    matches. Absence is never evidence of a timeout. `FAILURE.md` is the
    standing counterexample: that run left no workload outcome at all because it
    died at startup in 0.506s, which an absence-means-timeout reader would have
    reported as a publication timeout that never happened.
  * A PUBLICATION TIMEOUT GUARANTEES NO FILESYSTEM NON-EFFECT.
    `authoring_enforcement.py:586-594` bounds `write_text`, `os.replace` and
    `print` in ONE block, so a `TimeoutError` during the `print` follows an
    already-completed `os.replace` -- the report exists -- and one during
    `write_text` can leave a partial `.tmp`. So this program reports `.tmp`
    siblings explicitly and never treats a present report as proof that
    publication completed cleanly.
  * An unavailable final report RETRACTS NOTHING already recorded, and it is
    never success, never acceptance and never proof of cessation.

The authoring log is reported by presence, size and digest ONLY. Its bytes are
provider-adjacent output and are not this program's to emit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

# The four artifacts, as the vehicle actually names them.
#   workload           <outcome_path>
#   controller         <outcome_path>.enforcement-<pid>-<ns>.json
#   shutdown progress  <status_path>.progress.json, where status_path is
#                      <outcome_path>.manager-<pid>-<ns>.json
#   authoring log      <outcome_path>.authoring.log
CONTROLLER_GLOB = '.enforcement-*.json'
PROGRESS_GLOB = '.manager-*.json.progress.json'
SHUTDOWN_GLOB = '.manager-*.json.shutdown.json'
LOG_SUFFIX = '.authoring.log'

UNAVAILABLE = ('absent', 'inaccessible', 'pending', 'unknown-cause')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _listable(directory):
    """Can we enumerate it? This is what separates `absent` from `inaccessible`."""
    try:
        os.listdir(directory)
        return True, None
    except FileNotFoundError:
        return False, 'the directory does not exist'
    except OSError as fault:
        return False, type(fault).__name__ + ': ' + str(fault)


def _read_json(path):
    """-> (value, state, reason). Never raises; an unreadable file is a FACT."""
    try:
        return json.loads(Path(path).read_text()), 'present', None
    except FileNotFoundError:
        return None, 'absent', 'the path does not exist'
    except PermissionError as fault:
        return None, 'inaccessible', type(fault).__name__ + ': ' + str(fault)
    except OSError as fault:
        return None, 'inaccessible', type(fault).__name__ + ': ' + str(fault)
    except json.JSONDecodeError as fault:
        return None, 'unknown-cause', 'present but not parseable JSON: ' + str(fault)


def _expected_identity(place):
    """The run's own identity, for correlation. Absent is a fact, not a failure."""
    value, state, reason = _read_json(place / 'PACKET.json')
    if state != 'present':
        return dict(state=state, reason=reason, run_id=None, work=None, claim=None,
                    note='without the composed packet nothing can be correlated; '
                         'every identity check below is reported as unresolved '
                         'rather than passed')
    return dict(state='present', reason=None, run_id=value.get('run_id'),
                work=value.get('work'), claim=value.get('claim'),
                outcome_path=value.get('outcome_path'))


def _correlate(payload, expected, what):
    """An identity that does not match is `unknown-cause`, never a silent pass."""
    if expected.get('run_id') is None:
        return 'unresolved', ('the run identity could not be read, so this '
                              'report is not correlated to any run')
    held = payload.get('run_id') if isinstance(payload, dict) else None
    if held is None:
        return 'unresolved', f'the {what} carries no run_id member to correlate'
    if held != expected['run_id']:
        return 'mismatch', (f'the {what} names run {held!r}, not the composed '
                            f'run {expected["run_id"]!r}; it is evidence about '
                            f'a different run')
    return 'matched', None


def _artifact(place, name, *, glob=None, listable, why_unlistable):
    """One artifact, classified into present or one of the four unavailable states."""
    record = dict(artifact=name)
    if not listable:
        record.update(state='inaccessible', reason=why_unlistable, paths=[])
        return record
    if glob:
        found = sorted(str(one) for one in place.glob('outcome.json' + glob))
    else:
        found = [str(place / name)] if (place / name).exists() else []
    temporary = sorted(str(one) for one in place.glob('outcome.json*.tmp'))
    record['paths'] = found
    record['temporary_siblings'] = temporary
    if not found:
        if temporary:
            record.update(state='pending', reason=(
                'no final path, but a partial temporary exists: publication was '
                'entered and did not complete. NOT absent and NOT a named cause.'))
        else:
            record.update(state='absent', reason=(
                'the directory was listed and the path is not in it. This means '
                'the final result is UNAVAILABLE and its cause is UNKNOWN -- '
                'never that publication timed out, and never that nothing was '
                'written elsewhere.'))
        return record
    record['state'] = 'present'
    return record


def _controller(place, expected, listable, why):
    record = _artifact(place, 'controller final report',
                       glob=CONTROLLER_GLOB, listable=listable,
                       why_unlistable=why)
    record['who_writes_it'] = ('the outer controller, after supervise_process '
                               'returns and after child cleanup '
                               '(authoring_enforcement.py:552-591) -- which is '
                               'after any worker inside the run has ended')
    if record['state'] != 'present':
        return record
    reports = []
    for path in record['paths']:
        payload, state, reason = _read_json(path)
        one = dict(path=path, state=state, reason=reason, sha256=None)
        if state == 'present':
            one['sha256'] = sha(path)
            correlation, note = _correlate(payload, expected, 'controller report')
            one['identity'] = correlation
            one['identity_note'] = note
            if correlation == 'mismatch':
                one['state'] = 'unknown-cause'
            one['read'] = {key: payload.get(key) for key in (
                'state', 'faults', 'child_status', 'child_started', 'child_exited',
                'elapsed_seconds', 'shutdown_deadline', 'shutdown_progress',
                'author_invocation_started', 'recovery_only', 'manager_report_path',
                'enforcement_path')}
        reports.append(one)
    record['reports'] = reports
    record['state'] = 'present' if any(
        one['state'] == 'present' for one in reports) else 'unknown-cause'
    return record


def _workload(place, expected, listable, why):
    record = _artifact(place, 'workload final report', listable=listable,
                       why_unlistable=why)
    # `outcome.json` has no glob, so re-resolve it by name.
    if listable:
        target = place / 'outcome.json'
        record['paths'] = [str(target)] if target.exists() else []
        if not record['paths']:
            record['state'] = 'pending' if record['temporary_siblings'] else 'absent'
    record['who_writes_it'] = ('the supervisor, post-stop, inside the '
                               'workload-publication reservation '
                               '(baseline.py:1450-1461)')
    if record['state'] != 'present':
        return record
    payload, state, reason = _read_json(place / 'outcome.json')
    record['read_state'] = state
    record['read_reason'] = reason
    if state == 'present':
        record['sha256'] = sha(place / 'outcome.json')
        correlation, note = _correlate(payload, expected, 'workload outcome')
        record['identity'] = correlation
        record['identity_note'] = note
        if correlation == 'mismatch':
            record['state'] = 'unknown-cause'
        record['read'] = {key: payload.get(key) for key in (
            'state', 'stopped', 'held_because', 'uncertainty',
            'outstanding_cleanup', 'cleanup_sweeps', 'finished_at', 'job_id')}
    else:
        record['state'] = state
    return record


def _progress(place, listable, why):
    record = _artifact(place, 'shutdown progress', glob=PROGRESS_GLOB,
                       listable=listable, why_unlistable=why)
    record['who_writes_it'] = ('each Shutdown.call, BEFORE running its step; the '
                               'controller copies it into its own report')
    record['meaning'] = ('the last step ENTERED. Entering is not finishing, and '
                         'this is not a sampled stack and not a cessation receipt.')
    if listable:
        record['shutdown_requests'] = sorted(
            str(one) for one in place.glob('outcome.json' + SHUTDOWN_GLOB))
    if record['state'] != 'present':
        return record
    steps = []
    for path in record['paths']:
        payload, state, reason = _read_json(path)
        one = dict(path=path, state=state, reason=reason)
        if state == 'present':
            one['read'] = payload
        steps.append(one)
    record['entries'] = steps
    return record


def _log(place, listable, why):
    record = dict(artifact='authoring log', emitted='presence, size and digest '
                  'ONLY -- the bytes are provider-adjacent output and are not '
                  'this program\'s to emit')
    if not listable:
        record.update(state='inaccessible', reason=why, paths=[])
        return record
    target = place / ('outcome.json' + LOG_SUFFIX)
    if not target.exists():
        record.update(state='absent', paths=[], reason=(
            'listed and not present; unavailable, cause unknown'))
        return record
    try:
        record.update(state='present', paths=[str(target)],
                      size_bytes=target.stat().st_size, sha256=sha(target))
    except OSError as fault:
        record.update(state='inaccessible', paths=[str(target)],
                      reason=type(fault).__name__ + ': ' + str(fault))
    return record


def _timeout_verdict(controller):
    """A publication timeout is named ONLY on correlated positive evidence."""
    evidence = []
    for one in controller.get('reports', []) or []:
        if one.get('state') != 'present' or one.get('identity') != 'matched':
            continue
        for fault in (one.get('read', {}).get('faults') or []):
            if 'TimeoutError' in str(fault):
                evidence.append(dict(path=one['path'], fault=str(fault)))
    if evidence:
        return dict(established=True, evidence=evidence,
                    note='a TimeoutError fault was READ in a correlated '
                         'controller report. Even so: the bound at '
                         'authoring_enforcement.py:586-594 spans write_text, '
                         'os.replace and print, so this does NOT establish that '
                         'nothing was written -- check temporary_siblings.')
    return dict(established=False, evidence=[],
                note='NOT ESTABLISHED. No correlated TimeoutError fault was '
                     'read. An absent or inaccessible report is not evidence of '
                     'a timeout: a run that never started, an import or startup '
                     'failure (see FAILURE.md), process death, a failed read and '
                     'non-timeout publication errors all leave no final report.')


def collect(place):
    place = Path(place)
    listable, why = _listable(place)
    expected = _expected_identity(place)
    controller = _controller(place, expected, listable, why)
    workload = _workload(place, expected, listable, why)
    progress = _progress(place, listable, why)
    log = _log(place, listable, why)
    results = dict(controller=controller, workload=workload,
                   shutdown_progress=progress, authoring_log=log)
    unavailable = {name: one['state'] for name, one in results.items()
                   if one['state'] in UNAVAILABLE}
    return dict(
        schema='baton.w333486-final-result-collection/1',
        collected_from=str(place),
        directory_listable=listable,
        directory_reason=why,
        expected_identity=expected,
        results=results,
        unavailable=unavailable,
        publication_timeout=_timeout_verdict(controller),
        acceptance=('A missing or partial final report is INCOMPLETE: never '
                    'success, never acceptance and never proof of cessation. No '
                    'startup success and no producer exit substitutes for '
                    'final-result acceptance. An unavailable report retracts '
                    'nothing already recorded.'),
        owner=('the external operator and the independent reviewer. The worker '
               'inside the run cannot observe any of these artifacts; its own '
               'report covers what it saw before termination plus the retained '
               'candidate checkpoint -- see TASK.md item 6.'),
        read_only=('this program opened no store, wrote nothing, started '
                   'nothing, and read no credential, transcript or provider '
                   'output'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read-only post-run collection of the three final results '
                    'plus the retained authoring log. For the external operator '
                    'and reviewer; the worker inside the run cannot do this.')
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--root', help='the run root; its packet/ directory is read')
    target.add_argument('--packet-dir', help='the directory holding the outcome '
                                             'files directly, e.g. a retained '
                                             'read-only evidence copy')
    args = parser.parse_args()
    where = Path(args.packet_dir) if args.packet_dir else Path(args.root) / 'packet'
    json.dump(collect(where), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write('\n')
