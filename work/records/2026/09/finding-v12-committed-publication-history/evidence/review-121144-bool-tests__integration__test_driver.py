"""W103077: replay-safe proposal publication and integration driving."""

import contextlib
import copy
import inspect
import json
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
        # W120763: A REAL JOURNAL, because publication now commits a local
        # record before it reports success. Every manifest and assignment read
        # this case makes is still replaced below -- what the store is here for
        # is the one operation `publish_candidate` writes, and a stand-in for
        # that would be this case deciding whether effectively-once holds.
        import os
        import tempfile
        from baton_v12.worker_manager import ControlStore
        root = tempfile.TemporaryDirectory(prefix="v12-publication-")
        self.addCleanup(root.cleanup)
        self.manager = ControlStore.open(
            os.path.join(root.name, "control.sqlite3"),
            incarnation="manager-1", clock=lambda: "2026-09-08T00:00:00.000Z")
        self.addCleanup(self.manager.close)
        self.root = root.name
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


class ContinuationCase(unittest.TestCase):
    """W110774: the normal asynchronous continuation of a started integration.

    ADDITIVE, and deliberately over the SAME fixture as admission: what this
    operation must not do is anything admission does, so proving that against
    a second world would prove it about a second set of owners.

    COMPOSED RATHER THAN SUBCLASSED. A `TestCase` subclass re-runs every case
    of its parent under a second name -- and under THIS class's `call`, which
    drives a different operation entirely -- so the fixture is reused by
    calling admission's own `setUp` and nothing else is inherited.
    """

    def setUp(self):
        DriverCase.setUp(self)

    def live(self, **changed):
        held = {"lease_id": "lease-1", "state": "live", "fence": 1,
                "canonical_target_id": "target-1", "entry_id": self.entry_id,
                "attempt_id": "attempt-1",
                "integrator_participant": "baton.integrator"}
        held.update(changed)
        return held

    def call(self, *, lease=..., delivery=..., entry_state="queued",
             outcome="integrated", witness="destroyed", observed="ready",
             published={"owned": True}, target={"state": "open"}):
        """One continuation tick over the patched owners.

        The default is the ordinary one this operation exists for: a live
        grant, a delivery this execution published, an observed-stopped
        runtime and a model claim of `integrated`.
        """
        self.entry["state"] = entry_state
        held = self.live() if lease is ... else lease
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
                admit_candidate=mock.Mock(
                    side_effect=AssertionError("a continuation admits "
                                               "nothing")),
                entries_of=mock.Mock(return_value=[self.entry]),
                lease_of=mock.Mock(return_value=held),
                target_of=mock.Mock(return_value=target),
                _existing_assignment=mock.Mock(return_value={"owned": True}),
                ) as patched, \
                mock.patch.object(driver.runtime, "adopt_delivery",
                                  return_value=object() if delivery is ...
                                  else delivery), \
                mock.patch.object(
                    driver.execution, "integrate_next",
                    side_effect=AssertionError(
                        "a continuation never drives an executor")) as start, \
                mock.patch.object(driver.runtime, "compose_assignment",
                                  return_value={"owned": True}), \
                mock.patch.object(driver.runtime, "published_assignment",
                                  return_value=published), \
                mock.patch.object(driver.runtime, "prior_runtime_witness",
                                  return_value={"execution_runtime":
                                                witness}), \
                mock.patch.object(driver.runtime, "observed_delivery",
                                  return_value={"state": observed}), \
                mock.patch.object(driver.runtime,
                                  "publish_assignment") as publish, \
                mock.patch.object(driver.runtime,
                                  "materialize_delivery") as materialize, \
                mock.patch.object(driver, "live_grant") as live, \
                mock.patch.object(driver.execution, "settle_observed",
                                  return_value=answer) as settle, \
                mock.patch.object(driver.execution,
                                  "complete_integrated") as complete, \
                mock.patch.object(driver.recovery, "hold_interrupted",
                                  return_value={"state": "operator-held"}
                                  ) as hold, \
                mock.patch.object(driver.recovery, "held_status",
                                  return_value={"state": "blocked"}):
            result = driver.continue_accepted(
                self.store, self.manager, self.jobs, self.authority,
                self.verify, self.review, self.approve, self.integrator,
                canonical_target_id="target-1", line_id="line-1",
                proposal_id="proposal-1", policy_generation=3,
                profile=self.profile, attempt_id="attempt-1",
                launch_root="/launch", workspace_group=object(),
                required_tests=self.required)
            return (result, patched, start, publish, materialize, live,
                    settle, hold, complete)

    def refused(self, **changed):
        with self.assertRaises(ContractRefusal) as caught:
            self.call(**changed)
        return caught.exception

    def test_the_operation_has_no_operand_that_could_start_a_runtime(self):
        """THE STRONGEST FORM OF `it never starts a worker`: there is no port
        here to ask, so no branch of this operation can reach one."""
        import inspect
        taken = inspect.signature(driver.continue_accepted).parameters
        self.assertNotIn("port", taken)
        self.assertEqual(sorted(set(inspect.signature(
            driver.admit_accepted).parameters) - set(taken)), ["port"])

    def test_a_stopped_runtime_completes_through_the_receipt_then_the_store(
            self):
        """The ordinary ending, in the order the coordinator requires: the
        Authority receipt is written and read back while the live lease still
        excludes every later writer, and only then does the store settle."""
        answer, _, start, publish, materialize, _, settle, hold, complete = \
            self.call()
        self.assertEqual(answer["outcome"], "integrated")
        settle.assert_called_once()
        complete.assert_called_once()
        hold.assert_not_called()
        publish.assert_not_called()
        materialize.assert_not_called()
        self.assertIsNotNone(answer["authority_receipt"])
        # EXACTLY ONE Authority act, over this proposal.
        self.assertEqual(len(self.integrator.calls), 1)
        self.assertEqual(self.integrator.calls[0]["proposal_id"],
                         "proposal-1")

    def test_a_running_writer_is_pending_and_settles_nothing(self):
        """A RESULT WHILE THE WRITER CAN STILL WRITE IS NOT AN ENDING. The
        model claims `integrated` and the manager says the runtime is still
        up, so this answers `running`, releases nothing and writes no
        receipt."""
        for state in ("start-requested", "running", "cancel-requested",
                      "stopping"):
            with self.subTest(runtime=state):
                self.integrator.calls.clear()
                answer, _, _, _, _, live, settle, hold, complete = self.call(
                    witness=state, observed="ready")
                self.assertEqual(answer["outcome"], "running")
                self.assertEqual(answer["observed"], {"state": "ready"})
                settle.assert_not_called()
                complete.assert_not_called()
                hold.assert_not_called()
                live.assert_not_called()
                self.assertIsNone(answer["authority_receipt"])
                self.assertEqual(self.integrator.calls, [])

    def test_an_unaccountable_runtime_takes_the_accepted_interrupted_hold(
            self):
        answer, _, _, _, _, _, settle, hold, complete = self.call(
            witness="uncertain")
        self.assertEqual(answer["outcome"], "held")
        self.assertEqual(answer["observed"], {"state": "operator-held"})
        hold.assert_called_once()
        settle.assert_not_called()
        complete.assert_not_called()

    def test_an_unstarted_attempt_is_an_inconsistency_and_not_a_start(self):
        caught = self.refused(witness="not-started")
        self.assertIn("continues an integration that is already running",
                      caught.message)

    def test_a_continuation_without_a_lease_or_a_delivery_refuses(self):
        self.assertIn("no started integration to continue",
                      self.refused(lease=None).message)
        self.assertIn("nothing was ever started",
                      self.refused(delivery=None).message)

    def test_the_published_assignment_must_be_the_one_the_grant_composes(self):
        self.assertIn("carries no published assignment",
                      self.refused(published=None).message)
        caught = self.refused(published={"owned": "somebody else's"})
        self.assertIn("not the one the grant this target holds composes",
                      caught.message)

    def test_a_blocked_target_reports_its_hold_and_advances_nothing(self):
        answer, _, _, _, _, _, settle, _, complete = self.call(
            target={"state": "blocked"})
        self.assertEqual(answer["outcome"], "held")
        self.assertEqual(answer["observed"], {"state": "blocked"})
        settle.assert_not_called()
        complete.assert_not_called()

    def test_a_settled_entry_replays_its_terminal_path_and_nothing_else(self):
        """Repeated ticks after completion cannot duplicate a receipt, a
        settlement or a release: the entry is terminal, so the same terminal
        owner admission uses answers, reading the existing receipt."""
        basis = {"proposal_id": "proposal-1", "entry_id": self.entry_id,
                 "candidate_digest": "candidate-1", "target": "target-1",
                 "checkpoint_id": "cp-1", "verdict_id": "verdict-1"}
        self.integrator.integration_receipt = {
            "kind": "integration",
            "receipt_id": driver._identity("integration-receipt", basis),
            "proposal_id": "proposal-1", "actor": "baton.integrator",
            "disposition": "integrated", "candidate_digest": "candidate-1",
            "target": "target-1"}
        answer, _, _, _, _, _, settle, _, complete = self.call(
            lease=self.live(state="released"), entry_state="integrated")
        self.assertEqual(answer["outcome"], "integrated")
        self.assertEqual(self.integrator.calls, [])
        settle.assert_not_called()
        complete.assert_not_called()

    def test_an_authority_refusal_holds_before_coordinator_completion(self):
        """The same ending admission composes, through the same owner: a
        receipt that cannot be written or read back never reaches the store."""
        self.integrator.failure = AuthorityRefusal("completion unavailable")
        answer, _, _, _, _, _, _, hold, complete = self.call()
        self.assertEqual(answer["outcome"], "held")
        hold.assert_called_once()
        complete.assert_not_called()
        self.assertIsNone(answer["authority_receipt"])


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
        # THE SHAPE `integration_checkpoint` ACTUALLY ANSWERS. Review
        # 2026-09-07T18-00-22Z [P1]: the first version invented a top-level
        # `head`, which is exactly why a reader that read one passed here and
        # raised `KeyError` against the real owner. The objects live in
        # `evidence`.
        self.accepted = {"line_id": "line-1", "checkpoint_id": "cp-1",
                         "verdict_id": "verdict-1",
                         "checkpoint_digest": "sha256:" + "c" * 64,
                         "evidence": {"profile": "git",
                                      "base": PRIVATE_BASE,
                                      "head": PRIVATE_HEAD,
                                      "tree": "c3" * 20, "paths": ["a.py"],
                                      "path_set_digest": digest(["a.py"]),
                                      "reference":
                                          "refs/baton/checkpoints/line-1/1"}}
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
        self.accepted["evidence"]["head"] = "e" * 40
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


