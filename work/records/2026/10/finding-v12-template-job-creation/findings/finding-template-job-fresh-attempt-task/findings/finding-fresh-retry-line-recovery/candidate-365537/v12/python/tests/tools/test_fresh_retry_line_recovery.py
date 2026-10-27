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
from tools import stage_execution
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

    def settled_then_retried(self):
        """The released round, then the RETRY driven to its own review.

        R2's own shape: by the end of this there is a frozen checkpoint on the
        line and an active attachment over it, both belonging to the LATER
        round -- which is the state the first release has to keep answering
        from. The ending's own answer is recorded by `settled`, so the replay
        can be compared with it member for member rather than described.
        """
        held = self.settled()
        fresh = self.retried(held)["job_id"]
        held["retry"] = fresh
        for _ in range(14):
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
        self.driven(held["jobs"], held["composed"], fresh)
        attempt = self.stage_of(held["jobs"], held["composed"],
                                fresh)["attempt_id"]
        held["retry_attempt"] = attempt
        self.proposing = True
        self.turn(held["jobs"], held["control"], held["composed"],
                  "implementation", attempt, job_id=fresh)
        for _ in range(16):
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
        held["stages"] = self.stages(held["jobs"], held["composed"], fresh)
        held["newer"] = self.newer_state(held)
        return held

    def newer_state(self, held):
        """The LATER round's line, checkpoint and attachment, as rows."""
        taken = {}
        for name, statement in (
                ("line", "SELECT line_id, state, current_checkpoint_id "
                         "FROM review_lines"),
                ("checkpoints", "SELECT checkpoint_id, writer_id, state "
                                "FROM line_checkpoints"),
                ("attachments", "SELECT attachment_id, checkpoint_id, state "
                                "FROM review_attachments")):
            taken[name] = [dict(one) for one in
                           held["control"]._connection.execute(
                               statement).fetchall()]
        return taken

    def first_writer(self, held):
        return held["control"]._connection.execute(
            "SELECT * FROM line_writers WHERE runtime_attempt_id = ?",
            (self.first_attempt,)).fetchone()

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


class TheReleaseRefusesACandidateBeforeAnyFreeze(TheReleasedLineCase):
    """W365075 review 2026-10-27T01-42-10Z [R1], as the reviewer found it.

    THE INTERVAL THE EARLIER COVERAGE MISSED. Asking after a published round
    has frozen is easy -- the freeze revoked the writer, so the refusal is the
    writer's state. The dangerous moment is BEFORE that: a `completed` turn
    whose writer is still active on a line that is still `writing`, where
    every state check this operation makes passes and only the DISPOSITION
    distinguishes a round with a candidate from one without.

    DRIVEN THE REVIEWER'S WAY, through the real successful retry, and then one
    step further: this delegates to the real freeze afterwards, so the same
    case also says the round it refused to release still reached its review.
    """

    def released_at_the_freeze(self):
        """The release asked exactly where `freeze_checkpoint` would run."""
        from unittest import mock

        asked = []
        real = review_cycles.freeze_checkpoint

        def intercept(store, *, writer_id, generation, profile, port):
            writer = review_cycles.writer_of(store, writer_id)
            line = review_cycles.line_of(store, writer["line_id"])
            seen = {"writer_state": writer["state"],
                    "line_state": line["state"],
                    "disposition": store._connection.execute(
                        "SELECT worker_disposition FROM attempts "
                        "WHERE runtime_attempt_id = ?",
                        (writer["runtime_attempt_id"],)
                    ).fetchone()["worker_disposition"]}
            try:
                review_cycles.release_writer(
                    store, writer_id=writer_id, generation=generation,
                    port=port,
                    reason="implementation produced no candidate to review")
                seen["released"] = True
            except ContractRefusal as caught:
                seen["refusal"] = caught
            seen["line_after"] = review_cycles.line_of(
                store, writer["line_id"])["state"]
            asked.append(seen)
            # AND THEN THE REAL ONE, so this case can say the round it
            # protected still went to review.
            return real(store, writer_id=writer_id, generation=generation,
                        profile=profile, port=port)

        with mock.patch.object(review_cycles, "freeze_checkpoint", intercept):
            held = self.settled_then_retried()
        self.assertEqual(len(asked), 1, asked)
        held["asked"] = asked[0]
        return held

    def test_a_completed_writer_is_refused_while_it_is_still_active(self):
        held = self.released_at_the_freeze()
        asked = held["asked"]
        # THE INTERVAL IS REAL: every other precondition passed.
        self.assertEqual(asked["writer_state"], "active")
        self.assertEqual(asked["line_state"], "writing")
        self.assertEqual(asked["disposition"], "completed")
        self.assertNotIn("released", asked)
        caught = asked["refusal"]
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("carries a candidate", str(caught))

    def test_the_refused_asking_left_the_line_exactly_as_it_was(self):
        held = self.released_at_the_freeze()
        self.assertEqual(held["asked"]["line_after"], "writing")

    def test_the_round_it_protected_still_reached_its_review(self):
        held = self.released_at_the_freeze()
        self.assertEqual(held["stages"],
                         {"implementation": "completed", "review": "waiting"})
        self.assertEqual([one["state"] for one in
                          held["newer"]["checkpoints"]], ["frozen"])
        self.assertEqual([one["state"] for one in
                          held["newer"]["attachments"]], ["active"])

    def test_the_releasable_answers_are_the_complement_of_completed(self):
        """THE VOCABULARY PIN, so a fifth answer is visible rather than silent.

        `NO_CANDIDATE` is enumerated rather than subtracted, which fails
        closed -- a new worker answer is not releasable until somebody decides
        it is. This case is what makes that decision visible: adding to
        `schema.DISPOSITIONS` fails here until the complement is restated.
        """
        from baton_v12.worker_manager import schema

        self.assertEqual(set(schema.DISPOSITIONS)
                         - set(review_cycles.NO_CANDIDATE), {"completed"})
        self.assertEqual(sorted(review_cycles.NO_CANDIDATE),
                         ["cancelled", "plan-rejected", "unable"])


