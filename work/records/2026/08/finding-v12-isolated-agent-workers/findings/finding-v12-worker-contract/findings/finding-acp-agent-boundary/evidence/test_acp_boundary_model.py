"""Design-level tests for baton.agent-session 1.0.

Provider-free.  Runs with `python3 -B -m unittest -q test_acp_boundary_model`
from this directory.

The schema documents and the semantic model are exercised through ONE object
graph: every trace builds schema-shaped sealed documents, validates them, and
feeds those same documents to the model.  The first round of this design kept
two shapes for the same event and proved different things with each.
"""

from __future__ import annotations

import copy
import json
import pathlib
import unittest

from jsonschema import Draft7Validator, Draft202012Validator

import acp_boundary_model as m

HERE = pathlib.Path(__file__).resolve().parent
RECORD = HERE.parent
SCHEMA_PATH = RECORD / "schema" / "agent-session-1.0.schema.json"
OUTER_SCHEMA_PATH = (RECORD.parent / "finding-worker-control-api-manifests"
                     / "schema" / "worker-control-1.0.schema.json")

SCHEMA = json.loads(SCHEMA_PATH.read_text())
OUTER_SCHEMA = json.loads(OUTER_SCHEMA_PATH.read_text())
TRACES = json.loads((HERE / "traces.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)

PROFILES = {profile["profile_id"]: profile for profile in TRACES["profiles"]}
ACP_PROFILE = PROFILES["profile-acp-worker-1"]
CODEX_PROFILE = PROFILES["profile-codex-app-server-1"]

PROVIDER_SCHEMAS = HERE / "provider-schemas" / "codex-app-server"
PROVIDER_VALIDATORS = {
    method: Draft7Validator(json.loads((PROVIDER_SCHEMAS / filename).read_text()))
    for method, filename in m.CODEX_RESPONSE_SCHEMAS.items()
}

FULL_METHODS = set(m.REQUIRED_AGENT_METHODS) | {"session/set_mode", "session/close"}
WORK_REF = {"authority_uuid": "43c55d4b00ee85c84ae4ed134de36df5",
            "work_id": "43c55d4b-W1440"}
OTHER_WORK_REF = {"authority_uuid": "43c55d4b00ee85c84ae4ed134de36df5",
                  "work_id": "43c55d4b-W9999"}
CWD = {"scratch": "/scratch", "workspace": "/workspace"}
SIX = sorted(m.SESSION_CAPABILITIES)
JOURNAL = {"purpose": "log",
           "artifact": {"artifact_id": "relay-journal-1",
                        "media_type": "application/x-ndjson",
                        "bytes": 4096,
                        "content_digest": "sha256:" + "ab" * 32,
                        "locator": "artifact:relay-journal/attempt-1"}}


def modes(current: str, available: list) -> dict:
    return {"currentModeId": current, "availableModes": [{"id": i, "name": i} for i in available]}


def assignment(work_ref: dict, generation: int = 7) -> dict:
    return {"work_ref": copy.deepcopy(work_ref), "participant": "baton.claude",
            "generation": generation}


class TraceRunner:
    """Drives one trace through the model, building real schema documents."""

    def __init__(self, trace: dict) -> None:
        self.trace = trace
        self.profile = PROFILES[trace["profile"]]
        self.attempt = m.AttemptSessions("attempt-1")
        self.refs: dict = {}
        self.axes: dict = {}
        self.ledgers: dict = {}
        self.records: dict = {}
        self.epochs: dict = {}
        self.posture = None
        self.assignment_ref = None
        self.outcome = None
        self.accepted = None
        self.event_kinds: list = []
        self.observed_policy = None
        self.permission_answer = None
        self.codex_answer = None
        self.codex_answer_method = None
        self.transport = None
        self.reported_as = None
        self.experimental_api = None
        self.interrupt_reply = None
        self.cancellation_observed = None
        self.promotion_error = None
        self.thread_start_operands = None
        self.turn_start_operands = None
        self.cancellation = m.Cancellation()

    # -- helpers ------------------------------------------------------------

    @property
    def ref(self) -> dict:
        return self.refs[self.posture]

    @property
    def axis(self) -> m.SessionAxis:
        return self.axes[self.posture]

    @property
    def ledger(self) -> m.EventLedger:
        return self.ledgers[self.posture]

    @property
    def binding(self) -> dict:
        return self.profile["postures"][self.posture]

    def run(self) -> "TraceRunner":
        for step in self.trace["steps"]:
            getattr(self, "_" + step["step"])(step)
        self._seal_record()
        return self

    def _seal_record(self) -> None:
        if self.posture is None:
            return
        cancellation = None
        if self.cancellation.observed is not None:
            cancellation = {
                "ordered_at": "2026-08-21T22:06:00.000Z",
                "order_delivered": True,
                "drain_deadline_at": "2026-08-21T22:06:30.000Z",
                "observed": self.cancellation.observed,
                "observed_at": "2026-08-21T22:06:04.000Z",
                "satisfies_runtime_quiescence_gate": False,
            }
        record = m.seal_document({
            "session_family": "baton.agent-session",
            "version": {"major": 1, "minor": 0},
            "document": "session",
            "record_id": f"session-{self.posture}-{self.ref['session_epoch']}",
            "created_at": "2026-08-21T22:05:00.000Z",
            "agent_session_ref": copy.deepcopy(self.ref),
            "posture": self.posture,
            "profile_digest": self.profile["document_digest"],
            "work_ref": copy.deepcopy(WORK_REF),
            "assignment_ref": copy.deepcopy(self.assignment_ref)
            if self.posture == "execution" else None,
            "negotiated_wire_version": 1 if self.profile["wire_protocol"] == "acp" else None,
            "advertised_client_capabilities": copy.deepcopy(m.MINIMAL_CLIENT_CAPABILITIES)
            if self.profile["wire_protocol"] == "acp" else None,
            "negotiated_session_capabilities": SIX,
            "pinned_policy": copy.deepcopy(self.binding["policy"]),
            "observed_policy": copy.deepcopy(self.observed_policy),
            "state": self.axis.state,
            "state_history": [{"state": state, "observed_at": "2026-08-21T22:05:00.000Z"}
                              for state in self.axis.history],
            "cancellation": cancellation,
            "turn_ids": [],
            "journal": copy.deepcopy(JOURNAL),
            "adapter_diagnostics": {},
        })
        self.records[self.posture] = record

    # -- session lifecycle --------------------------------------------------

    def _open_session(self, step: dict) -> None:
        if self.posture is not None:
            self._seal_record()
        posture = step["posture"]
        ref = self.attempt.open_session(posture, f"prov-{posture}-1")
        self.posture = posture
        self.refs[posture] = ref
        self.epochs[posture] = ref["session_epoch"]
        self.axes[posture] = m.SessionAxis()
        self.ledgers[posture] = m.EventLedger(
            copy.deepcopy(ref), max_event_bytes=self.profile["limits"]["max_event_bytes"])
        self.observed_policy = None
        self.outcome = None
        self.cancellation = m.Cancellation()

    def _end_session(self, step: dict) -> None:
        self._seal_record()
        self.attempt.end_session(step["posture"])

    def _assert_no_promotion(self, _step: dict) -> None:
        try:
            self.attempt.promote_consent_to_execution()
        except m.BoundaryError as error:
            self.promotion_error = error
            return
        raise AssertionError("promoting a consent session must refuse")

    def _settle_claim(self, step: dict) -> None:
        self.assignment_ref = assignment(WORK_REF, step["generation"])

    # -- native ACP steps ---------------------------------------------------

    def _negotiate(self, step: dict) -> None:
        self.axis.observe("initializing")
        m.negotiate_acp(self.profile, step["agent_wire_version"], FULL_METHODS,
                        m.SESSION_CAPABILITIES)

    def _enforce_mode(self, step: dict) -> None:
        policy = m.PinnedPolicy.from_binding(self.posture, self.binding)
        observed = policy.enforce(modes(step["current_mode_id"], step["available_modes"]))
        self.observed_policy = {"kind": "acp", "session_mode_id": observed}
        self.axis.observe("ready")

    def _prompt(self, _step: dict) -> None:
        self.axis.observe("prompting")

    def _update(self, step: dict) -> None:
        kind = m.normalize_acp_update(step["update"])
        event = {
            "session_family": "baton.agent-session",
            "version": {"major": 1, "minor": 0},
            "document": "event",
            "agent_session_ref": copy.deepcopy(self.ref),
            "source_seq": step["source_seq"],
            "observed_at": "2026-08-21T22:05:02.000Z",
            "turn_id": None,
            "kind": kind,
            "source_kind": step["update"]["sessionUpdate"],
            "content": m.normalize_content(
                [step["update"]["content"]] if "content" in step["update"] else []),
            "tool_call": m.normalize_tool_call(step["update"])
            if "toolCallId" in step["update"] else None,
            "byte_count": 128,
            "redacted": True,
            "adapter_diagnostics": {},
        }
        # ONE contract: seal, validate, then hand THAT object to the ledger.
        sealed = m.seal_document(event)
        VALIDATOR.validate(sealed)
        outcome = self.ledger.record(sealed)
        assert outcome.event is None or outcome.event == sealed, \
            "the ledger returns the document it was given, unchanged"
        if step.get("expect_replay"):
            assert outcome.status == "replayed", "an identical duplicate must replay"
        else:
            assert outcome.status == "stored"
            self.event_kinds.append(kind)
        if step.get("expect_late"):
            assert outcome.late is True, "an event after the turn's terminal fact is late"

    def _acp_stop_reason(self, step: dict) -> None:
        self.outcome = m.outcome_from_acp(step["value"])
        self.ledger.end_turn()
        self.axis.observe("turn-ended")

    def _declare_result(self, step: dict) -> None:
        self.accepted = m.accept_result_declaration(self.outcome, step["disposition"])

    def _fence_and_end(self, _step: dict) -> None:
        self.cancellation.fence_and_end()

    def _order_cancel(self, _step: dict) -> None:
        self.cancellation.order_agent_cancel()
        self.axis.observe("cancel-requested")

    def _observe_terminal_fact(self, step: dict) -> None:
        self.cancellation_observed = self.cancellation.observe_terminal_fact(step["stop_reason"])
        if step["stop_reason"] is None:
            self.outcome = "timeout"
            self.reported_as = {"category": "runtime-observation", "code": "quiescence-unknown"}
            self.axis.observe("unknown")
        else:
            self.outcome = m.outcome_from_acp(step["stop_reason"])
            self.axis.observe("agent-quiescent")

    def _transport_loss(self, step: dict) -> None:
        self.transport = m.handle_transport_loss(self.ref, step["turn_in_flight"])
        self.outcome = self.transport["turn_outcome"]
        self.axis.observe("unknown")

    def _permission_request(self, step: dict) -> None:
        self.permission_answer = m.answer_permission_request(step["request"])
        if self.outcome is None:
            self.outcome = "policy-failed"
            self.reported_as = {"category": "policy", "code": "denied"}

    # -- Codex App Server steps --------------------------------------------

    def _bind_provider(self, step: dict) -> None:
        self.axis.observe("initializing")
        self.experimental_api = m.codex_initialize_capabilities()["experimentalApi"]
        m.bind_provider(self.profile, step["server_build_id"], step["interface_digest"])

    def _pin_codex_policy(self, _step: dict) -> None:
        pinned = self.binding["policy"]
        self.thread_start_operands = m.codex_thread_start_operands(self.binding, CWD)
        self.turn_start_operands = m.codex_turn_start_operands(
            self.binding, "thread-1", CWD, "do the work")
        self.observed_policy = copy.deepcopy(pinned)
        m.codex_check_policy_drift(pinned, self.observed_policy)
        self.axis.observe("ready")

    def _observe_codex_policy(self, step: dict) -> None:
        pinned = self.binding["policy"]
        observed = copy.deepcopy(pinned)
        observed["turn_start"]["approval_policy"] = step["approval_policy"]
        observed["turn_start"]["sandbox_policy"] = step["sandbox_policy"]
        self.observed_policy = observed
        try:
            m.codex_check_policy_drift(pinned, observed)
        except m.BoundaryError as error:
            self.outcome = "policy-failed"
            self.reported_as = {"category": error.category, "code": error.code}
            return
        raise AssertionError("drifted provider policy must refuse")

    def _codex_item(self, step: dict) -> None:
        self.event_kinds.append(m.codex_normalize_item(step["item_type"]))

    def _codex_turn_interrupt(self, _step: dict) -> None:
        self.cancellation.order_agent_cancel()
        self.interrupt_reply = {"accepted_for_processing": True}
        self.axis.observe("cancel-requested")

    def _codex_turn_completed(self, step: dict) -> None:
        outcome, category, code = m.codex_turn_outcome(step["status"], step.get("error_info"))
        self.outcome = outcome
        if category is not None:
            self.reported_as = {"category": category, "code": code}
        if step["status"] == "interrupted":
            self.cancellation_observed = self.cancellation.observe_terminal_fact("interrupted")
            self.axis.observe("agent-quiescent")
        else:
            self.axis.observe("turn-ended")

    def _codex_approval(self, step: dict) -> None:
        self.codex_answer = m.codex_deny_approval(step["method"])
        self.codex_answer_method = step["method"]
        self.outcome = "policy-failed"
        self.reported_as = {"category": "policy", "code": "denied"}


# ==========================================================================
# Schema fidelity
# ==========================================================================

class SchemaTests(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)

    def test_shared_definitions_are_byte_identical_to_worker_control(self) -> None:
        """A document valid here must not be invalid under the frozen contract."""
        for name in m.SHARED_WORKER_CONTROL_DEFS:
            with self.subTest(definition=name):
                self.assertIn(name, OUTER_SCHEMA["$defs"], "the outer contract owns this name")
                self.assertEqual(SCHEMA["$defs"][name], OUTER_SCHEMA["$defs"][name])

    def test_local_integer_bounds_match_the_outer_contract(self) -> None:
        outer = OUTER_SCHEMA["$defs"]["assignmentRef"]["properties"]["generation"]
        self.assertEqual(SCHEMA["$defs"]["positiveInt"], outer)
        outer_bytes = OUTER_SCHEMA["$defs"]["artifactRef"]["properties"]["bytes"]
        self.assertEqual(SCHEMA["$defs"]["nonNegativeInt"], outer_bytes)

    def test_error_pairs_in_schema_match_the_closed_taxonomy_exactly(self) -> None:
        pairs = {}
        for branch in SCHEMA["$defs"]["errorCategoryCode"]["oneOf"]:
            pairs[branch["properties"]["category"]["const"]] = set(
                branch["properties"]["code"]["enum"])
        self.assertEqual(pairs, m.WORKER_CONTROL_ERRORS)

    def test_trace_profiles_validate_and_reseal(self) -> None:
        for profile in TRACES["profiles"]:
            with self.subTest(profile=profile["profile_id"]):
                VALIDATOR.validate(profile)
                m.verify_document_digest(profile)
                self.assertEqual(m.seal_document(profile), profile)
                m.validate_postures(profile)

    def test_tampered_profile_digest_refuses(self) -> None:
        tampered = dict(ACP_PROFILE, pinned_wire_version=99)
        with self.assertRaises(m.BoundaryError) as caught:
            m.verify_document_digest(tampered)
        self.assertEqual((caught.exception.category, caught.exception.code), ("integrity", "digest"))

    def test_work_id_zero_is_refused_by_the_shared_definition(self) -> None:
        bad = {"authority_uuid": "43c55d4b00ee85c84ae4ed134de36df5", "work_id": "43c55d4b-W0"}
        self.assertFalse(Draft202012Validator(
            {**SCHEMA, "$ref": "#/$defs/workRef"}).is_valid(bad))

    def test_profile_shapes_are_conditional_on_the_wire_protocol(self) -> None:
        acp_with_binding = m.seal_document(dict(
            {k: v for k, v in ACP_PROFILE.items() if k != "document_digest"},
            provider_binding=CODEX_PROFILE["provider_binding"]))
        self.assertFalse(VALIDATOR.is_valid(acp_with_binding),
                         "an ACP profile negotiates a version and has no provider binding")
        codex_with_version = m.seal_document(dict(
            {k: v for k, v in CODEX_PROFILE.items() if k != "document_digest"},
            pinned_wire_version=1))
        self.assertFalse(VALIDATOR.is_valid(codex_with_version),
                         "the App Server documents no protocolVersion to pin")
        codex_with_acp_policy = copy.deepcopy(
            {k: v for k, v in CODEX_PROFILE.items() if k != "document_digest"})
        codex_with_acp_policy["postures"]["execution"]["policy"] = {
            "kind": "acp", "session_mode_id": "acceptEdits"}
        self.assertFalse(VALIDATOR.is_valid(m.seal_document(codex_with_acp_policy)),
                         "an ACP session_mode_id is not an App Server policy")

    def test_certified_profile_cannot_pin_an_approving_policy(self) -> None:
        for stage in ("thread_start", "turn_start"):
            with self.subTest(stage=stage):
                bad = copy.deepcopy(
                    {k: v for k, v in CODEX_PROFILE.items() if k != "document_digest"})
                bad["postures"]["execution"]["policy"][stage]["approval_policy"] = "onRequest"
                self.assertFalse(VALIDATOR.is_valid(m.seal_document(bad)))
        danger = copy.deepcopy({k: v for k, v in CODEX_PROFILE.items() if k != "document_digest"})
        danger["postures"]["execution"]["policy"]["turn_start"]["sandbox_policy"] = {
            "type": "dangerFullAccess"}
        self.assertFalse(VALIDATOR.is_valid(m.seal_document(danger)))

    def test_schema_rejects_the_three_forbidden_session_bindings(self) -> None:
        good = self.session_skeleton("execution", assignment(WORK_REF))
        VALIDATOR.validate(good)
        m.validate_session_binding_fields(good)

        execution_without = self.session_skeleton("execution", None)
        self.assertFalse(VALIDATOR.is_valid(execution_without))

        consent_with = self.session_skeleton("consent", assignment(WORK_REF))
        self.assertFalse(VALIDATOR.is_valid(consent_with))

        mismatched = self.session_skeleton("execution", assignment(WORK_REF), ref_posture="consent")
        self.assertFalse(VALIDATOR.is_valid(mismatched))

        # Cross-Work binding is shape-valid and must be caught semantically.
        cross = self.session_skeleton("execution", assignment(OTHER_WORK_REF))
        self.assertTrue(VALIDATOR.is_valid(cross))
        with self.assertRaises(m.BoundaryError) as caught:
            m.validate_session_binding_fields(cross)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_normalized_events_are_sealed(self) -> None:
        event = self.event_skeleton()
        self.assertFalse(VALIDATOR.is_valid(event), "an unsealed event is not a document")
        sealed = m.seal_document(event)
        VALIDATOR.validate(sealed)
        m.verify_document_digest(sealed)
        tampered = dict(sealed, kind="tool-call")
        with self.assertRaises(m.BoundaryError) as caught:
            m.verify_document_digest(tampered)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "digest"))

    def test_profile_cannot_restate_the_version_owned_method_or_capability_sets(self) -> None:
        """Two live sources of truth is how a profile comes to disagree with policy."""
        for gone in ("required_agent_methods", "refused_agent_methods"):
            with self.subTest(member=gone):
                self.assertNotIn(gone, SCHEMA["$defs"]["sessionProfile"]["properties"])
                widened = dict({k: v for k, v in ACP_PROFILE.items()
                                if k != "document_digest"}, **{gone: ["session/new"]})
                self.assertFalse(VALIDATOR.is_valid(m.seal_document(widened)))
        narrow = m.seal_document(dict(
            {k: v for k, v in ACP_PROFILE.items() if k != "document_digest"},
            session_capabilities=["session.prompt"]))
        self.assertFalse(VALIDATOR.is_valid(narrow),
                         "the version owns the capability list, not the profile")
        with self.assertRaises(m.BoundaryError) as fields:
            m.certify_profile_fields(narrow)
        self.assertEqual((fields.exception.category, fields.exception.code),
                         ("policy", "profile-uncertified"))
        with self.assertRaises(m.BoundaryError) as entry:
            m.validate_profile(narrow)
        self.assertEqual((entry.exception.category, entry.exception.code),
                         ("integrity", "schema"),
                         "the entry point refuses on shape before it reads policy")

    def test_codex_posture_policies_cannot_be_swapped(self) -> None:
        base = copy.deepcopy({k: v for k, v in CODEX_PROFILE.items()
                              if k != "document_digest"})
        base["postures"]["consent"]["policy"], base["postures"]["execution"]["policy"] = (
            copy.deepcopy(base["postures"]["execution"]["policy"]),
            copy.deepcopy(base["postures"]["consent"]["policy"]))
        swapped = m.seal_document(base)
        self.assertFalse(VALIDATOR.is_valid(swapped),
                         "a consent posture cannot pin workspaceWrite")
        with self.assertRaises(m.BoundaryError) as fields:
            m.certify_profile_fields(swapped)
        self.assertEqual((fields.exception.category, fields.exception.code),
                         ("policy", "profile-uncertified"))
        with self.assertRaises(m.BoundaryError) as entry:
            m.validate_profile(swapped)
        self.assertEqual((entry.exception.category, entry.exception.code),
                         ("integrity", "schema"))

    def test_posture_workspace_invariants_are_schema_constants(self) -> None:
        for posture, member, value in (("consent", "workspace", True),
                                       ("consent", "declared_output", True),
                                       ("execution", "workspace", False),
                                       ("execution", "declared_output", False)):
            with self.subTest(posture=posture, member=member):
                bad = copy.deepcopy({k: v for k, v in ACP_PROFILE.items()
                                     if k != "document_digest"})
                bad["postures"][posture][member] = value
                self.assertFalse(VALIDATOR.is_valid(m.seal_document(bad)))

    def test_schema_rejects_inline_bytes_unredacted_events_and_open_kinds(self) -> None:
        base = m.seal_document(self.event_skeleton())
        VALIDATOR.validate(base)
        for name, mutation in (
            ("inline image", {"content": [{"type": "image", "data": "AAAA"}]}),
            ("unredacted", {"redacted": False}),
            ("open kind", {"kind": "agent-said-it-finished"}),
            ("zero seq", {"source_seq": 0}),
            ("resealed lateness", {"late": True}),
            ("resealed observation seq", {"observation_seq": 7}),
        ):
            with self.subTest(mutation=name):
                self.assertFalse(VALIDATOR.is_valid(m.seal_document(
                    dict({k: v for k, v in base.items() if k != "document_digest"}, **mutation))))

    def test_invalid_policy_failure_documents_are_refused(self) -> None:
        turn = m.seal_document(self.turn_skeleton([]))
        VALIDATOR.validate(turn)
        for name, failure in TRACES["invalid_policy_failure_documents"].items():
            with self.subTest(vector=name):
                candidate = m.seal_document(self.turn_skeleton([failure]))
                self.assertFalse(VALIDATOR.is_valid(candidate))

    def test_schema_rejects_a_cancellation_claiming_to_satisfy_the_gate(self) -> None:
        honest = {
            "ordered_at": "2026-08-21T22:06:00.000Z",
            "order_delivered": True,
            "drain_deadline_at": "2026-08-21T22:06:30.000Z",
            "observed": "agent-turn-cancelled",
            "observed_at": "2026-08-21T22:06:04.000Z",
            "satisfies_runtime_quiescence_gate": False,
        }
        base = {k: v for k, v in self.session_skeleton("execution", assignment(WORK_REF)).items()
                if k != "document_digest"}
        VALIDATOR.validate(m.seal_document(dict(base, cancellation=honest)))
        claiming = m.seal_document(dict(base, cancellation=dict(
            honest, satisfies_runtime_quiescence_gate=True)))
        self.assertFalse(VALIDATOR.is_valid(claiming),
                         "an agent session cannot satisfy the runtime-quiescence gate")

    # -- skeletons ----------------------------------------------------------

    @staticmethod
    def session_skeleton(posture: str, assignment_ref, ref_posture: str | None = None) -> dict:
        return m.seal_document({
            "session_family": "baton.agent-session",
            "version": {"major": 1, "minor": 0},
            "document": "session",
            "record_id": "session-1",
            "created_at": "2026-08-21T22:05:00.000Z",
            "agent_session_ref": {"runtime_attempt_id": "attempt-1",
                                  "posture": ref_posture or posture,
                                  "session_epoch": 1, "provider_session_id": "sess_01ABC"},
            "posture": posture,
            "profile_digest": ACP_PROFILE["document_digest"],
            "work_ref": copy.deepcopy(WORK_REF),
            "assignment_ref": copy.deepcopy(assignment_ref),
            "negotiated_wire_version": 1,
            "advertised_client_capabilities": copy.deepcopy(m.MINIMAL_CLIENT_CAPABILITIES),
            "negotiated_session_capabilities": SIX,
            "pinned_policy": {"kind": "acp", "session_mode_id": "acceptEdits"},
            "observed_policy": {"kind": "acp", "session_mode_id": "acceptEdits"},
            "state": "turn-ended",
            "state_history": [{"state": "not-started", "observed_at": "2026-08-21T22:05:00.000Z"}],
            "cancellation": None,
            "turn_ids": ["turn-1"],
            "journal": copy.deepcopy(JOURNAL),
            "adapter_diagnostics": {"org.example.native-acp-relay/1": {"frames": 12}},
        })

    @staticmethod
    def event_skeleton() -> dict:
        return {
            "session_family": "baton.agent-session",
            "version": {"major": 1, "minor": 0},
            "document": "event",
            "agent_session_ref": {"runtime_attempt_id": "attempt-1", "posture": "execution",
                                  "session_epoch": 1, "provider_session_id": "sess_01ABC"},
            "source_seq": 1,
            "observed_at": "2026-08-21T22:05:02.000Z",
            "turn_id": "turn-1",
            "kind": "agent-message",
            "source_kind": "agent_message_chunk",
            "content": [{"type": "text", "text": "reading the contract"},
                        {"type": "dropped", "dropped_type": "image", "byte_count": 90210}],
            "tool_call": None,
            "byte_count": 512,
            "redacted": True,
            "adapter_diagnostics": {},
        }

    @staticmethod
    def turn_skeleton(policy_failures: list) -> dict:
        return {
            "session_family": "baton.agent-session",
            "version": {"major": 1, "minor": 0},
            "document": "turn",
            "turn_id": "turn-1",
            "agent_session_ref": {"runtime_attempt_id": "attempt-1", "posture": "execution",
                                  "session_epoch": 1, "provider_session_id": "sess_01ABC"},
            "started_at": "2026-08-21T22:05:01.000Z",
            "ended_at": "2026-08-21T22:06:01.000Z",
            "deadline_at": "2026-08-21T22:20:01.000Z",
            "prompt_digest": "sha256:" + "cd" * 32,
            "outcome": "completed",
            "terminal_fact": {"kind": "acp-stop-reason", "value": "end_turn"},
            "conclusive": True,
            "permitted_dispositions": ["completed", "plan-rejected", "unable"],
            "event_count": 3,
            "late_event_count": 0,
            "dropped_event_count": 0,
            "dropped_event_bytes": 0,
            "policy_failures": copy.deepcopy(policy_failures),
            "evidence": [copy.deepcopy(JOURNAL)],
            "adapter_diagnostics": {},
        }


