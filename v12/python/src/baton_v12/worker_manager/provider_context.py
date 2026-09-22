"""Private provider contexts, derived from this manager's operation journal.

A context is neither an AgentSession nor permission to launch. A committed use
binds an ordinary implementation assignment; a ready generation additionally
requires accepted output, a fenced checkpoint and positively completed cleanup.
Candidate execution requires a bounded grant; production requires retained
qualification evidence and independent acceptance.
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
SERVING_RECEIPT_SCHEMA = "baton.provider-context-receipt/2"
INVOCATION_KIND = "provider-context.invocation"
DELIVERY_SCHEMA = "baton.provider-context-delivery/1"
DELIVERY_MEMBERS = ("schema", "context_id", "use_id", "invocation_id", "attempt_id", "generation", "generation_digest", "mode", "conversation_id", "profile_digest", "delivery_digest", "invocation_binding_digest", "task_digest", "prompt_digest", "argv_digest", "cli_build", "model", "reported_model", "argv_policy_digest", "environment_policy_digest")
ARGV_POLICY = {"program": "claude", "arguments": ["--print", "--dangerously-skip-permissions", "--output-format", "json"], "open": "--session-id", "restore": "--resume"}
ENVIRONMENT_POLICY = {"cwd": "/output", "home": "/run/baton/context/home", "keys": ["HOME", "PATH", "PYTHONPYCACHEPREFIX", "TMPDIR", "XDG_CACHE_HOME"], "ephemera": "fresh-per-child"}
REASONS = frozenset(("runtime-unknown", "invocation-unknown", "receipt-invalid", "custody-invalid", "generation-damaged", "retired"))
_ACTION_KEYS = {
    "admit": ("identity", "attempt_id", "writer_id", "assignment", "stage_id", "episode", "profile_digest", "job_digest", "limits_digest", "repo_pin", "source_pin", "input_digest", "policy_digest", "generation", "conversation_id", "mode", "predecessor", "qualification_run"),
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
    # W177936 QUALIFICATION-CONTRACT-232133 (as corrected by review232154):
    # THREE VOCABULARY VALUES. `deterministic` is the composed fixtures'
    # world, unchanged in every consumer. `candidate` exists so the one
    # qualification run never masquerades as either other kind -- it is
    # admissible only under a live one-run authorization, checked at the
    # admission and the launch boundary, never here (a pure validator holds
    # no store). `production` is admissible only after certification
    # recorded the full-config evidence, checked at the same two places.
    if held["schema"] != PROFILE_SCHEMA or held["qualification"] not in (
            "deterministic", "candidate", "production"):
        _refuse("unknown context profile qualification")
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
    if held["qualification"] == "production":
        record = control.operation_record(_id("context-certification", key))
        if record is None or record["kind"] != CERTIFICATION_KIND or record["state"] != "committed":
            _refuse("production profile lacks recorded certification")
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


QUALIFICATION_KIND = "provider-context.qualification-authorization"
CERTIFICATION_KIND = "provider-context.production-certification"


def qualification_deployment(control, authority_uuid):
    """Bind the authority and both configured directory objects, not just names."""
    from . import context_delivery, workspaces
    _text(authority_uuid)
    storage = context_delivery.configured_context_storage(control)
    workspace = workspaces.configured_workspace_storage(control).place
    descriptor, pins = context_delivery._open_absolute(workspace)
    os.close(descriptor)
    return {"authority_uuid": authority_uuid, "context_path": storage.path,
            "context_pins": [list(one) for one in storage.pins],
            "workspace_path": workspace, "workspace_pins": pins}


def authorize_qualification_run(control, *, run_id, profile_digest,
                                storage_path, authority_uuid, job_id, note):
    """ONE owner-selected qualification run, as a durable journaled grant.

    Review232154 [R2]: the operation identity is the RUN's, not the
    profile's -- a later, separately selected run of the unchanged profile
    is a NEW grant under a new `run_id`, while an exact retry of THIS act
    replays. The operands bind the full-config candidate profile digest,
    the authority and configured context/workspace directory identities,
    and the exact Job it may serve. Consumption is not
    recorded here: it commits INSIDE the opening admission,
    which is what makes it crash-safe and exactly-once.
    """
    boundaries.identity(run_id, "a qualification run identity")
    _hash(profile_digest)
    _text(storage_path)
    _text(job_id)
    if type(note) is not str or not note or len(note) > 2000:
        _refuse("a qualification note is bounded non-empty text")
    profile = context_profile_of(control, profile_digest)
    if profile["qualification"] != "candidate":
        _refuse("a qualification run authorizes a candidate profile only")
    deployment = qualification_deployment(control, authority_uuid)
    if deployment["context_path"] != storage_path:
        _refuse("qualification storage differs from configured deployment")
    operands = {"run_id": run_id, "profile_digest": profile_digest,
                "storage_path": storage_path, "job_id": job_id,
                "deployment": deployment, "note": note}
    return control.transact(
        _id("context-qualification", run_id), QUALIFICATION_KIND,
        manager_signature(QUALIFICATION_KIND, operands),
        lambda connection: dict(operands))


def qualification_grant_of(control, run_id):
    """The committed grant, or None; reject a mismatched journal signature."""
    record = control.operation_record(_id("context-qualification", run_id))
    if record is None or record["state"] != "committed" \
            or record["kind"] != QUALIFICATION_KIND:
        return None
    grant = json.loads(record["result"])
    if record["signature"] != manager_signature(QUALIFICATION_KIND, grant):
        _refuse("qualification authorization journal disagrees")
    return grant


def _grant_consumer(control, run_id):
    """Which context consumed this grant, or None.

    The consumption RECORD is the opening admission's own committed
    payload naming the run -- one table, one commit, no second act to
    crash between.
    """
    for context_id, chain in _history(control).items():
        first = next((one for one in chain if one["action"] == "admit"),
                     None)
        if first is not None \
                and first["payload"].get("qualification_run") == run_id:
            return context_id
    return None


def _qualified(control, jobs, facts, profile, generation, context_id):
    """The vocabulary gate, at the admission -- the one store-side place.

    `deterministic` answers None (unchanged world). `candidate` requires
    the live grant and enforces review232154 [R1]'s cap: the grant covers
    exactly the OPEN (generation 0) and ONE correction restore
    (generation 1); a third or later generation refuses by name, however
    the correction machinery got there. `production` requires the
    recorded certification. The answer is what the admission journals as
    `qualification_run`, so consumption commits with the admit itself.
    """
    if profile["qualification"] == "deterministic":
        return None
    if profile["qualification"] == "production":
        record = control.operation_record(
            _id("context-certification", facts["profile_digest"]))
        if record is None or record["state"] != "committed" \
                or record["kind"] != CERTIFICATION_KIND:
            _refuse("production profile lacks recorded certification")
        certified = json.loads(record["result"])
        operands = {"profile": certified["profile"], "evidence": certified["evidence"]}
        if certified["profile"] != profile or certified["profile_digest"] != facts["profile_digest"] or record["signature"] != manager_signature(CERTIFICATION_KIND, operands):
            _refuse("production certification journal disagrees")
        grant = qualification_grant_of(control, certified["evidence"]["run_id"])
        if grant is None or grant.get("deployment") != qualification_deployment(control, facts["identity"]["authority_uuid"]):
            _refuse("production certification belongs to another deployment")
        return None
    # candidate
    if generation > 1:
        _refuse("a qualification grant covers the open and one correction "
                "restore; a third generation is not a qualification run")
    identity = facts["identity"]
    deployment = qualification_deployment(control, identity["authority_uuid"])
    granted = None
    for context_id_held, chain in _history(control).items():
        first = next((one for one in chain if one["action"] == "admit"),
                     None)
        run = first["payload"].get("qualification_run") \
            if first is not None else None
        if run is not None and context_id_held == context_id:
            granted = run
    if granted is not None:
        # This context already consumed a grant at its opening admission;
        # the restore rides the same one.
        grant = qualification_grant_of(control, granted)
        if grant is None or grant.get("deployment") != deployment or grant["profile_digest"] != facts["profile_digest"] or grant["job_id"] != identity["job_id"]:
            _refuse("consumed qualification grant no longer matches deployment or Job")
        return granted
    # An OPENING admission: find one live, unconsumed grant for exactly
    # this profile, storage and job. Only this owner reads its journal
    # family, exactly as `_history` reads the transitions.
    candidates = []
    rows = control._connection.execute(
        "SELECT operation_id FROM operations WHERE kind = ? ORDER BY rowid",
        (QUALIFICATION_KIND,)).fetchall()
    for row_id in rows:
        row = control.operation_record(row_id["operation_id"])
        if row["state"] != "committed":
            continue
        grant = json.loads(row["result"])
        grant = qualification_grant_of(control, grant["run_id"])
        if grant["profile_digest"] != facts["profile_digest"] \
                or grant.get("deployment") != deployment \
                or grant["job_id"] != identity["job_id"]:
            continue
        if _grant_consumer(control, grant["run_id"]) is None:
            candidates.append(grant)
    if not candidates:
        _refuse("candidate profile has no live qualification grant for "
                "this deployment and Job")
    if len(candidates) > 1:
        _refuse("more than one live qualification grant matches; retire "
                "the extras before admitting a run")
    return candidates[0]["run_id"]


def certify_production_profile(control, profile, evidence):
    """Record full-config production certification from the consumed run.

    Review232154 [R3]: state manifests and success receipts do not prove
    RECALL. The evidence must carry the independently accepted CONTINUITY
    outcome -- the restore turn produced first-turn content that was
    available nowhere in its own prompt, task or workspace -- as an
    independently committed review with retained, digest-bound findings.
    Certification reopens both generations, strict receipts and provider
    results before recording that review's bounded recall determination.
    """
    held = _profile(profile)
    if held["qualification"] != "production":
        _refuse("certification records a production profile")
    evidence = _document(evidence, ("run_id", "context_id",
                                    "continuity", "evidence_refs"))
    grant = qualification_grant_of(control, evidence["run_id"])
    if grant is None:
        _refuse("certification names no committed qualification grant")
    consumer = _grant_consumer(control, evidence["run_id"])
    if consumer is None or consumer != evidence["context_id"]:
        _refuse("certification's grant was not consumed by the named "
                "context")
    candidate = context_profile_of(control, grant["profile_digest"])
    for key in set(held) - {"qualification"}:
        if held[key] != candidate[key]:
            _refuse(f"production profile diverges from the qualified "
                    f"candidate at {key}")
    chain = _history(control, evidence["context_id"])
    finalized = [one for one in chain if one["action"] == "finalize"]
    if len(finalized) < 2:
        _refuse("certification requires the open and the correction "
                "restore both finalized")
    if not any(one["action"] == "retire" for one in chain):
        _refuse("certification requires the qualification context retired")
    # Counts and caller assertions are not evidence. Re-open the retained
    # generations and strict serving receipts, including after retirement.
    from . import context_delivery, workspaces
    storage = context_delivery.configured_context_storage(control)
    if grant.get("deployment") != qualification_deployment(control, chain[0]["payload"]["identity"]["authority_uuid"]):
        _refuse("certification deployment differs from authorization")
    admits = [one for one in chain if one["action"] == "admit"]
    if len(admits) != 2 or len(finalized) != 2 or [one["payload"]["mode"] for one in admits] != ["open", "restore"]:
        _refuse("certification requires exactly two serving invocations")
    for admission, final in zip(admits, finalized):
        context_delivery.validate_generation(control, storage, evidence["context_id"], final["payload"])
        if context_invocation_of(control, admission["payload"]["attempt_id"]) is None:
            _refuse("certification requires strict serving receipt bindings")
        reader = lambda attempt, artifact: context_delivery.read_context_receipt(control, attempt_id=attempt, artifact_id=artifact, workspace_storage=workspaces.configured_workspace_storage(control).place)
        if _receipt(control, admission, reader) != final["payload"]["receipt_digest"]:
            _refuse("certification receipt differs from finalization")
    continuity = _document(evidence["continuity"], ("verdict_id", "report_digest"))
    _hash(continuity["report_digest"])
    verdict = review_cycles.verdict_of(control, continuity["verdict_id"])
    identity = admits[0]["payload"]["identity"]
    if verdict["disposition"] != "accepted" or verdict["checkpoint_id"] != finalized[-1]["payload"]["checkpoint_id"] or verdict["line_id"] != identity["line_id"] or verdict["reviewer_principal"] == identity["principal"]:
        _refuse("certification requires an independent accepted continuity review of the final checkpoint")
    report = _qualification_review(control, verdict, continuity["report_digest"])
    expected = {"schema": "baton.context-qualification-review/1", "run_id": evidence["run_id"], "context_id": evidence["context_id"], "attempts": [one["payload"]["attempt_id"] for one in admits], "receipt_digests": [one["payload"]["receipt_digest"] for one in finalized], "generation_digests": [one["payload"]["manifest_digest"] for one in finalized]}
    report = _document(report, tuple(expected) + ("provider_results", "recall"))
    if any(report[key] != value for key, value in expected.items()):
        _refuse("independent qualification review names different run evidence")
    recall = _document(report["recall"], ("expected_digest", "observed_digest", "second_inputs_excluded"))
    _hash(recall["expected_digest"]); _hash(recall["observed_digest"])
    if recall["expected_digest"] != recall["observed_digest"] or recall["second_inputs_excluded"] is not True:
        _refuse("independent qualification review does not establish recall")
    results = report["provider_results"]
    if type(results) is not list or len(results) != 2:
        _refuse("qualification requires both retained provider results")
    for admission, result in zip(admits, results):
        attempt = admission["payload"]["attempt_id"]
        result = _document(result, ("path", "bytes", "digest"))
        _hash(result["digest"])
        if type(result["path"]) is not str or os.path.basename(result["path"]) != "provider.stdout.log" or os.path.basename(os.path.dirname(result["path"])) != attempt:
            _refuse("provider result is not in the named attempt room")
        raw = _verified_file(result["path"], result["bytes"], result["digest"], 16 * 1024 * 1024)
        try:
            terminal = json.loads(raw)
        except (ValueError, UnicodeError):
            _refuse("retained provider result is not complete JSON")
        if type(terminal) is not dict or terminal.get("type") != "result" or terminal.get("subtype") != "success" or terminal.get("is_error") is not False or terminal.get("model") != candidate["reported_model"] or terminal.get("session_id") != admission["payload"]["conversation_id"]:
            _refuse("retained provider result disagrees with strict serving evidence")
    # The accepted report itself binds every external reference; decorative
    # references supplied by the certification caller are not admitted.
    if evidence["evidence_refs"] != [continuity["report_digest"]]:
        _refuse("certification references must name the accepted report digest")
    operands = {"profile": held, "evidence": evidence}
    production_digest = digest(held)
    control.transact(
        _id("context-certification", production_digest),
        CERTIFICATION_KIND,
        manager_signature(CERTIFICATION_KIND, operands),
        lambda connection: dict(operands, profile_digest=production_digest))
    return certify_context_profile(control, profile)


def _verified_file(path, size, expected, limit):
    """Bounded, no-follow retained evidence read with byte identity checks."""
    import stat
    from .context_delivery import _open_absolute
    if type(size) is not int or not 0 < size <= limit:
        _refuse("retained qualification evidence exceeds its bound")
    try:
        parent, unused = _open_absolute(os.path.dirname(path))
        try:
            fd = os.open(os.path.basename(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally:
            os.close(parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != size:
                _refuse("retained qualification evidence type or size differs")
            raw = bytearray()
            while len(raw) <= size:
                part = os.read(fd, size + 1 - len(raw))
                if not part:
                    break
                raw.extend(part)
            after = os.fstat(fd)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                _refuse("retained qualification evidence changed while read")
        finally:
            os.close(fd)
    except OSError:
        _refuse("retained qualification evidence is unavailable")
    raw = bytes(raw)
    if len(raw) != size or digest_of_bytes(raw) != expected:
        _refuse("retained qualification evidence digest differs")
    return raw


def _qualification_review(control, verdict, expected):
    """Resolve the independently committed review's original retained report."""
    from urllib.parse import unquote, urlsplit
    retained = verdict["review_result"]
    result = manifests.load_manifest(control, retained["manifest_digest"], "resultManifest")
    outputs = [one for one in result["outputs"] if one["name"] == "findings" and one["status"] == "present"]
    artifacts = [one for one in retained["artifacts"] if one["output_name"] == "findings"]
    if len(outputs) != 1 or len(artifacts) != 1 or outputs[0]["artifact"]["artifact_id"] != artifacts[0]["artifact_id"]:
        _refuse("accepted qualification review has no retained findings")
    entries = [one for one in outputs[0]["content_manifest"]["entries"] if one["path"] == "report.json"]
    if len(entries) != 1 or entries[0]["content_digest"] != expected:
        _refuse("accepted qualification report digest differs")
    locator = urlsplit(artifacts[0]["locator"])
    if locator.scheme != "file" or locator.netloc or locator.query or locator.fragment:
        _refuse("qualification review requires local retained custody")
    raw = _verified_file(os.path.join(unquote(locator.path), "report.json"), entries[0]["bytes"], expected, MAX_REPORT_BYTES)
    try:
        document = json.loads(raw)
        if set(document) != {"schema", "verdict", "findings"} or document["schema"] != "baton.review-report/1" or document["verdict"] != "accepted" or type(document["findings"]) is not str:
            _refuse("qualification review report is not accepted")
        return json.loads(document["findings"])
    except (ValueError, TypeError, UnicodeError):
        _refuse("qualification review findings are not a structured evidence report")


