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


def collection(work, name, *, build, expect):
    """Run one collection probe and check the states it reports."""
    place = work / ('collect-' + name)
    place.mkdir(parents=True, exist_ok=True)
    target = build(place)
    done, seconds = run([sys.executable, '-B', str(HERE / 'collect.py'),
                         '--packet-dir', str(target)])
    held, mismatched = None, []
    if done.returncode == 0:
        held = json.loads(done.stdout)
        for key, want in expect.items():
            if key == 'publication_timeout_established':
                got = held['publication_timeout']['established']
            elif key == 'controller_identity':
                reports = held['results']['controller'].get('reports') or [{}]
                got = reports[0].get('identity')
            else:
                got = held['results'][key]['state']
            if got != want:
                mismatched.append(f'{key}: {got!r} != expected {want!r}')
    else:
        mismatched.append('collect.py exited ' + str(done.returncode) + ': '
                          + (done.stderr or '')[-200:])
    return dict(probe=name, status=done.returncode, expected=expect,
                mismatched=mismatched, passed=not mismatched, seconds=seconds,
                timeout_note=(held or {}).get('publication_timeout', {}).get('note', '')[:140])


def _report(run_id='attempt-diagnostics-w333486-339628', faults=(), state='held'):
    return dict(schema='x', run_id=run_id, state=state, faults=list(faults),
                child_status=1, child_started=True, child_exited=True,
                elapsed_seconds=1.0, shutdown_deadline=1.0,
                shutdown_progress=None, enforcement_path='x',
                manager_report_path='x', author_invocation_started=None,
                recovery_only=False)


def _with_packet(place, **kwargs):
    """A packet-dir fixture carrying a composed identity to correlate against."""
    (place / 'PACKET.json').write_text(json.dumps(dict(
        run_id='attempt-diagnostics-w333486-339628', work='W333486', claim=339628,
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

    # TWO BIND-SIDE REFUSALS. Both need a real staged root first, so they stage
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
        program = place / 'prepare.py'
        text = program.read_text().replace(
            "RUN = 'attempt-diagnostics-w333486-339628'",
            "RUN = 'attempt-diagnostics-w333486-000000'")
        assert text != program.read_text(), 'the run constant moved'
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
            "for name in ('v12/python/tests/manager/test_attempt_failure_cause.py',\n"
            "                 'v12/python/tests/tools/test_attempt_diagnostics.py'):",
            "for name in ('v12/python/tests/manager/test_intake.py',\n"
            "                 'v12/python/tests/tools/test_worker_visibility.py'):")
        assert text != program.read_text(), 'the owed-module branch moved'
        program.write_text(text)
    cases.append(refusal(work, 'owed-gate-module-already-on-the-host',
                         mutate=substitute, substituted=True))

    # ---- COLLECTION -----------------------------------------------------
    cases.append(collection(
        work, 'nothing-published',
        build=lambda place: _with_packet(place),
        expect=dict(controller='absent', workload='absent',
                    shutdown_progress='absent', authoring_log='absent',
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'inaccessible-is-not-absent',
        build=lambda place: (_with_packet(place), os.chmod(place, 0o000), place)[-1],
        expect=dict(controller='inaccessible', workload='inaccessible',
                    shutdown_progress='inaccessible', authoring_log='inaccessible',
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'partial-temporary-is-pending',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json.tmp': '{"partial":'}),
        expect=dict(controller='pending', workload='pending',
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'unparseable-report-is-unknown-cause',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json': 'not json at all'}),
        expect=dict(controller='unknown-cause',
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'uncorrelated-report-is-unknown-cause',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json':
                      _report(run_id='some-other-run')}),
        expect=dict(controller='unknown-cause', controller_identity='mismatch',
                    publication_timeout_established=False)))
    cases.append(collection(
        work, 'timeout-named-only-on-positive-evidence',
        build=lambda place: _with_packet(
            place, **{'outcome.json.enforcement-1-2.json':
                      _report(faults=['TimeoutError: outer outcome publication'])}),
        expect=dict(controller='present', controller_identity='matched',
                    publication_timeout_established=True)))
    cases.append(collection(
        work, 'real-retained-failure-evidence',
        build=lambda place: REPO / 'work/records/2026/10/finding-v12-attempt-failure-diagnostics/evidence/execution-334663-failure',
        expect=dict(controller='present', workload='absent',
                    shutdown_progress='absent', authoring_log='present',
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
