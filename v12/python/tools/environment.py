"""The v12 stack's prepared Python environment: create it, validate it, name it.

W183883. The owner's requirement: "we should use a venv with python3", and
"it should be a separate just cmd". So `just setup` under `v12/` prepares a
DEDICATED virtual environment with the locked dependencies, and
start/stop/status/monitor USE that environment's interpreter and never install
anything. A command that installs as a side effect of starting a scheduler is a
command an operator cannot reason about.

NO ACTIVATION. Nothing here asks an operator to remember `source .../activate`;
the recipes resolve the interpreter's absolute path and run it directly, which
is also what makes the stack's own children inherit it -- `tools/stack.py`
spawns with `sys.executable`, so whichever interpreter runs the launcher is the
one the manager and publisher run under.

AND NO AMBIENT FALLBACK. A recipe that quietly used the system `python3` when
the prepared environment was missing would run the scheduler against whatever
`jsonschema` the machine happened to have -- which is exactly the drift
`v12/python/justfile` already records finding in its own source stage, where a
green run resolved 4.19.2 against a lock pinning 4.26.0. `interpreter` refuses
and names `just setup` instead.

THE ENVIRONMENT IS NOT IN THE CHECKOUT. Item 4bp already ruled that downloaded
distributions do not belong in Git; a populated environment is the same thing
with more steps. It lives under the operator's state directory beside the
stack's own state root, and `BATON_V12_VENV` moves it.

REPEAT SETUP IS SAFE AND NEVER DESTRUCTIVE. It re-verifies an environment it
created and reinstalls when the lock has moved. Anything else at that path --
an environment this did not create, or one whose interpreter is too old -- is
REFUSED, with its path named, and is never deleted: this tool did not put it
there and a launcher that removes directories it does not own is the failure
`state-clean` was already corrected for.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

SCHEMA = "baton.v12.venv/1"
VENV_ENV = "BATON_V12_VENV"
# Where the deployment-setup checks put their disk-backed material, and the
# default when nobody says. They need REAL STORAGE OUTSIDE THE CHECKOUT: the
# accepted configuration validator refuses a configured mutable root inside the
# working tree, and the workspace boundary refuses one on a memory filesystem.
TEST_ROOT_ENV = "BATON_V12_STACK_TEST_ROOT"
DEFAULT_TEST_ROOT = "/var/tmp"
LOCK = "requirements.lock"
MARKER = "baton-v12-venv.json"

# This distribution, and the two files that define what the environment must be.
DISTRIBUTION = Path(__file__).resolve().parent.parent
PROJECT = DISTRIBUTION / "pyproject.toml"
LOCK_PATH = DISTRIBUTION / LOCK

# `requires-python` is read by REGEX rather than with `tomllib`, deliberately.
# This module runs under whatever `python3` an operator has, and that is the
# very thing it exists to check -- so it must be able to REFUSE an interpreter
# too old to import the parser it would have used to find out.
_REQUIRES = re.compile(r'^\s*requires-python\s*=\s*"[><=~^!\s]*(\d+)\.(\d+)',
                       re.MULTILINE)


class SetupRefusal(Exception):
    """An operator-facing refusal. Its text is the whole message."""


def venv_path(environ=None):
    environ = os.environ if environ is None else environ
    chosen = environ.get(VENV_ENV)
    if chosen:
        return Path(chosen)
    base = environ.get("XDG_STATE_HOME") or os.path.join(
        environ.get("HOME", "/tmp"), ".local", "state")
    return Path(base) / "baton-v12-venv"


def interpreter_path(root):
    return Path(root) / "bin" / "python"


def marker_path(root):
    return Path(root) / MARKER


def required_python():
    """The minimum this distribution declares, read from its own pyproject."""
    try:
        text = PROJECT.read_text(encoding="utf-8")
    except OSError as failure:
        raise SetupRefusal("cannot read " + str(PROJECT) + ": " + str(failure))
    found = _REQUIRES.search(text)
    if not found:
        raise SetupRefusal(
            str(PROJECT) + " does not declare requires-python, so there is no "
            "minimum to hold an interpreter to. This tool will not guess one.")
    return int(found.group(1)), int(found.group(2))


def lock_digest():
    """What the environment was installed FROM, so a moved lock is noticed."""
    try:
        return hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest()
    except OSError as failure:
        raise SetupRefusal("cannot read " + str(LOCK_PATH) + ": " + str(failure))


def _version_of(executable):
    """(major, minor, micro) for an interpreter, or None if it will not say."""
    try:
        done = subprocess.run(
            [str(executable), "-c",
             "import sys; print('%d %d %d' % sys.version_info[:3])"],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    try:
        return tuple(int(one) for one in done.stdout.split())
    except ValueError:
        return None


def read_marker(root):
    """Our own record of this environment, or None, or unreadable.

    POSITIVE OWNERSHIP, for `state-clean`'s reason: a path's shape cannot prove
    a directory is ours. Only the marker THIS tool wrote, naming this exact
    path, says so -- and without it nothing here will install into a directory
    or refuse to leave one alone.
    """
    try:
        value = json.loads(marker_path(root).read_bytes())
    except FileNotFoundError:
        return None
    except (ValueError, OSError):
        return {"unreadable": True}
    if type(value) is not dict or value.get("schema") != SCHEMA:
        return {"unreadable": True}
    if value.get("path") != str(Path(root).resolve()):
        # A copied or moved environment: its interpreter's shebangs and its
        # `pyvenv.cfg` still name where it was BUILT, so this is not simply a
        # relocatable directory.
        return {"unreadable": True, "names": value.get("path")}
    return value


def observe(root=None, environ=None):
    """The whole machine-readable answer, without changing anything."""
    root = venv_path(environ) if root is None else Path(root)
    answer = {"schema": SCHEMA, "path": str(root),
              "interpreter": str(interpreter_path(root)),
              "lock": str(LOCK_PATH), "setup_command": "just setup"}
    try:
        answer["requires_python"] = "%d.%d" % required_python()
        answer["lock_sha256"] = lock_digest()
    except SetupRefusal as refusal:
        answer["state"] = "unusable"
        answer["detail"] = str(refusal)
        return answer
    if not root.exists():
        answer["state"] = "absent"
        return answer
    marker = read_marker(root)
    if marker is None or marker.get("unreadable"):
        answer["state"] = "foreign"
        answer["detail"] = (
            "there is something at " + str(root) + " that this setup did not "
            "create" + ("" if not (marker or {}).get("names")
                        else ", or that was built at "
                             + str(marker["names"]) + " and moved here")
            + ". It will not be installed into and it will NOT be deleted.")
        return answer
    version = _version_of(interpreter_path(root))
    if version is None:
        answer["state"] = "broken"
        answer["detail"] = ("the interpreter at " + str(interpreter_path(root))
                            + " does not run")
        return answer
    answer["python"] = "%d.%d.%d" % version
    if version[:2] < required_python():
        answer["state"] = "incompatible"
        answer["detail"] = (
            "the environment at " + str(root) + " is Python %d.%d.%d and this "
            "distribution requires %d.%d or newer" % (version + required_python()))
        return answer
    if not marker.get("installed"):
        # REVIEW 2026-09-16T10-39-48Z [E2]. Ownership used to be published only
        # AFTER a successful install, so a first install that failed left a
        # directory this tool had created and could no longer recognise: the
        # next setup called its own partial environment foreign and told the
        # operator to delete it, and running the printed pip command by hand
        # could not write the missing marker either. So the marker is written
        # BEFORE the install and says so, and this state is neither ready nor
        # foreign -- it is ours, and it is resumable.
        answer["state"] = "incomplete"
        answer["detail"] = ("this environment was created by this setup but its "
                            "locked dependencies have not been installed yet; "
                            "`just setup` resumes it without recreating it")
        return answer
    if marker.get("lock_sha256") != answer["lock_sha256"]:
        answer["state"] = "stale"
        answer["detail"] = ("this environment was installed from a different "
                            + LOCK + "; `just setup` brings it up to date")
        return answer
    answer["state"] = "ready"
    return answer


def test_root(chosen=None, environ=None, *, stream=sys.stdout):
    """Which disk-backed root the deployment-setup checks should use.

    THE PRECEDENCE IS THE OPERATOR'S OWN ORDER, and REVIEW 2026-09-16T11-53-00Z
    [I1] is why it is stated here rather than in the recipe: the recipe assigned
    its default over an exported `BATON_V12_STACK_TEST_ROOT`, so an operator who
    had selected a root got a different one and was never told. A `just` default
    cannot read the environment, so a recipe that tried to express this would
    have had to reimplement it in shell -- and this is the same helper the
    recipes already ask for the interpreter.

      an explicit operand, because saying it here and now is the most specific
        thing an operator can do;
      then this deployment's own variable, because exporting it is how they say
        it once;
      then /var/tmp.
    """
    environ = os.environ if environ is None else environ
    selected = (chosen or "").strip() or environ.get(TEST_ROOT_ENV, "").strip() \
        or DEFAULT_TEST_ROOT
    print(selected, file=stream)
    return 0


def interpreter(root=None, environ=None, *, stream=sys.stdout):
    """The prepared interpreter's path, or a refusal naming `just setup`."""
    answer = observe(root, environ)
    if answer["state"] != "ready":
        raise SetupRefusal(
            "the v12 Python environment at " + answer["path"] + " is "
            + answer["state"] + ": " + answer.get("detail", "it has not been "
            "prepared yet") + ". Run `just setup` from v12/ first. Nothing "
            "here installs anything as a side effect of starting, stopping or "
            "watching the stack.")
    print(answer["interpreter"], file=stream)
    return 0


