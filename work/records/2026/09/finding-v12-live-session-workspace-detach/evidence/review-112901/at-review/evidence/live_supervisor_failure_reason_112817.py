"""W106673 reviewed-only live fixture supervisor; no standalone host execution.

Provider output is reduced here. Neither text/tool arguments nor diagnostics are
forwarded to the host. The fixture session directory is private, not evidence.
"""
import errno
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import time
import uuid

CLI = "/usr/local/bin/claude"
MODEL = "claude-fable-5[1m]"
ACTUAL_MODEL = "claude-fable-5"
VERSION = "2.1.247"
MAX_LINE = 256 * 1024
MAX_STREAM = 4 * 1024 * 1024
TURN_SECONDS = 180
MAX_TURNS = 8
SESSION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def require(condition, code):
    if not condition:
        raise Refusal(code)


class Refusal(Exception):
    pass


ARMS = frozenset(("unassigned", "retained-first", "restored-first", "restored-second"))
OPERATIONS = frozenset(("start", "turn", "identity", "probe"))
DIAGNOSTIC_STAGES = frozenset(("created", "command-validation", "provider-write-intent",
    "provider-write-completed", "provider-response-observed", "provider-result-validation"))
REFUSAL_CODES = frozenset(('actual-model-drift', 'actual-model-unobserved', 'artifact-file-boundary', 'artifact-path-set', 'artifact-size-bound', 'artifact-verification-failed', 'builtin-bridge-unproved', 'choose-one-operation', 'cleanup-deadline', 'cli-exited', 'cli-host-identity-unproved', 'cli-parent-drift', 'cli-pid-reused', 'cli-pidfd-exited', 'cli-version-drift', 'command-not-allowed', 'consumer-workspace-drift', 'container-image-drift', 'container-label-drift', 'container-not-current', 'created-id-unrecognized', 'credential-home-not-volatile', 'credential-link-changed', 'credential-link-occupied', 'credential-release-before-shutdown', 'credential-slot-drift', 'diagnostic-arm-invalid', 'diagnostic-frame-invalid', 'diagnostic-frame-limit', 'diagnostic-operation-invalid', 'diagnostic-stage-invalid', 'docker-output-bound', 'docker-refused', 'duplicate-start', 'execution-scope-not-selected', 'export-file-boundary', 'fixture-only', 'host-write-incomplete', 'idle-process-tree-changed', 'image-missing-or-drift', 'init-exit-unconfirmed', 'init-exited-or-reused', 'init-session-changed', 'initial-workspace-missing', 'initial-workspace-not-empty', 'initialize-frame', 'initialize-rejected', 'input-bound', 'manifest-constants', 'namespace-survivor', 'namespace-workspace-drift', 'overall-deadline', 'overall-timeout', 'package-drift', 'process-list-shape', 'process-namespace-drift', 'process-privilege-drift', 'process-user-drift', 'process-workspace-cwd', 'prompt-bound', 'provider-result-failed', 'provider-turn-limit', 'provider-write-incomplete', 'replacement-before-reviewed-stop', 'reported-cost-limit', 'response-shape-invalid', 'result-session-changed', 'resume-input', 'review-deadline', 'runtime-already-imported', 'runtime-copy-drift', 'runtime-file-set-drift', 'runtime-mount-config-drift', 'runtime-posture-drift', 'runtime-source-symlink', 'runtime-user-drift', 'schema-package-incomplete', 'separate-root-operator-approval-required', 'session-input', 'shutdown-unconfirmed', 'stopped', 'stream-eof', 'stream-json', 'stream-line-bound', 'stream-shape', 'stream-timeout', 'stream-total-bound', 'supervisor-cli-identity-drift', 'supervisor-identity', 'supervisor-refused', 'turn-clock-order', 'turn-runtime-identity', 'unexpected-control-request', 'unexpected-idle-process-tree', 'unknown-diagnostic-stage', 'unknown-setup-resource', 'unknown-setup-stage', 'unrecognized-provider-frame', 'unsupported-namespace-posture', 'user-turn-limit'))


REFUSAL_CODES = REFUSAL_CODES | frozenset(("restoration-verification-missing", "restoration-stop-unconfirmed",
    "restoration-workspace-changed", "restoration-session-changed", "restoration-process-not-replaced",
    "restoration-runtime-drift", "restoration-clock-order"))


