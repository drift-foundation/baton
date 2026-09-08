"""W103077: replay-safe proposal publication and integration driving."""

import copy
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.authority.errors import Refusal as AuthorityRefusal
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import driver, execution, runtime
from baton_v12.integration import entries_of, lease_of

from .test_execution import ExecutionCase, PARTICIPANT, profile


ASSIGNMENT = {
    "work_ref": {"authority_uuid": "0123456789abcdef0123456789abcdef",
                 "work_id": "01234567-W1"},
    "participant": "baton.impl", "generation": 1}
TARGET = {"algorithm": "sha1", "hex": "a" * 40}
HEAD = {"algorithm": "sha1", "hex": "b" * 40}


class Publisher:
    participant = "baton.impl"

    def __init__(self, expected, *, target=TARGET["hex"]):
        self.expected = expected
        self.target = target
        self.calls = []
        self.failure = None

    def canonical_target(self):
        return self.target

    def publish(self, operands):
        self.calls.append(copy.deepcopy(operands))
        if self.failure is not None:
            raise self.failure
        return copy.deepcopy(self.expected)

    def proposal(self, proposal_id):
        return dict(copy.deepcopy(self.expected), decision={},
                    published_at="2026-09-06T16:00:00.000Z")


class PublicationCase(unittest.TestCase):

    def setUp(self):
        self.manager = SimpleNamespace(_connection=lambda: None)
        artifact = {"artifact_id": "artifact-1",
                    "media_type": "application/octet-stream", "bytes": 8,
                    "content_digest": "sha256:" + "7" * 64,
                    "locator": "file:///var/lib/baton/artifact-1"}
        content = {"entries": [{"path": "change.bundle", "bytes": 8,
                                "content_digest": "sha256:" + "6" * 64}],
                   "entry_count": 1, "total_bytes": 8,
                   "tree_digest": "sha256:" + "5" * 64}
        self.result = {
            "assignment_ref": copy.deepcopy(ASSIGNMENT),
            "result_id": "result-1", "input_manifest_digest": "sha256:input",
            "policy_digest": "sha256:policy",
            "outputs": [{"name": "proposal", "type": "git-change-proposal",
                         "status": "present", "content_manifest": content,
                         "artifact": copy.deepcopy(artifact),
                         "result_metadata": {}}]}
        self.proposal = {
            "assignment_ref": copy.deepcopy(ASSIGNMENT),
            "proposal_id": "proposal-1", "result_id": "result-1",
            "result_manifest_digest": "sha256:result",
            "input_manifest_digest": "sha256:input",
            "policy_digest": "sha256:policy",
            "runtime_profile_digest": "sha256:profile",
            "output_digest": content["tree_digest"],
            "source_base": copy.deepcopy(TARGET),
            "target_revision": copy.deepcopy(TARGET),
            "proposal_head": copy.deepcopy(HEAD),
            "proposal_artifact": copy.deepcopy(artifact),
            "author_tests": [], "implementation_recap": "done",
            "dossier_evidence": []}
        operands = {
            "expect": ASSIGNMENT, "proposal_id": "proposal-1",
            "result_id": "result-1", "result_digest": "sha256:result",
            "candidate_digest": HEAD["hex"], "input_digest": "sha256:input",
            "policy_digest": "sha256:policy", "target": TARGET["hex"]}
        operation = {"operation_id": "publish-1",
                     "signature_digest": digest(
                         {"kind": "publish", "operands": operands})}
        self.proposal["publish_operation"] = operation
        self.expected = {
            "proposal_id": "proposal-1", "assignment_ref": ASSIGNMENT,
            "result_id": "result-1", "result_digest": "sha256:result",
            "candidate_digest": HEAD["hex"], "input_digest": "sha256:input",
            "policy_digest": "sha256:policy", "target": TARGET["hex"]}
        self.proposal["publish_receipt_digest"] = digest(self.expected)
        self.publisher = Publisher(self.expected)
        self.patches = mock.patch.multiple(
            driver,
            frozen_output_of=mock.DEFAULT,
            load_manifest=mock.DEFAULT,
            assignment_of=mock.DEFAULT)
        replaced = self.patches.start()
        self.addCleanup(self.patches.stop)
        replaced["frozen_output_of"].return_value = {
            "result_id": "result-1", "disposition": "completed",
            "manifest_digest": "sha256:result"}
        replaced["load_manifest"].side_effect = (
            lambda _manager, key, definition:
            copy.deepcopy(self.proposal if definition == "proposalManifest"
                          else self.result))
        replaced["assignment_of"].return_value = {
            "authority_uuid": ASSIGNMENT["work_ref"]["authority_uuid"],
            "work_id": ASSIGNMENT["work_ref"]["work_id"],
            "participant": ASSIGNMENT["participant"],
            "generation": ASSIGNMENT["generation"]}

    def publish(self):
        return driver.publish_candidate(
            self.manager, self.publisher, attempt_id="attempt-1",
            proposal_manifest_digest="sha256:proposal")

    def test_publication_uses_only_cross_bound_manager_owned_members(self):
        self.assertEqual(self.publish()["candidate_digest"], HEAD["hex"])
        self.assertEqual(self.publisher.calls[0], {
            "expect": ASSIGNMENT, "operation_id": "publish-1",
            "proposal_id": "proposal-1", "result_id": "result-1",
            "result_digest": "sha256:result",
            "candidate_digest": HEAD["hex"], "input_digest": "sha256:input",
            "policy_digest": "sha256:policy", "target": TARGET["hex"]})

    def test_exact_publication_replay_is_identical(self):
        self.assertEqual(self.publish(), self.publish())
        self.assertEqual(self.publisher.calls[0], self.publisher.calls[1])

    def test_a_fenced_producer_refuses_in_the_authority_before_publication(self):
        self.publisher.failure = AuthorityRefusal(
            "assignment generation was fenced and ended")
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("fenced", caught.exception.message)

    def test_target_movement_refuses_without_calling_publish(self):
        self.publisher.target = "c" * 40
        with self.assertRaises(ContractRefusal):
            self.publish()
        self.assertEqual(self.publisher.calls, [])

    def test_every_producer_cross_wire_refuses_before_publication(self):
        changes = (
            (self.proposal, "assignment_ref", dict(ASSIGNMENT, generation=2)),
            (self.proposal, "result_id", "result-2"),
            (self.proposal, "result_manifest_digest", "sha256:other"),
            (self.proposal, "input_manifest_digest", "sha256:other"),
            (self.proposal, "source_base", HEAD),
            (self.proposal, "output_digest", "sha256:other"),
        )
        for owner, name, changed in changes:
            with self.subTest(member=name):
                prior = owner[name]
                owner[name] = changed
                with self.assertRaises(ContractRefusal):
                    self.publish()
                owner[name] = prior
        self.assertEqual(self.publisher.calls, [])

    def test_changed_operation_or_receipt_binding_refuses_before_publish(self):
        for name in ("signature_digest",):
            with self.subTest(name=name):
                prior = self.proposal["publish_operation"][name]
                self.proposal["publish_operation"][name] = "sha256:other"
                with self.assertRaises(ContractRefusal):
                    self.publish()
                self.proposal["publish_operation"][name] = prior
        prior = self.proposal["publish_receipt_digest"]
        self.proposal["publish_receipt_digest"] = "sha256:other"
        with self.assertRaises(ContractRefusal):
            self.publish()
        self.proposal["publish_receipt_digest"] = prior
        self.assertEqual(self.publisher.calls, [])


