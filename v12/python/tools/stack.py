"""The persistent v12 stack's lifecycle: start, stop, status.

W183883. An operator runs the v12 scheduler and its read-only monitor BESIDE a
running v11, from `v12/justfile`. This module owns the parts a justfile recipe
should not: which processes are ours, where their state lives, how the child
reaches this distribution's package, and how the monitor's snapshot is
published.

WHAT IT IS NOT. It is not a scheduler. `job_manager serve` is the scheduler and
this starts exactly that, with the operator's own stores and the accepted
`tools.stage_execution:factory`. There is no dummy loop here, and a stack that
cannot be configured REFUSES rather than reporting a comfortable idle.

TWO OWNED PROCESSES, NOT ONE:

  manager    `job_manager serve`   -- the control loop, which reconciles
  publisher  this module           -- writes the status document the viewer reads

The publisher exists because `JOB-VIEWER.md` requires ATOMIC snapshot
publication and the viewer reads a DOCUMENT rather than a store. Putting it in
`start` rather than in `monitor` is what makes "stopping the monitor does not
stop scheduling" true: the monitor only ever reads a file.

OWNERSHIP IS PROVED, NOT ASSUMED, AND IT HAS FOUR ANSWERS. A pid file is a
claim, and pids are reused -- the recorded pid may be somebody else's process
by the time `stop` reads it. So every record carries the process's own start
time from `/proc/<pid>/stat`, and a process matches only when BOTH the pid and
that start time agree. Nothing is signalled on a pid alone.

  absent   there is no record: nobody claimed this role
  live     the pid exists and its start time agrees: ours, and running
  gone     POSITIVELY not ours any more -- no `/proc` entry, a start time that
           disagrees (the pid was reused), or state `Z` (exited, unreaped)
  unknown  we looked and could not tell: a record we cannot read or interpret,
           or a `/proc` read we were denied

REVIEW 2026-09-16T05-15-54Z [R2] IS WHY `unknown` EXISTS AS ITS OWN WORD. It
used to collapse into "not running", so an unreadable record let `start`
replace a manager that was still alive, and a denied `/proc` read was reported
as positive absence. Only `gone` licenses clearing a record, and only `live`
licenses a signal.

AND ADMISSION IS SERIALIZED. [R1]: the transition is read-decide-spawn-record,
and two starts both read absence, both spawned, and the second pair's records
erased the first pair's -- four processes, two of which nobody could ever stop
again. One exclusive lock over the WHOLE transition, taken by `start` and by
`stop`, is what makes "repeatable without duplicates" true under concurrency
rather than only in sequence.
"""
import argparse
import contextlib
import datetime
import errno
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

SCHEMA = "baton.v12.stack/1"
ROOT_ENV = "BATON_V12_STACK_ROOT"
CONFIG_ENV = "BATON_V12_STAGE_EXECUTION_CONFIG"

# What `start` needs named before it will start anything. None is defaulted
# into the checkout: the external state root exists to keep runtime state out
# of the tree, and a default store would put it straight back.
REQUIRED = ("BATON_V12_JOB_STORE", "BATON_V12_CONTROL_STORE",
            "BATON_V12_AUTHORITY_UUID", CONFIG_ENV)

MANAGER = "manager"
PUBLISHER = "publisher"
PROCESSES = (MANAGER, PUBLISHER)

# The four ownership answers. See the module docstring.
ABSENT, LIVE, GONE, UNKNOWN = "absent", "live", "gone", "unknown"

# The status document this launcher will read, PINNED rather than imported.
# `baton_v12.job_manager.documents.STATUS_SCHEMA` is the one authority for this
# string; copying it keeps the lifecycle helper standard-library-only, so
# `just status` still answers on an installation too broken to import the
# package -- which is exactly when an operator needs it. The copy cannot drift
# silently: `tests/tools/test_stack.py` holds it equal to the original.
STATUS_SCHEMA = "baton.v12.job-status/6"

# What `job_manager serve` prints on stderr once its deployment has composed.
# REVIEW 2026-09-16T06-00-07Z [C3]: an observer's published snapshot is
# evidence about the OBSERVER. `observation_from` builds a reader from a held
# configuration; `operations_from` opens the Authority, mints and authorizes
# five sessions, runs three worker preflights, opens the integration store and
# activates the pool. A manager stopped before any of that coexists with an
# observer reading a valid empty store, so publication alone accepted a stack
# that had not initialized.
SERVING_ACKNOWLEDGEMENT = "serving initialization complete: incarnation="

STOP_GRACE_SECONDS = 10.0
PUBLISH_SECONDS = 5
# How long `start` waits for POSITIVE acknowledgement that the stack came up.
# It has to cover a real composition: the manager opens the Job, control,
# Authority and integration stores, mints and authorizes five sessions,
# certifies each worker's profile and activates the pool before its first tick.
READY_SECONDS = 60.0
# How long a lifecycle operation waits for admission before refusing. Longer
# than a start's readiness wait would let two operators queue behind each other
# without knowing it; shorter would refuse an ordinary overlapping stop.
ADMISSION_SECONDS = 30.0
LOCK = "lifecycle.lock"

# This distribution, and the package directory `pyproject.toml` declares under
# `package-dir = {"" = "src"}`.
DISTRIBUTION = Path(__file__).resolve().parent.parent
PACKAGE_PATH = DISTRIBUTION / "src"


class StackRefusal(Exception):
    """An operator-facing refusal. Its text is the whole message."""


def state_root(environ=None):
    environ = os.environ if environ is None else environ
    chosen = environ.get(ROOT_ENV)
    if chosen:
        return Path(chosen)
    base = environ.get("XDG_STATE_HOME") or os.path.join(
        environ.get("HOME", "/tmp"), ".local", "state")
    return Path(base) / "baton-v12-stack"


def _record(root, name):
    return Path(root) / (name + ".json")


def snapshot_path(root):
    """The status document the publisher writes and the viewer reads."""
    return Path(root) / "status.json"


def log_path(root, name):
    return Path(root) / (name + ".log")


def lock_path(root):
    return Path(root) / LOCK


# -- the child's runtime ------------------------------------------------------


def child_environment(environ=None):
    """The environment a child of this stack actually needs to import.

    REVIEW 2026-09-16T05-15-54Z [R3]. The recipes ran a bare `python3 -m
    tools.job_manager` from `v12/python`, and `tools/job_manager.py` imports
    `baton_v12`, which lives under `src` because `pyproject.toml` declares
    `package-dir = {"" = "src"}`. So the documented child died at once on
    `ModuleNotFoundError: No module named \'baton_v12\'` -- and `start`, which
    only checked that the kernel had forked something, printed `started` and
    returned 0. `job_viewer` imports the same package, so `monitor` was broken
    for the identical reason.

    `DEPLOYMENT.md` states the prerequisite as `PYTHONPATH=src:.` throughout.
    It is built here ABSOLUTELY rather than relatively: a relative entry is
    resolved against whatever directory a child happens to run in, which is the
    same fault this module already refuses for a relative store. An operator's
    own PYTHONPATH is kept, after ours, rather than discarded.
    """
    prepared = dict(os.environ if environ is None else environ)
    wanted = [str(PACKAGE_PATH), str(DISTRIBUTION)]
    inherited = [part for part in (prepared.get("PYTHONPATH") or "").split(os.pathsep)
                 if part and part not in wanted]
    prepared["PYTHONPATH"] = os.pathsep.join(wanted + inherited)
    return prepared