def _create(root, chosen, *, runner=subprocess.run):
    version = _version_of(chosen)
    if version is None:
        raise SetupRefusal(
            "there is no working Python 3 interpreter at " + str(chosen)
            + ". Name one with `just setup /path/to/python3`.")
    if version[:2] < required_python():
        raise SetupRefusal(
            str(chosen) + " is Python %d.%d.%d and this distribution requires "
            "%d.%d or newer. Name a newer one with "
            "`just setup /path/to/python3`; nothing is installed."
            % (version + required_python()))
    done = runner([str(chosen), "-m", "venv", str(root)],
                  capture_output=True, text=True)
    if done.returncode != 0:
        raise SetupRefusal("could not create an environment at " + str(root)
                           + ":\n" + done.stderr + done.stdout)
    return version


def _install(root, *, runner=subprocess.run):
    """The locked dependencies, WITH THEIR HASHES ENFORCED.

    `--require-hashes` is what makes this a locked build rather than a
    resolution: pip refuses any artifact whose SHA-256 is not the one
    `requirements.lock` pins, wherever the index found it.
    `--ignore-installed` so every pin is actually fetched and verified rather
    than skipped as already satisfied.
    """
    done = runner([str(Path(root) / "bin" / "pip"), "install", "--no-cache-dir",
                   "--disable-pip-version-check", "--require-hashes",
                   "--ignore-installed", "-r", str(LOCK_PATH)],
                  capture_output=True, text=True)
    if done.returncode != 0:
        raise SetupRefusal(
            "the locked dependency install refused. Nothing was deleted. This "
            "is the exact command, so it can be run wherever the artifacts are "
            "reachable:\n\n    " + str(Path(root) / "bin" / "pip")
            + " install --no-cache-dir --disable-pip-version-check "
              "--require-hashes --ignore-installed -r " + str(LOCK_PATH)
            + "\n\npip said:\n" + done.stderr + done.stdout)
    return done


