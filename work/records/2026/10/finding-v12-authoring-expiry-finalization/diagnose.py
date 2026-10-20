"""W337955 deterministic process diagnostic; never invokes an engine/provider.

Run: python3 diagnose.py --repository /path/to/baton --output /fresh/tmp/path
The only Git operation is a read-only archive of the owner-selected commit.
"""
import argparse
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from unittest.mock import patch

BASE = 'fb48797903160aa764229d58f3a5beaf29648bfc'
BASELINE = 'work/records/2026/09/finding-v12-single-implementation-proof/baseline.py'
CONTROLLER = 'v12/python/tools/authoring_enforcement.py'
PINS = {BASELINE: 'c1b0a10e609503df0ba7ebdc7455cc8518c9175882edd185b65f20c342c4bd2f', CONTROLLER: 'bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f'}
VECTORS = 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'


def event(root, name, **data):
    row = dict(event=name, monotonic=time.monotonic(), pid=os.getpid(), thread=threading.get_ident(), **data)
    fd = os.open(root / 'events.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, (json.dumps(row, sort_keys=True) + '\n').encode())
    finally:
        os.close(fd)


def imports(source):
    sys.path[:0] = [str(source / 'v12/python/src'), str(source / 'v12/python'), str((source / BASELINE).parent)]


def prepare(source, root, mode):
    imports(source)
    from tests.tools.test_stage_execution import ServingCase
    from tests.manager import disk_roots
    case = ServingCase()
    # Keep all test-owned paths in the named disposable case, not the source.
    with patch.object(disk_roots, 'disk_backed_under', lambda case: str(root)):
        case.setUp()
    config = case.composed_document()
    for worker in config['workers']:
        worker['deployment']['credential_sources'] = str(root / 'unused-registry')
    (root / 'config.json').write_text(json.dumps(config))
    case.submission['schema'] = 'baton.v12.job-submission/2'
    case.submission['jobs'][0]['execution_limits'] = {'provider_turn_seconds': 20}
    (root / 'submission.json').write_text(json.dumps(case.submission))
    value = {'schema': 'baton.single-implementation-packet/2', 'context': {'mode': 'fresh'}, 'run_id': 'diagnostic-' + mode,
             'work': 'W337955', 'claim': 338073, 'submission': {'job_id': 'job-a', 'path': str(root / 'submission.json')},
             'deployment': {'authority_uuid': config['authority_uuid'], 'control_store': case.control_path, 'job_store': case.job_path, 'config_path': str(root / 'config.json')},
             'code_boundary': case.checkout, 'outcome_path': str(root / 'outcome.json'),
             'bounds': {'total_seconds': 20 if mode == 'normal' else 8, 'cleanup_seconds': 4, 'turn_seconds': 20, 'implementer_invocations': 1, 'retry': False},
             'manager_source': {'path': str(source / 'v12/python'), 'files': {'tools/authoring_enforcement.py': PINS[CONTROLLER]}},
             'diagnostic_mode': mode}
    (root / 'packet.json').write_text(json.dumps(value))
    case.doCleanups()


def fixture(source, argv):
    imports(source)
    import baseline
    from tools import authoring_enforcement as e, single_worker, stage_execution
    from tests.tools.test_single_worker import Engine
    from baton_v12.worker_manager import tokens, workspaces
    import baton_v12.job_manager as api
    from baton_v12.job_manager import manager
    root = Path(argv[argv.index('--packet') + 1]).parent
    packet = json.loads((root / 'packet.json').read_text())
    mode = packet['diagnostic_mode']
    event(root, 'process_entry', child='--child-of' in argv)

    # Instrument original functions without replacing their control flow.
    traced = {'child_main', 'supervise', '_supervise', '_handle', 'install', 'restore', 'defer', '_run', 'stop', 'publish_guard', '_publish', 'main'}
    points = {1207: 'serve_call', 1226: 'admission_closed', 1230: 'defer_call', 1293: 'cleanup_deadline', 1297: 'cleanup_sweep', 1337: 'cleanup_return', 1447: 'workload_publish'}
    phase = {'cleanup': False, 'injected': False}
    def trace(frame, kind, value):
        filename, name = frame.f_code.co_filename, frame.f_code.co_name
        if filename not in (baseline.__file__, e.__file__):
            return None
        if name in traced and kind in ('call', 'return', 'exception'):
            data = {'function': name, 'kind': kind, 'line': frame.f_lineno}
            if kind == 'exception':
                data['exception'] = value[0].__name__
            if name == '_handle':
                data['mode'] = getattr(frame.f_locals.get('self'), '_mode', None)
                data['signal'] = frame.f_locals.get('number')
            event(root, 'trace', **data)
            if name == 'defer' and kind == 'return':
                phase['cleanup'] = True
                if mode == 'absent_cleanup':
                    event(root, 'injected_deferred_signal')
                    os.kill(os.getpid(), signal.SIGTERM)
                    event(root, 'deferred_signal_returned', received=list(frame.f_locals['self'].received))
        if filename == baseline.__file__ and name == '_supervise' and kind == 'line' and frame.f_lineno in points:
            event(root, points[frame.f_lineno], cleanup_deadline=frame.f_locals.get('cleanup_deadline'), cleanup_started=frame.f_locals.get('cleanup_started'))
        if filename == e.__file__ and name == 'child_main' and kind == 'line' and frame.f_lineno == 448 and mode == 'pre_signal' and not phase['injected']:
            phase['injected'] = True
            event(root, 'injected_pre_supervision_signal', handler=repr(signal.getsignal(signal.SIGTERM)))
            os.kill(os.getpid(), signal.SIGTERM)
        return trace if name in traced else None
    sys.settrace(trace)
    threading.settrace(trace)

    class FakeEngine(Engine):
        def __call__(self, argv, *, seconds=None):
            event(root, 'fake_engine', argv=list(argv))
            if mode in ('normal', 'delayed_snapshot', 'snapshot_before') and argv[1] == 'create':
                return self.answer(status=1, stderr='selected fake provider setup refusal; normal baseline return control')
            if mode == 'unknown' and self.runtime_id is not None and argv[1] in ('stop', 'rm', 'inspect'):
                raise TimeoutError('selected fake engine uncertainty')
            if argv[1] in ('stop', 'rm'):
                self.running = False
                if argv[1] == 'rm':
                    self.runtime_id = None
                return self.answer()
            if argv[1] == 'inspect' and self.runtime_id is None:
                return self.answer(status=1, stderr='Error: No such container: ' + argv[-1])
            return super().__call__(argv, seconds=seconds)
    engine = FakeEngine()
    real_sweep = manager.sweep
    def sweep(*args, **kwargs):
        answer = real_sweep(*args, **kwargs)
        if mode == 'blocked_sweep' and engine.running and not phase['cleanup']:
            event(root, 'blocked_serving_sweep')
            time.sleep(20)
        return answer
    real_acquire = tokens.acquire
    def acquire(*args, **kwargs):
        kwargs.setdefault('seconds', 900 if mode in ('normal', 'delayed_snapshot', 'snapshot_before') else 2)
        return real_acquire(*args, **kwargs)
    class SourceFixture:
        name = 'git'
        def materialize(self, source, repository, declared_base):
            Path(repository).mkdir(exist_ok=True)
            event(root, 'fixture_materialize', repository=repository)
            return {'profile': self.name, 'base': declared_base, 'head': declared_base}
        def freeze(self, *args, **kwargs):
            raise AssertionError('no synthetic checkpoint acceptance')
        def validate(self, *args, **kwargs):
            raise AssertionError('no synthetic checkpoint acceptance')
    real_operations = stage_execution.operations_from
    def operations(*args, **kwargs):
        kwargs['checkpoint_profile'] = SourceFixture()
        return real_operations(*args, **kwargs)
    real_popen = subprocess.Popen
    def popen(argv, *args, **kwargs):
        if Path(argv[0]).name not in ('python', 'python3', Path(sys.executable).name):
            raise AssertionError('fixture prohibits external executable: ' + str(argv[0]))
        return real_popen(argv, *args, **kwargs)
    real_process = e.Process
    class Process(real_process):
        def __init__(self, command, **kwargs):
            command = [sys.executable, '-B', str(Path(__file__).resolve()), '--fixture', str(source), *command[command.index('--packet'):]]
            super().__init__(command, **kwargs)
            event(root, 'manager_started', manager=self.child.pid)
        def _signal(self, number):
            event(root, 'outer_signal', signal=number, manager=self.child.pid)
            return super()._signal(number)
        def wait(self, timeout):
            answer = super().wait(timeout)
            event(root, 'manager_reaped', status=answer, manager=self.child.pid)
            return answer

    real_publish = e.publish_guard
    def publish(path, guard):
        event(root, 'snapshot_begin', stopping=guard.stopping.is_set(), finished=guard.finished.is_set(), report=guard.report)
        if guard.finished.is_set() and mode in ('delayed_snapshot', 'snapshot_before'):
            delay = 6 if mode == 'delayed_snapshot' else .01
            event(root, 'snapshot_delay', seconds=delay)
            time.sleep(delay)
        real_publish(path, guard)
        event(root, 'snapshot_replaced', finished=guard.finished.is_set())

    real_prepare = e.prepare_manager
    def prepare_manager(control, packet):
        result = real_prepare(control, packet)
        held = workspaces.hold_manager_instance(control, baseline._workspace_root(packet))
        event(root, 'manager_guard_held', guard_pid=held.pid)
        assert held.pid == os.getpid()
        return result

    # Validation is outside this timing diagnostic. Archive hashes are checked
    # before any child; only the fixture packet and fake image check bypass it.
    with ExitStack() as stack:
        stack.enter_context(patch.object(baseline, 'held_packet', lambda path: json.loads(Path(path).read_text())))
        stack.enter_context(patch.object(baseline, 'verify_imported_sources', lambda packet: None))
        stack.enter_context(patch.object(baseline, 'verify_worker_image', lambda *args, **kwargs: None))
        stack.enter_context(patch.object(single_worker, '_engine_run', engine))
        stack.enter_context(patch.object(single_worker, 'UserCredentialSources', lambda *args, **kwargs: lambda *args: 'fake-no-credential-read'))
        stack.enter_context(patch.object(e, 'Process', Process))
        stack.enter_context(patch.object(e, 'publish_guard', publish))
        stack.enter_context(patch.object(e, 'prepare_manager', prepare_manager))
        stack.enter_context(patch.object(stage_execution, 'operations_from', operations))
        stack.enter_context(patch.object(subprocess, 'Popen', popen))
        stack.enter_context(patch.object(tokens, 'acquire', acquire))
        stack.enter_context(patch.object(manager, 'sweep', sweep))
        stack.enter_context(patch.object(api, 'sweep', sweep))
        return e.main(argv)


def run(repository, output, cases):
    output.mkdir(parents=True, exist_ok=False)
    source = Path(tempfile.mkdtemp(prefix='w337955-source-'))
    archive = subprocess.run(['git', '-C', str(repository), 'archive', BASE, 'v12/python', BASELINE, VECTORS], check=True, stdout=subprocess.PIPE).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            if not (member.isfile() or member.isdir()) or '..' in Path(member.name).parts or Path(member.name).is_absolute():
                raise RuntimeError('unexpected archive entry ' + member.name)
        tar.extractall(source, filter='data')
    for path, digest in PINS.items():
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
    for path in source.rglob('*'):
        if path.is_file():
            path.chmod(0o444)
    source_hashes = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest() for path in source.rglob('*') if path.is_file()}
    (output / 'source.json').write_text(json.dumps({'base': BASE, 'pins': PINS, 'path': str(source), 'files': source_hashes, 'archive_sha256': hashlib.sha256(archive).hexdigest()}, indent=2, sort_keys=True))
    results = []
    for mode in cases:
        root = output / mode
        root.mkdir()
        prepare(source, root, mode)
        started = time.monotonic()
        with (root / 'outer.log').open('w') as log:
            child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--fixture', str(source), '--packet', str(root / 'packet.json')], stdout=log, stderr=subprocess.STDOUT)
            try:
                code = child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
                raise RuntimeError('fixture timeout; inspect named manager PID before continuing')
        events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
        manager_pids = [row['manager'] for row in events if row['event'] == 'manager_started']
        reaped = [row['manager'] for row in events if row['event'] == 'manager_reaped']
        assert manager_pids and manager_pids == reaped, (manager_pids, reaped)
        absent = []
        for pid in manager_pids:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                absent.append(pid)
        assert absent == manager_pids, 'fixture manager still exists'
        from baton_v12.worker_manager import ControlStore, workspaces
        from tools.authoring_enforcement import utc
        value = json.loads((root / 'packet.json').read_text())
        with ControlStore.open(value['deployment']['control_store'], incarnation='post-fixture-guard-check', clock=utc) as control:
            held = workspaces.hold_manager_instance(control, str(root / 'storage'))
            held.release()
        result = dict(case=mode, outer_pid=child.pid, code=code, elapsed=time.monotonic() - started, managers_reaped=reaped, manager_pids_absent=absent, guard_reacquired=True)
        results.append(result)
        (output / 'summary.json').write_text(json.dumps(results, indent=2))
        print(json.dumps(result), flush=True)
    assert source_hashes == {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest() for path in source.rglob('*') if path.is_file()}, 'input source changed'
    (output / 'source-unchanged.json').write_text(json.dumps({'verified_files': len(source_hashes), 'unchanged': True}))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fixture':
        raise SystemExit(fixture(Path(sys.argv[2]), sys.argv[3:]))
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', choices=['normal', 'blocked_sweep', 'absent_cleanup', 'delayed_snapshot', 'unknown', 'pre_signal', 'snapshot_before'], default=['normal', 'blocked_sweep', 'absent_cleanup', 'delayed_snapshot', 'unknown', 'pre_signal', 'snapshot_before'])
    args = parser.parse_args()
    run(args.repository, args.output, args.cases)
