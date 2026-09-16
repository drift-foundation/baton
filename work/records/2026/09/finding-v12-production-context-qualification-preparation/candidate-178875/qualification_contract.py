"""Closed fixture contract. Importing this module performs no execution."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

IMAGE = "sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f"
MODEL = "claude-fable-5[1m]"
ACTUAL_MODEL = "claude-fable-5"
CLI_VERSION = "2.1.247"
GROUP = 1001
USER = "65532:65532"
SLOT = "/run/baton/credentials/claude"
HOME = "/run/baton/context/home"
LIMIT = 65536
STATE_BYTES = 32 * 1024 * 1024
STATE_FILES = 1024
STATE_DEPTH = 8
TURN_SECONDS = 180
OVERALL_SECONDS = 600
ACTIVE_SECONDS = 420
INITIAL = b"def scale(value):\n    return value * 2\n"
CORRECTED = b"def scale(value):\n    return value * 3\n"
KNOWN_FIELDS = frozenset(("type", "subtype", "is_error", "session_id", "model", "modelUsage", "api_error_status", "result", "duration_ms", "duration_api_ms", "num_turns", "total_cost_usd", "usage", "permission_denials", "uuid", "stop_reason"))
NONSUCCESS = frozenset(("error_during_execution", "error_max_turns", "error_max_budget_usd", "error_max_structured_output_retries"))


class Refusal(Exception):
    """Only fixture-authored constant codes may be exported."""


REFUSAL_CODES = frozenset(('event-bound', 'cleanup-ambiguous', 'cleanup-identity', 'cleanup-network-ambiguous', 'cleanup-network-identity', 'cleanup-unstarted', 'correction-artifact', 'created-identity', 'credential-link-drift', 'credential-link-missing', 'credential-source-boundary', 'duplicate-json-key', 'engine-deadline', 'engine-output-bound', 'engine-refused', 'engine-timeout', 'file-boundary', 'file-size-drift', 'first-turn-unsuccessful', 'fixture-drift', 'foreign-session-state', 'home-boundary', 'image-not-local-or-drift', 'initial-artifact', 'inspect-shape', 'invalid-json', 'invocation-shape', 'json-bound', 'manager-group', 'manifest-constants', 'manifest-digest', 'manifest-file-set', 'mount-path', 'mount-propagation', 'network-identity', 'nonfinite-json', 'owner-selection-required', 'project-key-ambiguous', 'provider-output-bound', 'provider-timeout', 'replacement-before-shutdown', 'request-shape', 'restored-subset-drift', 'runtime-identity', 'runtime-mounts', 'runtime-posture', 'second-turn-unsuccessful', 'selected-session-file-missing', 'session-shape', 'shutdown-receipt', 'shutdown-unconfirmed', 'state-byte-bound', 'state-copy-drift', 'state-depth', 'state-entry-bound', 'state-hardlink', 'state-type', 'terminal-object', 'terminal-record-shape', 'terminal-record-values', 'token-shape', 'turn-shape', 'unclassified', 'unexpected-credential-entry', 'worker-failure-shape', 'worker-identity', 'worker-observation', 'worker-record-shape'))

def failure_code(error):
    code = error.args[0] if type(error) is Refusal and len(error.args) == 1 else None
    return code if type(code) is str and code in REFUSAL_CODES else "unclassified"


def require(condition, code):
    if not condition:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def decoded(raw, limit=LIMIT):
    require(len(raw) <= limit, "json-bound")

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate-json-key")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(Refusal("nonfinite-json")))
    except (ValueError, UnicodeError, RecursionError):
        raise Refusal("invalid-json") from None


def valid_session(session):
    require(type(session) is str and str(uuid.UUID(session)) == session, "session-shape")


def prompt(turn, token=None):
    if turn == 1:
        require(type(token) is str and re.fullmatch(r"[0-9a-f]{32}", token), "token-shape")
        return ("Work only in /output. Remember this private continuity token in the conversation, "
                "but do not write it to any workspace file: " + token + ". "
                "Create only solution.py with exactly these bytes:\n" + INITIAL.decode() +
                "Do not create any other file. Finish now.")
    require(turn == 2 and token is None, "turn-shape")
    return ("Continue the earlier task in /output. Replace solution.py with exactly these bytes:\n" +
            CORRECTED.decode() + "Create continuity.txt containing only the private continuity token "
            "you were asked to remember, with a trailing newline. No other files. Finish now.")


def argv(session, turn, text):
    valid_session(session)
    require(type(turn) is int and turn in (1, 2) and type(text) is str and len(text.encode()) < LIMIT, "invocation-shape")
    return ["claude", "--print", "--dangerously-skip-permissions", "--output-format", "json", "--model", MODEL,
            "--session-id" if turn == 1 else "--resume", session, text]


def environment():
    return {"HOME": HOME, "PATH": "/usr/local/bin:/usr/bin:/bin", "TMPDIR": "/tmp/turn/tmp",
            "XDG_CACHE_HOME": "/tmp/turn/cache", "PYTHONPYCACHEPREFIX": "/tmp/turn/pycache"}


def projection(raw, session):
    value = decoded(raw)
    require(type(value) is dict, "terminal-object")
    subtype = value.get("subtype")
    shape = "missing" if "subtype" not in value else "wrong-type" if type(subtype) is not str else "success" if subtype == "success" else "known-nonsuccess" if subtype in NONSUCCESS else "unknown"
    error = "missing" if "is_error" not in value else "false" if value["is_error"] is False else "true" if value["is_error"] is True else "wrong-type"
    same = value.get("session_id") == session
    model_fields = []
    if value.get("model") == ACTUAL_MODEL:
        model_fields.append("model")
    usage = value.get("modelUsage")
    if type(usage) is dict and set(usage) == {ACTUAL_MODEL}:
        model_fields.append("modelUsage")
    conflicting = ("model" in value and value["model"] != ACTUAL_MODEL) or ("modelUsage" in value and (type(usage) is not dict or set(usage) != {ACTUAL_MODEL}))
    api = value.get("api_error_status")
    return {"members": sorted(set(value) & KNOWN_FIELDS), "unknown_member_hashes": sorted(sha(k.encode()) for k in set(value) - KNOWN_FIELDS),
            "type": "result" if value.get("type") == "result" else "unrecognized", "subtype": shape,
            "is_error": error, "session_matches": same, "session_id": session if same else None,
            "actual_model": ACTUAL_MODEL if model_fields and not conflicting else None, "model_fields": model_fields,
            "api_error_status": api if type(api) is int and 100 <= api <= 599 else None}


def success(record):
    return record["type"] == "result" and record["subtype"] == "success" and record["is_error"] == "false" and record["session_matches"]


def read_file(path, limit=LIMIT):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= limit, "file-boundary")
        result = bytearray()
        while len(result) <= limit:
            piece = os.read(fd, min(65536, limit + 1 - len(result)))
            if not piece:
                break
            result.extend(piece)
        require(len(result) <= limit and len(result) == info.st_size, "file-size-drift")
        return bytes(result)
    finally:
        os.close(fd)


def inventory(home):
    """Protected metadata, collected only after the owning runtime stopped.

    Reject links/hardlinks and credential-shaped entries before opening files.
    The one expected credential link is checked by readlink, never opened.
    Unknown configuration is listed by metadata, not made restorable state.
    """
    home = Path(home)
    require(stat.S_ISDIR(home.lstat().st_mode), "home-boundary")
    rows = []
    total = 0

    def walk(place, depth):
        nonlocal total
        require(depth <= STATE_DEPTH, "state-depth")
        with os.scandir(place) as entries:
            for entry in entries:
                require(len(rows) < STATE_FILES, "state-entry-bound")
                relative = str(Path(entry.path).relative_to(home))
                info = entry.stat(follow_symlinks=False)
                if relative == ".claude/.credentials.json":
                    require(stat.S_ISLNK(info.st_mode) and os.readlink(entry.path) == SLOT, "credential-link-drift")
                    rows.append({"path": relative, "type": "expected-credential-link", "size": None, "sha256": None, "uid": info.st_uid, "gid": info.st_gid, "mode": oct(stat.S_IMODE(info.st_mode))})
                    continue
                require(not re.search(r"credential|oauth|auth[-_.]?token|api[-_.]?key", entry.name, re.I), "unexpected-credential-entry")
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), "state-type")
                row = {"path": relative, "type": "directory" if stat.S_ISDIR(info.st_mode) else "file", "size": info.st_size, "sha256": None, "uid": info.st_uid, "gid": info.st_gid, "mode": oct(stat.S_IMODE(info.st_mode))}
                rows.append(row)
                if stat.S_ISDIR(info.st_mode):
                    walk(entry.path, depth + 1)
                else:
                    require(info.st_nlink == 1, "state-hardlink")
                    total += info.st_size
                    require(total <= STATE_BYTES, "state-byte-bound")
                    # Home configuration may contain authentication metadata;
                    # it is never opened or selected by this fixture.
                    if relative != ".claude.json":
                        row["sha256"] = sha(read_file(entry.path, STATE_BYTES))
    walk(home, 0)
    require(sum(row["type"] == "expected-credential-link" for row in rows) == 1, "credential-link-missing")
    return sorted(rows, key=lambda row: row["path"])


def subset(rows, session):
    valid_session(session)
    prefix = ".claude/projects/"
    projects = [r["path"] for r in rows if r["type"] == "directory" and r["path"].startswith(prefix) and len(r["path"].split("/")) == 3]
    require(len(projects) == 1, "project-key-ambiguous")
    path = projects[0] + "/" + session + ".jsonl"
    require(not any(r["type"] == "file" and r["path"].startswith(prefix) and r["path"].endswith(".jsonl") and r["path"] != path for r in rows), "foreign-session-state")
    selected = [r for r in rows if r["path"] == path and r["type"] == "file" and r["size"] > 0]
    require(len(selected) == 1, "selected-session-file-missing")
    # No adaptive nested-state copying or foreign session selection.
    return selected


def public_inventory(rows):
    return [{"path_sha256": sha(row["path"].encode()), **{key: row[key] for key in ("type", "size", "sha256", "uid", "gid", "mode")}} for row in rows]


def stopped(inspect, container, nonce):
    require(inspect["Id"] == container and inspect["Image"] == IMAGE and inspect["Config"]["Labels"].get("baton.qualification") == nonce, "runtime-identity")
    state = inspect["State"]
    require(state["Running"] is False and state["Pid"] == 0 and state["Status"] == "exited", "shutdown-unconfirmed")
    return {"container": container, "nonce": nonce, "running": False, "pid": 0, "exit_code": state["ExitCode"], "consumed": False}


def consume(receipt):
    require(receipt["consumed"] is False and receipt["running"] is False and receipt["pid"] == 0, "shutdown-receipt")
    receipt["consumed"] = True


def may_restore(receipt):
    require(receipt and receipt["consumed"] is True and receipt["running"] is False and receipt["pid"] == 0, "replacement-before-shutdown")
