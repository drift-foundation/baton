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

SEVEN DEFECTS IN TWO REVISIONS OF THIS PROGRAM, four found by
`decisions/review-339861.md` and three more by `decisions/review-340012.md`, all
fixed here. They are recorded because the fixes are the reason these revisions
exist, and because the pattern in them is the point: a reader that asserts more
than its inputs support is the exact fault this diagnostics outcome exists to
expose.

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
     KNOWN PUBLICATION STEP can, and every other timeout is reported as what it
     is.
  4. A MALFORMED REPORT ABORTED EVERYTHING. A JSON array raised `AttributeError`
     and no other evidence was collected. Every artifact is now collected inside
     its own guard: a malformed shape or a failed read is an `unknown-cause`
     OBSERVATION, and the rest of the collection still happens.
  5. SO DID A MALFORMED *LINK*, in the very revision that fixed defect 4.
     `_linked` called `Path(value)` on whatever the report carried and caught
     only `OSError`, so a correlated controller with `authoring_log: []` raised
     `TypeError` out of `collect()` and lost a perfectly readable workload
     report beside it. Link values are now shape-checked, a non-string is a
     malformed-link OBSERVATION, and the whole linkage pass is additionally
     guarded so it can never cost the artifacts their results.
  6. ONE UNRELATED TEMPORARY MARKED EVERY ARTIFACT `pending`. The old
     `_temporaries` handed the directory-wide `outcome.json*.tmp` set to every
     kind, so a single controller temporary made the workload, the progress file
     and the manager snapshot each report that ITS publication had been entered.
     The same glob never matched the workload temporary at all, which is
     `outcome.json.partial` and not a `.tmp`. Each artifact now sees only its own
     filenames, read from the producers (see `KINDS`).
  7. THE PROGRESS FILE WAS COUNTED AS A MANAGER SNAPSHOT. `outcome.json.manager-*.json`
     matches `outcome.json.manager-1-2.json.progress.json`, so a progress-only
     directory reported a manager snapshot that did not exist. The infix groups
     are now `[^.]+`, which cannot swallow a further `.progress.json`.

AND ONE FALSE CLAIM ABOUT THE PRODUCER, also from `decisions/review-340012.md`:
the previous revision said a child publication timeout "reaches the progress
file". It does not. `PUBLICATION_PERSISTENCE` below has the source order; the
short version is that `Shutdown.call` writes the snapshot BEFORE running its
step and appends that step's fault to memory only, the controller's final
publication is the LAST such call, and an exhausted deadline raises before the
write. **No publication fault is reliably persisted by this vehicle at all.**

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
import re
import sys