# -- process identity --------------------------------------------------------


def _proc(pid):
    """(state, start time) for a pid, or why we cannot say.

    Answers `("absent", None)` only for a POSITIVE absence -- the kernel says
    there is no such process -- and `("unknown", None)` when the read was
    denied or the record made no sense. [R2]: those were one answer before, so
    a `/proc` this process may not read reported as "nobody is there".

    The comm field is parenthesised and may itself contain spaces and
    parentheses, so the split is anchored on the LAST ')'.
    """
    try:
        with open("/proc/%d/stat" % pid, "rb") as handle:
            raw = handle.read()
    except (FileNotFoundError, ProcessLookupError):
        return "absent", None
    except OSError:
        return "unknown", None
    tail = raw[raw.rfind(b")") + 2:].split()
    if len(tail) < 20:
        return "unknown", None
    try:
        return tail[0].decode(), int(tail[19])
    except (ValueError, UnicodeDecodeError):
        return "unknown", None


def started_at(pid):
    """The process's own start time, which is what identifies it beside a pid.

    Returns None when the process does not exist OR when we could not tell;
    only `_spawn` uses it, and there the two cases are the same one -- a child
    we just forked and can no longer identify is a child we will not record.
    """
    return _proc(pid)[1]


def ownership(record):
    """What we POSITIVELY know about the process a record names.

    One of ABSENT, LIVE, GONE, UNKNOWN. A TERMINATED-BUT-UNREAPED process
    still HAS a `/proc` entry with its original start time, so an identity
    match alone reports a zombie as running; state 'Z' is the difference
    between "still running" and "not yet reaped".
    """
    if record is None:
        return ABSENT
    if type(record) is not dict or record.get("unreadable"):
        return UNKNOWN
    pid, start = record.get("pid"), record.get("started_at")
    if type(pid) is not int or type(start) is not int or pid <= 0:
        # A record we cannot interpret is not the same as no record: something
        # claimed this role and we cannot say what happened to it.
        return UNKNOWN
    state, observed = _proc(pid)
    if state == "absent":
        return GONE
    if state == "unknown":
        return UNKNOWN
    if observed != start:
        # The pid exists and is somebody else's. Positively not ours.
        return GONE
    return GONE if state == "Z" else LIVE


def alive(record):
    """Is the process this record names still running, and still the same one?"""
    return ownership(record) == LIVE


def read_record(root, name):
    place = _record(root, name)
    try:
        value = json.loads(place.read_bytes())
    except FileNotFoundError:
        return None
    except (ValueError, OSError):
        # A record we cannot read is reported as unreadable rather than as an
        # absence: "nobody is running" and "we cannot tell" are different.
        return {"unreadable": True}
    if type(value) is not dict or value.get("schema") != SCHEMA:
        return {"unreadable": True}
    return value


def write_record(root, name, record):
    place = _record(root, name)
    temporary = place.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, place)


def clear_record(root, name):
    try:
        _record(root, name).unlink()
    except FileNotFoundError:
        pass


# -- admission ----------------------------------------------------------------


