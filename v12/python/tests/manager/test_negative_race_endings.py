"""W32382: the local OCI negative and race endings, on a real engine.

`work/records/2026/08/finding-v12-local-oci-negative-race-endings/`.

Split from W6636 by the 2026-08-28 approver scheduling ruling. The
one-container topology, the production-provider crossing and the cleanup
ordering W6636 established are PRESERVED here rather than restated: this
module subclasses that composition's fixture, so a case here runs against the
same real daemon, the same built reference worker image and the same manager
seams, and a change that broke the positive arc would break these too.

WHAT IT ADDS is the endings the positive arc does not reach: an offer that
expired, a start that created a container and then failed, a terminal worker
disposition that is not `completed`, and a runtime deadline the manager itself
called time on.

WHERE THE FIFTH ENDING LIVES. `unsupported-version` is the one named ending
this module deliberately does NOT re-prove. W32576's
`test_refused_session_engine` is in the SAME serial registry, subclasses the
SAME fixture, and drives the whole crossing on a real daemon -- a refusal
derived from the session's own certified profile after the container exists,
exact removal, positive absence, launch-root teardown, the lane given back only
once the daemon agrees, sibling preservation and restart replay. A second copy
here would be coverage without evidence, so this module points at it instead.
"""

from __future__ import annotations

import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import oci
from baton_v12.worker_manager import (authorize_failed_start_cleanup,
                                      activate_assignment, authorize_cleanup,
                                      decide_retention, observe,
                                      reconcile_runtime, request_freeze,
                                      request_intake, request_runtime_start,
                                      retain_manifest, runtime_lane,
                                      settle_claim, submit_claim)

from baton_v12.worker_manager import (advance_deadline,
                                      deadline_cleanup_of, deadline_of,
                                      observe_deadline)

from .test_lifecycle_composition import (Lifecycle, POLICY, RETENTION,
                                         RecordingAgent)
from .test_offers import MUCH_LATER, NOW