def _publish(root, version, *, installed, now=None):
    """Record what this setup owns here, and how far it has got."""
    marker_path(root).write_text(json.dumps(
        {"schema": SCHEMA, "path": str(Path(root).resolve()),
         "python": "%d.%d.%d" % version, "lock_sha256": lock_digest(),
         "lock": str(LOCK_PATH), "installed": bool(installed),
         "prepared_at": time.time() if now is None else now},
        indent=2, sort_keys=True) + "\n")


def setup(root=None, environ=None, *, stream=sys.stdout, chosen="python3",
          runner=subprocess.run, now=None):
    root = venv_path(environ) if root is None else Path(root)
    answer = observe(root, environ)
    if answer["state"] in ("foreign", "incompatible", "broken", "unusable"):
        # NEVER DESTRUCTIVE. The operator is told exactly what is in the way and
        # decides what happens to it.
        raise SetupRefusal(
            answer.get("detail", answer["state"]) + " Remove it yourself if "
            "that is what you want, or point " + VENV_ENV + " at another path. "
            "This setup will not delete a directory it did not create.")
    if answer["state"] == "incomplete":
        print("resuming an interrupted setup at " + answer["path"], file=stream)
    if answer["state"] == "ready":
        print("already prepared: " + answer["path"], file=stream)
        print("interpreter: " + answer["interpreter"], file=stream)
        return 0
    if answer["state"] == "absent":
        Path(root).parent.mkdir(parents=True, exist_ok=True)
        version = _create(root, chosen, runner=runner)
        # CLAIMED BEFORE IT IS FINISHED [E2]. This directory is ours from the
        # moment it exists, and saying so is what makes a failed install
        # resumable instead of permanently foreign.
        _publish(root, version, installed=False, now=now)
    else:                                   # "incomplete" or "stale"
        version = _version_of(interpreter_path(root))
    _install(root, runner=runner)
    # AND READY ONLY NOW, after the locked install actually succeeded.
    _publish(root, version, installed=True, now=now)
    print("prepared: " + str(root), file=stream)
    print("interpreter: " + str(interpreter_path(root)), file=stream)
    print("locked dependencies installed with their hashes enforced, from "
          + str(LOCK_PATH), file=stream)
    print("the stack's own runtime state is untouched; `just start` uses this "
          "interpreter and installs nothing", file=stream)
    return 0


