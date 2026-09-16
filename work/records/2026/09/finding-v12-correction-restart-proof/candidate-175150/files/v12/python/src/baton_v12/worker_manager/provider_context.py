"""Private provider contexts, derived from this manager's operation journal.

A context is neither an AgentSession nor permission to launch. A committed use
binds an ordinary implementation assignment; a ready generation additionally
requires accepted output, a fenced checkpoint and positively completed cleanup.
Production CLI qualification is intentionally unavailable in this first slice.
"""

import json
import os
import uuid

from ..contracts import ContractRefusal, canonical_text, check_no_durable_secret, digest, digest_of_bytes
from ..job_manager import ending, episodes, submission
from ..job_manager.store import job_signature
from . import attempts, boundaries, intake, manifests, output, review_cycles
from .store import manager_signature

PROFILE_KIND = "provider-context.profile"
TRANSITION_KIND = "provider-context.transition"
PROFILE_SCHEMA = "baton.claude-context-profile/1"
RECEIPT_SCHEMA = "baton.provider-context-receipt/1"
REASONS = frozenset(("runtime-unknown", "invocation-unknown", "receipt-invalid", "custody-invalid", "generation-damaged", "retired"))
_ACTION_KEYS = {
    "admit": ("identity", "attempt_id", "writer_id", "assignment", "stage_id", "episode", "profile_digest", "job_digest", "limits_digest", "repo_pin", "source_pin", "input_digest", "policy_digest", "generation", "conversation_id", "mode", "predecessor"),
    "deliver": ("delivery_digest", "pins"),
    "finalize": ("generation", "manifest_digest", "generation_pins", "receipt_digest", "checkpoint_id", "checkpoint_digest", "exclusion_digest"),
    "hold": ("reason", "evidence_refs"),
    "retire": ("reason", "evidence_refs"),
}


def _refuse(reason, *, durable=False):
    # Reasons are controlled literals. Private paths/provider data are not diagnostics.
    raise ContractRefusal("refused", "precondition", "provider context: " + reason, durable=durable)


def _document(value, required):
    check_no_durable_secret(value, what="provider context metadata")
    return boundaries.document(value, "provider context metadata", required=required)


def _id(prefix, value):
    return prefix + "-" + digest(value).split(":", 1)[1]


def _integer(value, minimum=0):
    if type(value) is not int or not minimum <= value <= 2**53 - 1:
        _refuse("invalid integer")
    return value


def _text(value):
    boundaries.identity(value, "provider context identity")
    if len(value) > 256:
        _refuse("identity exceeds its bound")
    return value


def _hash(value):
    if type(value) is not str or len(value) != 71 or not value.startswith("sha256:") or any(c not in "0123456789abcdef" for c in value[7:]):
        _refuse("invalid digest")
    return value


def _profile(value):
    held = _document(value, ("schema", "qualification", "evidence_digest", "cli_build", "image_digest", "adapter_digest", "runtime_profile_digest", "argv_policy_digest", "environment_policy_digest", "layout_version", "reported_model", "model", "cwd", "state_paths", "max_entries", "max_bytes", "retention_policy_digest"))
    if held["schema"] != PROFILE_SCHEMA or held["qualification"] != "deterministic":
        _refuse("production one-shot profile qualification is unavailable")
    for key in ("evidence_digest", "image_digest", "adapter_digest", "runtime_profile_digest", "argv_policy_digest", "environment_policy_digest", "retention_policy_digest"):
        _hash(held[key])
    for key in ("cli_build", "model", "reported_model", "layout_version"):
        _text(held[key])
    if held["cwd"] != "/output":
        _refuse("unsupported provider working directory")
    paths = held["state_paths"]
    if type(paths) is not list or not 1 <= len(paths) <= 64:
        _refuse("invalid positive state allowlist")
    if any(type(path) is not str for path in paths) or len(set(paths)) != len(paths):
        _refuse("invalid positive state allowlist")
    for path in paths:
        if type(path) is not str or len(path) > 512 or any(p in ("", ".", "..") for p in path.split("/")) or not path.startswith(".claude/projects/") or any(p in (".credentials.json", "invocation", "cache", "tmp") for p in path.split("/")):
            _refuse("state path is outside the qualified layout")
    if not 1 <= _integer(held["max_entries"]) <= 4096 or not 1 <= _integer(held["max_bytes"]) <= 64 * 1024 * 1024:
        _refuse("state ceiling exceeds the supported bound")
    return held