# ==========================================================================
# Traces
# ==========================================================================

class TraceTests(unittest.TestCase):
    def test_every_trace_reaches_its_expected_outcome(self) -> None:
        self.assertEqual(len(TRACES["traces"]), 19)
        for trace in TRACES["traces"]:
            with self.subTest(trace=trace["name"]):
                self._check(TraceRunner(trace).run(), trace["expect"])

    def _check(self, run: TraceRunner, expect: dict) -> None:
        checks = {
            "turn_outcome": lambda v: self.assertEqual(run.outcome, v),
            "conclusive": lambda v: self.assertEqual(run.outcome in m.CONCLUSIVE_OUTCOMES, v),
            "session_state": lambda v: self.assertEqual(run.axis.state, v),
            "permitted_dispositions": lambda v: self.assertEqual(
                sorted(m.PERMITTED_DISPOSITIONS[run.outcome]), v),
            "accepted_disposition": lambda v: self.assertEqual(run.accepted, v),
            "event_kinds": lambda v: self.assertEqual(run.event_kinds, v),
            "cancellation_observed": lambda v: self.assertEqual(run.cancellation_observed, v),
            "permission_answer": lambda v: self.assertEqual(run.permission_answer, v),
            "reported_as": lambda v: self.assertEqual(run.reported_as, v),
            "experimental_api": lambda v: self.assertEqual(run.experimental_api, v),
            "negotiated_wire_version": lambda v: self.assertEqual(
                run.records[run.posture]["negotiated_wire_version"], v),
            "answer": lambda v: self.assertEqual(run.codex_answer, v),
            "negotiated_session_capabilities": lambda v: self.assertEqual(
                run.records[run.posture]["negotiated_session_capabilities"], v),
            "answer_valid_against_provider_schema": lambda v: self.assertEqual(
                PROVIDER_VALIDATORS[run.codex_answer_method].is_valid(run.codex_answer), v),
            "persisted_event_count": lambda v: self.assertEqual(len(run.ledger.persisted), v),
            "late_event_count": lambda v: self.assertEqual(run.ledger.late_count, v),
            "same_runtime_attempt": lambda v: self.assertEqual(
                len({ref["runtime_attempt_id"] for ref in run.refs.values()}) == 1, v),
            "consent_epoch": lambda v: self.assertEqual(run.epochs["consent"], v),
            "execution_epoch": lambda v: self.assertEqual(run.epochs["execution"], v),
            "consent_assignment_is_null": lambda v: self.assertEqual(
                run.records["consent"]["assignment_ref"] is None, v),
            "execution_assignment_generation": lambda v: self.assertEqual(
                run.records["execution"]["assignment_ref"]["generation"], v),
            "thread_start_operands": lambda v: self.assertEqual(run.thread_start_operands, v),
            "turn_start_operands": lambda v: self.assertEqual(run.turn_start_operands, v),
        }
        for key, value in expect.items():
            if key in checks:
                checks[key](value)

        if "granted" in expect:
            answer = run.permission_answer or {}
            self.assertEqual(m.permission_grants_anything(answer), expect["granted"])
            if run.codex_answer is not None:
                self.assertFalse(m.codex_answer_grants_anything(
                    "item/permissions/requestApproval", run.codex_answer))
        if expect.get("resume") is False:
            self.assertFalse(run.transport["resume"])
            self.assertFalse(run.transport["reprompt"])
            self.assertFalse(run.transport["next_epoch_allowed_without_runtime_reidentification"])
        if expect.get("interrupt_reply_is_not_an_outcome"):
            self.assertIsNotNone(run.interrupt_reply)
            self.assertEqual(run.outcome, "cancelled",
                             "the outcome comes from turn/completed, not the reply")
        if "promotion_refused" in expect:
            self.assertIsNotNone(run.promotion_error)
            self.assertEqual(
                (run.promotion_error.category, run.promotion_error.code),
                (expect["promotion_refused"]["category"], expect["promotion_refused"]["code"]))
        if expect.get("persisted_events_sealed"):
            for event in run.ledger.persisted:
                VALIDATOR.validate(event)
                m.verify_document_digest(event)
        for posture in ("consent", "execution"):
            key = f"{posture}_record_valid" if posture == "consent" else "session_record_valid"
            if expect.get(key):
                record = run.records[posture]
                VALIDATOR.validate(record)
                m.verify_document_digest(record)
                accepted = m.validate_session_binding(record, run.profile)
                self.assertEqual(accepted, record)
                self.assertIsNot(accepted, record,
                                 "certification hands back a copy, not the caller's object")
        # §7.4 holds for every trace without exception.
        self.assertFalse(m.satisfies_runtime_quiescence_gate(run.axis.state))

    def test_every_negative_vector_refuses_with_its_pair(self) -> None:
        self.assertEqual(len(TRACES["negative"]), 78)
        for vector in TRACES["negative"]:
            with self.subTest(vector=vector["name"]):
                self._run_negative(vector)

    def _run_negative(self, vector: dict) -> None:
        action = vector["action"]
        expect = vector["expect"]
        kind = action["kind"]

        if kind == "quiescence_gate":
            self.assertEqual(m.satisfies_runtime_quiescence_gate(action["agent_session_state"]),
                             expect["satisfies"])
            return
        if kind == "codex_thread_status":
            self.assertEqual(m.codex_thread_status_is_quiescence(action["status"]),
                             expect["satisfies"])
            return
        if kind == "permission_selected":
            answer = {"outcome": {"outcome": "selected", "optionId": action["option_id"]}}
            self.assertEqual(m.permission_grants_anything(answer), expect["granted"])
            self.assertNotEqual(answer, m.answer_permission_request({}),
                                "the relay never produces this answer")
            return
        if kind == "session_record_without_profile":
            # The profile is a required positional operand.  A record is a
            # claim about a certification; an entry point that could be called
            # without one preserves the non-compositional path.
            with self.assertRaises(TypeError):
                m.validate_session_binding(
                    SchemaTests.session_skeleton("execution", assignment(WORK_REF)))
            return
        if kind == "provider_response_shape":
            self.assertEqual(
                PROVIDER_VALIDATORS[action["method"]].is_valid(action["answer"]),
                expect["provider_schema_valid"])
            self.assertNotEqual(action["answer"], m.codex_deny_approval(action["method"]),
                                "the relay never produces a bare decision member")
            return
        if kind == "codex_granting_answer":
            self.assertEqual(
                m.codex_answer_grants_anything(action["method"], action["answer"]),
                expect["granted"])
            self.assertNotEqual(action["answer"], m.codex_deny_approval(action["method"]))
            self.assertNotEqual(action["answer"],
                                m.codex_deny_approval(action["method"], cancelling=True))
            return

        with self.assertRaises(m.BoundaryError) as caught:
            self._perform(kind, action)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         (expect["category"], expect["code"]))

    @staticmethod
    def _certify(profile: dict, action: dict) -> None:
        """Route a profile vector at the layer it is meant to exercise."""
        if action.get("via") == "fields":
            m.certify_profile_fields(profile)
        else:
            m.validate_profile(profile)

    def _perform(self, kind: str, action: dict) -> None:
        if kind == "negotiate":
            methods = set(FULL_METHODS)
            methods.discard(action.get("omit_method", ""))
            m.negotiate_acp(ACP_PROFILE, action["agent_wire_version"], methods,
                            m.SESSION_CAPABILITIES)
        elif kind == "negotiate_codex_profile":
            m.negotiate_acp(CODEX_PROFILE, 1, FULL_METHODS, m.SESSION_CAPABILITIES)
        elif kind == "bind_acp_profile":
            m.bind_provider(ACP_PROFILE, "any", "sharing")
        elif kind == "bind_provider":
            binding = dict(CODEX_PROFILE["provider_binding"])
            if "experimental_api" in action:
                binding["experimental_api"] = action["experimental_api"]
            profile = dict(CODEX_PROFILE, provider_binding=binding)
            m.bind_provider(profile,
                            action.get("server_build_id", binding["server_build_id"]),
                            action.get("interface_digest", binding["interface_digest"]))
        elif kind == "client_capabilities":
            m.validate_client_capabilities(action["advertised"])
        elif kind == "outbound_method":
            m.check_outbound_method(action["method"])
        elif kind == "client_method":
            m.serve_client_method(action["method"])
        elif kind == "enforce_mode":
            policy = m.PinnedPolicy("execution", "acceptEdits")
            policy.enforce(None if "modes" in action
                           else modes("default", action["available_modes"]))
        elif kind == "mode_drift":
            m.PinnedPolicy("execution", "acceptEdits").check_drift(action["observed_mode_id"])
        elif kind == "postures":
            profile = copy.deepcopy(ACP_PROFILE)
            if action.get("same_policy"):
                profile["postures"]["consent"]["policy"] = copy.deepcopy(
                    profile["postures"]["execution"]["policy"])
            if action.get("consent_workspace"):
                profile["postures"]["consent"]["workspace"] = True
            self._certify(profile, action)
        elif kind == "certify_profile":
            profile = self._mutated_profile(action["mutation"])
            entry = action["entry"]
            if entry == "negotiate":
                m.negotiate_acp(profile, 1, FULL_METHODS, m.SESSION_CAPABILITIES)
            elif entry == "bind":
                binding = profile["provider_binding"]
                m.bind_provider(profile, binding["server_build_id"],
                                binding["interface_digest"])
            else:
                m.validate_profile(profile)
        elif kind == "session_record":
            m.validate_session_binding(self._mutated_record(action["mutation"]), ACP_PROFILE)
        elif kind == "swap_codex_posture_policies":
            profile = copy.deepcopy(CODEX_PROFILE)
            profile["postures"]["consent"]["policy"], \
                profile["postures"]["execution"]["policy"] = (
                    copy.deepcopy(profile["postures"]["execution"]["policy"]),
                    copy.deepcopy(profile["postures"]["consent"]["policy"]))
            self._certify(profile, action)
        elif kind == "codex_posture_operand":
            profile = copy.deepcopy(CODEX_PROFILE)
            profile["postures"][action["posture"]]["policy"][action["stage"]][
                action["member"]] = action["value"]
            self._certify(profile, action)
        elif kind == "profile_capabilities":
            self._certify(dict(ACP_PROFILE, session_capabilities=action["capabilities"]), action)
        elif kind == "profile_posture_flag":
            profile = copy.deepcopy(ACP_PROFILE)
            profile["postures"][action["posture"]][action["member"]] = action["value"]
            self._certify(profile, action)
        elif kind == "cwd_injection":
            m.codex_thread_start_operands(
                CODEX_PROFILE["postures"][action["posture"]], action["cwd_by_role"])
        elif kind == "record_profile_digest":
            record = SchemaTests.session_skeleton("execution", assignment(WORK_REF))
            m.validate_session_binding(
                dict(record, profile_digest="sha256:" + "0" * 64), ACP_PROFILE)
        elif kind == "record_pinned_policy":
            record = SchemaTests.session_skeleton("execution", assignment(WORK_REF))
            m.validate_session_binding(
                dict(record, pinned_policy={"kind": "acp", "session_mode_id": "plan"}),
                ACP_PROFILE)
        elif kind == "codex_policy_drift":
            pinned = CODEX_PROFILE["postures"]["execution"]["policy"]
            observed = copy.deepcopy(pinned)
            stage = action["stage"]
            if "approval_policy" in action:
                observed[stage]["approval_policy"] = action["approval_policy"]
            if "sandbox_type" in action:
                observed[stage]["sandbox_policy"] = {"type": action["sandbox_type"]}
            if "sandbox" in action:
                observed[stage]["sandbox"] = action["sandbox"]
            m.codex_check_policy_drift(pinned, observed)
        elif kind == "declare_result":
            m.accept_result_declaration(action["outcome"], action["disposition"])
        elif kind == "cancel_without_fence":
            m.Cancellation().order_agent_cancel()
        elif kind == "session_axis":
            axis = m.SessionAxis()
            axis.state = action["from"]
            axis.observe(action["to"])
        elif kind in ("duplicate_conflict", "bad_source_seq", "event_other_epoch",
                      "unredacted_event", "tampered_event", "oversized_event",
                      "unsealed_event", "tampered_sealed_event"):
            self._event_negative(kind, action)
        elif kind == "session_binding":
            self._binding_negative(action)
        elif kind == "promote_consent":
            m.AttemptSessions("attempt-1").promote_consent_to_execution()
        elif kind == "second_session":
            attempt = m.AttemptSessions("attempt-1")
            attempt.open_session(action["posture"], "p1")
            attempt.open_session(action["posture"], "p2")
        elif kind == "participant_from_session":
            m.participant_from_session(action["provider_session_id"])
        elif kind == "session_ref":
            m.validate_session_ref(action["ref"])
        elif kind == "reprompt":
            m.reprompt_after_transport_loss("the same prompt")
        elif kind == "infer_outcome":
            m.infer_outcome_from(action["evidence"])
        elif kind == "codex_call":
            m.codex_call(action["method"])
        elif kind == "codex_item":
            m.codex_normalize_item(action["item_type"])
        elif kind == "codex_deny_approval":
            m.codex_deny_approval(action["method"])
        else:
            self.fail(f"unhandled negative vector kind {kind!r}")

    @staticmethod
    def _mutated_profile(mutation: str) -> dict:
        if mutation == "extra-member":
            # The member the profile schema no longer has, resealed so only
            # the shape check can catch it.
            return m.seal_document(dict(
                {k: v for k, v in ACP_PROFILE.items() if k != "document_digest"},
                required_agent_methods=["session/new"]))
        # A certified policy field changed while the old digest is retained:
        # schema-valid, seal-invalid, and only the seal check catches it.
        stale = copy.deepcopy(CODEX_PROFILE)
        stale["postures"]["execution"]["policy"]["turn_start"]["model"] = "some-other-model"
        return stale

    @staticmethod
    def _mutated_record(mutation: str) -> dict:
        base = {k: v for k, v in
                SchemaTests.session_skeleton("execution", assignment(WORK_REF)).items()
                if k != "document_digest"}
        if mutation == "profile-digest":
            return m.seal_document(dict(base, profile_digest="sha256:" + "0" * 64))
        if mutation == "pinned-policy":
            return m.seal_document(dict(
                base, pinned_policy={"kind": "acp", "session_mode_id": "plan"}))
        if mutation == "extra-member":
            return m.seal_document(dict(base, operator_note="added later"))
        sealed = m.seal_document(base)
        return dict(sealed, record_id="renamed-after-sealing")

    def _event_negative(self, kind: str, action: dict) -> None:
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 1, "provider_session_id": "p1"}
        raw = dict(SchemaTests.event_skeleton(), agent_session_ref=copy.deepcopy(ref))
        seal = m.seal_document
        ledger = m.EventLedger(copy.deepcopy(ref))
        if kind == "duplicate_conflict":
            ledger.record(seal(raw))
            ledger.record(seal(dict(raw, source_kind="something_else")))
        elif kind == "bad_source_seq":
            ledger.record(seal(dict(raw, source_seq=action["source_seq"])))
        elif kind == "event_other_epoch":
            ledger.record(seal(dict(raw, agent_session_ref=dict(ref, session_epoch=2))))
        elif kind == "unredacted_event":
            ledger.record(seal(dict(raw, redacted=False)))
        elif kind == "unsealed_event":
            ledger.record(raw)
        elif kind == "tampered_sealed_event":
            # A VALID kind with the old digest: shape checks alone would pass it.
            ledger.record(dict(seal(raw), kind="tool-call"))
        elif kind == "tampered_event":
            m.verify_document_digest(dict(seal(raw), kind="tool-call"))
        elif kind == "oversized_event":
            m.enforce_event_limit(dict(raw, source_kind="x" * 4096),
                                  action["max_event_bytes"])

    def _binding_negative(self, action: dict) -> None:
        posture = action["posture"]
        assignment_ref = {
            None: None,
            "own": assignment(WORK_REF),
            "other-work": assignment(OTHER_WORK_REF),
        }.get(action.get("assignment"), assignment(WORK_REF))
        work_ref = copy.deepcopy(WORK_REF)
        if "work_id" in action:
            work_ref["work_id"] = action["work_id"]
        record = {
            "posture": posture,
            "work_ref": work_ref,
            "assignment_ref": assignment_ref,
            "agent_session_ref": {"runtime_attempt_id": "attempt-1",
                                  "posture": action.get("ref_posture", posture),
                                  "session_epoch": 1, "provider_session_id": "p1"},
        }
        m.validate_session_binding_fields(record)


