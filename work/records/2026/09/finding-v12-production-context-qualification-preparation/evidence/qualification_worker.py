"""In-image fixture entry. Provider prose stays on an anonymous bounded pipe."""
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import time

import qualification_contract as c


def invoke(arguments, env, *, seconds=c.TURN_SECONDS, run=subprocess.Popen, started=None):
    process = run(arguments, cwd="/output", env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                  stderr=subprocess.DEVNULL, start_new_session=True, bufsize=0)
    data = bytearray()
    deadline = time.monotonic() + seconds
    try:
        if started is not None:
            started(process.pid)
        fd = process.stdout.fileno()
        os.set_blocking(fd, False)
        eof = False
        while not eof or process.poll() is None:
            left = deadline - time.monotonic()
            c.require(left > 0, "provider-timeout")
            if not eof and select.select([fd], [], [], min(left, 0.1))[0]:
                piece = os.read(fd, 4096)
                eof = not piece
                data.extend(piece)
                c.require(len(data) <= c.LIMIT, "provider-output-bound")
            elif eof:
                time.sleep(min(left, 0.01))
        return process.returncode, bytes(data)
    finally:
        # Kill surviving descendants in this invocation's own group. The
        # controller also requires whole-container stopped state before reads.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
        process.stdout.close()


# The fixture's own credential shape, so the worker stops exactly where the
# manager's inventory stops rather than inventing a second rule.
CREDENTIAL = re.compile(r"credential|oauth|auth[-_.]?token|api[-_.]?key", re.I)


def _open_at(parent_fd, name, directory):
    """One child of a VERIFIED parent descriptor, never followed.

    R1, review 2026-09-16T00-41-09Z. The first version opened absolute paths
    with O_NOFOLLOW on their FINAL component, which protects each object and not
    the PATH: a symlinked `.claude/projects` reached outside HOME entirely, and
    reopening the session by pathname after checking its directory let a
    rename-and-replace redirect the change to a decoy. Every component is now
    opened relative to its verified parent, so the chain itself is the guarantee.

    O_NONBLOCK because a FIFO or device substituted for an expected object would
    otherwise block in `open` before `fstat` could reject it.
    """
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_DIRECTORY if directory else 0)
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except OSError as failure:
        raise c.publication_failure("publish-type", "open", failure.errno) from None


def _mutable(fd, directory):
    """The two objects that will be changed: type, owner, group, and aliases.

    "Runtime-owned" means owned by THIS process rather than by a constant that
    could drift; `main` separately pins that this worker is uid 65532. A
    multi-link regular file is refused BEFORE any mode change, because a chmod
    reaches every alias and the manager's later hardlink refusal cannot undo it.
    """
    try:
        info = os.fstat(fd)
    except OSError as failure:
        # Without this the target's own metadata read escaped as a raw OSError:
        # `unclassified`, with the publication diagnostic null.
        raise c.publication_failure("publish-type", "target-metadata", failure.errno) from None
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise c.publication_failure("publish-type", "target-type")
    if info.st_uid != os.geteuid():
        raise c.publication_failure("publish-ownership", "target-owner")
    if info.st_gid != c.GROUP:
        raise c.publication_failure("publish-ownership", "target-group")
    if not directory and info.st_nlink != 1:
        raise c.publication_failure("publish-alias", "target-alias")
    return info


PROJECTS = ".claude/projects"