class TheReleaseReplaysAfterALaterCheckpoint(TheReleasedLineCase):
    """W365075 review 2026-10-27T01-42-10Z [R2], as the reviewer found it.

    THE OLD RELEASE IS STILL THE SAME OPERATION. By the time the retry's
    review has started there is a frozen checkpoint on this line and an active
    attachment over it -- and the first round's release has to answer from its
    own PINNED facts, not from those. The previous cut recomputed its
    signature out of the line's current checkpoint and so refused its own
    committed operation.
    """

    def test_the_old_release_answers_its_exact_committed_document(self):
        held = self.settled_then_retried()
        writer = self.first_writer(held)
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        again = review_cycles.release_writer(
            held["control"], writer_id=writer["writer_id"],
            generation=writer["assignment_generation"], port=worker.port,
            reason="implementation produced no candidate to review")
        self.assertEqual(
            json.dumps(again, sort_keys=True, default=str),
            json.dumps(held["ending"]["answered"]["released"],
                       sort_keys=True, default=str))
        # THE PINNED FACTS, AND THEY ARE NOT TODAY'S: `idle` and no
        # checkpoint, while the line is `reviewing` at a frozen one.
        self.assertEqual(again["state"], "idle")
        self.assertIsNone(again["current_checkpoint_id"])
        self.assertEqual(again["fence"]["fenced"]["gate"],
                         "runtime-quiescence:1")

    def test_the_newer_state_is_not_consulted_and_not_changed(self):
        held = self.settled_then_retried()
        writer = self.first_writer(held)
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        self.assertEqual(held["newer"]["line"][0]["state"], "reviewing")
        self.assertIsNotNone(held["newer"]["line"][0]["current_checkpoint_id"])
        review_cycles.release_writer(
            held["control"], writer_id=writer["writer_id"],
            generation=writer["assignment_generation"], port=worker.port,
            reason="implementation produced no candidate to review")
        self.assertEqual(self.newer_state(held), held["newer"])

    def test_a_reopened_store_answers_the_same_old_release(self):
        """REOPEN, because durable means across incarnations."""
        from baton_v12.worker_manager import ControlStore

        held = self.settled_then_retried()
        writer = self.first_writer(held)
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        reopened = ControlStore.open(self.control_path,
                                     incarnation="reopened-365155",
                                     clock=lambda: fixtures.NOW)
        self.addCleanup(reopened.close)
        again = review_cycles.release_writer(
            reopened, writer_id=writer["writer_id"],
            generation=writer["assignment_generation"], port=worker.port,
            reason="implementation produced no candidate to review")
        self.assertEqual(
            json.dumps(again, sort_keys=True, default=str),
            json.dumps(held["ending"]["answered"]["released"],
                       sort_keys=True, default=str))
        self.assertEqual(self.newer_state(held), held["newer"])

    def test_a_changed_reason_after_the_later_checkpoint_still_refuses(self):
        """THE IDENTITY STILL MEANS SOMETHING, which is the other half of R2."""
        held = self.settled_then_retried()
        writer = self.first_writer(held)
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        with self.assertRaises(ContractRefusal):
            review_cycles.release_writer(
                held["control"], writer_id=writer["writer_id"],
                generation=writer["assignment_generation"], port=worker.port,
                reason="a different sentence entirely")
        with self.assertRaises(ContractRefusal) as caught:
            review_cycles.release_writer(
                held["control"], writer_id=writer["writer_id"], generation=9,
                port=worker.port,
                reason="implementation produced no candidate to review")
        self.assertIn("stale writer generation", str(caught.exception))
        self.assertEqual(self.newer_state(held), held["newer"])


