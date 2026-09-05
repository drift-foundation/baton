"""W71875 — restart reconciliation: repeat no committed act, skip no owed one.

THE WINDOW THIS FILE IS ABOUT is one act wide. A delegated operation is
performed outside this store's transaction and its receipt is written
afterwards, so a process that dies between the two leaves the Worker Manager
holding a committed offer and the Job store holding no record of it. The next
incarnation must find that offer, adopt it, and NOT issue a second one --
`issue_offer` would refuse a second call anyway, and a control plane whose
recovery depends on being refused is not a recovery.

The cases below drive the REAL operations for exactly that reason: the whole
mechanism is the identity this build derives agreeing with the identity the
manager journalled, and a fake that agreed by construction would prove
nothing.
"""

import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, ManagerOperations, canonical_operation,
                                   job_of, owed_acts, receipt_rows,
                                   receipts_of, reconcile, stage_intent,
                                   stage_rows, status, submit, sweep)
from baton_v12.worker_manager import (AuthorityPort, accept_offer, issue_offer,
                                      submit_claim)

if __package__:
    from .fixtures import (INPUT_DIGEST, LATER, NOW, POLICY_DIGEST, PROFILE,
                           SOON, UUID, WORK_A, WORK_C, FakeOperations,
                           JobManagerCase, fake_claim_signature, job, stage,
                           submission)
else:
    from fixtures import (INPUT_DIGEST, LATER, NOW, POLICY_DIGEST, PROFILE,
                          SOON, UUID, WORK_A, WORK_C, FakeOperations,
                          JobManagerCase, fake_claim_signature, job, stage,
                          submission)

OTHER_INPUT = "sha256:" + "9" * 64