def _walk(fd, relative, depth, session, state):
    """One directory of the bounded home-wide preflight.

    R2, review 2026-09-16T02-11-27Z. The first version descended only `.claude`
    and the projects chain, so a credential-shaped entry under HOME/cache or
    HOME/.claude/cache was never seen and published before the manager's own
    inventory could refuse it. "Home-wide" now means home-wide, under the same
    entry and depth bounds the inventory uses, with the same type rule.

    R1, same review. Directories on the path to the two targets are RETAINED
    here, because the first version walked descriptors and then reopened the
    targets BY PATH -- which just moved the swap to the end of the survey.
    Verifying a descriptor is worthless if it is not the one you then change.
    """
    if depth > c.STATE_DEPTH:
        raise c.publication_failure("publish-shape", "depth-bound")
    # A preflight that cannot finish cannot clear anything. An entry that
    # vanishes or refuses mid-walk -- including one swapped out underneath us --
    # is a survey that did not complete, so it refuses with a registered code
    # rather than letting a raw OSError decide what happens next.
    try:
        names = sorted(os.listdir(fd))
    except OSError as failure:
        raise c.publication_failure("publish-shape", "listing", failure.errno) from None
    for name in names:
        state["seen"] += 1
        if state["seen"] > c.STATE_FILES:
            raise c.publication_failure("publish-shape", "entry-bound")
        path = name if not relative else relative + "/" + name
        try:
            info = os.lstat(name, dir_fd=fd)
        except OSError as failure:
            raise c.publication_failure("publish-shape", "entry-metadata", failure.errno) from None
        if path == ".claude/.credentials.json":
            # The one expected credential object: checked, never opened.
            try:
                target = os.readlink(name, dir_fd=fd)
            except OSError as failure:
                raise c.publication_failure("publish-shape", "credential-link", failure.errno) from None
            if not (stat.S_ISLNK(info.st_mode) and target == c.SLOT):
                raise c.publication_failure("publish-shape", "credential-link")
            continue
        if CREDENTIAL.search(name):
            raise c.publication_failure("publish-shape", "credential-name")
        # The manager's own admitted types. Anything else would refuse at
        # collection anyway; refusing it here keeps it from being published first.
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise c.publication_failure("publish-type", "entry-type")
        if stat.S_ISREG(info.st_mode):
            if path.startswith(PROJECTS + "/") and name.endswith(".jsonl"):
                state["sessions"].append(path)
                if relative in state["keep"] and name == session + ".jsonl":
                    # Opened from the directory we are standing in, not from a
                    # path resolved again later.
                    state["keep"]["selected"] = _open_at(fd, name, False)
            continue
        child = _open_at(fd, name, True)
        if relative == PROJECTS:
            state["projects"].append(path)
        # EVERY runtime-owned directory is retained, because traversal is what
        # gets published: the manager needs r-x on each one to see the names and
        # types its coverage rules are about, and needs r on no file but the
        # selected session. Each is held from the survey that verified it until
        # the mutation, so the descriptor that is checked is the one changed.
        mine = info.st_uid == os.geteuid() and info.st_gid == c.GROUP
        retained = mine or path in (".claude", PROJECTS) or relative == PROJECTS
        if retained:
            state["keep"][path] = child
        if mine:
            state["directories"].append(path)
            if len(state["directories"]) > c.PUBLISH_DIRECTORIES:
                raise c.publication_failure("publish-shape", "directory-bound")
        try:
            _walk(child, path, depth + 1, session, state)
        finally:
            if not retained:
                os.close(child)


def _survey(home_fd, session):
    """The whole bounded preflight, BEFORE anything is changed.

    Returns the two descriptors the walk itself opened. Nothing is mutated
    until this returns: the proposal requires a forbidden layout to refuse and
    relax nothing.
    """
    state = {"seen": 0, "sessions": [], "projects": [], "directories": [], "keep": {}}
    try:
        _walk(home_fd, "", 0, session, state)
        if len(state["projects"]) != 1:
            raise c.publication_failure("publish-shape", "project-count")
        expected = state["projects"][0] + "/" + session + ".jsonl"
        if state["sessions"] != [expected]:
            raise c.publication_failure("publish-shape", "session-set")
        project = state["keep"].get(state["projects"][0])
        selected = state["keep"].get("selected")
        if project is None or selected is None:
            raise c.publication_failure("publish-shape", "targets-missing")
        _mutable(project, True)
        _mutable(selected, False)
        # Verified here, mutated by the caller: nothing has changed yet.
        for path in state["directories"]:
            _mutable(state["keep"][path], True)
        return [state["keep"][path] for path in state["directories"]], selected, state["keep"]
    except BaseException:
        for fd in state["keep"].values():
            try:
                os.close(fd)
            except OSError:
                pass
        raise


