"""W365075 — AN ENDING WITH NOTHING TO REVIEW RELEASES THE LINE.

THE DEAD END THIS SUITE WAS WRITTEN FOR IS FIXED, and this is now its
regression. Before the fix `review_driver.end_implementation` performed
`freeze_checkpoint` unconditionally, so an implementation turn that answered
`unable` -- a turn with no candidate -- froze this line's checkpoint and left
the line `review-ready`. Nothing leaves that state but a verdict; a verdict
takes a review ATTACHMENT; and the Job whose implementation did not complete
never opens its review stage, so no attachment could ever exist. Every later
writer on that Work was then refused for ever -- correction and fresh retry
alike -- which DESIGN REC-4/5/7 forbid.

THE FIX IS THE RULE `_publishable` ALREADY STATES, one step later. That
constant exists because this module published unconditionally and "an
implementation turn that produced no candidate has nothing to offer against a
target"; a turn with nothing to offer has nothing to review either. Step eight
now freezes for a publishable disposition and calls the new
`review_cycles.release_writer` otherwise, which does what that step owes --
revoke the quiescent writer and fence its assignment -- and returns the line
to `correction-ready` when a frozen checkpoint is retained or `idle` when
there is none.

WHAT IT DOES NOT TOUCH: `grant_writer`'s admitted states, any verdict, the
line's current checkpoint, and every output, receipt and retention of the
round that ended. A legitimate pending review still refuses a later writer,
which `ALegitimatePendingReviewStillRefuses` asserts.
"""

import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import reconcile, sweep
from baton_v12.worker_manager import review_cycles

from tests.job_manager import fixtures
# THE MODULE AND NOT THE CLASS, because the loader collects every TestCase
# bound in a test module's namespace: importing the parent's class under an
# alias here would make unittest run the PARENT's cases a second time as part
# of this suite.
from tests.tools import test_retry_task_lineage as lineage
from tests.tools.test_stage_execution import ServingCase


class TheReleasedLineCase(ServingCase):
    """The parent's own fixture, asked about the line it leaves behind.

    THE HELPERS ARE BORROWED AND THE CASES ARE NOT: subclassing the parent's
    case class re-ran its assertions under this suite's name, which this
    dossier's ancestors have been corrected for twice.
    """

    # AND BOUND IN THE CLASS BODY, not the module's: a module attribute that
    # is a TestCase subclass is collected by the loader, so a module-level
    # alias would run the parent's cases a second time here.
    retrying = lineage.TheRetriedJobReachesItsOwnRuntimes
    BASE = retrying.BASE
    HEAD = retrying.HEAD
    SPARE = retrying.SPARE
    PROPOSAL_OUTPUTS = retrying.PROPOSAL_OUTPUTS
    proposal_manifest = retrying.proposal_manifest
    spare_capacity_document = retrying.spare_capacity_document
    failing_pool = retrying.failing_pool
    retried = retrying.retried
    task_of = retrying.task_of
    agent = retrying.agent
    turn = retrying.turn
    quiescing = retrying.quiescing
    worker_of = retrying.worker_of
    no_version_control = retrying.no_version_control
    identity_for = retrying.identity_for
    creation_ports = retrying.creation_ports
    create = retrying.create
    driven = retrying.driven
    stages = retrying.stages
    stage_of = retrying.stage_of
    published = retrying.published

    def setUp(self):
        """The two borrowed setups, spelled out.

        `retrying.setUp` and its parent's call zero-argument `super()`, which
        is bound to the class that defines them -- so borrowing either across
        this hierarchy raises `TypeError`.
        """
        from baton_v12.authority import Authority
        from tests.job_manager import test_fresh_attempt as retry_fixtures
        from tests.job_manager.test_fresh_attempt import (FakeBinding,
                                                          FakeExclusion)
        from tests.job_manager.test_review_driver import Profile

        ServingCase.setUp(self)
        self.profile_seam = Profile()
        self.no_version_control()
        held = retry_fixtures.CURRENT.get("identity")
        retry_fixtures.CURRENT["identity"] = self.identity_for()
        self.addCleanup(retry_fixtures.CURRENT.__setitem__, "identity", held)
        self.exclusion = FakeExclusion()
        self.binding = FakeBinding()
        self.proposing = True
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.BASE)
            self.spare_principal = authority.principal_of("baton.second")
            for route in (fixtures.ROUTE, "rview"):
                authority.add_route_handler(route, "baton.second")
        finally:
            authority.dispose()

    def settled(self):
        """The `unable` ending, with the composition's OWN call recorded.

        THE OPERANDS ARE THE PRODUCT'S, not a case's reconstruction. The
        resume cases re-enter `end_implementation` with exactly what the
        serving loop passed it, which is the only way to assert that a
        re-entered ending answers the same document: a hand-built operand set
        would be testing the case's guess at the composition instead.
        """
        from unittest import mock
        from baton_v12.job_manager import review_driver

        seen = []
        real = review_driver.end_implementation

        def recording(*operands, **named):
            answered = real(*operands, **named)
            seen.append({"operands": operands, "named": named,
                         "answered": answered})
            return answered

        with mock.patch.object(review_driver, "end_implementation", recording):
            held = self.failing_pool()
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        held["worker"] = worker
        held["line"] = worker.stage.deployment.line_for(self.job_id)
        self.assertEqual(len(seen), 1, seen)
        held["ending"] = seen[0]
        return held

    def reentered(self, held):
        """The same ending, asked again, through the public entry."""
        from baton_v12.job_manager import review_driver

        return review_driver.end_implementation(*held["ending"]["operands"],
                                                **held["ending"]["named"])