class RealComposition(JobManagerCase):
    """One Job, the real manager operations, and a store that gets restarted."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.stage = self.attempting(self.jobs)
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def restart(self, incarnation="jobs-2"):
        """A new Job manager incarnation over the same two stores."""
        self.jobs.close()
        self.jobs = JobStore.open(self.job_path, authority_uuid=UUID, incarnation=incarnation,
                                  clock=self.clock)
        self.addCleanup(self.jobs.close)
        return self.jobs

    def accept(self):
        return accept_offer(self.control_store, self.acts.port,
                            offer_id=self.stage["offer_id"], decision="accept",
                            bearer=self.delivered[-1]["bearer"], now=NOW,
                            runtime_attempt_id=self.stage["attempt_id"],
                            work_ref={"authority_uuid": UUID,
                                      "work_id": WORK_A})

    def test_one_sweep_issues_one_real_offer(self):
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual([one["outcome"] for one in report["acts"]],
                         ["performed"])
        self.assertEqual(len(self.minted), 1)
        self.assertEqual(
            self.control_store._connection.execute(
                "SELECT state FROM offers WHERE offer_id = ?",
                (self.stage["offer_id"],)).fetchone()[0], "issued")

    def test_a_committed_act_with_no_receipt_is_adopted_not_repeated(self):
        sweep(self.jobs, self.acts, now=NOW)
        # THE CRASH WINDOW, reproduced exactly: the manager committed the
        # offer and this store's receipt is gone.
        self.jobs._connection.execute("DELETE FROM receipts")
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE kind = 'stage.receipt'")
        resumed = self.restart()
        report = sweep(resumed, self.acts, now=SOON)
        self.assertEqual(report["acts"][0]["act"], "admit")
        self.assertEqual(report["acts"][0]["outcome"], "adopted")
        # AND THE SAME TICK GOES ON TO DERIVE WHAT THE ADOPTED ACT UNBLOCKS.
        # The claim is owed the moment the offer is known to exist, and it
        # defers because the worker has not accepted yet.
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]],
                         [("admit", "adopted"), ("claim", "deferred")])
        # NOT REPEATED: no second bearer was minted and no second offer exists.
        self.assertEqual(len(self.minted), 1)
        self.assertEqual(
            self.control_store._connection.execute(
                "SELECT count(*) FROM offers").fetchone()[0], 1)
        # AND NOT SKIPPED: the receipt is there, naming the same operation.
        held = receipts_of(resumed, self.stage["stage_id"], 1)["admit"]
        self.assertEqual(held["state"], "adopted")
        self.assertEqual(held["operation_id"],
                         canonical_operation("admit", self.stage["offer_id"]))
        self.assertEqual(held["incarnation"], "jobs-2")

    def test_an_adopted_receipt_records_the_managers_own_committed_result(self):
        sweep(self.jobs, self.acts, now=NOW)
        performed = receipts_of(self.jobs, self.stage["stage_id"], 1)["admit"]
        self.jobs._connection.execute("DELETE FROM receipts")
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE kind = 'stage.receipt'")
        resumed = self.restart()
        sweep(resumed, self.acts, now=LATER)
        adopted = receipts_of(resumed, self.stage["stage_id"], 1)["admit"]
        # SAME FACT, TWO PROVENANCES. The receipt is taken from the manager's
        # journal either way, so a restart audit compares receipts rather than
        # how they were obtained -- and the bearer is in neither.
        self.assertEqual(performed["detail"], adopted["detail"])
        self.assertNotEqual(performed["state"], adopted["state"])
        self.assertNotIn("bearer", adopted["detail"])

    def test_an_owed_act_is_not_skipped_by_a_restart(self):
        self.restart()
        self.assertEqual([one["act"] for one in owed_acts(self.jobs,
                                                          self.acts)],
                         ["admit"])
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([one["outcome"] for one in report["acts"]],
                         ["performed"])

    def test_the_claim_is_reconciled_by_the_same_rule(self):
        sweep(self.jobs, self.acts, now=NOW)
        self.accept()
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(
            self.control_store._connection.execute(
                "SELECT state FROM offers WHERE offer_id = ?",
                (self.stage["offer_id"],)).fetchone()[0], "claimed")
        self.jobs._connection.execute(
            "DELETE FROM receipts WHERE act = 'claim'")
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE operation_id LIKE '%:claim'")
        resumed = self.restart(incarnation="jobs-3")
        # EVERY CALL FROM HERE ON is the resumed process's, so a claim the
        # first incarnation already took cannot be mistaken for a repeat.
        self.session.calls.clear()
        report = sweep(resumed, self.acts, now=SOON)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]], [("claim", "adopted")])
        self.assertEqual(
            [call for call in self.session.calls if call[0] == "claim"], [],
            "the claim was already taken at the authority; a resumed sweep "
            "adopts that committed act rather than asking for it again")

    def test_a_resumed_sweep_proves_the_committed_act_is_this_intent(self):
        """Review [P1]: adoption compared nothing but the derived identity.

        The same store, restarted, with the persisted intent no longer the one
        the committed offer was issued for. A build that adopts by name alone
        records a receipt saying this Job's act is done and then projects this
        Job's digest beside an offer whose signature contains the other one.
        """
        sweep(self.jobs, self.acts, now=NOW)
        self.jobs._connection.execute("DELETE FROM receipts")
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE kind = 'stage.receipt'")
        self.jobs._connection.execute("UPDATE jobs SET input_digest = ?",
                                      (OTHER_INPUT,))
        resumed = self.restart()
        with self.assertRaises(ContractRefusal) as caught:
            sweep(resumed, self.acts, now=SOON)
        refusal = caught.exception
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "operation-collision"))
        self.assertIn("input_digest", refusal.message)
        # NOT RECORDED AS ADOPTED, and not recorded at all.
        self.assertEqual(receipts_of(resumed, self.stage["stage_id"], 1), {})
        self.assertEqual(receipt_rows(resumed), [])

    def test_a_committed_act_this_intent_does_own_is_still_adopted(self):
        """The ordinary performed-but-unrecorded path, unchanged by the proof.

        Kept beside the refusal above because a check that refused everything
        would also pass that one, and the whole value of this correction is
        that a genuine restart still reconciles.
        """
        sweep(self.jobs, self.acts, now=NOW)
        self.jobs._connection.execute("DELETE FROM receipts")
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE kind = 'stage.receipt'")
        resumed = self.restart()
        report = sweep(resumed, self.acts, now=SOON)
        self.assertEqual(report["acts"][0]["outcome"], "adopted")
        self.assertEqual(len(self.minted), 1)

    def test_reconcile_runs_the_managers_own_restart_recovery_first(self):
        sweep(self.jobs, self.acts, now=NOW)
        resumed = self.restart()
        # A DIFFERENT MANAGER INCARNATION is what makes an undelivered offer
        # abandonable; the rule is the manager's and this leaf only reports
        # what it answered.
        other = ManagerOperations(
            self.control(incarnation="manager-2"),
            AuthorityPort(self.session, fake_claim_signature),
            mint_bearer=self.mint, deliver_bearer=self.deliver)
        report = reconcile(resumed, other, now=SOON)
        self.assertEqual(report["recovered"]["abandoned"],
                         [self.stage["offer_id"]])
        self.assertEqual(report["observed_at"], SOON)


class OneControlStoreAndTwoJobStores(JobManagerCase):
    """Review [P1]: the reproduction that refused the first candidate.

    The CLI selects `--store` and `--control` independently, so two Job stores
    over one control store is a deployment an operator can reach without doing
    anything unusual. Both derive `offer:job-a/implementation` from the Job id
    and the stage kind, so the SECOND store finds the FIRST store's committed
    offer under a name it built itself. Adopting it made one operation id two
    accounts of intent: the measured sweep answered `admit/adopted` and then
    projected its own input digest beside an offer whose signature carried only
    the other one's.

    These cases drive the real operations, because the whole mechanism is what
    the manager actually journalled.
    """

    def setUp(self):
        super().setUp()
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)
        self.first = self.store(incarnation="jobs-a")
        submit(self.first, submission(jobs=[job("job-a")]))
        sweep(self.first, self.acts, now=NOW)

    def other(self, jobs):
        """A second Job store, sharing nothing with the first but the control
        store and, where a case wants the collision, a Job identity."""
        store = JobStore.open(os.path.join(self.root, "jobs-b.sqlite3"),
                              authority_uuid=UUID, incarnation="jobs-b",
                              clock=self.clock)
        self.addCleanup(store.close)
        submit(store, submission(submission_id="sub-2", jobs=jobs))
        return store

    def colliding(self):
        return self.other([job("job-a", input_digest=OTHER_INPUT)])

    def test_a_second_store_cannot_adopt_the_first_stores_offer(self):
        other = self.colliding()
        with self.assertRaises(ContractRefusal) as caught:
            sweep(other, self.acts, now=SOON)
        refusal = caught.exception
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "operation-collision"))
        # BOTH ACCOUNTS ARE NAMED, so an operator reading the refusal can tell
        # which store the offer belongs to. `name_value` elides a long value,
        # so the assertion is on the part it keeps.
        self.assertIn("input_digest", refusal.message)
        self.assertIn(OTHER_INPUT[:40], refusal.message)
        self.assertIn(("sha256:" + "1" * 64)[:40], refusal.message)
        # NOT RECORDED AS `adopted`, and nothing was performed either: no
        # second bearer, and the one offer the first store issued is still the
        # only one the manager holds.
        self.assertEqual(receipt_rows(other), [])
        self.assertEqual(len(self.minted), 1)
        self.assertEqual(
            self.control_store._connection.execute(
                "SELECT count(*) FROM offers").fetchone()[0], 1)

    def test_the_second_stores_status_refuses_rather_than_projecting_it(self):
        """AND NOT PROJECTED BESIDE THE NEW INTENT.

        A refusal during the sweep would not be enough on its own: `status` is
        a separate entry point and it reads the same canonical facts, so an
        operator running it against the mis-paired store would have been shown
        this store's Job wearing the other store's offer.
        """
        other = self.colliding()
        with self.assertRaises(ContractRefusal) as caught:
            status(other, self.acts, observed_at=SOON)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_two_stores_that_name_different_jobs_do_not_collide(self):
        """The proof is about INTENT, not about sharing a control store.

        Two Job stores over one control store is not by itself the defect, and
        a correction that refused it would break a deployment the CLI's own
        operands describe.
        """
        other = self.other([job("job-b",
                                stages=[stage("implementation", WORK_C)])])
        report = sweep(other, self.acts, now=SOON)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]], [("admit", "performed")])
        self.assertEqual(len(self.minted), 2)


class WindowLoser(FakeOperations):
    """The foreign commit lands inside `_delegate`'s read/call window.

    Every read this store makes BEFORE the delegated call answers absence, and
    the other store's offer appears while the call is in flight. That is what a
    second Job manager racing this one looks like from in here, and `refusing`
    picks which answer the canonical operation then gives: `issue_offer`
    refuses `operation-collision` when the derived identity is already taken,
    and a build that proved only the refusal path would still take the row a
    RETURNING call left behind.
    """

    def __init__(self, intent, *, refusing=True):
        super().__init__()
        self._intent = intent
        self._refusing = refusing

    def admit(self, stage, job):
        self.calls.append(("admit", stage["stage_id"]))
        self.committed("admit", stage["offer_id"], intent=self._intent)
        if self._refusing:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"operation {stage['offer_id']} is already recorded with a "
                f"different kind or signature")
        return None


class LateWinner(FakeOperations):
    """The foreign commit lands between the projection pass and the adoption.

    `stage_states` proves the binding for every stage, and `_adopt` then reads
    the journal for each act that has no receipt. Answering the FIRST read with
    absence and committing immediately afterwards puts the foreign row exactly
    where a build that inherited the earlier proof would take it as settled.
    """

    def __init__(self, intent):
        super().__init__()
        self._pending = intent

    def receipt_of(self, operation_id):
        record = super().receipt_of(operation_id)
        if (record is None and self._pending is not None
                and operation_id.startswith("offer.issue:")):
            # ANSWERED ABSENCE, THEN COMMITTED. Every later read in this same
            # sweep now sees a row the earlier one did not.
            self.committed("admit", operation_id.split(":", 1)[1],
                           intent=self._pending)
            self._pending = None
        return record


class TheReadCallWindow(JobManagerCase):
    """Re-review [P1]: a foreign offer that commits AFTER the proof read.

    `OneControlStoreAndTwoJobStores` above is the case where the other store
    got there first and every read in this store's sweep already sees its row.
    THIS is the other half. The reads that decided what to do returned absence
    -- which is the ordinary state of an unstarted stage and not evidence about
    anything -- and the foreign commit lands between one read and the next. The
    measured defect was that `sweep` then answered
    `{"act": "admit", "outcome": "performed"}` and this store durably recorded
    the other store's operation as its own act.

    THE SEAM IS DETERMINISTIC ON PURPOSE. The window is microseconds wide, so
    two racing processes would reproduce this only sometimes -- and a
    regression that fails only sometimes is not a regression. These classes put
    the commit at the exact instant that matters and leave everything else the
    ordinary fake.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.stage = self.attempting(self.jobs)
        self.job = job_of(self.jobs, "job-a")
        self.operation_id = canonical_operation("admit",
                                                self.stage["offer_id"])

    def foreign(self):
        """Another store's intent under this store's derived identity."""
        held = dict(stage_intent(self.stage, self.job))
        held["input_digest"] = OTHER_INPUT
        return held

    def refuses_the_window(self, acts):
        with self.assertRaises(ContractRefusal) as caught:
            sweep(self.jobs, acts, now=NOW)
        refusal = caught.exception
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "operation-collision"))
        self.assertIn("input_digest", refusal.message)
        # THE ROW IS THERE, so this is a proof refusing a foreign act rather
        # than a read that happened to find nothing.
        self.assertIsNotNone(acts.receipt_of(self.operation_id))
        # AND NONE OF IT REACHED THIS STORE: no receipt for the act, and no
        # outcome reported for it either -- the sweep raised instead of
        # answering.
        self.assertEqual(receipts_of(self.jobs, self.stage["stage_id"], 1), {})
        self.assertEqual(receipt_rows(self.jobs), [])

    def test_a_foreign_offer_winning_a_refused_call_is_not_performed(self):
        self.refuses_the_window(WindowLoser(self.foreign()))

    def test_a_foreign_offer_winning_a_returning_call_is_not_performed(self):
        """The same window, with the canonical call answering normally.

        A build that proved only the row it read after a REFUSAL would pass the
        case above and still record this one, so both answers are driven.
        """
        self.refuses_the_window(WindowLoser(self.foreign(), refusing=False))

    def test_a_foreign_offer_winning_before_the_adoption_read_is_not_adopted(self):
        """The same window one pass earlier, where it is `adopted` not
        `performed`.

        Nothing is delegated here at all: the projection proved absence, the
        adoption read found the foreign row, and a build that rested on that
        earlier proof would write a receipt saying this Job's offer was already
        issued.
        """
        acts = LateWinner(self.foreign())
        self.refuses_the_window(acts)
        self.assertEqual(acts.calls, [],
                         "the adoption pass performs nothing; the refusal is "
                         "about the row it read, not about an act it tried")

    def test_this_stores_own_offer_arriving_in_the_window_is_still_recorded(self):
        """THE PROOF IS ABOUT INTENT, NOT ABOUT THE WINDOW.

        A correction that refused any row appearing after its read would pass
        every case above and break the ordinary crash-recovery path this leaf
        exists for. So the same seam commits THIS store's own intent, and the
        act is recorded exactly as it was before.
        """
        acts = WindowLoser(stage_intent(self.stage, self.job))
        report = sweep(self.jobs, acts, now=NOW)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]], [("admit", "performed")])
        held = receipts_of(self.jobs, self.stage["stage_id"], 1)["admit"]
        self.assertEqual(held["state"], "performed")
        self.assertEqual(held["operation_id"], self.operation_id)