class ExecutionGrant:
    """The launch boundary's proof that the admission's gate held.

    Minted ONLY by `prove_context_execution`, which re-asks the store; the
    OCI adapter refuses real context execution without one whose identity
    matches the delivered context document. Shape cannot manufacture it:
    the mint is private to this module by the same nominal-type rule the
    workspace capabilities use.
    """

    def __init__(self, mint, context_id, use_id, qualification):
        if mint is not _MINT_GRANT:
            _refuse("an execution grant is minted by its own prover")
        self.context_id = context_id
        self.use_id = use_id
        self.qualification = qualification


_MINT_GRANT = object()


def prove_context_execution(control, attempt_id):
    """The launch boundary's half of the vocabulary gate.

    Deterministic profiles REFUSE real execution exactly as before -- the
    composed fixtures substitute the boundary explicitly and honestly.
    Candidate and production admissions, whose gates the admission itself
    already proved and journaled, mint the grant the adapter demands.
    """
    chain, admitted = _use(control, attempt_id)
    facts = admitted["payload"]
    profile = context_profile_of(control, facts["profile_digest"])
    if profile["qualification"] == "deterministic":
        _refuse("actual OCI context execution awaits a qualified runtime "
                "profile; deterministic profiles are composed, not "
                "executed")
    if profile["qualification"] == "candidate" \
            and facts.get("qualification_run") is None:
        _refuse("candidate admission carries no consumed qualification "
                "grant")
    if context_use_of(control, attempt_id)["status"] != "admitted":
        _refuse("execution requires a currently admitted context use")
    selected = _qualified(control, None, facts, profile, facts["generation"], admitted["context_id"])
    if selected != facts.get("qualification_run"):
        _refuse("execution qualification grant differs from admission")
    if profile["qualification"] == "production":
        record = control.operation_record(
            _id("context-certification", facts["profile_digest"]))
        if record is None or record["state"] != "committed":
            _refuse("production profile lacks recorded certification")
    return ExecutionGrant(_MINT_GRANT, admitted["context_id"],
                          admitted["use_id"], profile["qualification"])