def certify_context_profile(control, profile):
    held = _profile(profile)
    key = digest(held)
    signature = manager_signature(PROFILE_KIND, held)
    return control.transact(_id("context-profile", key), PROFILE_KIND, signature, lambda connection: {"profile_digest": key, "profile": held})


def context_profile_of(control, profile_digest):
    key = _hash(profile_digest)
    row = control.operation_record(_id("context-profile", key))
    if row is None or row["kind"] != PROFILE_KIND or row["state"] != "committed":
        _refuse("profile is not certified")
    result = _document(json.loads(row["result"]), ("profile_digest", "profile"))
    profile = _profile(result["profile"])
    if result["profile_digest"] != key or digest(profile) != key or row["signature"] != manager_signature(PROFILE_KIND, profile):
        _refuse("profile journal disagrees")
    return profile


def _operation(action, context_id, use_id, revision):
    return _id("context-" + action, [context_id, use_id, revision])



def _payload(action, payload):
    held = _document(payload, _ACTION_KEYS[action])
    if action == "admit":
        identity = _document(held["identity"], ("authority_uuid", "job_id", "work_id", "line_id", "participant", "principal", "purpose"))
        for value in identity.values():
            _text(value)
        if identity["purpose"] != "implementation":
            _refuse("only implementation context is supported")
        for key in ("attempt_id", "writer_id", "stage_id"):
            _text(held[key])
        for key in ("profile_digest", "job_digest", "limits_digest", "input_digest", "policy_digest"):
            _hash(held[key])
        _integer(held["episode"], 1); _integer(held["generation"])
        _document(held["assignment"], ("runtime_attempt_id", "authority_uuid", "work_id", "participant", "generation", "principal", "effective_scope"))
        if held["assignment"]["runtime_attempt_id"] != held["attempt_id"] or any(held["assignment"][key] != identity[key] for key in ("authority_uuid", "work_id", "participant", "principal")):
            _refuse("admitted assignment identity disagrees")
        if held["conversation_id"] != str(uuid.uuid5(uuid.NAMESPACE_OID, _id("context", identity))):
            _refuse("admitted conversation identity disagrees")
        _pins(held["repo_pin"]); _pins(held["source_pin"])
        if held["predecessor"] is not None:
            _hash(held["predecessor"])
    elif action == "deliver":
        _hash(held["delivery_digest"])
        for pin in _document(held["pins"], ("owner", "use", "home")).values():
            _pins([pin])
    elif action == "finalize":
        _integer(held["generation"], 1)
        for key in ("manifest_digest", "receipt_digest", "checkpoint_digest", "exclusion_digest"):
            _hash(held[key])
        _text(held["checkpoint_id"])
        for pin in _document(held["generation_pins"], ("owner", "generation", "state")).values():
            _pins([pin])
    else:
        if type(held["reason"]) is not str or held["reason"] not in REASONS or type(held["evidence_refs"]) is not list or len(held["evidence_refs"]) > 16:
            _refuse("invalid closed hold or retirement")
        for value in held["evidence_refs"]:
            _hash(value)
    return held


def _pins(value):
    if type(value) is not list or not 1 <= len(value) <= 128:
        _refuse("invalid directory pin chain")
    for pair in value:
        if type(pair) is not list or len(pair) != 2:
            _refuse("invalid directory object pin")
        for number in pair:
            _integer(number)


