"""W316918 -- the tick that proves a stage finished is the tick that frees it.

THE RESIDUAL THIS ANSWERS, from a completed Job on the deployed instance
(`STATUS-COPY-316831.json`): the implementation allocation was `released` with
reason `cleanup-retained`, and the review allocation -- reserved six
milliseconds later, on a Job every reader called completed -- was still
`reserved` with `released_at` null, with no runtime alive and its cleanup
retained.  A deployment whose review lane holds one logical worker could
therefore run exactly one Job and then queue forever behind an attempt that
was over.

WHY IT SURVIVED THE EXISTING PROOFS.  `reconcile_allocations` was always
right: given a projection whose cleanup axis is terminal it releases the exact
allocation, and `test_scheduling` pins that rule from both sides.  What was
wrong was WHEN it was asked.  A sweep reconciled from a projection taken
BEFORE its own acts, and the cleanup axis becomes terminal INSIDE `conclude`
-- so the release was owed to a tick that had already looked, and landed on
the next one.  For every stage but the last that reads as a one-tick delay
nobody sees; for the last stage of a Job there is no next tick, because a
supervisor stops once its stages are completed.

SO THESE CASES ARE ABOUT THE ORDERING AND NOTHING ELSE.  The fake deployment
here settles the cleanup axis inside `conclude`, which is where the real
Worker Manager settles it; the negatives then pin that the second ask is the
SAME rule -- a running, unknown or unsettled cleanup is still held, and an
allocation already released is not released again.

`tests/tools/test_stage_execution.py` carries the other half over the real
composed runtime: there the completing tick IS the last one, which is the
shape the deployed residual was measured in.
"""

import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (POOL_SCHEMA, PooledManagerOperations,
                                   activate_pool, allocation_of,
                                   allocation_rows, submit, sweep)
from baton_v12.job_manager import scheduler

if __package__:
    from .fixtures import (LATER, NOW, PROFILE, UUID, FakeOperations,
                           JobManagerCase, job, stage, submission)
else:
    from fixtures import (LATER, NOW, PROFILE, UUID, FakeOperations,
                          JobManagerCase, job, stage, submission)

LAST = "one/review"


def worker(worker_id, lane, participant, kinds):
    return {"worker_id": worker_id, "lane": lane, "participant": participant,
            "profile_name": "reference", "profile_digest": PROFILE,
            "eligible_kinds": kinds}


def one_each():
    """One logical worker per lane, which is what makes capacity legible.

    A pool with spare workers would let a second Job start while the first
    one's allocation was still held, and the whole defect is that the held
    allocation is invisible until something needs the capacity.  With exactly
    one review worker, "did the last stage give its capacity back" and "can
    another Job run" are the same question.
    """
    return {"schema": POOL_SCHEMA, "variant": "primary",
            "separation_class": "provider-diverse",
            "workers": [worker("impl", "implementation", "baton.impl",
                               ["implementation", "integration"]),
                        worker("review", "review", "baton.review",
                               ["review"])]}


def principals(document):
    return {entry["participant"]: "principal:" + entry["worker_id"]
            for entry in document["workers"]}


class _Bound:
    """One participant-bound view of one shared fake deployment.

    Pooled attachment proves that each configured worker's operations act for
    that worker's participant, by reading `operations.port.participant`.  What
    these cases are about is settlement timing, not routing -- which is proved
    against four real participant-bound operations in `test_scheduling` -- so
    the two views share one fake's journal and observations, and only the
    participant differs.
    """

    def __init__(self, shared, participant, principal):
        self._shared = shared
        self.principal = principal
        self.port = type("_Port", (), {"participant": participant})()

    def __getattr__(self, name):
        return getattr(self._shared, name)

    def admit(self, stage, job):
        """Journal the offer under the intent the pooled boundary binds.

        `check_binding` compares the recorded admit intent against
        `PooledManagerOperations.binding_intent`, which carries the reserved
        participant.  A fake that signed the unbound stage intent would make
        every pooled adoption unreadable -- and that comparison is the one
        thing this fixture must not weaken, because it is what proves an
        offer belongs to the worker the scheduler reserved.
        """
        from baton_v12.job_manager.delegation import stage_intent

        return self._shared._act(
            "admit", stage, {"offer_id": stage["offer_id"],
                             "work_id": stage["work_id"]},
            intent=dict(stage_intent(stage, job),
                        participant=self.port.participant))

    def claim(self, stage):
        """Answer the claim with this worker's own resolved principal.

        The pooled boundary compares the returned principal against the one
        the allocation reserved and quarantines a mismatch.  That binding is
        proved for real in `test_scheduling`; here the worker answers as
        itself so these cases measure settlement rather than re-measuring it.
        """
        self._shared._act("claim", stage, {"offer_id": stage["offer_id"],
                                           "state": "claimed"})
        return {"decision": {"principal": self.principal}}