def _operation(action, context_id, use_id, revision):
    return _id("context-" + action, [context_id, use_id, revision])



def _payload(action, payload):
    keys = _ACTION_KEYS[action]
    # Historical admissions predate qualification_run. Validate their original
    # shape without inserting a default: their signatures and chain digests
    # bind the old bytes. Only new non-deterministic uses require a grant.
    if action == "admit" and type(payload) is dict and "qualification_run" not in payload:
        keys = tuple(key for key in keys if key != "qualification_run")
    held = _document(payload, keys)
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
        if held.get("qualification_run") is not None:
            _text(held["qualification_run"])
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
        _transition(control, action="admit", context_id=request["context_id"], use_id=request["use_id"], expected_revision=request["revision"], payload=request["payload"], check=lambda: _check_admission(control, jobs, authority, request["context_id"], request["payload"]))
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
    # W177936: THE VOCABULARY GATE, and its answer commits WITH the admit --
    # a candidate profile's grant is consumed by this exact transition or
    # not at all (review232154 R1/R2 semantics live in `_qualified`).
    qualification_run = _qualified(
        control, jobs, facts, context_profile_of(
            control, facts["profile_digest"]), generation, context_id)
    payload = dict(facts, generation=generation, mode="restore" if generation else "open", predecessor=digest(predecessor) if predecessor else None, conversation_id=str(uuid.uuid5(uuid.NAMESPACE_OID, context_id)), qualification_run=qualification_run)
    use_id = _id("context-use", [context_id, attempt_id, generation])
    request = control.transact(request_id, request_kind, request_signature, lambda connection: {"context_id": context_id, "use_id": use_id, "revision": len(chain), "payload": payload})
    if request != {"context_id": context_id, "use_id": use_id, "revision": len(chain), "payload": payload}:
        # Another caller already pinned this attempt's exact request. Re-enter
        # its replay branch rather than compute a new operation identity.
        return admit_context_use(control, jobs, authority, attempt_id=attempt_id, writer_id=writer_id, profile_digest=profile_digest)
    def check():
        _check_admission(control, jobs, authority, context_id, payload)
    _transition(control, action="admit", context_id=context_id, use_id=use_id, expected_revision=len(chain), payload=payload, check=check)
    return context_use_of(control, attempt_id)


