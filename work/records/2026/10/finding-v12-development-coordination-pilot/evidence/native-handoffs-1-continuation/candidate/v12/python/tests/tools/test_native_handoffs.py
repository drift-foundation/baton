"""W385331 — one native handoff, end to end, over the composed stage deployment.

WHAT THESE CASES PROVE, and each is one of the slice's named proofs: an
implementer stops at a clarification or an in-scope finding, its exact
checkpoint is retained and nothing is published; the configured reviewer is
delivered the question and answers it in its own invocation; the SAME admitted
task resumes on the retained checkpoint with the answer delivered to it, with
ZERO human acts; the resumed turn's final submission then goes through the
ordinary independent technical review; a genuine ambiguity escalates ONCE to
the configured decision recipient and the execution stays held; and a restart
at the cuts between those steps duplicates no message and no attempt.

WHAT IS REAL HERE is `tests.tools.test_stage_execution.ComposedOneJobCase`'s
whole arrangement: the serving factory, real local Authority, Job, Control and
Integration stores, a real version-controlled line materialized by the accepted
checkpoint profile, the actual `claude_agent` workload entered through
`baton_worker.serve_exchange` over the namespaces the deployment mounted, and
`review_driver`'s endings. The engine is the fixture's daemonless callable and
the PROVIDER is a scripted process seam that writes files where a model would
-- there is no daemon, no container, no image, no network, no live model and no
live credential anywhere in this file.

THE ONLY ROW THIS SUITE WRITES BY HAND is the creation record naming the
handoff-capable `/3` template, exactly as `tests.job_manager.test_native_handoffs`
writes it: what is under test is what the deployment does with an admitted
template version, and composing a whole creation through its four deployment
ports would be proving the creation operation instead.
"""

import copy
import json
import os
import unittest
from types import SimpleNamespace

from baton_v12 import native_handoff
from baton_v12.authority import Authority
from baton_v12.authority import messages as work_messages
from baton_v12.contracts import digest, job_input_identity
from baton_v12.job_manager import (documents, episodes, job_control,
                                   native_handoffs, role_contract)
from baton_v12.worker_manager import review_cycles

from tools import stage_execution

from tests.job_manager import fixtures
from tests.tools import test_stage_execution as composed

OWNER = "baton.slaw"
REVIEWER = "baton.reviewer"
HANDOFF_OUTPUTS = composed.SHARED_OUTPUTS + (
    (role_contract.HANDOFF_OUTPUT, "directory-result"),
    (role_contract.RESPONSE_OUTPUT, "directory-result"))

REQUEST = {"kind": native_handoff.CLARIFICATION_KIND,
           "body": "Is the narrower harness the one in scope, or the wider?",
           "evidence": [{"reference": "harness.py",
                         "note": "the partial edit this question is about"}],
           "continuation": "finish the harness once the base is settled"}
ANSWER = {"disposition": "answer",
          "body": "the narrower harness is the admitted one",
          "rationale": "the task's requirements name one harness and no "
                       "other", "escalation": None}
ESCALATION = {"disposition": "escalate",
              "body": "both readings are admitted by the requirements",
              "rationale": "nothing in the accepted scope selects one",
              "escalation": {"ambiguity": "two incompatible harnesses are "
                                          "admitted",
                             "options": ["narrower", "wider"],
                             "recommendation": "narrower"}}


