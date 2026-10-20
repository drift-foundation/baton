"""Independent enforcement lane for the one-invocation authoring supervisor.

The lane owns its own connections and cancellation adapter in the manager
process. It never dispatches work. Authoring and enforcement use independent
threads under the same workspace manager guard; an outer watchdog bounds their
process lifetime. Blocking I/O in the author does not block the enforcement lane. Engine availability is an assumption for physical cessation, never a fact
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
from tools.authoring_shutdown import Shutdown, bounded

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
    def __init__(self, packet, *, factory=None, clock=utc, lock_fd=None, publish=None, prepare=None):
        self.packet, self.factory, self.clock = packet, factory, clock
        self.publish = publish or (lambda guard: None)
        self.prepare = prepare
        self.lock_fd = None if lock_fd is None else os.dup(lock_fd)
        self.recovery = False
        self.author_invocation_started = False
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
                if self.prepare is not None:
                    self.prepare(control, self.packet)
                operations = (self.factory or stage_execution.operations_from)(config, job, control, engine_run=bounded_engine, checkout=self.packet['code_boundary'])
                stack.callback(operations.close)
                lane = Lane(control, job, operations, self.packet, clock=self.clock, stopping=self.stopping)
                self.envelope = lane.held
                self.recovery = lane.recovery
                self.report = lane.tick()
                self.publish(self)
                self.ready.set()
                while not self.shutdown.wait(POLL_SECONDS):
                    self.report = lane.tick()
                    self.publish(self)
                self.report = lane.tick()
        except Exception as fault:
            self.stopping.set()
            self.report = {'state': 'held', 'attempts': dict(self.report.get('attempts', {})), 'faults': [type(fault).__name__ + ': ' + str(fault)]}
        finally:
            if self.lock_fd is not None:
                os.close(self.lock_fd)
            self.ready.set()
            self.finished.set()
            self.publish(self)

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


def supervise_process(packet, guard, launch, *, clock=time.monotonic, sleep=time.sleep, owned_child=None):
    """The outer deadline never calls the authoring sweep or cancellation engine.

    `launch` supplies one owned process with poll/terminate/kill/wait. Process
    exit is not runtime cessation. Recovery gets cleanup time, no new authoring.
    """
    started = clock()
    child = owned_child
    report = {'state': 'held', 'child_started': owned_child is not None, 'child_exited': False, 'faults': []}
    reserve = packet['bounds']['cleanup_seconds']
    total = max(0, (instant(guard.envelope['stop_at']) - instant(guard.clock())).total_seconds()) + reserve
    deadline = started + total
    try:
        if owned_child is None and not guard.recovery and not guard.stopping.is_set():
            child = launch()
            report['child_started'] = True
        elif guard.recovery:
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
                deadline = min(deadline, clock() + reserve)
                if not report['child_exited']:
                    request = getattr(child, "request_shutdown", None)
                    if request is not None:
                        request(deadline - tail)
                    child.terminate()
                terminating = True
            guard.watchdog_deadline = deadline - tail
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
        report['shutdown_deadline'] = deadline
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

    def request_shutdown(self, deadline):
        if not hasattr(self, "shutdown_path"):
            return
        with bounded(deadline, "outer shutdown request"):
            target = Path(self.shutdown_path)
            temporary = target.with_suffix(".tmp")
            temporary.write_text(json.dumps({"run_id": self.run_id, "deadline": deadline}))
            os.replace(temporary, target)

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


def publish_guard(path, guard):
    value = {'envelope': guard.envelope, 'recovery': guard.recovery,
             'stopping': guard.stopping.is_set(), 'finished': guard.finished.is_set(),
             'author_invocation_started': guard.author_invocation_started,
             'report': guard.report}
    target = Path(path)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True))
    os.replace(temporary, target)


class RemoteGuard:
    """The outer watchdog observes; only the manager process composes owners.

    Snapshots are observations, never cessation or permission grants. A missing
    final snapshot is held. The workspace guard stays close-on-exec in the
    manager process; no guard descriptor or store handle crosses this boundary.
    """
    def __init__(self, path, packet):
        self.path, self.packet, self.clock = Path(path), packet, utc
        self.envelope = None
        self.recovery = False
        self.author_invocation_started = False
        self.report = {'state': 'held', 'attempts': {}, 'faults': ['manager has not reported']}
        self.stopping, self.finished = threading.Event(), threading.Event()

    def refresh(self):
        try:
            value = json.loads(self.path.read_text())
        except FileNotFoundError:
            return
        self.envelope = value['envelope']
        self.recovery = value['recovery']
        self.author_invocation_started = value['author_invocation_started']
        self.report = value['report']
        if value['stopping']:
            self.stopping.set()
        if value['finished']:
            self.finished.set()

    def stop(self, *, timeout=0):
        if timeout > 0:
            try:
                with bounded(time.monotonic() + timeout, 'final manager snapshot read'):
                    self.refresh()
            except Exception as fault:
                return dict(self.report, state='held', faults=[*self.report.get('faults', []), str(fault)])
        if not self.finished.is_set():
            return dict(self.report, state='held', faults=[*self.report.get('faults', []), 'manager terminated without final enforcement report; retained observations do not resolve unknown effects'])
        return self.report


def prepare_manager(control, packet):
    # Preserve the historical fresh/reuse preparation order, but acquire the
    # real manager guard before configuration or qualification writes. This
    # process retains it; neither the outer watchdog nor execed tools do.
    import baseline
    from baton_v12.worker_manager import workspaces
    workspaces.hold_manager_instance(control, baseline._workspace_root(packet))
    baseline.prepare(control, packet)


def child_main(packet_path, parent, lock_fd, status_path):
    # One manager process, two independent threads/connections. Both real
    # compositions acquire the SAME process-local workspace guard. The outer
    # process never composes a second manager. Descendants inherit no workspace
    # guard; the existing close-on-exec and at-fork exclusion rules are unchanged.
    import ctypes
    import baseline
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        raise RuntimeError('cannot bind authoring lifetime to its controller')
    packet = baseline.held_packet(packet_path)
    verify_controller(packet)
    if lock_fd is None or os.fstat(lock_fd).st_ino != os.stat(packet['deployment']['control_store'] + '.authoring.lock').st_ino:
        raise RuntimeError('authoring child lacks its inherited controller lock')
    guard = Guard(packet, lock_fd=lock_fd, publish=lambda held: publish_guard(status_path, held), prepare=prepare_manager)
    shutdown = Shutdown(packet, status_path + ".shutdown.json", status_path + ".progress.json")
    failure = None
    previous = {number: signal.signal(number, lambda number, frame: guard.stopping.set()) for number in (signal.SIGTERM, signal.SIGINT)}
    try:
        guard.start()
        reserve = packet["bounds"]["cleanup_seconds"]
        shutdown.maximum = min(shutdown.maximum, time.monotonic() + max(0, (instant(guard.envelope["stop_at"]) - instant(guard.clock())).total_seconds()) + reserve - min(12, reserve / 2))
        if guard.recovery or guard.stopping.is_set():
            # Recovery never enters baseline.main, surveys/submits or admits an
            # author invocation. Keep enforcement available for its cleanup slice.
            guard.stopping.set()
            shutdown.begin()
            guard.finished.wait(max(0, shutdown.until("cleanup") - time.monotonic()))
            return 1
        with ControlStore.open(packet['deployment']['control_store'], incarnation='authoring-child-admission', clock=utc) as control:
            admit_child(control, packet, parent, os.getpid())
        guard.author_invocation_started = True
        return baseline.main(['--packet', packet_path, '--incarnation', 'authoring-child-' + str(os.getpid())], compose=child_compose, shutdown=shutdown)
    except BaseException as fault:
        failure = type(fault).__name__ + ': ' + str(fault)
        raise
    finally:
        guard.stopping.set()
        try:
            shutdown.begin()
            guard.report = shutdown.call('guard-stop', 'guard stop/join', lambda: guard.stop(timeout=max(0, shutdown.until('guard-stop') - time.monotonic())))
            if failure is not None:
                guard.report = dict(guard.report, state='held', faults=[*guard.report.get('faults', []), failure])
            if not guard.thread.is_alive():
                shutdown.call('guard-publication', 'final enforcement publication', lambda: publish_guard(status_path, guard))
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)


def main(argv=None):
    import argparse
    import fcntl
    import sys
    import baseline
    parser = argparse.ArgumentParser(description='One isolated authoring invocation with independent deadline and expiry enforcement')
    parser.add_argument('--packet', required=True)
    parser.add_argument('--child-of', type=int)
    parser.add_argument('--lock-fd', type=int)
    parser.add_argument('--status-path')
    args = parser.parse_args(argv)
    if args.child_of is not None:
        return child_main(args.packet, args.child_of, args.lock_fd, args.status_path)
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
        output_path = packet['outcome_path'] + '.authoring.log'
        status_path = packet['outcome_path'] + f'.manager-{os.getpid()}-{time.time_ns()}.json'
        guard = RemoteGuard(status_path, packet)
        received = []
        def stop(number, frame):
            del frame
            received.append(number)
            guard.stopping.set()
        previous = {number: signal.signal(number, stop) for number in (signal.SIGTERM, signal.SIGINT)}
        try:
            controller_deadline = time.monotonic() + packet['bounds']['total_seconds']
            with open(output_path, 'ab', buffering=0) as output:
                child = Process([sys.executable, '-m', 'tools.authoring_enforcement', '--packet', args.packet,
                                 '--child-of', str(os.getpid()), '--lock-fd', str(lock.fileno()),
                                 '--status-path', status_path], output=output, lock_fd=lock.fileno())
                child.shutdown_path = status_path + ".shutdown.json"
                child.run_id = packet["run_id"]
                try:
                    startup = time.monotonic() + 30
                    while guard.envelope is None and child.poll() is None and time.monotonic() < startup and not guard.stopping.is_set():
                        with bounded(startup, "manager startup snapshot"):
                            guard.refresh()
                        time.sleep(POLL_SECONDS)
                    if guard.envelope is None:
                        raise RuntimeError('manager did not establish its enforcement envelope')
                    def observe_sleep(seconds):
                        with bounded(guard.watchdog_deadline, "manager shutdown observation"):
                            time.sleep(seconds)
                            guard.refresh()
                    report = supervise_process(packet, guard, lambda: child, sleep=observe_sleep, owned_child=child)
                except BaseException as fault:
                    report = {'state': 'held', 'child_started': True, 'child_exited': False,
                              'shutdown_deadline': min(controller_deadline, time.monotonic() + packet['bounds']['cleanup_seconds']),
                              'faults': [type(fault).__name__ + ': ' + str(fault)]}
                    try:
                        child.kill()
                        report['child_status'] = child.wait(timeout=2)
                        report['child_exited'] = True
                    except Exception as cleanup_fault:
                        report['faults'].append('manager process cessation unknown: ' + str(cleanup_fault))
                    report['enforcement'] = guard.stop(timeout=max(0, report['shutdown_deadline'] - time.monotonic()))
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
        try:
            with bounded(report.get('shutdown_deadline', time.monotonic()), 'read shutdown progress'):
                report['shutdown_progress'] = json.loads(Path(status_path + '.progress.json').read_text())
        except FileNotFoundError:
            report['shutdown_progress'] = None
        except Exception as fault:
            report['shutdown_progress'] = {'unknown': type(fault).__name__ + ': ' + str(fault)}
        report['operator_signals'] = received
        if received:
            report['state'] = 'held'
        report['authoring_log'] = output_path
        report['manager_report_path'] = status_path
        report['author_invocation_started'] = guard.author_invocation_started
        report['original_envelope'] = guard.envelope
        report['recovery_only'] = guard.recovery
        result = Path(packet['outcome_path'] + f'.enforcement-{os.getpid()}-{time.time_ns()}.json')
        report['enforcement_path'] = str(result)
        temporary = result.with_suffix('.tmp')
        try:
            with bounded(report.get('shutdown_deadline', time.monotonic()), 'outer outcome publication'):
                temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
                os.replace(temporary, result)
                print(json.dumps(report, sort_keys=True))
        except TimeoutError:
            # No renewed publication budget. Preserve earlier manager/workload/phase
            # evidence; a missing outer result is incomplete, never success.
            return 1
        return 0 if report['state'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