def status(root=None, environ=None, *, stream=sys.stdout):
    answer = observe(root, environ)
    print("environment %s" % answer["state"], file=stream)
    print("path        " + answer["path"], file=stream)
    print("interpreter " + answer["interpreter"], file=stream)
    if answer.get("python"):
        print("python      " + answer["python"]
              + " (requires %s or newer)" % answer.get("requires_python"),
              file=stream)
    if answer.get("detail"):
        print("detail      " + answer["detail"], file=stream)
    if answer["state"] != "ready":
        print("run `just setup` from v12/", file=stream)
    return 0


def main(argv=None, *, stream=sys.stdout, environ=None):
    parser = argparse.ArgumentParser(
        prog="environment",
        description="Prepare and name the v12 stack's Python environment.")
    parser.add_argument("--root", default=None,
                        help="the environment's path; defaults to " + VENV_ENV
                             + " or the XDG state directory")
    parser.add_argument("--python", default="python3",
                        help="the interpreter to build the environment WITH")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("setup", "interpreter", "status"):
        commands.add_parser(name)
    rooted = commands.add_parser("test-root")
    rooted.add_argument("--chosen", default="",
                        help="an explicit root, which wins over " + TEST_ROOT_ENV)
    taken = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    root = Path(taken.root) if taken.root else None
    try:
        if taken.command == "setup":
            return setup(root, environ, stream=stream, chosen=taken.python)
        if taken.command == "interpreter":
            return interpreter(root, environ, stream=stream)
        if taken.command == "test-root":
            return test_root(taken.chosen, environ, stream=stream)
        return status(root, environ, stream=stream)
    except SetupRefusal as refusal:
        # ON STDERR, because `interpreter`'s STDOUT is consumed by a recipe as
        # the path to run: a refusal printed there would be executed.
        print("refused: " + str(refusal), file=sys.stderr)
        return 2


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