class HandoffJobCase(composed.ComposedOneJobCase):
    """One composed Job under the `/3` template and the native-handoff
    profile, with the routing and the answer capability configured."""

    def setUp(self):
        super().setUp()
        # THE `/3` UNION OF DECLARED OUTPUTS, composed exactly as the parent
        # composes the shared three: each role writes its own half and answers
        # the rest `missing-optional`, and none is required.
        manifest = copy.deepcopy(self.config["input_manifest"])
        held = manifest["outputs"][0]
        manifest["outputs"] = [dict(held, name=name, type=kind, path=name,
                                    required=False)
                               for name, kind in HANDOFF_OUTPUTS]
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        self.config["input_manifest"] = manifest
        self.manifest = manifest
        job = fixtures.job(
            "job-a", input_digest=job_input_identity(manifest),
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[
                fixtures.stage("implementation", self.work),
                fixtures.stage("review", self.work,
                               depends_on=[{"job_id": "job-a",
                                            "kind": "implementation"}]),
                fixtures.stage("integration", self.work,
                               depends_on=[{"job_id": "job-a",
                                            "kind": "review"}])])
        job["control"] = {"profile": job_control.NATIVE_HANDOFF_PROFILE}
        self.submission = dict(fixtures.submission(jobs=[job]),
                               schema=documents.SUBMISSION_CONTROL_SCHEMA)
        # THE CONFIGURED ROUTING AND THE EXPLICIT GRANT. Existing `review`
        # membership grants nothing here; the reviewer answers under its own
        # `answer-handoff` capability in the Work's effective scope, and the
        # decision recipient is the human owner and never the reviewer.
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy(work_messages.ROUTING_POLICY, {
                "schema": work_messages.ROUTING_SCHEMA,
                "reviewer": REVIEWER, "decision_recipient": OWNER})
            authority.grant_capability(
                REVIEWER, work_messages.ANSWER_CAPABILITY, scope=self.scope)
        finally:
            authority.dispose()
        self.prompts = []

    # -- the one hand-written row ---------------------------------------------

    def template_job(self, job, version=role_contract.HANDOFF_TEMPLATE):
        request = {"schema": "baton.v12.job-template-request/1"}
        job._connection.execute(
            "INSERT OR REPLACE INTO template_jobs (job_id, work_id, "
            "submission_id, template_version, state, request, request_digest, "
            "resolution_digest, resolution, task_document, "
            "submission_signature, intended_at, created_at, incarnation, "
            "holder) VALUES (?, ?, ?, ?, 'created', ?, ?, ?, ?, NULL, "
            "?, ?, ?, 'stage-composed', NULL)",
            ("job-a", self.work, self.submission["submission_id"], version,
             json.dumps(request), digest(request), digest({"v": version}),
             json.dumps({"template": version}), json.dumps({"kind": "submit"}),
             fixtures.NOW, fixtures.NOW))
        job._connection.commit()

    # -- the provider seam, recording what it was asked ----------------------

    def provider(self, edits=None, status=0):
        import claude_agent

        run = super().provider(edits, status)

        def recording(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.prompts.append(argv[-1])
            return run(argv, **options)

        return recording

    # -- the reads this suite makes, through public owners -------------------

    def authority(self):
        held = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        self.addCleanup(held.dispose)
        return held

    def messages(self):
        return self.authority().work_messages(self.work)

    def attempts_of(self, held, role):
        return sorted(self.worker_of(held.composed, role).stage._prepared)

    def operations(self, job, kind):
        return job._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = ?",
            (kind,)).fetchone()[0]

    def line(self, held):
        deployment = self.deployment_of(held)
        return review_cycles.line_of(deployment.control,
                                     deployment.line()["line_id"])

    # -- the composed rounds -------------------------------------------------

    def started(self):
        from baton_v12.job_manager import submit as submit_jobs

        job, control, serving = self.serving()
        submit_jobs(job, self.submission)
        self.template_job(job)
        self.assertTrue(native_handoffs.handoff_capable(job, "job-a"))
        self.drive(job, serving, "implementation", "waiting")
        attempt_id = self.only_attempt(serving, "implementation")
        return SimpleNamespace(job=job, control=control, composed=serving,
                               attempt_id=attempt_id,
                               roots=self.mounted(serving, "implementation",
                                                  attempt_id))

    def yielded(self, kind=native_handoff.CLARIFICATION_KIND):
        """One implementation turn that stops at a question, driven to the
        host's own `awaiting-answer` state by ordinary ticks."""
        held = self.started()
        request = dict(REQUEST, kind=kind)
        self.assertEqual(
            self.turn(held.control, "implementation", held.attempt_id,
                      held.roots,
                      edits={"harness.py": "print('the partial harness')\n",
                             "handoff/request.json": json.dumps(request)}),
            0)
        self.drive(held.job, held.composed, "implementation",
                   native_handoffs.AWAITING_STATE)
        held.request = request
        return held

    def answered(self, held, response=ANSWER):
        """The configured reviewer's own invocation over the yielded
        checkpoint, answering the delivered question."""
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt_of(held.composed, "review",
                                       exclude=getattr(held, "review", None))
        self.assertEqual(
            self.turn(held.control, "review", attempt,
                      self.mounted(held.composed, "review", attempt),
                      edits={"response.json": json.dumps(response)}), 0)
        held.review = attempt
        return held

    def resumed(self, held):
        """The continuation: the SAME line, the retained checkpoint, a fresh
        attempt, and the reply delivered to it."""
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        attempt = self.only_attempt_of(held.composed, "implementation",
                                       exclude=held.attempt_id)
        held.resumed = attempt
        held.resumed_roots = self.mounted(held.composed, "implementation",
                                          attempt)
        return held

    def submitted(self, held):
        """The resumed turn's FINAL submission and the ordinary review."""
        self.assertEqual(
            self.turn(held.control, "implementation", held.resumed,
                      held.resumed_roots,
                      edits={"harness.py": "print('the finished harness')\n"}),
            0)
        self.drive(held.job, held.composed, "implementation", "completed",
                   ticks=12)
        self.drive(held.job, held.composed, "review", "waiting", ticks=12)
        reviewer = self.only_attempt_of(held.composed, "review",
                                        exclude=held.review)
        report = copy.deepcopy(
            composed.TheComposedJobTraversesReviewAndAcceptance.REPORT)
        self.assertEqual(
            self.turn(held.control, "review", reviewer,
                      self.mounted(held.composed, "review", reviewer),
                      edits={"review-report.json": json.dumps(report)}), 0)
        held.final_review = reviewer
        return held

    def reconnected(self, held):
        """A FRESH serving object over the same stores: the restart cut.

        Nothing is carried over but the stores and the engine; every
        preparation, every delivery and every ending is re-derived from
        committed records, which is what a restart is.
        """
        serving = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base), held.job,
            held.control, engine_run=self.engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(serving.close)
        self._composed = serving
        held.composed = serving
        return held

    def only_attempt_of(self, held_composed, role, *, exclude):
        found = sorted(one for one in
                       self.worker_of(held_composed, role).stage._prepared
                       if one != exclude)
        self.assertEqual(len(found), 1, found)
        return found[0]

    deployment_of = staticmethod(
        composed.TheComposedJobTraversesReviewAndAcceptance.deployment_of)
    projected = composed.TheComposedJobTraversesReviewAndAcceptance.projected


