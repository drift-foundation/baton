"""One reviewed W71879 submission and ordinary CLI serve, with a deadline guard.

Read-only Authority owners and Docker observations measure the run. There is
no receipt/claim/transition API in this script. Failure/deadline containment
terminates this script's serving process and stops only this Authority's
labelled containers, retaining all state for diagnosis. No retry or repair.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from baton_v12.authority import Authority
from failure_observation import first_failure, provider_diagnostic
from target_posture import manager_git_environment
from deployment import ACTORS, BASE, CONFIG, HERE, REPO, RUN, TREE, UUID, WORKS, baseline, git_read, sha, write_json

PYTHON = '/usr/bin/python3'
CWD = REPO / 'v12/python'
PREFIX = ['/usr/bin/env', 'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=src:.', PYTHON, '-m', 'tools.job_manager',
          '--store', str(RUN / 'jobs.sqlite3'), '--incarnation', 'w71879-run7', '--authority-uuid', UUID]
SERVE = ['/usr/bin/env', 'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=src:.',
         'BATON_V12_STAGE_EXECUTION_CONFIG=' + str(CONFIG / 'stage-execution.json'),
         PYTHON, '-m', 'tools.job_manager', '--store', str(RUN / 'jobs.sqlite3'),
         '--incarnation', 'w71879-run7', '--authority-uuid', UUID, 'serve',
         '--control', str(RUN / 'control.sqlite3'), '--operations', 'tools.stage_execution:factory', '--interval', '1']
STATUS = PREFIX[:3] + ['BATON_V12_STAGE_EXECUTION_CONFIG=' + str(CONFIG / 'stage-execution.json')] + PREFIX[3:] + ['status', '--control', str(RUN / 'control.sqlite3'), '--observe', 'tools.stage_execution:observing_factory']
LIMITS = {ACTORS[name]: (240 if name.startswith('impl-') else 120 if name == 'integrator' else 180)
          for name in ACTORS if name != 'observer'}


class RequiredAttemptFailure(RuntimeError):
    """The current required attempt has a definitive failed owner answer."""


def command(argv, *, seconds=10):
    done = subprocess.run(argv, cwd=CWD, capture_output=True, text=True, timeout=seconds)
    if done.returncode:
        raise RuntimeError('command failed: ' + repr(argv) + '\n' + done.stderr[:2000])
    return done.stdout


def stats_observation(runtime_rows):
    """One bounded telemetry read; required commands and watchdogs stay strict."""
    ids = [row['Id'] for row in runtime_rows]
    began = time.monotonic()
    result = {'state': 'not-requested', 'requested_ids': ids,
              'started_at': datetime.now(timezone.utc).isoformat(),
              'exit_code': None, 'error': None, 'stdout': '', 'stderr': '',
              'stdout_truncated': False, 'stderr_truncated': False,
              'stdout_characters': 0, 'stderr_characters': 0}
    stdout, stderr = '', ''
    if ids:
        argv = ['docker', 'stats', '--no-stream', '--format', '{{json .}}', *ids]
        try:
            done = subprocess.run(argv, cwd=CWD, capture_output=True, text=True, timeout=10)
            stdout, stderr = done.stdout, done.stderr
            result['exit_code'] = done.returncode
            result['state'] = 'available' if done.returncode == 0 and stdout.strip() else 'unavailable'
            if result['state'] == 'unavailable':
                result['error'] = {'type': 'nonzero-exit' if done.returncode else 'empty-output'}
        except subprocess.TimeoutExpired as failure:
            # Do not catch OSError/Exception: the independently armed alarm's
            # built-in TimeoutError must propagate to ordinary containment.
            stdout, stderr = failure.stdout, failure.stderr
            result['state'] = 'unavailable'
            result['error'] = {'type': 'subprocess.TimeoutExpired', 'timeout_seconds': failure.timeout}
    for name, output, limit in (('stdout', stdout, 65536), ('stderr', stderr, 8192)):
        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='replace')
        output = output or ''
        result[name] = output[:limit]
        result[name + '_characters'] = len(output)
        result[name + '_truncated'] = len(output) > limit
    result['ended_at'] = datetime.now(timezone.utc).isoformat()
    result['elapsed_seconds'] = time.monotonic() - began
    return result


def containers():
    raw = command(['docker', 'ps', '--no-trunc', '--filter', 'label=baton.v12.authority_uuid=' + UUID, '--format', '{{.ID}}'])
    ids = raw.split()
    if not ids:
        return []
    rows = json.loads(command(['docker', 'inspect', *ids]))
    for row in rows:
        if row['Config']['Labels'].get('baton.v12.authority_uuid') != UUID:
            raise RuntimeError('runtime observation crossed the configured Authority')
    return rows


def retained_bytes():
    # Size metadata only. No credential contents are read or copied.
    total = 0
    for parent, dirs, files in os.walk(RUN, followlinks=False):
        dirs[:] = [name for name in dirs if not Path(parent, name).is_symlink()]
        for name in files:
            try:
                total += Path(parent, name).lstat().st_size
            except FileNotFoundError:
                pass
    return total


def stop_serving(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)


def main():
    approval = json.loads((HERE / 'execution-review.json').read_text())
    if approval.get('verdict') != 'accepted' or not approval.get('review_locator'):
        raise RuntimeError('existing independent material-delta review is required')
    for name in ('stage-execution.json', 'submission.json'):
        if approval['config_files'][name] != sha(CONFIG / name):
            raise RuntimeError('reviewed executable document drift: ' + name)
    for path, expected in approval['reviewed_files'].items():
        if sha(Path(path)) != expected:
            raise RuntimeError('reviewed input or helper drift: ' + path)
    if any(str(path) not in approval['reviewed_files'] for path in (HERE / 'run.py', HERE / 'deployment.py', HERE / 'target_posture.py', HERE / 'failure_observation.py')):
        raise RuntimeError('the existing review must bind all four execution helpers')
    if 1001 not in set(os.getgroups()):
        raise RuntimeError('manager launch boundary lacks supplementary workspace gid1001')
    if (RUN / 'jobs.sqlite3').exists() or containers():
        raise RuntimeError('this entry submits once into a fresh Job store; no automatic retry')
    initial = baseline()
    capacity = json.loads(command(['docker', 'info', '--format', '{"cpus":{{.NCPU}},"memory":{{.MemTotal}}}']))
    available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))) * 1024
    disk = os.statvfs(RUN)
    if capacity['cpus'] < 20 or capacity['memory'] < 21474836480 or available < 23622320128 or disk.f_bavail * disk.f_frsize < 17179869184:
        raise RuntimeError('host capacity no longer meets the reviewed20CPU/20GiB plus headroom and16GiB storage plan')
    evidence = RUN / 'evidence'
    started = time.monotonic()
    record = {'started_at': datetime.now(timezone.utc).isoformat(), 'submitted': False,
              'terminal_both': False, 'initial': initial, 'exceptional_stops': [], 'ordinary_operator_transitions': 0}
    record['stats_observations'] = {'available': 0, 'unavailable': 0, 'not-requested': 0,
                                  'gaps': [], 'truncated_samples': [],
                                  'coverage': 'sampled command output only; gaps are not measurements or lifecycle results'}
    sample_number = 0
    serve = None
    authority = None

    def alarm(_signum, _frame):
        raise TimeoutError('approved proof wall/active-attempt deadline reached')

    previous_alarm = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 1200)
    try:
        response = command(PREFIX + ['submit', '--document', str(CONFIG / 'submission.json')])
        (evidence / 'submit.json').write_text(response)
        record['submitted'] = True
        authority = Authority.open_readonly(str(RUN / 'authority.sqlite3'), expected_authority_uuid=UUID)
        with (evidence / 'serve.log').open('x') as log, (evidence / 'samples.jsonl').open('x') as samples:
            serve = subprocess.Popen(SERVE, cwd=CWD, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=manager_git_environment(RUN / 'target'))
            while True:
                if serve.poll() is not None:
                    raise RuntimeError('ordinary serve exited before both terminal Jobs')
                elapsed = time.monotonic() - started
                if elapsed >= 1200:
                    raise RuntimeError('approved1200s wall deadline reached')
                claims = {}
                now = datetime.now(timezone.utc)
                remaining = 1200 - elapsed
                for name, work_id in WORKS.items():
                    current = authority.assignment_of(work_id)
                    events = authority.assignment_events(work_id)
                    claims[name] = {'current': current, 'events': events}
                    for index, event in enumerate(events):
                        if event['cause'] != 'claimed':
                            continue
                        ending = next((later for later in events[index + 1:] if later['assignment_ref'] == event['assignment_ref']), None)
                        if ending:
                            began = datetime.fromisoformat(event['at'].replace('Z', '+00:00'))
                            ended = datetime.fromisoformat(ending['at'].replace('Z', '+00:00'))
                            if (ended - began).total_seconds() > LIMITS[event['assignment_ref']['participant']]:
                                raise RuntimeError('a completed claim exceeded its approved attempt limit: ' + work_id)
                    if current:
                        matched = [event for event in events if event['cause'] == 'claimed' and event['assignment_ref'] == current]
                        if not matched:
                            raise RuntimeError('public owner supplied no matching claim timestamp')
                        stamp = datetime.fromisoformat(matched[-1]['at'].replace('Z', '+00:00'))
                        age = (now - stamp).total_seconds()
                        if age >= LIMITS[current['participant']]:
                            raise RuntimeError('approved attempt deadline reached: ' + work_id + '/' + current['participant'])
                        remaining = min(remaining, LIMITS[current['participant']] - age)
                signal.setitimer(signal.ITIMER_REAL, max(0.001, remaining))
                runtime_rows = containers()
                held_bytes = retained_bytes()
                if held_bytes >= 17179869184:
                    raise RuntimeError('retained run storage reached16GiB stop threshold')
                # Before first serve initialization the control store can be
                # absent. That is startup, not a status command to run against
                # a made-up store. Once present, use the existing read-only
                # observation factory; no serving producer is constructed.
                status = json.loads(command(STATUS)) if (RUN / 'control.sqlite3').exists() else None
                failed = first_failure(status, authority_uuid=UUID, incarnation=PREFIX[PREFIX.index('--incarnation') + 1], works=WORKS)
                if failed is not None:
                    # Set primary evidence before optional diagnostics/telemetry.
                    # Pending collection and quiescence alone never reach here.
                    failed.update(sample='samples.jsonl:' + str(sample_number + 1), wall_seconds=elapsed)
                    record['primary_failure'] = failed
                    samples.write(json.dumps({'wall_seconds': elapsed, 'claims': claims, 'status': status,
                                              'runtime_observations': runtime_rows, 'docker_stats': None,
                                              'telemetry_skipped': 'definitive required-attempt failure',
                                              'retained_bytes': held_bytes}) + '\n')
                    samples.flush()
                    raise RequiredAttemptFailure('definitive required attempt failed: ' + failed['stage_id'])
                stats = stats_observation(runtime_rows)
                sample = {'wall_seconds': elapsed, 'claims': claims, 'status': status,
                          'runtime_observations': runtime_rows, 'docker_stats': stats,
                          'retained_bytes': held_bytes}
                samples.write(json.dumps(sample) + '\n')
                samples.flush()
                sample_number += 1
                summary = record['stats_observations']
                summary[stats['state']] += 1
                locator = 'samples.jsonl:' + str(sample_number)
                if stats['state'] == 'unavailable':
                    summary['gaps'].append({'sample': locator, 'requested_ids': stats['requested_ids'], 'error': stats['error']})
                if stats['stdout_truncated'] or stats['stderr_truncated']:
                    summary['truncated_samples'].append(locator)
                if status and {job['job_id'] for job in status['jobs']} == {'job-a', 'job-b'} and all(
                        stage['state'] == 'completed' for job in status['jobs'] for stage in job['stages']):
                    record['terminal_both'] = True
                    record['terminal_wall_seconds'] = time.monotonic() - started
                    write_json(evidence / 'terminal-status.json', status)
                    if runtime_rows:
                        raise RuntimeError('terminal stages still have a live labelled runtime')
                    break
                time.sleep(min(1, max(0, 1200 - (time.monotonic() - started))))
        signal.setitimer(signal.ITIMER_REAL, 0)
        stop_serving(serve)
        verify = subprocess.run([PYTHON, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                cwd=RUN / 'target', capture_output=True, text=True, timeout=30)
        (evidence / 'final-tests.log').write_text(verify.stdout + verify.stderr)
        record['final_test_exit'] = verify.returncode
        if verify.returncode:
            raise RuntimeError('whole-target final tests failed')
        record['final_source_identity'] = git_read(RUN / 'source', 'show', '--no-patch', '--format=%H %T', 'HEAD')
        record['final_source_status'] = git_read(RUN / 'source', 'status', '--porcelain')
        record['final_target_identity'] = git_read(RUN / 'target', 'show', '--no-patch', '--format=%H %T', 'HEAD')
        record['final_target_status'] = git_read(RUN / 'target', 'status', '--porcelain')
        (evidence / 'final-target.diff').write_text(git_read(RUN / 'target', 'diff', '--binary', BASE, 'HEAD') + '\n')
        if record['final_source_identity'] != BASE + ' ' + TREE or record['final_source_status'] or record['final_target_status']:
            raise RuntimeError('source changed or final target is dirty')
        record['result'] = 'both terminal; final verification passed; independent evidence assessment still owed'
    except BaseException as failure:
        signal.setitimer(signal.ITIMER_REAL, 0)
        primary = record.get('primary_failure')
        if primary is not None:
            record['failure'] = 'RequiredAttemptFailure: ' + primary['stage_id'] + '/' + primary['attempt_id'] + ' ' + (primary['disposition'] or primary['ending'])
            if not isinstance(failure, RequiredAttemptFailure):
                record['secondary_failure'] = type(failure).__name__
            write_json(evidence / 'first-failure.json', primary)
        else:
            record['failure'] = type(failure).__name__ + ': ' + str(failure)
        if serve is not None:
            try:
                stop_serving(serve)
            except BaseException as stop_failure:
                record['serve_containment_failure'] = type(stop_failure).__name__
        # Exceptional containment only. It cannot make a Job pass or clear a
        # claim. Retain the exact acted-on runtime IDs and all manager state.
        try:
            for row in containers():
                action = ['docker', 'stop', '--time', '2', row['Id']]
                record['exceptional_stops'].append({'argv': action, 'answer': command(action, seconds=5)})
        except BaseException as stop_failure:
            record['containment_failure'] = str(stop_failure)
        if primary is not None:
            # Contain first; a missing or invalid diagnostic cannot mask the
            # owner failure or postpone it until another deadline.
            diagnostic = provider_diagnostic(primary, run_root=RUN, incarnation=PREFIX[PREFIX.index('--incarnation') + 1])
            record['provider_diagnostic'] = diagnostic
            write_json(evidence / 'failure-diagnostic.json', diagnostic)
            raise RequiredAttemptFailure(record['failure']) from None
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_alarm)
        cleanup_failure = None
        for cleanup in ((lambda: stop_serving(serve)) if serve is not None else None,
                        authority.dispose if authority is not None else None):
            if cleanup is None:
                continue
            try:
                cleanup()
            except BaseException as cleanup_error:
                record.setdefault('cleanup_failures', []).append(type(cleanup_error).__name__)
                cleanup_failure = cleanup_error
        record['wall_seconds'] = time.monotonic() - started
        if cleanup_failure is not None and 'failure' not in record:
            record['failure'] = 'cleanup failed: ' + type(cleanup_failure).__name__
            record['terminal_both'] = False
        write_json(evidence / 'run-result.json', record)
        if cleanup_failure is not None and 'primary_failure' not in record:
            raise cleanup_failure


if __name__ == '__main__':
    main()