FOREIGN_OFFER = "offer:foreign-job/implementation"


class TwoOffersOneAttempt(JobManagerCase):
    """Re-review [P1, 2026-09-03]: two offers naming ONE attempt id.

    The classes above are about one derived OFFER id meaning two intents, and
    the proof that closed them compares what `issue_offer` signed. This is the
    other identity. The attempt id is deterministically derived from the Job
    id and stage kind exactly as the offer id is, and the manager holds ONE
    claimed offer per attempt -- so a distinct canonical offer, issued for
    another Work and proving nothing about this store, can take the slot this
    stage's own claim was going to take.

    The intent proof cannot see it and should not: it is keyed by THIS store's
    offer id, and this store's offer really is its own. What was unqualified
    was the read beside it. The measured defect is `status` reporting `claimed`
    for a stage whose Job store holds only its `admit` receipt, and it is
    DURABLE rather than a one-read anomaly -- a claimed stage owes nothing, so
    the next sweep asked for nothing and nothing came back to correct it.

    THIS IS THE WINDOW CASE TOO, and it needs no seam to be one. Every read
    this store makes is honest and current: `check_binding` re-reads the
    `offer.issue` row and passes, because that row is this store's act. The
    foreign fact arrives afterwards, at the very next read, which is exactly
    the ordering a deterministic seam would have to construct -- so the real
    two-store composition is the sharper regression.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.stage = self.attempting(self.jobs)
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)
        # This store's own offer, issued by an ordinary sweep. The stage is
        # `offered` from here on and its claim is the act it still owes.
        sweep(self.jobs, self.acts, now=NOW)

    def take_the_claim(self, offer_id, work_id, *, issue=None):
        """Carry one offer to the manager's claimed slot on THIS attempt."""
        if issue is not None:
            issue_offer(self.control_store, self.acts.port,
                        offer_id=offer_id, work_id=work_id,
                        runtime_attempt_id=self.stage["attempt_id"],
                        input_digest=issue, policy_digest=POLICY_DIGEST,
                        profile_digest=PROFILE, profile_name="reference",
                        mint_bearer=lambda: "foreign-bearer")
        accept_offer(self.control_store, self.acts.port, offer_id=offer_id,
                     decision="accept",
                     bearer=("foreign-bearer" if issue is not None
                             else self.delivered[-1]["bearer"]),
                     now=NOW,
                     runtime_attempt_id=self.stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": work_id})
        submit_claim(self.control_store, self.acts.port, offer_id=offer_id)

    def foreign_claim(self):
        """Another Work's offer, holding this stage's derived attempt id."""
        self.take_the_claim(FOREIGN_OFFER, WORK_C, issue=OTHER_INPUT)
        self.assertEqual(
            [row["offer_id"] for row in
             self.control_store._connection.execute(
                 "SELECT offer_id FROM offers WHERE runtime_attempt_id = ? "
                 "AND state = 'claimed'",
                 (self.stage["attempt_id"],)).fetchall()],
            [FOREIGN_OFFER],
            "the foreign offer holds the manager's claimed slot; without that "
            "there is nothing for this case to refuse")

    def refuses_the_holder(self, call):
        with self.assertRaises(ContractRefusal) as caught:
            call()
        refusal = caught.exception
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "operation-collision"))
        # BOTH OFFERS AND THE ATTEMPT ARE NAMED, so an operator reading the
        # refusal can tell which store the claim belongs to.
        self.assertIn(FOREIGN_OFFER, refusal.message)
        self.assertIn(self.stage["offer_id"][:32], refusal.message)
        self.assertIn(self.stage["attempt_id"][:32], refusal.message)
        return refusal

    def test_a_foreign_claim_on_this_attempt_is_not_projected_as_this_jobs(self):
        """The measured defect, at the entry point that reported it.

        `status` is where an operator saw `claimed`, and the reviewer's
        retained reproduction drives exactly this.
        """
        self.foreign_claim()
        self.refuses_the_holder(
            lambda: status(self.jobs, self.acts, observed_at=SOON))

    def test_a_foreign_claim_leaves_this_stages_own_claim_still_owed(self):
        """AND IT DOES NOT ANSWER AN ACT THIS JOB STILL OWES.

        This is the half that made the defect durable rather than transient.
        A claimed stage owes nothing, so the reviewed build derived an EMPTY
        owed set and every later sweep agreed with it; nothing was ever going
        to look again. The derivation must refuse instead of answering.
        """
        owed = [one["act"] for one in owed_acts(self.jobs, self.acts)]
        self.assertEqual(owed, ["claim"],
                         "before the collision this stage owes its claim")
        self.foreign_claim()
        self.refuses_the_holder(lambda: owed_acts(self.jobs, self.acts))
        self.refuses_the_holder(lambda: sweep(self.jobs, self.acts, now=SOON))

    def test_a_foreign_claim_writes_nothing_into_this_job_store(self):
        self.foreign_claim()
        self.refuses_the_holder(lambda: sweep(self.jobs, self.acts, now=SOON))
        # ONLY THE ADMIT THIS STORE REALLY PERFORMED. No claim receipt, and
        # nothing recording the other store's operation under any state.
        self.assertEqual([row["act"] for row in receipt_rows(self.jobs)],
                         ["admit"])
        self.assertEqual(
            sorted(receipts_of(self.jobs, self.stage["stage_id"], 1)), ["admit"])
        self.assertNotIn(
            FOREIGN_OFFER,
            str([dict(row) for row in receipt_rows(self.jobs)]))

    def test_this_stores_own_offer_taking_its_attempt_is_still_projected(self):
        """THE POSITIVE CONTROL, and the reason it is not optional.

        A correction that refused any claim found under this stage's attempt id
        would pass all three cases above and break the only path this leaf
        exists to walk. So the same attempt id, the same slot, and this store's
        OWN offer in it: the claim is performed, recorded, and projected.
        """
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]], [("claim", "deferred")],
                         "the worker has not accepted yet")
        self.take_the_claim(self.stage["offer_id"], WORK_A)
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]], [("claim", "adopted")])
        document = status(self.jobs, self.acts, observed_at=SOON)
        self.assertEqual(document["jobs"][0]["stages"][0]["state"], "claimed")
        self.assertEqual([row["act"] for row in receipt_rows(self.jobs)],
                         ["admit", "claim"])