class TheReceiptBoundaryRefusesBeforeItWritesAnything(ProducerCase):
    """W112029 review [P1]: four substitutions reached three real receipts.

    `ordinary_test_evidence` compared the RESULT's assignment to the producer's
    and never the PROPOSAL's, and never compared the proposal's target with the
    base its producer built on. A proposal naming another generation,
    participant or Work -- or offered against another revision -- therefore
    reached `_accepted_receipts` and had verification, review and approval
    written for it. `resolved_account` makes those comparisons three steps
    later, after immutable receipts exist, and a later admission refusal cannot
    retract one.

    These drive the ACTUAL `_accepted_receipts` with recorded external sessions
    and assert zero calls to all three.
    """

    def setUp(self):
        super().setUp()
        self.accepted = {"line_id": "line-1", "checkpoint_id": "cp-1",
                         "verdict_id": "verdict-1",
                         "checkpoint_digest": "sha256:" + "c" * 64,
                         "evidence": {"profile": "git",
                                      "base": PRIVATE_BASE,
                                      "head": PRIVATE_HEAD,
                                      "tree": "c3" * 20, "paths": ["a.py"],
                                      "path_set_digest": digest(["a.py"]),
                                      "reference":
                                          "refs/baton/checkpoints/line-1/1"}}
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
        self.verify = ReceiptSession("baton.verify", "verify")
        self.review = ReceiptSession("baton.review", "review")
        self.approve = ReceiptSession("baton.approve", "approve")
        self.authority = SimpleNamespace(
            proposal=lambda _id: dict(self.proposal,
                                      result_digest=self.result_digest),
            policy_generation=lambda: 3)

    def receipts(self):
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
            return driver._accepted_receipts(
                self.store, self.authority, self.verify, self.review,
                self.approve, line_id="line-1", proposal_id="proposal-1",
                policy_generation=3,
                required_tests=requirements(self.input_digest))

    def assertNoReceiptWasWritten(self):
        for session in (self.verify, self.review, self.approve):
            self.assertEqual(session.calls, [])

    def test_the_unchanged_control_writes_exactly_three_receipts(self):
        self.receipts()
        for session in (self.verify, self.review, self.approve):
            self.assertEqual(len(session.calls), 1)
        self.assertEqual(self.verify.calls[0]["observation"], "passed")

    def test_a_proposal_naming_another_generation_writes_nothing(self):
        self.proposal["assignment_ref"] = dict(
            copy.deepcopy(self.assignment), generation=9)
        with self.assertRaises(ContractRefusal) as caught:
            self.receipts()
        self.assertIn("the attempt that made the candidate",
                      caught.exception.message)
        self.assertNoReceiptWasWritten()

    def test_a_proposal_naming_another_participant_writes_nothing(self):
        self.proposal["assignment_ref"] = dict(
            copy.deepcopy(self.assignment), participant="baton.somebody")
        with self.assertRaises(ContractRefusal):
            self.receipts()
        self.assertNoReceiptWasWritten()

    def test_a_proposal_naming_another_work_writes_nothing(self):
        held = copy.deepcopy(self.assignment)
        held["work_ref"] = dict(held["work_ref"], work_id="01234567-W9")
        self.proposal["assignment_ref"] = held
        with self.assertRaises(ContractRefusal):
            self.receipts()
        self.assertNoReceiptWasWritten()

    def test_a_proposal_offered_against_another_revision_writes_nothing(self):
        self.proposal["target"] = "d4" * 20
        with self.assertRaises(ContractRefusal) as caught:
            self.receipts()
        self.assertIn("the revision the candidate was made from",
                      caught.exception.message)
        self.assertNoReceiptWasWritten()

    def test_a_checkpoint_recording_another_base_writes_nothing(self):
        self.accepted["evidence"]["base"] = "e5" * 20
        with self.assertRaises(ContractRefusal):
            self.receipts()
        self.assertNoReceiptWasWritten()

    def test_a_failing_required_command_writes_nothing(self):
        self.observed = {"status": 1}
        self.retain()
        with self.assertRaises(ContractRefusal) as caught:
            self.receipts()
        self.assertEqual(caught.exception.category, "policy")
        self.assertNoReceiptWasWritten()

    def test_an_unrun_required_command_writes_nothing(self):
        self.observed = {"status": None}
        self.retain()
        with self.assertRaises(ContractRefusal) as caught:
            self.receipts()
        self.assertIn("did not run", caught.exception.message)
        self.assertNoReceiptWasWritten()

    def test_a_mismatched_requirement_writes_nothing(self):
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
            with self.assertRaises(ContractRefusal):
                driver._accepted_receipts(
                    self.store, self.authority, self.verify, self.review,
                    self.approve, line_id="line-1", proposal_id="proposal-1",
                    policy_generation=3,
                    required_tests=requirements(self.input_digest,
                                                argv=["python3", "other.py"]))
        self.assertNoReceiptWasWritten()

    # -- the identity an operator actually reads -----------------------------

    def test_the_emitted_verification_identities_carry_the_marker(self):
        """Review [P2]: the marker was hashed into the basis and therefore
        invisible in the opaque id, while the emitted prefix stayed the generic
        one whatever the evidence was."""
        self.receipts()
        emitted = self.verify.calls[0]
        for member in ("verification_id", "operation_id"):
            with self.subTest(member=member):
                self.assertTrue(
                    emitted[member].startswith(
                        "integration-driver."
                        + driver.ORDINARY_TESTS_PREFIX + "-"),
                    emitted[member])
        # AND THE OTHER TWO ARE UNTOUCHED: what changed is which evidence a
        # VERIFICATION receipt rests on.
        self.assertIn("review-receipt", self.review.calls[0]["review_id"])
        self.assertIn("approval-receipt",
                      self.approve.calls[0]["approval_id"])

    def test_the_marker_is_not_a_certification_word(self):
        for word in ("clean", "certified", "verified"):
            self.assertNotIn(word, driver.ORDINARY_TESTS_PREFIX)

    def test_a_different_observation_changes_the_emitted_identity(self):
        self.receipts()
        first = self.verify.calls[0]["operation_id"]
        self.observed = {"task_id": "another-task"}
        self.retain()
        with self.assertRaises(ContractRefusal):
            self.receipts()
        # The refusal is the requirement mismatch; what this asserts is that
        # the identity is derived from the evidence rather than fixed.
        self.observed = {}
        self.retain()
        self.verify.calls.clear()
        self.receipts()
        self.assertEqual(self.verify.calls[0]["operation_id"], first)


