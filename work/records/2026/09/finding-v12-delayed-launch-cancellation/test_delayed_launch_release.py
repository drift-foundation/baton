"""W266336 stage 2: a DELAYED SUBMITTER holds the resource across cancellation.

Owner 267612 and thread T266336: force a paused launch across cancellation, prove
a replacement stays refused until the submitter cannot continue and its runtimes
are accounted for, and that an unknown outcome stays HELD -- one bounded runnable
command, real disposable state, controlled external adapter.

WHAT IS REAL: `attempts.request_runtime_start`, the public `abandon_attempt`
ending, the real `runtime_lanes` row and its predecessor interlock, a real
`ControlStore` on a disposable temporary file, and the real journal. The fixture
is the accepted `tests.manager.test_attempts.ExplicitAbandonmentFencesBeforeItRemoves`,
whose own cases already drive that ending.

THE SIMULATED BOUNDARIES, NAMED AS THE THREAD REQUIRES. The engine is the accepted
FAKE adapter. "The launcher was killed mid-submit" is a fault this module raises,
not an observed process death; "nothing is listed" is the fake's answer, not a
daemon's; and a fake CANNOT attest that a real engine terminated or that a real
submission cannot continue. Nothing here claims otherwise -- which is exactly why
the release predicate must not treat an adapter's silence as discharge.

WHAT THIS MEASURES RATHER THAN ASSUMES: on the paths reachable here the resource is
NOT released while a submission's outcome is unsettled. Each case asserts the lane
row, the axis and the adapter's submission count together, because any one of them
alone can look right while the others do not.
"""
import os
import sqlite3
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

import baton_v12.worker_manager as worker_manager             # noqa: E402
from baton_v12.contracts import ContractRefusal               # noqa: E402
from baton_v12.worker_manager import ControlStore              # noqa: E402
from baton_v12.worker_manager import activate_assignment       # noqa: E402
from baton_v12.worker_manager import attempts                  # noqa: E402
from baton_v12.worker_manager.attempts import (                # noqa: E402
    reconcile_runtime, request_runtime_start)

from baton_v12.worker_manager import output                     # noqa: E402

import tests.manager.test_attempts as accepted                 # noqa: E402

ATTEMPT = accepted.ATTEMPT
SUCCESSOR = "attempt-2"
RETENTION = "sha256:" + "7" * 64