def _check_admission(control, jobs, authority, context_id, payload):
    """Called under the transition's BEGIN IMMEDIATE, including crash replay."""
    facts = _facts(control, jobs, authority, payload["attempt_id"], payload["writer_id"], payload["profile_digest"], live=True)
    if any(facts[key] != payload[key] for key in facts):
        _refuse("admission owner facts changed", durable=True)
    selected = _qualified(control, jobs, facts, context_profile_of(control, facts["profile_digest"]), payload["generation"], context_id)
    if selected != payload.get("qualification_run"):
        _refuse("qualification grant changed before admission commit", durable=True)


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
    except (ValueError, UnicodeError, RecursionError):
        _refuse("receipt is not complete JSON")
    if type(raw) is not dict or any(type(value) not in (str, int, bool, type(None)) for value in raw.values()):
        _refuse("receipt must contain only its bounded scalar fields")
    binding = context_invocation_of(control, attempt_id)
    members = ("schema", "context_id", "use_id", "attempt_id", "conversation_id", "profile_digest", "invocation_id", "status", "complete", "model", "observed_model", "terminal", "cli_build", "mode", "delivery_digest", "input_digest", "policy_digest")
    if binding is not None:
        members += ("task_digest", "prompt_digest", "argv_digest", "invocation_binding_digest", "observed_conversation_id")
    value = _document(raw, members)
    profile = context_profile_of(control, facts["profile_digest"])
    delivered = next(one for one in _history(control, admitted["context_id"]) if one["action"] == "deliver" and one["use_id"] == admitted["use_id"])
    expected = {"model": profile["model"], "observed_model": profile["reported_model"], "terminal": "success", "cli_build": profile["cli_build"], "mode": facts["mode"], "delivery_digest": delivered["payload"]["delivery_digest"], "input_digest": facts["input_digest"], "policy_digest": facts["policy_digest"], "schema": RECEIPT_SCHEMA, "context_id": admitted["context_id"], "use_id": admitted["use_id"], "attempt_id": attempt_id, "conversation_id": facts["conversation_id"], "profile_digest": facts["profile_digest"], "invocation_id": _id("context-invocation", admitted["use_id"])}
    if binding is not None:
        expected.update(schema=SERVING_RECEIPT_SCHEMA, observed_conversation_id=facts["conversation_id"], **{key: binding[key] for key in ("task_digest", "prompt_digest", "argv_digest", "invocation_binding_digest")})
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
        if context_invocation_of(control, attempt_id) is not None:
            try:
                if _receipt(control, admitted, receipt_reader) != finalized["payload"]["receipt_digest"]:
                    _refuse("finalized serving receipt no longer matches its retained evidence")
            except ContractRefusal:
                hold_context_use(control, attempt_id=attempt_id, reason="receipt-invalid", evidence_refs=[digest(finalized)])
                raise
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


