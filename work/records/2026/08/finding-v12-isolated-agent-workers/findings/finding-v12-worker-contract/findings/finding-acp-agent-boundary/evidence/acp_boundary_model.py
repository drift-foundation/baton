"""Executable design model for baton.agent-session 1.0.

Provider-free evidence, not product code.  It models only the cross-field
rules that JSON Schema cannot express: handshake refusal, structural
capability withholding, policy pinning and drift, permission refusal,
turn-outcome derivation, update normalization, sequencing, the monotonic
session axis, the agent/runtime quiescence separation, and the Codex App
Server mapping.

Nothing here imports Baton or v12/ product code, and nothing here reaches a
model provider.  It does import `jsonschema`, because the durable shape
contract is part of certification rather than something a separate test proves
alongside it: an entry point that reads policy fields out of a document the
schema would reject is not validating that document.
"""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator


class BoundaryError(ValueError):
    """A refusal at the agent-session boundary.

    It carries the CLOSED baton.worker-control 1.0 category/code pair it
    reports as, because this family adds none of its own.
    """

    def __init__(self, message: str, category: str, code: str) -> None:
        super().__init__(message)
        self.category = category
        self.code = code
        validate_error_pair(category, code)


# --------------------------------------------------------------------------
# baton.worker-control 1.0 §11, reproduced verbatim.  Reused, never extended.
# --------------------------------------------------------------------------

WORKER_CONTROL_ERRORS = {
    "refused": {"precondition", "unsupported-version", "capability", "extension", "operation-collision", "already-terminal"},
    "ambiguous": {"operation", "runtime-start", "collection"},
    "unavailable": {"transport", "authority", "artifact-store", "source-provider"},
    "policy": {"denied", "profile-uncertified", "credential-lifetime", "retention"},
    "integrity": {"schema", "digest", "path", "file-type", "limit", "secret-leak"},
    "stale-assignment": {"ended", "generation", "contract", "target"},
    "runtime-observation": {"identity-mismatch", "duplicate-runtime", "quiescence-unknown", "state-regression"},
}

# The schema definitions this family reproduces verbatim from
# urn:baton:worker-control:1.0.  A test asserts they stay byte-identical, so a
# document valid here cannot be invalid under the contract that takes
# precedence.
SHARED_WORKER_CONTROL_DEFS = (
    "digest", "opaqueId", "timestamp", "participant",
    "workRef", "assignmentRef", "artifactRef", "evidenceRef",
)


def validate_error_pair(category: str, code: str) -> None:
    if category not in WORKER_CONTROL_ERRORS:
        raise ValueError(f"category {category!r} is not in the closed worker-control taxonomy")
    if code not in WORKER_CONTROL_ERRORS[category]:
        raise ValueError(f"code {code!r} does not belong to category {category!r}")


# --------------------------------------------------------------------------
# Canonicalization (worker-control §3.2), applied to agent-session documents.
# --------------------------------------------------------------------------

def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def seal_document(document: dict) -> dict:
    sealed = copy.deepcopy(document)
    sealed.pop("document_digest", None)
    sealed["document_digest"] = digest(sealed)
    return sealed


def verify_document_digest(document: dict) -> None:
    candidate = copy.deepcopy(document)
    recorded = candidate.pop("document_digest", None)
    if recorded != digest(candidate):
        raise BoundaryError("document digest mismatch", "integrity", "digest")


SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "schema" / "agent-session-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
_DOCUMENT_VALIDATOR = Draft202012Validator(SCHEMA)


def validate_document_shape(document: dict) -> None:
    """The durable shape contract, checked on the runtime path.

    Proving schema, seal and semantics separately in three tests does not make
    the runtime path compose them.  Every certification entry point below runs
    all three, in that order, before it reads a single policy field.
    """
    error = next(_DOCUMENT_VALIDATOR.iter_errors(document), None)
    if error is not None:
        raise BoundaryError(
            f"document does not satisfy agent-session 1.0: {error.message}",
            "integrity", "schema")


def accept_document(document: dict) -> dict:
    """Shape, then seal.  Returns a private copy nothing else can mutate."""
    validate_document_shape(document)
    verify_document_digest(document)
    return copy.deepcopy(document)


# --------------------------------------------------------------------------
# §2 handshake
# --------------------------------------------------------------------------

REQUIRED_AGENT_METHODS = frozenset({
    "initialize", "session/new", "session/prompt", "session/cancel", "session/update",
})

REFUSED_AGENT_METHODS = frozenset({
    "session/load", "session/resume", "session/fork", "session/list", "session/delete",
    "authenticate", "logout", "providers/list", "providers/set", "providers/disable",
    "nes/start", "nes/suggest", "nes/accept", "nes/reject", "nes/close",
    "document/didOpen", "document/didChange", "document/didClose",
    "document/didSave", "document/didFocus", "mcp/message",
})

# ACP client methods.  Serving any of these hands the agent a capability that
# reaches around the runtime's isolation boundary, so the relay advertises
# none of them and refuses the call rather than answering it.
CAPABILITY_CLIENT_METHODS = frozenset({
    "fs/read_text_file", "fs/write_text_file",
    "terminal/create", "terminal/output", "terminal/release",
    "terminal/wait_for_exit", "terminal/kill",
    "mcp/connect",
})

# @agentclientprotocol/sdk 1.3.0 ClientCapabilities, with the members its own
# type declaration marks UNSTABLE.  `session` is stable and is nonetheless not
# advertised, because §2.2 withholds everything rather than everything unsafe.
ACP_CLIENT_CAPABILITY_MEMBERS = ("fs", "terminal", "session", "plan", "auth",
                                 "elicitation", "nes", "positionEncodings")
ACP_UNSTABLE_CLIENT_CAPABILITIES = frozenset({
    "plan", "auth", "elicitation", "nes", "positionEncodings",
})

