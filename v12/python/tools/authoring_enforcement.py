"""Independent enforcement lane for the one-invocation authoring supervisor.

The lane owns its own connections and cancellation adapter. It never dispatches
work. A scheduler blocked in filesystem/provider/engine work cannot block this
lane. Engine availability is an assumption for physical cessation, never a fact
inferred from the timer. Restart is cancellation-only, not a fresh budget.
"""
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import json
import hashlib
import os
import signal
import subprocess
from pathlib import Path
import threading
import time

from baton_v12.worker_manager.store import manager_signature
from baton_v12.worker_manager import ControlStore, attempts, intake, tokens
from baton_v12.job_manager import JobStore
from baton_v12.job_manager.submission import stages_of
from baton_v12.job_manager.episodes import episodes_of
from tools import job_manager, single_worker, stage_execution

POLL_SECONDS = 0.25
ENGINE_SECONDS = 2
KIND = 'authoring.envelope'
HALT_KIND = 'authoring.halt'


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def envelope(control, packet):
    operands = {'run': packet['run_id'], 'job': packet['submission']['job_id'],
                'authority': packet['deployment']['authority_uuid'],
                'packet': packet}
    identity = KIND + ':' + packet['run_id']
    prior = control.operation_record(identity)
    def commit(connection):
        del connection
        now = control._now()
        stop = instant(now) + timedelta(seconds=packet['bounds']['total_seconds'] - packet['bounds']['cleanup_seconds'])
        return dict(operands, started_at=now, stop_at=stop.isoformat())
    held = control.transact(identity, KIND, manager_signature(KIND, operands), commit)
    return held, prior is not None


def halt(control, run):
    operands = {'run': run}
    return control.transact(HALT_KIND + ':' + run, HALT_KIND,
                            manager_signature(HALT_KIND, operands), lambda connection: operands)


def selected_attempts(job, job_id):
    return sorted({episode['attempt_id'] for stage in stages_of(job, job_id)
                   for episode in episodes_of(job, stage['stage_id']) if episode['attempt_id'] is not None})


def bounded_engine(argv, *, seconds=None):
    if seconds is not None and seconds <= 0:
        from baton_v12.contracts import ContractRefusal
        raise ContractRefusal('refused', 'precondition', 'engine allowance exhausted; no subprocess started')
    return single_worker._engine_run(argv, seconds=min(ENGINE_SECONDS, seconds) if seconds is not None else ENGINE_SECONDS)