# W177936 (owner 2026-09-21T14:37:12Z): HOW MUCH REVIEW FEEDBACK ONE RESTORE
# PROMPT MAY CARRY, in UTF-8 BYTES rather than characters, and how much of a
# retained report this module will read to obtain it. The report bound exists
# so a bounded feedback limit cannot be reached through an unbounded file
# read; both refuse by name.
MAX_FEEDBACK_BYTES = 32768
MAX_REPORT_BYTES = 1 << 20


def context_prompt(task, feedback=None):
    """The image's deterministic implementation prompt, without importing it.

    W177936: A RESTORE CARRIES THE REVIEW'S FEEDBACK, an open does not. The
    whole point of resuming the implementer's conversation is that the
    independent review's findings arrive IN it; without this member the
    resumed conversation was re-sent the original task text and the feedback
    reached the implementer nowhere. The worker's `_prompt` is this
    function's asserted twin, so both sides derive the same bytes and the
    bound prompt/argv digests hold the pair together.
    """
    if type(task) is not dict or type(task.get("instructions")) is not str or type(task.get("verification")) is not list or not all(type(one) is str for one in task["verification"]):
        _refuse("invalid serving task")
    opening = (f"{task['instructions']}\n\n"
               f"You are working in a private copy of the source tree, which "
               f"is the current working directory. Edit files here "
               f"directly.\n"
               f"When you are done, the following command will be run from "
               f"this directory and must pass:\n"
               f"  {' '.join(task['verification'])}\n")
    if feedback is None:
        return opening
    if type(feedback) is not str or not feedback \
            or len(feedback.encode("utf-8")) > MAX_FEEDBACK_BYTES:
        _refuse("serving feedback is bounded non-empty text")
    return (f"{opening}\n"
            f"An independent review of your previous proposal in this same "
            f"working copy requested changes. Revise your work here "
            f"accordingly; the verification command above is unchanged and "
            f"must still pass.\n\n"
            f"THE REVIEW'S FINDINGS:\n{feedback}\n")