class TheEndingReleasesTheLineItHeld(TheReleasedLineCase):
    """The fix, from the line's own record."""

    def test_an_unable_ending_leaves_no_checkpoint_and_an_idle_line(self):
        held = self.settled()
        line = held["line"]
        self.assertEqual(line["state"], "idle")
        self.assertIsNone(line["current_checkpoint_id"])
        # NOTHING WAS FROZEN AT ALL, so there is nothing awaiting a review.
        rows = held["control"]._connection.execute(
            "SELECT checkpoint_id, state FROM line_checkpoints").fetchall()
        self.assertEqual([tuple(one) for one in rows], [])
        self.assertEqual(
            held["control"]._connection.execute(
                "SELECT COUNT(*) FROM review_attachments").fetchone()[0], 0)

    def test_the_writer_is_revoked_as_released(self):
        held = self.settled()
        rows = held["control"]._connection.execute(
            "SELECT state, revocation_reason FROM line_writers").fetchall()
        self.assertEqual([tuple(one) for one in rows],
                         [("revoked", "released")])

    # WHAT IS NOT ASSERTED HERE, AND WHY. A case that called `grant_writer`
    # for the retry directly cannot: the admission requires the attempt to
    # exist in the CONTROL store, and a retry's attempt is recorded by
    # `start` -- which this fixture's retry does not reach, because its offer
    # waits on the prior attempt's runtime-quiescence gate (asserted in
    # `test_retry_task_lineage`). What the release achieves is asserted from
    # the line's own record above: `idle`, no checkpoint, nothing frozen.

    def test_the_first_attempts_outputs_and_record_survive_the_release(self):
        held = self.settled()
        outputs = held["control"]._connection.execute(
            "SELECT runtime_attempt_id, disposition FROM outputs").fetchall()
        self.assertEqual([tuple(one) for one in outputs],
                         [(self.first_attempt, "unable")])
        self.assertEqual(
            self.stages(held["jobs"], held["composed"], self.job_id),
            {"implementation": "exceptional", "review": "blocked"})
        self.assertEqual(self.published(self.first_attempt).decode("utf-8"),
                         self.task_of(held, self.job_id))