class TheReaderConsumesTheOwnersActualAnswer(unittest.TestCase):
    """W112029 review [P1]: the reader read a shape the owner never returns.

    `integration_checkpoint` answers `line_id`, `checkpoint_id`, `verdict_id`,
    `checkpoint_digest` and `evidence` -- with the objects INSIDE `evidence` --
    and the first version of this consumer read a top-level `head`. It raised
    `KeyError` the moment it met the real owner, and my own fixture hid that,
    because the document it mocked had a shape nothing produces.

    SO THIS CASE USES THE OWNER. It builds a real line, writer, checkpoint,
    reviewer and accepted verdict through the existing accepted fixture --
    imported and read, never edited -- and asserts the consumer's expectations
    against the document `integration_checkpoint` actually answers. A mock is
    what let the defect through, so a mock cannot be what proves it fixed.
    """

    def setUp(self):
        """COMPOSED, NOT SUBCLASSED. Inheriting a live `TestCase` re-runs every
        one of its own cases under a second name -- a defect I introduced once
        already in this campaign -- so the accepted fixture is DRIVEN here
        instead: its `setUp` and cleanups are run explicitly and its helpers
        are called on the instance. The file itself is imported and read,
        never edited.
        """
        # THE IMPORT IS INSIDE THE METHOD. A `TestCase` subclass bound at
        # module level is collected by the loader, so importing the accepted
        # fixture by name at the top would silently re-run its whole suite
        # under this module -- the same inflation, arriving through the import
        # rather than through inheritance.
        from tests.manager.test_review_cycles import ReviewCycles

        self.owner = ReviewCycles("run")
        self.owner.setUp()
        self.addCleanup(self.owner.doCleanups)
        self.addCleanup(self.owner.tearDown)
        self.store = self.owner.store

    def accepted_checkpoint(self):
        from baton_v12.worker_manager import (integration_checkpoint,
                                              record_verdict)
        line = self.owner.line()
        writer = self.owner.writer(line["line_id"], 1)
        checkpoint = self.owner.freeze(writer, 1)
        review = self.owner.review(checkpoint["checkpoint_id"], 1)
        self.owner.complete("review-attempt-1", review=True)
        record_verdict(self.store, attachment_id=review["attachment_id"],
                       disposition="accepted", profile=self.owner.profile,
                       port=self.owner.port("baton.review"))
        return integration_checkpoint(self.store, line["line_id"])

    def test_the_owner_answers_its_objects_inside_evidence(self):
        held = self.accepted_checkpoint()
        self.assertIsNotNone(held)
        self.assertEqual(sorted(held),
                         ["checkpoint_digest", "checkpoint_id", "evidence",
                          "line_id", "verdict_id"])
        # THE TWO MEMBERS THE CONSUMER READS, where the owner actually puts
        # them -- and NOT at the top level, which is the defect restated as an
        # assertion.
        for member in ("base", "head"):
            with self.subTest(member=member):
                self.assertIn(member, held["evidence"])
                self.assertNotIn(member, held)

    def test_the_consumer_reads_that_document_without_raising(self):
        """Reach the corrected read with an actual retained producer."""
        world = _OrdinaryAdmissionWorld(self)
        held = driver.integration_checkpoint(world.manager, world.line_id)
        self.assertIn("head", held["evidence"])
        self.assertNotIn("head", held)
        evidence = world.evidence()
        self.assertEqual(evidence["observation"], world.observation)
        self.assertEqual(evidence["observation"]["head"], held["evidence"]["head"])
        self.assertEqual(evidence["observation"]["base"], held["evidence"]["base"])


