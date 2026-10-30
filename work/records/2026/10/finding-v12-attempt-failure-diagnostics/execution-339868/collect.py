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
report name no cause.

FOUR DEFECTS IN THE FIRST VERSION OF THIS PROGRAM, all found by
`decisions/review-339861.md` and all fixed here. They are recorded because the
fixes are the reason this revision exists:

  1. A PRESENT WORKLOAD REPORT WAS REPORTED ABSENT. The old `_workload` passed a
     display label to the path resolver, found `outcome.json` afterwards,
     replaced `paths`, and never corrected the state or parsed the file. Fixed by
     resolving every artifact from an explicit path or glob and never from its
     label; the positive case is now a probe.
  2. CORRELATION LOOKED FOR A FIELD THE VEHICLE DOES NOT PUBLISH. The controller
     report has NO top-level `run_id`; its identity is `original_envelope`,
     built at `authoring_enforcement.py:40-52` as `{run, job, authority,
     packet}` and stored at `:580`. The old version demanded `run_id`, so every
     real controller report came back `unresolved` -- and the sealed probes hid
     it by inventing a top-level `run_id`. Each artifact is now correlated
     through ITS OWN shape, and the field actually used is named in the output.
  3. AN UNRELATED TIMEOUT BECAME A PUBLICATION TIMEOUT. The old verdict accepted
     any fault containing `TimeoutError`, so `TimeoutError: manager startup
     snapshot` "established" a publication timeout. Now only a fault naming a
     KNOWN PUBLICATION STEP can, every other timeout is reported separately as
     what it is, and the structural limit is stated: the outer publication
     handler at `:592-595` returns 1 WITHOUT recording its own fault, so an
     outer publication timeout is NOT establishable from these artifacts at all
     and its absence is expected rather than informative.
  4. A MALFORMED REPORT ABORTED EVERYTHING. A JSON array raised `AttributeError`
     and no other evidence was collected. Every artifact is now collected inside
     its own guard: a malformed shape or a failed read is an `unknown-cause`
     OBSERVATION, and the rest of the collection still happens.

WHAT IT REFUSES TO CONCLUDE, which is the whole point:

  * absent, inaccessible, pending and unknown-cause are FOUR DIFFERENT facts.
    A path that is not there is `absent` only if its directory could actually be
    listed; a read that failed is `inaccessible` and NOT absent; a `.tmp`
    sibling is `pending`; a report present but unparseable, not an object, or
    not correlated is `unknown-cause`.
  * A PUBLICATION TIMEOUT IS NAMED ONLY ON SPECIFIC CORRELATED EVIDENCE -- a
    fault naming a publication step, in an artifact that correlates to this run.
    Absence is never evidence of one. `FAILURE.md` is the standing
    counterexample: that run left no workload outcome because it died at startup
    in 0.506s, which an absence-means-timeout reader would have called a
    publication timeout that never happened.
  * A PUBLICATION TIMEOUT GUARANTEES NO FILESYSTEM NON-EFFECT.
    `authoring_enforcement.py:586-594` bounds `write_text`, `os.replace` and
    `print` in ONE block, so a `TimeoutError` during the `print` follows an
    already-completed `os.replace` -- the report exists -- and one during
    `write_text` can leave a partial `.tmp`. So `.tmp` siblings are always
    reported and a present report is never proof that publication finished.
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

# The artifacts, as the vehicle actually names them. `status_path` is
# `<outcome_path>.manager-<pid>-<ns>.json` (`authoring_enforcement.py:525`), so
# the progress file is that plus `.progress.json` (`authoring_shutdown.py:40`).
WORKLOAD = 'outcome.json'
CONTROLLER_GLOB = 'outcome.json.enforcement-*.json'
MANAGER_GLOB = 'outcome.json.manager-*.json'
PROGRESS_GLOB = 'outcome.json.manager-*.json.progress.json'
SHUTDOWN_GLOB = 'outcome.json.manager-*.json.shutdown.json'
TEMPORARY_GLOB = 'outcome.json*.tmp'
LOG = 'outcome.json.authoring.log'