class ALegitimatePendingReviewStillRefuses(TheReleasedLineCase):
    """The negative regression: a round WITH a candidate is untouched.

    The proposing agent publishes a candidate, the ending freezes as it
    always did, the line waits for its review -- and a writer asked for there
    is refused exactly as before. `release_writer` is not reachable from that
    state either, which its own precondition says in as many words.
    """

    def reviewed_round(self):
        jobs, control = self.stores("pending-review")
        document = self.spare_capacity_document()
        from tools import single_worker, stage_execution

        installed = single_worker._held(document["workers"][0]["deployment"])
        answered = self.create(jobs, installed, task_id="retry-first",
                               statement="A round that produces a candidate.")
        self.job_id = answered["job_id"]
        self.engine = self.quiescing()
        composed = stage_execution.operations_from(
            document, jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        self.driven(jobs, composed, self.job_id)
        attempt = self.stage_of(jobs, composed, self.job_id)["attempt_id"]
        # THE PROPOSING TURN, which is what `self.proposing` already selects.
        self.assertEqual(self.turn(jobs, control, composed, "implementation",
                                   attempt), 0)
        for _ in range(14):
            sweep(jobs, composed, now=fixtures.NOW)
            reconcile(jobs, composed, now=fixtures.NOW)
            if self.stages(jobs, composed,
                           self.job_id).get("review") == "waiting":
                break
        worker = self.worker_of(composed, "implementation",
                                worker_id="implementation-worker")
        return {"jobs": jobs, "control": control, "composed": composed,
                "attempt": attempt, "worker": worker,
                "line": worker.stage.deployment.line_for(self.job_id),
                "operations": control._connection.execute(
                    "SELECT COUNT(*) FROM operations").fetchone()[0]}

    def test_a_published_round_still_freezes_and_waits_for_its_review(self):
        held = self.reviewed_round()
        # `reviewing` IS THE REVIEW-PENDING STATE ONCE A REVIEWER HAS
        # ATTACHED; `review-ready` is the moment before it. This fixture
        # drives the loop until the review stage is `waiting`, so the
        # attachment exists and the line has moved on by one.
        self.assertIn(held["line"]["state"], ("review-ready", "reviewing"))
        self.assertIsNotNone(held["line"]["current_checkpoint_id"])
        self.assertEqual(
            self.stages(held["jobs"], held["composed"], self.job_id),
            {"implementation": "completed", "review": "waiting"})

    # AND NOT THROUGH `grant_writer` DIRECTLY: its operation id is derived
    # from the WRITER identity, so asking again for an attempt that already
    # has one collides on that operation ("already recorded with a different
    # kind or signature") rather than reaching the line's admission. The
    # pending review's protection is asserted by the state above and by the
    # release's own refusal below.

    def test_release_writer_refuses_a_round_that_produced_a_candidate(self):
        """And it refuses at the FIRST precondition that is false.

        THE REFUSAL NAMES THE WRITER, because the freeze this round performed
        already revoked it -- and the writer and line checks are asked BEFORE
        the assignment fence for exactly this case: a line holding material
        offered for a legitimate review must be refused without the Authority
        being asked anything. The attempt's quiescence is a precondition too,
        and it is deliberately the LATER one.
        """
        held = self.reviewed_round()
        writer = review_cycles.writer_for_attempt(
            held["control"], attempt_id=held["attempt"], generation=1)
        with self.assertRaises(ContractRefusal) as caught:
            review_cycles.release_writer(
                held["control"], writer_id=writer["writer_id"], generation=1,
                port=held["worker"].port, reason="a fixture asking wrongly")
        self.assertIn("no active writer", str(caught.exception))
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        # AND NOTHING WAS JOURNALLED FOR THE ASKING, which is how "before any
        # effect" is proved rather than asserted: the fence this operation
        # performs commits its decision to the journal BEFORE the Authority is
        # asked, so an unchanged operation count is also an unasked Authority.
        self.assertEqual(
            held["control"]._connection.execute(
                "SELECT COUNT(*) FROM operations").fetchone()[0],
            held["operations"])
        # AND THE LINE IS UNTOUCHED BY THE ASKING.
        self.assertIn(
            review_cycles.line_of(held["control"],
                                  held["line"]["line_id"])["state"],
            ("review-ready", "reviewing"))


class TheReleasedEndingIsReEnterable(TheReleasedLineCase):
    """REC-6's durable ending, for the branch that freezes nothing.

    `end_implementation` promises that "a process death between any two steps
    re-enters here and finishes", and the three entries that keep that promise
    all proved the ending by its FROZEN CHECKPOINT. A round that produced no
    candidate has none -- so before W365075 the promise had no meaning for
    this branch, and after it the branch has to keep it. Re-entry here is the
    composition's own call, replayed.
    """

    def test_the_whole_ending_answers_the_same_document_again(self):
        held = self.settled()
        again = self.reentered(held)
        self.assertEqual(json.dumps(again, sort_keys=True, default=str),
                         json.dumps(held["ending"]["answered"],
                                    sort_keys=True, default=str))

    def test_the_re_entered_ending_proves_the_release_it_performed(self):
        """AND BY THE RELEASE, because there is no checkpoint to prove it by.

        The re-entry is behind a committed cleanup -- the runtime is gone --
        so the `_quiescent_completed` proof the release takes on its first run
        cannot be re-taken here. What answers is the release's own journalled
        operation, which is why it is asked before any mutable fact.
        """
        held = self.settled()
        again = self.reentered(held)
        self.assertIsNone(again["checkpoint"])
        self.assertIsNone(again["checkpoint_id"])
        self.assertEqual(again["disposition"], "unable")
        self.assertEqual(again["released"]["state"], "idle")
        self.assertEqual(again["released"]["fence"]["fenced"]["gate"],
                         "runtime-quiescence:1")
        # AND THE RUNTIME IT IS ABOUT IS ALREADY DESTROYED, which is the state
        # that made this branch unresumable before.
        self.assertEqual(
            held["control"]._connection.execute(
                "SELECT execution_runtime FROM attempts "
                "WHERE runtime_attempt_id = ?",
                (self.first_attempt,)).fetchone()["execution_runtime"],
            "destroyed")

    def test_re_entering_it_twice_more_adds_no_effect(self):
        held = self.settled()
        before = self.state(held)
        self.reentered(held)
        self.reentered(held)
        self.assertEqual(before, self.state(held))

    def state(self, held):
        """Every row the ending could have written a second one of."""
        taken = {}
        for table in ("line_writers", "line_checkpoints", "review_lines",
                      "review_attachments", "outputs", "retentions",
                      "operations"):
            taken[table] = held["control"]._connection.execute(
                f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        taken["line"] = dict(review_cycles.line_of(held["control"],
                                                   held["line"]["line_id"]))
        return taken


class WhatTheReleaseRefuses(TheReleasedLineCase):
    """Unknown and conflicting operands, each before any effect."""

    def test_an_unknown_writer_refuses(self):
        held = self.settled()
        with self.assertRaises(ContractRefusal):
            review_cycles.release_writer(
                held["control"], writer_id="writer-nobody-granted",
                generation=1, port=held["worker"].port, reason="a probe")

    def test_a_stale_generation_refuses(self):
        held = self.settled()
        rows = held["control"]._connection.execute(
            "SELECT writer_id FROM line_writers").fetchall()
        with self.assertRaises(ContractRefusal) as caught:
            review_cycles.release_writer(
                held["control"], writer_id=rows[0]["writer_id"],
                generation=9, port=held["worker"].port, reason="a probe")
        self.assertIn("stale writer generation", str(caught.exception))

    def test_the_release_the_ending_performed_replays_its_own_answer(self):
        """The ending is replayable, so asking again answers rather than
        acting -- which is what an interrupted ending needs to find.

        The ending has ALREADY released this writer, so this is the replay
        path and the answer is the committed one: the same operands, the same
        record, no second effect.
        """
        held = self.settled()
        rows = held["control"]._connection.execute(
            "SELECT writer_id FROM line_writers").fetchall()
        answered = review_cycles.release_writer(
            held["control"], writer_id=rows[0]["writer_id"], generation=1,
            port=held["worker"].port,
            reason="implementation produced no candidate to review")
        self.assertEqual(answered["state"], "idle")
        self.assertEqual(answered["writer_id"], rows[0]["writer_id"])
        again = review_cycles.release_writer(
            held["control"], writer_id=rows[0]["writer_id"], generation=1,
            port=held["worker"].port,
            reason="implementation produced no candidate to review")
        self.assertEqual(json.dumps(again, sort_keys=True, default=str),
                         json.dumps(answered, sort_keys=True, default=str))
        # AND NOTHING MOVED: one revoked writer, no checkpoint.
        self.assertEqual(
            [tuple(one) for one in held["control"]._connection.execute(
                "SELECT state, revocation_reason FROM line_writers")],
            [("revoked", "released")])
        # THE FENCE TRAVELS IN THE COMMITTED ANSWER, AND SO IN THE REPLAY.
        # This is W365075's own regression: the first cut performed the fence
        # after the write and returned it to nobody, so the gate it installed
        # was owed by no consumer and the Work stayed gated for ever.
        self.assertEqual(answered["fence"]["fenced"]["gate"],
                         "runtime-quiescence:1")
        self.assertEqual(again["fence"], answered["fence"])

    def test_a_different_reason_for_the_same_writer_refuses(self):
        """An operation id reused with different operands changes nothing."""
        held = self.settled()
        rows = held["control"]._connection.execute(
            "SELECT writer_id FROM line_writers").fetchall()
        with self.assertRaises(ContractRefusal):
            review_cycles.release_writer(
                held["control"], writer_id=rows[0]["writer_id"], generation=1,
                port=held["worker"].port, reason="another reason entirely")


if __name__ == "__main__":
    unittest.main()