SESSION_CAPABILITIES = frozenset({
    "session.fresh", "session.mode-pin", "session.prompt",
    "session.cancel", "session.update-normalization", "session.permission-refusal",
})

# The required and refused method sets belong to the VERSION, not to a
# profile.  A profile that could restate them could disagree with them, and a
# certified document that disagrees with the policy actually enforced is worse
# than no document: it is a second source of truth wearing the first one's
# authority.
REQUIRED_METHODS_BY_WIRE = {
    "acp": REQUIRED_AGENT_METHODS,
    "codex-app-server": frozenset({
        "initialize", "thread/start", "turn/start", "turn/interrupt",
    }),
}

MINIMAL_CLIENT_CAPABILITIES = {
    "fs": {"read_text_file": False, "write_text_file": False},
    "terminal": False,
}


def validate_client_capabilities(advertised: dict) -> None:
    """§2.2 — the relay withholds fs and terminal capability structurally."""
    if advertised != MINIMAL_CLIENT_CAPABILITIES:
        raise BoundaryError(
            "the relay may advertise no filesystem, terminal or other client capability",
            "policy", "denied")


def negotiate_acp(profile: dict, agent_protocol_version: int, agent_methods: set,
                  agent_session_capabilities: set) -> dict:
    """§2.1-§2.4.  Exact wire-version match, or refusal."""
    if profile["wire_protocol"] != "acp":
        raise BoundaryError(
            "wire-version negotiation belongs to ACP; a provider without a negotiated "
            "version is certified through provider_binding instead",
            "refused", "unsupported-version")
    profile = validate_profile(profile)

    if agent_protocol_version != profile["pinned_wire_version"]:
        raise BoundaryError(
            f"agent answered wire version {agent_protocol_version}, "
            f"profile pins {profile['pinned_wire_version']}; no downgrade",
            "refused", "unsupported-version")

    missing = REQUIRED_METHODS_BY_WIRE["acp"] - set(agent_methods)
    if missing:
        raise BoundaryError(
            f"agent endpoint is missing required methods {sorted(missing)}",
            "refused", "capability")

    missing_caps = SESSION_CAPABILITIES - set(agent_session_capabilities)
    if missing_caps:
        raise BoundaryError(
            f"agent session cannot provide {sorted(missing_caps)}",
            "refused", "capability")

    return {
        "wire_version": agent_protocol_version,
        "client_capabilities": copy.deepcopy(MINIMAL_CLIENT_CAPABILITIES),
        "session_capabilities": sorted(SESSION_CAPABILITIES),
    }


def bind_provider(profile: dict, observed_build_id: str, observed_interface_digest: str) -> dict:
    """§2.1 and §10.1 — certification for a provider with NO wire version.

    The App Server documents no `protocolVersion` in its initialization, so
    there is nothing to negotiate and nothing to refuse a downgrade against.
    Certification binds an exact server build and its captured interface
    description instead.  This REPLACES version negotiation; it is not a
    second spelling of it.
    """
    if profile["wire_protocol"] == "acp":
        raise BoundaryError(
            "an ACP profile negotiates a wire version; it is not certified by provider binding",
            "refused", "unsupported-version")
    profile = validate_profile(profile)
    binding = profile["provider_binding"]
    if binding is None:
        raise BoundaryError("a provider profile must carry a certified provider binding",
                            "policy", "profile-uncertified")
    if binding["experimental_api"] is not False:
        raise BoundaryError("a certified profile never enables the provider's experimental API",
                            "policy", "denied")
    if observed_build_id != binding["server_build_id"]:
        raise BoundaryError(
            f"server build {observed_build_id!r} is not the certified "
            f"{binding['server_build_id']!r}",
            "policy", "profile-uncertified")
    if observed_interface_digest != binding["interface_digest"]:
        raise BoundaryError(
            "the server's interface description does not match the certified digest",
            "policy", "profile-uncertified")
    return {"wire_version": None, "provider_binding": copy.deepcopy(binding)}


def check_outbound_method(method: str) -> None:
    """§2.3 — the relay never SENDS a refused method."""
    if method in REFUSED_AGENT_METHODS:
        raise BoundaryError(
            f"{method} is refused in agent-session 1.0", "refused", "capability")


def serve_client_method(method: str) -> None:
    """§4.4 — the relay never SERVES an unadvertised client method."""
    if method in CAPABILITY_CLIENT_METHODS:
        raise BoundaryError(
            f"agent called unadvertised client method {method}", "policy", "denied")


# --------------------------------------------------------------------------
# §3 identity and session binding
# --------------------------------------------------------------------------

POSTURES = frozenset({"consent", "execution"})

SESSION_REF_MEMBERS = frozenset({
    "runtime_attempt_id", "posture", "session_epoch", "provider_session_id",
})


def validate_session_ref(ref: dict) -> None:
    unknown = set(ref) - SESSION_REF_MEMBERS
    if unknown:
        raise BoundaryError(
            f"agent_session_ref must not carry {sorted(unknown)}; it labels evidence "
            "and authorizes nothing",
            "integrity", "schema")
    if ref.get("posture") not in POSTURES:
        raise BoundaryError("agent_session_ref needs an explicit posture", "integrity", "schema")
    if not isinstance(ref.get("session_epoch"), int) or ref["session_epoch"] < 1:
        raise BoundaryError("session_epoch must be a positive integer", "integrity", "schema")


def validate_work_ref(work_ref: dict) -> None:
    """worker-control §12.1 — the Work ID's authority prefix must match."""
    authority = work_ref["authority_uuid"]
    work_id = work_ref["work_id"]
    if not work_id.startswith(authority[:8] + "-W"):
        raise BoundaryError(
            f"work_id {work_id!r} does not carry the first eight characters of its authority UUID",
            "integrity", "schema")