# THE ARTIFACTS, AND HOW THEIR FILENAMES ARE ACTUALLY FORMED. Read from the
# producers, because the previous revision guessed and got two of them wrong.
#
#   workload final       outcome.json                                  baseline._publish
#   workload temporary   outcome.json.partial                          baseline.py:1006 -- `path + ".partial"`, NOT `.tmp`
#   controller final     outcome.json.enforcement-<pid>-<ns>.json      authoring_enforcement.py:581
#   controller temporary outcome.json.enforcement-<pid>-<ns>.tmp       `.with_suffix('.tmp')` REPLACES `.json`, so it is not `...json.tmp`
#   manager snapshot     outcome.json.manager-<pid>-<ns>.json          authoring_enforcement.py:525
#   manager temporary    outcome.json.manager-<pid>-<ns>.tmp           publish_guard, same with_suffix behaviour
#   progress             outcome.json.manager-<pid>-<ns>.json.progress.json   authoring_shutdown.py:40
#   progress temporary   outcome.json.manager-<pid>-<ns>.json.progress.tmp
#   shutdown request     outcome.json.manager-<pid>-<ns>.json.shutdown.json   Process.request_shutdown
#   authoring log        outcome.json.authoring.log
#
# EVERY NAME IS CLASSIFIED ONCE, BY ANCHORED PATTERN, AND EACH ARTIFACT SEES ONLY
# ITS OWN FILES. The previous revision used one directory-wide `outcome.json*.tmp`
# set for every kind, so a single controller temporary made the workload, the
# progress file and the manager snapshot all report `pending` -- four artifacts
# each claiming its publication had been entered on the evidence of one unrelated
# file. It also matched the progress file with the manager-snapshot glob
# (`outcome.json.manager-*.json` matches `...json.progress.json`), reporting a
# snapshot that did not exist. The infix groups below are `[^.]+` precisely so a
# further `.progress.json` or `.shutdown.json` cannot be swallowed into them.
KINDS = {
    'workload': dict(
        final=r'^outcome\.json$', temporary=r'^outcome\.json\.partial$'),
    'controller': dict(
        final=r'^outcome\.json\.enforcement-([^.]+)\.json$',
        temporary=r'^outcome\.json\.enforcement-([^.]+)\.tmp$'),
    'manager_snapshot': dict(
        final=r'^outcome\.json\.manager-([^.]+)\.json$',
        temporary=r'^outcome\.json\.manager-([^.]+)\.tmp$'),
    'shutdown_progress': dict(
        final=r'^outcome\.json\.manager-([^.]+)\.json\.progress\.json$',
        temporary=r'^outcome\.json\.manager-([^.]+)\.json\.progress\.tmp$'),
    'shutdown_request': dict(
        final=r'^outcome\.json\.manager-([^.]+)\.json\.shutdown\.json$',
        temporary=r'^outcome\.json\.manager-([^.]+)\.json\.shutdown\.tmp$'),
    'authoring_log': dict(final=r'^outcome\.json\.authoring\.log$', temporary=None),
}

# The composed packet's own members, which legitimately share the directory with
# the artifacts. They are recognised so that `unclassified` means what it says --
# a name this program does not account for -- rather than listing the whole packet
# as a surprise. Written by baseline_bindings.write plus the launch tree.
COMPOSED_MEMBERS = ('PACKET.json', 'adapter.json', 'commands.json', 'deployment.json',
                    'policy.json', 'runtime-profile.json', 'submission.json',
                    'task.json', 'AUTHORING-COMMAND.json', 'launch', 'workspaces',
                    'credentials', 'deployment-state')

UNAVAILABLE = ('absent', 'inaccessible', 'pending', 'unknown-cause')

# A `TimeoutError` naming one of these is about a publication rather than about
# some other step. KEPT FOR PARSING A FAULT THAT IS LITERALLY ON DISK -- NOT a
# claim that the vehicle records one. See PUBLICATION_PERSISTENCE below.
PUBLICATION_STEPS = ('outer outcome publication', 'final enforcement publication',
                     'workload publication', 'workload-publication')