class _OrdinaryAdmissionWorld:
    """Actual command and custody owners, real Authority receipts/admission.

    Existing fixtures supply the model process, engine and manager-assignment
    transport. The checkpoint profile holds object names read from the actual
    worker repository. Publication and all policy receipts use minted Authority
    sessions; no producer, custody, eligibility or admission reader is replaced.
    """

    def __init__(self, case, *, command_status=0, unrun=False):
        import json
        import pathlib
        import shutil
        import tempfile
        from tests.manager import test_claude_agent as worker_fixture
        from tests.job_manager import test_review_driver as lifecycle
        from baton_v12.authority import Authority, V12
        from baton_v12.worker_manager import (authorize_cleanup, decide_retention, freeze_checkpoint,
            observe, reconcile_runtime, request_freeze, request_intake)
        from baton_v12.integration import IntegrationStore, activate_target
        from baton_v12.job_manager import JobStore, submit
        from .fixtures import target

        self.case = case
        worker = worker_fixture.TheOrdinaryTestObservationIsTheActualOne()
        case.addCleanup(worker.doCleanups)
        worker.setUp()
        self.worker = worker
        task_bytes = pathlib.Path(worker.inputs, worker_fixture.claude_agent.TASK_DOCUMENT).read_bytes()
        task = json.loads(task_bytes)
        edit = "print('actual admission command')\n" if command_status == 0 else f"raise SystemExit({command_status})\n"
        self.command_runs = []
        actual_runner = worker.really
        def tracked_runner(**operands):
            actual = actual_runner(**operands)
            def run(argv, **options):
                answer = actual(argv, **options)
                if list(argv) == task["verification"]:
                    self.command_runs.append((list(argv), answer.returncode))
                return answer
            return run
        worker.really = tracked_runner
        self.answered = worker.ran(edits={"harness.py": edit}, status=1 if unrun else 0)
        case.assertEqual(self.command_runs, [] if unrun else [(task["verification"], command_status)])
        self.observation = worker.observation(self.answered)
        case.assertEqual(self.observation["status"], None if unrun else command_status)
        case.assertEqual(self.observation["argv"], task["verification"])
        from hashlib import sha256
        case.assertEqual(self.observation["task_digest"], "sha256:" + sha256(task_bytes).hexdigest())

        owner = lifecycle.TheWorkerCompletionTraversesPublicCustody()
        case.addCleanup(owner.doCleanups)
        self.owner = owner
        def line_base():
            owner.container = tempfile.mkdtemp(prefix="ordinary-admission-", dir=owner.root)
            owner.reviewed_source = os.path.join(owner.container, "input", "source")
            shutil.copytree(worker.outputs, owner.reviewed_source)
            owner.review_output = os.path.join(owner.container, "output")
            os.makedirs(owner.review_output)
            owner.observed = {"base": worker.base, "head": worker.git("rev-parse", "HEAD").strip(),
                              "tree": worker.git("rev-parse", "HEAD^{tree}").strip()}
            owner.profile = lifecycle.RealLineProfile(owner.observed)
            return worker.base
        owner.line_base = line_base
        owner.setUp()
        self.manager = owner.control
        self.jobs = owner.jobs
        self.line_id = owner.line["line_id"]
        self.authority = Authority.create(os.path.join(owner.root, "ordinary-authority.sqlite3"),
            authority_uuid=owner.AUTHORITY, clock=owner.clock)
        case.addCleanup(self.authority.dispose)
        self.authority.set_policy("canonical_target", worker.base)
        self.authority.create_work(lifecycle.WORK_A, "implementation", contract=V12, operation_id="create-ordinary-work")
        self.authority.add_route_handler("implementation", lifecycle.WRITER)
        self.publisher = self.authority.session(lifecycle.WRITER)
        self.assignment = self.publisher.claim({"work_id": lifecycle.WORK_A, "operation_id": "claim-ordinary-writer"})["assignment"]
        self.sessions = {}
        self.calls = []
        for participant, capability, verb in (("baton.verify", "verify", "verify"),
                ("baton.review", "review", "review"), ("baton.approve", "approve", "approve")):
            self.authority.grant_capability(participant, capability)
            session = self.authority.session(participant)
            def call(operands, session=session, verb=verb):
                self.calls.append((verb, copy.deepcopy(operands)))
                return getattr(session, verb)(operands)
            self.sessions[verb] = SimpleNamespace(participant=participant, receipt=session.receipt, **{verb: call})
        self.authority_read = SimpleNamespace(proposal=self.publisher.proposal, receipt=self.publisher.receipt,
            canonical_target=self.publisher.canonical_target, policy_generation=self.authority.policy_generation)
        # W110774: THE INTEGRATOR'S OWN CAPABILITY, granted with the other
        # three rather than assumed. This world composes an integrator session
        # below; nothing exercised its receipt until the runtime port's own
        # suite drove one, and the Authority writes an integration receipt only
        # for a participant that holds `integrate`. Granted HERE, beside the
        # other grants, because a capability granted later moves the policy
        # generation under receipts this world has already written.
        self.authority.grant_capability(PARTICIPANT, "integrate")
        self.coordinator = IntegrationStore.open(os.path.join(owner.root, "ordinary-integration.sqlite3"), incarnation="integration-1", clock=owner.clock)
        case.addCleanup(self.coordinator.close)
        self.integrator = self.authority.session(PARTICIPANT)
        self.execution_entries = []
        self.target = "target:ordinary-admission"
        activate_target(self.coordinator, target(self.target))

        review_declarations = owner.DECLARED
        owner.DECLARED = copy.deepcopy(worker_fixture.DECLARED)
        owner.DECLARED[0]["type"] = "git-change-proposal"
        owner.DECLARED[0]["constraints"]["allowed_media_types"] = ["application/octet-stream"]
        self.port, self.adapter, assignment = owner.registered("public-writer", lifecycle.WRITER, "public-writer-principal")
        case.assertEqual(assignment, self.assignment)
        self.writer = lifecycle.review_driver.prepare_implementation(self.manager, line_id=self.line_id,
            attempt_id="public-writer", generation=1, worker_id="public-writer-worker", profile=owner.profile)
        owner.start_registered("public-writer", self.adapter, assignment)
        shutil.copytree(os.path.join(worker.outputs, "proposal"), os.path.join(self.adapter.roots["workspace"], "proposal"))
        with mock.patch.object(worker_fixture.baton_worker, "OUTPUT_ROOT", self.adapter.roots["workspace"]):
            self.measured = worker_fixture.baton_worker.answered(owner.DECLARED, self.answered["outputs"])
            self.completion = worker_fixture.baton_worker.publish_completion(assignment, self.answered["disposition"], self.measured)
            case.assertEqual(json.loads(pathlib.Path(self.adapter.roots["workspace"], "output.json").read_text()), self.completion)
        owner.DECLARED = review_declarations
        self.adapter.stop({"runtime_id": self.adapter.runtime_id})
        reconcile_runtime(self.manager, self.adapter, attempt_id="public-writer")
        observe(self.manager, attempt_id="public-writer", axis="worker_disposition", value=self.answered["disposition"])
        self.frozen = request_freeze(self.manager, self.port, self.adapter, attempt_id="public-writer", disposition=self.answered["disposition"])
        self.intake = request_intake(self.manager, self.port, self.adapter, attempt_id="public-writer")
        self.policy = "sha256:" + "9" * 64
        decide_retention(self.manager, self.port, self.adapter, attempt_id="public-writer",
            artifact_ids=[one["artifact_id"] for one in self.intake["artifacts"]], disposition="retain", retention_policy_digest=self.policy)
        self.required = {"task_id": task["task_id"], "task_digest": "sha256:" + sha256(task_bytes).hexdigest(),
                         "argv": task["verification"], "input_manifest_digest": self.adapter.input_digest}
        self.proposal_id = "no-published-proposal"
        if self.answered["disposition"] != "completed":
            from baton_v12.worker_manager.attempts import finalize_quiescent_assignment
            finalize_quiescent_assignment(self.manager, self.port, attempt_id="public-writer", reason="actual worker unable")
            authorize_cleanup(self.manager, self.port, self.adapter, attempt_id="public-writer", retention_policy_digest=self.policy)
            return
        self.proposal_manifest = driver.retain_proposal(self.manager, self.publisher, attempt_id="public-writer")
        self.published = driver.publish_candidate(self.manager, self.publisher, attempt_id="public-writer", proposal_manifest_digest=self.proposal_manifest)
        self.proposal_id = self.published["proposal_id"]
        checkpoint = freeze_checkpoint(self.manager, writer_id=self.writer["writer_id"], generation=1, profile=owner.profile, port=self.port)
        authorize_cleanup(self.manager, self.port, self.adapter, attempt_id="public-writer", retention_policy_digest=self.policy)
        port, adapter, assignment = owner.registered("public-review", lifecycle.REVIEWER, "public-review-principal")
        attachment = lifecycle.review_driver.prepare_review(self.manager, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id="public-review", generation=1, reviewer_worker_id="public-review-worker", profile=owner.profile)
        owner.start_registered("public-review", adapter, assignment)
        owner.review_output = adapter.roots["workspace"]
        answered, measured = owner.turn("accepted")
        owner.worker_turns += 1
        with mock.patch.object(worker_fixture.baton_worker, "OUTPUT_ROOT", owner.review_output):
            terminal = worker_fixture.baton_worker.publish_completion(assignment, answered["disposition"], measured)
        self.review = {"checkpoint_id": checkpoint["checkpoint_id"], "attachment": attachment, "attempt_id": "public-review",
                       "port": port, "adapter": adapter, "terminal": terminal, "measured": measured}
        self.ended = owner.end(self.review)
        case.assertEqual(self.ended["outcome"], "accepted")
        self.jobs = JobStore.open(os.path.join(owner.root, "ordinary-jobs.sqlite3"), authority_uuid=owner.AUTHORITY, incarnation="jobs-ordinary", clock=owner.clock)
        case.addCleanup(self.jobs.close)
        submission = lifecycle.one_work_submission("ordinary-admission")
        submission["jobs"][0].update(input_digest=self.adapter.input_digest, policy_digest=self.adapter.policy)
        submit(self.jobs, submission)

    def assert_retained_history(self):
        import json
        from pathlib import Path
        from baton_v12.worker_manager import (frozen_output_of, intake_receipt_of, load_manifest, retentions_of)
        from baton_v12.worker_manager.attempts import attempt_runtime_of
        from baton_v12.worker_manager.workspaces import directory_manifest
        case = self.case
        frozen = frozen_output_of(self.manager, "public-writer")
        result = load_manifest(self.manager, frozen["manifest_digest"], "resultManifest")
        receipt = intake_receipt_of(self.manager, "public-writer")
        case.assertEqual(result["completion_manifest_digest"], self.completion["manifest_digest"])
        case.assertEqual(result["assignment_ref"], self.assignment)
        case.assertEqual(result["result_id"], frozen["result_id"])
        case.assertEqual(receipt["result_id"], frozen["result_id"])
        case.assertEqual(receipt["custody"], "accepted")
        case.assertEqual(result["input_manifest_digest"], self.required["input_manifest_digest"])
        case.assertEqual(result["outputs"][0]["result_metadata"][driver.ORDINARY_TESTS_NAMESPACE], self.observation)
        case.assertEqual(result["outputs"][0]["content_manifest"], self.measured[0]["content_manifest"])
        retained = retentions_of(self.manager, "public-writer")
        case.assertEqual({one["artifact_id"] for one in retained}, {one["artifact_id"] for one in receipt["artifacts"]})
        case.assertTrue(all(one["disposition"] == "retain" for one in retained))
        for artifact in receipt["artifacts"]:
            place = Path(artifact["custody_locator"].removeprefix("file://"))
            case.assertTrue(place.is_dir())
            case.assertEqual(directory_manifest(str(place))["tree_digest"], artifact["content_digest"])
            report = json.loads((place / "result.json").read_text())
            case.assertEqual(None if report["verification"] is None else report["verification"]["status"], self.observation["status"])
            case.assertEqual(report["base"], self.observation["base"])
            case.assertEqual(report["head"], self.observation["head"])
        case.assertEqual(attempt_runtime_of(self.manager, "public-writer")["execution_runtime"], "destroyed")
        case.assertFalse(os.path.exists(self.adapter.roots["workspace"]))
        case.assertEqual(len(self.adapter.destroyed_with), 1)
        if hasattr(self, "review"):
            self.owner.assert_owned_custody(self.review, self.ended)

    def assert_no_admission(self):
        self.case.assertEqual(self.calls, [])
        self.case.assertEqual(self.publisher.receipts(self.proposal_id), [])
        self.case.assertEqual(entries_of(self.coordinator, self.target), [])
        self.case.assertEqual(self.execution_entries, [])

    def evidence(self):
        return driver.ordinary_test_evidence(self.manager, self.authority_read, line_id=self.line_id, proposal_id=self.proposal_id)

    def receipts(self, required=None):
        return driver._accepted_receipts(self.manager, self.authority_read, self.sessions["verify"],
            self.sessions["review"], self.sessions["approve"], line_id=self.line_id, proposal_id=self.proposal_id,
            policy_generation=self.authority.policy_generation(), required_tests=self.required if required is None else required)

    def admit(self, required=None):
        """Public admission through the durable enqueue; stop at execution."""
        class AdmissionReached(Exception):
            pass
        def reached(*args, **operands):
            entry = next(one for one in entries_of(self.coordinator, self.target) if one["entry_id"] == operands["entry_id"])
            self.case.assertEqual(entry["state"], "queued")
            self.execution_entries.append(entry)
            raise AdmissionReached()
        def no_runtime(*args):
            raise AssertionError("this admission proof starts no integration runtime")
        with mock.patch.object(execution, "integrate_next", side_effect=reached):
            try:
                driver.admit_accepted(self.coordinator, self.manager, self.jobs, self.authority_read,
                    self.sessions["verify"], self.sessions["review"], self.sessions["approve"], self.integrator,
                    SimpleNamespace(run=no_runtime), canonical_target_id=self.target, line_id=self.line_id,
                    proposal_id=self.proposal_id, policy_generation=self.authority.policy_generation(), profile=profile(),
                    attempt_id="ordinary-integrator", launch_root=os.path.join(self.owner.root, "no-runtime-delivery"),
                    workspace_group=self.owner.group, required_tests=self.required if required is None else required)
            except AdmissionReached:
                return self.execution_entries[-1]
        raise AssertionError("public admission did not reach its execution boundary")