def validate_session_binding_fields(record: dict) -> None:
    """PARTIAL helper: the cross-field binding rules only.

    Like `certify_profile_fields`, it assumes an already-accepted document and
    exists so isolated vectors can exercise one rule at a time.  Session-record
    validation is `validate_session_binding`.
    """
    validate_session_ref(record["agent_session_ref"])
    validate_work_ref(record["work_ref"])

    posture = record["posture"]
    if record["agent_session_ref"]["posture"] != posture:
        raise BoundaryError(
            "the session ref's posture must equal the record's posture",
            "integrity", "schema")

    assignment = record["assignment_ref"]
    if posture == "execution":
        if assignment is None:
            raise BoundaryError(
                "an execution session carries the exact live assignment; writable "
                "execution never begins without one",
                "refused", "precondition")
        validate_work_ref(assignment["work_ref"])
        if assignment["work_ref"] != record["work_ref"]:
            raise BoundaryError(
                "the session's assignment belongs to a different Work",
                "integrity", "schema")
    else:
        if assignment is not None:
            raise BoundaryError(
                "a consent session exists before any claim and carries no assignment",
                "refused", "precondition")


def validate_session_binding(record: dict, profile: dict) -> dict:
    """§3.2, §12.6-§12.7 — THE session-record entry point.

    The profile is MANDATORY.  A record is a claim about the certification it
    ran under, and a claim nobody checks against that certification is not
    evidence.  The record's own shape and seal are accepted before any binding
    field is read, for the same reason the profile's are.
    """
    record = accept_document(record)
    profile = validate_profile(profile)
    validate_session_binding_fields(record)

    posture = record["posture"]
    if record["profile_digest"] != profile["document_digest"]:
        raise BoundaryError(
            "the session record names a different profile than the one it ran under",
            "integrity", "digest")
    if record["pinned_policy"] != profile["postures"][posture]["policy"]:
        raise BoundaryError(
            f"the session's pinned policy is not the certified {posture} policy",
            "policy", "profile-uncertified")
    if set(record["negotiated_session_capabilities"]) != SESSION_CAPABILITIES:
        raise BoundaryError(
            "a session negotiates exactly the six mandatory capabilities",
            "refused", "capability")
    return record


def participant_from_session(_provider_session_id: str) -> None:
    """§3.1 — there is no such derivation, and asking for one is the defect."""
    raise BoundaryError(
        "a provider session or thread id is not a Baton participant, Handler or assignment",
        "integrity", "schema")


@dataclass
class AttemptSessions:
    """§3.2 — one fresh provider session per (attempt, posture, epoch).

    A consent session cannot become an execution session: it has no workspace
    and no assignment, and §4.2 says the postures are never interchangeable.
    So the execution session is a SEPARATE provider session under the same
    W151 runtime attempt, and the epoch counter is scoped per posture.
    """

    runtime_attempt_id: str
    _epochs: dict = field(default_factory=dict)
    _open: dict = field(default_factory=dict)

    def open_session(self, posture: str, provider_session_id: str | None = None) -> dict:
        if posture not in POSTURES:
            raise BoundaryError(f"unknown posture {posture!r}", "integrity", "schema")
        if self._open.get(posture) is not None:
            raise BoundaryError(
                f"a {posture} session is already open for this attempt; close or end it first",
                "runtime-observation", "duplicate-runtime")
        epoch = self._epochs.get(posture, 0) + 1
        self._epochs[posture] = epoch
        ref = {
            "runtime_attempt_id": self.runtime_attempt_id,
            "posture": posture,
            "session_epoch": epoch,
            "provider_session_id": provider_session_id,
        }
        validate_session_ref(ref)
        self._open[posture] = ref
        return ref

    def end_session(self, posture: str) -> None:
        self._open[posture] = None

    def promote_consent_to_execution(self) -> None:
        raise BoundaryError(
            "a consent session has no workspace and no assignment; it is never reused as "
            "an execution session",
            "refused", "precondition")


# --------------------------------------------------------------------------
# §4 policy
# --------------------------------------------------------------------------

@dataclass
class PinnedPolicy:
    """ACP posture policy: exactly one session mode, with no fallback."""

    posture: str
    session_mode_id: str

    @classmethod
    def from_binding(cls, posture: str, binding: dict) -> "PinnedPolicy":
        policy = binding["policy"]
        if policy["kind"] != "acp":
            raise BoundaryError("this posture is not pinned by an ACP session mode",
                                "policy", "denied")
        return cls(posture, policy["session_mode_id"])

    def enforce(self, modes: dict | None) -> str:
        """§4.1 — exact, with no fallback and no nearest match."""
        if not modes or not isinstance(modes.get("availableModes"), list):
            raise BoundaryError(
                f"agent advertised no session modes; pinned mode {self.session_mode_id!r} "
                "cannot be enforced",
                "policy", "denied")
        available = [mode["id"] for mode in modes["availableModes"]]
        if self.session_mode_id not in available:
            raise BoundaryError(
                f"pinned mode {self.session_mode_id!r} is not among {available}; "
                "refusing rather than falling back",
                "policy", "denied")
        return self.session_mode_id

    def check_drift(self, observed_mode_id: str) -> None:
        """§4.4 — a current_mode_update off the pinned mode is a policy failure."""
        if observed_mode_id != self.session_mode_id:
            raise BoundaryError(
                f"session drifted to mode {observed_mode_id!r} from pinned {self.session_mode_id!r}",
                "policy", "denied")