def refusal_projection(error):
    # No str(error): custom exception __str__ methods are outside projection.
    code = error.args[0] if type(error) is Refusal and len(error.args) == 1 else None
    if type(code) is not str or code not in REFUSAL_CODES:
        code = "unclassified"
    kinds = {Refusal: "fixture-refusal", BrokenPipeError: "broken-pipe", OSError: "os-error",
             ValueError: "value-error", TypeError: "type-error", KeyError: "key-error",
             subprocess.TimeoutExpired: "subprocess-timeout"}
    number = error.errno if isinstance(error, OSError) else None
    if type(number) is not int or not 0 < number < 4096:
        number = None
    return dict(refusal_code=code, exception_kind=kinds.get(type(error), "other"), errno=number)


def argv(session, resume):
    require(type(session) is str and SESSION.fullmatch(session), "session-input")
    require(type(resume) is bool, "resume-input")
    return [CLI, "--print", "--input-format", "stream-json", "--output-format", "stream-json",
            "--verbose", "--tools", "Bash,Read,Write,Edit", "--setting-sources=",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--dangerously-skip-permissions", "--model", MODEL,
            "--max-turns", str(MAX_TURNS), "--max-budget-usd", "1",
            "--resume" if resume else "--session-id", session]


def start_time(pid):
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]


class Lines:
    """No buffered readline after select: partial lines remain deadline-bound."""
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.buffer = b""
        self.count = 0

    def next(self, deadline):
        while b"\n" not in self.buffer:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "stream-timeout")
            require(select.select([self.descriptor], [], [], remaining)[0], "stream-timeout")
            chunk = os.read(self.descriptor, 16384)
            require(chunk, "stream-eof")
            self.count += len(chunk)
            require(self.count <= MAX_STREAM, "stream-total-bound")
            self.buffer += chunk
            require(len(self.buffer.split(b"\n", 1)[0]) <= MAX_LINE, "stream-line-bound")
        raw, self.buffer = self.buffer.split(b"\n", 1)
        require(len(raw) <= MAX_LINE, "stream-line-bound")
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError):
            raise Refusal("stream-json") from None
        require(type(value) is dict, "stream-shape")
        return value


# Closed labels from RESULT-DIAGNOSTICS.md's recorded transport contract.
# Their presence in this particular CLI image is an observation, not assumed.
KNOWN_RESULT_SUBTYPES = {
    "error_during_execution": "error_during_execution",
    "error_max_turns": "error_max_turns",
    "error_max_budget_usd": "error_max_budget_usd",
    "error_max_structured_output_retries": "error_max_structured_output_retries",
}
RESULT_SUBTYPE_SHAPES = frozenset(("success", "missing", "known-nonsuccess", "unknown", "wrong-type"))
RESULT_ERROR_SHAPES = frozenset(("false", "true", "missing", "wrong-type"))


def result_fields(value):
    """Observe only two success-predicate inputs; never copy provider prose."""
    subtype = value.get("subtype")
    known = None
    if "subtype" not in value:
        shape = "missing"
    elif type(subtype) is not str:
        shape = "wrong-type"
    elif subtype == "success":
        shape = "success"
    elif subtype in KNOWN_RESULT_SUBTYPES:
        shape = "known-nonsuccess"
        known = KNOWN_RESULT_SUBTYPES[subtype]
    else:
        shape = "unknown"
    error = value.get("is_error")
    flag = "missing" if "is_error" not in value else "false" if error is False else "true" if error is True else "wrong-type"
    return dict(subtype=shape, known_subtype=known, is_error=flag)


def validate_result_fields(value):
    require(type(value) is dict and set(value) == {"subtype", "known_subtype", "is_error"}, "diagnostic-frame-invalid")
    require(type(value["subtype"]) is str and value["subtype"] in RESULT_SUBTYPE_SHAPES
            and type(value["is_error"]) is str and value["is_error"] in RESULT_ERROR_SHAPES, "diagnostic-frame-invalid")
    known = value["known_subtype"]
    require((type(known) is str and known in KNOWN_RESULT_SUBTYPES) if value["subtype"] == "known-nonsuccess"
            else known is None, "diagnostic-frame-invalid")
    return dict(value)


# One documented result field; fixed values only, never provider prose.
KNOWN_API_ERROR_STATUSES = frozenset((400, 401, 402, 403, 404, 409, 413, 429, 500, 504, 529))
API_ERROR_STATUS_SHAPES = frozenset(("missing", "null", "known", "unknown", "wrong-type"))


