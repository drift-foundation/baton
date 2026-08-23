from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import unittest

from jsonschema import Draft202012Validator

from contract_model import (
    AssignmentFence,
    ContractError,
    GOLDEN_BEARER,
    GOLDEN_VERIFIER,
    ObservationLedger,
    ReplayLedger,
    digest,
    operation_signature,
    operation_signature_payload,
    seal_manifest,
    token_verifier,
    validate_envelope,
    validate_manifest,
    validate_offer_decide,
)


HERE = pathlib.Path(__file__).parent
SCHEMA_PATH = HERE.parent / "schema" / "worker-control-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
VECTORS = json.loads((HERE / "vectors.json").read_text())
D = "sha256:" + "a" * 64
WORK_REF = {"authority_uuid": "43c55d4b1234567890abcdef12345678", "work_id": "43c55d4b-W1439"}
ASSIGNMENT_REF = {"work_ref": WORK_REF, "participant": "baton.claude", "generation": 7}
GIT_OBJECT = {"algorithm": "sha1", "hex": "1" * 40}
OPERATION = {"operation_id": "operation-1", "signature_digest": D}


def artifact(name: str = "artifact-1") -> dict:
    return {
        "artifact_id": name,
        "media_type": "application/octet-stream",
        "bytes": 4,
        "content_digest": D,
        "locator": f"artifact://objects/{name}",
    }


def evidence(name: str = "evidence-1") -> dict:
    return {"purpose": "test-output", "artifact": artifact(name)}


def manifest(schema: str, manifest_id: str, **fields: object) -> dict:
    document = {
        "version": {"major": 1, "minor": 0},
        "manifest_id": manifest_id,
        "created_at": "2026-08-21T22:00:00.000Z",
        "extensions": {},
        "schema": schema,
        **fields,
    }
    return seal_manifest(document)


def receipt_base(schema: str, receipt_id: str, **fields: object) -> dict:
    return manifest(
        schema,
        receipt_id + "-manifest",
        receipt_id=receipt_id,
        operation=OPERATION,
        proposal_id="proposal-1",
        proposal_digest=D,
        candidate_tree_digest=D,
        target_revision=GIT_OBJECT,
        actor="baton.codex",
        policy_generation=3,
        rationale="Pinned evidence supports this disposition.",
        **fields,
    )