# §10.2-§10.3.  A posture is not just "some policy"; it is THIS policy.  These
# are the operands each posture must pin, and swapping them certifies the
# inverse of the normative text while still looking like a well-formed profile.
CODEX_POSTURE_OPERANDS = {
    "consent": {"sandbox": "readOnly", "cwd_role": "scratch",
                "sandbox_policy": {"type": "readOnly"}},
    "execution": {"sandbox": "workspaceWrite", "cwd_role": "workspace",
                  "sandbox_policy": {"type": "workspaceWrite", "network_access": False}},
}
POSTURE_INVARIANTS = {
    "consent": {"workspace": False, "declared_output": False},
    "execution": {"workspace": True, "declared_output": True},
}


def certify_profile_fields(profile: dict) -> None:
    """PARTIAL helper: the cross-field policy rules only.

    It assumes a document whose shape and seal have ALREADY been accepted, and
    it is exposed only so isolated vectors can exercise one rule at a time.
    It is not the certification validator; `validate_profile` is.  An earlier
    revision exposed this function under that name, and both `negotiate_acp`
    and `bind_provider` consequently acted on documents the durable contract
    rejects.
    """
    wire = profile["wire_protocol"]
    if wire not in REQUIRED_METHODS_BY_WIRE:
        raise BoundaryError(f"unknown wire protocol {wire!r}", "integrity", "schema")

    if set(profile["session_capabilities"]) != SESSION_CAPABILITIES:
        raise BoundaryError(
            "a certified profile declares exactly the six mandatory session capabilities",
            "policy", "profile-uncertified")

    if wire == "acp":
        if profile["pinned_wire_version"] is None or profile["provider_binding"] is not None:
            raise BoundaryError("an ACP profile pins a wire version and carries no provider binding",
                                "policy", "profile-uncertified")
        validate_client_capabilities(profile["client_capabilities"])
    else:
        if profile["pinned_wire_version"] is not None or profile["provider_binding"] is None:
            raise BoundaryError(
                "a provider profile carries a certified binding and pins no wire version",
                "policy", "profile-uncertified")
        if profile["client_capabilities"] is not None:
            raise BoundaryError("client capabilities are an ACP concept", "policy", "denied")

    for posture, invariants in POSTURE_INVARIANTS.items():
        binding = profile["postures"][posture]
        for member, expected in invariants.items():
            if binding[member] is not expected:
                raise BoundaryError(
                    f"a {posture} posture must declare {member}={expected}",
                    "policy", "profile-uncertified")
        policy = binding["policy"]
        if policy["kind"] != ("acp" if wire == "acp" else "codex-app-server"):
            raise BoundaryError(
                f"the {posture} policy is not a {wire} policy", "policy", "profile-uncertified")
        if wire == "codex-app-server":
            operands = CODEX_POSTURE_OPERANDS[posture]
            thread, turn = policy["thread_start"], policy["turn_start"]
            if (thread["approval_policy"] != "never" or turn["approval_policy"] != "never"):
                raise BoundaryError(
                    "a certified profile pins approvalPolicy 'never' in both stages; "
                    "'onRequest' and 'unlessTrusted' are what produce the approval "
                    "requests this contract treats as failures",
                    "policy", "profile-uncertified")
            if thread["sandbox"] != operands["sandbox"]:
                raise BoundaryError(
                    f"the {posture} thread sandbox must be {operands['sandbox']!r}",
                    "policy", "profile-uncertified")
            if turn["sandbox_policy"] != operands["sandbox_policy"]:
                raise BoundaryError(
                    f"the {posture} turn sandbox policy must be {operands['sandbox_policy']}",
                    "policy", "profile-uncertified")
            for stage in (thread, turn):
                if stage["cwd_role"] != operands["cwd_role"]:
                    raise BoundaryError(
                        f"the {posture} cwd role must be {operands['cwd_role']!r}",
                        "policy", "profile-uncertified")

    if profile["postures"]["consent"]["policy"] == profile["postures"]["execution"]["policy"]:
        raise BoundaryError(
            "consent and execution postures must pin different provider policy",
            "policy", "profile-uncertified")


def validate_profile(profile: dict) -> dict:
    """§4.2, §10.2-§10.3, §12.7a — THE certification entry point.

    Shape, then seal, then policy — in that order, because reading a policy
    field out of a document whose seal has not been checked is reading
    whatever the last writer put there.  Returns a private copy, so a caller
    that keeps a reference to the document it submitted cannot change the one
    this model went on to trust.
    """
    accepted = accept_document(profile)
    certify_profile_fields(accepted)
    return accepted


def validate_postures(profile: dict) -> dict:
    """Retained name for the posture rules; certification is one entry point."""
    return validate_profile(profile)


def answer_permission_request(_request: dict) -> dict:
    """§4.3 — the fixed ACP answer.  It selects nothing, in every ordering."""
    return {"outcome": {"outcome": "cancelled"}}


def permission_grants_anything(answer: dict) -> bool:
    return answer.get("outcome", {}).get("outcome") == "selected"


# --------------------------------------------------------------------------
# §5 turn outcome
# --------------------------------------------------------------------------

ACP_STOP_REASONS = {
    "end_turn": "completed",
    "refusal": "refused",
    "max_tokens": "truncated",
    "max_turn_requests": "truncated",
    "cancelled": "cancelled",
}

TURN_OUTCOMES = frozenset({
    "completed", "refused", "truncated", "cancelled",
    "agent-failed", "policy-failed", "timeout", "transport-lost",
})

# §5.2 — the last two say the relay does not know.
CONCLUSIVE_OUTCOMES = frozenset({
    "completed", "refused", "truncated", "cancelled", "agent-failed", "policy-failed",
})

PERMITTED_DISPOSITIONS = {
    "completed": frozenset({"completed", "unable", "plan-rejected"}),
    "refused": frozenset({"unable"}),
    "truncated": frozenset({"unable"}),
    "agent-failed": frozenset({"unable"}),
    "cancelled": frozenset(),
    "policy-failed": frozenset(),
    "timeout": frozenset(),
    "transport-lost": frozenset(),
}