def _history(control, context_id=None):
    # Only this owner reads its journal family. Refusals never advance the head.
    rows = control._connection.execute("SELECT operation_id FROM operations WHERE kind = ? ORDER BY rowid", (TRANSITION_KIND,)).fetchall()
    histories = {}
    for row_id in rows:
        row = control.operation_record(row_id["operation_id"])
        if row["state"] != "committed":
            continue
        value = _document(json.loads(row["result"]), ("action", "context_id", "use_id", "expected_revision", "revision", "previous_digest", "payload"))
        action = value["action"]
        if type(action) is not str or action not in _ACTION_KEYS:
            _refuse("unknown journal transition")
        _text(value["context_id"]); _text(value["use_id"])
        _integer(value["expected_revision"]); _integer(value["revision"], 1)
        _payload(action, value["payload"])
        if action == "admit" and (value["context_id"] != _id("context", value["payload"]["identity"]) or value["use_id"] != _id("context-use", [value["context_id"], value["payload"]["attempt_id"], value["payload"]["generation"]])):
            _refuse("context/use identity derivation disagrees")
        operands = {key: value[key] for key in value if key != "revision"}
        if row["signature"] != manager_signature(TRANSITION_KIND, operands) or row["operation_id"] != _operation(action, value["context_id"], value["use_id"], value["expected_revision"]):
            _refuse("transition identity disagrees")
        chain = histories.setdefault(value["context_id"], [])
        previous = chain[-1] if chain else None
        if value["expected_revision"] != len(chain) or value["revision"] != len(chain) + 1 or value["previous_digest"] != (digest(previous) if previous else None):
            _refuse("transition predecessor disagrees")
        _legal(previous, action, value["use_id"], value["payload"], chain)
        chain.append(value)
    if context_id is None:
        return histories
    return histories.get(context_id, [])


def _legal(previous, action, use_id, payload, chain):
    state = previous["action"] if previous else None
    if action == "admit":
        if state not in (None, "finalize") or any(x["action"] == "admit" and x["use_id"] == use_id for x in chain):
            _refuse("context already occupied or retired", durable=True)
        _integer(payload["generation"])
        if payload["generation"] != sum(x["action"] == "finalize" for x in chain):
            _refuse("generation predecessor disagrees")
        if payload["predecessor"] != (digest(previous) if previous else None):
            _refuse("admission predecessor disagrees")
        if payload["mode"] != ("restore" if payload["generation"] else "open"):
            _refuse("use mode disagrees")
    elif previous is None or previous["use_id"] != use_id:
        _refuse("transition names another active use", durable=True)
    elif action == "deliver" and state != "admit":
        _refuse("delivery is not admitted", durable=True)
    elif action == "finalize":
        if state != "deliver" or payload["generation"] != 1 + sum(one["action"] == "finalize" for one in chain):
            _refuse("finalization is not the next delivered generation", durable=True)
    elif action == "hold" and state not in ("admit", "deliver", "finalize"):
        _refuse("context is already held or retired", durable=True)
    elif action == "retire" and state != "finalize":
        _refuse("only an excluded finalized use can retire", durable=True)


def _transition(control, *, action, context_id, use_id, expected_revision, payload, check=None):
    _payload(action, payload)
    chain = _history(control, context_id)
    previous = next((one for one in chain if one["revision"] == expected_revision), None)
    operands = {"action": action, "context_id": context_id, "use_id": use_id, "expected_revision": expected_revision, "previous_digest": digest(previous) if previous else None, "payload": payload}
    signature = manager_signature(TRANSITION_KIND, operands)
    def act(connection):
        current = _history(control, context_id)
        if len(current) != expected_revision:
            _refuse("context revision changed", durable=True)
        _legal(current[-1] if current else None, action, use_id, payload, current)
        if check is not None:
            check()
        return dict(operands, revision=expected_revision + 1)
    return control.transact(_operation(action, context_id, use_id, expected_revision), TRANSITION_KIND, signature, act)