def typed_documents() -> list[dict]:
    states = {
        "consent_runtime": "running",
        "execution_runtime": "running",
        "output": "open",
        "worker_disposition": "none",
        "proposal": "none",
        "verification": "none",
        "technical_review": "none",
        "approval": "none",
        "integration": "none",
        "cleanup": "pending",
    }
    return [
        manifest(
            "baton.worker-manifest/assignment",
            "assignment-manifest-1",
            assignment_ref=ASSIGNMENT_REF,
            assignment_contract="v12-assignment-1",
            offer_id="offer-1",
            runtime_attempt_id="attempt-1",
            input_manifest_digest=D,
            policy_digest=D,
            runtime_profile_digest=D,
            claim_receipt_digest=D,
            claim_event_seq=44,
            activated_at="2026-08-21T22:00:01.000Z",
        ),
        manifest(
            "baton.worker-manifest/runtime-attempt",
            "attempt-manifest-1",
            runtime_attempt_id="attempt-1",
            assignment_ref=ASSIGNMENT_REF,
            adapter={"name": "local-process", "version": "adapter-1.0", "digest": D},
            runtime_profile_digest=D,
            worker_image_digest=D,
            toolchain_digest=D,
            policy_digest=D,
            runtime_id="runtime-1",
            observation_seq=2,
            states=states,
            observed_at="2026-08-21T22:00:02.000Z",
            diagnostics={},
        ),
        manifest(
            "baton.worker-manifest/result",
            "result-manifest-1",
            result_id="result-1",
            assignment_ref=ASSIGNMENT_REF,
            input_manifest_digest=D,
            policy_digest=D,
            disposition="completed",
            outputs=[],
            evidence=[evidence()],
            freeze_operation=OPERATION,
            manager_observed_at="2026-08-21T22:00:03.000Z",
        ),
        manifest(
            "baton.worker-manifest/proposal",
            "proposal-manifest-1",
            proposal_id="proposal-1",
            assignment_ref=ASSIGNMENT_REF,
            result_id="result-1",
            result_manifest_digest=D,
            input_manifest_digest=D,
            policy_digest=D,
            runtime_profile_digest=D,
            output_digest=D,
            source_base=GIT_OBJECT,
            target_revision=GIT_OBJECT,
            proposal_head={"algorithm": "sha1", "hex": "2" * 40},
            proposal_artifact=artifact("proposal-bundle"),
            author_tests=[evidence("author-tests")],
            implementation_recap="Changed only the declared output.",
            dossier_evidence=[evidence("dossier")],
            publish_operation=OPERATION,
            publish_receipt_digest=D,
        ),
        receipt_base(
            "baton.worker-manifest/verification",
            "verification-1",
            observation="passed",
            verifier_profile_digest=D,
            worker_image_digest=D,
            toolchain_digest=D,
            suites=[{"name": "unit", "observation": "passed", "evidence": evidence("unit-tests")}],
        ),
        receipt_base(
            "baton.worker-manifest/verification-assessment",
            "assessment-1",
            verification_receipt_id="verification-1",
            assessment="accepted",
        ),
        receipt_base(
            "baton.worker-manifest/technical-review",
            "review-1",
            verification_assessment_id="assessment-1",
            disposition="accepted",
        ),
        receipt_base(
            "baton.worker-manifest/approval",
            "approval-1",
            technical_review_id="review-1",
            disposition="approved",
        ),
        receipt_base(
            "baton.worker-manifest/integration",
            "integration-1",
            approval_id="approval-1",
            disposition="integrated",
            target_before=GIT_OBJECT,
            target_after={"algorithm": "sha1", "hex": "3" * 40},
        ),
    ]


# A command's operation is COMPUTED, because the signature is a function of
# the kind and the body rather than a free-standing label. Review
# 2026-08-22T14:39:32Z [P1]: this helper used to hand every envelope the same
# fixed `OPERATION`, so seventeen envelope shapes asserted nothing about the
# signature and the rule went unmodelled. `OPERATION` survives for the two
# REPLIES, whose signature is the request's and is deliberately not
# recomputable from a result body.
_COMPUTED = object()


def envelope(kind: str, body: dict, message_type: str = "command", operation: object = _COMPUTED) -> dict:
    if operation is _COMPUTED:
        operation = {"operation_id": "operation-" + kind.replace(".", "-"),
                     "signature_digest": operation_signature(kind, body)}
    return {
        "protocol": "baton.worker-control",
        "version": {"major": 1, "minor": 0},
        "message_type": message_type,
        "kind": kind,
        "message_id": "message-" + kind.replace(".", "-"),
        "correlation_id": "request-1" if message_type == "reply" else None,
        "sent_at": "2026-08-21T22:00:00.000Z",
        "sender": {"role": "worker-manager", "instance_id": "manager-1"},
        "operation": operation,
        "body_digest": digest(body),
        "body": body,
        "extensions": {},
    }