class AnUnclaimedAttempt(JobManagerCase):
    """Attempt-keyed facts under an attempt NOTHING has bound to this stage.

    The claim is the only thing the manager holds that ties an attempt id to an
    offer: the runtime, the activity and the frozen result carry the attempt id
    and no offer at all. So a fact found under a derived attempt id that no
    claim answers for is not this stage's to report, whoever recorded it.

    Driven through the fake, because the point is what the projection does with
    an observation rather than how the manager came to hold one.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        sweep(self.jobs, self.acts, now=NOW)

    def test_a_runtime_under_an_unclaimed_attempt_is_not_this_stages(self):
        self.acts.observed(
            "job-a/implementation",
            runtime={"attempt_id": "attempt:job-a/implementation",
                     "runtime_id": "runtime-1",
                     "execution_runtime": "running", "cleanup": None,
                     "assignment": None})
        held = status(self.jobs, self.acts,
                      observed_at=NOW)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "offered",
                         "an unclaimed attempt does not make this stage run")
        self.assertIsNone(held["runtime"])

    def test_an_observation_this_build_cannot_read_is_refused_not_trusted(self):
        """The document is OWNED on the way in, like every other received one.

        A reader is supplied by the deployment, so its answer crosses a trust
        boundary; a member this build's contract does not name means the two
        do not agree about what an observation is, and reading the members it
        does recognise anyway is the assumption this ownership exists to stop.
        """
        for spoiled in ({"claimed": True}, {"claimed_by": None, "extra": 1}):
            with self.subTest(observation=spoiled):
                self.acts.observations["job-a/implementation"] = dict(spoiled)
                with self.assertRaises(ContractRefusal):
                    status(self.jobs, self.acts, observed_at=NOW)


class RecoveryIsTheManagers(JobManagerCase):

    def test_an_ordinary_sweep_reports_no_recovery(self):
        jobs = self.store()
        submit(jobs, submission(jobs=[job("job-a")]))
        acts = FakeOperations()
        self.assertIsNone(sweep(jobs, acts, now=NOW)["recovered"])
        self.assertEqual(acts.calls, [("admit", "job-a/implementation")])

    def test_reconcile_asks_the_manager_before_it_derives_anything(self):
        jobs = self.store()
        submit(jobs, submission(jobs=[job("job-a")]))
        acts = FakeOperations()
        reconcile(jobs, acts, now=NOW)
        self.assertEqual(acts.calls[0], ("recover", NOW))


if __name__ == "__main__":
    unittest.main()