class Lane:
    """One decision/cessation pass, also usable with deterministic owner seams."""
    def __init__(self, control, job, operations, packet, *, engine_run=bounded_engine,
                 clock=utc, monotonic=time.monotonic, stopping=None, recovery=False):
        self.control, self.job, self.operations, self.packet = control, job, operations, packet
        self.clock, self.monotonic = clock, monotonic
        self.stopping = stopping or threading.Event()
        self.held, previous = envelope(control, packet)
        self.deadline = monotonic() + max(0, (instant(self.held['stop_at']) - instant(clock())).total_seconds())
        self.previous_clock = instant(clock())
        self.governance = tokens.workspace_governance()
        engines = {worker['deployment']['engine'] for worker in operations.configuration['workers']}
        if len(engines) != 1:
            raise RuntimeError('authoring enforcement requires one configured engine; cannot guess an attempt runtime owner')
        engine = engines.pop()
        self.adapter = job_manager._Reclaiming(job_manager._ReclaimAdapter(engine, engine_run))
        self.report = {'state': 'watching', 'attempts': {}, 'faults': []}
        self.recovery = recovery or previous
        self.cancelled = set()
        if recovery or previous or control.operation_record(HALT_KIND + ':' + packet['run_id']) is not None:
            self.stopping.set()

    def tick(self):
        now = instant(self.clock())
        if now < self.previous_clock or now >= instant(self.held['stop_at']) or self.monotonic() >= self.deadline:
            self.stopping.set()
        self.previous_clock = now
        ids = selected_attempts(self.job, self.packet['submission']['job_id'])
        # Public token decisions own expiry. Candidate enumeration performs only
        # local owner-store reads, before any adapter call or other-store access.
        rows = {row['runtime_attempt_id']: row for row in job_manager._governed_rows(self.control, self.governance) if row['runtime_attempt_id'] in ids}
        overdue = {identity for identity, row in rows.items() if self.governance.overdue(self.control, row, operation=attempts._start_operation_id(row)) is not None}
        if overdue:
            self.stopping.set()
        if self.stopping.is_set():
            halt(self.control, self.packet['run_id'])
        for attempt in ids:
            evidence = {'runtime': None, 'observation': None, 'token': None, 'faults': []}
            try:
                generation = None
                runtime = attempts.attempt_runtime_of(self.control, attempt)
                evidence['runtime'] = runtime
                row = rows.get(attempt)
                if row is not None:
                    domain = tokens.domain_of('workspace', self.governance.identity(row))
                    generation = tokens.generation_of(self.control, domain, execution=attempt, operation=attempts._start_operation_id(row))
                    if generation is not None:
                        evidence['token'] = tokens.token_of(self.control, domain, generation)
                token = evidence['token']
                if token is not None and token['container'] is not None and runtime['runtime_id'] not in (None, token['container']):
                    raise RuntimeError('token and attempt disagree on exact runtime; no cancellation or settlement issued')
                if attempt in overdue:
                    answer = intake.reclaim_expired_resource(self.control, self.adapter, attempt_id=attempt, govern=self.governance)
                    evidence['reclaim'] = answer
                    if answer.get('reclaimed') in ('held', 'returned'):
                        evidence['settlement'] = intake.settle_revoked_resource(self.control, self.adapter, attempt_id=attempt, govern=self.governance)
                elif self.stopping.is_set() and runtime is not None:
                    exact = runtime['runtime_id'] or (token or {}).get('container')
                    observed = self.adapter.observe(exact) if exact is not None else None
                    evidence['observation'] = observed
                    if attempt not in self.cancelled or (observed is not None and observed['state'] not in ('absent', 'quiescent')):
                        # Fence even before any identity is known. Revisit a late
                        # bound/running effect under the same cancellation identity;
                        # an acknowledgement cannot suppress a subsequent stop.
                        self.operations.cancel_attempt(attempt_id=attempt, reason='authoring-enforcement')
                        self.cancelled.add(attempt)
                exact = runtime['runtime_id'] if runtime is not None else None
                exact = exact or (token or {}).get('container')
                if self.stopping.is_set() and exact is not None:
                    evidence['observation'] = self.adapter.observe(exact)
            except Exception as fault:
                evidence['faults'].append(type(fault).__name__ + ': ' + str(fault))
            if generation is not None:
                evidence['token'] = tokens.token_of(self.control, domain, generation)
            self.report['attempts'][attempt] = evidence
            if self.stopping.is_set():
                # Journal observations outside every engine call. This preserves
                # uncertainty even if the authoring process never returns.
                signature = manager_signature('authoring.observation', evidence)
                self.control.transact('authoring.observation:' + signature, 'authoring.observation', signature, lambda connection: evidence)
        self.report['state'] = 'stopping' if self.stopping.is_set() else 'watching'
        return self.report