def _use(control, attempt_id):
    _text(attempt_id)
    found = [(chain, row) for chain in _history(control).values() for row in chain if row["action"] == "admit" and row["payload"]["attempt_id"] == attempt_id]
    if len(found) != 1:
        _refuse("attempt has no unique admitted context")
    return found[0]


def context_use_of(control, attempt_id):
    chain, admitted = _use(control, attempt_id)
    owned = [one for one in chain if one["use_id"] == admitted["use_id"]]
    result = {"context_id": admitted["context_id"], "use_id": admitted["use_id"], "attempt_id": attempt_id, "status": {"admit": "admitted", "deliver": "admitted", "finalize": "ready", "hold": "held", "retire": "retired"}[owned[-1]["action"]], "generation": admitted["payload"]["generation"], "revision": owned[-1]["revision"], "reason": owned[-1]["payload"].get("reason")}
    if owned[-1]["action"] == "finalize":
        from .context_delivery import configured_context_storage, validate_generation
        try:
            validate_generation(control, configured_context_storage(control), admitted["context_id"], owned[-1]["payload"])
        except ContractRefusal:
            result.update(status="held", reason="generation-damaged")
    return result


def context_of(control, context_id):
    _text(context_id)
    chain = _history(control, context_id)
    if not chain:
        return {"context_id": context_id, "status": "unavailable"}
    admitted = next(one for one in reversed(chain) if one["action"] == "admit")
    return context_use_of(control, admitted["payload"]["attempt_id"])


def _job_attempt(jobs, attempt_id):
    matches = [(stage, episode) for stage in submission.stage_rows(jobs) for episode in episodes.episodes_of(jobs, stage["stage_id"]) if episode["attempt_id"] == attempt_id]
    if len(matches) != 1 or matches[0][0]["kind"] != "implementation":
        _refuse("attempt is not a unique implementation episode")
    stage, episode = matches[0]
    return stage, episode, submission.job_of(jobs, stage["job_id"])


def _facts(control, jobs, authority, attempt_id, writer_id, profile_digest, *, live):
    profile = context_profile_of(control, profile_digest)
    assignment = attempts.assignment_of(control, attempt_id)
    stage, episode, job = _job_attempt(jobs, attempt_id)
    writer = review_cycles.writer_for_attempt(control, attempt_id=attempt_id, generation=assignment["generation"])
    if writer is None or writer["writer_id"] != writer_id:
        _refuse("attempt does not own the named writer")
    line = review_cycles.line_of(control, writer["line_id"])
    if assignment["authority_uuid"] != jobs.authority_uuid or stage["work_id"] != assignment["work_id"] or line["work_id"] != assignment["work_id"] or line["authority_uuid"] != jobs.authority_uuid or writer["participant"] != assignment["participant"] or writer["principal"] != assignment["principal"]:
        _refuse("assignment, Job and line disagree")
    if stage["profile_digest"] != profile["runtime_profile_digest"]:
        _refuse("runtime profile changed")
    runtime = attempts._require_attempt(control, attempt_id)
    if runtime["profile_digest"] != profile["runtime_profile_digest"] or runtime["adapter_digest"] != profile["adapter_digest"] or runtime["image_digest"] != profile["image_digest"]:
        _refuse("actual runtime profile or adapter changed")
    expected = {"work_ref": {"authority_uuid": assignment["authority_uuid"], "work_id": assignment["work_id"]}, "participant": assignment["participant"], "generation": assignment["generation"]}
    if live and (episode["ended_state"] is not None or writer["state"] != "active" or authority.assignment_of(assignment["work_id"], jobs.authority_uuid) != expected):
        _refuse("implementation assignment is no longer live")
    # The private repository object is pinned by the line owner. Open its entire
    # ancestry without links, then compare the final descriptor to that pin.
    from .context_delivery import _open_absolute
    fd, pins = _open_absolute(line["line_path"])
    try:
        info = os.fstat(fd)
        if [info.st_dev, info.st_ino] != [line["line_device"], line["line_inode"]]:
            _refuse("private repository object changed")
    finally:
        os.close(fd)
    source_fd, source_pins = _open_absolute(line["source_path"])
    os.close(source_fd)
    if source_pins[-1] != [line["source_device"], line["source_inode"]]:
        _refuse("source object changed")
    identity = {"authority_uuid": jobs.authority_uuid, "job_id": job["job_id"], "work_id": assignment["work_id"], "line_id": line["line_id"], "participant": assignment["participant"], "principal": assignment["principal"], "purpose": "implementation"}
    return {"identity": identity, "attempt_id": attempt_id, "writer_id": writer_id, "assignment": assignment, "stage_id": stage["stage_id"], "episode": episode["episode"], "profile_digest": profile_digest, "job_digest": digest(job), "limits_digest": digest(submission.execution_limits_of(jobs, job["job_id"])), "repo_pin": pins, "source_pin": source_pins, "input_digest": runtime["input_digest"], "policy_digest": runtime["policy_digest"]}


