"""Prepared W106673 offline exact-image transport probe; operator execution only.

--self-test has no Docker/provider side effects. --operator creates ONE offline
container and retains it stopped. No workspace, credential, mount syscall,
provider user message, model call, image acquisition or existing container use.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import uuid

IMAGE = "sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f"
VERSION = "2.1.247 (Claude Code)"
CLI = "/usr/local/bin/claude"
LIMIT = 262144
FLAGS = ("--input-format", "--output-format", "--verbose", "--print",
         "--resume", "--session-id", "--setting-sources", "--strict-mcp-config",
         "--mcp-config", "--tools", "--max-turns", "--max-budget-usd", "--model",
         "--dangerously-skip-permissions")
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp/probe-home",
       "TMPDIR": "/tmp", "XDG_CACHE_HOME": "/tmp/probe-cache",
       "PYTHONDONTWRITEBYTECODE": "1"}



# Only controller-authored vocabulary crosses either failure boundary.
STAGES = frozenset(("identity", "home", "version-command", "version-check",
                    "help-command", "help-check", "stream-start", "stream-pin",
                    "initialize-send", "initialize-read", "idle-check",
                    "image-check", "container-create", "offline-initialization", "done"))
REASONS = frozenset((
    "output-limit", "invalid-json", "invalid-record", "command-timeout",
    "command-failed", "invalid-control-response", "wrong-control-correlation",
    "initialization-refused", "wrong-probe-identity", "wrong-cli-version",
    "required-flag-absent", "initialization-timeout", "cli-exited-before-initialization",
    "initialized-cli-exited", "cli-process-changed", "docker-refused",
    "docker-output-limit", "container-image-mismatch", "container-label-mismatch",
    "wrong-container-posture", "wrong-container-user", "unexpected-bind", "wrong-image",
    "provider-image-environment", "invalid-created-id", "inside-probe-failed",
    "stop-unconfirmed", "path-not-found", "permission-denied", "os-error",
    "timeout", "invalid-encoding", "unexpected-error", "invalid-probe-diagnostic",
))
INITIALIZE_FLAGS = ("--print", "--input-format", "--output-format", "--verbose",
                    "--tools", "--setting-sources", "--strict-mcp-config", "--mcp-config")
UNEXERCISED_FLAGS = tuple(flag for flag in FLAGS if flag not in INITIALIZE_FLAGS)
FAILURE_KEYS = frozenset(("outcome", "stage", "reason", "child_exit_code", "os_errno",
                          "flags", "missing_help_flags", "unexercised_flags"))


def help_observation(flags):
    require(flags is None or (isinstance(flags, dict) and set(flags) == set(FLAGS)
            and all(type(value) is bool for value in flags.values())), "invalid-probe-diagnostic")
    return dict(flags=None if flags is None else dict(flags),
                missing_help_flags=None if flags is None else [flag for flag in FLAGS if not flags[flag]],
                unexercised_flags=list(UNEXERCISED_FLAGS))



class ProbeFailure(RuntimeError):
    def __init__(self, reason, exit_code=None):
        # Never use arbitrary exception text as a reason, even from our helpers.
        self.reason = reason if reason in REASONS else "unexpected-error"
        self.exit_code = exit_code
        super().__init__(self.reason)


def require(condition, reason):
    if not condition:
        raise ProbeFailure(reason)


def numeric(value, low, high):
    return value is None or (type(value) is int and low <= value <= high)


def failure(error, diagnostics):
    reason = "unexpected-error"
    if isinstance(error, ProbeFailure):
        reason = error.reason
    elif isinstance(error, FileNotFoundError):
        reason = "path-not-found"
    elif isinstance(error, PermissionError):
        reason = "permission-denied"
    elif isinstance(error, subprocess.TimeoutExpired):
        reason = "timeout"
    elif isinstance(error, OSError):
        reason = "os-error"
    elif isinstance(error, UnicodeError):
        reason = "invalid-encoding"
    elif isinstance(error, json.JSONDecodeError):
        reason = "invalid-json"
    code = error.exit_code if isinstance(error, ProbeFailure) else diagnostics.get("child_exit_code")
    if code is None:
        code = diagnostics.get("child_exit_code")
    number = getattr(error, "errno", None) if isinstance(error, OSError) else None
    stage = diagnostics.get("stage")
    return dict(outcome="offline-transport-preflight-failed",
                stage=stage if stage in STAGES else "identity", reason=reason,
                child_exit_code=code if numeric(code, -255, 255) else None,
                os_errno=number if numeric(number, 0, 4095) else None,
                **help_observation(diagnostics.get("flags")))


def checked_failure(answer):
    require(isinstance(answer, dict) and set(answer) == FAILURE_KEYS,
            "invalid-probe-diagnostic")
    require(answer["outcome"] == "offline-transport-preflight-failed"
            and isinstance(answer["stage"], str) and answer["stage"] in STAGES
            and isinstance(answer["reason"], str) and answer["reason"] in REASONS
            and numeric(answer["child_exit_code"], -255, 255)
            and numeric(answer["os_errno"], 0, 4095), "invalid-probe-diagnostic")
    observation = help_observation(answer["flags"])
    require(all(answer[key] == value for key, value in observation.items()),
            "invalid-probe-diagnostic")
    # Copy exactly the validated diagnostic projection, never other response data.
    return {key: answer[key] for key in sorted(FAILURE_KEYS)}


class Frames:
    """Bound retained and total bytes; errors never quote provider output."""
    def __init__(self):
        self.pending = b""
        self.total = 0

    def feed(self, chunk):
        self.total += len(chunk)
        require(self.total <= LIMIT, "output-limit")
        self.pending += chunk
        records = []
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                raise ProbeFailure("invalid-json") from None
            require(isinstance(record, dict), "invalid-record")
            records.append(record)
        return records


def captured(argv, diagnostics=None):
    diagnostics = diagnostics if diagnostics is not None else {}
    diagnostics["child_exit_code"] = None
    child = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             cwd="/tmp", env=ENV)
    data = bytearray()
    deadline = time.monotonic() + 15
    try:
        while True:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "command-timeout")
            require(select.select([child.stdout], [], [], remaining)[0], "command-timeout")
            chunk = os.read(child.stdout.fileno(), 8192)
            if not chunk:
                break
            data.extend(chunk)
            require(len(data) <= LIMIT, "output-limit")
        diagnostics["child_exit_code"] = child.wait(timeout=max(.01, deadline-time.monotonic()))
        require(diagnostics["child_exit_code"] == 0, "command-failed")
        return bytes(data)
    finally:
        # Preserve the natural exit if observable; do not call our cleanup signal
        # the cause of a timeout/output-limit failure.
        if diagnostics["child_exit_code"] is None:
            diagnostics["child_exit_code"] = child.poll()
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        child.stdout.close()


def initialized(record, request_id):
    # Project only an exact correlation and success bit, never response contents.
    if record.get("type") != "control_response":
        return False
    response = record.get("response")
    require(isinstance(response, dict), "invalid-control-response")
    require(response.get("request_id") == request_id, "wrong-control-correlation")
    require(response.get("subtype") == "success", "initialization-refused")
    return True


def inside(diagnostics):
    diagnostics.update(stage="identity", child_exit_code=None)
    require(os.geteuid() == 65532 and os.getpid() == 1, "wrong-probe-identity")
    diagnostics["stage"] = "home"
    Path(ENV["HOME"]).mkdir(mode=0o700)
    diagnostics["stage"] = "version-command"
    version = captured([CLI, "--version"], diagnostics)
    diagnostics["stage"] = "version-check"
    require(version.decode().strip() == VERSION, "wrong-cli-version")
    diagnostics["stage"] = "help-command"
    help_bytes = captured([CLI, "--help"], diagnostics)
    diagnostics["stage"] = "help-check"
    help_text = help_bytes.decode()
    flags = {flag: flag in help_text for flag in FLAGS}
    diagnostics["flags"] = flags
    # Help visibility is recorded, never substituted for actual behavior.
    # The unchanged argv below must still initialize successfully. The six
    # other flags remain explicit pending live requirements even on success.
    # No user frame is ever sent. No credential and network=none enforce the
    # offline boundary even if initialization attempts background traffic.
    argv = [CLI, "--print", "--input-format", "stream-json", "--output-format",
            "stream-json", "--verbose", "--tools", "", "--setting-sources=",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    diagnostics.update(stage="stream-start", child_exit_code=None)
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, cwd="/tmp", env=ENV)
    pidfd = None
    try:
        diagnostics["stage"] = "stream-pin"
        pidfd = os.pidfd_open(child.pid)
        start = Path(f"/proc/{child.pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
        request_id = uuid.uuid4().hex
        decoder = Frames()
        accepted = False
        begun = time.monotonic_ns()
        diagnostics["stage"] = "initialize-send"
        child.stdin.write((json.dumps({"type": "control_request", "request_id": request_id,
                                      "request": {"subtype": "initialize", "hooks": None}}) + "\n").encode())
        child.stdin.flush()
        deadline = time.monotonic() + 15
        diagnostics["stage"] = "initialize-read"
        while not accepted:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "initialization-timeout")
            require(select.select([child.stdout], [], [], remaining)[0], "initialization-timeout")
            chunk = os.read(child.stdout.fileno(), 8192)
            require(chunk, "cli-exited-before-initialization")
            for record in decoder.feed(chunk):
                accepted = initialized(record, request_id) or accepted
        elapsed = time.monotonic_ns() - begun
        # This proves only an idle initialized process, never a Claude turn/session.
        diagnostics["stage"] = "idle-check"
        require(not select.select([pidfd], [], [], 1)[0], "initialized-cli-exited")
        require(Path(f"/proc/{child.pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
                == start, "cli-process-changed")
        return dict(outcome="offline-transport-preflight-passed", version=VERSION,
                    help_sha256=hashlib.sha256(help_bytes).hexdigest(),
                    **help_observation(flags), initialized=True, idle_process_survived=True, pid=child.pid,
                    start=start, initialization_ns=elapsed,
                    real_turns=0, session_continuity="unproved", restore="unproved")
    finally:
        diagnostics["child_exit_code"] = child.poll()
        # Keep the primary failure stage/reason even when closing a broken pipe.
        active_error = sys.exc_info()[1]
        try:
            try:
                child.stdin.close()
            except BrokenPipeError:
                if active_error is None:
                    raise
            finally:
                if child.poll() is None:
                    child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=3)
        except Exception as cleanup:
            diagnostics["cleanup_failure"] = failure(cleanup, diagnostics)
            if active_error is None:
                raise
        finally:
            child.stdout.close()
            if pidfd is not None:
                os.close(pidfd)


def inside_result():
    diagnostics = {}
    try:
        return inside(diagnostics), 0
    except Exception as error:
        answer = failure(error, diagnostics)
        return answer, 1


def docker(*args, allow_exit=False):
    result = subprocess.run(["/usr/bin/docker", "--host", "unix:///var/run/docker.sock", *args],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=60,
                            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
                                 "DOCKER_CONFIG": "/nonexistent"})
    require(len(result.stdout) <= LIMIT, "docker-output-limit")
    if allow_exit:
        # start --attach can carry the structured inside failure with exit1.
        # Preserve it for validation rather than discarding stdout on that exit.
        return result.stdout, result.returncode
    if result.returncode != 0:
        raise ProbeFailure("docker-refused", result.returncode)
    return result.stdout


def checked_container(container, nonce):
    found = json.loads(docker("inspect", "--type=container", container))[0]
    require(found["Id"] == container and found["Image"] == IMAGE, "container-image-mismatch")
    require(found["Config"]["Labels"].get("baton.run") == nonce
            and found["Config"]["Labels"].get("baton.experiment") == "W106673-offline-session",
            "container-label-mismatch")
    host = found["HostConfig"]
    require(host["NetworkMode"] == "none" and not host["Privileged"]
            and host["ReadonlyRootfs"] and host["CapDrop"] == ["ALL"]
            and "no-new-privileges" in host["SecurityOpt"], "wrong-container-posture")
    require(found["Config"]["User"] == "65532:65532", "wrong-container-user")
    require(len(found["Mounts"]) == 1 and found["Mounts"][0]["Destination"] == "/probe.py"
            and not found["Mounts"][0]["RW"], "unexpected-bind")
    return found


def operator():
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix="baton-w106673-session-preflight-", dir="/tmp"))
    print(root, flush=True)
    script = root / "probe.py"
    script.write_bytes(Path(__file__).read_bytes())
    script.chmod(0o444)
    nonce = uuid.uuid4().hex
    result = dict(outcome="failed-or-blocked", image=IMAGE, run=nonce,
                  script_sha256=hashlib.sha256(script.read_bytes()).hexdigest())
    container = None
    try:
        result["stage"] = "image-check"
        image = json.loads(docker("image", "inspect", IMAGE))[0]
        require(image["Id"] == IMAGE and not image["Config"].get("Volumes"), "wrong-image")
        require(not any(one.split("=", 1)[0].startswith(("ANTHROPIC_", "CLAUDE_"))
                        for one in image["Config"].get("Env", [])), "provider-image-environment")
        result["stage"] = "container-create"
        container = docker("create", "--pull=never", "--network=none", "--read-only",
                           "--cap-drop=ALL", "--security-opt=no-new-privileges",
                           "--user=65532:65532", "--pids-limit=64", "--memory=1g", "--cpus=1",
                           "--label=baton.experiment=W106673-offline-session",
                           "--label=baton.run=" + nonce,
                           "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
                           "--mount", f"type=bind,src={script},dst=/probe.py,readonly",
                           "--workdir=/tmp", "--entrypoint=/usr/bin/python3",
                           IMAGE, "-B", "/probe.py", "--inside").decode().strip()
        require(len(container) == 64 and all(c in "0123456789abcdef" for c in container),
                "invalid-created-id")
        result["container"] = container
        (root / "registration.json").write_text(json.dumps(result, indent=2) + "\n")
        checked_container(container, nonce)
        result["stage"] = "offline-initialization"
        raw, result["docker_exit_code"] = docker("start", "--attach", container, allow_exit=True)
        answer = json.loads(raw)
        if isinstance(answer, dict) and answer.get("outcome") == "offline-transport-preflight-failed":
            result["probe"] = checked_failure(answer)
            raise ProbeFailure("inside-probe-failed")
        require(isinstance(answer, dict) and answer.get("outcome") == "offline-transport-preflight-passed",
                "inside-probe-failed")
        require(result["docker_exit_code"] == 0, "docker-refused")
        result["probe"] = answer
        result["outcome"] = "offline-transport-preflight-passed"
        result["stage"] = "done"
    except Exception as error:
        result["failure"] = failure(error, result)
        result["outcome"] = "failed-or-blocked"
    finally:
        if container is not None:
            try:
                found = checked_container(container, nonce)
                if found["State"]["Running"]:
                    docker("stop", "--time=3", container)
                found = checked_container(container, nonce)
                require(not found["State"]["Running"] and found["State"]["Pid"] == 0,
                        "stop-unconfirmed")
                result["cleanup"] = "confirmed-stopped-retained"
                result["container_exit_code"] = found["State"]["ExitCode"]
                if result["container_exit_code"] != 0:
                    result["outcome"] = "failed-or-blocked"
            except Exception as error:
                result["cleanup_failure"] = failure(error, result)
                result["cleanup"] = "unconfirmed-operator-inspection-required"
                result["outcome"] = "failed-or-blocked"
        (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["outcome"] == "offline-transport-preflight-passed" else 1


class LocalTests(unittest.TestCase):
    def test_cleanup_identity_check_refuses_a_different_container(self):
        with mock.patch(__name__ + ".docker", return_value=json.dumps([
                {"Id": "other", "Image": IMAGE}]).encode()):
            with self.assertRaisesRegex(RuntimeError, "container-image-mismatch"):
                checked_container("expected", "nonce")

    def test_fragmented_records(self):
        frames = Frames()
        self.assertEqual(frames.feed(b'{"type":"control_'), [])
        self.assertEqual(frames.feed(b'response"}\n'), [{"type": "control_response"}])

    def test_malformed_and_oversized_are_closed(self):
        for raw in (b'{secret}\n', b'[]\n', b'x' * (LIMIT + 1)):
            with self.subTest(size=len(raw)):
                with self.assertRaises(RuntimeError) as error:
                    Frames().feed(raw)
                self.assertNotIn("secret", str(error.exception))

    def test_control_response_requires_exact_success(self):
        good = {"type": "control_response", "response": {"request_id": "pin", "subtype": "success"}}
        self.assertTrue(initialized(good, "pin"))
        self.assertFalse(initialized({"type": "result", "result": "secret"}, "pin"))
        for response in ({"request_id": "old", "subtype": "success"},
                         {"request_id": "pin", "subtype": "error", "error": "secret"}):
            with self.assertRaises(RuntimeError) as error:
                initialized({"type": "control_response", "response": response}, "pin")
            self.assertNotIn("secret", str(error.exception))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--operator", action="store_true")
    group.add_argument("--inside", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LocalTests))
        return 0 if result.wasSuccessful() else 1
    if args.inside:
        answer, code = inside_result()
        print(json.dumps(answer, sort_keys=True))
        return code
    return operator()


if __name__ == "__main__":
    sys.exit(main())