def correction_feedback_of(control, jobs, attempt_id):
    """The findings text of the verdict that OPENED this correction attempt.

    THE SAME PROVENANCE THE ADMISSION USED, not a fresher opinion: the
    admitted use's predecessor generation names its frozen checkpoint, the
    owner-committed correction operation for exactly that checkpoint names
    the verdict, and the verdict is proved against its committed act by
    `verdict_of` -- so a newer verdict, another line's verdict or a
    tampered row cannot supply this prompt. The text itself is read from
    the verdict's own retained accepted custody, held to the frozen result
    manifest's bytes and digest before one byte is trusted.
    """
    chain, admitted = _use(control, attempt_id)
    facts = admitted["payload"]
    if facts["mode"] != "restore":
        _refuse("serving feedback belongs to a restore invocation")
    predecessor = next((one for one in reversed(chain)
                        if one["action"] == "finalize"), None)
    if predecessor is None:
        _refuse("restore invocation has no finalized predecessor")
    checkpoint = predecessor["payload"]["checkpoint_id"]
    row = jobs.operation_record(episodes.correction_operation_id(
        facts["identity"]["job_id"], checkpoint))
    if row is None or row["state"] != "committed" \
            or row["kind"] != episodes.CORRECT_KIND:
        _refuse("no owner-committed correction for this restore")
    operands = json.loads(row["signature"])["operands"]
    recorded = json.loads(row["result"])
    if recorded["implementation"]["attempt_id"] != attempt_id:
        _refuse("correction did not open this attempt")
    verdict = review_cycles.verdict_of(control, operands["verdict_id"])
    if verdict["checkpoint_id"] != checkpoint \
            or verdict["line_id"] != facts["identity"]["line_id"] \
            or verdict["disposition"] != "changes-requested":
        _refuse("correction verdict disagrees with this restore")
    retained = verdict["review_result"]
    artifacts = [one for one in retained["artifacts"]
                 if one["output_name"] == "findings"]
    if len(artifacts) != 1:
        _refuse("correction verdict retains no single findings artifact")
    artifact = artifacts[0]
    result = manifests.load_manifest(control, retained["manifest_digest"],
                                     "resultManifest")
    outputs = {one["name"]: one for one in result["outputs"]}
    held = outputs.get("findings")
    if held is None or held.get("status") != "present" \
            or (held.get("artifact") or {}).get("artifact_id") \
            != artifact["artifact_id"] or held.get("content_manifest") is None:
        _refuse("frozen review result and retained verdict custody disagree")
    entries = [one for one in held["content_manifest"]["entries"]
               if one["path"] == "report.json"]
    if len(entries) != 1 or type(entries[0].get("bytes")) is not int \
            or entries[0]["bytes"] > MAX_REPORT_BYTES:
        _refuse("frozen review result has no bounded report.json")
    from urllib.parse import unquote, urlsplit
    locator = urlsplit(artifact["locator"])
    if locator.scheme != "file" or locator.netloc or locator.query \
            or locator.fragment:
        _refuse("serving feedback reads local accepted custody only")
    import stat as _stat
    try:
        descriptor = os.open(
            os.path.join(unquote(locator.path), "report.json"),
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        _refuse("the accepted review report is unavailable")
    try:
        if not _stat.S_ISREG(os.fstat(descriptor).st_mode):
            _refuse("the retained review report is not a regular file")
        raw = os.read(descriptor, entries[0]["bytes"] + 1)
    finally:
        os.close(descriptor)
    if len(raw) != entries[0]["bytes"] \
            or digest_of_bytes(raw) != entries[0]["content_digest"]:
        _refuse("the retained review report differs from frozen custody")
    try:
        report = json.loads(raw)
    except (ValueError, UnicodeError):
        _refuse("the retained review report is not JSON")
    if type(report) is not dict or set(report) != {"schema", "verdict",
                                                   "findings"} \
            or report["schema"] != "baton.review-report/1" \
            or report["verdict"] != "changes-requested" \
            or type(report["findings"]) is not str or not report["findings"]:
        _refuse("the retained review report does not carry "
                "changes-requested findings")
    if len(report["findings"].encode("utf-8")) > MAX_FEEDBACK_BYTES:
        _refuse("the retained review findings exceed the feedback bound")
    return report["findings"]


def serving_argv(profile, facts, prompt):
    return ["claude", *ARGV_POLICY["arguments"], "--model", profile["model"], ARGV_POLICY[facts["mode"]], facts["conversation_id"], prompt]


def _invocation_base(control, admitted):
    facts = admitted["payload"]
    profile = context_profile_of(control, facts["profile_digest"])
    chain, original = _use(control, facts["attempt_id"])
    delivered = next((one for one in chain if one["use_id"] == admitted["use_id"] and one["action"] == "deliver"), None)
    if original != admitted or delivered is None:
        _refuse("serving invocation lacks delivery")
    previous = next((one for one in chain if one["action"] == "finalize" and one["payload"]["generation"] == facts["generation"]), None)
    return {"schema": DELIVERY_SCHEMA, "context_id": admitted["context_id"], "use_id": admitted["use_id"], "invocation_id": _id("context-invocation", admitted["use_id"]), "attempt_id": facts["attempt_id"], "generation": facts["generation"], "generation_digest": previous["payload"]["manifest_digest"] if previous else None, "mode": facts["mode"], "conversation_id": facts["conversation_id"], "profile_digest": facts["profile_digest"], "delivery_digest": delivered["payload"]["delivery_digest"], **{key: profile[key] for key in ("cli_build", "model", "reported_model", "argv_policy_digest", "environment_policy_digest")}}


def context_invocation_of(control, attempt_id):
    """Pure historical reader. Absence never authorizes a downgraded launch."""
    row = control.operation_record(_id("context-serving-invocation", attempt_id))
    if row is None:
        return None
    if row["state"] != "committed" or row["kind"] != INVOCATION_KIND:
        _refuse("serving invocation is not committed")
    value = _document(json.loads(row["result"]), DELIVERY_MEMBERS)
    operands = {key: value[key] for key in value if key != "invocation_binding_digest"}
    if row["signature"] != manager_signature(INVOCATION_KIND, operands) or value["invocation_binding_digest"] != digest(operands):
        _refuse("serving invocation journal disagrees")
    chain, admitted = _use(control, attempt_id)
    if any(value[key] != expected for key, expected in _invocation_base(control, admitted).items()):
        _refuse("serving invocation original identity disagrees")
    for key in ("task_digest", "prompt_digest", "argv_digest", "invocation_binding_digest"):
        _hash(value[key])
    return value


def bind_context_invocation(control, jobs, authority, *, attempt_id, writer_id, profile_digest, task_bytes):
    if type(task_bytes) is not bytes or len(task_bytes) > 65536:
        _refuse("serving task exceeds its bound")
    chain, admitted = _use(control, attempt_id)
    facts = admitted["payload"]
    if facts["writer_id"] != writer_id or facts["profile_digest"] != profile_digest:
        _refuse("serving invocation operands disagree")
    profile = context_profile_of(control, profile_digest)
    if profile["argv_policy_digest"] != digest(ARGV_POLICY) or profile["environment_policy_digest"] != digest(ENVIRONMENT_POLICY):
        _refuse("profile does not qualify the closed serving policy")
    try:
        task = json.loads(task_bytes)
    except (ValueError, UnicodeError):
        _refuse("serving task is not JSON")
    manifest = manifests.load_manifest(control, facts["input_digest"], "inputManifest")
    context_output_declaration(manifest["outputs"])
    if manifest["human_contract"]["content_digest"] != digest_of_bytes(task_bytes) or manifest["human_contract"]["bytes"] != len(task_bytes):
        _refuse("serving task differs from the submitted input")
    # W177936: A RESTORE PROMPT CARRIES THE OPENING VERDICT'S FEEDBACK. The
    # resolution follows the admission's own committed provenance, so a
    # replayed binding resolves the SAME verdict and the same bytes -- a
    # newer report can never overwrite a previously bound use, because the
    # committed invocation's prompt digest is what every later reader and
    # the worker itself hold the composition to.
    feedback = correction_feedback_of(control, jobs, attempt_id) \
        if facts["mode"] == "restore" else None
    prompt = context_prompt(task, feedback)
    value = dict(_invocation_base(control, admitted), task_digest=digest_of_bytes(task_bytes), prompt_digest=digest_of_bytes(prompt.encode()), argv_digest=digest(serving_argv(profile, facts, prompt)))
    def commit(connection):
        current = _facts(control, jobs, authority, attempt_id, writer_id, profile_digest, live=True)
        if context_use_of(control, attempt_id)["status"] != "admitted" or any(current[key] != facts[key] for key in current):
            _refuse("serving invocation owner changed", durable=True)
        return dict(value, invocation_binding_digest=digest(value))
    bound = control.transact(_id("context-serving-invocation", attempt_id), INVOCATION_KIND, manager_signature(INVOCATION_KIND, value), commit)
    if feedback is not None:
        # THE DELIVERED FILE AGREES WITH THE COMMITTED BINDING, whichever
        # came first. A fresh bind writes the bytes it just bound; a replay
        # or crash recovery re-proves that what stands (or what it rewrites)
        # composes to the COMMITTED prompt digest, and refuses anything
        # else rather than repairing it.
        if bound["prompt_digest"] != digest_of_bytes(
                context_prompt(task, feedback).encode()):
            _refuse("serving feedback disagrees with the committed binding")
        from .context_delivery import configured_context_storage, deliver_feedback
        deliver_feedback(control, configured_context_storage(control),
                         attempt_id=attempt_id,
                         payload=feedback.encode("utf-8"))
    return context_invocation_of(control, attempt_id)


def revalidate_context_start(control, jobs, authority, *, attempt_id):
    from .context_delivery import adopt_context_use, configured_context_storage
    binding = context_invocation_of(control, attempt_id)
    if binding is None or context_use_of(control, attempt_id)["status"] != "admitted":
        _refuse("serving use cannot start")
    chain, admitted = _use(control, attempt_id)
    facts = admitted["payload"]
    current = _facts(control, jobs, authority, attempt_id, facts["writer_id"], facts["profile_digest"], live=True)
    if any(current[key] != facts[key] for key in current):
        _refuse("serving start owner changed")
    adopt_context_use(control, configured_context_storage(control), attempt_id=attempt_id)
    return binding


def context_output_declaration(outputs):
    selected = [one for one in outputs if one["name"] == "provider-context-receipt"]
    if len(selected) != 1:
        _refuse("reserved receipt declaration is missing or duplicated")
    one = selected[0]
    if one["type"] != "directory-result" or one["path"] != "provider-context-receipt" or one["required"] is not False or one["constraints"] != {"max_entries": 1, "max_bytes": 16384, "allowed_media_types": ["application/octet-stream"], "link_policy": "forbid", "validator_digest": None}:
        _refuse("reserved receipt declaration differs from the optional bounded contract")
    return one