def admit_context_use(control, jobs, authority, *, attempt_id, writer_id, profile_digest):
    _text(attempt_id); _text(writer_id); _hash(profile_digest)
    request_kind = "provider-context.admission-request"
    request_id = _id("context-admission-request", attempt_id)
    request_operands = {"attempt_id": attempt_id, "writer_id": writer_id, "profile_digest": profile_digest}
    request_signature = manager_signature(request_kind, request_operands)
    request_found, request = control.replay(request_id, request_signature, kind=request_kind)
    if request_found:
        request = _document(request, ("context_id", "use_id", "revision", "payload"))
        _payload("admit", request["payload"])
        if any(request["payload"][key] != value for key, value in request_operands.items()):
            _refuse("admission request journal disagrees")
        operands = {"action": "admit", "context_id": request["context_id"], "use_id": request["use_id"], "expected_revision": request["revision"], "previous_digest": request["payload"]["predecessor"], "payload": request["payload"]}
        found, unused = control.replay(_operation("admit", request["context_id"], request["use_id"], request["revision"]), manager_signature(TRANSITION_KIND, operands), kind=TRANSITION_KIND)
        if found:
            return context_use_of(control, attempt_id)
        # A crash between request binding and transition retains that exact
        # expected predecessor; a later head cannot silently mint another use.
        facts = _facts(control, jobs, authority, attempt_id, writer_id, profile_digest, live=True)
        if any(facts[key] != request["payload"][key] for key in facts):
            _refuse("admission request owner facts changed")
        _transition(control, action="admit", context_id=request["context_id"], use_id=request["use_id"], expected_revision=request["revision"], payload=request["payload"], check=lambda: _facts(control, jobs, authority, attempt_id, writer_id, profile_digest, live=True))
        return context_use_of(control, attempt_id)
    existing = [row for chain in _history(control).values() for row in chain if row["action"] == "admit" and row["payload"]["attempt_id"] == attempt_id]
    if existing:
        row = existing[0]
        if row["payload"]["writer_id"] != writer_id or row["payload"]["profile_digest"] != profile_digest:
            _refuse("admission replay operands changed")
        # Adoption is not new launch authority; the serving consumer must repeat
        # its live checks immediately before an unstarted runtime is launched.
        return context_use_of(control, attempt_id)
    facts = _facts(control, jobs, authority, attempt_id, writer_id, profile_digest, live=True)
    context_id = _id("context", facts["identity"])
    for other in _history(control).values():
        first = other[0]["payload"]["identity"]
        if first["line_id"] == facts["identity"]["line_id"] and first != facts["identity"]:
            _refuse("private line cannot implicitly change context owner")
    chain = _history(control, context_id)
    predecessor = chain[-1] if chain else None
    generation = sum(one["action"] == "finalize" for one in chain)
    if predecessor is not None:
        initial = next(one for one in chain if one["action"] == "admit")["payload"]
        if any(facts[key] != initial[key] for key in ("profile_digest", "job_digest", "limits_digest", "repo_pin", "source_pin")):
            _refuse("context identity or pinned profile changed")
        if predecessor["action"] == "finalize":
            from .context_delivery import configured_context_storage, validate_generation
            validate_generation(control, configured_context_storage(control), context_id, predecessor["payload"])
            checkpoint = predecessor["payload"]["checkpoint_id"]
            row = jobs.operation_record(episodes.correction_operation_id(facts["identity"]["job_id"], checkpoint))
            if row is None or row["state"] != "committed" or row["kind"] != episodes.CORRECT_KIND:
                _refuse("no owner-committed correction")
            operands = json.loads(row["signature"])["operands"]
            verdict = review_cycles.verdict_of(control, operands["verdict_id"])
            if verdict["checkpoint_id"] != checkpoint or verdict["disposition"] != "changes-requested":
                _refuse("correction verdict disagrees")
            old = next(one for one in reversed(chain) if one["action"] == "admit")["payload"]
            if ending.settlement_of(jobs, old["stage_id"], old["episode"]) is None:
                _refuse("previous implementation ending is unsettled")
            if row["signature"] != job_signature(episodes.CORRECT_KIND, operands) or operands["job_id"] != facts["identity"]["job_id"] or operands["line_id"] != facts["identity"]["line_id"]:
                _refuse("correction owner operands disagree")
            recorded = json.loads(row["result"])
            if recorded["implementation"]["attempt_id"] != attempt_id or recorded["implementation"]["episode"] != facts["episode"]:
                _refuse("correction did not open this attempt")
    payload = dict(facts, generation=generation, mode="restore" if generation else "open", predecessor=digest(predecessor) if predecessor else None, conversation_id=str(uuid.uuid5(uuid.NAMESPACE_OID, context_id)))
    use_id = _id("context-use", [context_id, attempt_id, generation])
    request = control.transact(request_id, request_kind, request_signature, lambda connection: {"context_id": context_id, "use_id": use_id, "revision": len(chain), "payload": payload})
    if request != {"context_id": context_id, "use_id": use_id, "revision": len(chain), "payload": payload}:
        # Another caller already pinned this attempt's exact request. Re-enter
        # its replay branch rather than compute a new operation identity.
        return admit_context_use(control, jobs, authority, attempt_id=attempt_id, writer_id=writer_id, profile_digest=profile_digest)
    def check():
        if _facts(control, jobs, authority, attempt_id, writer_id, profile_digest, live=True) != facts:
            _refuse("admission owner facts changed", durable=True)
    _transition(control, action="admit", context_id=context_id, use_id=use_id, expected_revision=len(chain), payload=payload, check=check)
    return context_use_of(control, attempt_id)