class ADelayedSubmitterKeepsTheResource(
        accepted.ExplicitAbandonmentFencesBeforeItRemoves):
    """Stage 2's proofs, on the real start and the real public ending."""

    def prepared(self):
        """One claimed, activated attempt and the accepted custodian adapter."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        order = []
        adapter = self.Custodian(order)
        self.session.cancel = lambda operands: (
            order.append("fence"), self.session.fence_answer)[1]
        return adapter, order

    def lane_holders(self):
        """The real lane rows, read from a connection nothing here owns."""
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            return [row[0] for row in
                    beside.execute("SELECT holder FROM runtime_lanes")]
        finally:
            beside.close()

    def ending(self, adapter, attempt_id=ATTEMPT, reason="the ending"):
        try:
            answered = worker_manager.abandon_attempt(
                self.store, self.port, adapter, attempt_id=attempt_id,
                reason=reason, retention_policy_digest=RETENTION)
            return ("answered", answered["cleanup"]["cleanup"],
                    answered["cleanup"]["state"])
        except ContractRefusal as refusal:
            return ("refused", refusal.code, refusal.message)

    def unknown_outcome(self, adapter):
        """The simulated unknown: the submit faults and nothing is listed.

        This is what a daemon that may still be working looks like from the
        manager's side. It is a FAKE's silence, not evidence of absence.
        """
        adapter.start_failure = RuntimeError(
            "the launcher was killed mid-submit")
        adapter.listing = []
        adapter.observation = {"state": "absent", "why": "nothing listed",
                               "mounts": None}

    # -- cancellation across a launch that is still in flight -----------------

    def cancelled_mid_launch(self):
        """THE SELECTED SCHEDULE: a real cancellation while the launch pends.

        `attempts.request_cancellation` runs from INSIDE `adapter.start`, so the
        authority fence happens while this attempt's submission is in flight and
        no runtime is yet known. Returns everything the cases measure.
        """
        adapter, order = self.prepared()
        inside = {}
        submitted = adapter.start

        def racing(operands):
            inside["axis_before"] = self.row()["execution_runtime"]
            inside["lane_before"] = self.lane_holders()
            inside["cancelled"] = attempts.request_cancellation(
                self.store, self.port, accepted.Agent(), adapter,
                attempt_id=ATTEMPT,
                reason="cancelled while the launch was pending")
            inside["axis_after_cancel"] = self.row()["execution_runtime"]
            inside["lane_after_cancel"] = self.lane_holders()
            inside["order_at_cancel"] = list(order)
            return submitted(operands)

        adapter.start = racing
        try:
            inside["start"] = ("answered", request_runtime_start(
                self.store, adapter, attempt_id=ATTEMPT))
        except ContractRefusal as refusal:
            inside["start"] = ("refused", refusal.category, refusal.code,
                               refusal.message)
        return adapter, order, inside

    def test_cancellation_while_the_launch_is_pending_fences_and_holds(self):
        """R1: THE FENCE REALLY HAPPENS, and the reservation survives it.

        My first version called `abandon_attempt` here, which refuses at its
        no-attached-runtime precondition BEFORE any fence -- review
        2026-09-25T18-00-11Z is right that this proved a precondition and not a
        cancellation. `request_cancellation` is the concrete entry: it journals
        the intent, fences the exact generation at the authority, and only then
        orders quiescence.
        """
        adapter, order, inside = self.cancelled_mid_launch()

        # THE SUBMITTER WAS MID-FLIGHT when the cancellation ran.
        self.assertEqual(inside["axis_before"], "start-requested")
        self.assertEqual(inside["lane_before"], [ATTEMPT])
        # THE AUTHORITY FENCE IS THE MEASURED FACT, not an inferred one: the
        # session's cancel was called, and the answer carries the fence.
        self.assertEqual(inside["order_at_cancel"], ["fence"])
        self.assertEqual(sorted(inside["cancelled"]),
                         ["fenced", "intent", "quiescence",
                          "session_quiescence"])
        self.assertTrue(inside["cancelled"]["fenced"]["fenced"])
        self.assertEqual(inside["cancelled"]["intent"]["attempt_id"], ATTEMPT)
        # AND THE AXIS MOVED TO cancel-requested WITH THE LANE STILL HELD.
        self.assertEqual(inside["axis_after_cancel"], "cancel-requested")
        self.assertEqual(inside["lane_after_cancel"], [ATTEMPT])
        # THE LATE SUBMISSION STILL CROSSED -- that is what "delayed submitter"
        # means, and the fake really created a container for it.
        self.assertEqual(len(adapter.started), 1)
        self.assertEqual([one["runtime_id"] for one in adapter.list({})],
                         ["runtime-1"])
        # THE QUIESCENCE ORDER COULD NOT HAVE COVERED IT: it was ordered before
        # the runtime existed, and the fake was never asked to stop anything.
        self.assertEqual(adapter.stopped, [])
        self.assertEqual(self.lane_holders(), [ATTEMPT])

    def test_a_replacement_is_refused_after_the_cancellation(self):
        """R2, HELD SIDE: cancelled is not free while a runtime may exist."""
        adapter, _order, _inside = self.cancelled_mid_launch()
        self.assertEqual(self.lane_holders(), [ATTEMPT])

        self.claimed(offer_id="offer-2", attempt_id=SUCCESSOR)
        activate_assignment(self.store, self.port, attempt_id=SUCCESSOR,
                            expect=self.expect())
        replacement = self.Custodian([])
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, replacement,
                                  attempt_id=SUCCESSOR)

        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.assertEqual(replacement.started, [])
        self.assertEqual(self.lane_holders(), [ATTEMPT])

    def test_the_late_runtime_is_accounted_without_reviving_eligibility(self):
        """THE SAFE OUTCOME, replacing my earlier expect-the-defect assertions.

        Before the correction this schedule left `runtime_id` NULL: recording the
        observation was coupled to the attachment, `running` cannot follow
        `cancel-requested`, and the refusal discarded the identity with the state.
        Now the exact late runtime IS named while the cancellation stands --
        `stopping`, which is a legal successor and is what this manager's own
        ordered quiescence means. `running` never appears, so nothing re-admits
        execution.
        """
        adapter, _order, inside = self.cancelled_mid_launch()

        # THE IDENTITY IS RECORDED -- the whole point of the correction.
        self.assertEqual(self.row()["runtime_id"], "runtime-1")
        self.assertEqual(inside["start"][0], "answered", inside["start"])
        self.assertEqual(inside["start"][1]["runtime_id"], "runtime-1")
        # AND ELIGIBILITY IS NOT REVIVED: the axis says stopping, never running,
        # and the answer says why it was recorded that way.
        self.assertEqual(self.row()["execution_runtime"], "stopping")
        self.assertEqual(inside["start"][1]["observed"], "stopping")
        self.assertIn("already cancelled", inside["start"][1]["why"])
        # AND THE PROSE CLAIMS ONLY THE CANCELLATION, not a stop: on this
        # schedule the cancellation answered `quiescence.ordered=False` and no
        # stop command was issued, so intent, order and discharge stay distinct.
        self.assertIn("not evidence that the runtime was stopped",
                      inside["start"][1]["why"])
        self.assertFalse(inside["cancelled"]["quiescence"]["ordered"])
        self.assertEqual(adapter.stopped, [])
        self.assertNotIn(
            "running",
            attempts.TRANSITIONS["execution_runtime"]["cancel-requested"])
        self.assertNotIn(
            "running", attempts.TRANSITIONS["execution_runtime"]["stopping"])
        # THE RESERVATION IS STILL HELD: accounting is not release.
        self.assertEqual(self.lane_holders(), [ATTEMPT])

    def test_a_stale_generation_cannot_publish_a_result(self):
        """R2, AT THE REAL BOUNDARY THIS TIME.

        My earlier case called `reconcile_runtime` and asserted an axis refusal,
        which review 2026-09-25T18-19-46Z correctly says is not stale-result
        exclusion. `output.request_freeze` is the supported result-acceptance
        entry -- "a result is never published on a dead generation" -- and it
        reads liveness from the authority. So this drives the fenced attempt's
        own publication and asserts THAT refusal.

        The advanced projection is again FIXTURE SETUP standing in for an
        authority that fenced this generation, labelled as such.
        """
        adapter, order, _inside = self.cancelled_mid_launch()

        class Sealing(type(adapter)):
            def seal(inner, command):
                raise AssertionError("a stale generation reached the seal")

        publisher = Sealing(order)

        # FIRST BOUNDARY, on the way: a cancelled attempt is not quiescent, and
        # a freeze describes a tree nobody is still changing. This refusal is
        # real and is asserted rather than stepped over.
        with self.assertRaises(ContractRefusal) as early:
            output.request_freeze(self.store, self.port, publisher,
                                  attempt_id=ATTEMPT, disposition="completed")
        self.assertIn("only a positive quiescent observation",
                      early.exception.message)

        # NOW REACH THE GENERATION CHECK, still on this schedule: `quiescent` is
        # a legal successor of `stopping`, so the fake reports the late runtime
        # as finished and reconciliation records it.
        publisher.observation = {"state": "quiescent", "why": "it exited",
                                 "mounts": None}
        reconcile_runtime(self.store, publisher, attempt_id=ATTEMPT,
                          minted="runtime-1")
        self.assertEqual(self.row()["execution_runtime"], "quiescent")
        # AND THE SECOND GATE: a freeze needs a recorded turn outcome. The
        # accepted fixture records dispositions through the manager's own axis
        # recorder, and `cancelled` is the one consistent with this schedule --
        # FIXTURE SETUP to reach the gate under test, not a claim about a worker.
        accepted.observe(self.store, attempt_id=ATTEMPT,
                         axis="worker_disposition", value="cancelled")
        # THE SIMULATED AUTHORITY has moved on to another generation.
        self.session.live_assignment = dict(
            self.session.live_assignment, generation=2)

        # AND THE DECLARED OUTCOME MUST MATCH the recorded one, so the stale
        # publication declares what this attempt actually reached.
        with self.assertRaises(ContractRefusal) as caught:
            output.request_freeze(self.store, self.port, publisher,
                                  attempt_id=ATTEMPT, disposition="cancelled")

        self.assertIn("the live assignment is", caught.exception.message)
        self.assertIn("this attempt is fixed to", caught.exception.message)
        self.assertEqual(self.row()["output"], "open",
                         "a stale generation moved the output axis")

    def test_the_cancelled_attempt_settles_and_releases_on_this_schedule(self):
        """THE SELECTED SAFE RELEASE, on the SAME delayed-cancel schedule.

        This is what the correction buys, and it is the case the owner selected:
        the submitter was cancelled mid-flight, its late runtime is accounted
        for, the ending can therefore NAME and remove that exact runtime, absence
        is then observed, and only then is the lane released and a successor
        admitted. Before the correction every ending refused for want of a
        runtime to name, so no release was reachable here at all.

        The absence remains the FAKE's answer; the ORDER of the evidence is what
        this measures.
        """
        adapter, order, _inside = self.cancelled_mid_launch()
        self.assertEqual(self.row()["runtime_id"], "runtime-1")
        self.assertEqual(self.lane_holders(), [ATTEMPT])

        ended = self.ending(adapter, reason="the cancelled worker never answered")

        # THE EXACT LATE RUNTIME IS WHAT WAS REMOVED.
        self.assertEqual(ended[:3], ("answered", "retained", "absent"), ended)
        self.assertIn("remove", order)
        self.assertEqual([one["runtime_id"] for one in adapter.abandoned],
                         ["runtime-1"])
        self.assertEqual(self.row()["execution_runtime"], "destroyed")
        self.assertEqual(self.row()["cleanup"], "retained")
        # AND ONLY NOW IS THE RESERVATION GIVEN BACK.
        self.assertEqual(self.lane_holders(), [])
        self.claimed(offer_id="offer-2", attempt_id=SUCCESSOR)
        activate_assignment(self.store, self.port, attempt_id=SUCCESSOR,
                            expect=self.expect())
        replacement = self.Custodian([])
        follows = request_runtime_start(self.store, replacement,
                                       attempt_id=SUCCESSOR)
        self.assertEqual(follows["decision"], "attached")
        self.assertEqual(self.lane_holders(), [SUCCESSOR])

    def test_the_failed_start_cleanup_reaches_quiescence_unknown_once_fenced(self):
        """THE TYPED GUARD, REACHED THIS TIME, with the setup this Work allows.

        Review 2026-09-25T18-00-11Z: leaving the fencing setup out and counting
        the earlier refusal as coverage is not coverage. So this fails the start
        into `uncertain` -- which commits the failed-start record the ending is
        authorized by -- then models a FENCED AUTHORITY rather than driving the
        local cancellation, and only then calls the ending. What answers is the
        guard the rule lives in: `runtime-observation` / `quiescence-unknown`,
        whose message says there is NOTHING TO PROVE ABSENT.
        """
        adapter, order = self.prepared()
        self.unknown_outcome(adapter)
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

        adapter.start_failure = None
        # THE FENCE IS MODELLED AT THE AUTHORITY, NOT DRIVEN LOCALLY, and the
        # reason is itself a finding: `request_cancellation` moves this attempt's
        # axis from `uncertain` to `cancel-requested`, which makes the guard
        # below UNREACHABLE -- the ending then refuses for a missing runtime
        # identity instead. So this case models the other real ordering: the
        # authority has moved on while THIS manager's start outcome is unknown.
        #
        # THE SIMULATED AUTHORITY PROJECTION, named as such: the ending asks
        # `port.assignment_of`, and advancing the accepted fake's answer is
        # FIXTURE SETUP, not evidence about a real authority.
        self.session.live_assignment = dict(
            self.session.live_assignment, generation=2)
        # THE SIMULATED AUTHORITY PROJECTION, named as such. The ending asks
        # `port.assignment_of` whether this generation is still live, and the
        # accepted fake keeps answering generation 1 after its own fence. A real
        # authority would not, so the fixture advances the projection -- this is
        # setup, not evidence, and it is the only reason the deeper guard is
        # reachable at all.
        self.session.live_assignment = dict(
            self.session.live_assignment, generation=2)

        class Capable(type(adapter)):
            def destroy_failed_start(inner, command):
                raise AssertionError("the ending reached the destroy with an "
                                     "unknown outcome")

        capable = Capable(order)
        capable.listing = []
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.authorize_failed_start_cleanup(
                self.store, self.port, capable, attempt_id=ATTEMPT,
                retention_policy_digest=RETENTION)

        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "quiescence-unknown"))
        self.assertIn("nothing to prove absent", caught.exception.message)
        self.assertEqual(self.lane_holders(), [ATTEMPT])
        self.assertEqual(self.row()["cleanup"], "pending")

    def test_the_failed_start_cleanup_also_releases_nothing_here(self):
        """THE SECOND PUBLIC ENTRY that reaches the lane release, also refusing.

        AND THE BOUNDARY IT ACTUALLY STOPS AT IS ASSERTED, not the one I first
        expected. `authorize_failed_start_cleanup` carries a typed
        `runtime-observation` / `quiescence-unknown` guard for an `uncertain`
        attempt -- I READ it at intake.py:2175 and did NOT reach it, because an
        earlier boundary refuses first: a failed start is fenced at the authority
        before anything is destroyed, and this assignment is still authorized to
        execute. Reaching the deeper guard would mean fencing the generation
        first, which is setup this stage does not add. So this case proves what
        it can measure -- this ending releases NOTHING here -- and records the
        rest as a source reading rather than as executed evidence.
        """
        adapter, order = self.prepared()
        self.unknown_outcome(adapter)
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

        adapter.start_failure = None
        # THE ACCEPTED CUSTODIAN LACKS THIS ENDING'S OWN CAPABILITY, so without
        # supplying it the call refuses `integrity/schema` for a missing
        # `destroy_failed_start` -- true, and not the boundary under test. My
        # controlled adapter supplies one that REFUSES TO BE CALLED, so the case
        # cannot pass on a stub's answer: if the ending ever got past the
        # unknown-outcome guard, this would fail loudly instead.
        class Capable(type(adapter)):
            def destroy_failed_start(inner, command):
                raise AssertionError("the ending reached the destroy with an "
                                     "unknown outcome")

        capable = Capable(order)
        capable.listing = []
        capable.observation = dict(adapter.observation)
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.authorize_failed_start_cleanup(
                self.store, self.port, capable, attempt_id=ATTEMPT,
                retention_policy_digest=RETENTION)

        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("fenced at the authority before anything is destroyed",
                      caught.exception.message)
        self.assertEqual(self.lane_holders(), [ATTEMPT])
        self.assertEqual(self.row()["cleanup"], "pending")
        self.assertNotIn("remove", order)

    # -- the replacement -------------------------------------------------------

    def test_a_replacement_is_refused_while_the_submitter_may_continue(self):
        """THE POINT OF HOLDING IT: no second execution over this Work.

        A successor attempt of the same Work asks to start while the first
        attempt's submission outcome is unknown. The lane's predecessor
        interlock refuses it, and the measurement that matters is that the
        successor's own adapter was never asked to start anything.
        """
        adapter, _order = self.prepared()
        self.unknown_outcome(adapter)
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(self.lane_holders(), [ATTEMPT])

        # THE SUCCESSOR IS FULLY ADMITTED UP TO THE LANE, so the lane is what
        # refuses it. Without activation it refuses earlier -- "not activated" --
        # which is true but is a different boundary than the one under test.
        self.claimed(offer_id="offer-2", attempt_id=SUCCESSOR)
        activate_assignment(self.store, self.port, attempt_id=SUCCESSOR,
                            expect=self.expect())
        replacement = self.Custodian([])
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, replacement,
                                  attempt_id=SUCCESSOR)

        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.assertEqual(replacement.started, [],
                         "the replacement reached the adapter")
        self.assertEqual(self.lane_holders(), [ATTEMPT])


    # -- and the release that DOES happen, so the pair discriminates ----------

    def test_the_resource_is_released_once_the_start_is_settled_and_absent(self):
        """POSITIVE RELEASE, WITH THE EVIDENCE THE HELD CASES LACK.

        Without this the held cases above would be satisfied by a lane that is
        simply never given back, and "the replacement is refused" would be
        satisfied by a replacement that can never run. Here the submission
        SETTLES -- a runtime is attached and named -- the ending then observes
        absence and destroys, the lane is released, and the successor is admitted
        and reaches its adapter.

        The absence is still the FAKE's answer. What this case establishes is the
        shape of the predicate, not that a real daemon stopped.
        """
        adapter, order = self.prepared()
        started = request_runtime_start(self.store, adapter,
                                        attempt_id=ATTEMPT)
        self.assertEqual(started["runtime_id"], "runtime-1")
        self.assertEqual(self.lane_holders(), [ATTEMPT])

        answered = self.ending(adapter, reason="the worker never answered")

        self.assertEqual(answered[:3], ("answered", "retained", "absent"),
                         answered)
        self.assertEqual(order, ["fence", "remove"])
        self.assertEqual(self.row()["execution_runtime"], "destroyed")
        self.assertEqual(self.row()["cleanup"], "retained")
        # THE LANE IS GIVEN BACK, and only now.
        self.assertEqual(self.lane_holders(), [])
        # AND THE SUCCESSOR IS ADMITTED: it reaches its own adapter, which is
        # what every held case above denies.
        self.claimed(offer_id="offer-2", attempt_id=SUCCESSOR)
        activate_assignment(self.store, self.port, attempt_id=SUCCESSOR,
                            expect=self.expect())
        replacement = self.Custodian([])
        follows = request_runtime_start(self.store, replacement,
                                        attempt_id=SUCCESSOR)
        self.assertEqual(follows["decision"], "attached")
        self.assertEqual(len(replacement.started), 1)
        self.assertEqual(self.lane_holders(), [SUCCESSOR])


    # -- the release side, ON A CANCELLED PATH --------------------------------

    def test_a_cancelled_attempt_releases_once_its_runtime_is_accounted(self):
        """R2, RELEASE SIDE: cancellation whose runtime CAN be accounted for.

        The difference from the held cases is exactly when the submission
        settled. Here the runtime is attached BEFORE the cancellation, so the
        ordered quiescence has an identity to act on: the adapter is actually
        asked to stop it, the ending then observes absence, the lane is released
        and the successor is admitted. That is "supported completion plus runtime
        accounting, THEN release" on a cancelled path rather than an ordinary
        post-start abandonment.

        The absence is still the FAKE's answer; what this establishes is the
        shape of the predicate and the ORDER of its evidence.
        """
        adapter, order = self.prepared()
        started = request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(started["runtime_id"], "runtime-1")
        self.assertEqual(self.row()["runtime_id"], "runtime-1")

        cancelled = attempts.request_cancellation(
            self.store, self.port, accepted.Agent(), adapter,
            attempt_id=ATTEMPT, reason="cancelled after the runtime attached")

        # THE FENCE HAPPENED AND THE RUNTIME WAS ACCOUNTED FOR: this time the
        # quiescence order had an identity, and the adapter was asked to stop it.
        self.assertTrue(cancelled["fenced"]["fenced"])
        self.assertEqual(self.row()["execution_runtime"], "cancel-requested")
        self.assertEqual([one["runtime_id"] for one in adapter.stopped],
                         ["runtime-1"])
        # STILL HELD UNTIL AN ENDING SETTLES IT.
        self.assertEqual(self.lane_holders(), [ATTEMPT])

        ended = self.ending(adapter, reason="the cancelled worker never answered")
        self.assertEqual(ended[:3], ("answered", "retained", "absent"), ended)
        self.assertEqual(self.row()["execution_runtime"], "destroyed")
        self.assertEqual(self.row()["cleanup"], "retained")
        self.assertEqual(self.lane_holders(), [])

        # AND ONLY NOW IS THE REPLACEMENT ADMITTED.
        self.claimed(offer_id="offer-2", attempt_id=SUCCESSOR)
        activate_assignment(self.store, self.port, attempt_id=SUCCESSOR,
                            expect=self.expect())
        replacement = self.Custodian([])
        follows = request_runtime_start(self.store, replacement,
                                       attempt_id=SUCCESSOR)
        self.assertEqual(follows["decision"], "attached")
        self.assertEqual(len(replacement.started), 1)
        self.assertEqual(self.lane_holders(), [SUCCESSOR])


    # -- the positive counterpart to the reviewer's pending-submitter case -----

    def test_release_follows_the_submitter_returning_on_the_same_schedule(self):
        """THE POSITIVE COUNTERPART, in the reviewer's own two-handle shape.

        `review_pending_submitter_release.py` proves that a second manager
        cancelling, reconciling and ending an attempt CANNOT release while the
        original `adapter.start` has not returned. This is the other half: the
        same schedule, the same second handle, and then the original call comes
        back -- after which the ending settles, the lane is released and a
        successor is admitted.

        Both halves matter together: without the first, release is unsafe;
        without this one, the gate could be a permanently closed door.
        """
        adapter, order = self.prepared()
        other = ControlStore.open(self.path, incarnation="second-manager",
                                  clock=lambda: accepted.NOW)
        self.addCleanup(other.close)
        submitted = adapter.start
        seen = {}

        def pending(operands):
            answer = submitted(operands)
            attempts.request_cancellation(
                other, self.port, accepted.Agent(), adapter,
                attempt_id=ATTEMPT, reason="cancel while the submit is pending")
            attempts.reconcile_runtime(other, adapter, attempt_id=ATTEMPT)
            # THE GATE, WHILE THE SUBMITTER IS STILL ON THE STACK.
            try:
                worker_manager.abandon_attempt(
                    other, self.port, adapter, attempt_id=ATTEMPT,
                    reason="another manager observed the runtime",
                    retention_policy_digest=RETENTION)
                seen["early"] = "answered"
            except ContractRefusal as refusal:
                seen["early"] = (refusal.category, refusal.code,
                                 refusal.message)
            seen["lane_while_pending"] = self.lane_holders()
            return answer

        adapter.start = pending
        try:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        except ContractRefusal as refusal:
            seen["late_return"] = refusal.code

        # WHILE PENDING: refused, and the reservation is untouched.
        self.assertEqual(seen["early"][:2], ("refused", "precondition"),
                         seen["early"])
        self.assertIn("has not returned to the manager that made it",
                      seen["early"][2])
        self.assertEqual(seen["lane_while_pending"], [ATTEMPT])

        # AFTER THE SUBMITTER RETURNED: the SAME ending settles and releases.
        #
        # The same act, with the same reason. The first call fenced and journalled
        # its intent before my gate refused the settlement, so retrying with a
        # DIFFERENT reason is a different act at one identity and the store
        # refuses it by §4.2 -- which I learned here by writing it wrong. The
        # ending is retryable, not re-describable.
        ended = self.ending(adapter,
                            reason="another manager observed the runtime")
        self.assertEqual(ended[:3], ("answered", "retained", "absent"), ended)
        self.assertEqual(self.lane_holders(), [])
        self.claimed(offer_id="offer-2", attempt_id=SUCCESSOR)
        activate_assignment(self.store, self.port, attempt_id=SUCCESSOR,
                            expect=self.expect())
        replacement = self.Custodian([])
        follows = request_runtime_start(self.store, replacement,
                                       attempt_id=SUCCESSOR)
        self.assertEqual(follows["decision"], "attached")
        self.assertEqual(self.lane_holders(), [SUCCESSOR])


    def test_the_return_marker_alone_does_not_release_the_resource(self):
        """THE MARKER'S BOUNDED MEANING, asserted rather than trusted.

        Review 2026-09-25T18-48-10Z: "local return alone is not real-engine
        completion proof". So this takes the fault path where NOTHING is listed:
        the submitting call has demonstrably returned -- the marker is present --
        and the resource STILL stays held, because runtime accounting and absence
        are separate conditions the gate also requires.

        Together with the reviewer's `review_fault_return_release` case, which
        settles a fault whose runtime IS known, this fixes the marker's meaning
        from both sides: necessary, and not sufficient.
        """
        adapter, order = self.prepared()
        self.unknown_outcome(adapter)
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)

        # THE SUBMITTER RETURNED, and the manager knows it.
        self.assertTrue(attempts.start_submission_returned(
            self.store, attempts._require_attempt(self.store, ATTEMPT)))
        # AND THE RESOURCE IS STILL HELD, because nothing accounts for a runtime.
        self.assertIsNone(self.row()["runtime_id"])
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        ended = self.ending(adapter, reason="nothing was ever listed")
        self.assertEqual(ended[0], "refused", ended)
        self.assertEqual(self.lane_holders(), [ATTEMPT])
        self.assertNotIn("remove", order)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases defined in THIS module.

    The accepted fixture carries its own cases; re-running them here would
    inflate this stage's evidence with another suite's.
    """
    suite = unittest.TestSuite()
    for owner in list(globals().values()):
        if (isinstance(owner, type) and issubclass(owner, unittest.TestCase)
                and owner.__module__ == __name__):
            for name in loader.getTestCaseNames(owner):
                if name in owner.__dict__:
                    suite.addTest(owner(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