UNAVAILABLE = ('absent', 'inaccessible', 'pending', 'unknown-cause')

# The steps that are actually publications. A `TimeoutError` naming one of these
# is specific evidence; any other timeout is a timeout of something else.
#   `outer outcome publication`      authoring_enforcement.py:588 (NOT RECORDED --
#                                    the handler at :592-595 returns 1 without
#                                    appending the fault, so this string can only
#                                    reach a report through some other path)
#   `final enforcement publication`  authoring_enforcement.py:493, through
#                                    Shutdown.call, whose faults DO reach the
#                                    progress file (authoring_shutdown.py:84-86)
#   `workload publication`           baseline.py:1461, through bounded_call
PUBLICATION_STEPS = ('outer outcome publication', 'final enforcement publication',
                     'workload publication', 'workload-publication')
OUTER_PUBLICATION_IS_UNRECORDABLE = (
    'The outer controller publication timeout is NOT establishable from these '
    'artifacts. authoring_enforcement.py:592-595 catches its own TimeoutError '
    'and returns 1 WITHOUT adding that fault to the report it was trying to '
    'write, so no artifact records it. Its absence is EXPECTED and is not '
    'evidence either way. A partial .enforcement-*.tmp with no final path shows '
    'that publication was ENTERED and did not complete -- not why.')


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


def _read_object(path):
    """-> (value, state, reason). Never raises, and NEVER returns a non-object.

    A present file whose top level is not a JSON object is `unknown-cause`: it
    is an observation about a malformed artifact, not an exception that stops
    the collection. Defect 4 was exactly this.
    """
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return None, 'absent', 'the path does not exist'
    except (PermissionError, IsADirectoryError, OSError) as fault:
        return None, 'inaccessible', type(fault).__name__ + ': ' + str(fault)
    except UnicodeDecodeError as fault:
        return None, 'unknown-cause', 'present but not decodable text: ' + str(fault)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as fault:
        return None, 'unknown-cause', 'present but not parseable JSON: ' + str(fault)
    if not isinstance(value, dict):
        return None, 'unknown-cause', ('present and parseable, but its top level is a '
                                       + type(value).__name__ + ' rather than an object, '
                                       'so none of the expected members can be read')
    return value, 'present', None


def _found(place, pattern, *, exact=False):
    try:
        if exact:
            target = place / pattern
            return ([str(target)] if target.exists() else []), None
        return sorted(str(one) for one in place.glob(pattern)), None
    except OSError as fault:
        return [], type(fault).__name__ + ': ' + str(fault)


def _expected_identity(place, supplied=None):
    """The run's own identity, for correlation. Absent is a fact, not a failure.

    `supplied` is the operator's `--expect-run`, which matters for a RETAINED
    EVIDENCE COPY: those directories hold the published artifacts but not the
    composed `PACKET.json`, so without it nothing can be correlated and every
    identity comes back `unresolved`. Supplying it is an operator assertion and
    is labelled as one -- it never overrides a readable packet.
    """
    value, state, reason = _read_object(place / 'PACKET.json')
    if state != 'present':
        if supplied:
            return dict(state=state, reason=reason, run_id=supplied, job_id=None,
                        work=None, claim=None, authority=None, outcome_path=None,
                        identity_source='--expect-run, supplied by the operator',
                        note='no readable composed packet, so the run id was supplied '
                             'rather than read. Correlation below is against an '
                             'OPERATOR ASSERTION, not against the packet.')
        return dict(state=state, reason=reason, run_id=None, job_id=None, work=None,
                    claim=None, authority=None, outcome_path=None,
                    note='without a readable composed packet nothing can be correlated; '
                         'every identity check below is reported as unresolved rather '
                         'than passed. Pass --expect-run <run id> to correlate against '
                         'a run identity you supply, e.g. over a retained evidence copy.')
    submission = value.get('submission')
    deployment = value.get('deployment')
    if supplied and value.get('run_id') not in (None, supplied):
        return dict(state='unknown-cause', run_id=None, job_id=None, work=None,
                    claim=None, authority=None, outcome_path=value.get('outcome_path'),
                    reason=f'--expect-run {supplied!r} contradicts the composed '
                           f'packet run {value.get("run_id")!r}; refusing to correlate '
                           f'against either, because one of them is about another run',
                    note='resolve which run you are collecting before reading the '
                         'identity results below')
    return dict(
        state='present', reason=None, identity_source='composed PACKET.json',
        run_id=value.get('run_id'), work=value.get('work'), claim=value.get('claim'),
        job_id=(submission or {}).get('job_id') if isinstance(submission, dict) else None,
        authority=(deployment or {}).get('authority_uuid') if isinstance(deployment, dict) else None,
        outcome_path=value.get('outcome_path'))