def hold_context_use(control, *, attempt_id, reason, evidence_refs):
    if type(reason) is not str or reason not in REASONS or type(evidence_refs) is not list or len(evidence_refs) > 16:
        _refuse("invalid hold reason or evidence")
    for value in evidence_refs:
        _hash(value)
    chain, admitted = _use(control, attempt_id)
    head = chain[-1]
    if head["action"] == "hold" and head["use_id"] == admitted["use_id"] and head["payload"] == {"reason": reason, "evidence_refs": evidence_refs}:
        return context_use_of(control, attempt_id)
    _transition(control, action="hold", context_id=admitted["context_id"], use_id=admitted["use_id"], expected_revision=len(chain), payload={"reason": reason, "evidence_refs": evidence_refs})
    return context_use_of(control, attempt_id)


def retire_context(control, context_id):
    chain = _history(control, context_id)
    if not chain:
        _refuse("context is absent")
    head = chain[-1]
    if head["action"] != "retire":
        _transition(control, action="retire", context_id=context_id, use_id=head["use_id"], expected_revision=len(chain), payload={"reason": "retired", "evidence_refs": [digest(head)]})
    return context_of(control, context_id)


def _receipt(control, admitted, reader):
    facts = admitted["payload"]
    attempt_id = facts["attempt_id"]
    frozen = output.frozen_output_of(control, attempt_id)
    collected = intake.intake_receipt_of(control, attempt_id)
    if frozen is None or collected is None or collected["custody"] != "accepted" or any(frozen[key] != collected[key] for key in ("result_id", "manifest_digest")):
        _refuse("receipt has no matching accepted custody")
    manifest = manifests.load_manifest(control, frozen["manifest_digest"], "resultManifest")
    candidates = [one for one in manifest["outputs"] if one["name"] == "provider-context-receipt" and one["status"] == "present"]
    if len(candidates) != 1:
        _refuse("mandatory context receipt is missing")
    candidate = candidates[0]
    entries = candidate["content_manifest"]["entries"]
    if len(entries) != 1 or entries[0]["path"] != "receipt.json" or entries[0]["bytes"] > 16384:
        _refuse("receipt is not one bounded sealed file")
    artifact = candidate["artifact"]
    retained_ids = {one["artifact_id"] for one in intake.retentions_of(control, attempt_id) if one["disposition"] == "retain"}
    if artifact is None or artifact["artifact_id"] not in retained_ids:
        _refuse("context receipt was not retained")
    if artifact is None or not any(one["artifact_id"] == artifact["artifact_id"] and one["content_digest"] == artifact["content_digest"] and one["bytes"] == artifact["bytes"] for one in collected["artifacts"]) or not any(one["artifact_id"] == artifact["artifact_id"] and one["content_digest"] == artifact["content_digest"] for one in frozen["artifacts"]):
        _refuse("receipt artifact is not indexed and accepted")
    boundaries.capability(reader, "the retained context receipt byte reader")
    body = reader(attempt_id, artifact["artifact_id"])
    if type(body) is not bytes or len(body) != entries[0]["bytes"] or digest_of_bytes(body) != entries[0]["content_digest"]:
        _refuse("receipt bytes disagree with frozen custody")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _refuse("duplicate receipt member")
            result[key] = value
        return result
    try:
        raw = json.loads(body, object_pairs_hook=pairs)
    except (ValueError, UnicodeError):
        _refuse("receipt is not complete JSON")
    value = _document(raw, ("schema", "context_id", "use_id", "attempt_id", "conversation_id", "profile_digest", "invocation_id", "status", "complete", "model", "observed_model", "terminal", "cli_build", "mode", "delivery_digest", "input_digest", "policy_digest"))
    profile = context_profile_of(control, facts["profile_digest"])
    delivered = next(one for one in _history(control, admitted["context_id"]) if one["action"] == "deliver" and one["use_id"] == admitted["use_id"])
    expected = {"model": profile["model"], "observed_model": profile["reported_model"], "terminal": "success", "cli_build": profile["cli_build"], "mode": facts["mode"], "delivery_digest": delivered["payload"]["delivery_digest"], "input_digest": facts["input_digest"], "policy_digest": facts["policy_digest"], "schema": RECEIPT_SCHEMA, "context_id": admitted["context_id"], "use_id": admitted["use_id"], "attempt_id": attempt_id, "conversation_id": facts["conversation_id"], "profile_digest": facts["profile_digest"], "invocation_id": _id("context-invocation", admitted["use_id"])}
    if any(value[key] != wanted for key, wanted in expected.items()) or type(value["status"]) is not int or value["status"] != 0 or value["complete"] is not True:
        _refuse("receipt does not prove this healthy invocation")
    assignment = facts["assignment"]
    expected_assignment = {"work_ref": {"authority_uuid": assignment["authority_uuid"], "work_id": assignment["work_id"]}, "participant": assignment["participant"], "generation": assignment["generation"]}
    if manifest["assignment_ref"] != expected_assignment or collected["assignment"] != expected_assignment or manifest["input_manifest_digest"] != facts["input_digest"] or manifest["policy_digest"] != facts["policy_digest"]:
        _refuse("receipt belongs to another assignment")
    return digest_of_bytes(body)