# WHAT THE PRODUCERS ACTUALLY PERSIST, by source order. The previous revision
# claimed a child publication timeout "reaches the progress file"; that is FALSE
# and `decisions/review-340012.md` item 3 is the finding.
#
# `Shutdown.call` (`authoring_shutdown.py:72-86`) does, in this order:
#   :74  enters `bounded(deadline, step)` -- AN EXHAUSTED DEADLINE RAISES HERE,
#        before anything is written, so even the step name can be absent;
#   :76-81 writes the snapshot carrying `list(self.faults)` -- the faults from
#        EARLIER calls, never this one's;
#   :83  runs the thunk;
#   :85  on exception appends the fault to `self.faults` IN MEMORY and re-raises.
#
# So a step's own fault reaches disk only if a LATER `Shutdown.call` writes a
# snapshot successfully. Therefore:
#   * `final enforcement publication` (`authoring_enforcement.py:493`) is the LAST
#     `Shutdown.call` in the controller's `finally` block. Nothing follows it, so
#     its fault is NEVER persisted.
#   * `outer outcome publication` (`:588`) is not a `Shutdown.call` at all and its
#     handler at `:592-595` returns 1 without recording anything.
#   * `workload publication` (`baseline.py:1461`) is followed by later calls only
#     in `main` (`workload reporting` :2796, `operations close` :2884), reached
#     only if control gets there -- and because every call re-enters
#     `bounded(deadline, ...)` against the SAME exhausted deadline that caused the
#     first timeout, a later write is likely to raise before it writes too.
# CONCLUSION: this vehicle persists NO publication fault reliably. Absence of one
# is EXPECTED everywhere and is evidence of nothing. Where a fault IS on disk this
# program parses it and says so; that is parsing, not producer persistence.
PUBLICATION_PERSISTENCE = (
    'THIS VEHICLE PERSISTS NO PUBLICATION FAULT RELIABLY. Shutdown.call writes the '
    'snapshot with the faults from EARLIER calls (authoring_shutdown.py:76-81), then '
    'runs the step (:83) and appends its fault to memory only (:85), so a fault '
    'reaches disk only if a LATER Shutdown.call writes successfully. The controller '
    'final publication (authoring_enforcement.py:493) is the LAST such call, so its '
    'fault is never written; the outer publication (:588) is not a Shutdown.call and '
    'its handler at :592-595 records nothing; and a later write re-enters bounded() '
    'against the same exhausted deadline and will likely raise before writing. An '
    'exhausted deadline can also raise at :74 before the snapshot is written at all, '
    'so even the step name can be missing. ABSENCE OF A PUBLICATION FAULT IS '
    'EXPECTED AND MEANS NOTHING. Any verdict below rests on a fault FOUND ON DISK '
    'and is parsing, never proof that the producer records such faults.')

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


def classify(place, listable):
    """List the directory ONCE and bucket every name by anchored pattern.

    Returns (buckets, entries, fault). `buckets[kind]` is
    `{'final': [...], 'temporary': [...]}` holding only that kind's own files.
    `entries` is the whole directory listing, reported for the operator's
    information and NEVER used to infer any artifact's state -- which is defects
    6 and 7.
    """
    buckets = {kind: dict(final=[], temporary=[]) for kind in KINDS}
    buckets['composed'] = dict(final=[], temporary=[])
    buckets['other'] = dict(final=[], temporary=[])
    if not listable:
        return buckets, [], None
    try:
        entries = sorted(os.listdir(place))
    except OSError as fault:
        return buckets, [], type(fault).__name__ + ': ' + str(fault)
    for name in entries:
        if name in COMPOSED_MEMBERS:
            buckets['composed']['final'].append(name)
            continue
        for kind, patterns in KINDS.items():
            if re.match(patterns['final'], name):
                buckets[kind]['final'].append(str(Path(place) / name))
                break
            if patterns['temporary'] and re.match(patterns['temporary'], name):
                buckets[kind]['temporary'].append(str(Path(place) / name))
                break
        else:
            buckets['other']['final'].append(str(Path(place) / name))
    return buckets, entries, None


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


def _artifact(bucket, *, kind, name, listable, why_unlistable, expected, fields,
              read, who_writes_it, extra=None):
    """One artifact kind, classified ONLY from its own filenames.

    `bucket` is this kind's entry from `classify`. Nothing in this function can
    see another artifact's files, which is what defects 6 and 7 were.
    """
    record = dict(artifact=name, kind=kind, who_writes_it=who_writes_it,
                  final_pattern=KINDS[kind]['final'],
                  temporary_pattern=KINDS[kind]['temporary'])
    if extra:
        record.update(extra)
    if not listable:
        record.update(state='inaccessible', reason=why_unlistable, paths=[],
                      own_temporaries=[])
        return record
    found = list(bucket['final'])
    temporary = list(bucket['temporary'])
    record['paths'] = found
    record['own_temporaries'] = temporary
    if not found:
        if temporary:
            record.update(state='pending', reason=(
                'no final path, but a temporary belonging to THIS artifact exists: '
                'its publication was entered and did not complete. NOT absent, and '
                'NOT a named cause.'))
        else:
            record.update(state='absent', reason=(
                'the directory was listed and no file matching this artifact\'s own '
                'name is in it. The final result is UNAVAILABLE and its cause is '
                'UNKNOWN -- never that publication timed out, and never that nothing '
                'was written elsewhere. Another artifact\'s temporary says nothing '
                'about this one.'))
        return record
    if fields is None:                                  # the log: no parsing
        record['state'] = 'present'
        return record
    reports = [_one_report(path, expected, fields=fields, read=read, what=name)
               for path in found]
    record['reports'] = reports
    present = [one for one in reports if one['state'] == 'present']
    if present:
        record['state'] = 'present'
    else:
        for state in ('inaccessible', 'unknown-cause', 'pending', 'absent'):
            if any(one['state'] == state for one in reports):
                record['state'] = state
                break
        else:
            record['state'] = 'unknown-cause'
    return record


