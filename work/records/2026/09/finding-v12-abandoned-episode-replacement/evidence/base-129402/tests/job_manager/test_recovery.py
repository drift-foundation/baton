"""W73629 — a stage whose offer ended, and the episode that replaces it.

THE DEFECT, IN ONE SENTENCE. A different Worker Manager incarnation abandons
an `issued` offer because nothing durable proves its bearer was delivered; the
Job manager kept that stage's `admit` receipt, went on projecting `offered`,
and owed `claim` against an offer that no longer existed. One restart wedged
the stage permanently, and no later tick could notice, because a stage that
already looks offered owes nothing that would ask.

WHAT THESE CASES DRIVE. The real Worker Manager wherever the fact under test
is a canonical one -- what recovery actually does to an offer row is the whole
premise, and a fake that abandoned it by construction would prove nothing. The
fake is used where the fact under test is the CONSUMER's: at-least-once
delivery, republication, stale revisions and the pump's re-entrancy rules are
properties of this side of the seam, and constructing them for real would mean
racing two processes to reproduce something deterministically stated here.
"""

import os
import sqlite3
import sys
import unittest

# THE DISTRIBUTION ROOT, NAMED FROM THIS FILE, exactly as `test_tool` names it.
# `tools` is repository tooling rather than part of the wheel, so the read-only
# status surface is importable only when the distribution root is on
# `sys.path`. Doing it here rather than relying on `test_tool` having been
# imported first is what stops this file's verdict from depending on discovery
# order.
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import ContractRefusal
from baton_v12.eventing import EventQueue, pump
from baton_v12.job_manager import (JobStore, ManagerOperations,
                                   apply_offer_state, episodes_of, live_of,
                                   owed_acts, receipt_rows, receipts_of,
                                   reconcile, stage_rows, status, submit,
                                   sweep)
from baton_v12.job_manager.episodes import identities
from baton_v12.worker_manager import AuthorityPort, accept_offer
from baton_v12.worker_manager.events import (OFFER_STATE_KIND,
                                             STATE_REVISIONS,
                                             offer_state_revision,
                                             publish_offer_states)

if __package__:
    from .fixtures import (NOW, SOON, UUID, WORK_A, FakeOperations,
                           JobManagerCase, fake_claim_signature, job,
                           submission)
else:
    from fixtures import (NOW, SOON, UUID, WORK_A, FakeOperations,
                          JobManagerCase, fake_claim_signature, job,
                          submission)

STAGE = "job-a/implementation"
FIRST_OFFER, FIRST_ATTEMPT = identities(UUID, STAGE, 1)
SECOND_OFFER, _SECOND_ATTEMPT = identities(UUID, STAGE, 2)
ABANDONED = "abandoned-after-restart"


def assertion(offer_id, attempt_id, state):
    """One `offer.state` document, spelled the way the publisher spells it."""
    return {"kind": OFFER_STATE_KIND, "offer_id": offer_id,
            "attempt_id": attempt_id, "state": state,
            "revision": offer_state_revision(state)}