class TheOrdinaryCommandTraversesPublicAdmission(unittest.TestCase):
    def test_actual_command_custody_cleanup_and_authority_admission(self):
        world = _OrdinaryAdmissionWorld(self)
        observed = world.evidence()
        self.assertEqual(observed["observation"], world.observation)
        admitted = world.admit()
        self.assertEqual(admitted["state"], "queued")
        self.assertEqual(admitted["eligibility"]["proposal_id"], world.proposal_id)

    def test_exact_admission_replay_preserves_receipts_rank_and_retained_evidence(self):
        import contextlib
        from tests.manager.test_claude_agent import ClaudeAgent
        world = _OrdinaryAdmissionWorld(self)
        world.assert_retained_history()
        first = world.admit()
        receipts = world.publisher.receipts(world.proposal_id)
        calls = copy.deepcopy(world.calls)
        self.assertEqual([verb for verb, _ in calls], ["verify", "review", "approve"])
        verification = next(one for one in receipts if one["kind"] == "verification")
        self.assertTrue(verification["receipt_id"].startswith("integration-driver.ordinary-tests-verification-receipt:"))
        self.assertEqual(verification["disposition"], "passed")
        self.assertEqual(verification["candidate_digest"], world.observation["head"])
        self.assertEqual(verification["target"], world.observation["base"])
        self.assertTrue(calls[0][1]["operation_id"].startswith("integration-driver.ordinary-tests-verification-operation:"))
        self.assertEqual({one["kind"]: one["actor"] for one in receipts},
                         {"verification": "baton.verify", "review": "baton.review", "approval": "baton.approve"})
        manager_changes = world.manager._connection.total_changes
        coordinator_changes = world.coordinator._connection.total_changes
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(ClaudeAgent, "work", side_effect=AssertionError("no repeated worker")))
            for adapter in (world.adapter, world.review["adapter"]):
                for member in ("stop", "seal", "collect", "retain", "destroy", "normalize_directory"):
                    stack.enter_context(mock.patch.object(adapter, member, side_effect=AssertionError("no repeated custody act")))
            for _ in range(2):
                self.assertEqual(world.admit(), first)
                self.assertEqual(world.publisher.receipts(world.proposal_id), receipts)
                self.assertEqual(world.evidence()["observation"], world.observation)
        self.assertEqual(world.calls, calls * 3)
        self.assertEqual(world.manager._connection.total_changes, manager_changes)
        self.assertEqual(world.coordinator._connection.total_changes, coordinator_changes)
        self.assertEqual(len(entries_of(world.coordinator, world.target)), 1)
        self.assertEqual(world.command_runs, [(world.required["argv"], 0)])
        for _, operands in calls:
            operation = world.publisher.operation_record(operands["operation_id"])
            self.assertEqual(operation["state"], "committed")

    def test_actual_failed_and_unrun_completion_cannot_publish_policy_receipts_or_admit(self):
        for command_status, unrun in ((3, False), (0, True)):
            with self.subTest(command_status=command_status, unrun=unrun):
                world = _OrdinaryAdmissionWorld(self, command_status=command_status, unrun=unrun)
                self.assertEqual(world.answered["disposition"], "unable")
                self.assertEqual(world.frozen["disposition"], "unable")
                world.assert_retained_history()
                with self.assertRaises(ContractRefusal):
                    world.admit()
                world.assert_no_admission()

    def test_wrong_requirements_refuse_before_any_authority_receipt_or_admission(self):
        world = _OrdinaryAdmissionWorld(self)
        world.assert_retained_history()
        for member, wrong in (("task_id", "another-task"), ("task_digest", "sha256:" + "f" * 64),
                              ("argv", ["python3", "another.py"]), ("input_manifest_digest", "sha256:" + "e" * 64)):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal):
                    world.admit(dict(world.required, **{member: wrong}))
                world.assert_no_admission()
        self.assertEqual(world.admit()["state"], "queued")

    def test_a_real_conflicting_authority_receipt_is_not_overwritten_or_admitted(self):
        world = _OrdinaryAdmissionWorld(self)
        before = world.authority.session("baton.verify").verify({"proposal_id": world.proposal_id,
            "verification_id": "historical-fabricated-passed", "observation": "passed", "operation_id": "historical-verification"})
        retained = world.publisher.receipts(world.proposal_id)
        for _ in range(2):
            with self.assertRaises(ContractRefusal):
                world.admit()
            self.assertEqual(world.publisher.receipts(world.proposal_id), retained)
            self.assertEqual(entries_of(world.coordinator, world.target), [])
            self.assertEqual(world.execution_entries, [])
        self.assertEqual([verb for verb, _ in world.calls], ["verify", "verify"])
        self.assertEqual(world.publisher.receipt(world.proposal_id, "verification")["receipt_id"], "historical-fabricated-passed")

    def test_a_real_proposal_from_another_producer_refuses_before_receipts(self):
        from baton_v12.authority import V12
        world = _OrdinaryAdmissionWorld(self)
        other_work = "0000000a-W99"
        other = world.authority.session("baton.other")
        world.authority.create_work(other_work, "other", contract=V12, operation_id="create-other-producer")
        world.authority.add_route_handler("other", "baton.other")
        assignment = other.claim({"work_id": other_work, "operation_id": "claim-other-producer"})["assignment"]
        world.proposal_id = "other-producer-proposal"
        other.publish(dict({name: world.published[name] for name in
            ("result_digest", "candidate_digest", "input_digest", "policy_digest", "target")},
            result_id="another-producer-result", expect=assignment, proposal_id=world.proposal_id, operation_id="publish-other-producer"))
        with self.assertRaises(ContractRefusal):
            world.admit()
        world.assert_no_admission()

    def test_a_real_later_assignment_generation_cannot_certify_the_earlier_candidate(self):
        world = _OrdinaryAdmissionWorld(self)
        world.publisher.end({"expect": world.assignment, "operation_id": "release-first-producer"})
        later = world.publisher.claim({"work_id": world.assignment["work_ref"]["work_id"], "operation_id": "claim-later-generation"})["assignment"]
        self.assertEqual(later["participant"], world.assignment["participant"])
        self.assertEqual(later["work_ref"], world.assignment["work_ref"])
        self.assertEqual(later["generation"], world.assignment["generation"] + 1)
        world.proposal_id = "later-generation-proposal"
        world.publisher.publish(dict({name: world.published[name] for name in
            ("result_digest", "candidate_digest", "input_digest", "policy_digest", "target")},
            result_id="later-generation-result", expect=later, proposal_id=world.proposal_id, operation_id="publish-later-generation"))
        with self.assertRaises(ContractRefusal) as caught:
            world.admit()
        self.assertIn("published proposal names assignment", str(caught.exception))
        world.assert_no_admission()


