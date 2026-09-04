"""W71875 — the seam onto the v12 operations, driven against the real ones.

THE IDENTITIES ARE PINNED HERE, and that is the point of the file. This
control plane decides whether a restart already performed an act by asking the
Worker Manager's journal for an operation identity IT DERIVES. If the manager
ever spelled that identity differently, every sweep would repeat a committed
offer -- so these cases call `issue_offer` and the claim for real and assert
the manager journalled exactly what `canonical_operation` builds.

The rest of the file proves the other half of the composition claim: the
observation is four public reads and no opinion, and the bearer `issue_offer`
answers with is delivered once and stored nowhere.
"""

import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (CANONICAL_OPERATIONS, INTENT_OPERANDS,
                                   OBSERVATION_MEMBERS, OPERATIONS,
                                   ManagerOperations, Unobserved,
                                   canonical_operation, check_binding, job_of,
                                   stage_intent, stage_rows, submit)
from baton_v12.worker_manager import accept_offer

if __package__:
    from .fixtures import NOW, WORK_A, JobManagerCase, job, submission
else:
    from fixtures import NOW, WORK_A, JobManagerCase, job, submission


class CanonicalIdentities(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission())
        self.stages = {row["stage_id"]: self.attempting(self.jobs,
                                                        row["stage_id"])
                       for row in stage_rows(self.jobs)}
        self.stage = self.stages["job-a/implementation"]
        self.job = {"input_digest": "sha256:" + "1" * 64,
                    "policy_digest": "sha256:" + "2" * 64}
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def accept(self):
        issued = self.delivered[-1]
        return accept_offer(self.control_store, self.acts.port,
                            offer_id=self.stage["offer_id"], decision="accept",
                            bearer=issued["bearer"], now=NOW,
                            runtime_attempt_id=self.stage["attempt_id"],
                            work_ref={"authority_uuid": "0" * 31 + "a",
                                      "work_id": WORK_A})

    def test_the_manager_journals_the_admit_identity_this_build_derives(self):
        self.acts.admit(self.stage, self.job)
        derived = canonical_operation("admit", self.stage["offer_id"])
        self.assertEqual(derived, f"offer.issue:{self.stage['offer_id']}")
        self.assertNotIn("/", self.stage["offer_id"])
        record = self.acts.receipt_of(derived)
        self.assertIsNotNone(
            record,
            "the Job manager decides what a restart already did by asking the "
            "manager's journal for this identity; a spelling change here "
            "would make every sweep repeat the offer")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["kind"], "offer.issue")

    def test_the_manager_journals_the_claim_identity_this_build_derives(self):
        self.acts.admit(self.stage, self.job)
        self.accept()
        self.acts.claim(self.stage)
        derived = canonical_operation("claim", self.stage["offer_id"])
        self.assertEqual(derived, f"offer.settle:{self.stage['offer_id']}")
        record = self.acts.receipt_of(derived)
        self.assertIsNotNone(record)
        self.assertEqual(record["kind"], "offer.settle")

    def test_an_act_outside_the_closed_vocabulary_is_refused(self):
        with self.assertRaises(ContractRefusal):
            canonical_operation("integrate", "offer:x")

    def test_both_acts_have_a_template(self):
        self.assertEqual(sorted(CANONICAL_OPERATIONS), ["admit", "claim"])


class TheBearer(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission())
        self.stage = self.attempting(self.jobs)
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def test_the_bearer_is_minted_delivered_once_and_answered_nowhere(self):
        answer = self.acts.admit(self.stage,
                                 {"input_digest": "sha256:" + "1" * 64,
                                  "policy_digest": "sha256:" + "2" * 64})
        self.assertIsNone(answer, "an act answers nothing a caller could "
                                  "mistake for the secret")
        self.assertEqual(self.minted, ["bearer-1"])
        self.assertEqual(len(self.delivered), 1)
        self.assertEqual(self.delivered[0]["bearer"], "bearer-1")

    def test_no_durable_row_in_either_store_carries_the_bearer(self):
        self.acts.admit(self.stage, {"input_digest": "sha256:" + "1" * 64,
                                     "policy_digest": "sha256:" + "2" * 64})
        for store in (self.jobs, self.control_store):
            for row in store._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"):
                for entry in store._connection.execute(
                        f"SELECT * FROM {row[0]}").fetchall():
                    for value in tuple(entry):
                        self.assertNotIn("bearer-1", str(value))

    def test_a_capability_that_cannot_be_called_is_refused_at_construction(self):
        with self.assertRaises(ContractRefusal):
            ManagerOperations(self.control_store, self.acts.port,
                              mint_bearer=None, deliver_bearer=self.deliver)
        with self.assertRaises(ContractRefusal):
            ManagerOperations(self.control_store, self.acts.port,
                              mint_bearer=self.mint, deliver_bearer="nope")