class TheRealRestart(JobManagerCase):
    """The reproduction that opened this Work, and what it does now.

    Every fact here is canonical: a real `issue_offer` under one manager
    incarnation, a real `recover_on_restart` under another, and the real
    offers table read back. The reproduction is
    `/tmp/w71877-abandoned-offer-repro.py`.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.first = self.operations(control=self.control())
        sweep(self.jobs, self.first, now=NOW)

    def resume(self, incarnation="manager-2"):
        """A new Job manager incarnation over a new manager incarnation.

        A DIFFERENT MANAGER INCARNATION is what makes an undelivered offer
        abandonable; the rule is the manager's and this leaf only consumes
        what it answered.
        """
        self.jobs.close()
        self.jobs = JobStore.open(self.job_path, authority_uuid=UUID, incarnation="jobs-2",
                                  clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.acts = ManagerOperations(
            self.control(incarnation=incarnation),
            AuthorityPort(self.session, fake_claim_signature),
            mint_bearer=self.mint, deliver_bearer=self.deliver)
        return self.jobs

    def offer_states(self):
        return {row["offer_id"]: row["state"] for row in
                self.first.control._connection.execute(
                    "SELECT offer_id, state FROM offers")}

    def test_the_abandoned_stage_becomes_admissible_again(self):
        resumed = self.resume()
        report = reconcile(resumed, self.acts, now=SOON)
        # THE PREMISE, ASSERTED RATHER THAN ASSUMED: the manager really did
        # abandon it, so this case is about recovering from that rather than
        # about a condition the fixture arranged.
        self.assertEqual(report["recovered"]["abandoned"], [FIRST_OFFER])
        self.assertEqual(self.offer_states()[FIRST_OFFER], ABANDONED)
        # ONE assertion applied, ONE episode replaced, and the fresh episode's
        # own admit performed in the SAME tick.
        self.assertEqual(report["observed"], 1)
        self.assertEqual([(one["stage_id"], one["episode"])
                          for one in report["replaced"]], [(STAGE, 2)])
        self.assertEqual([(one["act"], one["outcome"], one["episode"])
                          for one in report["acts"]], [("admit", "performed",
                                                        2)])
        # AND THE STAGE IS OFFERED AGAINST A LIVE OFFER. Before this Work it
        # was offered against a terminal one, which is the whole difference.
        self.assertEqual(self.offer_states()[SECOND_OFFER], "issued")
        self.assertEqual([one["act"] for one in
                          owed_acts(resumed, self.acts)], ["claim"])

    def test_the_abandoned_episode_stays_auditable_beside_the_fresh_one(self):
        resumed = self.resume()
        reconcile(resumed, self.acts, now=SOON)
        history = episodes_of(resumed, STAGE)
        self.assertEqual([(one["episode"], one["offer_id"],
                           one["ended_state"]) for one in history],
                         [(1, FIRST_OFFER, ABANDONED),
                          (2, SECOND_OFFER, None)])
        # NOTHING WAS REWRITTEN. The abandoned episode keeps the admit receipt
        # it really earned, and the fresh one has its own.
        self.assertEqual(sorted(receipts_of(resumed, STAGE, 1)), ["admit"])
        self.assertEqual(sorted(receipts_of(resumed, STAGE, 2)), ["admit"])
        self.assertEqual([(row["episode"], row["act"], row["operation_id"])
                          for row in receipt_rows(resumed)],
                         [(1, "admit", f"offer.issue:{FIRST_OFFER}"),
                          (2, "admit", f"offer.issue:{SECOND_OFFER}")])

    def test_the_identities_of_the_fresh_episode_are_all_distinct(self):
        resumed = self.resume()
        reconcile(resumed, self.acts, now=SOON)
        first, second = episodes_of(resumed, STAGE)
        self.assertNotEqual(first["offer_id"], second["offer_id"])
        self.assertNotEqual(first["attempt_id"], second["attempt_id"])
        # AND THE ASSIGNMENT IS DISTINCT TOO, which is the manager's own fact
        # rather than this store's claim about it: the offer froze a different
        # runtime attempt, so nothing the first episode authorized can be
        # spent by the second.
        frozen = {row["offer_id"]: row["runtime_attempt_id"] for row in
                  self.acts.control._connection.execute(
                      "SELECT offer_id, runtime_attempt_id FROM offers")}
        self.assertEqual(frozen[FIRST_OFFER], first["attempt_id"])
        self.assertEqual(frozen[SECOND_OFFER], second["attempt_id"])
        self.assertNotEqual(frozen[FIRST_OFFER], frozen[SECOND_OFFER])

    def test_status_shows_the_abandoned_episode_beside_the_current_one(self):
        resumed = self.resume()
        reconcile(resumed, self.acts, now=SOON)
        held = status(resumed, self.acts,
                      observed_at=SOON)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "offered")
        # The CURRENT attempt is named as current...
        self.assertEqual(held["episode"], 2)
        self.assertEqual(held["offer_id"], SECOND_OFFER)
        # ...and the abandoned one is history rather than absence.
        self.assertEqual([(one["episode"], one["ended_state"])
                          for one in held["episodes"]],
                         [(1, ABANDONED), (2, None)])
        self.assertEqual([one["episode"] for one in held["receipts"]], [2],
                         "the receipts shown are the current episode's; the "
                         "abandoned one's live in its episode entry")

    def test_a_second_restart_reconciles_without_a_third_episode(self):
        """IDEMPOTENT ACROSS RESTARTS, which is the property that makes this
        recovery rather than a loop that re-offers every time it looks."""
        resumed = self.resume()
        reconcile(resumed, self.acts, now=SOON)
        minted = len(self.minted)
        # The SAME manager incarnation this time, so its own issued offer is
        # not abandonable and nothing new should end.
        again = reconcile(resumed, self.acts, now=SOON)
        self.assertEqual(again["recovered"]["abandoned"], [])
        self.assertEqual(again["replaced"], [])
        self.assertEqual([one["episode"] for one in episodes_of(resumed,
                                                                STAGE)],
                         [1, 2])
        self.assertEqual(len(self.minted), minted,
                         "no second bearer; the fresh offer already exists "
                         "and the sweep adopts rather than re-issues")

    def claim_it(self):
        """Carry this stage's own offer to a real canonical claim."""
        stage = self.attempting(self.jobs)
        accept_offer(self.first.control, self.first.port,
                     offer_id=stage["offer_id"], decision="accept",
                     bearer=self.delivered[-1]["bearer"], now=NOW,
                     runtime_attempt_id=stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        resumed = self.resume()
        reconcile(resumed, self.acts, now=SOON)
        return resumed

    def test_a_claimed_stage_survives_another_restart(self):
        """Review [P1, 2026-09-03]: A TERMINAL OFFER IS NOT A TERMINAL STAGE.

        `claimed` is terminal for the offer and is the ending that means the
        stage is RUNNING. Treating the offer's whole terminal set as episode
        endings ended the episode on success: the measured second restart
        answered `exceptional` with episode, offer and attempt all null, and
        stopped observing the very attempt the claim had just authorized. A
        stage that was working, broken by the machinery meant to recover the
        ones that were not.

        TWO restarts, because one is not the case. The first performs the
        claim; it is the SECOND attachment -- which republishes canonical
        `claimed` -- that used to destroy it.
        """
        resumed = self.claim_it()
        before = status(resumed, self.acts,
                        observed_at=SOON)["jobs"][0]["stages"][0]
        self.assertEqual(before["state"], "claimed")
        self.assertEqual(self.offer_states()[FIRST_OFFER], "claimed")

        again = self.resume(incarnation="manager-3")
        report = reconcile(again, self.acts, now=SOON)
        after = status(again, self.acts,
                       observed_at=SOON)["jobs"][0]["stages"][0]
        # THE SAME EXECUTION, still identified and still observed.
        self.assertEqual(after["state"], "claimed")
        self.assertEqual((after["episode"], after["offer_id"],
                          after["attempt_id"]),
                         (before["episode"], before["offer_id"],
                          before["attempt_id"]))
        # The episode is still LIVE, so nothing was ended and nothing replaced.
        self.assertEqual([(one["episode"], one["ended_state"])
                          for one in after["episodes"]], [(1, None)])
        self.assertEqual(report["replaced"], [])
        self.assertEqual(len(self.minted), 1, "no second offer was minted")

    def test_an_accepted_offer_is_recovered_and_never_replaced(self):
        """THE CASE A BLUNTER CORRECTION WOULD BREAK.

        Acceptance froze this offer's authorization and its claim operation,
        so the manager keeps it recoverable across a restart. Replacing it
        would throw away a claim the worker is entitled to take -- and would
        do it precisely when the pipeline was working.
        """
        stage = self.attempting(self.jobs)
        accept_offer(self.first.control, self.first.port,
                     offer_id=stage["offer_id"], decision="accept",
                     bearer=self.delivered[-1]["bearer"], now=NOW,
                     runtime_attempt_id=stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        resumed = self.resume()
        report = reconcile(resumed, self.acts, now=SOON)
        self.assertEqual(report["recovered"]["abandoned"], [])
        self.assertEqual([one["offer_id"] for one in
                          report["recovered"]["recoverable"]], [FIRST_OFFER])
        self.assertEqual(report["replaced"], [])
        self.assertEqual([one["episode"] for one in episodes_of(resumed,
                                                                STAGE)], [1])
        self.assertEqual(live_of(resumed, STAGE)["offer_id"], FIRST_OFFER)
        # AND THE CLAIM IT FROZE IS THE ACT THAT FOLLOWS, on episode 1.
        self.assertEqual([(one["act"], one["outcome"], one["episode"])
                          for one in report["acts"]],
                         [("claim", "performed", 1)])


class AClaimedStageGatesItsSuccessor(JobManagerCase):
    """AND THE STAGE STILL CONTROLS WHAT DEPENDS ON IT.

    Review [P1, 2026-09-03]'s damage does not stop at one row. A dependency
    gate opens only on `completed`, so a claimed stage wrongly reported
    `exceptional` is a gate that will never open -- the successor is held
    forever by a predecessor that is actually running fine. This drives the
    fixture's default two-stage submission, where the review stage gates on the
    implementation stage, through the same two restarts.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission())
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)
        sweep(self.jobs, self.acts, now=NOW)

    def test_the_successor_is_held_by_a_claim_that_is_still_a_claim(self):
        stage = self.attempting(self.jobs)
        accept_offer(self.control_store, self.acts.port,
                     offer_id=stage["offer_id"], decision="accept",
                     bearer=self.delivered[0]["bearer"], now=NOW,
                     runtime_attempt_id=stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        for incarnation in ("manager-2", "manager-3"):
            self.jobs.close()
            self.jobs = JobStore.open(self.job_path, authority_uuid=UUID, incarnation=incarnation,
                                      clock=self.clock)
            self.addCleanup(self.jobs.close)
            self.acts = ManagerOperations(
                self.control(incarnation=incarnation),
                AuthorityPort(self.session, fake_claim_signature),
                mint_bearer=self.mint, deliver_bearer=self.deliver)
            reconcile(self.jobs, self.acts, now=SOON)
        held = {one["stage_id"]: one for one in
                status(self.jobs, self.acts,
                       observed_at=SOON)["jobs"][0]["stages"]}
        self.assertEqual(held[STAGE]["state"], "claimed")
        self.assertEqual(held[STAGE]["offer_id"], FIRST_OFFER)
        review = held["job-a/review"]
        self.assertEqual(review["state"], "blocked")
        self.assertEqual([(one["stage_id"], one["state"], one["open"])
                          for one in review["gates"]],
                         [(STAGE, "claimed", False)])


class DeliveryIsAtLeastOnce(JobManagerCase):
    """Losing, repeating and replaying one canonical assertion.

    These are the consumer's own properties, so they are driven through the
    consumer's own handler with assertions spelled exactly as the publisher
    spells them. Racing two real processes to drop a message would reproduce
    this only sometimes, and a regression that fails only sometimes is not one.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.canonical_state(FIRST_OFFER, FIRST_ATTEMPT, ABANDONED)

    def test_a_lost_delivery_is_repaired_by_the_next_attachment(self):
        """THE WHOLE POINT OF PUBLISHING A LEVEL RATHER THAN AN EDGE.

        Nothing is delivered at all here -- the transport is emptied without
        dispatching, which is what a dropped message, a queue lost with a
        process, or a consumer that was not listening yet all look like. The
        stage stays wedged for exactly as long as nobody attaches, and one
        attachment repairs it. A transition NOTICE would have been consumed by
        the drop and there would be nothing left to ask.
        """
        self.acts.attach([FIRST_OFFER])
        self.acts.events._take()                      # the delivery is lost
        self.assertEqual(self.acts.drain({}), 0)
        self.assertIsNone(live_of(self.jobs, STAGE)["ended_state"])
        report = sweep(self.jobs, self.acts, now=SOON, attach=True)
        self.assertEqual(report["observed"], 1)
        self.assertEqual([one["episode"] for one in report["replaced"]], [2])

    def test_the_same_assertion_twice_has_the_effect_of_one(self):
        held = assertion(FIRST_OFFER, FIRST_ATTEMPT, ABANDONED)
        first = apply_offer_state(self.jobs, held)
        self.assertEqual(first["ended_state"], ABANDONED)
        # The second answers "nothing changed" and the row is untouched --
        # same ending, same instant, nothing appended.
        self.assertIsNone(apply_offer_state(self.jobs, dict(held)))
        self.assertEqual([dict(one) for one in episodes_of(self.jobs, STAGE)],
                         [dict(one) for one in [first]])

    def test_two_callers_applying_one_assertion_commit_one_ending(self):
        """The journalled identity, which is what covers the CONCURRENT case.

        Both callers read a live episode before either wrote, so neither takes
        the "already ended" path above; what stops the second from writing a
        second ending is the operation identity, which replays the first's
        committed document byte for byte.
        """
        from baton_v12.job_manager.episodes import end_episode

        episode = live_of(self.jobs, STAGE)
        revision = offer_state_revision(ABANDONED)
        first = end_episode(self.jobs, episode, ABANDONED, revision)
        self.assertEqual(end_episode(self.jobs, episode, ABANDONED, revision),
                         first)
        self.assertEqual(len(episodes_of(self.jobs, STAGE)), 1)

    def test_a_different_ending_for_one_episode_refuses(self):
        """One offer reaches one ending, so two assertions are a disagreement.

        Keeping the first by arrival order would decide it silently, and the
        thing being decided is which offer this episode actually asked for.
        """
        apply_offer_state(self.jobs, assertion(FIRST_OFFER, FIRST_ATTEMPT,
                                               ABANDONED))
        with self.assertRaises(ContractRefusal) as caught:
            apply_offer_state(self.jobs, assertion(FIRST_OFFER, FIRST_ATTEMPT,
                                                   "expired"))
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual([one["ended_state"] for one in
                          episodes_of(self.jobs, STAGE)], [ABANDONED])

    def test_periodic_republication_after_the_replacement_changes_nothing(self):
        sweep(self.jobs, self.acts, now=NOW, attach=True)
        self.assertEqual([one["episode"] for one in
                          episodes_of(self.jobs, STAGE)], [1, 2])
        before = [dict(one) for one in episodes_of(self.jobs, STAGE)]
        # The publisher is still asserting the same thing about the ended
        # offer, on a timer, forever. It must not mint a third episode.
        for _ in range(3):
            self.acts.attach([FIRST_OFFER])
            self.acts.drain({OFFER_STATE_KIND:
                             lambda event: apply_offer_state(self.jobs,
                                                             event)})
            sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([dict(one) for one in episodes_of(self.jobs, STAGE)],
                         before)

    def test_a_live_assertion_about_an_ended_offer_does_not_regress_it(self):
        """A STALE LOWER REVISION, which is what an out-of-order delivery is.

        `issued` ranks below every ending, so an assertion that arrives late
        saying the offer is still live must not un-end the episode or take the
        replacement's place.
        """
        apply_offer_state(self.jobs, assertion(FIRST_OFFER, FIRST_ATTEMPT,
                                               ABANDONED))
        sweep(self.jobs, self.acts, now=NOW)
        stale = assertion(FIRST_OFFER, FIRST_ATTEMPT, "issued")
        self.assertLess(stale["revision"],
                        offer_state_revision(ABANDONED))
        self.assertIsNone(apply_offer_state(self.jobs, stale))
        self.assertEqual([(one["episode"], one["ended_state"])
                          for one in episodes_of(self.jobs, STAGE)],
                         [(1, ABANDONED), (2, None)])

    def test_an_assertion_about_another_stores_offer_is_silence(self):
        self.assertIsNone(apply_offer_state(
            self.jobs, assertion("offer:somebody-else/implementation",
                                 "attempt:somebody-else/implementation",
                                 ABANDONED)))
        self.assertEqual([one["ended_state"] for one in
                          episodes_of(self.jobs, STAGE)], [None])

    def test_an_assertion_naming_another_attempt_refuses_rather_than_ending(self):
        """The offer id is this store's; the attempt it names is not.

        One offer froze one attempt, so this cannot be an assertion about the
        episode it appears to name -- and ending that episode on it would be
        recording an ending for an execution this store never asked for.
        """
        with self.assertRaises(ContractRefusal) as caught:
            apply_offer_state(self.jobs,
                              assertion(FIRST_OFFER, "attempt:somebody-else",
                                        ABANDONED))
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual([one["ended_state"] for one in
                          episodes_of(self.jobs, STAGE)], [None])

    def test_a_revision_that_does_not_follow_from_its_state_refuses(self):
        held = assertion(FIRST_OFFER, FIRST_ATTEMPT, ABANDONED)
        held["revision"] = 1
        with self.assertRaises(ContractRefusal) as caught:
            apply_offer_state(self.jobs, held)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))