def control_envelopes() -> list[dict]:
    limits = {
        "max_frame_bytes": 1048576,
        "max_extension_bytes": 65536,
        "max_artifact_bytes": 1073741824,
        "max_manifest_entries": 10000,
        "max_activity_bytes": 16000,
    }
    assignment_body = {
        "assignment_ref": ASSIGNMENT_REF,
        "runtime_attempt_id": "attempt-1",
        "input_manifest_digest": D,
        "assignment_manifest_digest": D,
    }
    output_body = {
        "assignment_ref": ASSIGNMENT_REF,
        "runtime_attempt_id": "attempt-1",
        "result_id": "result-1",
        "output_names": ["proposal"],
        "result_manifest_digest": D,
        "policy_digest": D,
    }
    return [
        envelope(
            "control.hello",
            {"role": "runtime-adapter", "supported_versions": [{"major": 1, "minor": 0}], "capabilities": ["core.runtime-lifecycle", "core.errors"], "extensions": [], "limits": limits, "runtime_profile_digest": D},
            operation=None,
        ),
        envelope(
            "control.welcome",
            {"selected_version": {"major": 1, "minor": 0}, "capabilities": ["core.runtime-lifecycle", "core.errors"], "extensions": [], "effective_limits": limits},
            message_type="reply",
            operation=None,
        ),
        envelope(
            "offer.issue",
            {
                "offer_id": "offer-1",
                "runtime_attempt_id": "attempt-1",
                "work_ref": WORK_REF,
                "human_contract_digest": D,
                "human_contract_summary": "Review the exact bound dossier.",
                "input_manifest_digest": D,
                "declared_output_names": ["proposal"],
                "policy_digest": D,
                "runtime_profile_digest": D,
                "expires_at": "2026-08-21T22:05:00.000Z",
                "sensitive": True,
                "claim_token": "x" * 32,
            },
        ),
        envelope(
            "offer.decide",
            {"offer_id": "offer-1", "runtime_attempt_id": "attempt-1", "work_ref": WORK_REF, "decision": "accept", "reason": "Contract accepted.", "claim_token": "x" * 32},
        ),
        envelope("assignment.activate", {**assignment_body, "policy_digest": D, "runtime_profile_digest": D}),
        envelope("runtime.start", assignment_body),
        envelope("runtime.cancel", {"assignment_ref": ASSIGNMENT_REF, "runtime_attempt_id": "attempt-1", "runtime_id": "runtime-1", "reason": "Authority fenced the assignment.", "fence_receipt_digest": D}),
        envelope("runtime.inspect", {"runtime_attempt_id": "attempt-1", "assignment_ref": ASSIGNMENT_REF, "runtime_id": "runtime-1"}, operation=None),
        envelope(
            "activity.emit",
            {"activity_id": "activity-1", "source_event_seq": 4, "assignment_ref": ASSIGNMENT_REF, "plan_step_id": "step-1", "kind": "evidence", "summary": "Recorded focused verification.", "record_paths": ["work/records/evidence.txt"]},
            message_type="event",
            operation=None,
        ),
        envelope("result.declare", {"result_id": "result-1", "assignment_ref": ASSIGNMENT_REF, "disposition": "completed", "declared_outputs": ["proposal"], "evidence": [evidence()], "summary": "Declared work complete."}),
        envelope("output.freeze", output_body),
        envelope("output.collect", output_body),
        envelope("proposal.publish", {"assignment_ref": ASSIGNMENT_REF, "proposal_id": "proposal-1", "proposal_manifest_digest": D, "target_revision": GIT_OBJECT, "policy_digest": D}),
        envelope("output.retain", {"assignment_ref": ASSIGNMENT_REF, "runtime_attempt_id": "attempt-1", "artifact_ids": ["artifact-1"], "disposition": "retain", "retention_policy_digest": D}),
        envelope("runtime.destroy", {"assignment_ref": ASSIGNMENT_REF, "runtime_attempt_id": "attempt-1", "runtime_id": "runtime-1", "intake_receipt_digest": D, "retention_policy_digest": D}),
        envelope("operation.reply", {"status": "committed", "result_schema": "runtime-start-result", "result_digest": D, "result_artifact": None}, message_type="reply", operation=OPERATION),
        envelope(
            "control.error",
            {"category": "integrity", "code": "digest", "summary": "Body digest did not match.", "retry": "never", "operation_state": "refused", "assignment_ref": ASSIGNMENT_REF, "runtime_attempt_id": "attempt-1", "diagnostic_artifact": None},
            message_type="reply",
            operation=OPERATION,
        ),
    ]


