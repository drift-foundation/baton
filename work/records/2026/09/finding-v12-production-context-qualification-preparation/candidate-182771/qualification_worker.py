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
    except OSError:
        raise c.Refusal("publish-type") from None


def _mutable(fd, directory):
    """The two objects that will be changed: type, owner, group, and aliases.

    "Runtime-owned" means owned by THIS process rather than by a constant that
    could drift; `main` separately pins that this worker is uid 65532. A
    multi-link regular file is refused BEFORE any mode change, because a chmod
    reaches every alias and the manager's later hardlink refusal cannot undo it.
    """
    info = os.fstat(fd)
    c.require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), "publish-type")
    c.require(info.st_uid == os.geteuid(), "publish-ownership")
    c.require(info.st_gid == c.GROUP, "publish-ownership")
    if not directory:
        c.require(info.st_nlink == 1, "publish-alias")
    return info


def _survey(home_fd, session):
    """Bounded no-follow survey of the whole home, BEFORE anything is changed.

    R2, same review. The first version checked one directory and the expected
    filename, so a foreign session, a nested session or a credential-shaped
    entry each still published and still moved 0600 to 0640 -- the proposal says
    those must "refuse and relax nothing", and a later inventory refusal cannot
    repair a mode change that already happened.

    Returns the verified project and selected descriptors, taken from this same
    traversal so selection and mutation are bound to one chain. Never opens a
    regular file; the expected credential link is checked by readlink only.
    """
    prefix = ".claude/projects"
    projects, sessions, keep = [], [], {}
    stack = [(home_fd, "", 0, False)]
    seen = 0
    try:
        while stack:
            fd, relative, depth, owned = stack.pop()
            try:
                c.require(depth <= c.STATE_DEPTH, "publish-shape")
                for name in sorted(os.listdir(fd)):
                    seen += 1
                    c.require(seen <= c.STATE_FILES, "publish-shape")
                    path = name if not relative else relative + "/" + name
                    info = os.lstat(name, dir_fd=fd)
                    if path == ".claude/.credentials.json":
                        # The one expected credential object, checked and never opened.
                        c.require(stat.S_ISLNK(info.st_mode) and os.readlink(name, dir_fd=fd) == c.SLOT,
                                  "publish-shape")
                        continue
                    c.require(not re.search(r"credential|oauth|auth[-_.]?token|api[-_.]?key", name, re.I),
                              "publish-shape")
                    if path.startswith(prefix + "/") and name.endswith(".jsonl"):
                        sessions.append(path)
                    if not stat.S_ISDIR(info.st_mode):
                        continue
                    if relative == prefix:
                        projects.append(path)
                    child = _open_at(fd, name, True)
                    if path in (".claude", prefix) or path.startswith(prefix + "/"):
                        stack.append((child, path, depth + 1, True))
                    else:
                        os.close(child)
            finally:
                if owned:
                    os.close(fd)
        c.require(len(projects) == 1, "publish-shape")
        expected = projects[0] + "/" + session + ".jsonl"
        # Exactly the expected session, and nothing foreign or nested anywhere
        # beneath the prefix.
        c.require(sessions == [expected], "publish-shape")
        claude = _open_at(home_fd, ".claude", True)
        keep["claude"] = claude
        projects_fd = _open_at(claude, "projects", True)
        keep["projects"] = projects_fd
        project = _open_at(projects_fd, projects[0].split("/")[-1], True)
        keep["project"] = project
        selected = _open_at(project, session + ".jsonl", False)
        keep["selected"] = selected
        _mutable(project, True)
        _mutable(selected, False)
        return project, selected, keep
    except BaseException:
        for fd in list(keep.values()) + [fd for fd, _, _, owned in stack if owned]:
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
    except OSError:
        raise c.Refusal("publish-type") from None
    try:
        project, selected, keep = _survey(home_fd, session)
        try:
            # EVERY refusal is already behind us. Setgid kept so entries created
            # later still inherit the group.
            os.fchmod(project, 0o2750)
            os.fchmod(selected, 0o640)
        finally:
            for fd in keep.values():
                os.close(fd)
    finally:
        os.close(home_fd)
    return {"project_mode": "0o2750", "session_mode": "0o640"}


def main():
    result = {"outcome": "failed", "provider_started": False}
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
        published = publish(request["session"], request["turn"])
        result.update(published=published, provider_exit=code, terminal=c.projection(raw, request["session"]),
                      argv=args[:-1] + [{"prompt_sha256": c.sha(args[-1].encode())}],
                      environment_keys=sorted(env), cwd="/output", uid=os.getuid(), groups=sorted(os.getgroups()),
                      home_mode=oct(Path(c.HOME).stat().st_mode & 0o7777), outcome="observed")
    except BaseException as error:
        # Only fixed fixture-authored refusal labels cross; never str(error).
        result = {"outcome": "failed", "provider_started": result["provider_started"], "failure_code": c.failure_code(error)}
    os.write(1, c.encoded(result) + b"\n")


if __name__ == "__main__":
    main()