def _correlate(payload, expected, *, fields, what):
    """Correlate through the artifact's OWN shape. Defect 2 was assuming one shape.

    `fields` is an ordered list of (expected_key, getter, description). The first
    one the artifact actually carries decides, and the output names it. A carried
    field that disagrees is a `mismatch` and is never a silent pass.
    """
    available, conflicts = [], []
    for expected_key, getter, description in fields:
        try:
            held = getter(payload)
        except Exception as fault:                      # a hostile shape is a fact
            conflicts.append(f'{description}: unreadable ({type(fault).__name__})')
            continue
        if held is None:
            continue
        want = expected.get(expected_key)
        available.append(dict(field=description, value=held, expected=want))
        if want is None:
            continue
        if held != want:
            conflicts.append(f'{description} is {held!r}, expected {want!r}')
    if conflicts:
        return dict(identity='mismatch', why='; '.join(conflicts), carried=available,
                    note=f'this {what} is evidence about a different run, or its '
                         f'identity disagrees with the composed packet')
    matched = [one for one in available if one['expected'] is not None]
    if matched:
        return dict(identity='matched', why=None, carried=available,
                    correlated_on=[one['field'] for one in matched])
    if not available:
        return dict(identity='unresolved', carried=[],
                    why=f'the {what} carries none of the identity fields this '
                        f'vehicle publishes for it')
    return dict(identity='unresolved', carried=available,
                why=f'the {what} carries identity fields but the composed packet '
                    f'supplied nothing to compare them against')


def _envelope(payload):
    held = payload.get('original_envelope')
    return held if isinstance(held, dict) else {}


CONTROLLER_FIELDS = (
    ('run_id', lambda p: _envelope(p).get('run'), 'original_envelope.run'),
    ('job_id', lambda p: _envelope(p).get('job'), 'original_envelope.job'),
    ('authority', lambda p: _envelope(p).get('authority'), 'original_envelope.authority'),
)
WORKLOAD_FIELDS = (
    ('run_id', lambda p: p.get('run_id'), 'run_id'),
    ('job_id', lambda p: p.get('job_id'), 'job_id'),
    ('work', lambda p: p.get('work'), 'work'),
    ('claim', lambda p: p.get('claim'), 'claim'),
)
PROGRESS_FIELDS = (
    ('run_id', lambda p: p.get('run_id'), 'run_id'),
    ('job_id', lambda p: p.get('job_id'), 'job_id'),
)

CONTROLLER_READ = ('state', 'faults', 'child_status', 'child_started', 'child_exited',
                   'elapsed_seconds', 'shutdown_deadline', 'shutdown_progress',
                   'operator_signals', 'author_invocation_started', 'recovery_only',
                   'manager_report_path', 'enforcement_path', 'authoring_log')
WORKLOAD_READ = ('state', 'stopped', 'held_because', 'uncertainty', 'outstanding_cleanup',
                 'cleanup_sweeps', 'finished_at', 'job_id', 'retry')
PROGRESS_READ = ('step', 'deadline', 'step_deadline', 'faults', 'run_id', 'job_id')


def _temporaries(place, listable):
    if not listable:
        return []
    found, _fault = _found(place, TEMPORARY_GLOB)
    return found