class Guard:
    """Own a separate enforcement thread; no connection crosses threads."""
    def __init__(self, packet, *, factory=None, clock=utc, lock_fd=None):
        self.packet, self.factory, self.clock = packet, factory, clock
        self.lock_fd = None if lock_fd is None else os.dup(lock_fd)
        self.recovery = False
        self.envelope = None
        self.stopping = threading.Event()
        self.ready, self.finished, self.shutdown = threading.Event(), threading.Event(), threading.Event()
        self.report = {'state': 'starting', 'attempts': {}, 'faults': []}
        self.thread = threading.Thread(target=self._run, name='authoring-enforcement', daemon=True)

    def _run(self):
        try:
            with ExitStack() as stack:
                dep = self.packet['deployment']
                control = stack.enter_context(ControlStore.open(dep['control_store'], incarnation=self.packet['run_id'] + '-enforcement', clock=self.clock))
                job = stack.enter_context(JobStore.open(dep['job_store'], authority_uuid=dep['authority_uuid'], incarnation=self.packet['run_id'] + '-enforcement', clock=self.clock))
                with open(dep['config_path'], encoding='utf-8') as handle:
                    config = json.load(handle)
                operations = (self.factory or stage_execution.operations_from)(config, job, control, engine_run=bounded_engine, checkout=self.packet['code_boundary'])
                stack.callback(operations.close)
                lane = Lane(control, job, operations, self.packet, clock=self.clock, stopping=self.stopping)
                self.envelope = lane.held
                self.recovery = lane.recovery
                self.report = lane.tick()
                self.ready.set()
                while not self.shutdown.wait(POLL_SECONDS):
                    self.report = lane.tick()
                self.report = lane.tick()
        except Exception as fault:
            self.stopping.set()
            self.report = {'state': 'held', 'attempts': dict(self.report.get('attempts', {})), 'faults': [type(fault).__name__ + ': ' + str(fault)]}
        finally:
            if self.lock_fd is not None:
                os.close(self.lock_fd)
            self.ready.set()
            self.finished.set()

    def start(self):
        self.thread.start()
        if not self.ready.wait(30) or self.finished.is_set():
            self.stopping.set()
            self.shutdown.set()
            raise RuntimeError('authoring enforcement unavailable: ' + str(self.report))
        return self

    def stop(self, *, timeout=ENGINE_SECONDS * 4 + 2):
        self.shutdown.set()
        self.thread.join(timeout=max(0, timeout))
        if self.thread.is_alive():
            return {'state': 'held', 'attempts': dict(self.report.get('attempts', {})), 'faults': ['enforcement did not finish; ownership remains unresolved']}
        return self.report



class Operations:
    """Gate dispatch at the durable halt, using the author's own connection."""
    def __init__(self, operations, control, run):
        self.operations, self.control, self.run = operations, control, run

    def __getattr__(self, name):
        return getattr(self.operations, name)

    def _dispatch(self, name, *args, **kwargs):
        from baton_v12.contracts import ContractRefusal
        if self.control.operation_record(HALT_KIND + ':' + self.run) is not None:
            raise ContractRefusal('refused', 'precondition', 'authoring enforcement closed admission')
        return getattr(self.operations, name)(*args, **kwargs)

    def admit(self, *args, **kwargs):
        return self._dispatch('admit', *args, **kwargs)

    def claim(self, *args, **kwargs):
        return self._dispatch('claim', *args, **kwargs)

    def launch(self, *args, **kwargs):
        return self._dispatch('launch', *args, **kwargs)

    def cancel_attempt(self, *, attempt_id, reason):
        # Both controllers retry the same canonical cancellation intent.
        return self.operations.cancel_attempt(attempt_id=attempt_id, reason='authoring-enforcement')


def child_compose(packet, job, control, stream):
    del stream
    with open(packet['deployment']['config_path'], encoding='utf-8') as handle:
        config = json.load(handle)
    operations = stage_execution.operations_from(config, job, control, engine_run=bounded_engine, checkout=packet['code_boundary'])
    return Operations(operations, control, packet['run_id'])