class ReceiptSession:
    def __init__(self, participant, verb):
        self.participant, self.verb = participant, verb
        self.calls = []
        self.failure = None
        self.integration_receipt = None
        setattr(self, verb, self.call)

    def call(self, operands):
        self.calls.append(copy.deepcopy(operands))
        if self.failure is not None:
            raise self.failure
        if self.verb == "integrate":
            self.integration_receipt = {
                "kind": "integration",
                "receipt_id": operands["integration_id"],
                "proposal_id": operands["proposal_id"],
                "actor": self.participant, "disposition": "integrated",
                "candidate_digest": "candidate-1", "target": "target-1"}
        return copy.deepcopy(operands)

    def receipt(self, proposal_id, kind):
        if kind == "integration" and self.integration_receipt is not None \
                and self.integration_receipt["proposal_id"] == proposal_id:
            return copy.deepcopy(self.integration_receipt)
        return None


class AcceptedReceiptCase(unittest.TestCase):

    def setUp(self):
        self.manager = SimpleNamespace(_connection=lambda: None)
        self.authority = SimpleNamespace(
            proposal=lambda proposal_id: {
                "proposal_id": proposal_id,
                "assignment_ref": copy.deepcopy(ASSIGNMENT),
                "decision": {}, "result_id": "result-1",
                "result_digest": "sha256:result",
                "candidate_digest": "candidate-1",
                "input_digest": "sha256:input",
                "policy_digest": "sha256:policy", "target": "target-1",
                "published_at": "2026-09-06T16:00:00.000Z"},
            policy_generation=lambda: 3)
        self.verify = ReceiptSession("baton.verify", "verify")
        self.review = ReceiptSession("baton.review", "review")
        self.approve = ReceiptSession("baton.approve", "approve")
        self.accepted = {"line_id": "line-1", "checkpoint_id": "cp-1",
                         "verdict_id": "verdict-1",
                         "checkpoint_digest": "sha256:checkpoint"}

    def receipts(self, generation=3, evidence=None):
        """W112029: these cases measure receipt IDENTITY and replay, so the
        evidence resolution is supplied rather than rebuilt -- this fixture has
        no producer to read one from. The resolution itself is driven against a
        real retained result in the admission cases below."""
        self.authority.policy_generation = lambda: generation
        held = evidence or {"attempt_id": "attempt-1",
                            "checkpoint_id": "cp-1",
                            "assignment_ref": {"generation": 1},
                            "input_manifest_digest": "sha256:" + "1" * 64,
                            "result_id": "result-attempt-1",
                            "result_digest": "sha256:" + "2" * 64,
                            "observation": observation()}
        with mock.patch.object(driver, "integration_checkpoint",
                               return_value=copy.deepcopy(self.accepted)), \
                mock.patch.object(driver, "ordinary_test_evidence",
                                  return_value=copy.deepcopy(held)):
            return driver._accepted_receipts(
                self.manager, self.authority, self.verify, self.review,
                self.approve, line_id="line-1", proposal_id="proposal-1",
                policy_generation=generation,
                required_tests=requirements(held["input_manifest_digest"]))

    def test_receipts_are_separate_attributable_and_replay_stable(self):
        first = self.receipts()[2]
        second = self.receipts()[2]
        self.assertEqual(first, second)
        self.assertEqual(self.verify.calls[0]["observation"], "passed")
        self.assertEqual(self.review.calls[0]["disposition"], "accepted")
        self.assertEqual(self.approve.calls[0]["disposition"], "approved")
        self.assertEqual(self.approve.calls[0]["policy_generation"], 3)
        ids = {self.verify.calls[0]["verification_id"],
               self.review.calls[0]["review_id"],
               self.approve.calls[0]["approval_id"]}
        self.assertEqual(len(ids), 3)

    def test_no_receipt_is_written_without_an_accepted_checkpoint(self):
        with mock.patch.object(driver, "integration_checkpoint",
                               return_value=None):
            with self.assertRaises(ContractRefusal):
                driver._accepted_receipts(
                    self.manager, self.authority, self.verify, self.review,
                    self.approve, line_id="line-1",
                    proposal_id="proposal-1", policy_generation=3,
                    required_tests=requirements("sha256:" + "1" * 64))
        self.assertEqual(self.verify.calls, [])

    def test_changed_policy_generation_changes_the_bound_operation(self):
        self.receipts(3)
        self.receipts(4)
        self.assertNotEqual(self.approve.calls[0]["operation_id"],
                            self.approve.calls[1]["operation_id"])
        self.assertNotEqual(self.approve.calls[0]["policy_generation"],
                            self.approve.calls[1]["policy_generation"])

    def test_the_pinned_generation_must_be_the_authoritys_current_one(self):
        self.authority.policy_generation = lambda: 4
        with mock.patch.object(driver, "integration_checkpoint",
                               return_value=copy.deepcopy(self.accepted)):
            with self.assertRaises(ContractRefusal):
                driver._accepted_receipts(
                    self.manager, self.authority, self.verify, self.review,
                    self.approve, line_id="line-1",
                    proposal_id="proposal-1", policy_generation=3,
                    required_tests=requirements("sha256:" + "1" * 64))
        self.assertEqual(self.verify.calls, [])


