#!/usr/bin/python3
"""One command, run under one bound, with every descendant accounted for.

W385695 C2 (review 2026-11-24T01-52-00Z). The owner-selected rule is that EACH
reviewer verification or test command has its own bound inside what remains of
the review invocation. A prompt cannot enforce that and neither can a process
group: a command's child that starts its own session leaves the group, outlives
its parent, and an empty group then says nothing about it.

THIS PROGRAM IS THE ENFORCEMENT, and it is reached two ways, both of which the
adapter chooses and neither of which the provider does:

  * the provider CLI is started with this file as its `CLAUDE_CODE_SHELL_PREFIX`,
    so the CLI hands EVERY shell-tool command to it as one argument -- the
    foreground ones, the ones it moves to the background, and the ones the
    model asks to run in the background;
  * the adapter runs its own required check, and the provider itself, through
    `--exec`.

WHAT IT DOES. It makes itself the child subreaper, so a descendant that
detaches is re-parented HERE rather than to the container's init. It runs the
command, ends it at the earlier of its bound and the absolute invocation
deadline, and then -- whatever the ending -- kills every process that still
descends from it and waits until none is left, within a stated grace. It
writes a start record before the command exists and a finish record after its
descendants are gone, so a supervisor that was itself killed leaves a start
with no finish, which the adapter reads as unfinished rather than as success.

WHAT IT DOES NOT CLAIM. It runs as the same user as the command, so a command
that deliberately attacks its own supervisor (kills it, rewrites the ledger)
is not prevented here; it is caught by the start-without-finish record, by the
outer supervisor the provider runs under, by the invocation deadline and by
the container's own cessation. This is a bound on work, not a sandbox.

Standard library only: it runs in the worker image beside the adapter.
"""

import json
import os
import signal
import sys
import time

SCHEMA = "baton.bounded-command/1"
# HOW LONG ENDING THE DESCENDANTS MAY TAKE after the command is over or its
# bound has passed. It is counted: the adapter hands every supervisor an
# absolute deadline that is already this much short of the invocation's.
END_GRACE_SECONDS = 5.0
SHELL = "/bin/bash"
PR_SET_CHILD_SUBREAPER = 36
# EXIT STATUSES THIS PROGRAM ITSELF ANSWERS WITH. 124 is the conventional
# "timed out"; 125 is "this supervisor could not do its own job", and a
# command is never run in that case.
TIMED_OUT, UNABLE, NOT_STARTED = 124, 125, 127


def descendants(root):
    """Every live, non-zombie process whose parent chain reaches `root`."""
    parents = {}
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/stat", "rb") as held:
                raw = held.read()
        except OSError:
            continue
        # THE COMMAND NAME MAY CONTAIN ANYTHING, including `)` and spaces; the
        # fields after the LAST `)` are the ones with a fixed shape.
        rest = raw[raw.rindex(b")") + 2:].split()
        if rest[0] == b"Z":
            continue
        parents[int(name)] = int(rest[1])
    found = []
    for pid in parents:
        seen, at = set(), pid
        while at in parents and at not in seen:
            seen.add(at)
            at = parents[at]
            if at == root:
                found.append(pid)
                break
    return found


def end_descendants(root, grace=END_GRACE_SECONDS):
    """Kill everything descending from `root` until nothing does.

    Returns `(ended, gone)`: how many distinct processes were signalled, and
    whether a scan found NONE left within the grace. `gone` is an observation
    of the process table, not an inference from a group or a wait status.
    """
    ended, deadline = set(), time.monotonic() + grace
    while True:
        live = descendants(root)
        for pid in live:
            ended.add(pid)
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        while True:
            try:
                if os.waitpid(-1, os.WNOHANG)[0] == 0:
                    break
            except ChildProcessError:
                break
        if not live:
            return len(ended), True
        if time.monotonic() >= deadline:
            return len(ended), False
        time.sleep(0.01)


def _written(ledger, name, document):
    place = os.path.join(ledger, name)
    handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        json.dump(document, out, sort_keys=True)