# ==========================================================================
# Boundary rules
# ==========================================================================

class BoundaryRuleTests(unittest.TestCase):
    def test_error_pairs_come_only_from_the_closed_worker_control_taxonomy(self) -> None:
        for _outcome, category, code in m.CODEX_ERROR_INFO.values():
            with self.subTest(code=code):
                m.validate_error_pair(category, code)
        with self.assertRaises(ValueError):
            m.validate_error_pair("agent-session", "turn-timeout")
        with self.assertRaises(ValueError):
            m.validate_error_pair("policy", "agent-refused")

    def test_all_acp_stop_reasons_are_mapped(self) -> None:
        self.assertEqual(set(m.ACP_STOP_REASONS),
                         {"end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled"})
        self.assertTrue(set(m.ACP_STOP_REASONS.values()) <= m.TURN_OUTCOMES)

    def test_all_acp_session_update_kinds_are_mapped(self) -> None:
        # The 13 SessionUpdate variants of @agentclientprotocol/sdk 1.3.0.
        self.assertEqual(set(m.ACP_UPDATE_KINDS), {
            "user_message_chunk", "agent_message_chunk", "agent_thought_chunk",
            "tool_call", "tool_call_update", "plan", "plan_update", "plan_removed",
            "available_commands_update", "current_mode_update", "config_option_update",
            "session_info_update", "usage_update",
        })
        self.assertTrue(set(m.ACP_UPDATE_KINDS.values()) <= m.EVENT_KINDS)

    def test_acp_client_capability_inventory_matches_the_vendored_declaration(self) -> None:
        """The 1.3.0 declaration marks five members UNSTABLE; `session` is not one."""
        self.assertEqual(m.ACP_UNSTABLE_CLIENT_CAPABILITIES,
                         {"plan", "auth", "elicitation", "nes", "positionEncodings"})
        self.assertNotIn("session", m.ACP_UNSTABLE_CLIENT_CAPABILITIES)
        self.assertIn("session", m.ACP_CLIENT_CAPABILITY_MEMBERS)
        # Withholding is total, so even the stable members are not advertised.
        advertised = set(m.MINIMAL_CLIENT_CAPABILITIES)
        self.assertEqual(advertised, {"fs", "terminal"})
        self.assertEqual(m.MINIMAL_CLIENT_CAPABILITIES["terminal"], False)
        # SUPERSEDED ASSERTION, on W641's ruling.  This required every `fs`
        # member to be present and False, which encoded the Baton-invented
        # normalized summary the ruling removes.  ACP's members are optional,
        # so withholding is ABSENCE and the object is empty.
        self.assertEqual(m.MINIMAL_CLIENT_CAPABILITIES["fs"], {})

    def test_a_filesystem_member_present_at_all_is_refused(self) -> None:
        """W641 -- absence is the withholding, so presence is the defect.

        Driven on the snake_case summary this contract used to require, on the
        ACP camelCase member set false, and on a member set true: none of the
        three is what version 1.0 sends.
        """
        m.validate_client_capabilities({"fs": {}, "terminal": False})
        # Member ORDER carries no meaning; the same document is the same.
        m.validate_client_capabilities({"terminal": False, "fs": {}})
        for advertised in (
            {"fs": {"read_text_file": False, "write_text_file": False},
             "terminal": False},
            {"fs": {"readTextFile": False}, "terminal": False},
            {"fs": {"readTextFile": True}, "terminal": False},
            {"fs": {}, "terminal": True},
            {"fs": {}, "terminal": False, "session": {}},
            {"terminal": False},
            {"fs": {}},
            "nothing",
        ):
            with self.assertRaises(m.BoundaryError) as caught:
                m.validate_client_capabilities(advertised)
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("policy", "denied"))

    def test_an_unmapped_update_kind_is_counted_as_other(self) -> None:
        self.assertEqual(m.normalize_acp_update({"sessionUpdate": "something_new_in_1_4"}), "other")

    def test_every_turn_outcome_has_a_disposition_rule(self) -> None:
        self.assertEqual(set(m.PERMITTED_DISPOSITIONS), set(m.TURN_OUTCOMES))
        for outcome in ("cancelled", "policy-failed", "timeout", "transport-lost"):
            self.assertEqual(m.PERMITTED_DISPOSITIONS[outcome], frozenset())

    def test_timeout_and_transport_loss_are_never_conclusive(self) -> None:
        self.assertFalse({"timeout", "transport-lost"} & m.CONCLUSIVE_OUTCOMES)

    def test_agent_quiescence_never_satisfies_the_runtime_gate(self) -> None:
        for state in sorted(m.SESSION_STATES):
            with self.subTest(state=state):
                self.assertFalse(m.satisfies_runtime_quiescence_gate(state))

    def test_cancellation_order_is_authority_first(self) -> None:
        cancellation = m.Cancellation()
        with self.assertRaises(m.BoundaryError):
            cancellation.order_agent_cancel()
        cancellation.fence_and_end()
        cancellation.order_agent_cancel()
        self.assertEqual(cancellation.observe_terminal_fact("cancelled"), "agent-turn-cancelled")

    def test_an_end_turn_after_cancellation_keeps_its_observed_reason(self) -> None:
        cancellation = m.Cancellation()
        cancellation.fence_and_end()
        cancellation.order_agent_cancel()
        self.assertEqual(cancellation.observe_terminal_fact("end_turn"), "agent-turn-cancelled")
        self.assertEqual(m.outcome_from_acp("end_turn"), "completed",
                         "the turn outcome is still what the agent reported")

    def test_session_axis_is_monotonic_and_unknown_is_terminal(self) -> None:
        axis = m.SessionAxis()
        for state in ("initializing", "ready", "prompting", "turn-ended", "closed"):
            axis.observe(state)
        self.assertEqual(axis.state, "closed")
        with self.assertRaises(m.BoundaryError):
            axis.observe("prompting")
        stuck = m.SessionAxis()
        stuck.state = "unknown"
        for state in ("closed", "ready", "agent-quiescent"):
            with self.subTest(state=state), self.assertRaises(m.BoundaryError):
                stuck.observe(state)

    def test_epochs_are_scoped_per_posture_within_one_attempt(self) -> None:
        attempt = m.AttemptSessions("attempt-1")
        consent = attempt.open_session("consent", "c1")
        self.assertEqual(consent["session_epoch"], 1)
        attempt.end_session("consent")
        execution = attempt.open_session("execution", "e1")
        self.assertEqual(execution["session_epoch"], 1,
                         "the execution counter is its own, not a continuation")
        attempt.end_session("execution")
        second = attempt.open_session("execution", "e2")
        self.assertEqual(second["session_epoch"], 2)
        self.assertEqual({consent["runtime_attempt_id"], execution["runtime_attempt_id"]},
                         {"attempt-1"}, "W151 binds one attempt across both postures")

    def test_event_overflow_is_counted_never_silent(self) -> None:
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 1, "provider_session_id": "p1"}
        ledger = m.EventLedger(copy.deepcopy(ref), max_queue_events=2)
        base = dict(SchemaTests.event_skeleton(), agent_session_ref=copy.deepcopy(ref))
        ledger.record(m.seal_document(dict(base, source_seq=1)))
        ledger.record(m.seal_document(dict(base, source_seq=2)))
        dropped = ledger.record(m.seal_document(dict(base, source_seq=3)))
        self.assertEqual(dropped.status, "dropped")
        self.assertIsNone(dropped.event)
        self.assertEqual(ledger.dropped_count, 1)
        self.assertGreater(ledger.dropped_bytes, 0)

    def test_ledger_returns_the_document_it_was_given_unchanged(self) -> None:
        """One contract in, the same contract out — for stores AND replays."""
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 1, "provider_session_id": "p1"}
        ledger = m.EventLedger(copy.deepcopy(ref))
        sealed = m.seal_document(dict(SchemaTests.event_skeleton(),
                                      agent_session_ref=copy.deepcopy(ref)))
        VALIDATOR.validate(sealed)

        stored = ledger.record(sealed)
        self.assertEqual(stored.status, "stored")
        self.assertEqual(stored.event, sealed)
        VALIDATOR.validate(stored.event)
        m.verify_document_digest(stored.event)
        self.assertFalse(stored.late)
        self.assertEqual(stored.observation_seq, 1)

        replayed = ledger.record(copy.deepcopy(sealed))
        self.assertEqual(replayed.status, "replayed")
        self.assertEqual(replayed.event, sealed)
        VALIDATOR.validate(replayed.event)
        m.verify_document_digest(replayed.event)
        self.assertEqual(replayed.observation_seq, 1,
                         "a replay does not mint a second observation")

        VALIDATOR.validate(ledger.persisted[0])
        self.assertEqual(len(ledger.persisted), 1)

    def test_the_ledger_owns_its_entry_and_no_caller_can_reach_it(self) -> None:
        """Immutable evidence a caller can still edit is not immutable."""
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 1, "provider_session_id": "p1"}
        ledger = m.EventLedger(copy.deepcopy(ref))
        submitted = m.seal_document(dict(SchemaTests.event_skeleton(),
                                         agent_session_ref=copy.deepcopy(ref)))
        expected = copy.deepcopy(submitted)
        outcome = ledger.record(submitted)

        # Byte equality, not object identity.
        self.assertEqual(outcome.event, expected)
        self.assertIsNot(outcome.event, submitted)
        self.assertIsNot(outcome.event, ledger.persisted[0])
        self.assertIsNot(ledger.persisted[0], ledger.persisted[0])

        # Mutation after store, through the caller's own input...
        submitted["kind"] = "tool-call"
        submitted["content"].append({"type": "text", "text": "smuggled"})
        # ...and after return, through what the ledger handed back.
        outcome.event["kind"] = "tool-call"
        outcome.event["adapter_diagnostics"]["org.example.x/1"] = "smuggled"

        persisted = ledger.persisted[0]
        self.assertEqual(persisted, expected, "the entry is untouched")
        VALIDATOR.validate(persisted)
        m.verify_document_digest(persisted)

        # And the replay decision still turns on the bytes, not on who edited what.
        replay = ledger.record(m.seal_document(dict(SchemaTests.event_skeleton(),
                                                    agent_session_ref=copy.deepcopy(ref))))
        self.assertEqual(replay.status, "replayed")
        self.assertEqual(replay.event, expected)
        with self.assertRaises(m.BoundaryError):
            ledger.record(m.seal_document(dict(SchemaTests.event_skeleton(),
                                               agent_session_ref=copy.deepcopy(ref),
                                               kind="tool-call")))

    def test_lateness_is_an_observation_not_part_of_the_frame(self) -> None:
        """A retransmission is the same frame; sealing lateness in would split it."""
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 1, "provider_session_id": "p1"}
        ledger = m.EventLedger(copy.deepcopy(ref))
        first = m.seal_document(dict(SchemaTests.event_skeleton(),
                                     agent_session_ref=copy.deepcopy(ref)))
        ledger.record(first)
        ledger.end_turn()
        late = m.seal_document(dict(SchemaTests.event_skeleton(), source_seq=2,
                                    agent_session_ref=copy.deepcopy(ref)))
        outcome = ledger.record(late)
        self.assertTrue(outcome.late)
        self.assertEqual(ledger.late_count, 1)
        self.assertEqual(outcome.event, late, "the frame is untouched by being late")
        # The same first frame arriving again after the turn ended still replays.
        again = ledger.record(copy.deepcopy(first))
        self.assertEqual(again.status, "replayed")
        self.assertFalse(again.late, "its lateness was decided when it was first seen")

    def test_the_ledger_verifies_the_seal_before_anything_else(self) -> None:
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 1, "provider_session_id": "p1"}
        raw = dict(SchemaTests.event_skeleton(), agent_session_ref=copy.deepcopy(ref))
        with self.assertRaises(m.BoundaryError) as unsealed:
            m.EventLedger(copy.deepcopy(ref)).record(raw)
        self.assertEqual((unsealed.exception.category, unsealed.exception.code),
                         ("integrity", "schema"))
        # A tamper that keeps the shape valid must still fail, and must fail on
        # the digest rather than on some later shape check.
        with self.assertRaises(m.BoundaryError) as tampered:
            m.EventLedger(copy.deepcopy(ref)).record(
                dict(m.seal_document(raw), kind="tool-call"))
        self.assertEqual((tampered.exception.category, tampered.exception.code),
                         ("integrity", "digest"))

    def test_content_bytes_are_counted_and_dropped_never_inlined(self) -> None:
        normalized = m.normalize_content([
            {"type": "text", "text": "hello"},
            {"type": "resource_link", "uri": "file:///workspace/a.md", "name": "a.md"},
            {"type": "image", "byte_count": 90210},
            {"type": "audio", "byte_count": 4},
            {"type": "resource", "byte_count": 7},
            {"type": "something-new", "byte_count": 1},
        ])
        self.assertEqual([block["type"] for block in normalized],
                         ["text", "resource_link", "dropped", "dropped", "dropped", "dropped"])
        self.assertEqual(normalized[2], {"type": "dropped", "dropped_type": "image",
                                         "byte_count": 90210})
        self.assertEqual(normalized[5]["dropped_type"], "unknown")

    def test_transport_loss_permits_no_new_epoch_without_reidentification(self) -> None:
        ref = {"runtime_attempt_id": "attempt-1", "posture": "execution",
               "session_epoch": 3, "provider_session_id": "p1"}
        result = m.handle_transport_loss(ref, turn_in_flight=True)
        self.assertFalse(result["resume"])
        self.assertFalse(result["reprompt"])
        self.assertFalse(result["next_epoch_allowed_without_runtime_reidentification"])
        self.assertEqual(result["turn_outcome"], "transport-lost")
        self.assertEqual(result["epoch"], 3)

    def test_capability_client_methods_are_all_refused(self) -> None:
        for method in sorted(m.CAPABILITY_CLIENT_METHODS):
            with self.subTest(method=method), self.assertRaises(m.BoundaryError) as caught:
                m.serve_client_method(method)
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("policy", "denied"))

    def test_history_bearing_session_methods_are_refused(self) -> None:
        for method in ("session/load", "session/resume", "session/fork"):
            with self.subTest(method=method), self.assertRaises(m.BoundaryError):
                m.check_outbound_method(method)

    def test_codex_excluded_surface_covers_process_and_host_capability(self) -> None:
        for method in ("process/spawn", "process/kill", "command/exec", "fs/writeFile",
                       "thread/shellCommand", "plugin/install", "thread/rollback",
                       "tool/requestUserInput", "review/start"):
            with self.subTest(method=method), self.assertRaises(m.BoundaryError):
                m.codex_call(method)

    def test_codex_turn_statuses_and_errors_map_completely(self) -> None:
        self.assertEqual(set(m.CODEX_TURN_STATUS), {"completed", "interrupted", "failed"})
        self.assertEqual(m.codex_turn_outcome("completed"), ("completed", None, None))
        self.assertEqual(m.codex_turn_outcome("interrupted"), ("cancelled", None, None))
        for error_info, expected in m.CODEX_ERROR_INFO.items():
            with self.subTest(error_info=error_info):
                self.assertEqual(m.codex_turn_outcome("failed", error_info), expected)
        self.assertEqual(m.codex_turn_outcome("failed", "NeverSeenBefore"),
                         m.CODEX_ERROR_INFO["Other"])

    def test_codex_denials_conform_to_the_captured_provider_schemas(self) -> None:
        """Validated against the provider's OWN schema, not a payload we wrote."""
        self.assertEqual(set(PROVIDER_VALIDATORS), set(m.CODEX_APPROVAL_FAMILIES))
        for method in sorted(m.CODEX_APPROVAL_FAMILIES):
            validator = PROVIDER_VALIDATORS[method]
            for cancelling in (False, True):
                with self.subTest(method=method, cancelling=cancelling):
                    answer = m.codex_deny_approval(method, cancelling=cancelling)
                    self.assertIsInstance(answer, dict,
                                          "every provider response is an object")
                    validator.validate(answer)
                    self.assertFalse(m.codex_answer_grants_anything(method, answer))

    def test_a_bare_decision_member_is_not_a_valid_provider_response(self) -> None:
        for method in ("item/commandExecution/requestApproval",
                       "item/fileChange/requestApproval"):
            validator = PROVIDER_VALIDATORS[method]
            for bare in ("decline", "cancel"):
                with self.subTest(method=method, bare=bare):
                    self.assertFalse(validator.is_valid(bare))
                    self.assertTrue(validator.is_valid({"decision": bare}))

    def test_provider_schema_bundle_matches_the_certified_interface_digest(self) -> None:
        bundle = {path.name: json.loads(path.read_text())
                  for path in sorted(PROVIDER_SCHEMAS.glob("*.json"))}
        digest = m.digest(bundle)
        self.assertEqual(digest, CODEX_PROFILE["provider_binding"]["interface_digest"],
                         "the certified binding names the captured interface")

    def test_codex_granting_answers_are_recognized_through_the_envelope(self) -> None:
        method = "item/commandExecution/requestApproval"
        for granting in ({"decision": "accept"}, {"decision": "acceptForSession"},
                         {"decision": {"acceptWithExecpolicyAmendment":
                                       {"execpolicy_amendment": ["rm"]}}}):
            with self.subTest(answer=granting):
                self.assertTrue(m.codex_answer_grants_anything(method, granting))
        self.assertTrue(m.codex_answer_grants_anything(
            "item/permissions/requestApproval",
            {"permissions": {"network": {}}, "scope": "session"}))
        self.assertTrue(m.codex_answer_grants_anything(
            "mcpServer/elicitation/request", {"action": "accept", "content": {}}))

    def test_codex_policy_operands_are_complete_and_repinned_per_turn(self) -> None:
        binding = CODEX_PROFILE["postures"]["execution"]
        thread = m.codex_thread_start_operands(binding, CWD)
        self.assertEqual(set(thread), {"model", "cwd", "approvalPolicy", "sandbox"})
        self.assertEqual(thread["approvalPolicy"], "never")
        self.assertEqual(thread["cwd"], CWD["workspace"])
        turn = m.codex_turn_start_operands(binding, "thread-1", CWD, "go")
        self.assertEqual(set(turn), {"threadId", "input", "model", "cwd",
                                     "approvalPolicy", "sandboxPolicy"})
        self.assertEqual(turn["approvalPolicy"], "never",
                         "turn/start may override the thread default, so it is re-pinned")
        self.assertEqual(turn["sandboxPolicy"], {"type": "workspaceWrite", "networkAccess": False})
        consent = m.codex_thread_start_operands(CODEX_PROFILE["postures"]["consent"], CWD)
        self.assertEqual(consent["sandbox"], "readOnly")
        self.assertEqual(consent["cwd"], CWD["scratch"],
                         "the PROFILE chooses the role; the caller only supplies paths")

    def test_a_request_cannot_be_given_a_path_the_posture_did_not_pin(self) -> None:
        with self.assertRaises(m.BoundaryError) as caught:
            m.codex_thread_start_operands(CODEX_PROFILE["postures"]["consent"],
                                          {"workspace": "/workspace"})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))

    def test_certification_composes_shape_seal_and_policy_on_the_runtime_path(self) -> None:
        """Proving the three separately in tests does not compose them in code."""
        extra = m.seal_document(dict(
            {k: v for k, v in ACP_PROFILE.items() if k != "document_digest"},
            required_agent_methods=["session/new"]))
        self.assertFalse(VALIDATOR.is_valid(extra))
        for label, call in (
            ("validate_profile", lambda: m.validate_profile(extra)),
            ("negotiate_acp", lambda: m.negotiate_acp(extra, 1, FULL_METHODS,
                                                      m.SESSION_CAPABILITIES)),
        ):
            with self.subTest(entry=label), self.assertRaises(m.BoundaryError) as caught:
                call()
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("integrity", "schema"))

        stale = copy.deepcopy(CODEX_PROFILE)
        stale["postures"]["execution"]["policy"]["turn_start"]["model"] = "some-other-model"
        self.assertTrue(VALIDATOR.is_valid(stale), "shape alone cannot catch this")
        binding = stale["provider_binding"]
        for label, call in (
            ("validate_profile", lambda: m.validate_profile(stale)),
            ("bind_provider", lambda: m.bind_provider(stale, binding["server_build_id"],
                                                      binding["interface_digest"])),
        ):
            with self.subTest(entry=label), self.assertRaises(m.BoundaryError) as caught:
                call()
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("integrity", "digest"))

    def test_certification_hands_back_a_copy_the_caller_cannot_reach(self) -> None:
        submitted = copy.deepcopy(ACP_PROFILE)
        accepted = m.validate_profile(submitted)
        self.assertEqual(accepted, ACP_PROFILE)
        self.assertIsNot(accepted, submitted)
        submitted["postures"]["execution"]["policy"]["session_mode_id"] = "plan"
        self.assertEqual(accepted["postures"]["execution"]["policy"]["session_mode_id"],
                         "acceptEdits")

    def test_a_session_record_is_never_validated_without_its_profile(self) -> None:
        record = SchemaTests.session_skeleton("execution", assignment(WORK_REF))
        with self.assertRaises(TypeError):
            m.validate_session_binding(record)
        self.assertEqual(m.validate_session_binding(record, ACP_PROFILE), record)

    def test_method_sets_are_owned_by_the_version_not_the_profile(self) -> None:
        self.assertEqual(set(m.REQUIRED_METHODS_BY_WIRE), {"acp", "codex-app-server"})
        self.assertEqual(m.REQUIRED_METHODS_BY_WIRE["acp"], m.REQUIRED_AGENT_METHODS)
        for profile in (ACP_PROFILE, CODEX_PROFILE):
            with self.subTest(profile=profile["profile_id"]):
                self.assertNotIn("required_agent_methods", profile)
                self.assertNotIn("refused_agent_methods", profile)
                self.assertEqual(m.validate_profile(profile), profile)

    def test_a_provider_without_a_wire_version_is_certified_by_binding(self) -> None:
        binding = CODEX_PROFILE["provider_binding"]
        result = m.bind_provider(CODEX_PROFILE, binding["server_build_id"],
                                 binding["interface_digest"])
        self.assertIsNone(result["wire_version"])
        self.assertEqual(result["provider_binding"]["experimental_api"], False)
        with self.assertRaises(m.BoundaryError):
            m.negotiate_acp(CODEX_PROFILE, 1, FULL_METHODS, m.SESSION_CAPABILITIES)
        with self.assertRaises(m.BoundaryError):
            m.bind_provider(ACP_PROFILE, "x", "y")

    def test_codex_item_kinds_map_into_the_closed_event_set(self) -> None:
        self.assertTrue(set(m.CODEX_ITEM_KINDS.values()) <= m.EVENT_KINDS)
        self.assertEqual(m.codex_normalize_item("somethingNewNextRelease"), "other")

    def test_codex_never_enables_the_experimental_api(self) -> None:
        self.assertEqual(m.codex_initialize_capabilities(), {"experimentalApi": False})

    def test_no_state_or_outcome_leaks_outside_its_closed_set(self) -> None:
        self.assertEqual(set(m.ALLOWED_SESSION_SUCCESSORS), set(m.SESSION_STATES))
        for state, successors in m.ALLOWED_SESSION_SUCCESSORS.items():
            with self.subTest(state=state):
                self.assertTrue(successors <= m.SESSION_STATES)