class DriverCase(unittest.TestCase):

    def setUp(self):
        self.store = SimpleNamespace(_connection=lambda: None)
        self.manager = SimpleNamespace(_connection=lambda: None)
        self.jobs = SimpleNamespace(_connection=lambda: None)
        self.authority = SimpleNamespace(proposal=lambda _proposal: {},
                                         policy_generation=lambda: 3)
        self.verify = ReceiptSession("baton.verify", "verify")
        self.review = ReceiptSession("baton.review", "review")
        self.approve = ReceiptSession("baton.approve", "approve")
        self.integrator = ReceiptSession("baton.integrator", "integrate")
        self.port = SimpleNamespace(run=mock.Mock())
        # W112029: this fixture drives the ADMISSION composition and holds no
        # frozen result, so the evidence resolution is supplied here and proved
        # for real in the admission cases that own a producer.
        self.required = requirements("sha256:" + "1" * 64)
        self.evidence = {"attempt_id": "attempt-1", "checkpoint_id": "cp-1",
                         "assignment_ref": {"generation": 1},
                         "input_manifest_digest": "sha256:" + "1" * 64,
                         "result_id": "result-attempt-1",
                         "result_digest": "sha256:" + "2" * 64,
                         "observation": observation()}
        self.profile = runtime.integration_profile(
            profile_kind="git", profile_version=1,
            integrator_participant="baton.integrator",
            instructions_digest="sha256:instructions")
        self.accepted = {"line_id": "line-1", "checkpoint_id": "cp-1",
                         "verdict_id": "verdict-1",
                         "checkpoint_digest": "sha256:checkpoint"}
        self.proposal = {"proposal_id": "proposal-1",
                         "candidate_digest": "candidate-1",
                         "target": "target-1"}
        self.account = {"proposal_id": "proposal-1", "line_id": "line-1"}
        self.entry_id = driver._identity(
            "entry", {"canonical_target_id": "target-1",
                      "eligibility": self.account})
        self.entry = {"entry_id": self.entry_id,
                      "canonical_target_id": "target-1", "state": "queued",
                      "settlement": {"imported_paths": [],
                                     "verification": {}},
                      "eligibility": copy.deepcopy(self.account)}

    def call(self, *, lease=None, delivery=None, entry_state="queued",
             outcome="running", witness="not-started", observed="waiting"):
        self.entry["state"] = entry_state
        answer = {"outcome": outcome, "entry": self.entry_id,
                  "assignment": {"owned": True}, "observed": None,
                  "settlement": {"imported_paths": [], "verification": {}}}
        accepted_receipts = (copy.deepcopy(self.accepted),
                             copy.deepcopy(self.proposal), {"ok": True})
        with mock.patch.multiple(
                driver,
                _accepted_receipts=mock.Mock(return_value=accepted_receipts),
                resolved_account=mock.Mock(return_value=copy.deepcopy(
                    self.account)),
                admit_candidate=mock.Mock(return_value=self.entry),
                entries_of=mock.Mock(return_value=[self.entry]),
                lease_of=mock.Mock(return_value=lease),
                target_of=mock.Mock(return_value={"state": "open"}),
                _existing_assignment=mock.Mock(return_value={"owned": True}),
                ) as patched, \
                mock.patch.object(driver.runtime, "adopt_delivery",
                                  return_value=delivery), \
                mock.patch.object(driver.execution, "integrate_next",
                                  return_value=answer) as integrate, \
                mock.patch.object(driver.runtime, "compose_assignment",
                                  return_value={"owned": True}), \
                mock.patch.object(driver.runtime, "prior_runtime_witness",
                                  return_value={"execution_runtime": witness}), \
                mock.patch.object(driver.runtime, "observed_delivery",
                                  return_value={"state": observed}), \
                mock.patch.object(driver.runtime, "publish_assignment") as publish, \
                mock.patch.object(driver, "live_grant") as live, \
                mock.patch.object(driver.execution, "settle_observed",
                                  return_value=answer) as settle, \
                mock.patch.object(driver.execution, "complete_integrated") as complete, \
                mock.patch.object(driver.recovery, "hold_interrupted",
                                  return_value={"state": "operator-held"}) as hold:
            result = driver.admit_accepted(
                self.store, self.manager, self.jobs, self.authority,
                self.verify, self.review, self.approve, self.integrator,
                self.port, canonical_target_id="target-1", line_id="line-1",
                proposal_id="proposal-1", policy_generation=3,
                profile=self.profile, attempt_id="attempt-1",
                launch_root="/launch", workspace_group=object(),
                required_tests=self.required)
            return (result, patched, integrate, publish, live, settle, hold,
                    complete)

    def test_fresh_admission_drives_the_existing_fenced_executor(self):
        answer, _, integrate, publish, _, _, _, _ = self.call()
        self.assertEqual(answer["outcome"], "running")
        integrate.assert_called_once()
        publish.assert_not_called()

    def test_restart_before_run_adopts_then_uses_the_final_live_cutpoint(self):
        lease = {"lease_id": "lease-1", "state": "live", "fence": 1,
                 "canonical_target_id": "target-1", "entry_id": self.entry_id,
                 "attempt_id": "attempt-1",
                 "integrator_participant": "baton.integrator"}
        answer, _, integrate, publish, live, settle, hold, complete = self.call(
            lease=lease, delivery=object(), outcome="integrated")
        integrate.assert_not_called()
        publish.assert_called_once()
        live.assert_called_once()
        self.port.run.assert_called_once()
        settle.assert_called_once()
        complete.assert_called_once()
        hold.assert_not_called()
        self.assertIsNotNone(answer["authority_receipt"])

    def test_restart_after_run_holds_and_never_starts_a_second_writer(self):
        lease = {"lease_id": "lease-1", "state": "live", "fence": 1,
                 "canonical_target_id": "target-1", "entry_id": self.entry_id,
                 "attempt_id": "attempt-1",
                 "integrator_participant": "baton.integrator"}
        answer, _, integrate, publish, live, settle, hold, _ = self.call(
            lease=lease, delivery=object(), witness="running")
        self.assertEqual(answer["outcome"], "held")
        hold.assert_called_once()
        integrate.assert_not_called()
        publish.assert_not_called()
        live.assert_not_called()
        settle.assert_not_called()
        self.port.run.assert_not_called()

    def test_authority_refusal_holds_before_coordinator_completion(self):
        self.integrator.failure = AuthorityRefusal("completion unavailable")
        answer, _, _, _, _, _, hold, complete = self.call(
            outcome="integrated")
        self.assertEqual(answer["outcome"], "held")
        hold.assert_called_once()
        complete.assert_not_called()
        self.assertIsNone(answer["authority_receipt"])

    def test_replayed_integrated_entry_only_reads_an_existing_receipt(self):
        lease = {"lease_id": "lease-1", "state": "released", "fence": 1,
                 "canonical_target_id": "target-1", "entry_id": self.entry_id,
                 "attempt_id": "attempt-1",
                 "integrator_participant": "baton.integrator"}
        basis = {"proposal_id": "proposal-1", "entry_id": self.entry_id,
                 "candidate_digest": "candidate-1", "target": "target-1",
                 "checkpoint_id": "cp-1", "verdict_id": "verdict-1"}
        self.integrator.integration_receipt = {
            "kind": "integration",
            "receipt_id": driver._identity("integration-receipt", basis),
            "proposal_id": "proposal-1", "actor": "baton.integrator",
            "disposition": "integrated", "candidate_digest": "candidate-1",
            "target": "target-1"}
        answer, _, integrate, _, _, _, _, _ = self.call(
            lease=lease, delivery=None, entry_state="integrated")
        self.assertEqual(answer["outcome"], "integrated")
        self.assertEqual(self.integrator.calls, [])
        integrate.assert_not_called()

    def test_integrated_entry_without_its_exact_lease_fails_closed(self):
        basis = {"proposal_id": "proposal-1", "entry_id": self.entry_id,
                 "candidate_digest": "candidate-1", "target": "target-1",
                 "checkpoint_id": "cp-1", "verdict_id": "verdict-1"}
        self.integrator.integration_receipt = {
            "kind": "integration",
            "receipt_id": driver._identity("integration-receipt", basis),
            "proposal_id": "proposal-1", "actor": "baton.integrator",
            "disposition": "integrated", "candidate_digest": "candidate-1",
            "target": "target-1"}
        with self.assertRaises(ContractRefusal):
            self.call(lease=None, delivery=None, entry_state="integrated")
        self.assertEqual(self.integrator.calls, [])