def _linked(controller, place):
    """What the controller report says its siblings are, and whether they are there.

    Exact linkage rather than glob guessing: `enforcement_path`,
    `manager_report_path` and `authoring_log` are paths the controller wrote about
    ITSELF, and `<manager_report_path>.progress.json` is the progress file for that
    incarnation.

    DEFECT 5 LIVED HERE. This used to call `Path(value)` on whatever the report
    carried and catch only `OSError`, so a report with `authoring_log: []` raised
    `TypeError` out of `collect()` and destroyed a perfectly readable workload
    result beside it. A link value is now SHAPE-CHECKED first and a non-string is
    an observation about that link. Malformed links are not followed, and this is
    not a traversal mechanism: it resolves exactly the four members the producer
    names and nothing else.
    """
    links = []
    for one in (controller.get('reports') or []):
        if one.get('state') != 'present':
            continue
        read = one.get('read') or {}
        manager = read.get('manager_report_path')
        derived = (manager + '.progress.json') if isinstance(manager, str) else None
        for label, value in (('enforcement_path', read.get('enforcement_path')),
                             ('authoring_log', read.get('authoring_log')),
                             ('manager_report_path', manager),
                             ('progress (manager_report_path + .progress.json)',
                              derived)):
            record = dict(source=one['path'], link=label)
            if value is None:
                # Either the member is absent, or it is a derived member whose
                # base was absent or malformed. Both are "not named".
                links.append(dict(record, path=None, state='not named by the report',
                                  note='the report does not carry a usable value for '
                                       'this member; for manager_report_path that is '
                                       'expected from a controller incarnation that '
                                       'never composed a child status path'))
                continue
            if not isinstance(value, str):
                links.append(dict(record, path=None, state='malformed',
                                  carried_type=type(value).__name__,
                                  note='the report carries this member as a '
                                       + type(value).__name__ + ' rather than a path '
                                       'string. Reported as a malformed link and NOT '
                                       'followed; every other result in this '
                                       'collection is unaffected.'))
                continue
            try:
                there = Path(value).exists()
            except (OSError, ValueError) as fault:
                links.append(dict(record, path=value, state='inaccessible',
                                  note=type(fault).__name__ + ': ' + str(fault)))
                continue
            inside = None
            try:
                inside = Path(value).parent.resolve() == Path(place).resolve()
            except OSError:
                pass
            links.append(dict(record, path=value,
                              state='found' if there else 'named but not present',
                              in_collected_directory=inside,
                              note=None if there else
                                   'the report names it and it is not there: '
                                   'unavailable, cause unknown. If the run root moved '
                                   'or was copied, these absolute paths will not '
                                   'resolve and that is not evidence about the run.'))
    return links