class ToolCallKind(unittest.TestCase):
    """§6.2.1, the W543 correction: portable, optional, never invented."""

    def test_a_supplied_kind_is_copied_verbatim(self):
        for kind in sorted(m.TOOL_KINDS):
            view = m.normalize_tool_call(
                {"toolCallId": "tc-1", "status": "completed", "kind": kind})
            self.assertEqual(view["kind"], kind)

    def test_the_vocabulary_is_the_pinned_acp_ten(self):
        self.assertEqual(sorted(m.TOOL_KINDS), sorted([
            "read", "edit", "delete", "move", "search", "execute", "think",
            "fetch", "switch_mode", "other"]))

    def test_an_absent_kind_is_omitted_and_never_invented(self):
        # The captured trace's own shape: root-level id and status, no kind.
        view = m.normalize_tool_call(
            {"toolCallId": "tc-1", "status": "in_progress"})
        self.assertNotIn("kind", view)
        # MIGRATED on the review's authority: explicit null is the SDK's
        # "not supplied" for an UPDATE, and the source used to be unspecified.
        # The omission assertion this case already made is unchanged.
        self.assertNotIn("kind", m.normalize_tool_call(
            {"sessionUpdate": "tool_call_update", "toolCallId": "tc-1",
             "status": "completed", "kind": None}))
        # And nothing else in the update may be used to infer one -- a title,
        # a tool name, a command and a status are all present here and the
        # member is still absent.
        rich = m.normalize_tool_call({
            "toolCallId": "tc-1", "status": "failed", "title": "read a file",
            "name": "fs_read", "command": "cat /etc/passwd"})
        self.assertNotIn("kind", rich)
        self.assertEqual(rich["title"], "read a file")

    def test_a_value_outside_the_pinned_vocabulary_refuses(self):
        for invented in ["summon", "READ", "", "read ", "execute_command", 7]:
            with self.assertRaises(m.BoundaryError) as caught:
                m.normalize_tool_call({"toolCallId": "tc-1",
                                       "status": "completed",
                                       "kind": invented})
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("integrity", "schema"))

    def test_null_is_absence_only_for_an_update(self):
        with self.assertRaises(m.BoundaryError) as caught:
            m.normalize_tool_call({"sessionUpdate": "tool_call",
                                   "toolCallId": "tc-1",
                                   "status": "completed", "kind": None})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        view = m.normalize_tool_call({"sessionUpdate": "tool_call_update",
                                      "toolCallId": "tc-1",
                                      "status": "completed", "kind": None})
        self.assertNotIn("kind", view)

    def test_an_unhashable_invalid_kind_uses_the_closed_error_pair(self):
        for invented in [[], {}]:
            with self.assertRaises(m.BoundaryError) as caught:
                m.normalize_tool_call({"toolCallId": "tc-1",
                                       "status": "completed",
                                       "kind": invented})
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("integrity", "schema"))

    def test_the_source_decides_which_shapes_are_absence(self):
        """The declaration was quoted and then implemented on one path."""
        table = [
            # shape, fields, on tool_call, on tool_call_update
            ("an omitted member", {}, "absent", "absent"),
            ("an explicit null", {"kind": None}, "refuses", "absent"),
            ("a pinned value", {"kind": "read"}, "read", "read"),
            ("a value outside the ten", {"kind": "summon"},
             "refuses", "refuses"),
        ]
        for shape, fields, on_call, on_update in table:
            for source, expected in (("tool_call", on_call),
                                     ("tool_call_update", on_update)):
                with self.subTest(shape=shape, source=source):
                    update = {"sessionUpdate": source, "toolCallId": "tc-1",
                              "status": "completed", **fields}
                    if expected == "refuses":
                        with self.assertRaises(m.BoundaryError) as caught:
                            m.normalize_tool_call(update)
                        self.assertEqual((caught.exception.category,
                                          caught.exception.code),
                                         ("integrity", "schema"))
                    elif expected == "absent":
                        self.assertNotIn("kind", m.normalize_tool_call(update))
                    else:
                        self.assertEqual(
                            m.normalize_tool_call(update)["kind"], expected)

    def test_a_refusal_names_the_shape_and_never_runs_the_value(self):
        """`x not in frozenset` HASHES x -- the check ran what it refused."""

        class Hostile:
            def __repr__(self):
                raise AssertionError("__repr__ ran")

            def __str__(self):
                raise AssertionError("__str__ ran")

            def __hash__(self):
                raise AssertionError("__hash__ ran")

            def __eq__(self, other):
                raise AssertionError("__eq__ ran")

        class Sneaky(str):
            # In the vocabulary BY VALUE and not by shape.  The pinned type is
            # the JSON string `read`; membership is tested only after the
            # shape is known, so this never reaches the frozenset either.
            def __hash__(self):
                raise AssertionError("__hash__ ran")

        marker = "zz-not-a-tool-kind-zz"
        for what, value in [("a list", []), ("a dict", {}), ("a set", set()),
                            ("an int", 7), ("a bool", True),
                            ("an object that raises if anything reads it",
                             Hostile()),
                            ("a str subclass", Sneaky("read")),
                            ("an invalid string", marker)]:
            for source in ("tool_call", "tool_call_update"):
                with self.subTest(what=what, source=source):
                    with self.assertRaises(m.BoundaryError) as caught:
                        m.normalize_tool_call({"sessionUpdate": source,
                                               "toolCallId": "tc-1",
                                               "status": "completed",
                                               "kind": value})
                    self.assertEqual((caught.exception.category,
                                      caught.exception.code),
                                     ("integrity", "schema"))
                    # The message describes the SHAPE rather than echoing the
                    # value this boundary has just rejected.
                    self.assertNotIn(marker, str(caught.exception))
                    self.assertIn(type(value).__name__, str(caught.exception))

    def test_the_view_still_needs_an_id_and_one_of_the_four_statuses(self):
        for update in [{"status": "completed"},
                       {"toolCallId": "", "status": "completed"},
                       {"toolCallId": "tc-1"},
                       {"toolCallId": "tc-1", "status": "cancelled"}]:
            with self.assertRaises(m.BoundaryError):
                m.normalize_tool_call(update)


if __name__ == "__main__":
    unittest.main()
