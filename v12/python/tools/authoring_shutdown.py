"""One process-local shutdown budget, capped by the outer watchdog's deadline.

The request is ephemeral to one manager incarnation on the same host/boot. It is
not a persisted token deadline, a grant, or evidence of container cessation.
"""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import signal
import threading
import time


@contextmanager
def bounded(deadline, step):
    """Interrupt blocking main-thread work; the outer process remains the backstop."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('shutdown allowance exhausted: ' + step)
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('shutdown step requires the manager main thread')
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError('shutdown cannot replace an existing alarm')
    def expired(number, frame):
        raise TimeoutError('shutdown step timed out: ' + step)
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class Shutdown:
    def __init__(self, packet, request, progress):
        self.packet = packet
        self.request, self.progress = Path(request), Path(progress)
        self.deadline = None
        self.maximum = time.monotonic() + packet['bounds']['total_seconds']
        self.phase = 'running'
        self.faults = []

    def begin(self):
        if self.deadline is not None:
            return
        allowance = self.packet['bounds']['cleanup_seconds']
        # The outer reserves this same tail for kill/reap. Inner accounting,
        # guard join and publication must all fit BEFORE that boundary.
        self.deadline = min(self.maximum, time.monotonic() + allowance - min(12, allowance / 2))
        self.reserve = min(4, max(0, self.deadline - time.monotonic()) / 2)
        with bounded(self.deadline, 'read-shutdown-request'):
            try:
                request = json.loads(self.request.read_text())
            except FileNotFoundError:
                request = None
            if request is not None:
                if (type(request.get('deadline')) not in (int, float) or not math.isfinite(request['deadline'])
                        or request['run_id'] != self.packet['run_id']):
                    raise RuntimeError('shutdown request belongs to another run')
                self.deadline = min(self.deadline, request['deadline'])
        self.reserve = min(4, max(0, self.deadline - time.monotonic()) / 2)

    def until(self, phase):
        self.begin()
        fractions = {'cleanup': 1, 'accounting': .7, 'workload-publication': .45,
                     'guard-stop': .2, 'guard-publication': .05}
        return self.deadline - self.reserve * fractions[phase]

    def call(self, phase, step, thunk):
        deadline = self.until(phase)
        with bounded(deadline, step):
            self.phase = step
            value = {'run_id': self.packet['run_id'], 'job_id': self.packet['submission']['job_id'],
                     'step': step, 'deadline': self.deadline, 'step_deadline': deadline,
                     'faults': list(self.faults)}
            temporary = self.progress.with_suffix('.tmp')
            temporary.write_text(json.dumps(value, sort_keys=True))
            os.replace(temporary, self.progress)
            try:
                return thunk()
            except BaseException as fault:
                self.faults.append(type(fault).__name__ + ': ' + str(fault))
                raise
