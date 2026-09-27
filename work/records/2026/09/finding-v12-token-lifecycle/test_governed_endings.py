"""W275774 — the INTAKE endings return the governed resource.

Review 16:05:19Z: "Next implement actual intake authorize_cleanup/abandon_attempt
endings." Those are the endings `tools/single_worker.py` actually uses, so they are
why required governance was still disabled: the finalization return I wired last
claim is never reached in that tool.

AND THE EVIDENCE IS THE CLEANUP'S OWN, NOT A DOCUMENT SHAPE. Review 16:05:19Z again:
"document shape alone is not runtime/writer/effect proof." So the cessation is read
from the COMMITTED cleanup record and answers nothing unless that record carries both
halves -- `state == "absent"` (the exact runtime positively gone, the same fact a gate
discharge requires) and adopted `directory_custody` (each governed root normalized
under this manager's own custody, which is what justifies reporting no surviving
writer). Anything less returns nothing and leaves the resource held.

Real disposable stores through the intake suite's own fixtures, controlled custodian,
no live engine, no container created or signalled.
"""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts, intake, tokens

from tests.manager.test_intake import (
    ATTEMPT, RETENTION, Custodian, RetainedAndCompleteAreDifferentEndings,
    TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence)


class TheEndingReturnsTheResource(RetainedAndCompleteAreDifferentEndings):
    """The cleanup ending, with the token authority actually attached."""

    def attempt_row(self):
        return attempts._require_attempt(self.store, ATTEMPT)

    def governance(self):
        return tokens.workspace_governance()

    def reserved(self):
        """One governed start's worth of records for this attempt's workspace.

        The attempt's own pinned workspace object is used, so the domain here is
        the one a governed start would have reserved rather than a convenient
        stand-in.
        """
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = self.attempt_row()
        governance = self.governance()
        reservation = governance.reserve(
            self.store, attempt,
            operation=attempts._start_operation_id(attempt))
        container = attempt["runtime_id"]
        reservation.bind(container)()
        reservation.settle(container)
        return governance, tokens.domain_of("workspace", "66:4242")

    def cleaned(self, disposition="discard-after-intake", **kwargs):
        """The real `authorize_cleanup`, governed."""
        self.retained_ready(disposition)
        self.ended()
        governance, domain = self.reserved()
        answer = intake.authorize_cleanup(
            self.store, self.port, Custodian(**kwargs), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION, govern=governance)
        return answer, governance, domain

    # -- the ending that proves cessation -------------------------------------

    def test_a_complete_cleanup_returns_the_workspace(self):
        """THE ENDING THE REAL TOOL USES, now returning what it held."""
        answer, _, domain = self.cleaned()
        self.assertEqual(answer["cleanup"], "complete")
        self.assertEqual(answer["state"], "absent")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "a proved-absent cleanup must return the resource")

    def test_the_next_attempt_over_that_workspace_may_then_proceed(self):
        """The whole point: the lifecycle is no longer one-shot."""
        _, governance, domain = self.cleaned()
        second = governance.reserve(
            self.store, {"runtime_attempt_id": "attempt-2",
                         "workspace_device": 66, "workspace_inode": 4242},
            operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)

    def test_a_retained_ending_also_returns_it(self):
        """Retention keeps MATERIAL, not the runtime. The container is still gone
        and the roots are still under this manager's custody, so the resource is
        free -- reporting otherwise would hold a workspace because bytes were
        kept."""
        answer, _, domain = self.cleaned("retain")
        self.assertEqual(answer["cleanup"], "retained")
        self.assertEqual(tokens.outstanding(self.store, domain), [])

    def test_a_repeated_cleanup_replays_and_returns_the_same_generation(self):
        """REVIEW 16:05:19Z ASKED FOR THE REPLAY, and this is its shape here.

        The ending is journalled, so a second authorization replays it. The return
        is idempotent and bound to the execution and operation that reserved the
        generation, so the replay answers the same ending and touches no other
        generation -- which is what makes a return that failed after the ending
        recoverable by simply running the ending again.
        """
        answer, governance, domain = self.cleaned()
        again = intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION, govern=governance)
        self.assertEqual(again["cleanup"], answer["cleanup"])
        self.assertEqual(tokens.outstanding(self.store, domain), [])

    def test_the_return_after_a_failed_return_still_converges(self):
        """AUTHORITY SUCCEEDED, RETURN DID NOT: the case the review named.

        The ending commits and the release then fails -- here because the token
        store refuses the evidence offered. The resource stays held, which is
        correct, and running the ending again converges: the replayed ending
        returns the generation it always named.
        """
        self.retained_ready("discard-after-intake")
        self.ended()
        governance, domain = self.reserved()

        class Failing:
            """A governance whose release refuses, standing in for a return that
            could not be committed after the ending already had been."""

            def __init__(self, real):
                self.real = real
                self.identity = real.identity
                self.resource_kind = real.resource_kind

            def release(self, *args, **named):
                raise ContractRefusal("refused", "precondition",
                                      "the return could not be committed")

        with self.assertRaises(ContractRefusal):
            intake.authorize_cleanup(
                self.store, self.port, Custodian(), attempt_id=ATTEMPT,
                retention_policy_digest=RETENTION, govern=Failing(governance))
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "a return that failed leaves the resource held")
        # AND THE ENDING RUN AGAIN CONVERGES.
        intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION, govern=governance)
        self.assertEqual(tokens.outstanding(self.store, domain), [])

    # -- and the endings that prove nothing -----------------------------------

    def test_a_blocked_cleanup_returns_nothing(self):
        """Blocked is an answer, not a cessation: the adapter was never called."""
        # The attempt must EXIST before its boundary identity can be pinned; a
        # blocked cleanup is about material never taken into custody, not about a
        # missing attempt. Measured: without this the pin refused at
        # `_require_attempt` rather than reaching the case's own subject.
        self.frozen_attempt()
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = self.attempt_row()
        governance = self.governance()
        governance.reserve(self.store, attempt,
                           operation=attempts._start_operation_id(attempt))
        domain = tokens.domain_of("workspace", "66:4242")
        intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION, govern=governance)
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "a cleanup that destroyed nothing must hold the resource")

    def test_an_unproved_cessation_composes_nothing(self):
        """`_resource_cessation` is the gate, and it answers None on either half.

        A surviving runtime and an absent-but-uncustodied cleanup both prove
        nothing, and neither is turned into a termination here.
        """
        attempt = {"runtime_attempt_id": ATTEMPT, "runtime_id": "runtime-1"}
        for settled in ({"state": "survived", "directory_custody": None},
                        {"state": "survived", "directory_custody": {"a": 1}},
                        {"state": "absent", "directory_custody": None}):
            with self.subTest(settled=settled):
                self.assertIsNone(
                    intake._resource_cessation(settled, attempt, ATTEMPT))
        self.assertEqual(
            intake._resource_cessation(
                {"state": "absent", "directory_custody": {"a": 1}},
                attempt, ATTEMPT),
            {"container": "runtime-1", "stopped": True, "helpers": []})

    def test_an_ungoverned_cleanup_is_unchanged(self):
        answer = self.settle("discard-after-intake")
        self.assertEqual(answer["cleanup"], "complete")