class AClarificationResumesTheSameTaskWithNoHumanAct(HandoffJobCase):

    def test_the_yield_is_retained_and_publishes_nothing(self):
        held = self.yielded()
        self.assertEqual(self.states(held.job, held.composed)["implementation"],
                         native_handoffs.AWAITING_STATE)
        # ONE DURABLE ATTRIBUTED REQUEST, authored by the assignment and not
        # by the worker, addressed to the configured reviewer.
        [request] = self.messages()
        self.assertEqual(request["kind"], native_handoff.CLARIFICATION_KIND)
        self.assertEqual(request["author"], self.config["participant"])
        self.assertEqual(request["destination"], REVIEWER)
        self.assertEqual(request["body"]["body"], REQUEST["body"])
        self.assertEqual(request["body"]["evidence"][0]["reference"],
                         "harness.py")
        # THE EXACT PARTIAL CHECKPOINT IS FROZEN, and the message names it.
        line = self.line(held)
        checkpoint = review_cycles.checkpoint_of(
            self.deployment_of(held).control, line["current_checkpoint_id"])
        self.assertEqual(checkpoint["state"], "frozen")
        # THE MESSAGE NAMES THE RETAINED HEAD OBJECT, which is what both the
        # worker's own claim and the frozen evidence spell, and the yield
        # record names the manager's checkpoint identity that froze it.
        self.assertEqual(request["checkpoint_ref"],
                         checkpoint["evidence"]["head"])
        self.assertEqual(request["body"]["checkpoint"]["reference"],
                         checkpoint["evidence"]["head"])
        # NOTHING IS PUBLISHED AND NOTHING IS ELIGIBLE: no proposal rides the
        # line and no integration checkpoint exists.
        deployment = self.deployment_of(held)
        self.assertIsNone(review_cycles.integration_checkpoint(
            deployment.control, line["line_id"]))
        self.assertEqual(deployment.control._connection.execute(
            "SELECT count(*) FROM checkpoint_verdicts").fetchone()[0], 0)
        # AND THE YIELD RECORD IS THE HOST'S OWN JOURNALLED FACT.
        live = episodes.live_of(held.job, "job-a/implementation")
        recorded = native_handoffs.yield_of(held.job, "job-a/implementation",
                                            live["episode"])
        self.assertEqual(recorded["message_id"], request["message_id"])
        self.assertEqual(recorded["checkpoint_id"],
                         checkpoint["checkpoint_id"])
        self.assertEqual(recorded["template_version"],
                         role_contract.HANDOFF_TEMPLATE)

    def test_the_reviewer_answers_and_the_same_task_resumes(self):
        held = self.answered(self.yielded())
        self.resumed(held)
        # TWO MESSAGES: the request and ONE reply, bound to it by identity and
        # digest, with the effect recorded separately and never a receipt.
        request, reply = self.messages()
        self.assertEqual(reply["reply_to"], request["message_id"])
        self.assertEqual(reply["body"]["request"]["digest"],
                         request["handoff_digest"])
        self.assertEqual(reply["author"], REVIEWER)
        self.assertEqual(reply["task_digest"], request["task_digest"])
        transition = self.authority().work_message_transition(
            reply["message_id"])
        self.assertEqual(transition["effect"],
                         work_messages.CONTINUATION_EFFECT)
        # THE CONTINUATION SPENT ITS OWN ALLOWANCE AND NO CORRECTION ROUND.
        self.assertEqual(job_control.continuations_used_in(
            held.job._connection, "job-a"), 1)
        self.assertEqual(job_control.rounds_used_in(
            held.job._connection, "job-a"), 0)
        self.assertEqual(self.operations(held.job,
                                         native_handoffs.CONTINUE_KIND), 1)
        continued = native_handoffs.continuation_of(
            held.job, "job-a/implementation", 1)
        self.assertEqual(continued["message_id"], reply["message_id"])
        # THE RESUMED WRITER IS BASED ON THE EXACT RETAINED CHECKPOINT.
        deployment = self.deployment_of(held)
        writer = review_cycles.writer_for_attempt(
            deployment.control, attempt_id=held.resumed,
            generation=deployment.generation_of(held.resumed))
        self.assertEqual(writer["based_checkpoint_id"],
                         continued["checkpoint_id"])
        self.assertEqual(self.line(held)["current_checkpoint_id"],
                         continued["checkpoint_id"])
        # AND THE REPLY REACHED THE RESUMED TURN: the worker is delivered
        # the exact correspondence beside its task, and the provider is told
        # the answer. Read from the delivered root, not from this fixture.
        with open(os.path.join(held.resumed_roots["inputs"], "handoff.json"),
                  "rb") as reading:
            delivered = json.loads(reading.read())
        self.assertEqual(delivered["schema"], native_handoffs.CONTEXT_SCHEMA)
        self.assertEqual(delivered["continuation"]["reply"]["message_id"],
                         reply["message_id"])
        self.assertEqual(delivered["continuation"]["request"]["message_id"],
                         request["message_id"])

    def test_zero_human_acts_to_the_ordinary_final_review(self):
        held = self.submitted(self.resumed(self.answered(self.yielded())))
        # THE RESUMED PROVIDER WAS TOLD THE ANSWER, verbatim.
        self.assertIn(ANSWER["body"], self.prompts[-2])
        self.assertIn(REQUEST["body"], self.prompts[-2])
        states = self.drive(held.job, held.composed, "integration", "claimed",
                            ticks=12)
        self.assertEqual(states["implementation"], "completed")
        self.assertEqual(states["review"], "completed")
        # EXACTLY TWO IMPLEMENTATION ATTEMPTS AND TWO REVIEW ATTEMPTS, on ONE
        # line, and still two messages: the final review is a verdict and
        # mints no third one.
        self.assertEqual(len(self.attempts_of(held, "implementation")), 2)
        self.assertEqual(len(self.attempts_of(held, "review")), 2)
        self.assertEqual(len(self.messages()), 2)
        self.assertEqual(self.authority().pending_handoff_requests(self.work),
                         [])
        deployment = self.deployment_of(held)
        line = self.line(held)
        accepted = review_cycles.integration_checkpoint(deployment.control,
                                                        line["line_id"])
        self.assertIsNotNone(accepted)
        checkpoint = review_cycles.checkpoint_of(deployment.control,
                                                 accepted["checkpoint_id"])
        writer = review_cycles.writer_of(deployment.control,
                                         checkpoint["writer_id"])
        self.assertEqual(writer["runtime_attempt_id"], held.resumed)
        self.assertEqual(self.projected()["route"], self.INTEGRATION_ROUTE)
        self.assertEqual(job_control.continuations_used_in(
            held.job._connection, "job-a"), 1)
        self.assertEqual(job_control.rounds_used_in(
            held.job._connection, "job-a"), 0)