REPLAY_INPUT = "sha256:" + "1" * 64


class TerminalReleaseReplayCase(ExecutionCase):

    def restart(self, entry, target_id):
        basis = {"proposal_id": "proposal-1", "entry_id": "entry-1",
                 "candidate_digest":
                     self.candidates[1]["proposal"]["candidate_digest"],
                 "target": self.candidates[1]["proposal"]["target"],
                 "checkpoint_id": "checkpoint-1",
                 "verdict_id": "verdict-1"}
        integrator = ReceiptSession(PARTICIPANT, "integrate")
        integrator.integration_receipt = {
            "kind": "integration",
            "receipt_id": driver._identity("integration-receipt", basis),
            "proposal_id": "proposal-1", "actor": PARTICIPANT,
            "disposition": "integrated",
            "candidate_digest": basis["candidate_digest"],
            "target": basis["target"]}
        receipt = mock.Mock(wraps=integrator.receipt)
        integrator.receipt = receipt
        restart_port = SimpleNamespace(run=mock.Mock())
        original_identity = driver._identity

        def retained_identity(kind, account):
            if kind == "entry":
                return "entry-1"
            if kind == "lease":
                return "lease-1"
            return original_identity(kind, account)

        with mock.patch.object(
                driver, "_accepted_receipts", return_value=(
                    copy.deepcopy(self.candidates[1]["accepted"]),
                    copy.deepcopy(self.candidates[1]["proposal"]),
                    {"accepted": True})), \
                mock.patch.object(
                    driver, "resolved_account",
                    return_value=copy.deepcopy(entry["eligibility"])), \
                mock.patch.object(driver, "_identity",
                                  side_effect=retained_identity):
            replayed = driver.admit_accepted(
                self.coordinator, self.manager, self.jobs, self.authority,
                None, None, None, integrator, restart_port,
                canonical_target_id=target_id, line_id="line-1",
                proposal_id="proposal-1", policy_generation=1,
                profile=profile(), attempt_id="attempt-1",
                launch_root=os.path.join(self.launch, "attempt-1"),
                workspace_group=self.group,
                # W112029: this replay drives the RESTART tail rather than the
                # evidence gate, so the resolution is supplied and the exact
                # requirement matches it.
                required_tests=requirements(REPLAY_INPUT))
        return replayed, integrator, receipt, restart_port

    def test_restart_replays_the_settled_live_lease_tail(self):
        model = self.model()
        answered = self.integrate(model, complete=False)
        with mock.patch.object(
                execution, "release_lease",
                side_effect=RuntimeError("process died after settlement")):
            with self.assertRaises(RuntimeError):
                execution.complete_integrated(
                    self.coordinator, answered["assignment"],
                    answered["settlement"])

        target_id = answered["assignment"]["canonical_target_id"]
        entry = entries_of(self.coordinator, target_id)[0]
        held = lease_of(self.coordinator, "lease-1")
        self.assertEqual(entry["state"], "integrated")
        self.assertEqual(held["state"], "live")
        prior_calls = list(model.asked)
        replayed, integrator, receipt, restart_port = self.restart(
            entry, target_id)

        self.assertEqual(replayed["outcome"], "integrated")
        self.assertEqual(integrator.calls, [])
        receipt.assert_called_once_with("proposal-1", "integration")
        restart_port.run.assert_not_called()
        self.assertEqual(model.asked, prior_calls)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "released")
        next_model = self.model()
        next_answer = self.integrate(
            next_model, attempt_id="attempt-2", lease_id="lease-2")
        self.assertEqual(next_answer["entry"], "entry-2")
        self.assertEqual(next_model.asked, [("attempt-2", "entry-2")])

    def test_released_terminal_restart_is_read_only(self):
        model = self.model()
        answered = self.integrate(model)
        target_id = answered["assignment"]["canonical_target_id"]
        entry = entries_of(self.coordinator, target_id)[0]
        before = self.coordinator._connection.execute(
            "SELECT COUNT(*) FROM operations").fetchone()[0]

        replayed, integrator, receipt, restart_port = self.restart(
            entry, target_id)

        after = self.coordinator._connection.execute(
            "SELECT COUNT(*) FROM operations").fetchone()[0]
        self.assertEqual(replayed["outcome"], "integrated")
        self.assertEqual(integrator.calls, [])
        receipt.assert_called_once_with("proposal-1", "integration")
        restart_port.run.assert_not_called()
        self.assertEqual(model.asked, [("attempt-1", "entry-1")])
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "released")
        self.assertEqual(after, before)