class EndingsOutsideTheReplaceableSet(JobManagerCase):
    """A stage that STOPPED, and is reported rather than quietly re-offered.

    `abandoned-after-restart` is the one ending this Work re-admits, because
    nobody decided anything about the stage. An expired or declined offer was
    delivered and answered, and whether to offer it again is a scheduling
    policy decision this leaf does not own. What it must not do is hide it.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        sweep(self.jobs, self.acts, now=NOW)

    def ending(self, state):
        self.acts.canonical_state(FIRST_OFFER, FIRST_ATTEMPT, state)
        return sweep(self.jobs, self.acts, now=SOON, attach=True)

    def test_an_expired_offer_stops_the_stage_visibly(self):
        report = self.ending("expired")
        self.assertEqual(report["observed"], 1)
        self.assertEqual(report["replaced"], [])
        self.assertEqual(report["acts"], [])
        held = status(self.jobs, self.acts,
                      observed_at=SOON)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "exceptional")
        self.assertIsNone(held["offer_id"])
        self.assertEqual([(one["episode"], one["ended_state"])
                          for one in held["episodes"]], [(1, "expired")])
        self.assertEqual(owed_acts(self.jobs, self.acts), [],
                         "a stopped stage owes nothing; it is reported")

    def test_a_declined_offer_stops_the_stage_visibly(self):
        self.assertEqual(self.ending("declined")["replaced"], [])
        self.assertEqual(status(self.jobs, self.acts, observed_at=SOON)
                         ["jobs"][0]["stages"][0]["state"], "exceptional")

    def test_a_claimed_offer_ends_no_episode_at_all(self):
        """The success path, which must survive the recovery machinery.

        A claimed offer is terminal too, so a correction that treated every
        terminal state as an ending would end the episode of a stage that had
        just started running. Review [P1, 2026-09-03] measured exactly that,
        which is why this case now asserts the EPISODE and the projected state
        rather than only that nothing was replaced -- the earlier version
        checked `replaced` alone and passed while the stage was being wrecked.
        """
        self.acts.observed(STAGE, claimed_by=True)
        report = self.ending("claimed")
        self.assertEqual(report["replaced"], [])
        self.assertEqual([(one["episode"], one["ended_state"]) for one in
                          episodes_of(self.jobs, STAGE)], [(1, None)])
        held = status(self.jobs, self.acts,
                      observed_at=SOON)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "claimed")
        self.assertEqual(held["episode"], 1)
        self.assertEqual(held["offer_id"], FIRST_OFFER)

    def test_the_two_ending_vocabularies_are_related_and_not_equal(self):
        """Written down because conflating them was the defect.

        Every ending this store acts on is a terminal offer state; the one
        terminal offer state it does NOT act on is the successful one.
        """
        from baton_v12.job_manager import EPISODE_ENDINGS, REPLACEABLE_ENDINGS
        from baton_v12.worker_manager.events import TERMINAL_OFFER_STATES

        self.assertLess(frozenset(EPISODE_ENDINGS),
                        frozenset(TERMINAL_OFFER_STATES))
        self.assertEqual(frozenset(TERMINAL_OFFER_STATES)
                         - frozenset(EPISODE_ENDINGS), {"claimed"})
        self.assertLessEqual(frozenset(REPLACEABLE_ENDINGS),
                             frozenset(EPISODE_ENDINGS))


class OneReplacementPerEnding(JobManagerCase):
    """Two managers reconciling one abandonment, and the store deciding it."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.canonical_state(FIRST_OFFER, FIRST_ATTEMPT, ABANDONED)
        sweep(self.jobs, self.acts, now=SOON, attach=True)

    def test_a_second_manager_replays_the_replacement_it_did_not_open(self):
        other = JobStore.open(self.job_path, authority_uuid=UUID, incarnation="jobs-b",
                              clock=self.clock)
        self.addCleanup(other.close)
        report = sweep(other, self.acts, now=SOON)
        self.assertEqual(report["replaced"], [],
                         "episode 2 is already live, so nothing is owed")
        self.assertEqual([one["episode"] for one in
                          episodes_of(other, STAGE)], [1, 2])

    def test_the_table_refuses_a_second_live_episode_outright(self):
        """The guarantee is the partial unique index, not the loop above it.

        A handler that ran twice, a manager that raced, or a future caller
        that opened one directly all meet the same refusal.
        """
        with self.assertRaises(sqlite3.IntegrityError):
            self.jobs._connection.execute(
                "INSERT INTO episodes (stage_id, episode, offer_id, "
                "attempt_id, opened_at, incarnation) "
                "VALUES (?, 3, 'offer:x', 'attempt:x', ?, 'jobs-1')",
                (STAGE, NOW))

    def test_an_episode_records_one_ending_and_is_not_rewritten(self):
        self.acts.canonical_state(SECOND_OFFER, _SECOND_ATTEMPT, "expired")
        sweep(self.jobs, self.acts, now=SOON, attach=True)
        first, second = episodes_of(self.jobs, STAGE)
        self.assertEqual(first["ended_state"], ABANDONED,
                         "the earlier episode's ending is untouched")
        self.assertEqual(second["ended_state"], "expired")