class _SettlesOnConclude(FakeOperations):
    """A fake deployment whose `conclude` settles the cleanup axis.

    THIS IS THE FIXTURE'S WHOLE CONTRIBUTION, and it is a fact about the real
    seam rather than a convenience.  In production the frozen output and the
    authorized cleanup are what `conclude` PRODUCES: the ending freezes the
    result, takes the intake receipt and authorizes cleanup, so the cleanup
    axis is `pending` when the tick begins and terminal when it ends.  A case
    that set a terminal cleanup before the tick would be describing the one
    state in which this defect cannot appear -- the tick's own pre-act
    projection would already have seen it.
    """

    def __init__(self):
        super().__init__()
        self.settles = {}

    def settling(self, stage_id, disposition="accepted", cleanup="complete"):
        """What this stage's ending will freeze, and where cleanup lands."""
        self.endings[stage_id] = {"ended": True}
        self.settles[stage_id] = (disposition, cleanup)

    def conclude(self, stage, job):
        answer = super().conclude(stage, job)
        held = self.settles.get(stage["stage_id"])
        if held is not None:
            disposition, cleanup = held
            self.frozen(stage["stage_id"], disposition,
                        execution_runtime="ended", cleanup=cleanup)
        return answer


class FinalAllocationCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.document = one_each()
        self.resolved = principals(self.document)
        activate_pool(self.jobs, self.document, self.resolved)
        self.acts = _SettlesOnConclude()

    def pooled(self):
        """Attachment re-read from the store, as a serving process does it.

        `PooledManagerOperations` validates the attachment against the live
        allocations AT CONSTRUCTION, so a case that reserved capacity after
        building one would be asserting against a stale proof.
        """
        return PooledManagerOperations(
            self.jobs,
            {(1, "impl"): _Bound(self.acts, "baton.impl",
                                 self.resolved["baton.impl"]),
             (1, "review"): _Bound(self.acts, "baton.review",
                                   self.resolved["baton.review"])},
            resolved_principals=self.resolved)

    def tick(self, now=NOW):
        return sweep(self.jobs, self.pooled(), now=now)

    def answering(self, job_id="one", cleanup="complete",
                  disposition="accepted"):
        """One stage driven to the moment before its ending, canonically.

        Every step is a real derived act: admit, claim, launch, dispatch, and
        then the worker's own terminal receipt.  Nothing here reaches into the
        allocation, so what the ending tick does to it is this fixture's
        answer rather than its assumption.
        """
        stage_id = f"{job_id}/review"
        submit(self.jobs, submission(f"sub-{job_id}", jobs=[
            job(job_id, stages=[stage("review", f"work:{job_id}")])]))
        self.acts.starts(stage_id, attaches=True)
        self.tick()                                     # admit
        self.tick()                                     # claim
        self.tick()                                     # launch
        self.tick()                                     # dispatch
        self.acts.commanded(stage_id, state="answered")
        self.acts.settling(stage_id, disposition, cleanup)
        return stage_id

    def allocation(self, stage_id=LAST):
        rows = [row for row in allocation_rows(self.jobs)
                if row["stage_id"] == stage_id]
        self.assertEqual(len(rows), 1, rows)
        return rows[0]

    def releases(self):
        return [row for row in self.jobs._connection.execute(
            "SELECT operation_id, state FROM operations "
            "WHERE kind = 'allocation.released' ORDER BY operation_id")]


class TheEndingTickReturnsTheCapacity(FinalAllocationCase):
    """The positive: one tick proves the stage finished and frees it."""

    def test_the_tick_that_concludes_the_last_stage_releases_its_allocation(self):
        stage_id = self.answering()
        self.assertEqual(self.allocation()["allocation_state"], "reserved")
        self.tick()
        held = self.allocation()
        self.assertEqual(held["allocation_state"], "released")
        self.assertEqual(held["release_reason"], "cleanup-complete")
        self.assertEqual(held["released_at"], NOW)
        self.assertEqual(held["stage_id"], stage_id)

    def test_the_release_names_the_allocation_the_ending_settled(self):
        """The assignment, not just "some allocation of this stage"."""
        self.answering()
        attempt = self.attempting(self.jobs, LAST)
        self.tick()
        settled = allocation_of(self.jobs, attempt["attempt_id"])
        self.assertEqual(settled["allocation_state"], "released")
        self.assertEqual(settled["assignment_id"], attempt["attempt_id"])
        self.assertEqual(settled["episode"], attempt["episode"])

    def test_a_retained_cleanup_frees_it_too_and_says_which(self):
        """RETAINED IS PROVEN CESSATION.  The runtime is over and the
        workspace was deliberately kept for evidence; the reason carries that
        distinction forward rather than claiming the container was destroyed.
        """
        self.answering(cleanup="retained")
        self.tick()
        self.assertEqual(self.allocation()["release_reason"],
                         "cleanup-retained")

    def test_no_new_capacity_rule_appears_in_the_report(self):
        """The sweep document is unchanged.  A release is visible where a
        reader already looks for it -- the allocation's own state, instant and
        reason -- and the settlement is not a second account of an act."""
        self.answering()
        report = self.tick()
        self.assertNotIn("settled", report)
        self.assertEqual(sorted(report),
                         ["acts", "observed", "observed_at", "recovered",
                          "refreshed", "replaced", "spoken", "started"])