def _timeout_verdict(results):
    """Defect 3, narrowed again by defect-3b: parsing, never producer persistence."""
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
                    entry['found_how'] = ('PARSED FROM A FAULT ALREADY ON DISK. This '
                                          'vehicle is not known to persist publication '
                                          'faults -- see producer_persistence.')
                    publication.append(entry)
                else:
                    entry['why_not_publication'] = (
                        'a TimeoutError naming no publication step. It is a real '
                        'observed timeout of SOMETHING ELSE -- a startup snapshot, a '
                        'shutdown observation, a cleanup step -- and it says nothing '
                        'about whether a final report was published.')
                    other.append(entry)
    verdict = dict(
        parsed_publication_faults=publication,
        other_timeouts_observed=other,
        uncorrelated_timeouts=uncorrelated,
        producer_persistence=PUBLICATION_PERSISTENCE,
        rule='A publication fault is reported only when a correlated artifact '
             'literally carries a TimeoutError naming one of '
             + ', '.join(PUBLICATION_STEPS) + '. That is PARSING. Absence proves '
             'nothing, because the producers do not reliably record such faults.')
    if publication:
        verdict['established'] = True
        verdict['note'] = (
            'A correlated fault naming a publication step was FOUND ON DISK, so that '
            'step did time out. This is the one case where the cause is readable -- '
            'and it is still not evidence that the producer records such faults in '
            'general, nor that nothing was written: the bound at '
            'authoring_enforcement.py:586-594 spans write_text, os.replace and print, '
            'so check own_temporaries.')
    else:
        verdict['established'] = False
        verdict['note'] = (
            'NOT ESTABLISHED, and for this vehicle NOT ESTABLISHABLE from absence. No '
            'correlated fault naming a publication step is on disk -- which is the '
            'EXPECTED state even when a publication really did time out, because the '
            'producers do not persist those faults (producer_persistence). So this '
            'says nothing either way. An absent or inaccessible report is likewise not '
            'evidence of a timeout: a run that never started, an import or startup '
            'failure (see FAILURE.md), process death, a failed read and non-timeout '
            'publication errors all leave no final report.'
            + (' Timeouts of other steps WERE observed and are listed separately; they '
               'are not publication evidence.' if other else ''))
    return verdict