class ReadOnlyStatusAppliesNothing(JobManagerCase):
    """Review [P2, 2026-09-03]: which surface attaches, pinned as a mechanism.

    The earlier draft gave the status tool's read-only surface `attach` and
    `drain` and said a status run drained regenerated assertions. `status`
    never called them, so an operator was told a fact had been consumed that
    was in fact discarded. The contract taken instead: ONLY THE SERVING
    RECONCILER ATTACHES, because applying a canonical ending is a durable act
    and a read-only surface performs none.

    These cases pin both halves -- that the surface cannot do it, and that what
    status reports meanwhile is the recorded state rather than a guess.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)
        sweep(self.jobs, self.acts, now=NOW)

    def reader(self):
        from tools.job_manager import _ReadOnly

        return _ReadOnly(self.control_store)

    def test_the_read_only_surface_has_no_way_to_attach_or_apply(self):
        held = self.reader()
        for absent in ("attach", "drain", "recover", "admit", "claim"):
            self.assertFalse(hasattr(held, absent), absent)

    def test_status_reports_the_recorded_state_and_records_nothing(self):
        """A canonical ending the store has not applied leaves it as it was.

        This is the STALENESS BOUND, asserted rather than left to be
        discovered: the offer is canonically over, status still answers what
        the store recorded, and -- the half that matters -- status wrote
        nothing while answering.
        """
        from baton_v12.worker_manager import recover_on_restart

        other = self.control(incarnation="manager-2")
        self.assertEqual(recover_on_restart(other, now=SOON)["abandoned"],
                         [FIRST_OFFER])
        # BOTH SNAPSHOTS TAKEN BEFORE THE CALL, which is the whole mechanism:
        # a comparison whose two sides are both read afterwards is true
        # whatever the call did. Review [P2, 2026-09-03] caught exactly that
        # here -- the receipts side compared one read against a second read of
        # the same rows and proved nothing.
        episodes_before = [dict(one) for one in episodes_of(self.jobs, STAGE)]
        receipts_before = [dict(one) for one in receipt_rows(self.jobs)]
        journal_before = [tuple(one) for one in self.jobs._connection.execute(
            "SELECT operation_id, kind, state FROM operations "
            "ORDER BY operation_id")]
        held = status(self.jobs, self.reader(),
                      observed_at=SOON)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "offered")
        self.assertEqual([dict(one) for one in episodes_of(self.jobs, STAGE)],
                         episodes_before,
                         "a read-only status applies no ending")
        self.assertEqual([dict(one) for one in receipt_rows(self.jobs)],
                         receipts_before, "and writes no receipt")
        # AND NOTHING WAS JOURNALLED EITHER. Every durable act in this store
        # goes through `transact`, so an unchanged operations table is the
        # general statement of "recorded nothing" rather than a check of the
        # two tables this case happened to think of.
        self.assertEqual([tuple(one) for one in
                          self.jobs._connection.execute(
                              "SELECT operation_id, kind, state FROM "
                              "operations ORDER BY operation_id")],
                         journal_before, "and journalled no operation")

    def test_one_serving_reconcile_then_corrects_it(self):
        """AND THE STALENESS IS ONE TICK, which is what makes the bound a bound.

        The same store, the same canonical fact, through the surface that IS
        allowed to attach.
        """
        self.acts = ManagerOperations(
            self.control(incarnation="manager-2"),
            AuthorityPort(self.session, fake_claim_signature),
            mint_bearer=self.mint, deliver_bearer=self.deliver)
        reconcile(self.jobs, self.acts, now=SOON)
        held = status(self.jobs, self.acts,
                      observed_at=SOON)["jobs"][0]["stages"][0]
        self.assertEqual(held["episode"], 2)
        self.assertEqual([(one["episode"], one["ended_state"])
                          for one in held["episodes"]],
                         [(1, ABANDONED), (2, None)])


class TheEventPump(JobManagerCase):
    """Non-reentrancy, and the transaction boundary it exists to keep."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()

    def test_nothing_is_dispatched_while_a_store_transaction_is_held(self):
        """The rule is CHECKED, not promised.

        A consumer's handler writing its own store inside a producer's
        transaction is one transaction with two owners, which is the boundary
        this distribution keeps everywhere else.
        """
        self.acts.events.publish(assertion(FIRST_OFFER, FIRST_ATTEMPT,
                                           ABANDONED))
        self.jobs._connection.execute("BEGIN IMMEDIATE")
        self.addCleanup(lambda: self.jobs._connection.execute("ROLLBACK"))
        self.assertTrue(self.jobs._connection.in_transaction)
        with self.assertRaises(ContractRefusal) as caught:
            self.acts.drain(
                {OFFER_STATE_KIND: lambda event: None},
                quiescent=(lambda: self.jobs._connection.in_transaction,))
        self.assertEqual(caught.exception.code, "precondition")
        self.assertIn("store transaction is open", caught.exception.message)

    def test_a_follow_up_is_queued_and_not_dispatched_recursively(self):
        seen = []

        def handler(event):
            seen.append((event["offer_id"], depth[0]))
            depth[0] += 1
            if len(seen) < 3:
                self.acts.events.publish(
                    assertion(FIRST_OFFER, FIRST_ATTEMPT, ABANDONED))
            depth[0] -= 1

        depth = [0]
        self.acts.events.publish(assertion(FIRST_OFFER, FIRST_ATTEMPT,
                                           ABANDONED))
        self.assertEqual(self.acts.drain({OFFER_STATE_KIND: handler}), 3)
        # EVERY HANDLER RAN AT DEPTH ZERO. A recursive dispatch would have run
        # the follow-up inside its producer and shown depth 1 and 2.
        self.assertEqual([one[1] for one in seen], [0, 0, 0])

    def test_a_pump_inside_a_handler_refuses_rather_than_nesting(self):
        def handler(event):
            with self.assertRaises(ContractRefusal) as caught:
                pump(self.acts.events, {})
            self.assertEqual(caught.exception.code, "precondition")
            nested.append(caught.exception.message)

        nested = []
        self.acts.events.publish(assertion(FIRST_OFFER, FIRST_ATTEMPT,
                                           ABANDONED))
        self.acts.drain({OFFER_STATE_KIND: handler})
        self.assertEqual(len(nested), 1)

    def test_an_unhandled_kind_is_ordinary_rather_than_an_error(self):
        queue = EventQueue()
        queue.publish({"kind": "something.else", "detail": 1})
        self.assertEqual(pump(queue, {OFFER_STATE_KIND: lambda event: None}),
                         0)

    def test_publishing_takes_a_copy_the_producer_cannot_reach(self):
        queue = EventQueue()
        held = assertion(FIRST_OFFER, FIRST_ATTEMPT, ABANDONED)
        queue.publish(held)
        held["state"] = "claimed"
        self.assertEqual([one["state"] for one in queue.pending()],
                         [ABANDONED])