# -- W103874: the proposal manifest producer ---------------------------------
#
# `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/
# finding-standalone-stage-composition/findings/finding-proposal-manifest-
# producer/`.
#
# RETENTION AND LOAD-BACK ARE THE THING BEING PROVED, so neither is mocked
# here. The input and result manifests are really retained in a real Worker
# Manager store, the proposal this composes is really retained, and
# `publish_candidate` then selects it through the real `load_manifest` rather
# than through the module patch the accepted publication cases use. What is
# supplied is only what a store cannot answer without a whole attempt
# lifecycle: the frozen-output summary row, the fixed assignment, and the
# Authority.

import pathlib                                              # noqa: E402
import tempfile                                             # noqa: E402

from baton_v12.contracts import check_no_durable_secret      # noqa: E402
from baton_v12.worker_manager import (ControlStore, load_manifest,
                                      retain_manifest)      # noqa: E402


REPOSITORY = pathlib.Path(__file__).resolve().parents[4]
VECTORS = (REPOSITORY / "work" / "records" / "2026" / "08"
           / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")

# Hex with LETTERS in it, deliberately: an all-digit name cannot tell an
# upper-case spelling apart from its own, and the case rule is one of the
# things these cases exist to hold.
PRIVATE_BASE = "a1" * 20
PRIVATE_HEAD = "b2" * 20
CLAIM = "baton.git-proposal/1"
TRANSPORT = "objects.bundle"
RECAP = "candidate: the provider changed one path and its check passed"

# W112029: one ordinary-test observation and the requirement it answers. The
# two are separate documents on purpose -- the producer OBSERVES and the
# deployment REQUIRES -- and the cases below drive every way they disagree.
TASK_ID = "w112029-ordinary"
TASK_DIGEST = "sha256:" + "7" * 64
ARGV = ["python3", "harness.py"]
ORDINARY = driver.ORDINARY_TESTS_NAMESPACE


def observation(**changed):
    held = {"task_id": TASK_ID, "task_digest": TASK_DIGEST,
            "argv": list(ARGV), "status": 0,
            "base": PRIVATE_BASE, "head": PRIVATE_HEAD}
    held.update(changed)
    return held


def requirements(input_digest, **changed):
    held = {"task_id": TASK_ID, "task_digest": TASK_DIGEST,
            "argv": list(ARGV), "input_manifest_digest": input_digest}
    held.update(changed)
    return held


def _sealed(document):
    body = {name: value for name, value in document.items()
            if name != "manifest_digest"}
    return {**body, "manifest_digest": digest(body)}


def _vector(schema):
    import json as _json
    for case in _json.loads(VECTORS.read_text(encoding="utf-8"))["valid"]:
        document = case.get("document")
        if isinstance(document, dict) and document.get("schema") == schema:
            return copy.deepcopy(document)
    raise AssertionError(f"the published vectors carry no {schema}")


class LinePublisher:
    """An Authority that answers exactly what it was asked.

    Which is what makes `publish_candidate`'s equality check meaningful over a
    manifest this producer composed: the answer is derived from the operands,
    so the case proves the producer's own `publish_receipt_digest` binds it.
    """

    participant = "baton.impl"

    def __init__(self, target):
        self.target = target
        self.calls = []
        self.recorded = None

    def canonical_target(self):
        return self.target

    def publish(self, operands):
        self.calls.append(copy.deepcopy(operands))
        self.recorded = {
            "proposal_id": operands["proposal_id"],
            "assignment_ref": copy.deepcopy(operands["expect"]),
            "result_id": operands["result_id"],
            "result_digest": operands["result_digest"],
            "candidate_digest": operands["candidate_digest"],
            "input_digest": operands["input_digest"],
            "policy_digest": operands["policy_digest"],
            "target": operands["target"]}
        return copy.deepcopy(self.recorded)

    def proposal(self, proposal_id):
        return dict(copy.deepcopy(self.recorded), decision={},
                    published_at="2026-09-07T02:00:00.000Z")


class ProducerCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-producer-")
        self.addCleanup(self._root.cleanup)
        self.store = ControlStore.open(
            os.path.join(self._root.name, "control.sqlite3"),
            incarnation="manager-1",
            clock=lambda: "2026-09-07T02:00:00.000Z")
        self.addCleanup(self.store.close)
        given = _vector("baton.worker-manifest/input")
        self.input_digest = retain_manifest(self.store, given,
                                            "inputManifest")["digest"]
        self.profile_digest = given["runtime_profile_digest"]
        self.assignment = copy.deepcopy(
            _vector("baton.worker-manifest/result")["assignment_ref"])
        self.artifact = {"artifact_id": "attempt-1:proposal",
                         "media_type": "application/octet-stream",
                         "bytes": 12,
                         "content_digest": "sha256:" + "5" * 64,
                         "locator": "file:///var/lib/baton/attempt-1/proposal"}
        # §12 rule 6: sorted, unique, and every aggregate recomputed over the
        # entries — so the fixture is a real content manifest rather than a
        # shape, which is what makes the retention below a real retention.
        entries = [{"path": "change.patch", "bytes": 4,
                    "content_digest": "sha256:" + "6" * 64},
                   {"path": TRANSPORT, "bytes": 8,
                    "content_digest": "sha256:" + "7" * 64}]
        entries.sort(key=lambda one: one["path"].encode("utf-8"))
        self.content = {"entries": entries, "entry_count": len(entries),
                        "total_bytes": sum(one["bytes"] for one in entries),
                        "tree_digest": digest(entries)}
        self.artifact["content_digest"] = self.content["tree_digest"]
        self.artifact["bytes"] = self.content["total_bytes"]
        self.claim = {"base": PRIVATE_BASE, "head": PRIVATE_HEAD,
                      "transport": TRANSPORT, "recap": RECAP}
        self.publisher = LinePublisher(PRIVATE_BASE)
        # W112029: what this producer OBSERVED and what the deployment
        # REQUIRES, defaulted to agreement so a case that is about something
        # else is not measuring this gate.
        self.observed = {}
        self.retain()
        self.required = requirements(self.input_digest)

    # -- the frozen result, really retained ---------------------------------

    def retain(self, **members):
        composed = dict(
            _vector("baton.worker-manifest/result"),
            result_id="result-attempt-1",
            input_manifest_digest=self.input_digest,
            outputs=[{"name": "proposal", "type": "git-change-proposal",
                      "status": "present",
                      "content_manifest": copy.deepcopy(self.content),
                      "artifact": copy.deepcopy(self.artifact),
                      "result_metadata": {
                          CLAIM: copy.deepcopy(self.claim),
                          ORDINARY: observation(**self.observed)}}])
        composed.update(members)
        result = _sealed(composed)
        self.result = result
        self.result_digest = retain_manifest(self.store, result,
                                             "resultManifest")["digest"]
        return self.result_digest

    def produced(self):
        with mock.patch.multiple(
                driver,
                frozen_output_of=mock.Mock(return_value={
                    "result_id": self.result["result_id"],
                    "disposition": "completed",
                    "manifest_digest": self.result_digest}),
                assignment_of=mock.Mock(return_value={
                    "authority_uuid":
                        self.assignment["work_ref"]["authority_uuid"],
                    "work_id": self.assignment["work_ref"]["work_id"],
                    "participant": self.assignment["participant"],
                    "generation": self.assignment["generation"]})):
            return driver.retain_proposal(self.store, self.publisher,
                                          attempt_id="attempt-1")

    def retained(self):
        return load_manifest(self.store, self.produced(), "proposalManifest")

    def manifests(self):
        return self.store._connection.execute(
            "SELECT COUNT(*) FROM manifests WHERE schema = ?",
            ("baton.worker-manifest/proposal",)).fetchone()[0]


class TheProducerComposesBothHalvesFromTheirOwners(ProducerCase):

    def test_the_worker_owns_its_three_facts_and_nothing_else(self):
        held = self.retained()
        self.assertEqual(held["source_base"],
                         {"algorithm": "sha1", "hex": PRIVATE_BASE})
        self.assertEqual(held["proposal_head"],
                         {"algorithm": "sha1", "hex": PRIVATE_HEAD})
        self.assertEqual(held["implementation_recap"], RECAP)
        # A WORKER CANNOT MINT CUSTODY IDENTITIES, so it offers no evidence.
        self.assertEqual(held["author_tests"], [])
        self.assertEqual(held["dossier_evidence"], [])

    def test_every_other_member_is_read_back_from_its_accepted_producer(self):
        held = self.retained()
        self.assertEqual(held["assignment_ref"], self.assignment)
        self.assertEqual(held["result_id"], "result-attempt-1")
        self.assertEqual(held["result_manifest_digest"], self.result_digest)
        self.assertEqual(held["input_manifest_digest"], self.input_digest)
        self.assertEqual(held["policy_digest"], self.result["policy_digest"])
        # FROM THE RETAINED INPUT MANIFEST, which is the only place it lives.
        self.assertEqual(held["runtime_profile_digest"], self.profile_digest)
        # FROM THE MANAGER'S OWN MEASUREMENT of the proposal output.
        self.assertEqual(held["output_digest"], self.content["tree_digest"])
        self.assertEqual(held["proposal_artifact"], self.artifact)
        # FROM THE AUTHORITY, and its namespace from the object-name width.
        self.assertEqual(held["target_revision"],
                         {"algorithm": "sha1", "hex": PRIVATE_BASE})

    def test_the_created_instant_is_the_frozen_one_and_not_a_clock(self):
        """Retention is keyed by the digest of the bytes, so a clock read here
        would retain a differently keyed account of one result on every call
        and the exact-replay guarantee would be silently false."""
        held = self.retained()
        self.assertEqual(held["created_at"],
                         self.result["manager_observed_at"])
        self.assertEqual(held["manifest_id"],
                         driver._identity("proposal-manifest", {
                             "assignment_ref": self.assignment,
                             "result_id": self.result["result_id"],
                             "result_digest": self.result_digest,
                             "candidate_digest": PRIVATE_HEAD}))

    def test_a_result_id_at_its_own_ceiling_is_still_proposable(self):
        """A result id and a manifest id are both `opaqueId`, bounded at 160.

        So a manifest id COMPOSED BY PREFIX is longer than its own type allows
        for every result id from 152 characters up, and the producer refused
        perfectly valid frozen results at retention. The identity is derived
        from the account instead, which makes its length this module's rather
        than its input's.
        """
        ceiling = 160
        for width in (ceiling - 9, ceiling - 8, ceiling - 1, ceiling):
            with self.subTest(width=width):
                self.retain(result_id="r" * width)
                held = self.retained()
                self.assertEqual(held["result_id"], "r" * width)
                self.assertLessEqual(len(held["manifest_id"]), ceiling)
                self.assertLessEqual(len(held["proposal_id"]), ceiling)

    def test_distinct_results_never_share_a_derived_identity(self):
        """Bounding an identity by truncating it is how two distinct results
        become one name, so nothing here truncates."""
        seen = set()
        for width in (159, 160):
            for tail in ("a", "b"):
                self.retain(result_id=tail + "r" * (width - 1))
                held = self.retained()
                seen.add((held["manifest_id"], held["proposal_id"]))
        self.assertEqual(len(seen), 4)

    def test_the_document_really_loads_back_under_its_own_digest(self):
        answered = self.produced()
        held = load_manifest(self.store, answered, "proposalManifest")
        self.assertIsNotNone(held)
        self.assertEqual(held["manifest_digest"], answered)
        self.assertEqual(held["schema"], "baton.worker-manifest/proposal")

    def test_exact_replay_returns_one_retained_account(self):
        first = self.produced()
        second = self.produced()
        self.assertEqual(first, second)
        self.assertEqual(self.manifests(), 1)

    def test_no_secret_and_no_output_byte_reaches_the_retained_document(self):
        held = self.retained()
        check_no_durable_secret(held, what="the retained proposal")
        # ONLY DIGESTS AND IDENTITIES. The one locator is the manager's own
        # custody reference, carried through from the frozen result.
        self.assertEqual(
            [value for value in held.values() if isinstance(value, str)
             and "not-a-credential" in value], [])
        self.assertEqual(held["proposal_artifact"]["locator"],
                         self.artifact["locator"])


class TheProducerFeedsThePublicationDriver(ProducerCase):

    def test_the_retained_digest_publishes_end_to_end(self):
        answered = self.produced()
        with mock.patch.multiple(
                driver,
                frozen_output_of=mock.Mock(return_value={
                    "result_id": self.result["result_id"],
                    "disposition": "completed",
                    "manifest_digest": self.result_digest}),
                assignment_of=mock.Mock(return_value={
                    "authority_uuid":
                        self.assignment["work_ref"]["authority_uuid"],
                    "work_id": self.assignment["work_ref"]["work_id"],
                    "participant": self.assignment["participant"],
                    "generation": self.assignment["generation"]})):
            recorded = driver.publish_candidate(
                self.store, self.publisher, attempt_id="attempt-1",
                proposal_manifest_digest=answered)
        # THE HEAD THE WORKER CLAIMED IS THE CANDIDATE THE AUTHORITY GOT.
        self.assertEqual(self.publisher.calls[0]["candidate_digest"],
                         PRIVATE_HEAD)
        self.assertEqual(self.publisher.calls[0]["target"], PRIVATE_BASE)
        self.assertEqual(recorded["candidate_digest"], PRIVATE_HEAD)
        self.assertEqual(recorded["result_digest"], self.result_digest)
        # AND ITS OPERATION IDENTITY BINDS THOSE EXACT OPERANDS.
        held = load_manifest(self.store, answered, "proposalManifest")
        self.assertEqual(
            held["publish_operation"]["operation_id"],
            self.publisher.calls[0]["operation_id"])


class TheProducerRefusesWhatItCannotAccountFor(ProducerCase):

    def refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.produced()
        self.assertEqual(self.manifests(), 0)
        return caught.exception

    def test_a_missing_claim_refuses_rather_than_being_invented(self):
        self.retain(outputs=[dict(self.result["outputs"][0],
                                  result_metadata={})])
        self.assertIn(CLAIM, self.refuses().message)

    def test_a_wrong_namespace_claim_is_not_read(self):
        self.retain(outputs=[dict(self.result["outputs"][0],
                                  result_metadata={"baton.other-proposal/1":
                                                   dict(self.claim)})])
        self.assertIn(CLAIM, self.refuses().message)

    def test_an_extra_or_missing_claim_member_refuses(self):
        for metadata in (dict(self.claim, artifact_id="attempt-1:proposal"),
                         {name: value for name, value in self.claim.items()
                          if name != "head"}):
            with self.subTest(members=sorted(metadata)):
                self.retain(outputs=[dict(self.result["outputs"][0],
                                          result_metadata={CLAIM: metadata})])
                self.refuses()

    def test_a_malformed_object_name_refuses(self):
        for spelling in (PRIVATE_HEAD[:39], PRIVATE_HEAD.upper(),
                         PRIVATE_HEAD + "0", "", "z" * 40):
            with self.subTest(head=spelling):
                self.claim = dict(self.claim, head=spelling)
                self.retain()
                self.refuses()

    def test_a_transport_the_manager_did_not_measure_refuses(self):
        self.claim = dict(self.claim, transport="elsewhere.bundle")
        self.retain()
        self.assertIn("measured nothing there", self.refuses().message)

    def test_target_drift_retains_nothing_and_publishes_nothing(self):
        self.publisher.target = "3" * 40
        self.assertIn("offered against the revision it was built from",
                      self.refuses().message)
        self.assertEqual(self.publisher.calls, [])

    def test_a_head_and_target_in_different_namespaces_refuse(self):
        """A sha1 name under a sha256 repository is a different object, not a
        shorter digest."""
        self.claim = dict(self.claim, head="c3" * 32)
        self.retain()
        self.assertIn("different object namespaces", self.refuses().message)

    def test_zero_or_two_proposal_outputs_refuse(self):
        for outputs in ([], [self.result["outputs"][0],
                             dict(self.result["outputs"][0], name="second")]):
            with self.subTest(outputs=len(outputs)):
                self.retain(outputs=copy.deepcopy(outputs))
                self.refuses()

    def test_a_non_proposal_or_absent_output_refuses(self):
        self.retain(outputs=[dict(self.result["outputs"][0],
                                  type="directory-result")])
        self.refuses()
        self.retain(outputs=[{"name": "proposal",
                              "type": "git-change-proposal",
                              "status": "missing-optional",
                              "content_manifest": None, "artifact": None,
                              "result_metadata": {CLAIM: dict(self.claim)}}])
        self.refuses()

    def test_a_result_that_is_not_this_attempts_refuses(self):
        self.retain(assignment_ref=dict(self.assignment, generation=2))
        self.assertIn("one assignment", self.refuses().message)

    def test_an_unfinished_attempt_has_nothing_to_propose(self):
        with mock.patch.multiple(
                driver,
                frozen_output_of=mock.Mock(return_value=None),
                assignment_of=mock.DEFAULT):
            with self.assertRaises(ContractRefusal):
                driver.retain_proposal(self.store, self.publisher,
                                       attempt_id="attempt-1")
        self.assertEqual(self.manifests(), 0)


if __name__ == "__main__":
    unittest.main()


class TheAdmissionNeedsActualOrdinaryTestEvidence(ProducerCase):
    """W112029: the receipt that used to say `passed` for everything.

    `_accepted_receipts` published `observation="passed"` unconditionally for
    every accepted checkpoint. An accepted TECHNICAL REVIEW is a judgement
    about a change; it is not a statement that the required commands ran and
    exited zero, and publishing one as the other made the strongest receipt in
    the protocol the least evidenced.

    These drive the real reader over the really retained result this fixture
    already builds -- no mocked observation anywhere.
    """

    def setUp(self):
        super().setUp()
        self.accepted = {"line_id": "line-1", "checkpoint_id": "cp-1",
                         "verdict_id": "verdict-1",
                         "checkpoint_digest": "sha256:" + "c" * 64,
                         "head": PRIVATE_HEAD}
        self.proposal = {
            "proposal_id": "proposal-1",
            "assignment_ref": copy.deepcopy(self.assignment),
            "result_id": "result-attempt-1",
            "result_digest": self.result_digest,
            "candidate_digest": PRIVATE_HEAD,
            "input_digest": self.input_digest,
            "policy_digest": self.result["policy_digest"],
            "target": PRIVATE_BASE,
            "decision": {},
            "published_at": "2026-09-07T02:00:00.000Z"}
        self.authority = SimpleNamespace(
            # THE LIVE RETAINED DIGEST, because a case that re-retains its
            # result changes it and a proposal frozen at setUp would then be
            # measuring staleness rather than its own subject.
            proposal=lambda _id: dict(self.proposal,
                                      result_digest=self.result_digest),
            policy_generation=lambda: 3)

    def evidence(self):
        """The RETAINED result is real; the frozen summary row and the
        checkpoint's writer are the two facts this fixture has no runtime to
        produce, and they are supplied exactly as `produced()` already supplies
        them for the publication producer beside this."""
        with mock.patch.object(driver, "integration_checkpoint",
                               return_value=copy.deepcopy(self.accepted)), \
                mock.patch.object(driver, "checkpoint_of",
                                  return_value={"writer_id": "writer-1"}), \
                mock.patch.object(driver, "writer_of",
                                  return_value={
                                      "runtime_attempt_id": "attempt-1"}), \
                mock.patch.object(driver, "frozen_output_of",
                                  return_value={
                                      "result_id": self.result["result_id"],
                                      "disposition": "completed",
                                      "manifest_digest": self.result_digest}), \
                mock.patch.object(driver, "_assignment",
                                  return_value=self.assignment):
            return driver.ordinary_test_evidence(
                self.store, self.authority, line_id="line-1",
                proposal_id="proposal-1")

    def refused(self, action, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            action(*operands, **named)
        return caught.exception

    # -- resolution ----------------------------------------------------------

    def test_the_producers_own_observation_is_resolved_from_custody(self):
        held = self.evidence()
        self.assertEqual(held["attempt_id"], "attempt-1")
        self.assertEqual(held["observation"], observation())
        self.assertEqual(held["result_digest"], self.result_digest)
        self.assertEqual(held["input_manifest_digest"], self.input_digest)

    def test_a_result_with_no_observation_refuses(self):
        composed = copy.deepcopy(self.result)
        composed["outputs"][0]["result_metadata"] = {CLAIM: self.claim}
        self.retain(outputs=composed["outputs"])
        caught = self.refused(self.evidence)
        self.assertIn(ORDINARY, caught.message)

    def test_an_observation_over_another_candidate_refuses(self):
        self.observed = {"head": "f" * 40}
        self.retain()
        caught = self.refused(self.evidence)
        self.assertIn("another candidate", caught.message)

    def test_a_checkpoint_naming_another_head_refuses(self):
        self.accepted["head"] = "e" * 40
        self.refused(self.evidence)

    def test_a_proposal_naming_another_result_refuses(self):
        self.proposal["result_id"] = "result-other"
        caught = self.refused(self.evidence)
        self.assertIn("different results", caught.message)

    def test_a_proposal_naming_another_input_refuses(self):
        self.proposal["input_digest"] = "sha256:" + "9" * 64
        caught = self.refused(self.evidence)
        self.assertIn("input or policy", caught.message)

    # -- the decision --------------------------------------------------------

    def test_an_actual_zero_for_the_exact_requirement_passes(self):
        self.assertEqual(
            driver._ordinary_tests_passed(self.evidence(), self.required),
            self.required)

    def test_a_nonzero_status_is_refused_as_a_failing_requirement(self):
        self.observed = {"status": 1}
        self.retain()
        caught = self.refused(driver._ordinary_tests_passed, self.evidence(),
                              self.required)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertIn("exited 1", caught.message)
        self.assertIn("not a substitute", caught.message)

    def test_an_unrun_command_is_a_different_refusal_from_a_failing_one(self):
        """No evidence and evidence of failure are not the same answer, and
        reporting one as the other sends an operator to the wrong place."""
        self.observed = {"status": None}
        self.retain()
        caught = self.refused(driver._ordinary_tests_passed, self.evidence(),
                              self.required)
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("did not run", caught.message)

    def test_a_status_zero_for_another_command_proves_nothing(self):
        for name, changed in (("task_id", {"task_id": "another-task"}),
                              ("task_digest",
                               {"task_digest": "sha256:" + "0" * 64}),
                              ("argv", {"argv": ["python3", "other.py"]})):
            with self.subTest(member=name):
                self.observed = changed
                self.retain()
                self.refused(driver._ordinary_tests_passed, self.evidence(),
                             self.required)

    def test_requirements_selected_for_another_attempt_refuse(self):
        caught = self.refused(
            driver._ordinary_tests_passed, self.evidence(),
            requirements("sha256:" + "4" * 64))
        self.assertIn("another attempt", caught.message)

    def test_a_requirement_may_never_carry_an_observation(self):
        """There is no `status` in the selection and there never will be: a
        caller that could supply the observation would be certifying its own
        candidate, which is the exact defect the unconditional receipt was."""
        self.assertNotIn("status", driver.REQUIRED_TESTS_MEMBERS)
        self.refused(driver._owned_requirements,
                     dict(self.required, status=0))

    # -- the receipt ---------------------------------------------------------

    def test_the_receipt_identity_binds_the_evidence_and_the_requirement(self):
        first = driver._identity("verification-operation", {
            "workflow": driver.ORDINARY_TESTS_WORKFLOW,
            "ordinary_tests": digest(observation()),
            "required_tests": digest(self.required)})
        second = driver._identity("verification-operation", {
            "workflow": driver.ORDINARY_TESTS_WORKFLOW,
            "ordinary_tests": digest(observation(status=0)),
            "required_tests": digest(self.required)})
        third = driver._identity("verification-operation", {
            "workflow": driver.ORDINARY_TESTS_WORKFLOW,
            "ordinary_tests": digest(observation(task_id="other")),
            "required_tests": digest(self.required)})
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_the_workflow_marker_is_not_a_certification_word(self):
        """It says what actually happened: the author's own container ran the
        required command. It is explicitly not a clean-verification claim."""
        self.assertIn("ordinary-tests", driver.ORDINARY_TESTS_WORKFLOW)
        for word in ("clean", "certified", "verified"):
            self.assertNotIn(word, driver.ORDINARY_TESTS_WORKFLOW)