class TheReleaseRefusesUnsettledAndForeignExecution(TheReleasedLineCase):
    """The two refusals that are about the RUNTIME rather than the line."""

    def retry_in_flight(self):
        """The retry's own writer, active, with its container still running."""
        held = self.settled()
        fresh = self.retried(held)["job_id"]
        held["retry"] = fresh
        for _ in range(14):
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
        self.driven(held["jobs"], held["composed"], fresh)
        attempt = self.stage_of(held["jobs"], held["composed"],
                                fresh)["attempt_id"]
        held["retry_attempt"] = attempt
        held["writer"] = held["control"]._connection.execute(
            "SELECT * FROM line_writers WHERE runtime_attempt_id = ?",
            (attempt,)).fetchone()
        return held

    def test_a_live_runtime_with_no_answer_yet_refuses(self):
        """UNKNOWN EXECUTION IS NOT A RELEASABLE ROUND.

        The retry's container is running and its worker has answered nothing,
        so there is no terminal disposition and no positive quiescence. The
        release refuses on the quiescence half, which is the earlier of the
        two, and nothing about the line or the runtime moves.
        """
        held = self.retry_in_flight()
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id=self.SPARE)
        rows = held["control"]._connection.execute(
            "SELECT execution_runtime, worker_disposition FROM attempts "
            "WHERE runtime_attempt_id = ?",
            (held["retry_attempt"],)).fetchone()
        self.assertEqual(rows["execution_runtime"], "running")
        self.assertEqual(rows["worker_disposition"], "none")
        self.assertEqual(held["writer"]["state"], "active")
        with self.assertRaises(ContractRefusal) as caught:
            review_cycles.release_writer(
                held["control"], writer_id=held["writer"]["writer_id"],
                generation=held["writer"]["assignment_generation"],
                port=worker.port, reason="a fixture asking too early")
        self.assertIn("positively quiescent", str(caught.exception))
        self.assertEqual(
            review_cycles.writer_of(
                held["control"],
                held["writer"]["writer_id"])["state"], "active")
        self.assertEqual(
            review_cycles.line_of(held["control"],
                                  held["line"]["line_id"])["state"],
            "writing")
        self.assertEqual(
            dict(held["control"]._connection.execute(
                "SELECT execution_runtime, worker_disposition FROM attempts "
                "WHERE runtime_attempt_id = ?",
                (held["retry_attempt"],)).fetchone()),
            dict(rows))

    def test_a_session_for_another_participant_refuses_at_the_releasable_moment(
            self):
        """THE CAPABILITY REFUSAL, asked where every other check passes.

        It has to be asked exactly where the real ending asks: an active
        writer, a `writing` line, a quiescent attempt and a no-candidate
        disposition. Anywhere else an earlier precondition answers first and
        the case would be about that instead. So this intercepts the
        composition's own release call, asks once with the SPARE producer's
        session -- which acts for `baton.second` while this attempt is
        assigned to `baton.claude` -- and then delegates.
        """
        from unittest import mock

        asked, kept = [], {}
        real = review_cycles.release_writer
        real_compose = stage_execution.operations_from

        def composing(document, jobs, control, **named):
            answered = real_compose(document, jobs, control, **named)
            kept["composed"] = answered
            return answered

        def intercept(store, *, writer_id, generation, port, reason):
            writer = review_cycles.writer_of(store, writer_id)
            # THE SPARE PRODUCER'S REAL SESSION, taken from the composition
            # this run built rather than from a stand-in: the point of the
            # case is that a genuine session for another participant is
            # refused, and an object with a `participant` attribute would be
            # asserting the check exists rather than that it binds.
            foreign = self.worker_of(kept["composed"], "implementation",
                                     worker_id=self.SPARE)
            seen = {"writer_state": writer["state"],
                    "line_state": review_cycles.line_of(
                        store, writer["line_id"])["state"],
                    "mine": getattr(port, "participant", None),
                    "foreign": getattr(foreign.port, "participant", None)}
            try:
                real(store, writer_id=writer_id, generation=generation,
                     port=foreign.port, reason=reason)
                seen["released"] = True
            except ContractRefusal as caught:
                seen["refusal"] = caught
            asked.append(seen)
            return real(store, writer_id=writer_id, generation=generation,
                        port=port, reason=reason)

        with mock.patch.object(stage_execution, "operations_from", composing), \
                mock.patch.object(review_cycles, "release_writer", intercept):
            held = self.failing_pool()
        self.assertEqual(len(asked), 1, asked)
        seen = asked[0]
        self.assertEqual(seen["writer_state"], "active")
        self.assertEqual(seen["line_state"], "writing")
        self.assertNotEqual(seen["mine"], seen["foreign"])
        self.assertNotIn("released", seen)
        self.assertEqual((seen["refusal"].category, seen["refusal"].code),
                         ("refused", "capability"))
        self.assertIn("acts for another participant", str(seen["refusal"]))
        # AND THE REAL ENDING STILL FINISHED, with the line released.
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        self.assertEqual(
            worker.stage.deployment.line_for(self.job_id)["state"], "idle")