def _finalize_context_use(control, jobs, authority, *, attempt_id, storage, receipt_reader, checkpoint_reader):
    """Historical owner reads; never ask Authority for a fresh admission here."""
    from . import context_delivery
    chain, admitted = _use(control, attempt_id)
    own = [one for one in chain if one["use_id"] == admitted["use_id"]]
    if own[-1]["action"] in ("hold", "retire"):
        _refuse("context use is held or retired")
    finalized = next((one for one in own if one["action"] == "finalize"), None)
    if finalized is not None:
        context_delivery.validate_generation(control, storage, admitted["context_id"], finalized["payload"])
        return context_use_of(control, attempt_id)
    facts = admitted["payload"]
    current = _facts(control, jobs, authority, attempt_id, facts["writer_id"], facts["profile_digest"], live=False)
    if any(current[key] != facts[key] for key in current):
        _refuse("historical use owner facts changed")
    profile = context_profile_of(control, facts["profile_digest"])
    cleanup = intake.cleanup_of(control, attempt_id=attempt_id, retention_policy_digest=profile["retention_policy_digest"])
    runtime = attempts.attempt_runtime_of(control, attempt_id)
    if cleanup is None or runtime is None or cleanup["state"] != "absent" or cleanup["cleanup"] not in ("complete", "retained") or runtime["execution_runtime"] != "destroyed":
        _refuse("old runtime exclusion is unproved")
    writer = review_cycles.writer_of(control, facts["writer_id"])
    boundaries.capability(checkpoint_reader, "the historical checkpoint identity reader")
    checkpoint = review_cycles.checkpoint_of(control, checkpoint_reader(attempt_id, writer["writer_id"]))
    if writer["state"] != "revoked" or checkpoint["writer_id"] != writer["writer_id"] or checkpoint["state"] != "frozen" or checkpoint["fence"] is None:
        _refuse("old writer checkpoint is not fenced")
    try:
        receipt_digest = _receipt(control, admitted, receipt_reader)
    except ContractRefusal:
        hold_context_use(control, attempt_id=attempt_id, reason="receipt-invalid", evidence_refs=[digest(admitted)])
        raise
    sealed = context_delivery.seal_generation(control, storage, attempt_id=attempt_id, exclusion=cleanup)
    payload = dict(sealed, receipt_digest=receipt_digest, checkpoint_id=checkpoint["checkpoint_id"], checkpoint_digest=checkpoint["checkpoint_digest"], exclusion_digest=digest(cleanup))
    _transition(control, action="finalize", context_id=admitted["context_id"], use_id=admitted["use_id"], expected_revision=own[-1]["revision"], payload=payload)
    return context_use_of(control, attempt_id)


def finalize_context_use(control, jobs, authority, *, attempt_id, storage, receipt_reader, checkpoint_reader):
    """Persist a closed hold for an unprovable ending; faults remain retryable."""
    try:
        return _finalize_context_use(control, jobs, authority, attempt_id=attempt_id, storage=storage, receipt_reader=receipt_reader, checkpoint_reader=checkpoint_reader)
    except ContractRefusal:
        chain, admitted = _use(control, attempt_id)
        if chain[-1]["use_id"] == admitted["use_id"] and chain[-1]["action"] not in ("hold", "retire"):
            hold_context_use(control, attempt_id=attempt_id, reason="generation-damaged" if chain[-1]["action"] == "finalize" else "custody-invalid", evidence_refs=[digest(chain[-1])])
        raise
