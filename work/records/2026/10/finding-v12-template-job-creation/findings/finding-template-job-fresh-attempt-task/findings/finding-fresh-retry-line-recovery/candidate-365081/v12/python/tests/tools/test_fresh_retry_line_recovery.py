"""W365075 — AN `unable` IMPLEMENTATION ENDING LEAVES THE LINE UNWRITABLE.

The bound FINDING asks for safe writer ownership for a fresh retry, and asks
first that the supported recovery APIs be revalidated. They were, and the
answer is that none of them applies -- because the state the retry meets is
not one any of them transitions out of. This suite is that revalidation,
written as cases so it is a guarded fact rather than prose.

WHAT THE PARENT'S CASE REPRODUCED. A fresh retry of a settled failed Job is
offered, claimed by an authorized spare producer, and then refused before any
runtime: "line state 'review-ready' does not admit a writer".

WHAT THIS SUITE ADDS. Why the line is in that state and why nothing can leave
it:

  * `review_driver.end_implementation`'s step EIGHT freezes the line's
    checkpoint for EVERY disposition -- its own comment says "An `unable` or
    `cancelled` turn skips straight to eight and nine, which are the acts that
    actually end an attempt" -- and freezing moves the line to `review-ready`;
  * the attempt answered `unable`, so nothing was published and the Job's own
    REVIEW stage is `blocked`: its gate needs a completed implementation,
    which never happened;
  * so there is NO review attachment and there never will be, and
    `record_verdict` takes an attachment id;
  * and `grant_writer` admits a writer only from `idle` or
    `correction-ready` (review_cycles.py:1848-1864).

Every other public operation of that module is checked in
`NoSupportedOperationAdvancesIt` below, each with the precondition it refuses
on. The conclusion is a specification conflict and is pinned in PROGRESS for
an owner ruling, because the three ways out all change a rule: what an ending
with nothing to review does to the line, whether a frozen-with-no-review line
has an operator transition, or whether a fresh retry may be admitted as a
correction writer. This suite forges no verdict, erases no checkpoint and
edits no row.
"""

import json
import unittest

from baton_v12.job_manager import reconcile, sweep

from tests.job_manager import fixtures

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import review_cycles

from tests.tools.test_retry_task_lineage import (
    TheRetriedJobReachesItsOwnRuntimes as retrying)
from tests.tools.test_stage_execution import ServingCase