def outcome_from_acp(stop_reason: str) -> str:
    if stop_reason not in ACP_STOP_REASONS:
        raise BoundaryError(f"unknown ACP stopReason {stop_reason!r}", "integrity", "schema")
    return ACP_STOP_REASONS[stop_reason]


def accept_result_declaration(outcome: str, disposition: str) -> str:
    """§5.5 — the turn outcome GATES the declaration; it never makes it."""
    if outcome not in TURN_OUTCOMES:
        raise BoundaryError(f"unknown turn outcome {outcome!r}", "integrity", "schema")
    if disposition not in PERMITTED_DISPOSITIONS[outcome]:
        raise BoundaryError(
            f"turn outcome {outcome!r} does not permit disposition {disposition!r}",
            "refused", "precondition")
    return disposition


def infer_outcome_from(evidence_kind: str) -> str:
    """§5.4 — every one of these is a refusal, not a shortcut."""
    raise BoundaryError(
        f"{evidence_kind} is not a turn outcome; it proves nothing about the turn",
        "refused", "precondition")


# --------------------------------------------------------------------------
# §6 update normalization
# --------------------------------------------------------------------------

EVENT_KINDS = frozenset({
    "agent-message", "agent-reasoning", "tool-call", "tool-call-update", "plan",
    "mode-change", "usage", "session-info", "commands-changed", "other",
})

ACP_UPDATE_KINDS = {
    "agent_message_chunk": "agent-message",
    "agent_thought_chunk": "agent-reasoning",
    "user_message_chunk": "other",
    "tool_call": "tool-call",
    "tool_call_update": "tool-call-update",
    "plan": "plan",
    "plan_update": "plan",
    "plan_removed": "plan",
    "current_mode_update": "mode-change",
    "config_option_update": "other",
    "session_info_update": "session-info",
    "usage_update": "usage",
    "available_commands_update": "commands-changed",
}

NORMALIZED_CONTENT_TYPES = frozenset({"text", "resource_link"})
DROPPED_CONTENT_TYPES = frozenset({"image", "audio", "resource"})


def normalize_acp_update(update: dict) -> str:
    """§6.1-§6.2.  An unmapped kind is COUNTED as 'other', never guessed at."""
    return ACP_UPDATE_KINDS.get(update.get("sessionUpdate"), "other")


def normalize_content(blocks: list) -> list:
    """§6.3 — text and resource links survive; bytes are counted and dropped."""
    normalized = []
    for block in blocks:
        block_type = block.get("type")
        if block_type in NORMALIZED_CONTENT_TYPES:
            normalized.append(copy.deepcopy(block))
        elif block_type in DROPPED_CONTENT_TYPES:
            normalized.append({
                "type": "dropped",
                "dropped_type": block_type,
                "byte_count": int(block.get("byte_count", 0)),
            })
        else:
            normalized.append({
                "type": "dropped",
                "dropped_type": "unknown",
                "byte_count": int(block.get("byte_count", 0)),
            })
    return normalized


def enforce_event_limit(event: dict, max_event_bytes: int) -> None:
    if len(canonical_bytes(event)) > max_event_bytes:
        raise BoundaryError("normalized event exceeds the negotiated byte limit",
                            "integrity", "limit")


@dataclass
class LedgerOutcome:
    """What the ledger DID, reported beside the document rather than in it.

    `late` and `observation_seq` live here and not in the sealed event for a
    concrete reason: both are properties of an OBSERVATION, not of the frame.
    A retransmitted frame is the same frame; if lateness were sealed into its
    bytes, the retransmission would carry a different digest and an ordinary
    duplicate would be indistinguishable from a spliced stream.
    """

    status: str
    event: dict | None
    source_seq: int
    late: bool = False
    observation_seq: int | None = None
    dropped_bytes: int = 0


@dataclass
class EventLedger:
    """§6.4 — per-epoch sequencing, duplicates, lateness.

    ONE contract crosses this boundary: the caller seals the event, and the
    ledger verifies that seal before it looks at anything else and answers
    with the same sealed BYTES.

    "Unchanged" means byte equality, not object identity.  The ledger deep-
    copies on the way in and on the way out, because an entry that aliased the
    caller's dictionary could be edited after acceptance — the seal would then
    be invalid on durable evidence nobody wrote to, and a later replay
    comparison would turn on whether some unrelated caller happened to keep a
    reference.  Immutable evidence that a caller can still reach is not
    immutable.
    """

    session_ref: dict
    max_event_bytes: int = 16000
    max_queue_events: int = 1024
    _seen: dict = field(default_factory=dict)
    _order: list = field(default_factory=list)
    _late: dict = field(default_factory=dict)
    _observation: dict = field(default_factory=dict)
    dropped_count: int = 0
    dropped_bytes: int = 0
    late_count: int = 0
    _next_observation_seq: int = 1
    _turn_ended: bool = False

    def __post_init__(self) -> None:
        validate_session_ref(self.session_ref)

    @property
    def epoch(self) -> int:
        return self.session_ref["session_epoch"]

    def end_turn(self) -> None:
        self._turn_ended = True

    def record(self, event: dict) -> LedgerOutcome:
        # The seal is checked FIRST.  Everything below trusts the bytes, so
        # nothing below may run against bytes whose digest was never verified.
        if "document_digest" not in event:
            raise BoundaryError(
                "the ledger consumes a sealed event; seal and validate it first",
                "integrity", "schema")
        verify_document_digest(event)

        if event.get("agent_session_ref") != self.session_ref:
            raise BoundaryError("event belongs to a different agent session",
                                "runtime-observation", "identity-mismatch")
        source_seq = event.get("source_seq")
        if not isinstance(source_seq, int) or isinstance(source_seq, bool) or source_seq < 1:
            raise BoundaryError("source_seq must be a positive integer",
                                "integrity", "schema")
        enforce_event_limit(event, self.max_event_bytes)
        if event.get("kind") not in EVENT_KINDS:
            raise BoundaryError(f"event kind {event.get('kind')!r} is outside the closed set",
                                "integrity", "schema")
        if event.get("redacted") is not True:
            raise BoundaryError("an event is redacted before it is durable",
                                "integrity", "schema")

        previous = self._seen.get(source_seq)
        if previous is not None:
            # Both sides are sealed, so the digests ARE the comparison.
            if previous["document_digest"] != event["document_digest"]:
                raise BoundaryError(
                    f"duplicate source_seq {source_seq} with different content",
                    "integrity", "digest")
            return LedgerOutcome("replayed", copy.deepcopy(previous), source_seq,
                                 late=self._late[source_seq],
                                 observation_seq=self._observation[source_seq])

        if len(self._order) >= self.max_queue_events:
            # §6.5 — dropping is allowed; dropping SILENTLY is not.
            size = len(canonical_bytes(event))
            self.dropped_count += 1
            self.dropped_bytes += size
            return LedgerOutcome("dropped", None, source_seq, dropped_bytes=size)

        late = self._turn_ended
        if late:
            self.late_count += 1
        observation_seq = self._next_observation_seq
        self._next_observation_seq += 1
        self._seen[source_seq] = copy.deepcopy(event)
        self._late[source_seq] = late
        self._observation[source_seq] = observation_seq
        self._order.append(source_seq)
        return LedgerOutcome("stored", copy.deepcopy(self._seen[source_seq]), source_seq,
                             late=late, observation_seq=observation_seq)

    @property
    def persisted(self) -> list:
        return [copy.deepcopy(self._seen[seq]) for seq in self._order]