class NegativeEndings(Lifecycle):
    """Every ending that is not the completed arc."""

    def test_an_expired_offer_creates_no_runtime_and_no_runtime_delivery(
            self):
        """A reservation that timed out is a reservation nobody may execute.

        The settlement retires the claim identity as `settlement-expired`, and
        the crossing into execution has to be closed afterwards exactly as it
        is for a claim somebody else won.
        """
        given, assignment = self.reserved()
        # NOTHING COMMITTED, and the deadline has passed.
        self.session.settle_answer = {"kind": "retired", "record": {
            "disposition": "settlement-expired",
            "reason": "the settlement deadline passed"}}
        settled = settle_claim(self.store, self.port, offer_id=self.offer,
                               now=MUCH_LATER)
        self.assertTrue(settled["adopted"], settled)
        self.assertEqual(self.offer_row()["state"], "settlement-expired")

        with self.assertRaises(ContractRefusal) as denied:
            activate_assignment(self.store, self.port,
                                attempt_id=self.attempt,
                                expect=dict(self.live))
        self.assertIn("has no committed claim", str(denied.exception))

        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertIn("is not activated", str(refused.exception))

        # NO CONTAINER, asked of the daemon, AND NO RUNTIME DELIVERY.
        #
        # Review [P2]: the first version said "no delivery" and proved "not
        # mounted", which are two states and one word. Manager-side
        # materialization is allowed and happens here -- the fixture mints a
        # launch root when the adapter is built -- and what an expired offer
        # must not produce is a delivery a RUNTIME received. That is what is
        # asserted, and the root's survival is asserted beside it so the two
        # states stay visibly different.
        self.assertEqual([argv for argv in self.engine_calls
                          if "run" in argv], [])
        self.assertEqual(self.carrying(self.labels()), [])
        self.assertTrue(os.path.exists(adapter.launch_delivery.root),
                        "the manager-side root is the manager's until it is "
                        "settled; only a RUNTIME delivery is forbidden here")

    def test_a_post_create_failure_leaves_no_duplicate_and_no_container(
            self):
        """THE RACE THIS ORDERING EXISTS FOR, with the failure INJECTED.

        Review [P1]: the first version ran one ordinary successful start and
        then checked that a second was refused. That is duplicate-start
        coverage and it never exercised the boundary it named -- the engine
        never created a container and then failed on the way back, so the
        failed-start settlement was not reached at all.

        The engine really runs, so the container really exists; the port then
        raises on the way back, which is exactly what a driver or transport
        fault looks like from the manager's side.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)

        real, faulted = self.spawn, []

        def create_then_fail(argv):
            answer = real(argv)
            if "run" in argv:
                faulted.append(list(argv))
                raise ContractRefusal(
                    "unavailable", "transport",
                    "the engine created the runtime and then the call failed")
            return answer

        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        adapter.run = oci.EnginePort(create_then_fail)
        with self.assertRaises(ContractRefusal) as failed:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertEqual(len(faulted), 1, faulted)
        self.assertIn("created the runtime", str(failed.exception))

        # THE EXACT RUNTIME THE FAILED START CREATED IS ATTACHED, which is
        # what makes it nameable by the ordinary destroy crossing.
        created = self.carrying(self.labels())
        self.assertEqual(len(created), 1, created)
        row = self.attempt_row()
        self.assertIsNotNone(row["runtime_id"])
        self.assertTrue(created[0].startswith(row["runtime_id"][:12]),
                        (created, row["runtime_id"]))

        # AND NO REPLACEMENT IS STARTED, on the retry or on reconciliation.
        healthy = self.adapter(roots=roots, mounts=self.plan(roots),
                               launch_delivery=adapter.launch_delivery)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, healthy,
                                  attempt_id=self.attempt, inputs=inputs)
        reconcile_runtime(self.store, healthy, attempt_id=self.attempt)
        self.assertEqual(self.attempt_row()["runtime_id"], row["runtime_id"])
        self.assertEqual(len(self.carrying(self.labels())), 1)

        # AND IT CONVERGES THROUGH THE FAILED-START CROSSING, WITH NOTHING
        # MANUFACTURED.
        #
        # W32648 review [P1]: this used to observe `worker_disposition
        # ="unable"`, freeze an output, take intake, decide retention and
        # reach the receipt-authorized `authorize_cleanup` -- the whole set of
        # preconditions the finding exists to remove. The engine CREATED and
        # started the container before the call failed, so "the worker never
        # ran" is something this manager cannot know; `output.py`'s contract is
        # that the handled turn outcome gates the disposition and a proof the
        # caller can write is not proof.
        #
        # What authorizes the ending now is the manager's own durable
        # `runtime.start-failed` record, written by `request_runtime_start`
        # when the start above failed -- against a real daemon, with a real
        # container to remove.
        self.settled(row["runtime_id"])
        reconcile_runtime(self.store, healthy, attempt_id=self.attempt)
        # THE UNTRUSTED RESULT DIRECTORY, with a sentinel in it. M33800 makes
        # the existing unique per-attempt directory the custody boundary: it
        # began untrusted and stays untrusted, and this ending deletes nothing.
        place = os.path.join(roots["workspace"], "result-attempt")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "sentinel.txt"), "wb") as handle:
            handle.write(b"whatever the worker got to")

        self.session.live_assignment = None
        settled = authorize_failed_start_cleanup(
            self.store, self.port, healthy, attempt_id=self.attempt,
            retention_policy_digest=RETENTION)

        # `retained` RATHER THAN `complete`, because the result directory
        # stays. Nothing was frozen and no artifact was decided, so there is
        # nothing to count -- the material that stays IS that directory.
        self.assertEqual(settled["cleanup"], "retained", settled)
        self.assertEqual(self.attempt_row()["execution_runtime"], "destroyed")
        # NOTHING WAS FABRICATED ON THE WAY THERE.
        self.assertEqual(self.attempt_row()["worker_disposition"], "none")
        self.assertEqual(self.attempt_row()["output"], "open")
        self.assertEqual(
            [dict(one) for one in self.store._connection.execute(
                "SELECT * FROM intakes")], [])
        # THE DAEMON IS EMPTY BEFORE THIS METHOD RETURNS. Fixture cleanup is
        # only a backstop, and a case that leaned on it was asserting nothing.
        self.assertEqual(self.carrying(self.labels()), [])
        self.assertFalse(os.path.exists(healthy.launch_delivery.root))
        # ...AND THE UNTRUSTED DIRECTORY IS EXACTLY WHERE IT WAS.
        with open(os.path.join(place, "sentinel.txt"), "rb") as handle:
            self.assertEqual(handle.read(), b"whatever the worker got to")

    def test_plan_rejected_takes_the_same_cleanup_crossing(self):
        """A terminal disposition that is not `completed` ends the same way.

        The acceptance requires force-removal, exact absence, provider
        teardown and settlement to be ONE crossing whatever the worker
        answered -- so this drives the arc with `plan-rejected` and asserts the
        same endings the completed arc asserts.

        `plan-rejected` PUBLISHES NO ENVELOPE, and that is the frozen rule
        rather than a convenience: the completion envelope IS the completion
        signal, and the other dispositions are the endings where a worker may
        have died before publishing one.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               outputs=declared,
                               credential_delivery=delivery)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.settled(runtime_id)
        reconcile_runtime(self.store, adapter, attempt_id=self.attempt)

        # THE MATERIAL EXISTS AND THE ENVELOPE DOES NOT, which is exactly the
        # frozen difference this case is for: the completion envelope IS the
        # completion signal, so only `completed` requires one. The declared
        # output is still declared REQUIRED by the assignment's own manifest,
        # and that rule is not a disposition's to relax.
        self.produced(roots, declared)
        observe(self.store, attempt_id=self.attempt,
                axis="worker_disposition", value="plan-rejected")
        request_freeze(self.store, self.port, adapter,
                       attempt_id=self.attempt, disposition="plan-rejected")
        self.assertEqual(self.attempt_row()["output"], "frozen")

        receipt = request_intake(self.store, self.port, adapter,
                                 attempt_id=self.attempt)
        artifacts = [one["artifact_id"] for one in receipt["artifacts"]]
        decide_retention(self.store, self.port, adapter,
                         attempt_id=self.attempt, artifact_ids=artifacts,
                         disposition="discard-after-intake",
                         retention_policy_digest=RETENTION)

        self.session.live_assignment = None
        settled = authorize_cleanup(self.store, self.port, adapter,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=RETENTION)
        self.assertEqual(settled["cleanup"], "complete", settled)
        self.assertEqual(settled["state"], "absent")
        self.assertEqual(self.attempt_row()["execution_runtime"], "destroyed")
        # THE ENGINE, NOT THE ROW.
        self.assertEqual(self.carrying(self.labels()), [])
        # AND BOTH DELIVERED ROOTS ARE GONE, which is the half a runtime
        # observation can never establish.
        self.assertEqual(delivery.state, "torn-down")
        self.assertFalse(os.path.exists(delivery.root))
        self.assertFalse(os.path.exists(
            adapter.launch_delivery.root))

    def test_a_reached_deadline_takes_the_same_cleanup_crossing(self):
        """THE FIFTH NAMED ENDING, and the last one this Work was waiting on.

        W32577 ruled the runtime deadline and composed it: the Worker Manager
        owns the authoritative clock, persists the exact deadline with its
        policy generation BEFORE the start, and expiry records a typed
        `deadline-reached` observation that by itself kills nothing. A
        `cancel` policy must first commit an authority-owned cancellation or
        fence, and only then may the exact runtime be removed.

        WHAT THIS CASE ADDS TO THAT CHILD'S OWN EVIDENCE. `test_runtime_
        deadline_engine` proves the crossing under a separately authorized,
        environment-supervised gate that the ordinary registry does not run.
        This Work's acceptance is that the deadline takes the SAME crossing as
        the completed arc -- so it is asserted here, beside `plan-rejected`,
        in the ordinary serial registry and against the same daemon, the same
        built image and the same seams. A change that broke the positive arc
        breaks this too, which is the whole reason this module subclasses that
        fixture rather than restating it.

        NOTHING IS FABRICATED TO GET HERE. No worker disposition is written,
        no output is frozen and no intake receipt is manufactured: the worker
        was running when its deadline arrived and never said anything, which
        is exactly the ending this door exists for.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               credential_delivery=delivery)

        # THE MANAGER'S OWN CLOCK, which is what the ruling makes
        # authoritative. The case moves it; it does not move the deadline.
        now = [NOW]
        self.store._clock = lambda: now[0]
        # AND THE AUTHORITY'S AFTER-STATE, because a `cancel` policy fences
        # before it removes anything and the ending reads the fence back.
        self.session.discharge_answer["kind"] = "runtime-absent"
        cancelled = self.session.cancel

        def fencing(command):
            answer = cancelled(command)
            self.session.live_assignment = None
            self.session._work = dict(
                self.session._work, phase="block",
                gate="runtime-quiescence:1",
                fenced_generations=[{"generation": 1, "cause": "cancelled",
                                     "reason": command["reason"]}])
            return answer

        self.session.cancel = fencing

        policy = {"policy_digest": POLICY, "policy_generation": 1,
                  "duration_seconds": 1, "action": "cancel"}
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs, deadline_policy=policy)
        runtime_id = self.attempt_row()["runtime_id"]
        # THE CONTAINER IS REALLY RUNNING when its deadline arrives. That is
        # this ending's distinguishing fact: the worker is up and the manager
        # is the one calling time.
        self.assertEqual(adapter.observe(runtime_id)["state"], "running")
        self.assertTrue(runtime_lane(self.store, self.attempt)
                        ["held_by_this_attempt"])

        pin = deadline_of(self.store, attempt_id=self.attempt)
        self.assertEqual(pin["policy"]["policy_generation"], 1)
        now[0] = pin["deadline_at"]

        # THE OBSERVATION ALONE TOUCHES NOTHING, which is the ruling's own
        # sentence: expiry records that the deadline was reached and never by
        # itself kills, fences, cancels or discards output.
        before = list(self.engine_calls)
        observe_deadline(self.store, self.port, attempt_id=self.attempt)
        self.assertEqual(self.engine_calls, before)
        # ASKED OF THE DAEMON: the container this attempt attached is still
        # the one carrying these labels, and it is still running.
        [carried] = self.carrying(self.labels())
        self.assertTrue(runtime_id.startswith(carried[:12])
                        or carried.startswith(runtime_id[:12]),
                        (carried, runtime_id))
        self.assertEqual(adapter.observe(runtime_id)["state"], "running")

        settled = advance_deadline(self.store, self.port,
                                   RecordingAgent(self.trace), adapter,
                                   attempt_id=self.attempt,
                                   retention_policy_digest=RETENTION)
        proof = settled["cleanup"]
        # THE SAME CROSSING THE COMPLETED ARC TAKES: exact removal, positive
        # absence, BOTH provider teardowns, and settlement.
        self.assertEqual(proof["observed"]["state"], "absent")
        for provider in ("credentials", "launch"):
            self.assertEqual(
                proof["observed"][provider]["lifecycle_state"], "torn-down")
        self.assertEqual(self.attempt_row()["execution_runtime"], "destroyed")
        # THE ENGINE, NOT THE ROW.
        self.assertEqual(self.carrying(self.labels()), [])
        self.assertFalse(os.path.exists(delivery.root))
        self.assertFalse(os.path.exists(adapter.launch_delivery.root))
        # AND NOTHING WAS FABRICATED ON THE WAY.
        row = self.attempt_row()
        self.assertEqual(row["worker_disposition"], "none")
        self.assertEqual(row["output"], "open")
        self.assertEqual(
            [dict(one) for one in self.store._connection.execute(
                "SELECT * FROM intakes")], [])
        # THE LANE IS GIVEN BACK ONLY ON THAT ABSENCE.
        self.assertFalse(runtime_lane(self.store, self.attempt)
                         ["held_by_this_attempt"])
        # AND THE PROOF REPLAYS rather than being re-decided.
        self.assertEqual(
            deadline_cleanup_of(self.store, attempt_id=self.attempt,
                                retention_policy_digest=RETENTION), proof)

    def test_no_ending_settles_before_every_required_one_is_established(self):
        """THE LANE IS NOT RELEASED EARLY.

        Positive container absence alone does not settle a cleanup while a
        delivered root is unresolved -- W6636 established that at the unit
        boundary; this drives it on a REAL runtime, so the ordering claim is
        about a container the daemon really removed.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               outputs=declared)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.settled(runtime_id)
        reconcile_runtime(self.store, adapter, attempt_id=self.attempt)
        self.produced(roots, declared)
        self.published(roots, declared)
        observe(self.store, attempt_id=self.attempt,
                axis="worker_disposition", value="completed")
        request_freeze(self.store, self.port, adapter,
                       attempt_id=self.attempt, disposition="completed")
        receipt = request_intake(self.store, self.port, adapter,
                                 attempt_id=self.attempt)
        decide_retention(
            self.store, self.port, adapter, attempt_id=self.attempt,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="discard-after-intake",
            retention_policy_digest=RETENTION)
        self.session.live_assignment = None

        # THE LAUNCH ROOT IS HELD OPEN by making its removal impossible to
        # prove: the adapter reports `unresolved`, and the manager may not
        # call that a clean ending however absent the container is.
        real = adapter._launch_ended
        adapter._launch_ended = lambda proved, why: {
            "lifecycle_state": "unresolved",
            "why": "held open by this case"}
        try:
            pending = authorize_cleanup(self.store, self.port, adapter,
                                        attempt_id=self.attempt,
                                        retention_policy_digest=RETENTION)
        finally:
            adapter._launch_ended = real
        self.assertNotIn("cleanup", pending, pending)
        self.assertEqual(self.attempt_row()["cleanup"], "pending")

        # AND THE REUSE BOUNDARY IS ACTUALLY ASKED. Review [P1]: a pending row
        # is not proof that every consumer refuses reuse, and the first
        # version inferred one from the other. A replacement start on this
        # attempt is the reuse this ordering guards, so it is attempted -- and
        # it must refuse WITHOUT starting anything.
        before = len(self.carrying(self.labels()))
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt,
                                  inputs=roots["inputs"])
        self.assertIn("execution is", str(refused.exception))
        self.assertEqual(len(self.carrying(self.labels())), before)
        # THE CONTAINER REALLY IS GONE, which is what makes this an ordering
        # claim rather than a failure to destroy.
        self.assertEqual(self.attempt_row()["execution_runtime"], "destroyed")
        self.assertEqual(self.carrying(self.labels()), [])

        # AND A REAL SUCCESSOR IS REFUSED WHILE THIS ENDING IS UNPROVED.
        #
        # THE ORDER USED TO BE VOLUNTARY AND THIS CASE SAID SO. When it was
        # written no owner arbitrated one lane across two attempts --
        # `posture_slots` is keyed `(attempt_id, posture)`, so a successor's
        # slot is a different slot and nothing consulted an unsettled
        # predecessor -- and a case asserting a refusal would have been
        # asserting a guard that did not exist. Mandatory child W32649 landed
        # that owner, so the relation is now ENFORCED and asserted rather than
        # witnessed: the successor is a real attempt, offered, claimed and
        # activated, and its start is refused BEFORE the predecessor's ending
        # is proved.
        predecessor = self.attempt
        self.assertTrue(runtime_lane(self.store, predecessor)
                        ["held_by_this_attempt"])
        self.attempt = f"{predecessor}-successor"
        # W16823: the authority answers a CLOSED claim result, so a case that
        # re-points the fence re-points the member rather than the whole.
        self.session.claim_answer = dict(self.session.claim_answer,
                                         assignment=dict(self.live))
        self.session.live_assignment = dict(self.live)
        next_roots = self.roots()
        next_given, next_assignment = self.activated()
        next_inputs = self.composed(next_roots, next_given, next_assignment)
        successor = self.adapter(roots=next_roots,
                                 mounts=self.plan(next_roots))
        with self.assertRaises(ContractRefusal) as held:
            request_runtime_start(self.store, successor,
                                  attempt_id=self.attempt,
                                  inputs=next_inputs)
        # PINNED TO THE RELATION THAT REFUSED, not to the word "lane". Two
        # guards in `_occupy_lane` overlap for a successor on the SAME four
        # part lane -- the by-Work predecessor query and the table's own
        # primary key -- and they are different facts: the first says a
        # predecessor's ending is unsettled, the second says two callers raced
        # for one lane. Measured: neutering the predecessor query alone left
        # this case passing on the primary key's refusal, which is a case
        # asserting less than it reads. So the exact predecessor sentence is
        # what this asserts.
        self.assertIn("still holds this Work's runtime lane",
                      str(held.exception))
        # AND THE REFUSAL CREATED NOTHING. The predecessor's container is
        # already gone, so a lane taken here would show up as a container the
        # daemon holds for this assignment while an ending is unproved --
        # which is the state this whole ordering exists to prevent.
        self.assertEqual(self.carrying(self.labels()), [])
        self.assertEqual(runtime_lane(self.store, self.attempt)["holder"],
                         predecessor)
        self.assertIsNone(self.attempt_row()["runtime_id"])

        # AND THE RETRY, once the root can be proved gone, settles.
        #
        # THE LIVE ASSIGNMENT IS CLEARED AGAIN because activating the
        # successor re-pointed it: `authorize_cleanup` destroys the runtime of
        # an assignment that has ENDED, and the predecessor's has. The
        # successor's activation is a fact about the successor.
        self.attempt = predecessor
        self.session.live_assignment = None
        done = authorize_cleanup(self.store, self.port, adapter,
                                 attempt_id=self.attempt,
                                 retention_policy_digest=RETENTION)
        self.assertEqual(done["cleanup"], "complete", done)
        self.assertEqual(self.attempt_row()["cleanup"], "complete")
        self.assertEqual(self.attempt_row()["execution_runtime"], "destroyed")
        self.assertEqual(self.carrying(self.labels()), [])
        self.assertFalse(runtime_lane(self.store, predecessor)
                         ["held_by_this_attempt"])

        # ...AND ONLY THEN DOES THE SUCCESSOR TAKE THE LANE. One winner, after
        # the ending is established, which is the acceptance's own sentence.
        self.attempt = f"{predecessor}-successor"
        request_runtime_start(self.store, successor, attempt_id=self.attempt,
                              inputs=next_inputs)
        self.assertEqual(len(self.carrying(self.labels())), 1)
        self.assertIsNotNone(self.attempt_row()["runtime_id"])
        self.assertTrue(runtime_lane(self.store, self.attempt)
                        ["held_by_this_attempt"])


class DockerNegativeEndings(NegativeEndings, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanNegativeEndings(NegativeEndings, unittest.TestCase):
    engine = "podman"
    required = False
