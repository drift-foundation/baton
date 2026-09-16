"""In-image fixture entry. Provider prose stays on an anonymous bounded pipe."""
import os
from pathlib import Path
import select
import signal
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
        result.update(provider_exit=code, terminal=c.projection(raw, request["session"]),
                      argv=args[:-1] + [{"prompt_sha256": c.sha(args[-1].encode())}],
                      environment_keys=sorted(env), cwd="/output", uid=os.getuid(), groups=sorted(os.getgroups()),
                      home_mode=oct(Path(c.HOME).stat().st_mode & 0o7777), outcome="observed")
    except BaseException as error:
        # Only fixed fixture-authored refusal labels cross; never str(error).
        result = {"outcome": "failed", "provider_started": result["provider_started"], "failure_code": c.failure_code(error)}
    os.write(1, c.encoded(result) + b"\n")


if __name__ == "__main__":
    main()