def collect(place, supplied_run=None):
    place = Path(place)
    listable, why = _listable(place)
    buckets, entries, listing_fault = classify(place, listable)
    if listing_fault:
        listable, why = False, listing_fault
    expected = _expected_identity(place, supplied_run)
    common = dict(listable=listable, why_unlistable=why, expected=expected)

    results = {}
    results['workload'] = _artifact(
        buckets['workload'], kind='workload', name='workload final report',
        fields=WORKLOAD_FIELDS, read=WORKLOAD_READ,
        who_writes_it='the supervisor, post-stop, inside the workload-publication '
                      'reservation (baseline.py:1450-1461)',
        extra=dict(temporary_is='outcome.json.partial, from baseline._publish '
                                '(baseline.py:1006) -- NOT a .tmp'), **common)
    results['controller'] = _artifact(
        buckets['controller'], kind='controller', name='controller final report',
        fields=CONTROLLER_FIELDS, read=CONTROLLER_READ,
        who_writes_it='the outer controller, after supervise_process returns and after '
                      'child cleanup (authoring_enforcement.py:552-591) -- which is '
                      'after any worker inside the run has ended',
        extra=dict(identity_lives_in='original_envelope {run, job, authority}, built at '
                                     'authoring_enforcement.py:40-52 and stored at :580. '
                                     'This report has NO top-level run_id.'), **common)
    results['shutdown_progress'] = _artifact(
        buckets['shutdown_progress'], kind='shutdown_progress',
        name='shutdown progress', fields=PROGRESS_FIELDS, read=PROGRESS_READ,
        who_writes_it='each Shutdown.call, BEFORE running its step '
                      '(authoring_shutdown.py:72-81)',
        extra=dict(meaning='the last step ENTERED. Entering is not finishing, and this '
                           'is not a sampled stack and not a cessation receipt.',
                   faults_it_carries='the faults of EARLIER steps only. A step\'s own '
                                     'fault is appended to memory after the write '
                                     '(authoring_shutdown.py:85) and reaches disk only '
                                     'if a LATER call writes successfully -- see '
                                     'publication_timeout.producer_persistence.'),
        **common)
    results['manager_snapshot'] = _artifact(
        buckets['manager_snapshot'], kind='manager_snapshot',
        name='manager status snapshot',
        fields=(('run_id', lambda p: (p.get('envelope') or {}).get('run')
                 if isinstance(p.get('envelope'), dict) else None, 'envelope.run'),),
        read=('envelope', 'recovery', 'stopping', 'finished',
              'author_invocation_started', 'report'),
        who_writes_it='publish_guard, each observation (authoring_enforcement.py:387-395)',
        extra=dict(note='an observation, never cessation and never a permission grant. '
                        'A missing final snapshot is held. Its name ends at .json: the '
                        'progress and shutdown-request files are NOT snapshots, which '
                        'an earlier revision got wrong.'), **common)
    results['shutdown_request'] = _artifact(
        buckets['shutdown_request'], kind='shutdown_request',
        name='shutdown request', fields=None, read=None,
        who_writes_it='Process.request_shutdown, before terminate() '
                      '(authoring_enforcement.py:342-349)',
        extra=dict(note='the transmitted deadline, not a result. Its presence means a '
                        'bounded shutdown was REQUESTED, not that it completed.'),
        **common)
    results['authoring_log'] = _artifact(
        buckets['authoring_log'], kind='authoring_log', name='authoring log',
        fields=None, read=None, who_writes_it='the run',
        extra=dict(emitted='presence, size and digest ONLY -- the bytes are '
                           'provider-adjacent output and are not this program\'s to '
                           'emit'), **common)
    if results['authoring_log']['state'] == 'present':
        try:
            target = Path(results['authoring_log']['paths'][0])
            results['authoring_log'].update(size_bytes=target.stat().st_size,
                                            sha256=sha(target))
        except OSError as fault:
            results['authoring_log'].update(
                state='inaccessible', reason=type(fault).__name__ + ': ' + str(fault))

    try:
        links = _linked(results['controller'], place)
        link_fault = None
    except Exception as fault:                 # defect 5: belt as well as braces
        links, link_fault = [], ('the linkage pass failed and was isolated: '
                                 + type(fault).__name__ + ': ' + str(fault)
                                 + '. Every artifact result above stands.')

    unavailable = {name: one['state'] for name, one in results.items()
                   if one['state'] in UNAVAILABLE}
    available = sorted(name for name, one in results.items() if one['state'] == 'present')
    return dict(
        schema='baton.w333486-final-result-collection/3',
        collected_from=str(place),
        directory_listable=listable,
        directory_reason=why,
        directory_entries=entries,
        directory_entries_note=('the whole listing, for your information. It is NEVER '
                                'used to infer any artifact\'s state: each artifact '
                                'above is classified only from files matching its own '
                                'anchored name pattern.'),
        composed_packet_members=buckets['composed']['final'],
        unclassified_entries=buckets['other']['final'],
        unclassified_entries_note=('names that are neither one of this vehicle\'s '
                                   'artifacts nor a known composed-packet member. '
                                   'Reported so nothing is silently swallowed; not '
                                   'used to infer any artifact\'s state.'),
        expected_identity=expected,
        results=results,
        available=available,
        unavailable=unavailable,
        isolated_failures=([one['path'] for record in results.values()
                            for one in (record.get('reports') or [])
                            if one.get('isolated')]
                           + ([link_fault] if link_fault else [])),
        linked_artifacts=links,
        publication_timeout=_timeout_verdict(results),
        acceptance=('A missing or partial final report is INCOMPLETE: never success, '
                    'never acceptance and never proof of cessation. No startup success '
                    'and no producer exit substitutes for final-result acceptance. An '
                    'unavailable report retracts nothing already recorded, and neither '
                    'one unreadable artifact nor one malformed link invalidates the '
                    'others.'),
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