class AFindingContinuesTheSameWay(HandoffJobCase):

    def test_an_in_scope_finding_is_classified_and_the_task_resumes(self):
        held = self.yielded(kind=native_handoff.FINDING_KIND)
        [request] = self.messages()
        self.assertEqual(request["kind"], native_handoff.FINDING_KIND)
        self.resumed(self.answered(held))
        self.assertEqual(self.states(held.job, held.composed)["implementation"],
                         "waiting")
        self.assertEqual(job_control.continuations_used_in(
            held.job._connection, "job-a"), 1)


class AGenuineAmbiguityEscalatesOnceAndStaysHeld(HandoffJobCase):

    def test_one_escalation_to_the_owner_and_nothing_scheduled(self):
        held = self.answered(self.yielded(), response=ESCALATION)
        self.drive(held.job, held.composed, "review",
                   native_handoffs.ANSWERED_STATE, ticks=12)
        # THE EXECUTION STAYS HELD: the implementation stage owes no admission
        # and no claim, the review stage is ANSWERED and not completed -- so
        # the integration's gate stays shut on a question -- the line admits
        # no writer, and no continuation was spent.
        states = self.states(held.job, held.composed)
        self.assertEqual(states["implementation"],
                         native_handoffs.AWAITING_STATE)
        self.assertEqual(states["review"], native_handoffs.ANSWERED_STATE)
        self.assertEqual(states["integration"], "blocked")
        answer = native_handoffs.answer_of(
            held.job, "job-a/review",
            episodes.live_of(held.job, "job-a/review")["episode"])
        self.assertEqual(answer["disposition"],
                         native_handoff.ESCALATE_DISPOSITION)
        self.assertEqual(self.line(held)["state"], "review-ready")
        self.assertEqual(job_control.continuations_used_in(
            held.job._connection, "job-a"), 0)
        # ONE ESCALATION, ADDRESSED TO THE OWNER AND NOT TO THE REVIEWER.
        request, escalation = self.messages()
        self.assertEqual(escalation["kind"], work_messages.ESCALATION_KIND)
        self.assertEqual(escalation["destination"], OWNER)
        self.assertEqual(escalation["body"]["escalation"]["options"],
                         ["narrower", "wider"])
        self.assertEqual(
            len(self.authority().handoff_escalations(self.work)), 1)
        self.assertEqual(self.authority().work_message_transition(
            escalation["message_id"])["effect"], work_messages.HELD_EFFECT)
        live = episodes.live_of(held.job, "job-a/implementation")
        hold = native_handoffs.hold_of(held.job, "job-a/implementation",
                                       live["episode"])
        self.assertEqual(hold["destination"], OWNER)
        self.assertEqual(hold["request_id"], request["message_id"])
        # AND RE-ENTRY REREADS IT RATHER THAN RAISING IT AGAIN: five more
        # ordinary ticks mint no message, no attempt, no hold and no episode.
        from baton_v12.job_manager import sweep as tick

        before = (len(self.messages()), self.attempts_of(held, "implementation"),
                  self.attempts_of(held, "review"),
                  self.operations(held.job, native_handoffs.HOLD_KIND),
                  live["episode"])
        for _ in range(5):
            tick(held.job, held.composed, now=fixtures.NOW)
        after = (len(self.messages()), self.attempts_of(held, "implementation"),
                 self.attempts_of(held, "review"),
                 self.operations(held.job, native_handoffs.HOLD_KIND),
                 episodes.live_of(held.job, "job-a/implementation")["episode"])
        self.assertEqual(after, before)
        self.assertEqual(self.states(held.job, held.composed)["implementation"],
                         native_handoffs.AWAITING_STATE)
        self.assertIsNone(self.projected()["handler"])