class TheAbandonedEndingReturnsTheResource(
        TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence):
    """THE FOURTH ENDING, which review 16:29:48Z found ungoverned in the real tool.

    An abandonment is the case a resource token exists for -- a runtime whose worker
    never answered -- so an ungoverned abandonment would hold its workspace for the
    life of the store. It is also the ending where a failed return hurts most,
    because it is terminal: the replay is the LAST thing that will ever run for that
    attempt.
    """

    def evidence(self):
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        governance = tokens.workspace_governance()
        operation = attempts._start_operation_id(attempt)
        reservation = governance.reserve(self.store, attempt,
                                        operation=operation)
        container = attempt["runtime_id"]
        reservation.bind(container)()
        reservation.settle(container)
        return governance, tokens.domain_of("workspace", "66:4242")

    def abandoned_governed(self, governance):
        self.adapter = self.Abandoner()
        return intake.abandon_attempt(
            self.store, self.port, self.adapter, attempt_id=ATTEMPT,
            reason=self.REASON, retention_policy_digest=RETENTION,
            govern=governance)

    def test_an_abandonment_returns_the_governed_workspace(self):
        self.running_attempt()
        self.fence_for_this_attempt()
        governance, domain = self.evidence()
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        self.abandoned_governed(governance)
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "an abandoned ending must return what the start reserved")

    def test_a_failed_return_converges_on_the_terminal_replay(self):
        """THE DEFECT REVIEW 16:29:48Z FOUND, as my own case.

        The ending commits, the return fails, and because an abandonment is terminal
        the retry is the only remaining chance. The replay path now releases, so the
        generation is not stranded.
        """
        self.running_attempt()
        self.fence_for_this_attempt()
        governance, domain = self.evidence()

        class Failing:
            def __init__(self, real):
                self.identity = real.identity
                self.resource_kind = real.resource_kind

            def release(self, *args, **named):
                raise ContractRefusal("refused", "precondition",
                                      "the return could not be committed")

        with self.assertRaises(ContractRefusal):
            self.abandoned_governed(Failing(governance))
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "a failed return leaves the resource held")
        # THE TERMINAL REPLAY, which is the last thing that runs for this attempt.
        self.abandoned_governed(governance)
        self.assertEqual(tokens.outstanding(self.store, domain), [])

    def test_a_stale_terminal_replay_cannot_release_a_later_generation(self):
        """The replay is bound to the generation ITS OWN start reserved."""
        self.running_attempt()
        self.fence_for_this_attempt()
        governance, domain = self.evidence()
        self.abandoned_governed(governance)
        second = governance.reserve(
            self.store, {"runtime_attempt_id": "attempt-2",
                         "workspace_device": 66, "workspace_inode": 4242},
            operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)
        # THE STALE REPLAY, arriving after generation 2 took the resource.
        self.abandoned_governed(governance)
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [2],
                         "a stale terminal replay released a live generation")


if __name__ == "__main__":
    unittest.main()
