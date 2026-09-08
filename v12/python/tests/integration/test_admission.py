"""W101491: one accepted candidate account, proved before queue mutation."""

import copy
import json
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import IntegrationStore, activate_target
from baton_v12.integration import admission
from baton_v12.integration.admission import admit_candidate
from baton_v12.source_profiles import GIT_PROFILE

from .fixtures import (CoordinatorCase, PATHS, TARGET, TEST_SCOPE, UUID_A,
                       UUID_B, eligibility, target)


WORK = "0000000a-W1"
NOW = "2026-09-06T14:00:00.000Z"


class Authority:
    def __init__(self, case):
        self.case = case

    def proposal(self, proposal_id):
        return copy.deepcopy(self.case.proposal)

    def receipt(self, proposal_id, kind):
        answer = self.case.receipts.get(kind)
        return None if answer is None else copy.deepcopy(answer)

    def canonical_target(self):
        return self.case.current_target


class AdmissionCase(CoordinatorCase):

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        self.manager = SimpleNamespace(_connection=lambda: None)
        self.jobs = SimpleNamespace(_connection=lambda: None,
                                    authority_uuid=UUID_A)
        self.authority = Authority(self)
        evidence = {
            "profile": GIT_PROFILE, "base": "a" * 40,
            "head": "b" * 40, "tree": "c" * 40,
            "paths": list(PATHS), "path_set_digest": digest(PATHS),
            "reference": "checkpoint/line-1/1"}
        self.accepted = {
            "line_id": "line-1", "checkpoint_id": "checkpoint-1",
            "verdict_id": "verdict-1",
            "checkpoint_digest": digest(evidence), "evidence": evidence}
        self.line = {"line_id": "line-1", "authority_uuid": UUID_A,
                     "work_id": WORK, "current_checkpoint_id": "checkpoint-1"}
        self.checkpoint = {
            "checkpoint_id": "checkpoint-1", "writer_id": "writer-1",
            "line_id": "line-1", "checkpoint_digest":
                self.accepted["checkpoint_digest"],
            "path_set_digest": digest(PATHS),
            "evidence": copy.deepcopy(self.accepted["evidence"])}
        self.writer = {
            "writer_id": "writer-1", "line_id": "line-1",
            "runtime_attempt_id": "attempt-1", "assignment_generation": 1,
            "participant": "baton.impl"}
        self.assignment = {
            "runtime_attempt_id": "attempt-1", "authority_uuid": UUID_A,
            "work_id": WORK, "participant": "baton.impl", "generation": 1,
            "principal": "principal.impl", "effective_scope": "repository"}
        self.frozen = {
            "attempt_id": "attempt-1", "result_id": "result-1",
            "disposition": "completed", "manifest_digest":
                "sha256:" + "3" * 64,
            "freeze_operation_id": "freeze-1", "frozen_at": NOW,
            "artifacts": []}
        self.proposal = {
            "proposal_id": "proposal-1",
            "assignment_ref": {
                "work_ref": {"authority_uuid": UUID_A, "work_id": WORK},
                "participant": "baton.impl", "generation": 1},
            "decision": {}, "result_id": "result-1",
            "result_digest": self.frozen["manifest_digest"],
            "candidate_digest": "sha256:" + "2" * 64,
            "input_digest": "sha256:input", "policy_digest": "sha256:policy",
            "target": "revision-1", "published_at": NOW}
        self.receipts = {
            kind: {"receipt_id": kind + "-1", "kind": kind,
                   "proposal_id": "proposal-1", "actor": "baton." + kind,
                   "disposition": disposition,
                   "candidate_digest": self.proposal["candidate_digest"],
                   "target": "revision-1",
                   "policy_generation": 1 if kind == "approval" else None,
                   "recorded_at": NOW, "decision": {}}
            for kind, disposition in admission._RECEIPT_DISPOSITIONS.items()}
        self.current_target = "revision-1"
        self.job = {"job_id": "job-1", "submission_id": "submission-1",
                    "ordinal": 0, "input_digest": "sha256:input",
                    "policy_digest": "sha256:policy",
                    "test_scope": json.dumps(TEST_SCOPE),
                    "terminal_policy": "report-and-hold"}
        self.stages = [{"stage_id": "job-1/implementation",
                        "job_id": "job-1", "ordinal": 0,
                        "kind": "implementation", "work_id": WORK,
                        "profile_name": "implementation",
                        "profile_digest": "sha256:profile",
                        "depends_on": "[]"}]
        patches = {
            "integration_checkpoint": lambda store, line_id:
                copy.deepcopy(self.accepted),
            "line_of": lambda store, line_id: copy.deepcopy(self.line),
            "checkpoint_of": lambda store, checkpoint_id:
                copy.deepcopy(self.checkpoint),
            "writer_of": lambda store, writer_id: copy.deepcopy(self.writer),
            "assignment_of": lambda store, attempt_id:
                copy.deepcopy(self.assignment),
            "frozen_output_of": lambda store, attempt_id:
                copy.deepcopy(self.frozen),
            "job_rows": lambda store: [copy.deepcopy(self.job)],
            "stages_of": lambda store, job_id: copy.deepcopy(self.stages),
        }
        self.patch = mock.patch.multiple(admission, **patches)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def admit(self, entry_id="entry-1", store=None):
        return admit_candidate(
            store or self.coordinator, self.manager, self.jobs, self.authority,
            canonical_target_id=TARGET, entry_id=entry_id, line_id="line-1",
            proposal_id="proposal-1")

    def unchanged(self):
        self.assertEqual(self.coordinator._connection.execute(
            "SELECT COUNT(*) FROM entries").fetchone()[0], 0)
        # Target activation is the only coordinator act before admission.
        self.assertEqual(self.coordinator._connection.execute(
            "SELECT COUNT(*) FROM operations").fetchone()[0], 1)

    def refusal(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.admit()
        self.unchanged()
        return caught.exception


class AcceptedAccount(AdmissionCase):

    def test_complete_evidence_enqueues_the_exact_producer_account(self):
        placed = self.admit()
        self.assertEqual(placed["eligibility"], eligibility(
            work_id=WORK, checkpoint_digest=self.accepted["checkpoint_digest"],
            candidate_digest=self.proposal["candidate_digest"],
            result_digest=self.proposal["result_digest"],
            expected_target_revision=self.proposal["target"]))
        self.assertEqual((placed["entry_id"], placed["rank"], placed["state"]),
                         ("entry-1", 1, "queued"))

    def test_exact_replay_returns_the_same_entry_and_rank(self):
        first = self.admit()
        self.assertEqual(self.admit(), first)
        self.assertEqual(self.coordinator._connection.execute(
            "SELECT COUNT(*) FROM entries").fetchone()[0], 1)

    def test_two_authorities_share_one_target_order(self):
        first = self.admit()
        self.jobs.authority_uuid = UUID_B
        self.line.update(line_id="line-2", authority_uuid=UUID_B,
                         work_id="0000000b-W2",
                         current_checkpoint_id="checkpoint-2")
        self.accepted.update(line_id="line-2", checkpoint_id="checkpoint-2",
                             verdict_id="verdict-2")
        self.checkpoint.update(checkpoint_id="checkpoint-2",
                               writer_id="writer-2", line_id="line-2")
        self.writer.update(writer_id="writer-2", line_id="line-2",
                           runtime_attempt_id="attempt-2")
        self.assignment.update(runtime_attempt_id="attempt-2",
                               authority_uuid=UUID_B, work_id="0000000b-W2")
        self.frozen.update(attempt_id="attempt-2", result_id="result-2")
        self.proposal.update(proposal_id="proposal-2", result_id="result-2",
                             candidate_digest="sha256:" + "4" * 64)
        self.proposal["assignment_ref"]["work_ref"] = {
            "authority_uuid": UUID_B, "work_id": "0000000b-W2"}
        for receipt in self.receipts.values():
            receipt["proposal_id"] = "proposal-2"
            receipt["candidate_digest"] = self.proposal["candidate_digest"]
        self.stages[0]["work_id"] = "0000000b-W2"
        second = admit_candidate(
            self.coordinator, self.manager, self.jobs, self.authority,
            canonical_target_id=TARGET, entry_id="entry-2", line_id="line-2",
            proposal_id="proposal-2")
        self.assertEqual((first["rank"], second["rank"]), (1, 2))
        self.assertEqual((first["authority_uuid"], second["authority_uuid"]),
                         (UUID_A, UUID_B))

    def test_concurrent_exact_admission_returns_one_entry_and_rank(self):
        gate = threading.Barrier(2)
        answers, failures = [], []

        def run(incarnation):
            store = None
            try:
                store = IntegrationStore.open(
                    self.path, incarnation=incarnation, clock=self.clock)
                gate.wait()
                answers.append(self.admit(store=store))
            except BaseException as failure:
                failures.append(failure)
            finally:
                if store is not None:
                    store.close()

        threads = [threading.Thread(target=run, args=(f"coordinator-{one}",))
                   for one in (2, 3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(failures, [])
        self.assertEqual(len(answers), 2)
        self.assertEqual(answers[0], answers[1])
        self.assertEqual((answers[0]["entry_id"], answers[0]["rank"]),
                         ("entry-1", 1))
        self.assertEqual(self.coordinator._connection.execute(
            "SELECT COUNT(*) FROM entries").fetchone()[0], 1)


class RefusalBeforeMutation(AdmissionCase):

    def test_the_checkpoint_must_be_accepted(self):
        with mock.patch.object(admission, "integration_checkpoint",
                               return_value=None):
            self.refusal()

    def test_each_required_policy_receipt_must_be_present_and_accepted(self):
        for kind in tuple(self.receipts):
            with self.subTest(kind=kind, failure="missing"):
                held = self.receipts.pop(kind)
                self.refusal()
                self.receipts[kind] = held
            with self.subTest(kind=kind, failure="wrong disposition"):
                self.receipts[kind]["disposition"] = "not-accepted"
                self.refusal()
                self.receipts[kind]["disposition"] = \
                    admission._RECEIPT_DISPOSITIONS[kind]

    def test_receipt_candidate_and_target_cross_wiring_refuses(self):
        for member in ("candidate_digest", "target"):
            with self.subTest(member=member):
                self.receipts["review"][member] = "different"
                self.refusal()
                self.receipts["review"][member] = self.proposal[
                    "candidate_digest" if member == "candidate_digest" else
                    "target"]

    def test_assignment_identity_cross_wiring_refuses(self):
        for target, member, value in (
                (self.proposal["assignment_ref"]["work_ref"],
                 "authority_uuid", UUID_B),
                (self.proposal["assignment_ref"]["work_ref"],
                 "work_id", "0000000b-W2"),
                (self.proposal["assignment_ref"], "participant", "baton.other"),
                (self.proposal["assignment_ref"], "generation", 2)):
            with self.subTest(member=member):
                prior = target[member]
                target[member] = value
                self.refusal()
                target[member] = prior

    def test_the_job_store_must_share_the_candidate_authority(self):
        self.jobs.authority_uuid = UUID_B
        self.refusal()

    def test_checkpoint_identity_digest_profile_and_path_cross_wiring_refuses(self):
        changes = (
            (self.checkpoint, "line_id", "line-other"),
            (self.checkpoint, "checkpoint_digest", "sha256:different"),
            (self.checkpoint["evidence"], "profile", "generic"),
            (self.checkpoint, "path_set_digest", "sha256:different"),
        )
        for target, member, value in changes:
            with self.subTest(member=member):
                prior = target[member]
                target[member] = value
                self.refusal()
                target[member] = prior

    def test_frozen_result_identity_digest_and_disposition_must_match(self):
        for member, value in (("result_id", "result-other"),
                              ("manifest_digest", "sha256:different"),
                              ("disposition", "unable")):
            with self.subTest(member=member):
                prior = self.frozen[member]
                self.frozen[member] = value
                self.refusal()
                self.frozen[member] = prior

    def test_stale_target_refuses(self):
        self.current_target = "revision-2"
        self.refusal()

    def test_job_input_policy_scope_and_work_are_not_caller_claims(self):
        for member in ("input_digest", "policy_digest"):
            with self.subTest(member=member):
                prior = self.job[member]
                self.job[member] = "sha256:different"
                self.refusal()
                self.job[member] = prior
        self.stages[0]["work_id"] = "0000000b-W2"
        self.refusal()

    def test_ambiguous_job_scope_refuses(self):
        second = copy.deepcopy(self.job)
        second["job_id"] = "job-2"
        second["test_scope"] = json.dumps(["tests/other"])
        with mock.patch.object(admission, "job_rows",
                               return_value=[self.job, second]), \
                mock.patch.object(admission, "stages_of",
                                  return_value=self.stages):
            self.refusal()

    def test_malformed_scope_refuses(self):
        for scope in ("not-a-list", ["../outside"], ["tests/a", "tests/a"]):
            with self.subTest(scope=scope):
                self.job["test_scope"] = json.dumps(scope)
                self.refusal()


if __name__ == "__main__":
    unittest.main()