class AMalformedRequestIsRefusedNotPublished(HandoffJobCase):

    def test_a_request_the_adapter_cannot_bind_ends_the_turn_unable(self):
        """"Undeclared, mixed, missing or foreign output holds." A provider
        that wrote a request this adapter cannot bind -- here, one citing a
        path that is not in the tree -- produced no question anybody can
        answer: the turn ends `unable`, no claim is published, no message is
        committed, and the stage is honestly exceptional rather than silently
        a final submission."""
        held = self.started()
        request = dict(REQUEST, evidence=[{"reference": "nowhere.py",
                                           "note": "not in this tree"}])
        # THE WORKER'S OWN REFUSAL ENDS THE TURN: `serve_exchange` reports it
        # rather than publishing a claim, so the status is the worker's and
        # what matters is what the host then does with the ending.
        self.turn(held.control, "implementation", held.attempt_id, held.roots,
                  edits={"harness.py": "print('the partial harness')\n",
                         "handoff/request.json": json.dumps(request)})
        self.drive(held.job, held.composed, "implementation", "exceptional",
                   ticks=12)
        self.assertEqual(self.messages(), [])
        self.assertIsNone(native_handoffs.yield_of(
            held.job, "job-a/implementation", 1))


class ARestartBetweenTheCutsDuplicatesNothing(HandoffJobCase):

    def test_a_fresh_serving_object_rereads_the_yield_and_the_answer(self):
        held = self.yielded()
        self.reconnected(held)
        # RESTART AFTER THE YIELD: the message, the attempt and the state are
        # reread, not re-made.
        self.drive(held.job, held.composed, "review", "waiting", ticks=12)
        self.assertEqual(len(self.messages()), 1)
        self.assertEqual(self.states(held.job, held.composed)["implementation"],
                         native_handoffs.AWAITING_STATE)
        self.answered(held)
        self.reconnected(held)
        # RESTART AFTER THE ANSWER: one continuation, one reply, and the
        # resumed attempt opens exactly once.
        self.resumed(held)
        self.assertEqual(len(self.messages()), 2)
        self.assertEqual(self.operations(held.job,
                                         native_handoffs.CONTINUE_KIND), 1)
        self.assertEqual(job_control.continuations_used_in(
            held.job._connection, "job-a"), 1)
        from baton_v12.job_manager import sweep as tick

        for _ in range(3):
            tick(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(self.operations(held.job,
                                         native_handoffs.CONTINUE_KIND), 1)
        self.assertEqual(len(self.messages()), 2)
        self.assertEqual(episodes.live_of(
            held.job, "job-a/implementation")["episode"], 2)
        # AND ONLY ONE WRITER IS EVER ACTIVE ON THE LINE.
        deployment = self.deployment_of(held)
        active = deployment.control._connection.execute(
            "SELECT count(*) FROM line_writers WHERE state = 'active'"
        ).fetchone()[0]
        self.assertEqual(active, 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
