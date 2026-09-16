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
# Owner179142, from review 2026-09-15T15-16-11Z: an artifact is accepted as the
# expected constant, or as that constant with its ONE final LF absent. Those two
# forms and no others. See `artifact_form` for what this deliberately still
# refuses; `continuity.txt` keeps its exact token-plus-LF contract.
ARTIFACT_FORMS = frozenset(("exact", "missing-final-lf"))
MODEL_KEY_CAP = 8
MODEL_DIAGNOSTICS = frozenset(("missing", "wrong-type", "expected", "other-string"))
MODEL_USAGE_DIAGNOSTICS = frozenset(("missing", "wrong-type", "empty-object", "expected-only", "other-only", "expected-plus-other"))
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
    """Explicit byte boundaries, per review 2026-09-15T15-16-11Z.

    The old wording ran the expected bytes straight into the next sentence, so
    where the content ended was a matter of reading. Markers make that exact,
    and the optional final newline is stated rather than left to be guessed.
    WORDING IS NOT ACCEPTANCE: a prompt cannot guarantee compliance, and the
    two accepted forms in `artifact_form` are what actually decides. The
    `continuity.txt` sentence is made equally explicit and its exact
    token-plus-one-LF contract is UNCHANGED.
    """
    if turn == 1:
        require(type(token) is str and re.fullmatch(r"[0-9a-f]{32}", token), "token-shape")
        return ("Work only in /output. Remember this private continuity token in the conversation, "
                "but do not write it to any workspace file: " + token + ". "
                "Create only solution.py. Its content is exactly the lines between the two markers "
                "below and nothing else; a final newline after the last line is optional.\n"
                "<<<BEGIN>>>\n" + INITIAL.decode() + "<<<END>>>\n"
                "Do not create any other file. Finish now.")
    require(turn == 2 and token is None, "turn-shape")
    return ("Continue the earlier task in /output. Replace solution.py so that its content is "
            "exactly the lines between the two markers below and nothing else; a final newline "
            "after the last line is optional.\n"
            "<<<BEGIN>>>\n" + CORRECTED.decode() + "<<<END>>>\n"
            "Also create continuity.txt whose content is exactly the private continuity token you "
            "were asked to remember followed by one newline character, and nothing else. "
            "Do not create any other file. Finish now.")


def artifact_form(raw, expected):
    """The expected bytes, or the expected bytes without their one final LF.

    THOSE TWO FORMS AND NO OTHERS. The failed run179075 produced the expected
    38 bytes with its final newline absent, and the exact-byte guard refused
    correctly -- requiring that newline was simply not part of the question
    this experiment asks. Owner179142 removed that one sensitivity and nothing
    else, so this is a bounded acceptance decision rather than a repair.

    Still refused, deliberately: an EXTRA final LF, any leading whitespace,
    horizontal trailing whitespace, altered indentation, an altered multiplier,
    an added comment, CRLF line endings anywhere. There is no `strip()`, no
    Unicode normalization, no AST equivalence and no general whitespace
    tolerance here, and adding one later would need its own selection.
    """
    if raw == expected:
        return "exact"
    if expected.endswith(b"\n") and raw == expected[:-1]:
        return "missing-final-lf"
    return "mismatch"


def artifact_record(raw, expected):
    """Closed artifact projection, recorded BEFORE any refusal.

    Observed and expected digests are named apart. While equality was exact a
    constant digest was the observed one; under two accepted forms it is not,
    and exporting `sha(INITIAL)` under an observed-sounding name would be a
    false record of what the provider wrote. No file content is exported.
    """
    return {"form": artifact_form(raw, expected), "observed_sha256": sha(raw), "observed_bytes": len(raw),
            "expected_sha256": sha(expected), "expected_bytes": len(expected)}


def token_record(raw, expected):
    """continuity.txt carries the PRIVATE token, so this record carries no digest.

    Its contract is unchanged and exact: the token followed by one newline.
    Lengths and a verdict are enough to diagnose a failure without turning a
    secret into an exported digest.
    """
    return {"form": "exact" if raw == expected else "mismatch",
            "observed_bytes": len(raw), "expected_bytes": len(expected)}


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
            **model_diagnostics(value, usage),
            "api_error_status": api if type(api) is int and 100 <= api <= 599 else None}


