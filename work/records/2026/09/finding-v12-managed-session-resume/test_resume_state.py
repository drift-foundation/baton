"""What the retained subject allows, ASSERTED rather than described.

Owner reroute 250274 asks for the real continuation input and for any
additional selection it needs. `resume_state.py` reads the retained stores;
this asserts what that read found, so the conclusion is a failing check when it
stops being true rather than a paragraph somebody has to re-derive.

EVERY STORE HERE IS OPENED READ-ONLY, through the public `open_readonly`
constructors, and no act is committed. Nothing is started, no runtime is
reached, and nothing under `/home/sl/baton-runs` is written. The source
citations are read from the PINNED manager snapshot rather than the checkout,
for the reason W247941's review made plain: cwd independence is not provenance.

WHAT THIS ESTABLISHES, in one sentence: the half of a managed resume that this
dossier was worried about -- a finalized provider context to resume -- is
present and ready, and the half nobody was worried about -- a verdict that asks
for a correction -- does not exist and cannot be made to exist on this subject.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                      # pragma: no cover
    sys.path.insert(0, HERE)

import resume_state                                           # noqa: E402


class TheRetainedSubjectIsResumableAndHasNothingToCorrect(unittest.TestCase):
    """The two halves of a restore, read from the accepted run's own stores."""

    @classmethod
    def setUpClass(cls):
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        for place in (resume_state.CONTROL, resume_state.JOBS):
            if not os.path.isfile(place):
                raise unittest.SkipTest(f"{place} is not present to read")
        cls.control = ControlStore.open_readonly(
            resume_state.CONTROL, incarnation="resume-state-checks",
            clock=lambda: resume_state.NOW)
        cls.jobs = JobStore.open_readonly(
            resume_state.JOBS, authority_uuid=resume_state.AUTHORITY,
            incarnation="resume-state-checks",
            clock=lambda: resume_state.NOW)

    @classmethod
    def tearDownClass(cls):
        cls.jobs.close()
        cls.control.close()

    def test_the_product_that_answers_is_the_pinned_snapshot(self):
        """Not the checkout, and the receipt says so by digest."""
        held = resume_state.provenance()
        self.assertEqual(held["not_from_snapshot"], [])
        self.assertIn("baton_v12.worker_manager.provider_context",
                      held["modules"])

    def test_the_line_is_ACCEPTED_and_therefore_closed_to_corrections(self):
        """The honest outcome of W239533, and what it costs this Job.

        `record_verdict` maps `accepted` to the line state `accepted` and
        records integration eligibility; `changes-requested` is the only
        disposition that produces `correction-ready`, and `grant_writer`
        admits a correction writer from `idle` or `correction-ready` alone.
        So this one value is why no correction round can open here.
        """
        from baton_v12.worker_manager import review_cycles
        line = review_cycles.line_of(self.control, resume_state.LINE)
        self.assertEqual(line["state"], "accepted")
        self.assertEqual(line["current_checkpoint_id"],
                         resume_state.CHECKPOINT)
        self.assertEqual(line["revision"], 1)

    def test_the_accepted_verdict_is_the_lines_own_integration_eligibility(
            self):
        """Read through the product's own accepted-verdict reader.

        `integration_checkpoint` refuses unless the line is `accepted`, the
        named checkpoint is its current frozen one, and the eligibility row
        names a verdict whose recorded disposition is exactly `accepted` with
        matching digests. Reaching an answer here IS the assertion that the
        retained verdict is an acceptance and not something read loosely.
        """
        from baton_v12.worker_manager import review_cycles
        held = review_cycles.integration_checkpoint(self.control,
                                                    resume_state.LINE)
        self.assertIsNotNone(held)
        self.assertEqual(held["checkpoint_id"], resume_state.CHECKPOINT)
        self.assertEqual(held["line_id"], resume_state.LINE)
        # AND THE NAMED VERDICT ITSELF, read back through `verdict_of`, which
        # proves the row against its own committed act before answering.
        verdict = review_cycles.verdict_of(self.control, held["verdict_id"])
        self.assertEqual(verdict["disposition"], "accepted")
        self.assertEqual(verdict["checkpoint_id"], resume_state.CHECKPOINT)
        self.assertEqual(verdict["line_id"], resume_state.LINE)

    def test_no_further_review_can_attach_to_this_line(self):
        """`attach_review` admits `review-ready` only, and this is `accepted`.

        This is a SOURCE CITATION against the pinned snapshot, not a
        behavioural probe: attaching a review would be a durable act on a
        retained store, which this claim does not have and does not want.
        """
        place = os.path.join(resume_state.SNAPSHOT, "baton_v12",
                             "worker_manager", "review_cycles.py")
        with open(place, encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn('if line["state"] != "review-ready"', source)
        self.assertIn('{"accepted": "accepted", "changes-requested":',
                      source)

    def test_the_producer_context_IS_there_to_resume(self):
        """The half a restore needs, and it survived cleanup intact.

        A managed resume is a SECOND USE of the producer's own provider
        context at generation 1. That predecessor has to be finalized and
        undamaged -- `context_use_of` reports `held` with
        `generation-damaged` when the retained generation no longer validates
        -- and here it reports `ready` at generation 0.
        """
        from baton_v12.worker_manager import provider_context
        held = provider_context.context_use_of(self.control,
                                               resume_state.PRODUCER_ATTEMPT)
        self.assertEqual(held["status"], "ready")
        self.assertEqual(held["generation"], 0)
        self.assertIsNone(held["reason"])
        self.assertTrue(held["context_id"].startswith("context-"))

    def test_no_owner_committed_correction_exists_for_the_checkpoint(self):
        """Asked by derived identity, not by scanning for something like one."""
        from baton_v12.job_manager import episodes, submission
        stages = list(submission.stage_rows(self.jobs))
        self.assertTrue(stages)
        for stage in stages:
            with self.subTest(job=stage["job_id"]):
                held = episodes.correction_operation_id(
                    stage["job_id"], resume_state.CHECKPOINT)
                self.assertIsNone(self.jobs.operation_record(held))

    def test_the_product_REFUSES_to_build_a_restore_prompt_here(self):
        """The finding, in the product's own words.

        `correction_feedback_of` is the reader a restore invocation uses to
        compose its prompt. Asked over this subject it refuses at its first
        gate, because the producer's only context use is generation 0 -- an
        `open` invocation. There is no restore to feed.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import provider_context
        with self.assertRaises(ContractRefusal) as caught:
            provider_context.correction_feedback_of(
                self.control, self.jobs, resume_state.PRODUCER_ATTEMPT)
        self.assertIn("serving feedback belongs to a restore invocation",
                      str(caught.exception))

    def test_the_restore_reader_requires_a_changes_requested_verdict(self):
        """Why no verdict of this subject's could ever serve.

        Even with a restore invocation admitted, `correction_feedback_of`
        holds the opening verdict's disposition to `changes-requested` AND
        the retained report's own `verdict` member to the same string. Both
        gates read the frozen custody, so neither can be satisfied by an
        acceptance however it is presented. A SOURCE CITATION, for the same
        reason as above.
        """
        place = os.path.join(resume_state.SNAPSHOT, "baton_v12",
                             "worker_manager", "provider_context.py")
        with open(place, encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn('verdict["disposition"] != "changes-requested"', source)
        self.assertIn('report["verdict"] != "changes-requested"', source)
        self.assertIn('_refuse("correction verdict disagrees with this '
                      'restore")', source)

    def test_the_reviewer_was_told_every_verdict_was_equally_valid(self):
        """So the acceptance is a judgement, not an artefact of the criteria.

        This matters to the selection: if the criteria had steered the
        reviewer toward accepting, the missing correction would be a defect in
        the review packet and the answer would be to fix it. They did not --
        the executed criteria say all three verdicts are valid and that no
        outcome is better for the reviewer than another.
        """
        place = ("/home/sl/baton-runs/independent-review-248377/run/task.json")
        if not os.path.isfile(place):
            self.skipTest(f"{place} is not present to read")
        import json
        with open(place, encoding="utf-8") as handle:
            criteria = json.load(handle)["instructions"]
        self.assertIn("Every one of the three is a valid review result",
                      criteria)
        self.assertIn("there is no outcome here that is better for you than "
                      "another one", criteria)

    def test_a_separate_review_JOB_already_carries_its_own_criteria(self):
        """Which retires the product seam PLAN.md pinned as unavoidable.

        The pinned seam was reasoned from ONE Job carrying one digest-sealed
        input manifest, so both roles necessarily read the same task string.
        The owner's split gives each Job its own task document, and the
        executed review Job's is review criteria that the implementation Job
        never saw. Stage-specific requirements therefore need no product
        change; the combined-Job shape is what needed one.
        """
        place = ("/home/sl/baton-runs/independent-review-248377/run/task.json")
        if not os.path.isfile(place):
            self.skipTest(f"{place} is not present to read")
        import json
        with open(place, encoding="utf-8") as handle:
            criteria = json.load(handle)["instructions"]
        self.assertIn("You are the independent reviewer", criteria)
        self.assertIn("YOU ARE NOT THE IMPLEMENTER", criteria)
        self.assertIn("your checkout is read-only", criteria.lower())


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