def supervise_process(packet, guard, launch, *, clock=time.monotonic, sleep=time.sleep):
    """The outer deadline never calls the authoring sweep or cancellation engine.

    `launch` supplies one owned process with poll/terminate/kill/wait. Process
    exit is not runtime cessation. Recovery gets cleanup time, no new authoring.
    """
    started = clock()
    child = None
    report = {'state': 'held', 'child_started': False, 'child_exited': False, 'faults': []}
    reserve = packet['bounds']['cleanup_seconds']
    total = max(0, (instant(guard.envelope['stop_at']) - instant(guard.clock())).total_seconds()) + reserve
    deadline = started + total
    try:
        if not guard.recovery and not guard.stopping.is_set():
            child = launch()
            report['child_started'] = True
        else:
            guard.stopping.set()
            deadline = started + reserve
        terminating = False
        tail = min(12, reserve / 2)
        while clock() < deadline - tail:
            if child is not None and child.poll() is not None:
                report['child_exited'] = True
                report['child_status'] = child.poll()
                guard.stopping.set()
                observed = guard.report.get('attempts', {}).values()
                if guard.finished.is_set() or all((row.get('observation') or {}).get('state') in ('absent', 'quiescent') and not (row.get('token') or {}).get('activating') for row in observed):
                    break
            if guard.finished.is_set() or clock() >= deadline - reserve:
                guard.stopping.set()
            if guard.stopping.is_set() and child is not None and not terminating:
                if not report['child_exited']:
                    child.terminate()
                deadline = min(deadline, clock() + reserve)
                terminating = True
            sleep(min(POLL_SECONDS, max(0, deadline - tail - clock())))
    except BaseException as fault:
        report['faults'].append(type(fault).__name__ + ': ' + str(fault))
    finally:
        guard.stopping.set()
        if child is not None:
            try:
                child.kill()
                report['child_status'] = child.wait(timeout=min(2, max(0, deadline - clock())))
                report['child_exited'] = True
            except Exception as fault:
                report['faults'].append('authoring process cessation unknown: ' + str(fault))
        report['enforcement'] = guard.stop(timeout=max(0, deadline - clock()))
        report['elapsed_seconds'] = clock() - started
    # Success requires the workload supervisor's own success. The enforcement
    # record cannot turn a held/absent author outcome into an accepted result.
    if report.get('child_status') == 0 and not report['faults'] and not report['enforcement']['faults']:
        observed = report['enforcement']['attempts'].values()
        if all((row.get('observation') or {}).get('state') == 'absent' and not row.get('faults') and (row.get('token') is None or row['token']['returned']) for row in observed):
            report['state'] = 'completed'
    return report