def publish(session, turn):
    """Turn 1 only: open exactly two runtime-owned objects to the shared group.

    The manager collects this home after shutdown as a different uid holding the
    workspace group. Setgid gave every entry that group and setgid never gives
    group PERMISSION BITS, so state the CLI creates 0o700/0o600 is unreadable to
    the collector. The owning identity -- this worker -- opens exactly the
    project directory and the expected session file, and nothing else.

    TURN 2 PUBLISHES NOTHING. Its home is manager-reconstructed, its restored
    state is already 0o660 per accepted R1/178875, and the manager does not
    collect again after it.
    """
    if turn != 1:
        return None
    try:
        home_fd = os.open(c.HOME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_DIRECTORY)
    except OSError as failure:
        raise c.publication_failure("publish-type", "home-open", failure.errno) from None
    try:
        directories, selected, keep = _survey(home_fd, session)
        try:
            # EVERY refusal is already behind us. TRAVERSAL, NOT CONTENTS: each
            # runtime-owned directory becomes group-readable and searchable so
            # the manager can see the names and types its coverage rules are
            # about, with setgid kept and no world access. Every FILE keeps the
            # mode the CLI gave it -- .claude.json, other sessions, every cache
            # entry -- except the one selected session the manager may copy.
            try:
                for fd in directories:
                    os.fchmod(fd, 0o2750)
                os.fchmod(selected, 0o640)
            except OSError as failure:
                raise c.publication_failure("publish-type", "chmod", failure.errno) from None
        finally:
            for fd in keep.values():
                os.close(fd)
    finally:
        os.close(home_fd)
    return {"directories": len(directories), "directory_mode": "0o2750", "session_mode": "0o640"}


def main():
    result = {"outcome": "failed", "provider_started": False}
    observed = None
    try:
        c.require(os.getuid() == 65532 and c.GROUP in os.getgroups(), "worker-identity")
        request = c.decoded(c.read_file("/qualification/request.json"))
        c.require(set(request) == {"session", "turn", "prompt"}, "request-shape")
        args = c.argv(request["session"], request["turn"], request["prompt"])
        env = c.environment()
        for key in ("TMPDIR", "XDG_CACHE_HOME", "PYTHONPYCACHEPREFIX"):
            Path(env[key]).mkdir(mode=0o700, parents=True)
        c.require(os.readlink(Path(c.HOME) / ".claude/.credentials.json") == c.SLOT, "credential-link-drift")
        code, raw = invoke(args, env, started=lambda pid: result.update(provider_started=True))
        # THE OBSERVATION IS MADE BEFORE PUBLICATION, AND SURVIVES IT. Run183114
        # published first, so a publication refusal discarded a provider exit
        # and a terminal record that were already available -- the run could not
        # even say whether the provider's answer was well-formed. An observation
        # must not depend on an unrelated later step.
        #
        # It is EVIDENCE, NOT A PASS: the arm still fails below, and a preserved
        # observation bypasses no publication, shutdown or qualification gate.
        # Malformed or missing terminal data stays refused here, unobserved.
        observed = {"provider_exit": code, "terminal": c.projection(raw, request["session"])}
        published = publish(request["session"], request["turn"])
        result.update(published=published, provider_exit=code, terminal=observed["terminal"],
                      argv=args[:-1] + [{"prompt_sha256": c.sha(args[-1].encode())}],
                      environment_keys=sorted(env), cwd="/output", uid=os.getuid(), groups=sorted(os.getgroups()),
                      home_mode=oct(Path(c.HOME).stat().st_mode & 0o7777), outcome="observed")
    except BaseException as error:
        # Only fixed fixture-authored labels cross; never str(error). The
        # publication diagnostic names WHICH check failed, from a closed
        # vocabulary, and the observation above is carried through if one was
        # already made.
        result = {"outcome": "failed", "provider_started": result["provider_started"],
                  "failure_code": c.failure_code(error),
                  "publication": c.publication_detail(error) if getattr(error, "check", None) else None,
                  "observed": observed}
    os.write(1, c.encoded(result) + b"\n")


if __name__ == "__main__":
    main()