def _one_report(path, expected, *, fields, read, what):
    """One file, fully classified, never raising out."""
    record = dict(path=path)
    try:
        payload, state, reason = _read_object(path)
        record.update(state=state, reason=reason)
        if state != 'present':
            return record
        record['sha256'] = sha(path)
        correlation = _correlate(payload, expected, fields=fields, what=what)
        record['identity'] = correlation.pop('identity')
        record['identity_detail'] = correlation
        if record['identity'] == 'mismatch':
            record['state'] = 'unknown-cause'
        record['read'] = {key: payload.get(key) for key in read}
    except Exception as fault:                          # defect 4: never abort
        record.update(state='unknown-cause',
                      reason='collection of this artifact failed: '
                             + type(fault).__name__ + ': ' + str(fault),
                      isolated=True)
    return record


def _artifact(place, *, name, pattern, exact, listable, why_unlistable, expected,
              fields, read, who_writes_it, extra=None):
    """One artifact kind. The path comes from the pattern, NEVER from the label."""
    record = dict(artifact=name, who_writes_it=who_writes_it,
                  resolved_by=('exact name ' + pattern) if exact else ('glob ' + pattern))
    if extra:
        record.update(extra)
    if not listable:
        record.update(state='inaccessible', reason=why_unlistable, paths=[],
                      temporary_siblings=[])
        return record
    found, fault = _found(place, pattern, exact=exact)
    record['paths'] = found
    record['temporary_siblings'] = _temporaries(place, listable)
    if fault:
        record.update(state='inaccessible', reason=fault)
        return record
    if not found:
        if record['temporary_siblings']:
            record.update(state='pending', reason=(
                'no final path, but a partial temporary exists: publication was '
                'entered and did not complete. NOT absent, and NOT a named cause.'))
        else:
            record.update(state='absent', reason=(
                'the directory was listed and the path is not in it. The final '
                'result is UNAVAILABLE and its cause is UNKNOWN -- never that '
                'publication timed out, and never that nothing was written '
                'elsewhere.'))
        return record
    reports = [_one_report(path, expected, fields=fields, read=read, what=name)
               for path in found]
    record['reports'] = reports
    present = [one for one in reports if one['state'] == 'present']
    if present:
        record['state'] = 'present'
    else:
        # Every candidate was unreadable or uncorrelated: that is an observation
        # about the artifact, and the WORST specific state is the honest answer.
        for state in ('inaccessible', 'unknown-cause', 'pending', 'absent'):
            if any(one['state'] == state for one in reports):
                record['state'] = state
                break
        else:
            record['state'] = 'unknown-cause'
    return record


def _linked(controller, place):
    """What the controller report says its siblings are, and whether they are there.

    This is exact linkage rather than glob guessing: `enforcement_path`,
    `manager_report_path` and `authoring_log` are absolute paths the controller
    wrote about itself, and `<manager_report_path>.progress.json` is the progress
    file for THAT incarnation.
    """
    links = []
    for one in (controller.get('reports') or []):
        if one.get('state') != 'present':
            continue
        read = one.get('read') or {}
        manager = read.get('manager_report_path')
        for label, value in (('enforcement_path', read.get('enforcement_path')),
                             ('authoring_log', read.get('authoring_log')),
                             ('manager_report_path', manager),
                             ('progress (manager_report_path + .progress.json)',
                              (manager + '.progress.json') if isinstance(manager, str) else None)):
            if value is None:
                links.append(dict(source=one['path'], link=label, path=None,
                                  state='not named by the report',
                                  note='the report does not carry this member; for '
                                       'manager_report_path that is expected from a '
                                       'controller incarnation that never composed a '
                                       'child status path'))
                continue
            try:
                there = Path(value).exists()
            except OSError as fault:
                links.append(dict(source=one['path'], link=label, path=value,
                                  state='inaccessible',
                                  note=type(fault).__name__ + ': ' + str(fault)))
                continue
            inside = False
            try:
                inside = Path(value).parent.resolve() == Path(place).resolve()
            except OSError:
                pass
            links.append(dict(source=one['path'], link=label, path=value,
                              state='found' if there else 'named but not present',
                              in_collected_directory=inside,
                              note=None if there else
                                   'the report names it and it is not there: '
                                   'unavailable, cause unknown. If the run root moved '
                                   'or was copied, these absolute paths will not '
                                   'resolve and that is not evidence about the run.'))
    return links