def apply_patch(document: dict, patch: dict[str, object]) -> None:
    for dotted, value in patch.items():
        cursor: object = document
        parts = dotted.split(".")
        for part in parts[:-1]:
            cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
        if isinstance(cursor, list):
            cursor[int(parts[-1])] = value
        else:
            cursor[parts[-1]] = value


def error_messages(error) -> list[str]:
    messages = [error.message]
    for child in error.context:
        messages.extend(error_messages(child))
    return messages


class SchemaAndVectorTests(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)

    def test_canonical_valid_vectors(self) -> None:
        for vector in VECTORS["valid"]:
            with self.subTest(vector=vector["name"]):
                document = vector["document"]
                VALIDATOR.validate(document)
                if document.get("protocol") == "baton.worker-control":
                    validate_envelope(document)
                else:
                    validate_manifest(document)

    def test_every_typed_manifest_and_receipt_shape(self) -> None:
        for document in typed_documents():
            with self.subTest(schema=document["schema"]):
                VALIDATOR.validate(document)
                validate_manifest(document)

    def test_every_portable_operation_body_shape(self) -> None:
        for document in control_envelopes():
            with self.subTest(kind=document["kind"]):
                VALIDATOR.validate(document)
                validate_envelope(document)

    def test_invalid_vectors(self) -> None:
        valid = {item["name"]: item["document"] for item in VECTORS["valid"]}
        for vector in VECTORS["invalid"]:
            with self.subTest(vector=vector["name"]):
                document = copy.deepcopy(valid[vector["mutate_valid"]])
                apply_patch(document, vector["patch"])
                if vector["layer"] == "schema":
                    errors = list(VALIDATOR.iter_errors(document))
                    self.assertTrue(errors)
                    messages = [message for error in errors for message in error_messages(error)]
                    self.assertTrue(any(vector["expected"] in message for message in messages), messages)
                elif document.get("protocol") == "baton.worker-control":
                    with self.assertRaisesRegex(ContractError, vector["expected"]):
                        validate_envelope(document)
                else:
                    document = seal_manifest(document)
                    with self.assertRaisesRegex(ContractError, vector["expected"]):
                        validate_manifest(document)


