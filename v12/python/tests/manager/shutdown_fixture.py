"""Candidate-native real baseline/controller process fixtures; fake external engine.

Adapted from accepted W337955 diagnosis; no Git export or frozen-base execution.
"""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from unittest.mock import patch

CONTROLLER = 'v12/python/tools/authoring_enforcement.py'


def event(root, name, **data):
    row = dict(event=name, monotonic=time.monotonic(), pid=os.getpid(), thread=threading.get_ident(), **data)
    fd = os.open(root / 'events.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, (json.dumps(row, sort_keys=True) + '\n').encode())
    finally:
        os.close(fd)


# W384870 C7 review 2026-10-30T17:17:47Z: WHAT EACH MODE MUST PROVABLY REACH.
# The matrix passed vacuously for eight days because every start was refused
# before the engine and no mode asserted its own scenario. Each mode names the
# journal facts that distinguish its intended scenario -- the scripted create
# refusal, an actual fake runtime start, or the pre-invocation signal -- plus
# the selected injection, and `unreached` lists every fact a journal lacks.
SCRIPTED_CREATE_REFUSAL = 'selected fake provider setup refusal'
RUNTIME_MODES = ('blocked_sweep', 'absent_cleanup', 'stuck_cleanup', 'stuck_accounting', 'unknown')
CREATE_REFUSAL_MODES = ('normal', 'delayed_snapshot', 'snapshot_before', 'stuck_snapshot', 'stuck_workload')
INJECTIONS = {'blocked_sweep': 'blocked_serving_sweep', 'unknown': 'blocked_serving_sweep',
              'absent_cleanup': 'deferred_signal_returned', 'stuck_cleanup': 'stalled_cleanup_sweep',
              'stuck_accounting': 'stalled_workload_accounting', 'delayed_snapshot': 'snapshot_delay',
              'snapshot_before': 'snapshot_delay', 'stuck_snapshot': 'snapshot_delay',
              'stuck_workload': 'workload_publication_stalled', 'pre_signal': 'injected_pre_supervision_signal'}


def unreached(mode, events):
    """Every intended-scenario fact this mode's journal fails to establish."""
    names = [row['event'] for row in events]
    engine = [row['argv'][1] for row in events if row['event'] == 'fake_engine']
    refusals = [row['refusal'] for row in events if row['event'] == 'start_refused']
    missing = []
    if mode in INJECTIONS and INJECTIONS[mode] not in names:
        missing.append('selected injection ' + INJECTIONS[mode] + ' never happened')
    if 'token_acquire_refused' in names:
        missing.append('token acquisition was refused: ' + next(row['refusal'] for row in events if row['event'] == 'token_acquire_refused'))
    if mode == 'pre_signal':
        for fact, held in (('no token acquisition', 'token_acquire' not in names), ('no engine create', 'create' not in engine), ('no start refusal', not refusals)):
            if not held:
                missing.append('pre-invocation signal mode expected ' + fact)
        return missing
    if not any(row['event'] == 'token_acquire' and row['permission'] for row in events):
        missing.append('no token acquired under the controller envelope')
    if 'create' not in engine:
        missing.append('the fake engine never created the runtime')
    if mode in RUNTIME_MODES:
        if 'start' not in engine:
            missing.append('the fake runtime never started')
        if refusals:
            missing.append('the start was refused: ' + refusals[0])
    elif mode in CREATE_REFUSAL_MODES:
        if 'start' in engine:
            missing.append('the fake runtime started although create was scripted to refuse')
        if not any(SCRIPTED_CREATE_REFUSAL in refusal for refusal in refusals):
            missing.append('the scripted create refusal never reached the start' + ('' if not refusals else ': ' + refusals[0]))
        if any(SCRIPTED_CREATE_REFUSAL not in refusal for refusal in refusals):
            missing.append('an unscripted refusal: ' + next(refusal for refusal in refusals if SCRIPTED_CREATE_REFUSAL not in refusal))
    else:
        missing.append('mode ' + mode + ' declares no intended scenario')
    return missing


def imports(source):
    sys.path[:0] = [str(source / 'v12/python/src'), str(source / 'v12/python')]


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
    # W384870 C7: the controller composes a permission ENVELOPE for every start
    # (`authoring_enforcement.permission_policy`, 30245386) and refuses a start
    # whose provider turn plus ordinary verification exceed the envelope's
    # execution window, `total_seconds - cleanup_seconds`. The Job's limits
    # must fit the window the diagnostic bounds leave AT ACQUISITION TIME (the
    # start reaches the token about 1.3 s in), or every mode is refused before
    # the engine and the matrix measures nothing. `turn_seconds` must equal the
    # Job's provider turn (`authoring_baseline` refuses a packet that differs).
    case.submission['jobs'][0]['execution_limits'] = {'provider_turn_seconds': 2, 'verification_command_seconds': 1}
    (root / 'submission.json').write_text(json.dumps(case.submission))
    value = {'schema': 'baton.single-implementation-packet/2', 'context': {'mode': 'fresh'}, 'run_id': 'shutdown-' + mode,
             'work': 'W338305', 'claim': 338472, 'submission': {'job_id': 'job-a', 'path': str(root / 'submission.json')},
             'deployment': {'authority_uuid': config['authority_uuid'], 'control_store': case.control_path, 'job_store': case.job_path, 'config_path': str(root / 'config.json')},
             'code_boundary': case.checkout, 'outcome_path': str(root / 'outcome.json'),
             'bounds': {'total_seconds': 20 if mode == 'normal' else 10, 'cleanup_seconds': 4, 'turn_seconds': 2, 'implementer_invocations': 1, 'retry': False},
             # W384870 B3: `verify_controller` pins BOTH controller programs (the
             # enforcement controller and its shutdown helper), as its own test says.
             'manager_source': {'path': str(source / 'v12/python'), 'files': {
                 'tools/authoring_enforcement.py': hashlib.sha256((source / CONTROLLER).read_bytes()).hexdigest(),
                 'tools/authoring_shutdown.py': hashlib.sha256((source / 'v12/python/tools/authoring_shutdown.py').read_bytes()).hexdigest()}},
             'diagnostic_mode': mode}
    (root / 'packet.json').write_text(json.dumps(value))
    case.doCleanups()


def fixture(source, argv):
    imports(source)
    # W384870 B3: patch the baseline module THE CONTROLLER IMPORTS. This used
    # to import the historical proof's `baseline.py` from its dossier, so every
    # patch below landed on a module `tools/authoring_enforcement.py` never
    # reads, and the real `held_packet` refused the fixture packet.
    from tools import authoring_baseline as baseline
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
    traced = {'start', 'child_main', 'supervise', '_supervise', '_handle', 'install', 'restore', 'defer', '_run', 'stop', 'publish_guard', '_publish', 'main'}
    phase = {'cleanup': False, 'injected': False}
    def trace(frame, kind, value):
        filename, name = frame.f_code.co_filename, frame.f_code.co_name
        if filename not in (baseline.__file__, e.__file__):
            return None
        if name in traced and kind in ('call', 'return'):
            event(root, 'trace', function=name, kind=kind)
            if name == 'defer' and kind == 'return':
                phase['cleanup'] = True
                if mode == 'absent_cleanup':
                    os.kill(os.getpid(), signal.SIGTERM)
                    event(root, 'deferred_signal_returned', received=list(frame.f_locals['self'].received))
            if name == 'start' and kind == 'return' and mode == 'pre_signal' and not phase['injected']:
                phase['injected'] = True
                event(root, 'injected_pre_supervision_signal')
                os.kill(os.getpid(), signal.SIGTERM)
        return trace if name in traced else None
    sys.settrace(trace)
    threading.settrace(trace)

    class FakeEngine(Engine):
        def __call__(self, argv, *, seconds=None):
            event(root, 'fake_engine', argv=list(argv))
            if mode in ('normal', 'delayed_snapshot', 'snapshot_before', 'stuck_snapshot', 'stuck_workload') and argv[1] == 'create':
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
        if mode == 'stuck_cleanup' and phase['cleanup']:
            event(root, 'stalled_cleanup_sweep')
            time.sleep(60)
        answer = real_sweep(*args, **kwargs)
        if mode in ('blocked_sweep', 'unknown') and engine.running and not phase['cleanup']:
            event(root, 'blocked_serving_sweep')
            time.sleep(20)
        return answer
    real_acquire = tokens.acquire
    def acquire(*args, **kwargs):
        # W384870 C7: no injected duration. The controller's envelope IS the
        # token lifetime now, and `acquire` refuses a duration beside one.
        event(root, 'token_acquire', operands=sorted(kwargs), permission=kwargs.get('permission') is not None)
        try:
            return real_acquire(*args, **kwargs)
        except Exception as refusal:
            event(root, 'token_acquire_refused', refusal=type(refusal).__name__ + ': ' + str(refusal))
            raise
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
        if guard.finished.is_set() and mode in ('delayed_snapshot', 'snapshot_before', 'stuck_snapshot'):
            delay = 60 if mode == 'stuck_snapshot' else (6 if mode == 'delayed_snapshot' else .01)
            event(root, 'snapshot_delay', seconds=delay)
            time.sleep(delay)
        real_publish(path, guard)
        event(root, 'snapshot_replaced', finished=guard.finished.is_set())

    real_evidence = baseline._workload_evidence
    def evidence(*args, **kwargs):
        if mode == 'stuck_accounting':
            event(root, 'stalled_workload_accounting')
            time.sleep(60)
        return real_evidence(*args, **kwargs)

    real_workload_publish = baseline._publish
    def workload_publish(path, document):
        if mode == 'stuck_workload':
            event(root, 'workload_publication_stalled')
            time.sleep(60)
        return real_workload_publish(path, document)

    real_prepared = single_worker._SingleWorker._prepared
    def prepared(self, *args, **kwargs):
        try:
            return real_prepared(self, *args, **kwargs)
        except Exception as refusal:
            event(root, 'start_refused', refusal=type(refusal).__name__ + ': ' + str(refusal))
            raise
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
        stack.enter_context(patch.object(baseline, '_publish', workload_publish))
        stack.enter_context(patch.object(baseline, '_workload_evidence', evidence))
        stack.enter_context(patch.object(e, 'Process', Process))
        stack.enter_context(patch.object(e, 'publish_guard', publish))
        stack.enter_context(patch.object(e, 'prepare_manager', prepare_manager))
        stack.enter_context(patch.object(single_worker._SingleWorker, '_prepared', prepared))
        stack.enter_context(patch.object(stage_execution, 'operations_from', operations))
        stack.enter_context(patch.object(subprocess, 'Popen', popen))
        stack.enter_context(patch.object(tokens, 'acquire', acquire))
        stack.enter_context(patch.object(manager, 'sweep', sweep))
        stack.enter_context(patch.object(api, 'sweep', sweep))
        return e.main(argv)



if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fixture':
        raise SystemExit(fixture(Path(sys.argv[2]), sys.argv[3:]))
    raise SystemExit('fixture entry requires --fixture candidate-root --packet path')