# --------------------------------------------------------------------------
# §7 cancellation and the session axis
# --------------------------------------------------------------------------

SESSION_STATES = frozenset({
    "not-started", "initializing", "ready", "prompting", "turn-ended",
    "cancel-requested", "agent-quiescent", "unknown", "closed",
})

ALLOWED_SESSION_SUCCESSORS = {
    "not-started": {"initializing", "unknown"},
    "initializing": {"ready", "unknown", "closed"},
    "ready": {"prompting", "cancel-requested", "unknown", "closed"},
    "prompting": {"turn-ended", "cancel-requested", "unknown"},
    "turn-ended": {"prompting", "cancel-requested", "unknown", "closed"},
    "cancel-requested": {"agent-quiescent", "unknown"},
    "agent-quiescent": {"closed"},
    # §3.3 and §7.3: 'unknown' is terminal.  It is the honest end of an epoch
    # whose ending nobody observed, and promoting it to 'closed' would record
    # knowledge that was never acquired.
    "unknown": set(),
    "closed": set(),
}


@dataclass
class SessionAxis:
    state: str = "not-started"
    history: list = field(default_factory=lambda: ["not-started"])

    def observe(self, state: str) -> str:
        if state not in SESSION_STATES:
            raise BoundaryError(f"unknown agent session state {state!r}", "integrity", "schema")
        if state == self.state:
            return self.state
        if state not in ALLOWED_SESSION_SUCCESSORS[self.state]:
            raise BoundaryError(
                f"agent session state cannot move {self.state!r} -> {state!r}",
                "runtime-observation", "state-regression")
        self.state = state
        self.history.append(state)
        return self.state


@dataclass
class Cancellation:
    """§7.1-§7.2.  Ordering intent, then observing what the agent actually did."""

    generation_fenced: bool = False
    assignment_ended: bool = False
    ordered: bool = False
    observed: str | None = None

    def fence_and_end(self) -> None:
        self.generation_fenced = True
        self.assignment_ended = True

    def order_agent_cancel(self) -> None:
        if not (self.generation_fenced and self.assignment_ended):
            raise BoundaryError(
                "the authority must fence the generation and end the assignment before "
                "the agent is asked to cancel",
                "refused", "precondition")
        self.ordered = True

    def observe_terminal_fact(self, stop_reason: str | None) -> str:
        if not self.ordered:
            raise BoundaryError("no cancellation was ordered", "refused", "precondition")
        if stop_reason is None:
            self.observed = "agent-quiescence-unknown"
        else:
            # An agent that answers end_turn after cancellation was ordered keeps
            # its observed reason; relabelling it would erase what it did.
            self.observed = "agent-turn-cancelled"
        return self.observed


def satisfies_runtime_quiescence_gate(agent_session_state: str) -> bool:
    """§7.4 — the one function in this model that always returns False.

    A finished conversation says nothing about whether the runtime that held
    the generation is absent.  The gate is satisfied only by worker-control
    §6.3 runtime inspection reaching positive absence, or by W151's pinned
    certified-isolation clause.  Neither is an agent-session fact.
    """
    if agent_session_state not in SESSION_STATES:
        raise BoundaryError(f"unknown agent session state {agent_session_state!r}",
                            "integrity", "schema")
    return False


# --------------------------------------------------------------------------
# §8.4 reconnect
# --------------------------------------------------------------------------

def handle_transport_loss(session_ref: dict, turn_in_flight: bool) -> dict:
    """§8.4 — the epoch dies.  No resume, no re-prompt."""
    validate_session_ref(session_ref)
    return {
        "epoch": session_ref["session_epoch"],
        "posture": session_ref["posture"],
        "next_epoch_allowed_without_runtime_reidentification": False,
        "resume": False,
        "reprompt": False,
        "turn_outcome": "transport-lost" if turn_in_flight else None,
        "session_state": "unknown",
    }


