"""Preparation probes for this packet: every refusal, and the collection semantics.

Read-only with respect to the repository and to every retained instance. Each
probe works on a COPY of this packet under its own temporary root, and every
probe that could create a preparation root also asserts whether the root was
created -- because an earlier reference program created a root and wrote 112
files before validating its inputs, and a refusal that leaves a half-staged root
is blocked forever by the refuse-reuse rule.

Nothing here submits a Job, starts an engine or provider, reads a credential, or
runs a product test module. Writes land under the `--work` directory only.

TWO GROUPS.

  * REFUSALS -- `prepare.py` must refuse a packet that would build the wrong
    thing, before anything exists.
  * COLLECTION -- `collect.py` must keep `absent`, `inaccessible`, `pending` and
    `unknown-cause` apart, and must refuse to name a publication timeout without
    correlated positive evidence. One of these cases runs against the REAL
    retained evidence of this Work's one actual execution, which left no workload
    outcome because it died at startup: an absence-means-timeout reader would
    report a timeout that never happened.

ONE PROBE USES SUBSTITUTED NAMES AND SAYS SO. `owed-gate-module-already-on-the-host`
would need a product test file created in the host working tree to be probed
literally. It is probed instead by substituting two module paths that already
exist for the two owed names in the COPY's `prepare.py`, which exercises the same
branch without writing into the repository. Labelled `substituted: true`.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
SUPERSEDED_CONTROLLER = 'bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f'
ZEROES = '0' * 64
CONTROLLER = 'tools/authoring_enforcement.py'
SHUTDOWN = 'tools/authoring_shutdown.py'


def run(argv, **kwargs):
    started = time.monotonic()
    done = subprocess.run(argv, capture_output=True, text=True, **kwargs)
    return done, round(time.monotonic() - started, 3)


def copy_packet(work, name):
    place = work / ('packet-' + name)
    shutil.copytree(HERE, place)
    return place


def edit_json(path, change):
    doc = json.loads(Path(path).read_text())
    change(doc)
    Path(path).write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')


def refusal(work, name, *, mutate=None, step='stage', acknowledge=True,
            root=None, expect_root=False, substituted=False, prepared=None):
    """Run one refusal probe against a copy, and report what actually happened."""
    place = copy_packet(work, name)
    if mutate:
        mutate(place)
    target = Path(root) if root else work / ('root-' + name)
    if prepared:
        prepared(target)
    argv = [sys.executable, '-B', str(place / 'prepare.py'), step,
            '--root', str(target)]
    if acknowledge and step == 'stage':
        argv.append('--acknowledge-unselected-start')
    done, seconds = run(argv)
    text = (done.stderr or '') + (done.stdout or '')
    line = ''
    for one in reversed(text.strip().splitlines()):
        if one.strip():
            line = one.strip()
            break
    created = target.exists()
    return dict(probe=name, status=done.returncode, refused=done.returncode != 0,
                refusal=line[:240], root_created=created,
                root_expected=expect_root,
                passed=done.returncode != 0 and created == expect_root,
                seconds=seconds, substituted=substituted or None)


def collection(work, name, *, build, expect, expect_run=None):
    """Run one collection probe and check exactly the claims it is supposed to make."""
    place = work / ('collect-' + name)
    place.mkdir(parents=True, exist_ok=True)
    target = build(place)
    argv = [sys.executable, '-B', str(HERE / 'collect.py'), '--packet-dir', str(target)]
    if expect_run:
        argv += ['--expect-run', expect_run]
    done, seconds = run(argv)
    held, mismatched = None, []
    if done.returncode != 0:
        mismatched.append('collect.py exited ' + str(done.returncode) + ': '
                          + (done.stderr or '')[-300:])
    else:
        try:
            held = json.loads(done.stdout)
        except json.JSONDecodeError as fault:
            mismatched.append('collect.py did not emit JSON: ' + str(fault))
    if held is not None:
        for key, want in expect.items():
            got = _observed(held, key)
            if got != want:
                mismatched.append(f'{key}: {got!r} != expected {want!r}')
    return dict(probe=name, status=done.returncode, expected=expect,
                observed={key: _observed(held, key) for key in expect} if held else None,
                mismatched=mismatched, passed=not mismatched, seconds=seconds,
                timeout_note=((held or {}).get('publication_timeout', {})
                              .get('note', '') or '')[:120])


def _observed(held, key):
    """Pull one checkable claim out of the collection report."""
    if held is None:
        return None
    timeout = held.get('publication_timeout', {})
    if key == 'publication_timeout_established':
        return timeout.get('established')
    if key == 'publication_evidence_steps':
        return sorted(one.get('publication_step')
                      for one in timeout.get('parsed_publication_faults', []))
    if key == 'other_timeouts_observed':
        return len(timeout.get('other_timeouts_observed', []))
    if key == 'uncorrelated_timeouts':
        return len(timeout.get('uncorrelated_timeouts', []))
    if key == 'available':
        return held.get('available')
    if key == 'identity_source':
        return held['expected_identity'].get('identity_source')
    if key == 'expected_identity_state':
        return held['expected_identity']['state']
    if key == 'linked_states':
        return sorted({one['state'] for one in held.get('linked_artifacts', [])})
    if key == 'isolated_failures':
        return len(held.get('isolated_failures', []))
    if key == 'linked_progress_found':
        return [one['state'] for one in held.get('linked_artifacts', [])
                if one['link'].startswith('progress')]
    if key == 'link_states':
        return {one['link']: one['state'] for one in held.get('linked_artifacts', [])}
    if key == 'parsed_publication_steps':
        return sorted(one.get('publication_step')
                      for one in timeout.get('parsed_publication_faults', []))
    if key == 'parsed_found_how_labelled':
        return all('PARSED FROM A FAULT ALREADY ON DISK' in (one.get('found_how') or '')
                   for one in timeout.get('parsed_publication_faults', []))
    if key == 'producer_persistence_states_unreliable':
        return 'PERSISTS NO PUBLICATION FAULT RELIABLY' in (
            timeout.get('producer_persistence') or '')
    if key == 'unclassified_entries':
        return held.get('unclassified_entries')
    if key.endswith('_own_temporaries'):
        return len(held['results'][key[:-len('_own_temporaries')]].get('own_temporaries') or [])
    if key.endswith('_identity'):
        reports = held['results'][key[:-len('_identity')]].get('reports') or [{}]
        return reports[0].get('identity')
    if key.endswith('_correlated_on'):
        reports = held['results'][key[:-len('_correlated_on')]].get('reports') or [{}]
        return (reports[0].get('identity_detail') or {}).get('correlated_on')
    if key.endswith('_read_state'):
        reports = held['results'][key[:-len('_read_state')]].get('reports') or [{}]
        return (reports[0].get('read') or {}).get('state')
    return held['results'][key]['state']


RUN = re.search(r"^RUN = '([^']+)'$", (HERE / 'prepare.py').read_text(),
                re.M).group(1)
JOB = 'job-' + RUN
AUTHORITY = '00000000000000000000000000000000'


def _controller_report(*, run=RUN, faults=(), state='held', manager_report_path=None,
                       envelope=True, log=None):
    """A controller report in the shape the vehicle ACTUALLY publishes.

    No top-level `run_id`: identity is `original_envelope` {run, job, authority},
    built at authoring_enforcement.py:40-52 and stored at :580. Getting this
    wrong is defect 2.
    """
    report = dict(state=state, faults=list(faults), child_status=1,
                  child_started=True, child_exited=True, elapsed_seconds=1.0,
                  shutdown_deadline=1.0, shutdown_progress=None,
                  operator_signals=[], recovery_only=False,
                  author_invocation_started=None,
                  manager_report_path=manager_report_path, authoring_log=log,
                  enforcement_path='x')
    if envelope:
        report['original_envelope'] = dict(run=run, job=JOB, authority=AUTHORITY,
                                           started_at='x', stop_at='x')
    return report


def _workload_outcome(*, run=RUN, state='settled'):
    return dict(schema='x', run_id=run, work='W333486', claim=339868, job_id=JOB,
                state=state, stopped='completed', held_because=[], uncertainty=[],
                outstanding_cleanup=[], cleanup_sweeps=1, retry=False, finished_at='x')


def _progress(*, run=RUN, step='final enforcement publication', faults=()):
    return dict(run_id=run, job_id=JOB, step=step, deadline=1.0, step_deadline=1.0,
                faults=list(faults))


def _with_packet(place, **kwargs):
    """A packet-dir fixture carrying a composed identity to correlate against.

    The identity members are the ones `_expected_identity` actually reads:
    `run_id`, `work`, `claim`, `submission.job_id`, `deployment.authority_uuid`.
    """
    (place / 'PACKET.json').write_text(json.dumps(dict(
        run_id=RUN, work='W333486', claim=339868,
        submission=dict(job_id=JOB), deployment=dict(authority_uuid=AUTHORITY),
        outcome_path=str(place / 'outcome.json'))) + '\n')
    for name, value in kwargs.items():
        target = place / name.replace('__', '.')
        target.write_text(value if isinstance(value, str)
                          else json.dumps(value, indent=2) + '\n')
    return place


def probes(work):
    cases = []

    # ---- REFUSALS -------------------------------------------------------
    cases.append(refusal(work, 'no-acknowledgement', acknowledge=False))
    cases.append(refusal(
        work, 'superseded-controller',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'authoring_controller'].__setitem__('sha256', SUPERSEDED_CONTROLLER))))
    cases.append(refusal(
        work, 'unpinned-shutdown-helper',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json',
                                   lambda d: d['manager_files'].pop(SHUTDOWN))))
    cases.append(refusal(
        work, 'drifted-shutdown-helper',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'shutdown_helper'].__setitem__('sha256', ZEROES))))
    cases.append(refusal(
        work, 'drifted-manager-source',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'manager_files'].__setitem__(CONTROLLER, ZEROES))))
    cases.append(refusal(
        work, 'drifted-supervisor-baseline',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'supervisor_files'].__setitem__('baseline.py', ZEROES))))
    cases.append(refusal(
        work, 'provenance-claims-selected-start',
        mutate=lambda p: edit_json(p / 'PROVENANCE.json',
                                   lambda d: d.__setitem__('start_selected', True))))
    cases.append(refusal(
        work, 'provenance-claims-authorized-start',
        mutate=lambda p: edit_json(p / 'PROVENANCE.json',
                                   lambda d: d.__setitem__('start_authorized', True))))
    cases.append(refusal(
        work, 'provenance-declares-a-restored-buffer',
        mutate=lambda p: edit_json(p / 'PROVENANCE.json', lambda d: d[
            'checkpoint'].__setitem__('paths', {'v12/python/x.py': 'sha'}))))
    cases.append(refusal(
        work, 'damaged-shutdown-snapshot',
        mutate=lambda p: (p / 'decisions/shutdown-review.md').open('a').write('x')))
    cases.append(refusal(
        work, 'damaged-new-review-snapshot',
        mutate=lambda p: (p / 'decisions/review-339623.md').open('a').write('x')))
    cases.append(refusal(
        work, 'absent-decision-snapshot',
        mutate=lambda p: (p / 'decisions/review-339623.md').unlink()))
    cases.append(refusal(
        work, 'absent-shutdown-document',
        mutate=lambda p: (p / 'SHUTDOWN.md').unlink()))
    cases.append(refusal(
        work, 'absent-task-input',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'task_inputs'].append('work/records/this/does/not/exist.md'))))
    cases.append(refusal(
        work, 'checkout-input-not-at-the-base',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'read_from_checkout_at_base'].append('v12/NOT-AT-THE-BASE.md'))))
    cases.append(refusal(
        work, 'drifted-preparation-input',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'files'].__setitem__(sorted(d['files'])[0], ZEROES))))
    cases.append(refusal(work, 'root-inside-the-repository',
                         root=REPO / 'work/records/2026/10/probe-root'))
    cases.append(refusal(work, 'relative-root', root='probe-relative-root'))
    cases.append(refusal(work, 'existing-root', expect_root=True,
                         prepared=lambda target: target.mkdir(parents=True)))

    # THE RECOVERY INPUT. This slice continues from preserved partial work, so
    # the pins that make those bytes reachable have to refuse the same way the
    # controller and helper pins do. Six cases, matching the six checks.
    def drift_recovery(place, which):
        def mutate(copy):
            edit_json(copy / 'PREPARATION-PINS.json',
                      lambda d: d['recovery_input']['files'].__setitem__(
                          [k for k in d['recovery_input']['files'] if which in k][0],
                          ZEROES))
        return mutate

    cases.append(refusal(work, 'drifted-recovery-producer-diff',
                         mutate=drift_recovery(work, 'producer.diff')))
    cases.append(refusal(work, 'drifted-recovery-producer-source',
                         mutate=drift_recovery(work, 'failure_cause.py')))
    cases.append(refusal(work, 'drifted-recovery-producer-tests',
                         mutate=drift_recovery(work, 'test_attempt_failure_cause.py')))
    cases.append(refusal(
        work, 'recovery-input-not-a-task-input',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'task_inputs'].remove(d['recovery_input']['diff_relative']))))
    cases.append(refusal(
        work, 'recovery-index-names-another-parent-snapshot',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'recovery_input'].__setitem__('parent_tracked_diff_sha256', ZEROES))))
    cases.append(refusal(
        work, 'absent-recovery-document',
        mutate=lambda p: (p / 'RECOVERY.md').unlink()))
    # THE CUTOFFS MUST REACH THE WORKER. review341628 is explicit that placing
    # them only in PROGRESS is insufficient, so their absence is a refusal.
    cases.append(refusal(
        work, 'absent-completion-document',
        mutate=lambda p: (p / 'COMPLETION.md').unlink()))
    cases.append(refusal(
        work, 'completion-document-not-a-task-input',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'task_inputs'].remove([k for k in d['task_inputs']
                                   if k.endswith('/COMPLETION.md')][0]))))
    cases.append(refusal(
        work, 'recovery-disagrees-with-the-reviewers-published-digest',
        mutate=lambda p: edit_json(p / 'PREPARATION-PINS.json', lambda d: d[
            'recovery_input']['reviewer_published_digests'].__setitem__(
                'failure_cause.py', ZEROES))))

    # TWO BIND-SIDE REFUSALS.    # TWO BIND-SIDE REFUSALS. Both need a real staged root first, so they stage
    # into their own root and then ask `bind` to do the wrong thing with it.
    staged = work / 'root-bind-cases'
    done, seconds = run([sys.executable, '-B', str(HERE / 'prepare.py'), 'stage',
                         '--root', str(staged), '--acknowledge-unselected-start'])
    assert done.returncode == 0, 'the bind probes need a staged root: ' + done.stderr[-300:]
    cases.append(dict(probe='stage-for-the-bind-cases', status=0, refused=False,
                      refusal='(staged on purpose; the two probes below use it)',
                      root_created=True, root_expected=True, passed=True,
                      seconds=seconds, substituted=None))
    # `bind` before bootstrap cannot compose, so point a COPY whose RUN differs
    # at this root: the run-identity check must refuse before anything else.
    def other_run(place):
        # Derived, never hardcoded: an earlier revision pinned the run string
        # here and the probe broke the moment the run id changed.
        program = place / 'prepare.py'
        original = program.read_text()
        text = re.sub(r"^RUN = '[^']+'$", "RUN = 'attempt-diagnostics-w333486-000000'",
                      original, count=1, flags=re.M)
        assert text != original, 'the RUN constant in prepare.py moved'
        program.write_text(text)
    cases.append(refusal(work, 'bind-a-root-staged-for-another-run', step='bind',
                         mutate=other_run, root=staged, expect_root=True))
    # And a root that already holds a composed packet must not be rebound.
    def composed(target):
        (target / 'packet').mkdir(parents=True, exist_ok=True)
        (target / 'packet/PACKET.json').write_text('{}\n')
    composed(staged)
    cases.append(refusal(work, 'rebind-over-a-composed-packet', step='bind',
                         root=staged, expect_root=True))

    # The owed-module branch, probed with SUBSTITUTED names so that nothing is
    # written into the host product tree. See the module docstring.
    def substitute(place):
        program = place / 'prepare.py'
        text = program.read_text().replace(
            "for name in ('v12/python/tests/manager/test_attempt_failure_cause.py',):",
            "for name in ('v12/python/tests/manager/test_intake.py',):")
        assert text != program.read_text(), 'the owed-module branch moved'
        program.write_text(text)
    cases.append(refusal(work, 'owed-gate-module-already-on-the-host',
                         mutate=substitute, substituted=True))

    # ---- COLLECTION -----------------------------------------------------
    # Every case states the exact claim it checks. The first four are
    # review339861's own fixtures, reproduced here as regressions for the four
    # defects they found; the rest are the cases that review required.

    # Defect 1: a present, readable, correlated workload report must be READ.
    cases.append(collection(
        work, 'present-workload-is-read',
        build=lambda place: _with_packet(place, **{'outcome.json': _workload_outcome()}),
        expect=dict(workload='present', workload_identity='matched',
                    workload_read_state='settled',
                    workload_correlated_on=['run_id', 'job_id', 'work', 'claim'],
                    available=['workload'],
                    publication_timeout_established=False)))

    # Defect 2: the REAL controller shape correlates, through original_envelope.
    cases.append(collection(
        work, 'actual-controller-shape-correlates',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': _controller_report()}),
        expect=dict(controller='present', controller_identity='matched',
                    controller_correlated_on=['original_envelope.run',
                                              'original_envelope.job',
                                              'original_envelope.authority'],
                    publication_timeout_established=False)))

    # Defect 3: an unrelated TimeoutError, in a CORRELATED report, is not a
    # publication timeout. It is reported as the timeout of something else.
    cases.append(collection(
        work, 'unrelated-timeout-is-not-publication',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': _controller_report(
                faults=['TimeoutError: manager startup snapshot'])}),
        expect=dict(controller='present', controller_identity='matched',
                    publication_timeout_established=False,
                    other_timeouts_observed=1, uncorrelated_timeouts=0)))

    # Defect 4: a non-object report is an observation, and the OTHER artifacts
    # are still collected rather than lost to an exception.
    cases.append(collection(
        work, 'nonobject-report-does-not-abort-collection',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': '[]',
                      'outcome.json': _workload_outcome()}),
        expect=dict(controller='unknown-cause', workload='present',
                    available=['workload'], publication_timeout_established=False)))

    # A publication fault that is LITERALLY ON DISK is parsed and reported --
    # and the report says so, because this is a SYNTHETIC fixture and NOT
    # evidence that the producer persists such faults. An earlier revision of
    # this probe was labelled a "producer-shaped positive fixture", which was
    # false: Shutdown.call writes the snapshot with EARLIER faults
    # (authoring_shutdown.py:76-81), runs the step, then appends that step's
    # fault to memory only (:85). `final enforcement publication`
    # (authoring_enforcement.py:493) is the LAST such call, so nothing flushes
    # it. review-340012 item 3 caught the claim; the fixture now tests PARSING.
    cases.append(collection(
        work, 'publication-fault-on-disk-is-parsed-not-producer-proof',
        build=lambda place: _with_packet(
            place, **{'outcome.json.manager-1-2.json.progress.json': _progress(
                faults=['TimeoutError: final enforcement publication'])}),
        expect=dict(shutdown_progress='present',
                    shutdown_progress_identity='matched',
                    publication_timeout_established=True,
                    parsed_publication_steps=['final enforcement publication'],
                    parsed_found_how_labelled=True,
                    producer_persistence_states_unreliable=True,
                    other_timeouts_observed=0)))

    # And with nothing on disk, the verdict must say NOT ESTABLISHABLE from
    # absence rather than merely "not established".
    cases.append(collection(
        work, 'absent-publication-fault-stays-unknown',
        build=lambda place: _with_packet(
            place, **{'outcome.json.manager-1-2.json.progress.json': _progress(
                step='workload publication')}),
        expect=dict(shutdown_progress='present',
                    publication_timeout_established=False,
                    producer_persistence_states_unreliable=True,
                    parsed_publication_steps=[])))

    # A conflicting identity is a mismatch, never a silent pass.
    cases.append(collection(
        work, 'conflicting-identity-is-mismatch',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json':
                      _controller_report(run='some-other-run')}),
        expect=dict(controller='unknown-cause', controller_identity='mismatch',
                    publication_timeout_established=False)))

    # A controller incarnation that never established an envelope carries no
    # identity at all: unresolved, stated as such.
    cases.append(collection(
        work, 'no-envelope-is-unresolved',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json':
                      _controller_report(envelope=False)}),
        expect=dict(controller='present', controller_identity='unresolved',
                    publication_timeout_established=False)))

    # A timeout in an UNCORRELATED report is not evidence about this run.
    cases.append(collection(
        work, 'uncorrelated-timeout-is-not-evidence',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': _controller_report(
                run='some-other-run',
                faults=['TimeoutError: outer outcome publication'])}),
        expect=dict(controller='unknown-cause', controller_identity='mismatch',
                    publication_timeout_established=False,
                    uncorrelated_timeouts=1, other_timeouts_observed=0)))

    # Exact linkage: the controller names its own manager report path, and the
    # progress file for that incarnation is <that>.progress.json.
    def linked(place):
        manager = place / 'outcome.json.manager-7-8.json'
        _with_packet(place, **{
            'outcome.json.enforcement-1-2.json': _controller_report(
                manager_report_path=str(manager)),
            'outcome.json.manager-7-8.json': dict(
                envelope=dict(run=RUN, job=JOB, authority=AUTHORITY),
                recovery=False, stopping=True, finished=False,
                author_invocation_started=None, report={}),
            'outcome.json.manager-7-8.json.progress.json': _progress(step='cleanup')})
        return place
    cases.append(collection(
        work, 'linked-progress-resolves-from-the-report',
        build=linked,
        expect=dict(controller='present', shutdown_progress='present',
                    manager_snapshot='present',
                    shutdown_progress_identity='matched',
                    linked_progress_found=['found'],
                    publication_timeout_established=False)))

    # A read failure on one artifact leaves the others intact.
    def read_failure(place):
        _with_packet(place, **{'outcome.json': _workload_outcome(),
                               'outcome.json.enforcement-1-2.json': _controller_report()})
        os.chmod(place / 'outcome.json.enforcement-1-2.json', 0o000)
        return place
    cases.append(collection(
        work, 'read-failure-is-isolated',
        build=read_failure,
        expect=dict(controller='inaccessible', workload='present',
                    available=['workload'], publication_timeout_established=False)))

    # Nothing published at all, and the directory itself unreadable.
    cases.append(collection(
        work, 'nothing-published',
        build=lambda place: _with_packet(place),
        expect=dict(controller='absent', workload='absent',
                    shutdown_progress='absent', authoring_log='absent',
                    available=[], publication_timeout_established=False)))
    cases.append(collection(
        work, 'inaccessible-is-not-absent',
        build=lambda place: (_with_packet(place), os.chmod(place, 0o000), place)[-1],
        expect=dict(controller='inaccessible', workload='inaccessible',
                    shutdown_progress='inaccessible', authoring_log='inaccessible',
                    publication_timeout_established=False)))
    # THE REAL TEMPORARY NAMES, read from the producers. `with_suffix('.tmp')`
    # REPLACES `.json`, so the controller temporary is `...enforcement-1-2.tmp`
    # and not `...enforcement-1-2.json.tmp`; and the workload temporary is
    # `outcome.json.partial`, not a `.tmp` at all. An earlier revision of this
    # probe invented both and so proved nothing.
    cases.append(collection(
        work, 'controller-own-temporary-is-pending',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.tmp': '{"partial":'}),
        expect=dict(controller='pending', controller_own_temporaries=1,
                    workload='absent', shutdown_progress='absent',
                    manager_snapshot='absent', unclassified_entries=[],
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'workload-own-temporary-is-pending',
        build=lambda place: _with_packet(
            place, **{'outcome.json.partial': '{"partial":'}),
        expect=dict(workload='pending', workload_own_temporaries=1,
                    controller='absent', unclassified_entries=[],
                    publication_timeout_established=False)))

    # DEFECT 6: one artifact's temporary must not mark the others pending.
    cases.append(collection(
        work, 'unrelated-temporary-cannot-fabricate-pending',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.tmp': '{"partial":',
                      'outcome.json.manager-3-4.json.progress.json': _progress(step='cleanup')}),
        expect=dict(controller='pending', shutdown_progress='present',
                    workload='absent', manager_snapshot='absent',
                    shutdown_request='absent',
                    workload_own_temporaries=0, manager_snapshot_own_temporaries=0,
                    publication_timeout_established=False)))

    # DEFECT 7: the progress file is not a manager snapshot.
    cases.append(collection(
        work, 'progress-is-not-a-manager-snapshot',
        build=lambda place: _with_packet(
            place, **{'outcome.json.manager-1-2.json.progress.json': _progress(step='cleanup')}),
        expect=dict(shutdown_progress='present', manager_snapshot='absent',
                    shutdown_request='absent', available=['shutdown_progress'],
                    unclassified_entries=[],
                    publication_timeout_established=False)))

    # DEFECT 5: a malformed LINK must not cost the readable artifacts. This is the
    # reviewer's own fixture shape -- a correlated controller carrying
    # `authoring_log: []` beside a valid workload report.
    cases.append(collection(
        work, 'malformed-link-does-not-lose-other-results',
        build=lambda place: _with_packet(
            place, **{'outcome.json': _workload_outcome(),
                      'outcome.json.enforcement-1-2.json': _controller_report(log=[])}),
        expect=dict(workload='present', controller='present',
                    available=['controller', 'workload'],
                    link_states={'enforcement_path': 'named but not present',
                                 'authoring_log': 'malformed',
                                 'manager_report_path': 'not named by the report',
                                 'progress (manager_report_path + .progress.json)':
                                     'not named by the report'},
                    isolated_failures=0,
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'unparseable-report-is-unknown-cause',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': 'not json at all'}),
        expect=dict(controller='unknown-cause',
                    publication_timeout_established=False)))
    # An unreadable PACKET.json means nothing can be correlated, and that is
    # reported rather than passed.
    cases.append(collection(
        work, 'no-composed-packet-is-unresolved',
        build=lambda place: (
            (place / 'outcome.json.enforcement-1-2.json').write_text(
                json.dumps(_controller_report()) + '\n'), place)[-1],
        expect=dict(controller='present', controller_identity='unresolved',
                    publication_timeout_established=False)))

    # An --expect-run that contradicts a readable packet is refused outright,
    # rather than silently correlating against one of two different runs.
    cases.append(collection(
        work, 'expect-run-contradicting-the-packet-is-refused',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': _controller_report()}),
        expect_run='some-other-run',
        expect=dict(expected_identity_state='unknown-cause',
                    controller_identity='unresolved',
                    publication_timeout_established=False)))

    # And the real thing: this Work's one actual execution, read-only copies. The
    # evidence directory holds the published artifacts but NOT the composed
    # packet, so it is collected both ways.
    REAL = REPO / 'work/records/2026/10/finding-v12-attempt-failure-diagnostics/evidence/execution-334663-failure'
    cases.append(collection(
        work, 'real-retained-failure-evidence',
        build=lambda place: REAL,
        expect=dict(controller='present', controller_identity='unresolved',
                    workload='absent', shutdown_progress='absent',
                    authoring_log='present', available=['authoring_log', 'controller'],
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'real-retained-failure-evidence-correlated',
        build=lambda place: REAL,
        expect_run='attempt-diagnostics-w333486-334663',
        expect=dict(controller='present', controller_identity='matched',
                    controller_correlated_on=['original_envelope.run'],
                    identity_source='--expect-run, supplied by the operator',
                    workload='absent', authoring_log='present',
                    publication_timeout_established=False)))
    return cases


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', required=True,
                        help='a fresh absolute temporary directory; the only '
                             'place this program writes')
    args = parser.parse_args()
    work = Path(args.work)
    if not work.is_absolute() or REPO in work.parents or work == REPO:
        raise SystemExit('select a fresh absolute temporary work directory '
                         'outside the repository')
    work.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    cases = probes(work)
    elapsed = round(time.monotonic() - started, 3)
    # Leave nothing unreadable behind for the reviewer.
    for one in work.glob('collect-*'):
        try:
            os.chmod(one, 0o700)
        except OSError:
            pass
    report = dict(schema='baton.w333486-preparation-probes/1', work=str(work),
                  cases=cases, seconds=elapsed,
                  passed=sum(1 for one in cases if one['passed']),
                  total=len(cases),
                  all_passed=all(one['passed'] for one in cases))
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write('\n')
    raise SystemExit(0 if report['all_passed'] else 1)