def failure_reason(value):
    status = value.get("api_error_status")
    if "api_error_status" not in value:
        shape = "missing"
    elif status is None:
        shape = "null"
    elif type(status) is not int:
        shape = "wrong-type"
    elif status in KNOWN_API_ERROR_STATUSES:
        shape = "known"
    else:
        shape = "unknown"
    return dict(shape=shape, http_status=status if shape == "known" else None)


def validate_failure_reason(value):
    require(type(value) is dict and set(value) == {"shape", "http_status"}, "diagnostic-frame-invalid")
    require(type(value["shape"]) is str and value["shape"] in API_ERROR_STATUS_SHAPES, "diagnostic-frame-invalid")
    status = value["http_status"]
    require((type(status) is int and status in KNOWN_API_ERROR_STATUSES) if value["shape"] == "known"
            else status is None, "diagnostic-frame-invalid")
    return dict(value)


def result_projection(value, session):
    require(value.get("type") == "result" and value.get("subtype") == "success"
            and value.get("is_error") is False, "provider-result-failed")
    require(value.get("session_id") == session, "result-session-changed")
    turns = value.get("num_turns")
    cost = value.get("total_cost_usd")
    require(type(turns) is int and 0 < turns <= MAX_TURNS, "provider-turn-limit")
    require(type(cost) in (int, float) and math.isfinite(cost) and 0 <= cost <= 1,
            "reported-cost-limit")
    # This is a reported-cost check AFTER execution, never a hard billing cap.
    return dict(session=session, num_turns=turns, reported_cost_usd=cost)