class TheStuckLineCase(ServingCase):
    """The parent's own fixture, asked about the line it leaves behind.

    THE HELPERS ARE BORROWED AND THE CASES ARE NOT: subclassing the parent's
    case class re-ran its five assertions under this suite's name, which this
    dossier's ancestors have been corrected for twice.
    """

    BASE = retrying.BASE
    HEAD = retrying.HEAD
    SPARE = retrying.SPARE
    PROPOSAL_OUTPUTS = retrying.PROPOSAL_OUTPUTS
    proposal_manifest = retrying.proposal_manifest
    spare_capacity_document = retrying.spare_capacity_document
    failing_pool = retrying.failing_pool
    admitted_retry = retrying.admitted_retry
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
        """THE TWO BORROWED SETUPS, SPELLED OUT.

        `retrying.setUp` and its own parent's call zero-argument `super()`,
        which is bound to the class that defines them -- so borrowing either
        across this hierarchy raises `TypeError`. What they do is small and is
        done here: the serving fixture, the non-version-controlled checkpoint
        profile, the process guard, the retry ports' identity, and the
        Authority facts a spare producer needs.
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
        held = self.failing_pool()
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        held["worker"] = worker
        held["line"] = worker.stage.deployment.line_for(self.job_id)
        return held


class TheEndingLeavesAReviewThatCannotHappen(TheStuckLineCase):

    def test_an_unable_ending_still_freezes_the_lines_checkpoint(self):
        held = self.settled()
        line = held["line"]
        self.assertEqual(line["state"], "review-ready")
        self.assertIsNotNone(line["current_checkpoint_id"])
        checkpoint = review_cycles.checkpoint_of(
            held["control"], line["current_checkpoint_id"])
        self.assertEqual(checkpoint["state"], "frozen")
        self.assertEqual(checkpoint["line_id"], line["line_id"])

    def test_nothing_is_attached_and_the_review_stage_is_blocked(self):
        held = self.settled()
        rows = held["control"]._connection.execute(
            "SELECT runtime_attempt_id FROM review_attachments").fetchall()
        self.assertEqual([tuple(one) for one in rows], [])
        self.assertEqual(
            self.stages(held["jobs"], held["composed"], self.job_id),
            {"implementation": "exceptional", "review": "blocked"})

    def test_the_writer_that_produced_it_is_revoked(self):
        """So nothing is `writing` either: the abandonment recovery's
        precondition is absent as well."""
        held = self.settled()
        rows = held["control"]._connection.execute(
            "SELECT state FROM line_writers").fetchall()
        self.assertTrue(rows)
        self.assertNotIn("active", [one["state"] for one in rows])


class NoSupportedOperationAdvancesIt(TheStuckLineCase):
    """The revalidation the FINDING asked for first, one case per API."""

    def test_the_retrys_own_preparation_meets_the_line_state(self):
        """THE REFUSAL AS THE LOOP MEETS IT, through the composition.

        `grant_writer` is not called directly here, and the two drafts that
        tried show why: asked with an attempt this manager never recorded it
        refuses "no runtime attempt ...", and asked with the retry's attempt
        and a hand-named generation it refuses "the runtime attempt is not
        the named generation of this line's Authority and Work". Both are
        true and neither is the state under test. The composition the serving
        loop uses derives every one of those operands from the attempt, so it
        is what this asks -- and it reaches the line state.
        """
        held = self.settled()
        fresh = self.retried(held)["job_id"]
        for _ in range(8):
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
        stage = self.stage_of(held["jobs"], held["composed"], fresh)
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id=self.SPARE)
        with self.assertRaises(ContractRefusal) as caught:
            worker.stage.mount(worker, dict(stage, job_id=fresh), None)
        self.assertIn("does not admit a writer", str(caught.exception))

    def test_record_verdict_has_no_attachment_to_take(self):
        held = self.settled()
        with self.assertRaises(ContractRefusal):
            review_cycles.record_verdict(
                held["control"],
                attachment_id="review-nobody-attached",
                disposition="changes-requested", profile=self.profile_seam,
                port=held["worker"].port)

    def test_restore_abandoned_correction_needs_a_writing_line(self):
        """Its own docstring is about the `writing` case; this line is not."""
        held = self.settled()
        with self.assertRaises(ContractRefusal):
            review_cycles.restore_abandoned_correction(
                held["control"], attempt_id=self.first_attempt, generation=1,
                retention_policy_digest=self.config[
                    "retention_policy_digest"],
                profile=self.profile_seam)

    def test_integration_checkpoint_answers_nothing_to_integrate(self):
        """It is a READ with a precondition, and this line does not meet it.

        `integration_checkpoint` answers only for an `accepted` line, and a
        line awaiting a review that cannot happen is not accepted -- so it
        reports absence rather than advancing anything. Asserted as the
        absence it is, because an earlier draft of this case expected a
        refusal and the operation is gentler than that.
        """
        held = self.settled()
        answered = review_cycles.integration_checkpoint(
            held["control"], held["line"]["line_id"])
        self.assertIsNone(answered)
        self.assertEqual(
            review_cycles.line_of(held["control"],
                                  held["line"]["line_id"])["state"],
            "review-ready")

    def test_audit_checkpoint_reads_and_changes_nothing(self):
        """The one operation that accepts this state, and it is a READ."""
        held = self.settled()
        before = json.dumps(dict(review_cycles.line_of(
            held["control"], held["line"]["line_id"])), default=str)
        review_cycles.audit_checkpoint(
            held["control"], held["line"]["current_checkpoint_id"],
            self.profile_seam)
        self.assertEqual(json.dumps(dict(review_cycles.line_of(
            held["control"], held["line"]["line_id"])), default=str), before)


if __name__ == "__main__":
    unittest.main()