@contextlib.contextmanager
def admission(root, *, wait=ADMISSION_SECONDS, sleep=time.sleep,
              monotonic=time.monotonic):
    """Exclusive admission for a whole ownership transition.

    REVIEW 2026-09-16T05-15-54Z [R1]. `start` read the records, decided, spawned
    and then wrote the records, with nothing covering the gap. Two starts both
    read absence, both spawned a manager and a publisher, and the second pair's
    records overwrote the first pair's: four live processes, two ownership
    records, and two processes no later `stop` could ever find. Repeating a
    start SEQUENTIALLY proved nothing about that.

    `stop` takes the same lock, so a stop cannot interleave with a start
    either -- otherwise a stop could clear a record for a process a start was
    at that moment replacing.

    An `flock` rather than a lock FILE, because a lock file is a claim with the
    same problem as a pid file: it outlives whatever wrote it. A kernel lock is
    released when the holder exits, however it exits, so an operator who kills
    a start does not have to know about a stale lock to run the next one.
    O_CLOEXEC so the lock never reaches a child we are about to spawn.
    """
    Path(root).mkdir(parents=True, exist_ok=True)
    handle = os.open(str(lock_path(root)),
                     os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    try:
        deadline = monotonic() + wait
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as failure:
                if failure.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if monotonic() >= deadline:
                    raise StackRefusal(
                        "another v12 stack lifecycle operation holds %s and "
                        "did not release it within %gs; nothing was started or "
                        "stopped. Run `just status` to see what is there."
                        % (lock_path(root), wait))
                sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        os.close(handle)


# -- configuration -----------------------------------------------------------


def configured(environ=None):
    """The operands `start` needs, or a refusal naming every missing one.

    Named all at once rather than one per attempt: an operator setting these up
    for the first time should see the whole list, not discover it four runs in.
    """
    environ = os.environ if environ is None else environ
    missing = [name for name in REQUIRED if not environ.get(name)]
    if missing:
        raise StackRefusal(
            "the v12 stack is not configured: set " + ", ".join(missing)
            + ". See v12/STACK.md for the one-time setup; nothing is defaulted "
              "into the checkout, because runtime state belongs outside it.")
    settings = {name: environ[name] for name in REQUIRED}
    for name in (CONFIG_ENV, "BATON_V12_JOB_STORE", "BATON_V12_CONTROL_STORE"):
        if not os.path.isabs(settings[name]):
            raise StackRefusal(name + " must be an absolute path; " + settings[name]
                               + " is relative, and a relative store resolves "
                                 "against whatever directory the recipe ran from")
    if not Path(settings[CONFIG_ENV]).is_file():
        raise StackRefusal("the stage-execution configuration named by " + CONFIG_ENV
                           + " does not exist: " + settings[CONFIG_ENV]
                           + ". A stack with no worker configuration is not an idle "
                             "stack, and reporting it as one would hide the gap.")
    return settings


# -- start -------------------------------------------------------------------


def _python():
    return sys.executable or "python3"


def incarnation():
    """A fresh incarnation for every manager process start.

    `DEPLOYMENT.md` requires one, and [C3] gives it a second job: it is what
    ties a serving acknowledgement in the log to THIS start rather than to a
    previous one that happened to leave a line behind.
    """
    return "v12-stack-%d-%d" % (os.getpid(), time.time_ns())


def _child(subcommand, operands):
    """One child's argv, in whichever form this process is running in.

    W183883, OWNER-PYINSTALLER-20260916.md. These used to be
    `sys.executable -m tools.X`, which is right for an interpreter and WRONG
    for a bundle: in a frozen build `sys.executable` is the application itself
    and `-m` means nothing to it, so a deployed supervisor would have started
    copies of itself with operands it does not understand. `stack_command`
    owns the one place the two forms differ.
    """
    from tools import stack_command
    return stack_command.bundled_argv(subcommand, operands)


def manager_argv(settings, named):
    return _child("manager", [
            "--store", settings["BATON_V12_JOB_STORE"],
            "--incarnation", named,
            "--authority-uuid", settings["BATON_V12_AUTHORITY_UUID"],
            "serve",
            "--control", settings["BATON_V12_CONTROL_STORE"],
            "--operations", "tools.stage_execution:factory"])


def publisher_argv(root):
    # `--root` is a TOP-LEVEL operand, so it precedes the subcommand. Found by
    # running the recipes rather than by reading them: argparse refused the
    # reversed order, the publisher exited at once, and `status` correctly
    # reported it stale while the manager ran. `stack_command` appends the verb
    # for this reason, so only the root is named here.
    return _child("publish", ["--root", str(root)])


def _log_tail(root, name, lines=12):
    """The child's own last words, which are the concrete reason it failed."""
    try:
        text = log_path(root, name).read_text(errors="replace")
    except OSError:
        return "(no readable log at " + str(log_path(root, name)) + ")"
    kept = [one for one in text.splitlines() if one.strip()][-lines:]
    return "\n".join("    " + one for one in kept) if kept else "(its log is empty)"


def _spawn(root, name, argv, environ, extra=None):
    """Start one owned process detached from this shell, recording its identity.

    ONE RECORD WRITE, AND IT PUBLISHES THE WHOLE IDENTITY. REVIEW
    2026-09-16T06-35-51Z [D1]: the caller used to write the record a SECOND time
    to add the manager's incarnation, and only then registered the process for
    rollback -- so a failure in that second write escaped with the manager live
    and outside the unwind list. `extra` exists so there is no second write to
    fail rather than a second write that is guarded.

    [R1], last clause: a spawn that could not be RECORDED used to leave the
    process running and unowned, which is exactly the orphan the admission lock
    exists to prevent. The child is a `Popen` we own, so it can be stopped by
    object identity -- not by a bare pid, which is the thing this module refuses
    to signal anywhere else.
    """
    try:
        before = log_path(root, name).stat().st_size
    except OSError:
        before = 0
    log = open(log_path(root, name), "ab", buffering=0)
    try:
        child = subprocess.Popen(
            argv, cwd=str(DISTRIBUTION),
            env=child_environment(environ), stdin=subprocess.DEVNULL,
            stdout=log, stderr=log, start_new_session=True)
    finally:
        log.close()
    try:
        # Read the start time back from /proc rather than trusting the moment
        # of spawn: this is the value `ownership` and `stop` compare against.
        start = started_at(child.pid)
        if start is None:
            raise StackRefusal(
                name + " exited before it could be identified. Its log says:\n"
                + _log_tail(root, name))
        record = {"schema": SCHEMA, "name": name, "pid": child.pid,
                  "started_at": start, "argv": argv,
                  # WHERE THIS PROCESS'S OUTPUT BEGINS. [C3]: a serving
                  # acknowledgement is only this start's if it was written
                  # after this start opened the log.
                  "log_from": before,
                  "log": str(log_path(root, name))}
        record.update(extra or {})
        write_record(root, name, record)
    except BaseException:
        _reap(child)
        raise
    _ADMITTED.append(child)
    return record


# The children THIS process admitted. A detached stack outlives the command
# that started it, so a `Popen` dropped while its child still runs is the
# intended outcome rather than a leak -- but the interpreter cannot know that,
# and an abandoned handle also leaves an exited child unreaped. Holding them
# lets `_collect` reap the ones that have actually ended.
_ADMITTED = []


def _collect(pid):
    """Reap a child this process started, if it is one of ours and has ended.

    `waitpid` reaches our own children only, so a reused pid cannot be touched
    through it -- which is the same rule `_signal` keeps for the same reason.
    """
    for child in list(_ADMITTED):
        if child.pid == pid:
            if child.poll() is not None:
                _ADMITTED.remove(child)
            return
    try:
        os.waitpid(pid, os.WNOHANG)
    except (ChildProcessError, OSError):
        pass


def _reap(child):
    """Stop and collect a child we own but did not manage to record."""
    for act in (child.terminate, child.kill):
        try:
            act()
            child.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue
        except OSError:
            return
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def _snapshot_mark(root):
    try:
        return snapshot_path(root).stat().st_mtime_ns
    except OSError:
        return None


def acknowledged(record):
    """Has the process this record names said its deployment composed?

    [C3]. `job_manager serve` prints one line on stderr after
    `_operations_from` returns and before it serves -- which is the only
    statement anywhere that a SERVING deployment initialized, because the
    observer that publishes snapshots composes nothing. The line must name THIS
    record's incarnation and must sit after the offset at which this start
    opened the log, so neither another manager's line nor a previous run's can
    answer for it.
    """
    named = record.get("incarnation")
    if type(named) is not str:
        return False
    try:
        with open(record["log"], "rb") as handle:
            handle.seek(record.get("log_from") or 0)
            written = handle.read()
    except OSError:
        return False
    wanted = (SERVING_ACKNOWLEDGEMENT + repr(named)).encode()
    return wanted in written


def _await_ready(root, mark, expecting, *, started, require_snapshot,
                 ready_seconds, sleep, monotonic, now=time.time):
    """A BOUNDED, POSITIVE acknowledgement that the stack actually came up.

    [R3]: reading a pid's start time immediately after `Popen` proves that the
    kernel forked, and nothing else. The documented child in fact died on
    `ModuleNotFoundError` and `start` reported both processes started and
    returned 0, while `status` reported the manager stale.

    TWO THINGS ARE REQUIRED, and each one answers a different failure:

      every owned process is still LIVE -- which catches an import failure, a
        refused operand and any other early exit; and

      the publisher has written a snapshot DURING this start -- which is the
        only evidence available here that the CONFIGURATION composes, because
        publishing means `job_manager status --observe` read the operator's
        Job and control stores through the real deployment document and
        `tools.stage_execution:observing_factory` held it.

    The second is compared against the mark taken before spawning, so a stale
    snapshot left by a previous run cannot be mistaken for this run's, and the
    document it writes must be valid and fresh BY ITS OWN `observed_at` -- a
    file copied into place is freshly written and stalely observed.

    AND A THIRD, ADDED BY [C3]. The first two are facts about processes and
    about the OBSERVER. `observation_from` builds a reader out of a held
    configuration and composes no deployment, so a manager that never
    initialized -- delayed, stopped, or still opening the Authority -- passed
    this gate while its publisher happily read an empty store. Every manager
    THIS start spawned must therefore have printed its own serving
    acknowledgement, naming this start's incarnation, after this start opened
    its log. A manager that was already running is not this start's to
    acknowledge; the start that admitted it proved it, and its record says so.
    """
    deadline = monotonic() + ready_seconds
    while True:
        for name in PROCESSES:
            record = read_record(root, name)
            held = ownership(record)
            if held != LIVE:
                raise StackRefusal(
                    name + " did not stay up (" + held + "). Its log says:\n"
                    + _log_tail(root, name))
        pending = [record for record in expecting if not acknowledged(record)]
        if not pending:
            if not require_snapshot:
                # Nothing was spawned, so nothing new is owed here: this is the
                # repeated-start path, which publishes no snapshot of its own.
                #
                # AN EXPLICIT OPERAND, NOT `mark is None`. That spelling was
                # wrong and a case caught it: a genuine FIRST start also has no
                # previous snapshot to mark, and would have skipped the
                # observation check entirely.
                return None
            current = _snapshot_mark(root)
            published = snapshot(root, now())
            if (current is not None and current != mark
                    and published["state"] == "fresh"):
                return current
        if monotonic() >= deadline:
            if pending:
                ours = [one["pid"] for one in started]
                inherited = [one for one in pending if one["pid"] not in ours]
                raise StackRefusal(
                    ", ".join(one["name"] for one in pending)
                    + " is running but never acknowledged that its deployment "
                      "composed within %gs, so this stack has NOT been shown "
                      "to have initialized. A published snapshot cannot answer "
                      "for it: the observer composes no deployment."
                    % ready_seconds
                    + ("" if not inherited else
                       " pid %d was ALREADY running when this start arrived, so "
                       "it is not this start's to take away; run `just stop` and "
                       "then `just start` if it is stuck."
                       % inherited[0]["pid"])
                    + " Its log says:\n" + _log_tail(root, pending[0]["name"]))
            raise StackRefusal(
                "every process is running and acknowledged, but no valid, "
                "freshly observed status snapshot was published within %gs, so "
                "this stack has not been shown to compose its observation. The "
                "publisher's log says:\n" % ready_seconds
                + _log_tail(root, PUBLISHER))
        sleep(0.1)


def _unwind(root, started, stream):
    """Take back exactly what this start put up, and say what it could not.

    TRUTHFUL OWNERSHIP DURING CLEANUP [R3]: a record is cleared only for a
    process this unwind positively stopped. One it could not stop keeps its
    record, so the next `stop` can still find it.
    """
    for record in started:
        name = record["name"]
        try:
            _take_back(root, record, stream)
        except BaseException as failure:                     # noqa: BLE001
            # [D1]: ONE PROCESS THAT CANNOT BE TAKEN BACK MUST NOT STOP THE
            # OTHERS BEING ACCOUNTED FOR. The record stays either way, so the
            # next stop can still find whatever this could not.
            print("could not unwind %s (%s: %s; record retained)"
                  % (name, type(failure).__name__, failure), file=stream)


def _take_back(root, record, stream):
    """Stop one process this start admitted, or say why its record stays."""
    name = record["name"]
    try:
        _signal(record, signal.SIGTERM)
    except StackRefusal as refusal:
        print("could not unwind %s: %s (record retained)" % (name, refusal),
              file=stream)
        return
    for _ in range(100):
        if ownership(record) != LIVE:
            break
        time.sleep(0.05)
    if ownership(record) == LIVE:
        try:
            _signal(record, signal.SIGKILL)
        except StackRefusal:
            pass
    held = ownership(record)
    if held != GONE:
        # [C1]: ONLY A POSITIVE `gone` CLEARS A RECORD. This waited on LIVE and
        # cleared on anything else, so visibility that became `unknown` after
        # the signal -- a denied `/proc` read -- read as a process taken back.
        # The process may be running; the record stays.
        print("could not unwind %s pid %d (%s; record retained)"
              % (name, record["pid"], held), file=stream)
        return
    _collect(record["pid"])
    clear_record(root, name)


def start(root, environ=None, *, stream=sys.stdout, ready_seconds=None,
          sleep=time.sleep, monotonic=time.monotonic):
    # Resolved here rather than bound as a default, so the module constant
    # stays the one place the bound lives.
    ready_seconds = READY_SECONDS if ready_seconds is None else ready_seconds
    environ = dict(os.environ if environ is None else environ)
    settings = configured(environ)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with admission(root, sleep=sleep, monotonic=monotonic):
        return _start_admitted(root, settings, environ, stream=stream,
                               ready_seconds=ready_seconds, sleep=sleep,
                               monotonic=monotonic)


def _start_admitted(root, settings, environ, *, stream, ready_seconds, sleep,
                    monotonic):
    running = {name: read_record(root, name) for name in PROCESSES}
    held = {name: ownership(running[name]) for name in PROCESSES}

    unknown = [name for name in PROCESSES if held[name] == UNKNOWN]
    if unknown:
        # [R2]: NOT REPLACED, NOT SIGNALLED, AND THE EVIDENCE IS KEPT. A record
        # we cannot read may name a manager that is running right now; starting
        # a second one over it is how the first becomes unstoppable.
        raise StackRefusal(
            "ownership of " + ", ".join(unknown) + " cannot be established, so "
            "nothing was started: a process this stack owns may still be "
            "running. The record" + ("s are" if len(unknown) > 1 else " is")
            + " retained at " + ", ".join(str(_record(root, one)) for one in unknown)
            + ". Recover by reading " + ", ".join(str(log_path(root, one)) for one in unknown)
            + " and, once you have established that nothing is running, "
            "removing the retained record. Nothing here will remove it for "
            "you, and nothing here will signal a process it cannot identify.")

    # [D2]: LIVENESS IS NOT READINESS, FOR A MANAGER THIS START DID NOT SPAWN
    # EITHER. Both the fast return below and the publisher-replacement path
    # accepted a live manager on the reading that "the start that admitted it
    # proved it" -- which is false after an interrupted start, and false after
    # an unwind that deliberately RETAINED a live process it could not stop. A
    # live manager is reused only when its acknowledgement holds for that
    # identity NOW; otherwise it waits in the same bounded gate a fresh one
    # does, and is never killed and never duplicated.
    expecting = []
    if held[MANAGER] == LIVE and not acknowledged(running[MANAGER]):
        expecting.append(running[MANAGER])

    if all(held[name] == LIVE for name in PROCESSES):
        # REPEATABLE WITHOUT DUPLICATES. A second start is not an error and is
        # not a second manager; it reports the one that is already there --
        # once that one has been shown to have initialized. No new snapshot is
        # required, because this start published nothing.
        if expecting:
            _await_ready(root, None, expecting, started=[],
                         require_snapshot=False, ready_seconds=ready_seconds,
                         sleep=sleep, monotonic=monotonic)
            print("the manager that was already running has now acknowledged "
                  "that its deployment composed", file=stream)
        for name in PROCESSES:
            print("already running: %s pid %d" % (name, running[name]["pid"]),
                  file=stream)
        return 0
    for name in PROCESSES:
        # Only a POSITIVELY gone process has its record cleared.
        if held[name] == GONE:
            clear_record(root, name)

    mark = _snapshot_mark(root)
    started = []
    try:
        if held[MANAGER] != LIVE:
            named = incarnation()
            # ONE OWNED TRANSACTION, and registered for rollback immediately.
            record = _spawn(root, MANAGER, manager_argv(settings, named),
                            environ, extra={"incarnation": named})
            started.append(record)
            expecting.append(record)
        if held[PUBLISHER] != LIVE:
            started.append(_spawn(root, PUBLISHER, publisher_argv(root), environ))
        _await_ready(root, mark, expecting, started=started,
                     require_snapshot=True, ready_seconds=ready_seconds,
                     sleep=sleep, monotonic=monotonic)
    except BaseException:
        # [C2]: EVERY FAILED ADMISSION UNWINDS, not only a refusal. This caught
        # `StackRefusal` alone, and `_spawn` also raises `OSError` from opening
        # the log, from `Popen` and from writing the record -- so a publisher
        # that failed after the manager was admitted escaped with the manager
        # still running and recorded. The ORIGINAL error is re-raised
        # unchanged: a cleanup problem must not replace the failure that caused
        # it, which is the rule `job_manager` already keeps for its own
        # releases.
        _unwind(root, started, stream)
        raise
    for record in started:
        print("started: %s pid %d" % (record["name"], record["pid"]), file=stream)
    # NOTHING IS WRITTEN HERE. [D1]: a `serving_acknowledged` flag used to be
    # published at this point, OUTSIDE the block that unwinds -- and it was a
    # CACHE of what the manager's own log already says, which is both a write
    # that can fail and a second place the truth can live. `acknowledged` reads
    # that log directly, so there is no post-spawn record write at all.
    print("ready: every manager this start ran acknowledged that its deployment "
          "composed, and the publisher wrote a valid, freshly observed snapshot",
          file=stream)
    print("state root: " + str(root), file=stream)
    print("no Job was submitted; an empty configured stack is a valid idle state",
          file=stream)
    return 0


# -- stop --------------------------------------------------------------------


def _signal(record, number):
    """Signal ONLY a process whose pid and start time both still match.

    This is where pid reuse would otherwise become someone else's problem --
    literally: a recorded pid that now belongs to an unrelated process must
    never be signalled.
    """
    if ownership(record) != LIVE:
        return False
    try:
        os.kill(record["pid"], number)
    except ProcessLookupError:
        return False
    except PermissionError:
        # It exists and is not ours to signal. Reported, never forced.
        raise StackRefusal("pid %d is not ours to signal" % record["pid"])
    return True


def runtime_boundary(root, *, now=None, held=None):
    """What stopping the SUPERVISORS does not tell you about execution.

    REVIEW 2026-09-16T05-15-54Z [R4]. `stop` inspected its own two records and
    then said the stack was stopped. The manager is a SUPERVISOR: the attempts
    it opened live in runtimes it does not own, and a manager that had to be
    KILLed cannot have reconciled anything on its way out. So supervisor exit
    is not evidence that execution finished, and it is not evidence that a
    restart is safe.

    The honest answer is read from the last published snapshot -- and when that
    snapshot is absent, unreadable or STALE, the answer is `unknown`, because a
    stale document describes a world the manager has since moved on from.
    """
    now = time.time() if now is None else now
    answer = snapshot(root, now) if held is None else held
    if answer["state"] == "absent":
        return {"state": UNKNOWN,
                "detail": "no snapshot was ever published under " + str(root)}
    if answer["state"] == "unreadable":
        return {"state": UNKNOWN, "detail": "the last snapshot at "
                + answer["path"] + " could not be read as a status document ("
                + str(answer.get("detail")) + ")"}
    if answer["state"] == "stale":
        return {"state": UNKNOWN,
                "observed_age_seconds": answer["observed_age_seconds"],
                "published_age_seconds": answer["published_age_seconds"],
                "detail": "the last snapshot was observed %.1fs ago and written "
                          "%.1fs ago" % (answer["observed_age_seconds"],
                                         answer["published_age_seconds"])}
    if not answer["canonical"]:
        # A partial observation cannot say what is NOT executing, which is the
        # only thing this line would be used for.
        return {"state": UNKNOWN,
                "observed_age_seconds": answer["observed_age_seconds"],
                "detail": "the last snapshot is not canonical, so it does not "
                          "describe every Job"}
    open_episodes, recorded_runtimes = 0, 0
    # Safe to walk: `_malformed` already refused every shape this traverses.
    for job in (answer["document"].get("jobs") or []):
        for stage in (job.get("stages") or []):
            for episode in (stage.get("episodes") or []):
                if episode.get("ended_state") is None:
                    open_episodes += 1
            if stage.get("runtime") is not None:
                recorded_runtimes += 1
    return {"state": "observed",
            "observed_age_seconds": answer["observed_age_seconds"],
            "published_age_seconds": answer["published_age_seconds"],
            "open_episodes": open_episodes,
            "recorded_runtimes": recorded_runtimes}


def _print_runtime_boundary(answer, stream):
    if answer["state"] == UNKNOWN:
        print("runtime   unknown: " + answer["detail"]
              + ", so what is still executing was NOT resolved here", file=stream)
        return
    print("runtime   %d open episode(s), %d with a recorded runtime, observed "
          "%.1fs ago" % (answer["open_episodes"], answer["recorded_runtimes"],
                         answer["observed_age_seconds"]), file=stream)
    if answer["open_episodes"]:
        print("          stopping a supervisor does not stop a runtime, and "
              "this is the last RECORDED answer rather than a fresh one",
              file=stream)


def stop(root, *, stream=sys.stdout, grace=STOP_GRACE_SECONDS, sleep=time.sleep,
         monotonic=time.monotonic, now=None):
    root = Path(root)
    with admission(root, sleep=sleep, monotonic=monotonic):
        return _stop_admitted(root, stream=stream, grace=grace, sleep=sleep,
                              monotonic=monotonic, now=now)


def _stop_admitted(root, *, stream, grace, sleep, monotonic, now):
    stopped, absent, unresolved = [], [], []
    for name in PROCESSES:
        record = read_record(root, name)
        held = ownership(record)
        if held == ABSENT:
            absent.append(name)
            continue
        if held == UNKNOWN:
            # [R2]/[R4]: the record stays, and this stop is NOT a success.
            print("unresolved ownership: %s (record retained at %s)"
                  % (name, _record(root, name)), file=stream)
            unresolved.append(name)
            continue
        if held == GONE:
            # Either it exited, or its pid now belongs to somebody else. The
            # record goes; nothing is signalled.
            clear_record(root, name)
            absent.append(name)
            continue
        try:
            _signal(record, signal.SIGTERM)
        except StackRefusal as refusal:
            print("unresolved: %s (%s; record retained)" % (name, refusal),
                  file=stream)
            unresolved.append(name)
            continue
        stopped.append((name, record))

    deadline = monotonic() + grace
    for name, record in stopped:
        while ownership(record) == LIVE and monotonic() < deadline:
            sleep(0.05)
        if ownership(record) == LIVE:
            try:
                _signal(record, signal.SIGKILL)
            except StackRefusal:
                pass
            while ownership(record) == LIVE and monotonic() < deadline + 1:
                sleep(0.05)
        held = ownership(record)
        if held == LIVE:
            # Truthful rather than optimistic: the record stays so a later stop
            # can find it again, AND this stop reports failure.
            print("did not stop: %s pid %d (record retained)"
                  % (name, record["pid"]), file=stream)
            unresolved.append(name)
            continue
        if held != GONE:
            # [C1]: `unknown` AFTER SIGNALLING IS NOT COMPLETION. This waited on
            # LIVE and then cleared the record for every other answer, so a
            # process whose visibility was lost was announced `stopped` while it
            # was still running, and the stop returned 0.
            print("unresolved: %s pid %d is %s after signalling (record "
                  "retained)" % (name, record["pid"], held), file=stream)
            unresolved.append(name)
            continue
        _collect(record["pid"])
        clear_record(root, name)
        print("stopped: %s pid %d" % (name, record["pid"]), file=stream)
    for name in absent:
        # REPEATED STOP IS NOT AN ERROR.
        print("not running: " + name, file=stream)
    _print_runtime_boundary(runtime_boundary(root, now=now), stream)
    print("stores and evidence retained under the configured paths", file=stream)
    if unresolved:
        print("unresolved: " + ", ".join(sorted(set(unresolved)))
              + "; this stack is NOT stopped", file=stream)
        return 1
    return 0


# -- status ------------------------------------------------------------------


def _instant(value):
    """A status document's own observation time, as a POSIX timestamp.

    None when it is not one. `observed_at` is the MANAGER'S wall clock -- when
    the store was read -- which is a different fact from when the file was
    written, and `JOB-VIEWER.md` draws that distinction because a document can
    be copied, restored or republished without being re-observed.
    """
    if type(value) is not str:
        return None
    try:
        held = datetime.datetime.fromisoformat(value)
    except ValueError:
        return None
    if held.tzinfo is None:
        held = held.replace(tzinfo=datetime.timezone.utc)
    return held.timestamp()


def _malformed(document):
    """Why this is not a status document, or None.

    REVIEW 2026-09-16T06-00-07Z [C4]: `runtime_boundary` guarded the parse and
    then walked jobs, stages and episodes OUTSIDE that guard, so
    `{"jobs": [null]}` raised `AttributeError` out of a `stop` that had already
    signalled its processes. The viewer's own reader learned this in
    claim168169 for the same input. Everything this module traverses is checked
    HERE, before anything traverses it.
    """
    if type(document) is not dict:
        return "a status snapshot is one document, not " + type(document).__name__
    if document.get("schema") != STATUS_SCHEMA:
        return ("this launcher reads " + STATUS_SCHEMA + " and this is "
                + repr(document.get("schema")))
    if _instant(document.get("observed_at")) is None:
        return ("this document does not carry a readable observed_at: "
                + repr(document.get("observed_at")))
    jobs = document.get("jobs")
    if jobs is None:
        return None
    if type(jobs) is not list:
        return "this document's jobs are a list; this is " + type(jobs).__name__
    for job in jobs:
        if type(job) is not dict:
            return ("every Job in this document is a document; one is "
                    + type(job).__name__)
        stages = job.get("stages")
        if stages is None:
            continue
        if type(stages) is not list:
            return "a Job's stages are a list; one is " + type(stages).__name__
        for stage in stages:
            if type(stage) is not dict:
                return ("every stage is a document; one is "
                        + type(stage).__name__)
            episodes = stage.get("episodes")
            if episodes is None:
                continue
            if type(episodes) is not list:
                return ("a stage's episodes are a list; one is "
                        + type(episodes).__name__)
            for episode in episodes:
                if type(episode) is not dict:
                    return ("every episode is a document; one is "
                            + type(episode).__name__)
    return None


def snapshot(root, now):
    """The published document, validated before anything reads it.

    TWO AGES, NOT ONE. `observed` is how old the MANAGER'S reading of the store
    is; `published` is how old the file is. A document copied into place is
    freshly published and stalely observed, and reporting only the second would
    call it current. Either one being old makes the snapshot stale.
    """
    place = snapshot_path(root)
    try:
        raw = place.read_bytes()
        published = now - place.stat().st_mtime
    except FileNotFoundError:
        return {"state": "absent"}
    except OSError as failure:
        return {"state": "unreadable", "path": str(place),
                "detail": "%s: %s" % (type(failure).__name__, failure)}
    try:
        document = json.loads(raw)
    except ValueError:
        return {"state": "unreadable", "path": str(place),
                "published_age_seconds": round(published, 3),
                "detail": "this file is not one JSON document"}
    problem = _malformed(document)
    if problem is not None:
        return {"state": "unreadable", "path": str(place),
                "published_age_seconds": round(published, 3),
                "detail": problem}
    observed = now - _instant(document["observed_at"])
    oldest = max(observed, published)
    return {"state": "stale" if oldest > PUBLISH_SECONDS * 3 else "fresh",
            "path": str(place), "document": document,
            "canonical": bool(document.get("canonical")),
            "observed_age_seconds": round(observed, 3),
            "published_age_seconds": round(published, 3)}


def _reported(answer):
    """The snapshot answer without the document it carries."""
    return {name: value for name, value in answer.items() if name != "document"}


def observe(root, *, now=None, environ=None):
    """The whole machine-readable answer `status` prints."""
    root = Path(root)
    now = time.time() if now is None else now
    processes = {}
    for name in PROCESSES:
        record = read_record(root, name)
        held = ownership(record)
        if held == ABSENT:
            processes[name] = {"state": "absent"}
        elif held == UNKNOWN:
            processes[name] = {
                "state": "unknown", "record": str(_record(root, name)),
                "detail": "ownership cannot be established; the record is "
                          "retained and nothing will be started over it"}
        elif held == LIVE:
            processes[name] = {"state": "running", "pid": record["pid"],
                               "log": record.get("log")}
            if name == MANAGER:
                # [C3]: a running manager is not necessarily an INITIALIZED
                # one, so the two facts are reported separately.
                processes[name]["serving"] = (
                    "acknowledged" if acknowledged(record)
                    else "unacknowledged: this manager has not said its "
                         "deployment composed")
        else:
            # The distinction that matters: the record claims a process that is
            # positively not there, which is not the same as no record at all.
            processes[name] = {"state": "stale", "pid": record.get("pid"),
                               "log": record.get("log")}
    published = snapshot(root, now)
    try:
        configured(environ)
        configuration = {"state": "configured"}
    except StackRefusal as refusal:
        configuration = {"state": "unconfigured", "detail": str(refusal)}
    return {"schema": SCHEMA, "root": str(root), "processes": processes,
            "snapshot": _reported(published), "configuration": configuration,
            "jobs": _jobs(published),
            "runtime": runtime_boundary(root, now=now, held=published)}


def _jobs(answer):
    """What the published document says about Jobs, or why it says nothing.

    `absent` is "nobody has published yet"; `unreadable` is "we looked and
    could not tell". Neither is reported as an empty pipeline. A STALE document
    still counts its Jobs -- how old the reading is belongs to the snapshot
    line, which says it.
    """
    if answer["state"] in ("absent", "unreadable"):
        return {"state": answer["state"], "detail": answer.get("detail")}
    listed = answer["document"].get("jobs") or []
    return {"state": "observed", "count": len(listed),
            "canonical": answer["canonical"]}


def status(root, *, stream=sys.stdout, environ=None, now=None):
    answer = observe(root, now=now, environ=environ)
    for name in PROCESSES:
        one = answer["processes"][name]
        detail = "" if one.get("pid") is None else " pid %s" % one["pid"]
        print("%-10s %s%s" % (name, one["state"], detail), file=stream)
        if one["state"] == "unknown":
            print("           " + one["detail"] + " (" + one["record"] + ")",
                  file=stream)
    published = answer["snapshot"]
    if published["state"] == "absent":
        print("snapshot   absent (the publisher has not written one yet)", file=stream)
    elif published["state"] == "unreadable":
        print("snapshot   unreadable: " + str(published.get("detail")), file=stream)
    else:
        # BOTH AGES, because they answer different questions: how old the
        # manager's reading is, and how long since anything was written.
        print("snapshot   %s (observed %.1fs ago, written %.1fs ago)"
              % (published["state"], published["observed_age_seconds"],
                 published["published_age_seconds"]), file=stream)
    jobs = answer["jobs"]
    if jobs["state"] == "observed":
        print("jobs       %d observed (canonical=%s)" % (jobs["count"], jobs["canonical"]),
              file=stream)
    else:
        print("jobs       " + jobs["state"], file=stream)
    manager = answer["processes"][MANAGER]
    if manager.get("serving"):
        print("serving    " + manager["serving"], file=stream)
    _print_runtime_boundary(answer["runtime"], stream)
    if answer["configuration"]["state"] != "configured":
        print("configuration unconfigured: " + answer["configuration"]["detail"],
              file=stream)
    return 0


# -- the publisher ------------------------------------------------------------


def publish_once(root, settings, *, runner=subprocess.run, environ=None):
    """One status document, written atomically.

    ATOMIC because `JOB-VIEWER.md` requires it: a viewer that reads a partially
    written document reports a torn snapshot as the pipeline's state. The
    temporary file is in the same directory so `os.replace` is a rename rather
    than a copy.
    """
    root = Path(root)
    done = runner(_child("manager", [
                   "--store", settings["BATON_V12_JOB_STORE"],
                   "--incarnation", "v12-stack-publisher",
                   "--authority-uuid", settings["BATON_V12_AUTHORITY_UUID"],
                   "status",
                   "--control", settings["BATON_V12_CONTROL_STORE"],
                   "--observe", "tools.stage_execution:observing_factory"]),
                  cwd=str(DISTRIBUTION), env=child_environment(environ),
                  capture_output=True, text=True)
    if done.returncode != 0:
        # [R3]: the publisher is where a configuration that does not compose
        # becomes visible, so its reason is written where `start` can read it.
        print("status refused (returncode %d):\n%s%s"
              % (done.returncode, done.stderr, done.stdout), file=sys.stderr)
        return False
    temporary = snapshot_path(root).with_suffix(".json.tmp")
    temporary.write_text(done.stdout)
    os.replace(temporary, snapshot_path(root))
    return True


def publish(root, *, environ=None, interval=PUBLISH_SECONDS, should_continue=None,
            sleep=time.sleep, runner=subprocess.run):
    settings = configured(environ)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    running = [True]

    def stop_running(*_):
        running[0] = False

    if should_continue is None:
        for number in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(number, stop_running)
            except ValueError:                              # pragma: no cover
                pass
        should_continue = lambda: running[0]
    while should_continue():
        publish_once(root, settings, runner=runner, environ=environ)
        if not should_continue():
            break
        sleep(interval)
    return 0


# -- entry point --------------------------------------------------------------


def instance_settings(place, environ):
    """Everything an instance selector says, in the vocabulary this module reads.

    W183883, OWNER-INSTANCE-DESTINATION-20260916.md: the four exports and the
    global state-root default are superseded as the SELECTION interface. One
    file names the destination, and every store, log and process path is
    derived from it -- so an operator addresses a deployment by saying which one
    they mean, rather than by remembering four variables correctly.

    THE RUNTIME IS VERIFIED BEFORE ANYTHING IS DERIVED. `instance.verify`
    recomputes the whole one-folder manifest, because a distro whose native
    library or frozen schema assets had been replaced would otherwise fail
    inside a child this command had already started.
    """
    from tools import instance

    document = instance.read(place)
    instance.verify(document)
    prepared = dict(environ)
    prepared.update(instance.settings(document))
    return document, prepared


def monitor(root, *, interval, ticks, stream=sys.stdout):
    """The read-only monitor, over the snapshot the PUBLISHER writes.

    W183883: an installed instance must be watchable without the development
    checkout. The recipe used to derive the snapshot path itself, from an
    environment variable, which is a second place for a fact `snapshot_path`
    already owns -- and it could not answer for an instance at all. This runs
    inside whichever form of the command was started, so `<destination>/distro/
    baton-v12-stack monitor --instance ...` and `python3 -m tools.stack monitor`
    watch the same document.

    IT READS AND NOTHING ELSE. Leaving the monitor does not stop scheduling;
    that is `stop`.
    """
    place = snapshot_path(root)
    if not place.exists():
        raise StackRefusal(
            "there is no snapshot at " + str(place) + " yet, so there is "
            "nothing to watch. Start this stack first, or ask it for `status` "
            "to see why it has not published one.")
    from tools import job_viewer

    return job_viewer.main(["--status", str(place), "--interval", str(interval),
                            "--ticks", str(ticks)], stream=stream)


def repository(document, *, stream=sys.stdout):
    """What this instance's repository IS, read and nothing else.

    W183883 review 2026-09-16T14-06-35Z. An installed deployment has a `repo/`
    of its own, and a configured `integration_target` that is the OWNER's
    selection -- a repository this Work may not create, clone or modify. What
    it can do is say, read-only, exactly what is there, so the owner's own
    preparation can be checked before a Job is ever submitted.

    NO REPOSITORY TOOL IS RUN AND NOTHING IS WRITTEN. The layout is read from
    the filesystem and `HEAD` from the file of that name; the exact read-only
    commands for the rest are in OPERATOR-INDEPENDENT-REPOSITORY.md.
    """
    from tools import instance as instances

    places = instances.layout(document["destination"])
    try:
        configured = json.loads(Path(document["deployment"]).read_bytes())
    except (OSError, ValueError) as failure:
        print("refused: this instance's deployment document at "
              + document["deployment"] + " could not be read ("
              + type(failure).__name__ + "), so nothing was derived from it",
              file=stream)
        return 2

    reference = configured.get("integration_target_reference")
    # SORTED AFTER THE NONES ARE GONE: a `/1` document derives its single
    # binding and carries no `job_bindings`, so one side of this is routinely
    # absent and sorting a set holding None raises out of a reporter.
    named = {binding.get("line_declared_base")
             for binding in configured.get("job_bindings", [])
             if isinstance(binding, dict)}
    named.add(configured.get("line_declared_base"))
    bases = sorted(one for one in named if isinstance(one, str) and one)
    workspace = _repository_place(configured.get("integration_workspace"),
                                  places)
    answers = [
        ("workspace", workspace),
        ("target", _repository_place(configured.get("integration_target"),
                                     places, owned=False)),
        ("reference", reference if reference is not None
         else "not configured -- a reconciled result is imported at exactly "
              "one explicitly configured reference"),
        ("declared bases", ", ".join(bases) or "none configured"),
    ]
    for name, said in answers:
        print("%-14s %s" % (name, said), file=stream)
    # WHAT RECONCILIATION WILL DO WITH IT, said here rather than discovered
    # when a result is ready to import. `reconciliation._prove_isolation` asks
    # the profile to resolve the workspace's own repository identity -- its
    # common directory -- and refuses a workspace that is not a repository, or
    # that is the same repository as the target or as a producer's line or
    # source. An empty directory is none of those things.
    if "a repository" not in workspace:
        print("\nthis workspace is not a repository yet, so a reconciled "
              "result could not be prepared in it: isolation is proved before "
              "anything is written. OPERATOR-INDEPENDENT-REPOSITORY.md has the "
              "owner's commands for preparing one that is separate from the "
              "target and from every producer's line.", file=stream)
    print("\nnothing was run and nothing was written; preparing the target is "
          "the owner's, and the read-only commands to check it are in "
          "OPERATOR-INDEPENDENT-REPOSITORY.md", file=stream)
    return 0


def _repository_place(named, places, *, owned=True):
    """One repository path, described from the filesystem alone."""
    if named is None:
        return ("not configured -- `just bootstrap` derives "
                + places["repository"] + " when the input does not name one"
                if owned else "not configured")
    if type(named) is not str or not named:
        return "configured as " + repr(named) + ", which is not a path"
    said = [named]
    inside = os.path.realpath(places["destination"])
    held = os.path.realpath(named)
    within = held == inside or held.startswith(inside.rstrip("/") + "/")
    said.append("inside this instance" if within else "outside this instance")
    if not os.path.exists(named):
        said.append("ABSENT")
        return " -- ".join(said)
    if not os.path.isdir(named):
        said.append("not a directory")
        return " -- ".join(said)
    entries = sorted(os.listdir(named))
    if not entries:
        said.append("empty")
        return " -- ".join(said)
    # A WORK TREE CARRIES `.git`; A BARE REPOSITORY IS THE LAYOUT ITSELF.
    # Neither is proved by a name, so both are read from what is on disk.
    marker = os.path.join(named, ".git")
    root = marker if os.path.exists(marker) else named
    layout = all(os.path.exists(os.path.join(root, one))
                 for one in ("HEAD", "objects", "refs"))
    if not layout:
        said.append(str(len(entries)) + " entries, no repository layout")
        return " -- ".join(said)
    said.append("a repository" + (" (work tree)" if root is marker else " (bare)"))
    try:
        head = Path(root, "HEAD").read_text().strip()
    except OSError as failure:
        said.append("HEAD unreadable (" + type(failure).__name__ + ")")
        return " -- ".join(said)
    said.append("HEAD " + head)
    if head.startswith("ref: "):
        pointed = Path(root, head[5:].strip())
        if pointed.exists():
            try:
                said.append(pointed.read_text().strip()[:40])
            except OSError:                                  # pragma: no cover
                pass
        else:
            said.append("that reference has no file here (packed or unborn)")
    return " -- ".join(said)


def main(argv=None, *, stream=sys.stdout, environ=None):
    parser = argparse.ArgumentParser(
        prog="stack", description="Lifecycle for the persistent v12 stack.")
    parser.add_argument("--instance", default=None,
                        help="the instance.json a bootstrap emitted; it names "
                             "the destination and every path is derived from it")
    parser.add_argument("--root", default=None,
                        help="the external state root; defaults to "
                             + ROOT_ENV + " or the XDG state directory")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "stop", "status", "publish"):
        commands.add_parser(name)
    commands.add_parser("repository")
    watching = commands.add_parser("monitor")
    watching.add_argument("--interval", type=float, default=5.0,
                          help="seconds between refreshes")
    watching.add_argument("--ticks", type=int, default=1000000,
                          help="bounded refreshes; Ctrl-C is the way out")
    taken = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    try:
        if taken.instance:
            from tools import instance as instances

            document, environ = instance_settings(taken.instance, environ)
            root = Path(document["state"])
            Path(document["logs"]).mkdir(parents=True, exist_ok=True)
        else:
            root = Path(taken.root) if taken.root else state_root(environ)
    except Exception as refusal:                             # noqa: BLE001
        from tools import instance as instances

        if not isinstance(refusal, instances.InstanceRefusal):
            raise
        print("refused: " + str(refusal), file=stream)
        return 2
    try:
        if taken.command == "start":
            return start(root, environ, stream=stream)
        if taken.command == "stop":
            return stop(root, stream=stream)
        if taken.command == "status":
            return status(root, stream=stream, environ=environ)
        if taken.command == "repository":
            if not taken.instance:
                print("refused: `repository` reads an instance's own "
                      "configuration, so it needs --instance", file=stream)
                return 2
            return repository(document, stream=stream)
        if taken.command == "monitor":
            return monitor(root, interval=taken.interval, ticks=taken.ticks,
                           stream=stream)
        return publish(root, environ=environ)
    except StackRefusal as refusal:
        print("refused: " + str(refusal), file=stream)
        return 2


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