# -- W120763: the local record that a publication actually committed ----------
#
# `work/records/2026/09/finding-v12-committed-publication-history/`.
#
# WHAT A RETAINED MANIFEST DOES NOT PROVE. `retain_proposal` composes and
# retains a proposal from a frozen result, and that manifest exists whether or
# not the Authority was ever asked to publish it. A consumer recovering a
# composed ending had nothing local that told the two apart, so reading the
# retained manifest as publication evidence was inferring an act from its
# preparation. These cases drive the real producer, the real
# `publish_candidate` and the deterministic publisher transport, then REOPEN
# the store and read the record back.
#
# WHAT IS STILL A STAND-IN, and it is this suite's own: `frozen_output_of` and
# `assignment_of` are replaced, exactly as `TheProducerFeedsThePublicationDriver`
# replaces them, because this fixture retains real manifests without writing
# the attempt rows those two read. The proposal manifest, the result manifest
# and the publication record are all really durable.


class TheCommittedPublicationSurvivesTheProcessThatMadeIt(ProducerCase):

    ATTEMPT = "attempt-1"

    def owners(self):
        """The two attempt-row readers this fixture stands in for."""
        return mock.patch.multiple(
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
                "generation": self.assignment["generation"]}))

    def published(self):
        """One real retained proposal, really published."""
        digest_ = self.produced()
        with self.owners():
            recorded = driver.publish_candidate(
                self.store, self.publisher, attempt_id=self.ATTEMPT,
                proposal_manifest_digest=digest_)
        return digest_, recorded

    def reopened(self):
        """A manager handle that published nothing."""
        self.store.close()
        self.store = ControlStore.open(
            os.path.join(self._root.name, "control.sqlite3"),
            incarnation="manager-2",
            clock=lambda: "2026-09-07T02:00:00.000Z")
        self.addCleanup(self.store.close)
        return self.store

    def read(self, digest_):
        with self.owners():
            return driver.publication_of(
                self.store, attempt_id=self.ATTEMPT,
                proposal_manifest_digest=digest_)

    def rows(self):
        return self.store._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = ?",
            (driver.PUBLICATION_KIND,)).fetchone()[0]

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception

    @contextlib.contextmanager
    def damaged(self, statement, values=()):
        self.store._connection.execute("SAVEPOINT damaged")
        try:
            self.store._connection.execute(statement, values)
            yield
        finally:
            self.store._connection.execute("ROLLBACK TO damaged")
            self.store._connection.execute("RELEASE damaged")

    # -- what it answers -----------------------------------------------------

    def test_it_takes_no_publisher(self):
        """The structural half of "local reads only".

        A reader that accepted a publisher could republish; this one has
        nowhere to put one.
        """
        self.assertEqual(
            list(inspect.signature(driver.publication_of).parameters),
            ["manager", "attempt_id", "proposal_manifest_digest"])

    def test_a_reopened_manager_reads_the_publication_back(self):
        held, recorded = self.published()
        self.reopened()
        answered = self.read(held)
        self.assertEqual(sorted(answered), sorted(driver.PUBLICATION_RECEIPT))
        self.assertEqual(answered["attempt_id"], self.ATTEMPT)
        self.assertEqual(answered["proposal_manifest_digest"], held)
        self.assertEqual(answered["proposal_id"], recorded["proposal_id"])
        self.assertEqual(answered["result_id"], self.result["result_id"])
        self.assertEqual(answered["result_manifest_digest"],
                         self.result_digest)
        self.assertEqual(answered["candidate_digest"], PRIVATE_HEAD)
        self.assertEqual(answered["target"], PRIVATE_BASE)
        # THE ONE MEMBER NO LOCAL RECORD CAN RE-DERIVE.
        self.assertEqual(answered["published"], self.publisher.proposal(
            recorded["proposal_id"]))

    def test_a_retained_proposal_is_not_a_published_one(self):
        """The whole reason this record exists.

        `retain_proposal` succeeded and the Authority was never asked, so
        there is nothing to read.
        """
        held = self.produced()
        self.assertIsNotNone(load_manifest(self.store, held,
                                           "proposalManifest"))
        self.reopened()
        self.assertIsNone(self.read(held))
        self.assertEqual(self.publisher.calls, [])

    def test_an_exact_republication_replays_one_record(self):
        held, recorded = self.published()
        with self.owners():
            again = driver.publish_candidate(
                self.store, self.publisher, attempt_id=self.ATTEMPT,
                proposal_manifest_digest=held)
        self.assertEqual(again, recorded)
        self.assertEqual(self.rows(), 1)
        self.reopened()
        self.assertEqual(self.read(held), self.read(held))

    # -- the interruption this record is written around ----------------------

    def test_a_publish_whose_record_was_lost_is_not_upgraded_to_success(self):
        """Remote success, local nothing — and recovery re-enters the act.

        The Authority holds the proposal and this manager holds no evidence,
        so the reader answers absence. Absence means "no local record" and
        never "not published": ordinary recovery re-enters `publish_candidate`
        under the already-owned publication identity, which is what turns the
        interruption into a committed record rather than a second proposal.
        """
        held = self.produced()

        class Interrupted(Exception):
            pass

        with self.owners(), mock.patch.object(
                self.store, "transact", side_effect=Interrupted):
            with self.assertRaises(Interrupted):
                driver.publish_candidate(
                    self.store, self.publisher, attempt_id=self.ATTEMPT,
                    proposal_manifest_digest=held)
        self.assertEqual(len(self.publisher.calls), 1)
        self.reopened()
        self.assertIsNone(self.read(held))
        self.assertEqual(self.rows(), 0)

        with self.owners():
            driver.publish_candidate(
                self.store, self.publisher, attempt_id=self.ATTEMPT,
                proposal_manifest_digest=held)
        self.assertEqual(len(self.publisher.calls), 2)
        self.assertEqual(self.publisher.calls[0], self.publisher.calls[1])
        self.assertEqual(self.rows(), 1)
        self.assertIsNotNone(self.read(held))

    def test_a_remote_answer_that_is_not_the_requested_proposal_records_none(self):
        held = self.produced()
        original = self.publisher.publish

        def wrong(operands):
            answer = original(operands)
            return dict(answer, candidate_digest="0" * 40)

        with self.owners(), mock.patch.object(self.publisher, "publish",
                                              side_effect=wrong):
            self.refusal(driver.publish_candidate, self.store,
                         self.publisher, attempt_id=self.ATTEMPT,
                         proposal_manifest_digest=held)
        self.assertEqual(self.rows(), 0)
        self.reopened()
        self.assertIsNone(self.read(held))

    def test_a_readback_that_disagrees_records_none(self):
        held = self.produced()
        with self.owners(), mock.patch.object(
                self.publisher, "proposal",
                side_effect=lambda proposal_id: dict(
                    copy.deepcopy(self.publisher.recorded),
                    result_id="another-result")):
            self.refusal(driver.publish_candidate, self.store,
                         self.publisher, attempt_id=self.ATTEMPT,
                         proposal_manifest_digest=held)
        self.assertEqual(self.rows(), 0)
        self.reopened()
        self.assertIsNone(self.read(held))


    # -- W120763 review [P2]: a boolean is not a generation --------------------

    def test_a_boolean_generation_in_the_readback_commits_nothing(self):
        """`True == 1`, so equality alone accepted it at generation 1.

        The journal signature does not close the gap either: it is derived for
        integer generation 1 and says nothing about the types the recorded
        RESULT carries. So the types are proved before anything is committed.
        """
        held = self.produced()

        def boolean(proposal_id):
            answer = copy.deepcopy(self.publisher.recorded)
            answer["assignment_ref"] = dict(answer["assignment_ref"],
                                            generation=True)
            return dict(answer, decision={},
                        published_at="2026-09-07T02:00:00.000Z")

        with self.owners(), mock.patch.object(self.publisher, "proposal",
                                              side_effect=boolean):
            caught = self.refusal(
                driver.publish_candidate, self.store, self.publisher,
                attempt_id=self.ATTEMPT, proposal_manifest_digest=held)
        self.assertIn("generation", caught.message)
        self.assertEqual(self.rows(), 0)
        self.reopened()
        self.assertIsNone(self.read(held))

    def test_a_boolean_generation_in_the_record_refuses_on_read(self):
        held, _recorded = self.published()
        self.reopened()
        row = self.store._connection.execute(
            "SELECT operation_id, result FROM operations WHERE kind = ?",
            (driver.PUBLICATION_KIND,)).fetchone()
        receipt = json.loads(row["result"])
        for name, damaged in (
                ("the receipt's own assignment",
                 dict(receipt, assignment=dict(
                     receipt["assignment"], generation=True))),
                ("the recorded Authority answer",
                 dict(receipt, published=dict(
                     receipt["published"],
                     assignment_ref=dict(
                         receipt["published"]["assignment_ref"],
                         generation=True))))):
            with self.subTest(assignment=name):
                with self.damaged(
                        "UPDATE operations SET result = ? WHERE "
                        "operation_id = ?",
                        (json.dumps(damaged), row["operation_id"])):
                    caught = self.refusal(self.read, held)
                self.assertIn("generation", caught.message)

    def test_an_honest_generation_still_reads_back_after_reopening(self):
        """The positive half, so the type proof is a gate and not a wall.

        Publisher methods are forbidden here, which is the same statement the
        signature makes structurally: the reader performs no remote act.
        """
        held, recorded = self.published()
        self.reopened()
        with mock.patch.object(self.publisher, "publish",
                               side_effect=AssertionError("no republish")), \
                mock.patch.object(self.publisher, "proposal",
                                  side_effect=AssertionError("no remote read")):
            changes = self.store._connection.total_changes
            answered = self.read(held)
            again = self.read(held)
        self.assertEqual(answered, again)
        self.assertEqual(answered["assignment"]["generation"],
                         self.assignment["generation"])
        self.assertIs(type(answered["assignment"]["generation"]), int)
        self.assertEqual(answered["published"]["assignment_ref"],
                         recorded["assignment_ref"])
        self.assertEqual(self.store._connection.total_changes, changes)

    # -- present, and not this publication's ---------------------------------

    def test_a_record_of_another_kind_refuses(self):
        held, _recorded = self.published()
        self.reopened()
        with self.damaged("UPDATE operations SET kind = 'foreign.publication' "
                          "WHERE kind = ?", (driver.PUBLICATION_KIND,)):
            self.assertIsInstance(self.refusal(self.read, held),
                                  ContractRefusal)

    def test_a_signature_this_manager_does_not_derive_refuses(self):
        """The record and the retained proposal it names must still agree.

        The operands are re-derived from that proposal, the frozen result and
        the fixed assignment, so a row signed over anything else is not this
        act — and a proposal edited underneath a real record refuses here too.
        """
        held, _recorded = self.published()
        self.reopened()
        for name, statement, values in (
                ("an empty signature",
                 "UPDATE operations SET signature = '{}' WHERE kind = ?",
                 (driver.PUBLICATION_KIND,)),
                ("a foreign signature",
                 "UPDATE operations SET signature = ? WHERE kind = ?",
                 (json.dumps({"kind": driver.PUBLICATION_KIND,
                              "operands": {}}, sort_keys=True,
                             separators=(",", ":")),
                  driver.PUBLICATION_KIND))):
            with self.subTest(signature=name):
                with self.damaged(statement, values):
                    caught = self.refusal(self.read, held)
                self.assertIn("does not derive", caught.message)

    def test_a_receipt_whose_selectors_this_manager_does_not_derive_refuses(self):
        held, recorded = self.published()
        self.reopened()
        row = self.store._connection.execute(
            "SELECT operation_id, result FROM operations WHERE kind = ?",
            (driver.PUBLICATION_KIND,)).fetchone()
        receipt = json.loads(row["result"])
        for name, changed in (
                ("another attempt", {"attempt_id": "another-attempt"}),
                ("another proposal", {"proposal_id": "proposal-elsewhere"}),
                ("another result", {"result_id": "another-result"}),
                ("another candidate", {"candidate_digest": "0" * 40}),
                ("another target", {"target": "0" * 40}),
                ("another assignment",
                 {"assignment": dict(recorded["assignment_ref"],
                                     generation=99)})):
            with self.subTest(receipt=name):
                with self.damaged(
                        "UPDATE operations SET result = ? WHERE "
                        "operation_id = ?",
                        (json.dumps(dict(receipt, **changed)),
                         row["operation_id"])):
                    self.assertIsInstance(self.refusal(self.read, held),
                                          ContractRefusal)

    def test_a_malformed_receipt_refuses(self):
        held, _recorded = self.published()
        self.reopened()
        row = self.store._connection.execute(
            "SELECT operation_id, result FROM operations WHERE kind = ?",
            (driver.PUBLICATION_KIND,)).fetchone()
        receipt = json.loads(row["result"])
        short = {member: value for member, value in receipt.items()
                 if member != "published"}
        for name, value in (("a missing member", short),
                            ("an unknown member",
                             dict(receipt, invented="anything")),
                            ("not a document", ["published"]),
                            ("an answer that is not a document",
                             dict(receipt, published="published"))):
            with self.subTest(receipt=name):
                with self.damaged(
                        "UPDATE operations SET result = ? WHERE "
                        "operation_id = ?",
                        (json.dumps(value), row["operation_id"])):
                    self.assertIsInstance(self.refusal(self.read, held),
                                          ContractRefusal)

    def test_a_recorded_answer_that_disagrees_with_its_operands_refuses(self):
        held, _recorded = self.published()
        self.reopened()
        row = self.store._connection.execute(
            "SELECT operation_id, result FROM operations WHERE kind = ?",
            (driver.PUBLICATION_KIND,)).fetchone()
        receipt = json.loads(row["result"])
        answer = dict(receipt["published"], result_digest="sha256:foreign")
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(receipt, published=answer)),
                 row["operation_id"])):
            caught = self.refusal(self.read, held)
        self.assertIn("disagrees about", caught.message)