class Supervisor:
    def __init__(self):
        self.process = None
        self.pidfd = None
        self.turns = 0
        self.session = None
        self.model = None
        self.deadline = None
        self.arm = "unassigned"
        self.operation = "start"
        self.stage = "created"

    def observe(self, stage, result=None):
        require(stage in DIAGNOSTIC_STAGES, "diagnostic-stage-invalid")
        self.stage = stage
        projection = dict(event="diagnostic", arm=self.arm, operation=self.operation,
                          turn=self.turns, stage=stage, monotonic_ns=time.monotonic_ns())
        if result is not None:
            require(stage == "provider-result-validation", "diagnostic-frame-invalid")
            projection["result_fields"] = result_fields(result)
            projection["failure_reason"] = failure_reason(result)
        print(json.dumps(projection), flush=True)

    def identity(self):
        require(self.process is not None and self.process.poll() is None, "cli-exited")
        require(not select.select([self.pidfd], [], [], 0)[0], "cli-pidfd-exited")
        require(start_time(self.process.pid) == self.start, "cli-pid-reused")
        return dict(cli_pid=self.process.pid, cli_start=self.start, session=self.session,
                    actual_model=self.model, cli_version=VERSION)

    def initialize(self, command):
        require(self.process is None, "duplicate-start")
        require(command.get("arm") in ARMS - {"unassigned"}, "diagnostic-arm-invalid")
        self.arm = command["arm"]
        self.session = command["session"]
        self.limit = 1  # Restored-only scope: exactly one possible user turn per container.
        self.deadline = command["deadline"]
        require(type(self.deadline) in (int, float) and math.isfinite(self.deadline)
                and 0 < self.deadline - time.monotonic() <= 900, "overall-deadline")
        seconds = self.deadline - time.monotonic()
        signal.setitimer(signal.ITIMER_REAL, seconds)
        home = Path("/session/home")
        (home / ".claude").mkdir(parents=True, exist_ok=True)
        slot = home / ".claude/.credentials.json"
        if slot.is_symlink():
            require(os.readlink(slot) == "/run/baton/credentials/claude", "credential-link-changed")
        else:
            require(not slot.exists(), "credential-link-occupied")
            slot.symlink_to("/run/baton/credentials/claude")
        env = dict(PATH="/usr/local/bin:/usr/bin:/bin", HOME=str(home), TMPDIR="/tmp",
                   XDG_CACHE_HOME="/session/cache", CLAUDE_CONFIG_DIR=str(home / ".claude"),
                   DISABLE_AUTOUPDATER="1", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
        version = subprocess.run([CLI, "--version"], stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 env=env, cwd="/session/work", timeout=15)
        require(version.returncode == 0 and version.stdout.strip() == b"2.1.247 (Claude Code)",
                "cli-version-drift")
        self.process = subprocess.Popen(argv(self.session, command["resume"]), env=env,
            cwd="/session/work", stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=0, start_new_session=True)
        self.pidfd = os.pidfd_open(self.process.pid)
        self.start = start_time(self.process.pid)
        self.lines = Lines(self.process.stdout.fileno())
        request = uuid.uuid4().hex
        self.send(dict(type="control_request", request_id=request,
                       request=dict(subtype="initialize", hooks=None)))
        began = time.monotonic_ns()
        deadline = min(self.deadline, time.monotonic() + 30)
        while True:
            value = self.lines.next(deadline)
            if value.get("type") == "control_response":
                response = value.get("response", {})
                require(type(response) is dict and response.get("request_id") == request
                        and response.get("subtype") == "success", "initialize-rejected")
                break
            require(value.get("type") in ("system", "rate_limit_event"), "initialize-frame")
            if value.get("type") == "system" and value.get("subtype") == "init":
                require(value.get("session_id") == self.session, "init-session-changed")
                require(value.get("model") == ACTUAL_MODEL, "actual-model-drift")
                self.model = value["model"]
        return dict(event="initialized", initialize_ns=time.monotonic_ns() - began, **self.identity())

    def send(self, value):
        raw = json.dumps(value, separators=(",", ":")).encode() + b"\n"
        require(len(raw) <= 8192, "input-bound")
        written = self.process.stdin.write(raw)
        require(written == len(raw), "provider-write-incomplete")
        self.process.stdin.flush()

    def turn(self, command):
        self.identity()
        require(self.turns < self.limit, "user-turn-limit")
        prompt = command["prompt"]
        require(type(prompt) is str and len(prompt) <= 4096, "prompt-bound")
        self.turns += 1
        self.observe("provider-write-intent")
        self.lines.count = len(self.lines.buffer)
        self.send(dict(type="user", message=dict(role="user", content=prompt),
                       parent_tool_use_id=None, session_id=self.session))
        self.observe("provider-write-completed")
        deadline = min(self.deadline, time.monotonic() + TURN_SECONDS)
        while True:
            value = self.lines.next(deadline)
            kind = value.get("type")
            if kind == "system" and value.get("subtype") == "init":
                require(value.get("session_id") == self.session, "init-session-changed")
                require(value.get("model") == ACTUAL_MODEL, "actual-model-drift")
                self.model = value["model"]
            elif kind == "result":
                self.observe("provider-response-observed")
                self.observe("provider-result-validation", result=value)
                answer = result_projection(value, self.session)
                require(self.model == ACTUAL_MODEL, "actual-model-unobserved")
                return dict(event="complete", completed_ns=time.monotonic_ns(),
                            **answer, **{k: v for k, v in self.identity().items() if k != "session"})
            elif kind == "control_request":
                # No interactive permissions, hooks, MCP or unreviewed protocol fallback.
                raise Refusal("unexpected-control-request")
            else:
                require(kind in ("system", "assistant", "user", "stream_event", "rate_limit_event"),
                        "unrecognized-provider-frame")

    def command(self, command):
        operation = command.get("op")
        require(operation in OPERATIONS, "diagnostic-operation-invalid")
        self.operation = operation
        self.stage = "command-validation"
        if operation == "start":
            return self.initialize(command)
        if operation == "turn":
            return self.turn(command)
        if operation == "identity":
            return dict(event="identity", **self.identity())
        if operation == "probe":
            self.identity()
            try:
                descriptor = os.open("/output/solution.py", os.O_RDWR | os.O_NOFOLLOW)
            except OSError as error:
                return dict(event="probe", writable=False, errno=error.errno)
            else:
                os.close(descriptor)
                return dict(event="probe", writable=True, errno=0)
        raise Refusal("command-not-allowed")

    def close(self):
        if self.process is not None and self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=3)
        if self.pidfd is not None:
            os.close(self.pidfd)


def main():
    supervisor = Supervisor()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(Refusal("overall-timeout")))
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(Refusal("stopped")))
    try:
        require(os.getpid() == 1 and os.getuid() == 65532 and os.getgid() == 65532, "fixture-only")
        print(json.dumps(dict(event="ready", pid=1, uid=os.getuid(), gid=os.getgid())), flush=True)
        reader = Lines(sys.stdin.fileno())
        while True:
            command = reader.next(supervisor.deadline or time.monotonic() + 30)
            answer = supervisor.command(command)
            print(json.dumps(answer, allow_nan=False), flush=True)
    except BaseException as error:
        print(json.dumps(dict(event="refused", arm=supervisor.arm, operation=supervisor.operation,
              turn=supervisor.turns, stage=supervisor.stage, **refusal_projection(error))), flush=True)
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        supervisor.close()


if __name__ == "__main__":
    sys.exit(main())
