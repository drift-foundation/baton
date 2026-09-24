"""The ROUTED abandonment, through the pooled deployment's own composition.

Review 2026-09-24T09:12:54Z: "Complete StageExecution routing with actual
alternate mounts… Historical replay still traverses wrapper recovery and engine
observation: cover missing/closed roots and a fresh composition explicitly."

`test_abandonment.py` drives the single-worker composition, whose `stage` is
`None`, so its root recovery takes the `adopted_assignment_workspace` branch.
The POOLED deployment composes a `StageComposition` per worker, so the same
capability takes the OTHER branch -- the stage's own mounts, where a private
line is the writable root. That branch had no case at all; this is it.

THE FIXTURE IS THE PRODUCT'S OWN and SUBSTITUTES NO ENGINE.
`ComposedOneJobCase` composes the deployment the serving loop composes, and
its accepted `quiescing` seam already answers a removal, an identity-bound
absence sentence and a custody helper's own verb.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import intake, workspaces        # noqa: E402
from tools import single_worker, stage_execution               # noqa: E402
from tests.tools.test_stage_execution import (                 # noqa: E402
    ComposedOneJobCase)

REASON = "the pooled run stopped and this attempt never answered"


class TheRoutedAbandonmentReachesTheAllocatedWorker(ComposedOneJobCase):
    """The FOURTH ending, declared through the deployment that routes.

    THE BASE IS THE PRODUCT'S COMPOSED LIFECYCLE and its engine is the
    accepted `quiescing` seam -- which already models a removal, an
    identity-bound absence sentence AND a custody helper answering the verb it
    was asked for, through `tests.manager.test_custody.reported`. Nothing here
    substitutes an engine: the routed act runs against the same deterministic
    boundary the accepted lifecycle cases run against.
    """

    def started(self):
        """One submitted Job carried to a STARTED runtime, and no turn.

        `ComposedOneJobCase.implemented` drives the same ticks and then RUNS
        the worker; this stops one step short, which is the abandonment's
        whole subject: the manager started a runtime and its worker never
        answered. Every transition here is a `sweep`.
        """
        from baton_v12.job_manager import status as projected_status
        from baton_v12.job_manager import submit as submit_jobs
        from baton_v12.worker_manager import attempt_runtime_of
        from tests.job_manager import fixtures

        job, control, composed = self.serving()
        submit_jobs(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        attempt_id = self.only_attempt(composed, "implementation")
        # THE RUNTIME REALLY IS ATTACHED, read from the manager's own record
        # rather than inferred from the projected stage state.
        state = attempt_runtime_of(control, attempt_id)
        self.assertIsNotNone(state["runtime_id"],
                             "the stage waits but no runtime is attached")
        projected = projected_status(job, composed, observed_at=fixtures.NOW)
        [stage] = [one for one in projected["jobs"][0]["stages"]
                   if one["kind"] == "implementation"]
        self.assertEqual(stage["attempt_id"], attempt_id)
        return job, control, composed, stage, attempt_id

    def test_the_routed_ending_runs_through_the_stages_own_mounts(self):
        """The OTHER root-recovery branch, and it is proved to be the one.

        `adopted_assignment_workspace` is the branch the single-worker
        composition takes. A pooled worker holds a `StageComposition`, so the
        capability must recover the stage's own mounts instead -- and the way
        to prove which branch ran is to watch the function that belongs to the
        other one.
        """
        job, control, composed, stage, attempt_id = self.started()
        self.assertIsNotNone(
            composed.workers[0]["operations"]._worker.stage,
            "the pooled worker composes no stage; this file would be "
            "proving the single-worker branch a second time")

        adopted = []
        original = workspaces.adopted_assignment_workspace

        def watched(storage, assignment_id):
            adopted.append(assignment_id)
            return original(storage, assignment_id)

        workspaces.adopted_assignment_workspace = watched
        self.addCleanup(setattr, workspaces, "adopted_assignment_workspace",
                        original)

        # AND THE BRANCH THAT DID RUN IS NAMED POSITIVELY. An absence proof
        # alone would also pass over a call that recovered no roots at all.
        mounted = []
        held_mount = single_worker._SingleWorker._mounted

        recovered = []

        def watching(worker, stage, attempt, **operands):
            mounted.append(attempt)
            answered = held_mount(worker, stage, attempt, **operands)
            recovered.append(answered[0])
            return answered

        single_worker._SingleWorker._mounted = watching
        self.addCleanup(setattr, single_worker._SingleWorker, "_mounted",
                        held_mount)

        # THE ROOTS THE CONTAINER WAS REALLY STARTED OVER, read from the
        # stage composition's own preparation record.
        recorded = self.mounted(composed, "implementation", attempt_id)
        # AND BYTES THAT WERE THERE, so "retained" is measured rather than
        # taken from the cleanup's own word for itself.
        sentinel = os.path.join(recorded["workspace"], "kept-by-retention.txt")
        with open(sentinel, "w", encoding="utf-8") as writing:
            writing.write("the retained tree still holds this\n")

        answered = composed.abandon_attempt(attempt_id=attempt_id,
                                            reason=REASON, stage=stage)
        self.assertEqual(adopted, [], "the routed ending recovered the "
                                      "workspace roots instead of the "
                                      "stage's own mounts")
        self.assertEqual(mounted, [attempt_id],
                         "the stage's own mounts were never recovered")
        # AND THEY ARE THE RECORDED ROOTS, not merely "some roots". Review
        # 2026-09-24T09:29:06Z: a spy proves the branch executed and says
        # nothing about WHICH tree it recovered, and recovering an ordinary
        # pair for a different stage tree is exactly the failure that would
        # pass a branch assertion.
        self.assertEqual(dict(recovered[0]), dict(recorded),
                         "the ending recovered a different tree than the one "
                         "this attempt's container was started over")
        self.assertTrue(answered["fenced"].get("fenced"))
        cleanup = answered["cleanup"]
        self.assertEqual(cleanup.get("cleanup"), "retained")
        self.assertEqual(cleanup.get("state"), "absent")
        self.assertEqual(sorted(cleanup["directory_custody"]),
                         ["result", "workspace"])
        for root, record in cleanup["directory_custody"].items():
            self.assertEqual(record["root"], root)
            self.assertEqual(json.loads(record["account"])["custody"],
                             "normalize")
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id,
            retention_policy_digest=composed.deployment
            .retention_policy_digest)
        self.assertEqual(settled["cleanup"].get("cleanup"), "retained")
        # AND THE GATE IT INSTALLED IS DISCHARGED on this path too, which is
        # the composition's act rather than the router's.
        discharge = intake.abandoned_gate_discharge_of(control, attempt_id)
        self.assertIsNotNone(discharge)
        self.assertEqual(discharge.get("gate"), answered["fenced"].get("gate"))
        # RETAINED MEANS THE BYTES ARE STILL THERE. A cleanup that reported
        # `retained` over a tree it had emptied would pass every assertion
        # above.
        with open(sentinel, encoding="utf-8") as reading:
            self.assertEqual(reading.read(),
                             "the retained tree still holds this\n")

    def test_an_altered_stage_identity_is_refused_against_the_allocation(self):
        """The members that decide MOUNTS, bound to the durable record.

        Measured under claim 255665 in the single-worker fixture: with only
        the attempt bound, an altered `stage_id`, `episode` or `kind` was
        ACCEPTED -- and `kind` selects the tree a review attempt recovers.
        The pooled deployment holds a recorded allocation carrying all three,
        so the routed boundary binds them and this proves it.
        """
        job, control, composed, stage, attempt_id = self.started()
        del job, control
        before = len(self.engine.vectors)
        for member, value in (("stage_id", "job-a:review"),
                              ("episode", (stage.get("episode") or 0) + 7),
                              ("kind", "review")):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    composed.abandon_attempt(attempt_id=attempt_id,
                                             reason=REASON,
                                             stage=dict(stage,
                                                        **{member: value}))
                self.assertIn(member, caught.exception.message)
        self.assertEqual(len(self.engine.vectors), before,
                         "a refused stage identity still reached the engine")
        # AND THE RECORDED ONE STILL WORKS, so the binding is not a wall.
        answered = composed.abandon_attempt(attempt_id=attempt_id,
                                            reason=REASON, stage=stage)
        self.assertEqual(answered["cleanup"].get("cleanup"), "retained")

    def test_a_routed_prior_cancellation_is_recovered_too(self):
        """The recovery, through the deployment that ROUTES.

        `test_abandonment` proves it over the unpooled composition. This is
        the same history through the router and the stage's own mounts: the
        allocated worker is stopped, and the routed abandonment then fences by
        replaying that cancellation and settles.
        """
        job, control, composed, stage, attempt_id = self.started()
        del job
        owners = {one["worker_id"]: one["operations"]
                  for one in composed.workers}
        [operations] = [one for one in owners.values()
                        if getattr(one, "_worker", None) is not None
                        and attempt_id in getattr(
                            one._worker.stage, "_prepared", {})]
        operations.cancel_attempt(attempt_id=attempt_id,
                                  reason="the supervisor stopped this attempt")
        answered = composed.abandon_attempt(attempt_id=attempt_id,
                                            reason=REASON, stage=stage)
        self.assertTrue(answered["fenced"].get("fenced"))
        self.assertEqual(answered["intent"]["reason"], REASON)
        self.assertTrue(answered["intent"]["authority_operation_id"]
                        .startswith("authority.attempt.cancel:"))
        self.assertEqual(answered["cleanup"].get("cleanup"), "retained")
        self.assertEqual(answered["cleanup"].get("state"), "absent")
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id,
            retention_policy_digest=composed.deployment
            .retention_policy_digest))
        self.assertIsNotNone(
            intake.abandoned_gate_discharge_of(control, attempt_id))
        removals = self.removals()
        composed.abandon_attempt(attempt_id=attempt_id, reason=REASON,
                                 stage=stage)
        self.assertEqual(self.removals(), removals,
                         "the routed replay removed a runtime again")

    def test_an_altered_context_at_the_worker_cannot_divert_the_tree(self):
        """The invariant BEHIND the router's binding, measured not assumed.

        I reported under claim 255665 that `kind` "decides MOUNTS", so a
        review kind over an implementation attempt would recover the frozen
        checkpoint. **That was wrong**, and this case is the correction.
        `StageComposition._prepare` branches on `self.role` -- the worker's
        own composition -- and `_recovered` reads the attempt's DURABLE grant
        by attempt id; the caller's `stage["job_id"]` reaches
        `deployment.line_for` only on a first preparation, which an attempt
        with a started runtime no longer has.

        So a caller holding the worker's own operations, bypassing the
        router's binding entirely, still cannot divert the tree. This asserts
        that directly: the roots recovered under an altered kind, stage_id and
        episode are the roots the container was started over.

        The router's binding stays worth having as operand hygiene -- it
        refuses a wrong context before any worker is reached -- but it is not
        what keeps the tree correct, and the record should say which is which.
        """
        job, control, composed, stage, attempt_id = self.started()
        del job, control
        owners = [one["operations"] for one in composed.workers]
        [operations] = [one for one in owners
                        if getattr(one, "_worker", None) is not None
                        and attempt_id in getattr(one._worker.stage,
                                                  "_prepared", {})]
        recorded = self.mounted(composed, "implementation", attempt_id)

        recovered = []
        held_mount = single_worker._SingleWorker._mounted

        def watching(worker, stage, attempt, **operands):
            answered = held_mount(worker, stage, attempt, **operands)
            recovered.append(answered[0])
            return answered

        single_worker._SingleWorker._mounted = watching
        self.addCleanup(setattr, single_worker._SingleWorker, "_mounted",
                        held_mount)

        answered = operations.abandon_attempt(
            attempt_id=attempt_id, reason=REASON,
            stage=dict(stage, kind="review", stage_id="job-a:review",
                       episode=(stage.get("episode") or 0) + 7))
        self.assertEqual(answered["cleanup"].get("cleanup"), "retained")
        self.assertTrue(recovered, "no mount recovery happened at all")
        self.assertEqual(dict(recovered[0]), dict(recorded),
                         "an altered context diverted the recovered tree")

    def test_a_worker_composing_no_abandonment_capability_refuses(self):
        """The router's third boundary, which had no case.

        A deployment whose worker predates this capability must refuse by
        name rather than raise an attribute error somewhere inside routing.
        """
        from unittest import mock

        _job, _control, composed = self.serving()
        owners = {one["worker_id"]: one["operations"]
                  for one in composed.workers}
        wanted = next(iter(owners))

        class Incapable:
            pass

        for one in composed.workers:
            if one["worker_id"] == wanted:
                one["operations"] = Incapable()
        with mock.patch.object(stage_execution, "allocation_of",
                               return_value={"worker_id": wanted}):
            with self.assertRaises(ContractRefusal) as caught:
                composed.abandon_attempt(attempt_id="attempt-1",
                                         reason=REASON,
                                         stage={"attempt_id": "attempt-1"})
        self.assertIn("composes no", caught.exception.message)

    def test_a_fresh_composition_replays_the_committed_ending(self):
        """A RESTARTED MANAGER, not the same object asked twice.

        The repeat case in `test_abandonment` replays through the composition
        that performed the act, so its recovery is warm. This composes a
        SECOND deployment over the same stores -- which is what a restart is --
        and asks it. Nothing destructive may happen a second time.
        """
        job, control, composed, stage, attempt_id = self.started()
        first = composed.abandon_attempt(attempt_id=attempt_id, reason=REASON,
                                         stage=stage)
        removals = self.removals()

        from tests.job_manager import fixtures

        second = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base), job, control,
            engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(second.close)
        again = second.abandon_attempt(attempt_id=attempt_id, reason=REASON,
                                       stage=stage)
        self.assertEqual(again["cleanup"]["operation"],
                         first["cleanup"]["operation"])
        self.assertEqual(self.removals(), removals,
                         "the fresh composition removed a runtime again")
        self.assertEqual(
            intake.abandoned_gate_discharge_of(control, attempt_id).get(
                "gate"),
            first["fenced"].get("gate"))

    def removals(self):
        return sum(1 for one in self.engine.vectors
                   if len(one) > 1 and one[1] == "rm")

    def test_an_attempt_with_no_recorded_allocation_refuses_by_name(self):
        _job, _control, composed = self.serving()
        with self.assertRaises(ContractRefusal) as caught:
            composed.abandon_attempt(attempt_id="attempt-nobody-started",
                                     reason=REASON,
                                     stage={"attempt_id":
                                            "attempt-nobody-started"})
        self.assertIn("no recorded allocation", caught.exception.message)

    def test_an_allocation_naming_an_uncomposed_worker_refuses(self):
        from unittest import mock

        _job, _control, composed = self.serving()
        with mock.patch.object(stage_execution, "allocation_of",
                               return_value={"worker_id": "somebody-else"}):
            with self.assertRaises(ContractRefusal) as caught:
                composed.abandon_attempt(attempt_id="attempt-1",
                                         reason=REASON,
                                         stage={"attempt_id": "attempt-1"})
        self.assertIn("this deployment does not compose",
                      caught.exception.message)

    def test_the_router_binds_the_stage_before_it_reaches_a_worker(self):
        """The router's own operand rules, proved to fire FIRST.

        The worker binds the stage too, and that is deliberate; what this
        proves is that a wrong operand never reaches a composition that holds
        an engine at all.
        """
        from unittest import mock

        _job, _control, composed = self.serving()
        reached = []
        owners = {one["worker_id"]: one["operations"]
                  for one in composed.workers}
        wanted = next(iter(owners))
        for malformed in ("a string", ["a", "list"], 7, None,
                          {"attempt_id": "attempt-2"}):
            with self.subTest(stage=type(malformed).__name__):
                with mock.patch.object(stage_execution, "allocation_of",
                                       return_value={"worker_id": wanted}), \
                    mock.patch.object(
                        type(owners[wanted]), "abandon_attempt",
                        lambda *a, **k: reached.append(k)):
                    with self.assertRaises(ContractRefusal):
                        composed.abandon_attempt(attempt_id="attempt-1",
                                                 reason=REASON,
                                                 stage=malformed)
        self.assertEqual(reached, [], "a refused operand reached a worker")


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only this module's own cases."""
    suite = unittest.TestSuite()
    for name in loader.getTestCaseNames(
            TheRoutedAbandonmentReachesTheAllocatedWorker):
        if name in TheRoutedAbandonmentReachesTheAllocatedWorker.__dict__:
            suite.addTest(TheRoutedAbandonmentReachesTheAllocatedWorker(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
