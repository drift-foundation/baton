"""The ONE command a deployed v12 stack is, frozen into a bundle. W183883.

OWNER-PYINSTALLER-20260916.md selects PyInstaller one-folder: the application,
the Python interpreter, the dependency libraries and the package resources ship
together, so a running deployment does not read the development checkout and
work can continue in that checkout while Jobs run.

WHY THIS FILE EXISTS AT ALL. The stack's children are started as
`sys.executable -m tools.X`. In a frozen build `sys.executable` is THIS
application, not an interpreter, and `-m` means nothing to it -- so a bundle
whose supervisor kept that dispatch would start copies of itself with operands
it does not understand. The bundled command therefore exposes each child as a
SUBCOMMAND of itself, and `tools/stack.py` dispatches through
`bundled_argv` when it is frozen.

RUNNING FROM SOURCE IS THE SAME PROGRAM. Nothing here is conditional on being
frozen except where the argv must be: `python3 -m tools.stack_command serve ...`
and `<distro>/baton-v12-stack serve ...` reach the same code. That is what makes
the bundle checkable without a second implementation to keep in step.
"""
import argparse
import os
from pathlib import Path
import sys

# The name the bundle is built under. `packaging/stack.spec` uses it, the
# instance records it, and `bundled_argv` looks for it beside the interpreter.
COMMAND = "baton-v12-stack"

# Every child the supervisor starts, and the module that owns each one. A
# frozen build cannot resolve `-m`, so this is the table that replaces it.
# The children the supervisor starts. `manager` is `job_manager`, whose OWN
# verb (`serve` or `status`) is one of its operands -- naming the subcommand
# after one of those verbs would have made the other one read as a lie.
CHILDREN = ("manager", "publish", "view", "logs")


def frozen():
    """Is this process the bundled command rather than an interpreter?

    PyInstaller sets `sys.frozen` and `sys._MEIPASS`; both are read rather than
    one, because a bundle that set only the first would be some other tool's.
    """
    return bool(getattr(sys, "frozen", False)) and hasattr(sys, "_MEIPASS")


def executable():
    """The command this process IS, when it is the bundled one."""
    return os.path.realpath(sys.executable)


def bundled_argv(subcommand, operands):
    """How to start one child, from whichever form this process is running in.

    THE ONE PLACE THE TWO FORMS DIFFER. Frozen, the child is this executable
    with a subcommand. From source, it is this interpreter with `-m`. Callers
    ask for a child by name and never decide which world they are in.
    """
    if subcommand not in COMMANDS:
        raise ValueError("no bundled subcommand named " + repr(subcommand))
    if frozen():
        return [executable(), subcommand] + list(operands)
    return [sys.executable or "python3", "-m", "tools.stack_command",
            subcommand] + list(operands)


def resources():
    """Where the bundle's own read-only material lives.

    `sys._MEIPASS` for a one-folder build is the folder itself. From source it
    is the distribution directory, so a caller that needs a packaged asset asks
    here instead of computing a path relative to a module file -- which is what
    makes checkout-relative discovery impossible to leave behind by accident.
    """
    if frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _manager(operands):
    from tools import job_manager
    return job_manager.main(operands)


def _view(operands):
    from tools import job_viewer
    return job_viewer.main(operands)


def _logs(operands):
    """W198667: one attempt's retained raw output, from the DEPLOYED command.

    Review 2026-09-18T02-31-51Z [5]: the module advertised a
    `baton-attempt-logs` program that nothing installed, and it lives outside
    the packaged `src` tree so a console script could not reach it either. An
    operator reading evidence after an incident has the DEPLOYED bundle, not a
    checkout -- so the supported invocation is this bundle's own subcommand,
    which is the same surface `status` and `monitor` are reached by.
    """
    from tools import attempt_logs_command
    return attempt_logs_command.main(operands)


def _stack(subcommand):
    """The four `tools.stack` verbs, which take their verb LAST.

    `stack.main` parses `--root` as a top-level operand ahead of the
    subcommand -- a fact an earlier review established the hard way, when the
    reversed order was refused by argparse and the publisher exited at once.
    So the verb is appended rather than prepended, once, here.
    """
    def running(operands):
        from tools import stack

        operands = list(operands)
        head = []
        # AND A VERB'S OWN OPTIONS COME AFTER IT. `monitor --interval` is the
        # monitor's, and argparse reads a subcommand's options only after the
        # subcommand -- so the instance selection (top-level) is split from
        # everything else rather than the whole list being appended to.
        while operands:
            if operands[0] in ("--instance", "--root") and len(operands) > 1:
                head += operands[:2]
                operands = operands[2:]
                continue
            if operands[0].startswith(("--instance=", "--root=")):
                head.append(operands[0])
                operands = operands[1:]
                continue
            break
        return stack.main(head + [subcommand] + operands)
    return running