class TheReleaseSurvivesAnInterruptedWrite(TheReleasedLineCase):
    """REC-6 at the one external effect this operation has.

    The fence reaches the Authority BEFORE the release's own write commits, so
    the window between them is the one a process death can land in. The loop
    keeps asking `conclude` until the cleanup axis is terminal, so re-entry is
    the ordinary path rather than a special one -- and the fence replays by
    its own authority operation id, so recovery must not produce a second one.
    """

    def interrupted(self):
        """The release's write fails ONCE; a later manager tick re-enters.

        MODELLED AS A DEATH AND NOT AS A REFUSAL. An I/O failure at this write
        is not something the serving loop catches -- it propagates out of the
        tick, which is exactly what a process dying there looks like. So the
        fixture keeps the stores the aborted run had opened and then ticks
        again with nothing patched, which is the next manager doing its
        ordinary work rather than a recovery act anybody wrote.
        """
        from unittest import mock
        from baton_v12.worker_manager import ControlStore

        failed, kept = [], {}
        real_transact = ControlStore.transact
        real_compose = stage_execution.operations_from

        def flaky(self, operation_id, kind, signature, action):
            if kind == "review-line.release-writer" and not failed:
                failed.append(operation_id)
                raise OSError("the process died before this write committed")
            return real_transact(self, operation_id, kind, signature, action)

        def composing(document, jobs, control, **named):
            answered = real_compose(document, jobs, control, **named)
            kept.update(jobs=jobs, control=control, composed=answered)
            return answered

        with mock.patch.object(stage_execution, "operations_from", composing), \
                mock.patch.object(ControlStore, "transact", flaky):
            with self.assertRaises(OSError):
                self.failing_pool()
        self.assertEqual(len(failed), 1, failed)
        held = {"jobs": kept["jobs"], "control": kept["control"],
                "composed": kept["composed"], "failed_operation": failed[0]}
        # THE ORDINARY TICKS, UNPATCHED. This is the recovery.
        for _ in range(14):
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
        self.assertEqual(
            self.stages(held["jobs"], held["composed"], self.job_id),
            {"implementation": "exceptional", "review": "blocked"})
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        held["worker"] = worker
        held["line"] = worker.stage.deployment.line_for(self.job_id)
        return held

    def test_the_ending_finishes_on_a_later_tick(self):
        held = self.interrupted()
        self.assertEqual(held["line"]["state"], "idle")
        self.assertIsNone(held["line"]["current_checkpoint_id"])
        self.assertEqual(
            [tuple(one) for one in held["control"]._connection.execute(
                "SELECT state, revocation_reason FROM line_writers")],
            [("revoked", "released")])

    def test_the_interruption_produced_no_second_authority_fence(self):
        """THE POINT OF THE CASE: one ending, one fence, one gate.

        `finalize_quiescent_assignment` commits its decision before the
        Authority is asked and reissues the SAME act afterwards, so a release
        whose write failed after that call must come back to one journalled
        finalization -- not two, and not a second gate to discharge.
        """
        held = self.interrupted()
        rows = [one["operation_id"] for one in
                held["control"]._connection.execute(
                    "SELECT operation_id FROM operations WHERE kind = ?",
                    ("attempt.finalize-quiescent",)).fetchall()]
        self.assertEqual(len(rows), 1, rows)
        released = [one["operation_id"] for one in
                    held["control"]._connection.execute(
                        "SELECT operation_id FROM operations WHERE kind = ?",
                        ("review-line.release-writer",)).fetchall()]
        self.assertEqual(released, [held["failed_operation"]])

    def test_the_recovered_ending_still_discharged_the_works_gate(self):
        """AND THE RETRY IS STILL REACHABLE AFTERWARDS."""
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import gate_discharge_of

        held = self.interrupted()
        discharged = gate_discharge_of(held["control"], self.first_attempt)
        self.assertIsNotNone(discharged)
        self.assertEqual(discharged["gate"], "runtime-quiescence:1")
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            self.assertIsNone(authority.project_work(self.work).get("gate"))
        finally:
            authority.dispose()


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