class TheSettlementHappensExactlyOnce(FinalAllocationCase):

    def test_later_ticks_do_not_release_it_again(self):
        self.answering()
        self.tick()
        first = self.allocation()
        for index in range(3):
            with self.subTest(tick=index + 1):
                self.tick(LATER)
                held = self.allocation()
                self.assertEqual(held["allocation_state"], "released")
                # THE INSTANT IS THE EVIDENCE: a second release would restamp
                # it with the later tick's clock.
                self.assertEqual(held["released_at"], first["released_at"])
                self.assertEqual(held["release_reason"],
                                 first["release_reason"])
        self.assertEqual([row["operation_id"] for row in self.releases()],
                         [f"allocation.released:{first['assignment_id']}"])

    def test_a_restart_after_the_release_settles_nothing_further(self):
        """A new incarnation over the same store, which is how a sweep is
        really repeated: the journal is the only thing that remembers."""
        self.answering()
        self.tick()
        before = self.allocation()
        self.jobs.close()
        self.jobs = self.store(incarnation="jobs-2")
        self.tick(LATER)
        held = self.allocation()
        self.assertEqual(held["released_at"], before["released_at"])
        self.assertEqual(len(self.releases()), 1)
        self.assertEqual(self.releases()[0]["state"], "committed")

    def test_the_settled_assignment_is_never_reserved_again(self):
        """Freed capacity is not a re-runnable attempt.  A released
        assignment's reservation refuses durably, so nothing about returning
        capacity reopens an episode that is over."""
        self.answering()
        attempt = self.attempting(self.jobs, LAST)
        self.tick()
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.reserve(self.jobs, attempt)
        self.assertTrue(caught.exception.durable)


class TheFreedCapacityServesTheNextJob(FinalAllocationCase):
    """What the residual actually cost: the next Job could not start."""

    def test_a_later_independent_job_takes_the_released_worker(self):
        self.answering("one")
        first = self.allocation()
        self.tick()
        self.assertEqual(self.allocation()["allocation_state"], "released")
        submit(self.jobs, submission("sub-two", jobs=[
            job("two", stages=[stage("review", "work:two")])]))
        self.tick(LATER)
        second = self.allocation("two/review")
        self.assertEqual(second["allocation_state"], "reserved")
        self.assertEqual(second["worker_id"], first["worker_id"])
        self.assertEqual(second["participant"], first["participant"])

    def test_the_same_job_queued_behind_a_held_allocation_is_the_defect(self):
        """The negative that proves the case above measures something.

        While the finished attempt still holds the only review worker, the
        next Job's admission cannot reserve -- which is exactly what the
        deployed instance would have done on its second Job.
        """
        self.answering("one", cleanup="pending")
        self.tick()
        self.assertEqual(self.allocation()["allocation_state"], "reserved")
        submit(self.jobs, submission("sub-two", jobs=[
            job("two", stages=[stage("review", "work:two")])]))
        self.tick(LATER)
        self.assertEqual([row["stage_id"] for row in allocation_rows(self.jobs)],
                         [LAST])


class AnUnprovenEndingKeepsItsCapacity(FinalAllocationCase):
    """The second ask is the SAME rule.  Nothing below is proven cessation."""

    def held(self, **members):
        self.answering(**members)
        self.tick()
        row = self.allocation()
        self.assertEqual(row["allocation_state"], "reserved")
        self.assertIsNone(row["released_at"])
        self.assertIsNone(row["release_reason"])

    def test_an_unsettled_cleanup_is_held(self):
        self.held(cleanup="pending")

    def test_an_unknown_cleanup_is_held(self):
        """Silence about cleanup is not a claim that it happened."""
        self.held(cleanup=None)

    def test_a_running_cleanup_is_held(self):
        self.held(cleanup="running")

    def test_a_changes_requested_ending_settles_on_its_own_cleanup(self):
        """The disposition is not the axis.  A stage that asked for changes
        has finished its attempt exactly as much as an accepted one, and what
        decides the release is cleanup either way."""
        self.answering(disposition="changes-requested")
        self.tick()
        self.assertEqual(self.allocation()["release_reason"],
                         "cleanup-complete")

    def test_a_live_runtime_with_a_terminal_cleanup_is_still_settled(self):
        """AND THE HOLD IS NOT WIDENED EITHER.  `reconcile_allocations` reads
        the cleanup axis and not the execution axis, and this second ask does
        not invent a stricter test than the first one -- a stricter rule here
        would be a new scheduling policy smuggled in as a bug fix.
        """
        stage_id = self.answering()
        self.acts.settling(stage_id, "accepted", "complete")
        self.tick()
        self.assertEqual(self.allocation()["allocation_state"], "released")


if __name__ == "__main__":
    unittest.main()