def supervise(argv, *, label, seconds, deadline, ledger):
    """Run `argv` under the bound and return this program's exit status."""
    me = os.getpid()
    began = time.monotonic()
    allowed = float(seconds)
    if deadline is not None:
        allowed = min(allowed, deadline - began)
    name = f"{label}-{me}-{time.monotonic_ns()}"
    record = {"schema": SCHEMA, "label": label, "seconds_bound": seconds,
              "outcome": None, "status": None, "seconds": None,
              "descendants_ended": 0, "descendants_gone": None}
    try:
        import ctypes

        if ctypes.CDLL(None, use_errno=True).prctl(
                PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
            raise OSError("prctl refused")
        _written(ledger, name + ".started", {"schema": SCHEMA, "label": label})
    except Exception:
        # NOTHING RUNS UNSUPERVISED. A supervisor that cannot adopt
        # descendants or cannot leave its start record refuses the command.
        sys.stderr.write("baton: this command was not run: its supervisor "
                         "could not be established\n")
        return UNABLE
    if allowed <= 0:
        _written(ledger, name + ".json",
                 dict(record, outcome="not-run", seconds=0.0,
                      descendants_gone=True))
        sys.stderr.write("baton: this command was not run: no time remained "
                         "of the review invocation\n")
        return TIMED_OUT
    stop = []
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(number, lambda received, _frame: stop.append(received))
    try:
        child = os.fork()
        if child == 0:
            try:
                for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                    signal.signal(number, signal.SIG_DFL)
                os.execvp(argv[0], argv)
            except BaseException:
                os._exit(NOT_STARTED)
    except OSError:
        _written(ledger, name + ".json",
                 dict(record, outcome="not-started", seconds=0.0,
                      descendants_gone=True))
        return NOT_STARTED
    status = None
    while True:
        try:
            pid, raw = os.waitpid(child, os.WNOHANG)
        except ChildProcessError:
            pid, raw = child, 0
        if pid:
            status = os.waitstatus_to_exitcode(raw)
            break
        if stop:
            record["outcome"] = "signalled"
            break
        if time.monotonic() - began >= allowed:
            record["outcome"] = "timed-out"
            break
        time.sleep(0.02)
    ended, gone = end_descendants(me)
    if record["outcome"] is None:
        record["outcome"] = "exited"
    record.update(status=status, seconds=round(time.monotonic() - began, 3),
                  descendants_ended=ended, descendants_gone=gone)
    _written(ledger, name + ".json", record)
    if record["outcome"] == "timed-out":
        sys.stderr.write(f"baton: this command was ended at its "
                         f"{round(allowed)}s bound\n")
        return TIMED_OUT
    if record["outcome"] == "signalled":
        return 128 + stop[0]
    return status if status >= 0 else 128 - status


def account(ledger):
    """What the supervisors in `ledger` recorded, read by the adapter.

    A start with no finish is UNFINISHED: its supervisor did not get to end
    and observe its descendants, so nothing is known about them from here.
    """
    started, finished = set(), {}
    for name in sorted(os.listdir(ledger)):
        stem, _dot, kind = name.rpartition(".")
        if kind == "started":
            started.add(stem)
        elif kind == "json":
            try:
                handle = os.open(os.path.join(ledger, name),
                                 os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(handle, "rb") as held:
                    document = json.loads(held.read(65536).decode("utf-8"))
            except (OSError, ValueError):
                document = None
            finished[stem] = document if type(document) is dict else None
    return {stem: finished.get(stem) for stem in sorted(started | set(finished))}


def main(arguments):
    if arguments[:1] == ["--exec"]:
        try:
            cut = arguments.index("--")
            options = dict(zip(arguments[1:cut:2], arguments[2:cut:2]))
            argv = arguments[cut + 1:]
            seconds = int(options["--seconds"])
            deadline = (float(options["--deadline"])
                        if "--deadline" in options else None)
            label, ledger = options["--label"], options["--ledger"]
            if not argv or set(options) - {"--seconds", "--deadline",
                                           "--label", "--ledger"}:
                raise ValueError(arguments)
        except (KeyError, ValueError):
            return UNABLE
        return supervise(argv, label=label, seconds=seconds,
                         deadline=deadline, ledger=ledger)
    # THE SHELL PREFIX FORM: exactly one argument, the whole command string
    # the CLI composed. The bound and ledger come from the environment the
    # adapter composed for the CLI; a missing or unreadable one refuses.
    if len(arguments) != 1:
        return UNABLE
    try:
        seconds = int(os.environ["BATON_COMMAND_SECONDS"])
        deadline = float(os.environ["BATON_COMMAND_DEADLINE"])
        ledger = os.environ["BATON_COMMAND_LEDGER"]
    except (KeyError, ValueError):
        sys.stderr.write("baton: this command was not run: its bound was not "
                         "delivered\n")
        return UNABLE
    return supervise([SHELL, "-c", arguments[0]], label="tool",
                     seconds=seconds, deadline=deadline, ledger=ledger)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