class Process:
    def __init__(self, command, *, output, lock_fd):
        self.child = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                      start_new_session=True, pass_fds=(lock_fd,))

    def poll(self):
        # Do not reap the session leader before its last group signal: the
        # unreaped PID cannot be recycled into an unrelated process group.
        info = os.waitid(os.P_PID, self.child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if info is None:
            return None
        return info.si_status if info.si_code == os.CLD_EXITED else -info.si_status

    def _signal(self, number):
        try:
            os.killpg(self.child.pid, number)
        except ProcessLookupError:
            pass

    def terminate(self):
        self._signal(signal.SIGTERM)

    def kill(self):
        self._signal(signal.SIGKILL)

    def wait(self, timeout):
        return self.child.wait(timeout=timeout)


def verify_controller(packet):
    source = packet['manager_source']
    here = Path(__file__).resolve()
    try:
        relative = str(here.relative_to(Path(source['path']).resolve()))
    except ValueError as error:
        raise RuntimeError('authoring controller is outside the pinned manager source') from error
    expected = source['files'].get(relative)
    if expected is None or hashlib.sha256(here.read_bytes()).hexdigest() != expected:
        raise RuntimeError('authoring controller bytes are not pinned by this packet')


def admit_child(control, packet, parent, pid):
    from baton_v12.contracts import ContractRefusal
    # Reusing a packet is recovery, including a crash after this intent but
    # before the first submission. No automatic replacement child is allowed.
    envelope(control, packet)
    identity = 'authoring.child:' + packet['run_id']
    if control.operation_record(identity) is not None:
        raise ContractRefusal('refused', 'precondition', 'this authoring invocation was already consumed; recovery never launches another')
    if control.operation_record(HALT_KIND + ':' + packet['run_id']) is not None:
        raise ContractRefusal('refused', 'precondition', 'authoring admission is closed')
    operands = {'parent': parent, 'pid': pid, 'run': packet['run_id']}
    return control.transact(identity, 'authoring.child', manager_signature('authoring.child', operands), lambda connection: operands)


def child_main(packet_path, parent, lock_fd):
    # Linux is the selected OCI host. The inherited flock also prevents a new
    # controller while this child remains alive following parent loss.
    import ctypes
    import baseline
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        raise RuntimeError('cannot bind authoring lifetime to its controller')
    packet = baseline.held_packet(packet_path)
    verify_controller(packet)
    if lock_fd is None or os.fstat(lock_fd).st_ino != os.stat(packet['deployment']['control_store'] + '.authoring.lock').st_ino:
        raise RuntimeError('authoring child lacks its inherited controller lock')
    with ControlStore.open(packet['deployment']['control_store'], incarnation='authoring-child-admission', clock=utc) as control:
        if control.operation_record(KIND + ':' + packet['run_id']) is None:
            raise RuntimeError('no committed authoring controller envelope')
        admit_child(control, packet, parent, os.getpid())
    return baseline.main(['--packet', packet_path, '--incarnation', 'authoring-child-' + str(os.getpid())], compose=child_compose)


def main(argv=None):
    import argparse
    import fcntl
    import sys
    import baseline
    parser = argparse.ArgumentParser(description='One isolated authoring invocation with independent deadline and expiry enforcement')
    parser.add_argument('--packet', required=True)
    parser.add_argument('--child-of', type=int)
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args(argv)
    if args.child_of is not None:
        return child_main(args.packet, args.child_of, args.lock_fd)
    packet = baseline.held_packet(args.packet)
    baseline.verify_imported_sources(packet)
    verify_controller(packet)
    with open(packet['deployment']['control_store'] + '.authoring.lock', 'a') as lock:
        # Never unlink the lock inode; the child inherits the same open lock.
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        existing = None
        if os.path.exists(packet['deployment']['control_store']):
            with ControlStore.open_readonly(packet['deployment']['control_store'], incarnation='authoring-recovery-check', clock=utc) as control:
                existing = control.operation_record(KIND + ':' + packet['run_id'])
        if existing is None:
            baseline.verify_worker_image(packet, image_inspect=baseline._engine_inspect)
        with ControlStore.open(packet['deployment']['control_store'], incarnation='authoring-prepare', clock=utc) as control:
            baseline.prepare(control, packet)
        guard = Guard(packet, lock_fd=lock.fileno()).start()
        output_path = packet['outcome_path'] + '.authoring.log'
        received = []
        def stop(number, frame):
            del frame
            received.append(number)
            guard.stopping.set()
        previous = {number: signal.signal(number, stop) for number in (signal.SIGTERM, signal.SIGINT)}
        try:
            with open(output_path, 'ab', buffering=0) as output:
                report = supervise_process(packet, guard, lambda: Process(
                    [sys.executable, '-m', 'tools.authoring_enforcement', '--packet', args.packet, '--child-of', str(os.getpid()), '--lock-fd', str(lock.fileno())], output=output, lock_fd=lock.fileno()))
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
        report['operator_signals'] = received
        if received:
            report['state'] = 'held'
        report['authoring_log'] = output_path
        report['original_envelope'] = guard.envelope
        report['recovery_only'] = guard.recovery
        result = Path(packet['outcome_path'] + f'.enforcement-{os.getpid()}-{time.time_ns()}.json')
        report['enforcement_path'] = str(result)
        temporary = result.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        os.replace(temporary, result)
        print(json.dumps(report, sort_keys=True))
        return 0 if report['state'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