class Observation(JobManagerCase):

    def test_an_unstarted_stage_observes_absence_rather_than_a_guess(self):
        jobs = self.store()
        submit(jobs, submission())
        stage = self.attempting(jobs)
        observed = self.operations().observe(stage)
        self.assertEqual(sorted(observed), sorted(OBSERVATION_MEMBERS))
        self.assertEqual(observed, {"claimed_by": None, "runtime": None,
                                    "activity": None, "output": None,
                                    "start_failure": None,
                                    "preparation_failure": None})

    def test_the_closed_surface_is_what_a_deployment_must_supply(self):
        acts = self.operations()
        for member in OPERATIONS:
            self.assertTrue(hasattr(acts, member), member)

    def test_a_status_surface_with_no_control_store_refuses_every_act(self):
        # `observe` still answers -- emptily -- because a read-only status has
        # to be able to say "nobody looked" without pretending it did.
        unobserved = Unobserved()
        self.assertFalse(unobserved.canonical)
        self.assertEqual(unobserved.observe({"attempt_id": "attempt:x"}),
                         {"claimed_by": None, "runtime": None,
                          "activity": None, "output": None,
                          "start_failure": None,
                          "preparation_failure": None})
        for call in (lambda: unobserved.receipt_of("offer.issue:x"),
                     lambda: unobserved.recover(now=NOW),
                     lambda: unobserved.admit({}, {}),
                     lambda: unobserved.claim({})):
            with self.assertRaises(ContractRefusal) as caught:
                call()
            self.assertEqual(caught.exception.code, "capability")


class Binding(JobManagerCase):
    """What `check_binding` answers, act by act, at the seam itself.

    The reproduction that refused the first candidate lives in `test_restart`,
    against two real stores. These are the surrounding cases: an offer nobody
    has issued, a caller with no control store at all, and a journal row whose
    signature this build cannot read.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.stage = self.attempting(self.jobs)
        self.job = job_of(self.jobs, "job-a")
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def test_an_unissued_offer_is_absence_and_not_a_foreign_act(self):
        self.assertIsNone(check_binding(self.acts, self.stage, self.job))

    def test_a_caller_with_no_control_store_is_answered_without_a_read(self):
        # `Unobserved.receipt_of` refuses, so an implementation that asked
        # anyway would make a read-only status surface impossible to assemble.
        self.assertIsNone(check_binding(Unobserved(), self.stage, self.job))

    def test_the_committed_offers_own_intent_is_what_agrees(self):
        self.acts.admit(self.stage, self.job)
        record = check_binding(self.acts, self.stage, self.job)
        self.assertEqual(record["operation_id"],
                         canonical_operation("admit", self.stage["offer_id"]))
        # AND THE REAL SIGNATURE IS WHERE THE INTENT CAME FROM. If `issue_offer`
        # ever stopped signing one of these operands, this build would be
        # comparing against a member that is not there -- which is a refusal to
        # discover here rather than a proof that silently stops proving.
        signed = json.loads(record["signature"])["operands"]
        wanted = stage_intent(self.stage, self.job)
        for member in INTENT_OPERANDS:
            self.assertEqual(signed[member], wanted[member], member)

    def test_a_signature_this_build_cannot_read_is_refused_not_trusted(self):
        """Answering "it matches" for an unreadable row is the fail-open.

        The signature is durable text this process did not write, so a row that
        is not an operation signature at all cannot say whether the act was
        ours -- and a proof that passes when it cannot tell is not a proof.
        """
        self.acts.admit(self.stage, self.job)
        operation_id = canonical_operation("admit", self.stage["offer_id"])
        for spoiled in ("not json", "[]", "null", '{"operands": "text"}',
                        '{"kind": "offer.issue"}'):
            with self.subTest(signature=spoiled):
                self.control_store._connection.execute(
                    "UPDATE operations SET signature = ? "
                    "WHERE operation_id = ?", (spoiled, operation_id))
                with self.assertRaises(ContractRefusal) as caught:
                    check_binding(self.acts, self.stage, self.job)
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))


if __name__ == "__main__":
    unittest.main()
