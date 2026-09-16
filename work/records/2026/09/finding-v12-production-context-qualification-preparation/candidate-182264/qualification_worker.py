"""In-image fixture entry. Provider prose stays on an anonymous bounded pipe."""
import os
from pathlib import Path
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


def _owned(path, directory):
    """A descriptor for one runtime-owned object, verified before it is changed.

    The check and the change go through THE SAME no-follow descriptor, so there
    is no window between them: a symlink refuses instead of redirecting the
    chmod, and a swap after the check cannot reach a different object.
    """
    flags = os.O_RDONLY | os.O_NOFOLLOW | (os.O_DIRECTORY if directory else 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        raise c.Refusal("publish-type") from None
    try:
        info = os.fstat(fd)
        expected = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
        c.require(expected, "publish-type")
        # RUNTIME-OWNED ONLY, and "runtime-owned" means owned by THIS process
        # rather than by a constant that could drift: the only objects an
        # identity may reopen are its own. `main` separately pins that this
        # worker is uid 65532, so the two checks together say exactly what is
        # meant. The turn-2 home is manager-reconstructed and its restored
        # state is manager-owned 0o660 -- the writable working copy accepted at
        # R1/178875 -- so this would refuse it even if turn 2 ever reached
        # here, which it does not.
        c.require(info.st_uid == os.geteuid() and info.st_gid == c.GROUP, "publish-ownership")
        return fd, info
    except BaseException:
        os.close(fd)
        raise


def publish(session, turn):
    """Turn 1 only: open exactly two runtime-owned objects to the shared group.

    The manager collects this home after shutdown as a different uid that holds
    the workspace group. Setgid gave every entry gid GROUP and setgid never
    gives group PERMISSION BITS, so state the CLI creates 0o700/0o600 is
    unreadable to the collector. The owning identity -- this worker -- opens
    exactly the project directory and the expected session file, and nothing
    else: .claude.json, the credential link, other sessions and every cache
    entry keep the modes the CLI gave them.

    TURN 2 PUBLISHES NOTHING. Its home is manager-reconstructed, its restored
    state is already group-readable and group-writable at 0o660, and the
    manager does not collect again after it.
    """
    if turn != 1:
        return None
    projects = Path(c.HOME) / ".claude/projects"
    try:
        found = sorted(entry.name for entry in os.scandir(projects) if entry.is_dir(follow_symlinks=False))
    except OSError:
        raise c.Refusal("publish-shape") from None
    c.require(len(found) == 1, "publish-shape")
    directory, info = _owned(projects / found[0], True)
    try:
        selected, _ = _owned(projects / found[0] / (session + ".jsonl"), False)
        try:
            # Setgid kept so entries created later still inherit the group.
            os.fchmod(directory, 0o2750)
            os.fchmod(selected, 0o640)
        finally:
            os.close(selected)
    finally:
        os.close(directory)
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