class SemanticModelTests(unittest.TestCase):
    def test_exact_retry_replays_first_result(self) -> None:
        ledger = ReplayLedger()
        first = ledger.apply("op-1", D, {"runtime_id": "runtime-1"})
        retry = ledger.apply("op-1", D, {"runtime_id": "runtime-1"})
        self.assertEqual(first[0], "committed")
        self.assertEqual(retry, ("replayed", first[1]))

    def test_operation_id_collision_refuses(self) -> None:
        ledger = ReplayLedger()
        ledger.apply("op-1", D, {"runtime_id": "runtime-1"})
        with self.assertRaisesRegex(ContractError, "operation collision"):
            ledger.apply("op-1", "sha256:" + "b" * 64, {"runtime_id": "runtime-2"})

    def test_same_participant_new_generation_does_not_authorize_old(self) -> None:
        fence = AssignmentFence(ASSIGNMENT_REF)
        stale = copy.deepcopy(ASSIGNMENT_REF)
        stale["generation"] -= 1
        with self.assertRaisesRegex(ContractError, "stale assignment generation"):
            fence.require_live(stale)

    def test_fenced_assignment_refuses_publication(self) -> None:
        fence = AssignmentFence(ASSIGNMENT_REF)
        fence.end()
        with self.assertRaisesRegex(ContractError, "assignment ended"):
            fence.require_live(ASSIGNMENT_REF)

    def test_runtime_observation_cannot_regress(self) -> None:
        observations = ObservationLedger()
        observations.observe(1, "running")
        observations.observe(2, "quiescent")
        with self.assertRaisesRegex(ContractError, "runtime state regression"):
            observations.observe(3, "running")

    def test_destroyed_runtime_is_terminal(self) -> None:
        observations = ObservationLedger()
        observations.observe(1, "destroyed")
        with self.assertRaisesRegex(ContractError, "runtime state regression"):
            observations.observe(2, "destroyed")

    # --- W4487: the decline binding, ruled 2026-08-22 --------------------
    #
    # The frozen schema proves the SHAPE (null for a decline, a string for
    # an accept). It cannot prove the BINDING, and the binding is exactly
    # what the superseded bearer requirement used to stand in for — so
    # these pin the section 12 rule that replaces it.

    def _issued(self, **overrides: object) -> dict:
        issued = {
            "offer_id": "offer-w4487-1",
            "runtime_attempt_id": "attempt-w4487-1",
            "work_ref": WORK_REF,
            "verifier_unspent": True,
        }
        issued.update(overrides)
        return issued

    def _decline_body(self) -> dict:
        return copy.deepcopy(
            {item["name"]: item["document"] for item in VECTORS["valid"]}
            ["offer-decide-decline-carries-no-bearer"]["body"])

    def test_a_decline_naming_its_own_offer_is_authorized_without_a_bearer(self) -> None:
        validate_offer_decide(self._decline_body(), self._issued())

    def test_a_differently_bound_decline_refuses(self) -> None:
        for field, value in [
            ("offer_id", "offer-w4487-2"),
            ("runtime_attempt_id", "attempt-w4487-2"),
            ("work_ref", {"authority_uuid": "43c55d4b1234567890abcdef12345678",
                          "work_id": "43c55d4b-W9999"}),
        ]:
            with self.subTest(field=field):
                body = self._decline_body()
                body[field] = value
                with self.assertRaisesRegex(ContractError, "does not match the issued offer"):
                    validate_offer_decide(body, self._issued())

    def test_a_decline_against_a_spent_verifier_refuses(self) -> None:
        with self.assertRaisesRegex(ContractError, "already spent"):
            validate_offer_decide(self._decline_body(),
                                  self._issued(verifier_unspent=False))

    def test_the_bearer_asymmetry_is_enforced_in_both_directions(self) -> None:
        carrying = self._decline_body()
        carrying["claim_token"] = "b" * 43
        with self.assertRaisesRegex(ContractError, "must not carry the claim bearer"):
            validate_offer_decide(carrying, self._issued())
        # And acceptance is UNCHANGED by the ruling: it still requires one.
        bare_accept = self._decline_body()
        bare_accept["decision"] = "accept"
        with self.assertRaisesRegex(ContractError, "must carry the claim bearer"):
            validate_offer_decide(bare_accept, self._issued())
        accepting = self._decline_body()
        accepting.update({"decision": "accept", "claim_token": "b" * 43})
        validate_offer_decide(accepting, self._issued())

    def test_a_decline_is_never_a_durable_secret_surface(self) -> None:
        """`claim_token: null` is a wire field, and the durable-secret rule
        is about persisted documents — but a decline is the one decision
        body that carries the key at all, so the boundary is pinned."""
        sealed = seal_manifest({"schema": "baton.worker-manifest/assignment",
                                "work_ref": WORK_REF,
                                "decline": self._decline_body()})
        with self.assertRaisesRegex(ContractError, "secret field"):
            validate_manifest(sealed)

    # --- The operation signature (review 2026-08-22T14:39:32Z [P1]) ------
    #
    # Section 4.2 always said the signature is the canonical digest of the
    # operation KIND and every effective durable operand. Nothing computed
    # one, so the decline vector copied `body_digest` into it and a document
    # that changed its durable reason, recomputed the body digest and kept the
    # old signature passed both the frozen schema and this model.

    def _decline_envelope(self) -> dict:
        return copy.deepcopy(
            {item["name"]: item["document"] for item in VECTORS["valid"]}
            ["offer-decide-decline-carries-no-bearer"])

    def test_the_signature_covers_the_kind_and_so_is_not_the_body_digest(self) -> None:
        document = self._decline_envelope()
        self.assertNotEqual(document["operation"]["signature_digest"],
                            document["body_digest"])
        # Two kinds carrying byte-identical operands are different operations.
        self.assertNotEqual(operation_signature("offer.decide", document["body"]),
                            operation_signature("offer.issue", document["body"]))
        payload = operation_signature_payload(document["kind"], document["body"])
        self.assertEqual(payload["kind"], "offer.decide")

    def test_every_durable_operand_is_in_the_signature(self) -> None:
        document = self._decline_envelope()
        for field in ("offer_id", "runtime_attempt_id", "work_ref", "decision", "reason"):
            with self.subTest(operand=field):
                changed = copy.deepcopy(document["body"])
                changed[field] = ({"authority_uuid": "43c55d4b1234567890abcdef12345678",
                                   "work_id": "43c55d4b-W9999"}
                                  if field == "work_ref" else "different-" + str(changed[field]))
                self.assertNotEqual(operation_signature(document["kind"], changed),
                                    document["operation"]["signature_digest"])

    def test_a_changed_reason_with_a_stale_signature_refuses(self) -> None:
        """The reviewer's exact reproduction.

        Changing the durable prose and recomputing ONLY the body digest left a
        signature that still named the first decline. A manager journalling by
        it would have replayed that first decline against conflicting prose.
        """
        document = self._decline_envelope()
        stale = document["operation"]["signature_digest"]
        document["body"]["reason"] = "the worker endpoint declines for an entirely different reason"
        document["body_digest"] = digest(document["body"])
        VALIDATOR.validate(document)          # the frozen schema still accepts it
        with self.assertRaisesRegex(ContractError, "operation signature mismatch"):
            validate_envelope(document)
        self.assertEqual(document["operation"]["signature_digest"], stale)

    def test_the_bearer_rides_the_signature_as_its_verifier_not_literally(self) -> None:
        """`claim_token` is an effective operand and a forbidden durable value.

        Both at once, so it enters the payload as the verifier the manager
        already holds: the signature changes with the bearer, and the bearer
        itself never lands in a durable signature payload.
        """
        accepting = self._decline_envelope()["body"]
        accepting.update({"decision": "accept", "claim_token": GOLDEN_BEARER})
        other = copy.deepcopy(accepting)
        other["claim_token"] = "y" * 43
        self.assertNotEqual(operation_signature("offer.decide", accepting),
                            operation_signature("offer.decide", other))
        payload = operation_signature_payload("offer.decide", accepting)
        self.assertNotIn("claim_token", payload["operands"])
        # The value W151 STORES, pinned as a literal on both sides. Round 2 of
        # this review asserted `digest(bearer)` here — SHA-256 over the JCS
        # JSON encoding — which is a self-consistent answer to the wrong
        # question and is exactly what the re-review found.
        self.assertEqual(payload["operands"]["claim_token_verifier"],
                         GOLDEN_VERIFIER)
        self.assertNotEqual(GOLDEN_VERIFIER, digest(GOLDEN_BEARER),
                            "the verifier is the JSON encoding's digest again")
        # A decline commits to the ABSENCE of a bearer just as positively.
        declining = operation_signature_payload("offer.decide", self._decline_envelope()["body"])
        self.assertIsNone(declining["operands"]["claim_token_verifier"])
        # And the payload is safe to persist, which is the whole reason for it.
        seal_manifest(payload)
        validate_manifest(seal_manifest({"schema": "baton.worker-manifest/assignment",
                                         "work_ref": WORK_REF,
                                         "signature_payload": payload}))

    def test_the_verifier_hashes_the_bearer_bytes_not_a_json_encoding(self) -> None:
        """The re-review's P1, on this side of the boundary.

        W151 owns the offer record and therefore owns what the verifier IS.
        This module repeated the derivation instead of importing it, because
        the two packages are independent design records — so the golden pair
        is pinned as a LITERAL here and there, and the conformance package
        asserts the two agree. A derivation that changed on one side would
        move its own expectation with it; a literal cannot.
        """
        self.assertEqual(token_verifier(GOLDEN_BEARER), GOLDEN_VERIFIER)
        self.assertTrue(GOLDEN_VERIFIER.startswith("sha256:"))
        self.assertEqual(len(GOLDEN_VERIFIER), len("sha256:") + 64)
        # A token whose JSON encoding is not its own bytes still verifies by
        # its bytes: the quote escapes, the backslash doubles, the non-ASCII
        # character may or may not survive as itself.
        for awkward in ['a"b' + "c" * 29, "a\\b" + "c" * 29, "\u00e9" + "c" * 31]:
            with self.subTest(token=awkward):
                self.assertEqual(
                    token_verifier(awkward),
                    "sha256:" + hashlib.sha256(awkward.encode("utf-8")).hexdigest())
                self.assertNotEqual(token_verifier(awkward), digest(awkward))
        # A decline commits to `null`, so no derivation is involved at all —
        # which is why the frozen decline vector's signature is unchanged by
        # this correction.
        declining = operation_signature_payload(
            "offer.decide", self._decline_envelope()["body"])
        self.assertIsNone(declining["operands"]["claim_token_verifier"])

    def test_a_reply_echoes_the_request_signature_and_is_not_recomputed(self) -> None:
        """Section 5: a reply carries "the same operation" as its request.

        Its `signature_digest` is the REQUEST's, so recomputing it over the
        result body would refuse every conforming reply. The same document
        sent as a COMMAND is refused, which is what keeps this an exemption
        for replies rather than a hole for everyone.
        """
        reply = envelope("operation.reply",
                         {"status": "committed", "result_schema": "offer-decide-result",
                          "result_digest": D, "result_artifact": None},
                         message_type="reply", operation=OPERATION)
        validate_envelope(reply)
        as_command = copy.deepcopy(reply)
        as_command.update({"message_type": "command", "correlation_id": None})
        with self.assertRaisesRegex(ContractError, "operation signature mismatch"):
            validate_envelope(as_command)

    def test_a_reused_id_with_its_own_valid_signature_is_a_collision(self) -> None:
        """The second stage, and a different failure from the stale signature.

        Stage one refuses a document whose signature does not describe it.
        This is the document that passes stage one honestly — new prose, its
        OWN correct signature — and is refused because it reuses a committed
        operation id. Both are needed: neither catches the other's case.
        """
        first = self._decline_envelope()
        second = copy.deepcopy(first)
        second["body"]["reason"] = "the worker endpoint declines for an entirely different reason"
        second["body_digest"] = digest(second["body"])
        second["operation"]["signature_digest"] = operation_signature(second["kind"], second["body"])
        validate_envelope(second)             # honestly signed, and still refused below
        ledger = ReplayLedger()
        ledger.apply(first["operation"]["operation_id"],
                     first["operation"]["signature_digest"], {"offer_state": "declined"})
        with self.assertRaisesRegex(ContractError, "operation collision"):
            ledger.apply(second["operation"]["operation_id"],
                         second["operation"]["signature_digest"], {"offer_state": "declined"})
        # And the exact retry of the first still replays byte-for-byte.
        self.assertEqual(ledger.apply(first["operation"]["operation_id"],
                                      first["operation"]["signature_digest"],
                                      {"offer_state": "declined"})[0], "replayed")

    def test_error_code_must_match_category(self) -> None:
        envelope = copy.deepcopy(VECTORS["valid"][0]["document"])
        envelope.update({"message_type": "reply", "kind": "control.error", "correlation_id": "message-hello-1"})
        envelope["body"] = {
            "category": "integrity",
            "code": "runtime-start",
            "summary": "Mapped to the wrong portable category.",
            "retry": "never",
            "operation_state": "refused",
            "assignment_ref": None,
            "runtime_attempt_id": None,
            "diagnostic_artifact": None,
        }
        envelope["body_digest"] = digest(envelope["body"])
        VALIDATOR.validate(envelope)
        with self.assertRaisesRegex(ContractError, "does not belong"):
            validate_envelope(envelope)


if __name__ == "__main__":
    unittest.main()