def model_diagnostics(value, usage):
    """WHY a model did not qualify, never WHICH model it was.

    The failed run179075 recorded `actual_model: null` and `model_fields: []`
    with `modelUsage` present, and that projection cannot say whether the
    member held a non-object, an empty object, one other key or several. The
    original provider JSON was read from an anonymous bounded pipe and never
    retained, so nothing can recover the distinction after the fact -- these
    members exist so the NEXT run does not lose it again.

    THE ACCEPTANCE PREDICATE ABOVE IS UNTOUCHED. An expected key inside a mixed
    object does not qualify a model, and neither does the matching `--model`
    argument; missing, wrong-type, conflicting and other-only stay unqualified.
    No arbitrary key name, value, usage payload, provider prose or raw JSON is
    exported: other keys are reported only as a bounded count with an explicit
    overflow flag.
    """
    model = ("missing" if "model" not in value else
             "wrong-type" if type(value["model"]) is not str else
             "expected" if value["model"] == ACTUAL_MODEL else "other-string")
    if "modelUsage" not in value:
        return {"model_diagnostic": model, "model_usage_diagnostic": "missing",
                "model_usage_keys": None, "model_usage_keys_capped": None, "model_usage_expected_key": None}
    if type(usage) is not dict:
        return {"model_diagnostic": model, "model_usage_diagnostic": "wrong-type",
                "model_usage_keys": None, "model_usage_keys_capped": None, "model_usage_expected_key": None}
    keys = set(usage)
    present = ACTUAL_MODEL in keys
    others = len(keys) - (1 if present else 0)
    shape = ("empty-object" if not keys else "expected-only" if present and not others else
             "expected-plus-other" if present else "other-only")
    return {"model_diagnostic": model, "model_usage_diagnostic": shape,
            "model_usage_keys": min(len(keys), MODEL_KEY_CAP), "model_usage_keys_capped": len(keys) > MODEL_KEY_CAP,
            "model_usage_expected_key": present}


# Each modelUsage diagnostic pinned to the observation it claims to describe:
# whether the known member was present, whether the expected key was among its
# keys, and the inclusive count range that shape can actually have. `None`
# bounds mean the shape reports no counts at all.
#
# R1, review 2026-09-15T15-39-27Z. The first version of `consistent` checked
# types, ranges and boolean identity and then never related the terms to each
# other, so `expected-only` could report two keys, or overflow at one key, and
# still be admitted as an internally consistent qualification report. A guard
# that type-checks a vocabulary without relating its terms is not a guard.
USAGE_SHAPES = {
    "missing": {"member": False, "expected_key": None, "low": None, "high": None},
    "wrong-type": {"member": True, "expected_key": None, "low": None, "high": None},
    "empty-object": {"member": True, "expected_key": False, "low": 0, "high": 0},
    "expected-only": {"member": True, "expected_key": True, "low": 1, "high": 1},
    "other-only": {"member": True, "expected_key": False, "low": 1, "high": MODEL_KEY_CAP},
    "expected-plus-other": {"member": True, "expected_key": True, "low": 2, "high": MODEL_KEY_CAP},
}
# Only these can hold more keys than the cap, so only these may report overflow.
# Named rather than derived from `high == MODEL_KEY_CAP` for explicitness: at
# MODEL_KEY_CAP 8 the two forms are exactly equivalent, and a reversal probe
# confirmed the substitution changes no behaviour, so this is a readability
# choice and not a guard against a reachable fault.
OVERFLOW_SHAPES = frozenset(("other-only", "expected-plus-other"))


def consistent(record):
    """The diagnostic members must agree with each other AND with the verdict.

    A forged or drifted record cannot report a conflict and claim a qualified
    model in the same breath, and it cannot claim a cardinality its own shape
    excludes. Boolean checks are identity-based on purpose: `1 in (None, True,
    False)` is true in Python, so a truthy integer would pass a membership test
    where a boolean is required.

    This validates the emitted projection's finite vocabulary. It infers no
    unknown model name and qualifies no mixed `modelUsage`: the actual-model
    predicate above is untouched and is the only thing that accepts a model.
    """
    if type(record["members"]) is not list or type(record["model_fields"]) is not list:
        return False
    members, fields = set(record["members"]), set(record["model_fields"])
    model, usage = record["model_diagnostic"], record["model_usage_diagnostic"]
    if model not in MODEL_DIAGNOSTICS or usage not in USAGE_SHAPES:
        return False
    # A diagnostic ABOUT a member the closed member list says was absent is a
    # contradiction, not an observation -- and it was the fourth malformed
    # record that reached `qualified`.
    if ("model" in members) != (model != "missing"):
        return False
    shape = USAGE_SHAPES[usage]
    if ("modelUsage" in members) != shape["member"]:
        return False
    count, capped, present = record["model_usage_keys"], record["model_usage_keys_capped"], record["model_usage_expected_key"]
    if shape["low"] is None:
        if not (count is None and capped is None and present is None):
            return False
    else:
        if not (type(count) is int and shape["low"] <= count <= shape["high"]):
            return False
        if not ((capped is True or capped is False) and (present is True or present is False)):
            return False
        if present is not shape["expected_key"]:
            return False
        # Overflow means the count was CLAMPED, which can only happen at the cap
        # and only for a shape that can hold more keys than that.
        if capped and not (count == MODEL_KEY_CAP and usage in OVERFLOW_SHAPES):
            return False
    if not fields <= {"model", "modelUsage"}:
        return False
    if ("model" in fields) != (model == "expected"):
        return False
    if ("modelUsage" in fields) != (usage == "expected-only"):
        return False
    if record["actual_model"] not in (None, ACTUAL_MODEL):
        return False
    clean = model in ("missing", "expected") and usage in ("missing", "expected-only")
    return (record["actual_model"] == ACTUAL_MODEL) == bool(fields and clean)


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