def _bootstrap(operands):
    from tools import bootstrap
    return bootstrap.main(operands)


def _identity(operands):
    """What this build IS, so an instance can record it rather than assume it.

    A HOST-SPECIFIC DISTRIBUTION, said out loud. One-folder bundles are built
    for the platform they are built on; nothing here claims portability, and
    the identity is what an instance keeps so a later start can tell whether it
    is looking at the same distro.
    """
    import hashlib
    import json
    import platform

    from baton_v12 import version as application
    from tools import build_stamp

    said = {"command": COMMAND, "frozen": frozen(),
            "version": application.VERSION,
            "build_stamp": build_stamp.stamped(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine()}
    # THE PACKAGED RESOURCES, PROVED RATHER THAN ASSUMED. `contracts.frozen`
    # reads its schema assets from disk at IMPORT time, so a bundle missing
    # them fails here rather than silently refusing every document later. The
    # native validator is reported the same way: `rpds` has no pure-Python
    # fallback, so "it imported" is the whole question.
    try:
        from baton_v12.contracts import frozen as assets
        said["schema_assets"] = {
            "worker-control-1.0": len(assets.WORKER_CONTROL_BYTES),
            "agent-session-1.0": len(assets.AGENT_SESSION_BYTES)}
    except Exception as failure:                             # noqa: BLE001
        said["schema_assets"] = "%s: %s" % (type(failure).__name__, failure)
    try:
        # THE EXTENSION, NOT THE PACKAGE. A one-folder build freezes pure-Python
        # modules into the archive, so `rpds.__file__` names an `__init__.py`
        # that does not exist on disk -- the first real install refused this
        # bundle for reporting a validator that is not one of the files it
        # binds, which was true of the path and false of the bundle. What has
        # to have travelled is the compiled extension, and it is on disk.
        from rpds import rpds as native
        said["native_rpds"] = getattr(native, "__file__", "imported")
    except Exception as failure:                             # noqa: BLE001
        said["native_rpds"] = "%s: %s" % (type(failure).__name__, failure)
    if frozen():
        place = Path(executable())
        said["executable"] = str(place)
        said["resources"] = str(resources())
        try:
            said["sha256"] = hashlib.sha256(place.read_bytes()).hexdigest()
        except OSError as failure:
            said["sha256"] = None
            said["detail"] = "%s: %s" % (type(failure).__name__, failure)
    print(json.dumps(said, indent=2, sort_keys=True))
    return 0


COMMANDS = {
    "bootstrap": _bootstrap,
    "start": _stack("start"), "stop": _stack("stop"),
    "status": _stack("status"), "publish": _stack("publish"),
    # THE INSTALLED MONITOR. `view` is the raw viewer over a named document;
    # `monitor` derives this instance's own snapshot, so an operator watching a
    # deployment names the instance rather than a path inside it.
    "monitor": _stack("monitor"),
    # READ-ONLY, and part of the installed command because the question --
    # "what is this deployment's repository, actually?" -- is asked of a
    # deployment, from wherever it is installed.
    "repository": _stack("repository"),
    "manager": _manager, "view": _view, "logs": _logs,
    "identity": _identity,
}


def _version():
    """What this build IS, in one line, before anything else can fail.

    OWNER-VERSION-STAMP-20260916.md: `--version` must answer with the
    development checkout and the repository tool BOTH unavailable, without
    opening an instance store, reading a credential or starting a runtime. It
    reads one captured file beside the executable and prints a string.
    """
    from baton_v12 import version as application
    from tools import build_stamp

    print(application.stated(build_stamp.stamped()))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # BEFORE THE PARSER, because `--version` is not one of the subcommands and
    # must not be reachable only by arranging the rest of a command line
    # correctly.
    if argv and argv[0] in ("-V", "--version"):
        return _version()
    parser = argparse.ArgumentParser(
        prog=COMMAND, add_help=False,
        description="The deployed v12 stack: one command, several subcommands.")
    parser.add_argument("subcommand", nargs="?", choices=sorted(COMMANDS))
    if not argv or argv[0] in ("-h", "--help"):
        parser.print_help()
        print("\nEvery operand after the subcommand is that subcommand's own.",
              file=sys.stdout)
        print("--version (-V) says what this build is and needs nothing else.",
              file=sys.stdout)
        return 0
    subcommand, operands = argv[0], argv[1:]
    if subcommand not in COMMANDS:
        print("refused: no subcommand named " + repr(subcommand)
              + "; this command serves " + ", ".join(sorted(COMMANDS)),
              file=sys.stderr)
        return 2
    return COMMANDS[subcommand](operands)


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