def reprompt_after_transport_loss(_prompt: object) -> None:
    raise BoundaryError(
        "a turn in flight when the transport died may have run side effects the "
        "manager cannot enumerate; re-prompting is refused",
        "ambiguous", "operation")


# --------------------------------------------------------------------------
# §10 Codex App Server profile
# --------------------------------------------------------------------------

CODEX_TURN_STATUS = {
    "completed": "completed",
    "interrupted": "cancelled",
    "failed": "agent-failed",
}

CODEX_ERROR_INFO = {
    "ContextWindowExceeded": ("truncated", "unavailable", "source-provider"),
    "UsageLimitExceeded": ("agent-failed", "unavailable", "source-provider"),
    "HttpConnectionFailed": ("agent-failed", "unavailable", "transport"),
    "ResponseStreamConnectionFailed": ("agent-failed", "unavailable", "transport"),
    "ResponseStreamDisconnected": ("agent-failed", "unavailable", "transport"),
    "ResponseTooManyFailedAttempts": ("agent-failed", "unavailable", "transport"),
    "Unauthorized": ("agent-failed", "policy", "denied"),
    "SandboxError": ("agent-failed", "policy", "denied"),
    "BadRequest": ("agent-failed", "unavailable", "source-provider"),
    "InternalServerError": ("agent-failed", "unavailable", "source-provider"),
    "Other": ("agent-failed", "unavailable", "source-provider"),
}

CODEX_ITEM_KINDS = {
    "agentMessage": "agent-message",
    "reasoning": "agent-reasoning",
    "plan": "plan",
    "userMessage": "other",
    "commandExecution": "tool-call",
    "fileChange": "tool-call",
    "mcpToolCall": "tool-call",
    "collabToolCall": "tool-call",
    "webSearch": "tool-call",
    "imageView": "tool-call",
    "contextCompaction": "other",
    "enteredReviewMode": "other",
    "exitedReviewMode": "other",
}

# §10.5 — the denial payload is request-family-specific, because each family's
# reply has its own documented shape.  A generic "decline" string is not valid
# JSON-RPC for the permissions or elicitation families.
CODEX_APPROVAL_FAMILIES = frozenset({
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/permissions/requestApproval",
    "mcpServer/elicitation/request",
})

# The provider's own response schema for each family, captured under
# provider-schemas/codex-app-server/ and bound by the certified interface
# digest.  Conformance is validated against these, never against a payload
# this record authored.
CODEX_RESPONSE_SCHEMAS = {
    "item/commandExecution/requestApproval": "CommandExecutionRequestApprovalResponse.json",
    "item/fileChange/requestApproval": "FileChangeRequestApprovalResponse.json",
    "item/permissions/requestApproval": "PermissionsRequestApprovalResponse.json",
    "mcpServer/elicitation/request": "McpServerElicitationRequestResponse.json",
}

CODEX_GRANTING_ANSWERS = frozenset({
    "accept", "acceptForSession", "acceptWithExecpolicyAmendment",
})

CODEX_APPROVAL_POLICIES = frozenset({"never", "onRequest", "unlessTrusted"})
CODEX_SANDBOX_TYPES = frozenset({"readOnly", "workspaceWrite", "dangerFullAccess", "externalSandbox"})

CODEX_EXCLUDED_METHODS = frozenset({
    # experimental
    "process/spawn", "process/writeStdin", "process/resizePty", "process/kill",
    "thread/turns/list", "thread/items/list",
    "thread/backgroundTerminals/clean", "thread/backgroundTerminals/list",
    "thread/backgroundTerminals/terminate",
    "experimentalFeature/list", "environment/info",
    "permissionProfile/list", "collaborationMode/list", "tool/requestUserInput",
    # under development
    "plugin/list", "plugin/read", "plugin/install", "plugin/uninstall",
    # deprecated
    "thread/rollback",
    # history-bearing, refused by §2.3
    "thread/resume", "thread/fork", "thread/read", "thread/list",
    "thread/loaded/list", "thread/inject_items",
    # host-application capability, outside this boundary entirely
    "command/exec", "command/exec/write", "command/exec/resize", "command/exec/terminate",
    "thread/shellCommand", "fs/readFile", "fs/writeFile", "fs/createDirectory",
    "fs/getMetadata", "fs/readDirectory", "fs/remove", "fs/copy", "fs/watch",
    "config/read", "config/value/write", "config/batchWrite", "configRequirements/read",
    "config/mcpServer/reload", "skills/list", "skills/extraRoots/set", "skills/config/write",
    "hooks/list", "marketplace/add", "marketplace/remove", "marketplace/upgrade",
    "app/installed", "app/list", "app/read", "mcpServer/oauth/login",
    "mcpServer/resource/read", "mcpServer/tool/call", "mcpServerStatus/list",
    "model/list", "modelProvider/capabilities/read", "feedback/upload",
    "windowsSandbox/setupStart", "externalAgentConfig/detect",
    "externalAgentConfig/import", "review/start",
})

# §10.2 — all four are adapter diagnostics.  'idle' in particular is a thread
# with no active turn; it is not quiescence of anything.
CODEX_THREAD_STATUS = frozenset({"notLoaded", "idle", "systemError", "active"})


def codex_initialize_capabilities() -> dict:
    """§10.1 — the exclusion is enforced at the handshake."""
    return {"experimentalApi": False}


def codex_call(method: str) -> None:
    if method in CODEX_EXCLUDED_METHODS:
        raise BoundaryError(
            f"{method} is excluded from the Codex App Server profile",
            "refused", "capability")


def _cwd_for(role: str, cwd_by_role: dict) -> str:
    """The caller supplies the role->path map; the PROFILE chooses the role.

    Taking a bare path here is how an execution workspace ends up mounted into
    a consent session that pinned a scratch root.
    """
    if role not in cwd_by_role:
        raise BoundaryError(f"no path was supplied for the pinned cwd role {role!r}",
                            "policy", "denied")
    return cwd_by_role[role]