def _timeout_verdict(results):
    """Defect 3. A publication timeout needs a fault naming a PUBLICATION step."""
    publication, other, uncorrelated = [], [], []
    for which, record in results.items():
        for one in (record.get('reports') or []):
            if one.get('state') not in ('present', 'unknown-cause'):
                continue
            faults = (one.get('read') or {}).get('faults')
            if not isinstance(faults, list):
                continue
            for fault in faults:
                text = str(fault)
                if 'TimeoutError' not in text:
                    continue
                entry = dict(artifact=which, path=one['path'], fault=text,
                             identity=one.get('identity'))
                step = next((name for name in PUBLICATION_STEPS if name in text), None)
                if one.get('identity') != 'matched':
                    entry['why_not_evidence'] = (
                        'this artifact does not correlate to the collected run, so its '
                        'faults are not evidence about it')
                    uncorrelated.append(entry)
                elif step:
                    entry['publication_step'] = step
                    publication.append(entry)
                else:
                    entry['why_not_publication'] = (
                        'a TimeoutError naming no publication step. It is a real '
                        'observed timeout of SOMETHING ELSE -- a startup snapshot, a '
                        'shutdown observation, a cleanup step -- and it says nothing '
                        'about whether a final report was published.')
                    other.append(entry)
    verdict = dict(
        established=bool(publication),
        evidence=publication,
        other_timeouts_observed=other,
        uncorrelated_timeouts=uncorrelated,
        outer_publication_limit=OUTER_PUBLICATION_IS_UNRECORDABLE,
        rule='Only a correlated fault naming one of ' + ', '.join(PUBLICATION_STEPS)
             + ' establishes a publication timeout.')
    if publication:
        verdict['note'] = (
            'ESTABLISHED for the named publication step(s) only, from a correlated '
            'fault actually read. Even so: the bound at '
            'authoring_enforcement.py:586-594 spans write_text, os.replace and print, '
            'so this does NOT establish that nothing was written -- check '
            'temporary_siblings.')
    else:
        verdict['note'] = (
            'NOT ESTABLISHED, and for an absent outer report NOT ESTABLISHABLE. No '
            'correlated fault naming a publication step was read. An absent or '
            'inaccessible report is not evidence of a timeout: a run that never '
            'started, an import or startup failure (see FAILURE.md), process death, a '
            'failed read and non-timeout publication errors all leave no final report.'
            + (' Timeouts of other steps WERE observed and are listed separately; they '
               'are not publication evidence.' if other else ''))
    return verdict