class ThePublisher(JobManagerCase):
    """What the Worker Manager asserts, read back off its own rows."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)
        sweep(self.jobs, self.acts, now=NOW)

    def test_the_assertion_is_regenerated_from_the_row_every_time(self):
        queue = EventQueue()
        published = publish_offer_states(self.control_store, queue,
                                         [FIRST_OFFER])
        self.assertEqual(published, [FIRST_OFFER])
        self.assertEqual(queue.pending(),
                         [assertion(FIRST_OFFER, FIRST_ATTEMPT, "issued")])
        # THE SAME CALL AGAIN ANSWERS THE SAME THING, which is what makes
        # republication a repair rather than a second event.
        again = EventQueue()
        publish_offer_states(self.control_store, again, [FIRST_OFFER])
        self.assertEqual(again.pending(), queue.pending())

    def test_an_offer_this_manager_does_not_hold_is_silence(self):
        queue = EventQueue()
        self.assertEqual(publish_offer_states(self.control_store, queue,
                                              ["offer:nobody/implementation"]),
                         [])
        self.assertEqual(queue.pending(), [])

    def test_every_canonical_offer_state_has_a_monotone_revision(self):
        """The rank IS the revision, so a state without one cannot be
        published at all -- and the lifecycle's order is what makes it usable
        for ordering."""
        from baton_v12.worker_manager.schema import OFFER_STATES

        self.assertEqual(sorted(STATE_REVISIONS), sorted(OFFER_STATES))
        self.assertLess(offer_state_revision("issued"),
                        offer_state_revision("accepted"))
        for ending in ("declined", "expired", ABANDONED, "claimed",
                       "claim-refused", "settlement-expired"):
            self.assertGreater(offer_state_revision(ending),
                               offer_state_revision("accepted"), ending)


if __name__ == "__main__":
    unittest.main()