def codex_thread_start_operands(binding: dict, cwd_by_role: dict) -> dict:
    """§10.2 — the complete pinned thread/start request."""
    pinned = binding["policy"]
    if pinned["kind"] != "codex-app-server":
        raise BoundaryError("this posture is not pinned by an App Server policy",
                            "policy", "denied")
    thread = pinned["thread_start"]
    return {
        "model": thread["model"],
        "cwd": _cwd_for(thread["cwd_role"], cwd_by_role),
        "approvalPolicy": thread["approval_policy"],
        "sandbox": thread["sandbox"],
    }


def codex_turn_start_operands(binding: dict, thread_id: str, cwd_by_role: dict,
                              prompt: str) -> dict:
    """§10.3 — the complete pinned turn/start request.

    turn/start may OVERRIDE the thread default, so the policy is re-pinned on
    every turn.  An unpinned turn silently inherits, and a thread-level
    default nobody restated is not a pinned policy.
    """
    pinned = binding["policy"]
    turn = pinned["turn_start"]
    sandbox_policy = {"type": turn["sandbox_policy"]["type"]}
    if "network_access" in turn["sandbox_policy"]:
        sandbox_policy["networkAccess"] = turn["sandbox_policy"]["network_access"]
    return {
        "threadId": thread_id,
        "input": [{"type": "text", "text": prompt}],
        "model": turn["model"],
        "cwd": _cwd_for(turn["cwd_role"], cwd_by_role),
        "approvalPolicy": turn["approval_policy"],
        "sandboxPolicy": sandbox_policy,
    }


def codex_check_policy_drift(pinned: dict, observed: dict) -> None:
    """§10.2-§10.3 — any divergence from the certified operands is a failure."""
    if observed["kind"] != "codex-app-server":
        raise BoundaryError("observed policy is not an App Server policy", "policy", "denied")
    for stage in ("thread_start", "turn_start"):
        if observed[stage]["approval_policy"] not in CODEX_APPROVAL_POLICIES:
            raise BoundaryError(f"unknown approval policy in {stage}", "integrity", "schema")
        if pinned[stage] != observed[stage]:
            raise BoundaryError(
                f"{stage} policy drifted from the certified operands: "
                f"{observed[stage]} is not {pinned[stage]}",
                "policy", "denied")


def codex_turn_outcome(status: str, error_info: str | None = None) -> tuple:
    """§10.3 and §10.6.  Returns (turn outcome, category, code).

    The App Server's three terminal statuses do not include ACP's `refusal`,
    `max_tokens` or `max_turn_requests`.  Only `ContextWindowExceeded` reports
    budget exhaustion structurally, so it is the one failure that becomes
    `truncated`; nothing here is synthesized from prose or token counts.
    """
    if status not in CODEX_TURN_STATUS:
        raise BoundaryError(f"unknown Codex turn status {status!r}", "integrity", "schema")
    outcome = CODEX_TURN_STATUS[status]
    if status != "failed":
        return outcome, None, None
    # An unrecognized codexErrorInfo takes the last row rather than inventing one.
    return CODEX_ERROR_INFO.get(error_info, CODEX_ERROR_INFO["Other"])


def codex_deny_approval(method: str, cancelling: bool = False) -> dict:
    """§10.5 — the complete typed denial RESPONSE for each family.

    Every one is an object, because every one of the provider's four response
    schemas is an object.  `"decline"` on its own is the decision MEMBER, not
    the response: the command and file families require `{"decision": ...}`,
    and a reply the provider cannot parse leaves the request hanging, which is
    a worse failure than an honest grant would be.  The captured schemas in
    `provider-schemas/codex-app-server/` are what the tests validate against;
    an equality assertion against a payload this file authored proves only
    that this file is self-consistent.
    """
    if method not in CODEX_APPROVAL_FAMILIES:
        raise BoundaryError(f"{method} is not answerable under this profile",
                            "refused", "capability")
    if method in ("item/commandExecution/requestApproval", "item/fileChange/requestApproval"):
        return {"decision": "cancel" if cancelling else "decline"}
    if method == "item/permissions/requestApproval":
        # The response carries the GRANTED SUBSET, so the denial is the empty
        # subset at the narrowest scope.  No cancel form is documented and
        # none is needed: an empty subset grants nothing in either ordering.
        return {"permissions": {}, "scope": "turn"}
    return {"action": "cancel" if cancelling else "decline", "content": None}


def codex_answer_grants_anything(method: str, answer: object) -> bool:
    if isinstance(answer, str):
        # A bare decision member is not a valid response, but if one is
        # presented for judgement it is still judged on what it would grant.
        return answer in CODEX_GRANTING_ANSWERS
    if isinstance(answer, dict):
        if "decision" in answer:
            decision = answer["decision"]
            if isinstance(decision, dict):
                return "acceptWithExecpolicyAmendment" in decision
            return decision in CODEX_GRANTING_ANSWERS
        if "acceptWithExecpolicyAmendment" in answer:
            return True
        if "permissions" in answer:
            return bool(answer["permissions"])
        if "action" in answer:
            return answer["action"] == "accept"
    return False


def codex_normalize_item(item_type: str) -> str:
    if item_type == "dynamicToolCall":
        raise BoundaryError("dynamicToolCall is experimental and is refused",
                            "refused", "capability")
    return CODEX_ITEM_KINDS.get(item_type, "other")


def codex_thread_status_is_quiescence(status: str) -> bool:
    """§10.2 — the most plausible error available in this profile."""
    if status not in CODEX_THREAD_STATUS:
        raise BoundaryError(f"unknown Codex thread status {status!r}", "integrity", "schema")
    return False