def collect(place, supplied_run=None):
    place = Path(place)
    listable, why = _listable(place)
    expected = _expected_identity(place, supplied_run)
    common = dict(listable=listable, why_unlistable=why, expected=expected)

    results = {}
    results['workload'] = _artifact(
        place, name='workload final report', pattern=WORKLOAD, exact=True,
        fields=WORKLOAD_FIELDS, read=WORKLOAD_READ,
        who_writes_it='the supervisor, post-stop, inside the workload-publication '
                      'reservation (baseline.py:1450-1461)', **common)
    results['controller'] = _artifact(
        place, name='controller final report', pattern=CONTROLLER_GLOB, exact=False,
        fields=CONTROLLER_FIELDS, read=CONTROLLER_READ,
        who_writes_it='the outer controller, after supervise_process returns and after '
                      'child cleanup (authoring_enforcement.py:552-591) -- which is '
                      'after any worker inside the run has ended',
        extra=dict(identity_lives_in='original_envelope {run, job, authority}, built at '
                                     'authoring_enforcement.py:40-52 and stored at :580. '
                                     'This report has NO top-level run_id.'), **common)
    results['shutdown_progress'] = _artifact(
        place, name='shutdown progress', pattern=PROGRESS_GLOB, exact=False,
        fields=PROGRESS_FIELDS, read=PROGRESS_READ,
        who_writes_it='each Shutdown.call, BEFORE running its step '
                      '(authoring_shutdown.py:72-81)',
        extra=dict(meaning='the last step ENTERED. Entering is not finishing, and this '
                           'is not a sampled stack and not a cessation receipt.',
                   faults_do_reach_here='Shutdown.call appends a step fault before '
                                        're-raising (authoring_shutdown.py:84-86), so a '
                                        'child publication timeout CAN appear here.'),
        **common)
    results['manager_snapshot'] = _artifact(
        place, name='manager status snapshot', pattern=MANAGER_GLOB, exact=False,
        fields=(('run_id', lambda p: (p.get('envelope') or {}).get('run')
                 if isinstance(p.get('envelope'), dict) else None, 'envelope.run'),),
        read=('envelope', 'recovery', 'stopping', 'finished',
              'author_invocation_started', 'report'),
        who_writes_it='publish_guard, each observation (authoring_enforcement.py:387-395)',
        extra=dict(note='an observation, never cessation and never a permission grant. '
                        'A missing final snapshot is held.'), **common)

    log = dict(artifact='authoring log', who_writes_it='the run',
               emitted='presence, size and digest ONLY -- the bytes are '
                       'provider-adjacent output and are not this program\'s to emit')
    if not listable:
        log.update(state='inaccessible', reason=why, paths=[])
    else:
        found, fault = _found(place, LOG, exact=True)
        log['paths'] = found
        if fault:
            log.update(state='inaccessible', reason=fault)
        elif not found:
            log.update(state='absent',
                       reason='listed and not present; unavailable, cause unknown')
        else:
            try:
                target = Path(found[0])
                log.update(state='present', size_bytes=target.stat().st_size,
                           sha256=sha(target))
            except OSError as fault:
                log.update(state='inaccessible',
                           reason=type(fault).__name__ + ': ' + str(fault))
    results['authoring_log'] = log

    unavailable = {name: one['state'] for name, one in results.items()
                   if one['state'] in UNAVAILABLE}
    available = sorted(name for name, one in results.items() if one['state'] == 'present')
    return dict(
        schema='baton.w333486-final-result-collection/2',
        collected_from=str(place),
        directory_listable=listable,
        directory_reason=why,
        expected_identity=expected,
        results=results,
        available=available,
        unavailable=unavailable,
        isolated_failures=[one['path'] for record in results.values()
                           for one in (record.get('reports') or [])
                           if one.get('isolated')],
        linked_artifacts=_linked(results['controller'], place),
        publication_timeout=_timeout_verdict(results),
        acceptance=('A missing or partial final report is INCOMPLETE: never success, '
                    'never acceptance and never proof of cessation. No startup success '
                    'and no producer exit substitutes for final-result acceptance. An '
                    'unavailable report retracts nothing already recorded, and one '
                    'unreadable artifact does not invalidate the others.'),
        owner=('the external operator and the independent reviewer. The worker inside '
               'the run cannot observe any of these artifacts; its own report covers '
               'what it saw before termination plus the retained candidate checkpoint '
               '-- see TASK.md item 6.'),
        read_only=('this program opened no store, wrote nothing, started nothing, and '
                   'read no credential, transcript or provider output'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read-only post-run collection of the final results plus the '
                    'retained authoring log. For the external operator and reviewer; '
                    'the worker inside the run cannot do this.')
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--root', help='the run root; its packet/ directory is read')
    target.add_argument('--packet-dir', help='the directory holding the outcome files '
                                             'directly, e.g. a retained read-only '
                                             'evidence copy')
    parser.add_argument('--expect-run', help='the run id to correlate against when the '
                                             'directory has no readable PACKET.json, as '
                                             'a retained evidence copy does not. An '
                                             'operator assertion, labelled as one, and '
                                             'refused if it contradicts a packet that '
                                             'IS readable.')
    args = parser.parse_args()
    where = Path(args.packet_dir) if args.packet_dir else Path(args.root) / 'packet'
    json.dump(collect(where, args.expect_run), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write('\n')
