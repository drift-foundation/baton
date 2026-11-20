"""W385331 — the host's side of one native handoff, and what it refuses.

WHAT THESE CASES ARE ABOUT. A completed implementation invocation that asked a
question instead of submitting a candidate: the classification that happens
BEFORE publication, the yield that is not a completed stage, the dependency
window that opens for a response and closes on the answer, the resolved
continuation under its own finite allowance, and the escalation that leaves
the execution held.

WHAT IS REAL HERE. The control store, its development line, its writer, its
frozen checkpoint, its review attachment and its retained result manifests are
the accepted operations -- `tests.job_manager.test_review_driver`'s own
`ReviewResultCase`, which exists precisely so a reader of a frozen result is
driven against documents the manager really sealed. The Job store, its
submission, its control profile, its episodes and its projection are real. The
Authority is real: a real Work, a real route, a real claim, a real capability
grant and real committed messages.

WHAT IS FAKED, AND ONLY WHERE A DEPLOYMENT WOULD SUPPLY ONE: the checkpoint
profile, the authority-bound fence port, the runtime adapter and the
publication seam. There is no provider and no model anywhere in this file.

WHAT IS DELIBERATELY ABSENT. No verdict is recorded on any path a handoff
takes, no proposal is published for a yielded invocation, no receipt of any
kind is written, and `open_correction` is never called -- which is the point:
a question is not a changes-requested verdict, and resuming on one would be
forging the verdict nobody gave.
"""

import contextlib
import json
import os
import tempfile
import unittest
from unittest import mock

from baton_v12 import native_handoff
from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.job_manager import (JobStore, cancellation, documents,
                                   episodes, job_control, native_handoffs,
                                   review_driver, role_contract, submit)
from baton_v12.job_manager.projection import (owed_acts, stage_states,
                                              materialized)
from baton_v12.authority import messages as work_messages
from baton_v12.worker_manager import (create_line, freeze_checkpoint,
                                      review_cycles)
from baton_v12.worker_manager.source_boundary import nominate_source

from tests.job_manager import test_review_driver as driver
from tests.job_manager.fixtures import NOW, PROFILE, WORK_A, job, stage

WRITER = driver.WRITER
REVIEWER = driver.REVIEWER
OWNER = "baton.slaw"
HANDOFF_PROFILE = job_control.NATIVE_HANDOFF_PROFILE
TEMPLATE = role_contract.HANDOFF_TEMPLATE
TASK_DIGEST = "sha256:" + "7" * 64
POLICY_DIGEST = "sha256:" + "8" * 64
# THE RETAINED CONTINUATION, AS TEXT AND AS THE DIGEST THE REQUEST NAMES
# (review 2026-11-20T19-39-15Z R1): the implementer's own note of what
# remained, which the yield journals and the resumed attempt is delivered.
CONTINUATION_TEXT = "finish the harness once the base is settled\n"
CONTINUATION_DIGEST = digest_of_bytes(CONTINUATION_TEXT.encode("utf-8"))
CONTINUATION_REFERENCE = f"{role_contract.HANDOFF_OUTPUT}/continuation.txt"


def handoff_request(head, *, kind=native_handoff.CLARIFICATION_KIND,
                    recipient=REVIEWER, body="which base is in scope?"):
    """One worker's own request document, in the bounded handoff contract.

    THE CHECKPOINT MEMBER NAMES THE HEAD OBJECT THE WORKER SAYS IT YIELDED,
    which the host cross-binds against the checkpoint it actually froze -- the
    same shape `baton.checkpoint-review/1` uses for a reviewer's observed
    objects, and for the same reason.
    """
    return {"schema": native_handoff.HANDOFF_SCHEMA, "kind": kind,
            "body": body,
            "evidence": [{"reference": "v12/python/src/baton_v12/x.py",
                          "digest": "sha256:" + "1" * 64, "note": ""}],
            "continuation": {"reference": CONTINUATION_REFERENCE,
                             "digest": CONTINUATION_DIGEST},
            "checkpoint": {"reference": head, "digest": "sha256:" + "3" * 64},
            "recipient": recipient}


def handoff_final():
    return {"schema": native_handoff.HANDOFF_SCHEMA,
            "kind": native_handoff.FINAL_KIND}


def handoff_response(request_id, request_digest, checkpoint_id, *,
                     disposition="answer"):
    return {"schema": native_handoff.HANDOFF_SCHEMA,
            "kind": native_handoff.RESPONSE_KIND,
            "request": {"reference": request_id, "digest": request_digest},
            "disposition": disposition,
            "body": "the narrower base is the admitted one",
            "rationale": "within the accepted scope of the admitted task",
            "evidence": [],
            "checkpoint": {"reference": checkpoint_id,
                           "digest": "sha256:" + "3" * 64},
            "escalation": (None if disposition == "answer" else
                           {"ambiguity": "two incompatible bases are admitted",
                            "options": ["narrower", "wider"],
                            "recommendation": "narrower"})}


@contextlib.contextmanager
def _implementation_endings():
    """The deployment half of an implementation ending, RECORDED; the rest REAL.

    THE SHAPE IS `test_review_driver._frozen_endings`', and the reason is that
    suite's own: the quiesce, the intake, the retention and the cleanup need an
    engine, a delivered workspace and a custody tree -- a deployment's half
    that `tests/manager` drives -- while the freeze answers the attempt's own
    REAL frozen result through its accepted public owner.

    WHAT STAYS REAL IS EVERYTHING THIS SUITE IS ABOUT: the retained result
    manifest, the classification read out of it, the publication seam, the
    checkpoint freeze and the committed Authority message. A fixture that faked
    the classification would be proving its own idea of a handoff.
    """
    from baton_v12.worker_manager import frozen_output_of

    recorded = []

    def note(name, answer=None):
        def call(*operands, **named):
            recorded.append(name)
            return answer() if callable(answer) else answer
        return call

    receipt = {"receipt_digest": "sha256:" + "5" * 64,
               "artifacts": [{"artifact_id": "artifact-1"}]}

    def freeze(control, _port, _adapter, *, attempt_id, disposition):
        recorded.append("freeze")
        del disposition
        return frozen_output_of(control, attempt_id)

    real_classified = review_driver._classified_handoff

    def classify(*operands, **named):
        recorded.append("classify")
        return real_classified(*operands, **named)

    with mock.patch.object(review_driver, "reconcile_runtime",
                           note("quiesce")), \
            mock.patch.object(review_driver, "observe", note("observe")), \
            mock.patch.object(review_driver, "request_freeze", freeze), \
            mock.patch.object(review_driver, "_correlated",
                              note("correlate")), \
            mock.patch.object(review_driver, "_classified_handoff", classify), \
            mock.patch.object(review_driver, "request_intake",
                              note("intake", lambda: dict(receipt))), \
            mock.patch.object(review_driver, "decide_retention",
                              note("retain",
                                   lambda: {"disposition": "retain"})), \
            mock.patch.object(review_driver, "authorize_cleanup",
                              note("cleanup",
                                   lambda: {"state": "absent",
                                            "cleanup": "retained"})):
        yield recorded


class _Publication:
    """The publication seam, which a YIELD must never reach.

    IT COUNTS AND IT REFUSES NOTHING. A seam that raised would prove only that
    this fixture can raise; what the cases below assert is that the call list
    is EMPTY for a request and holds exactly one entry for a final submission.
    """

    def __init__(self):
        self.calls = []

    def publish(self, **operands):
        self.calls.append(operands)
        return {"proposal_id": "proposal-1", "target": "revision-1"}

    def published_of(self, *, attempt_id):
        return None


class HandoffCase(driver.ReviewResultCase):
    """One handoff-capable Job: a `/3` template, a native-handoff profile, a
    real Authority and a real line."""

    def setUp(self):
        super().setUp()
        self.jobs.close()
        self.jobs = JobStore.open(
            os.path.join(self.root, "handoff-jobs.sqlite3"),
            authority_uuid=self.AUTHORITY, incarnation="jobs-3",
            clock=self.clock)
        self.addCleanup(self.jobs.close)
        submit(self.jobs, self.submission())
        self.template_job()
        self.authority = Authority.create(
            os.path.join(self.root, "authority.sqlite3"),
            authority_uuid=self.AUTHORITY, clock=self.clock)
        self.addCleanup(self.authority.dispose)
        self.authority.create_work(WORK_A, "impl", operation_id="op-create",
                                   contract="baton.v12.contract/1")
        self.authority.add_route_handler("impl", WRITER)
        self.authority.set_policy(work_messages.ROUTING_POLICY, {
            "schema": work_messages.ROUTING_SCHEMA, "reviewer": REVIEWER,
            "decision_recipient": OWNER})
        self.scope = self.authority.project_work(WORK_A)["scope"]
        self.authority.grant_capability(
            REVIEWER, work_messages.ANSWER_CAPABILITY, scope=self.scope)
        self.producer = self.authority.session(WRITER)
        self.answerer = self.authority.session(REVIEWER)
        self.assignment = self.producer.claim(
            {"work_id": WORK_A, "operation_id": "op-claim"})["assignment"]

    # -- the two store fixtures ---------------------------------------------

    def submission(self, profile=HANDOFF_PROFILE):
        """One `/3` submission of one handoff-capable Job.

        BOTH STAGES NAME THE SAME WORK, which is what a real submission for
        this pipeline has to do -- a line is one `(authority_uuid, work_id)`
        pair, and its reviewer is an assignment of that same Work.
        """
        held = job("job-a", stages=[
            stage("implementation", WORK_A),
            stage("review", WORK_A,
                  depends_on=[{"job_id": "job-a", "kind": "implementation"}])])
        held["control"] = {"profile": profile}
        document = {"schema": documents.SUBMISSION_CONTROL_SCHEMA,
                    "submission_id": "sub-1", "jobs": [held]}
        return document

    def template_job(self, version=TEMPLATE, job_id="job-a"):
        """The creation record a real `create_template_job` would have left.

        WRITTEN AS A ROW, exactly as `DriverCase.attempt` writes the manager
        rows a runtime would have written: what this suite is about is what the
        host does with an admitted template version, and composing a whole
        creation through its four deployment ports would be proving the
        creation operation instead.
        """
        request = {"schema": "baton.v12.job-template-request/1"}
        self.jobs._connection.execute(
            "INSERT OR REPLACE INTO template_jobs (job_id, work_id, "
            "submission_id, template_version, state, request, request_digest, "
            "resolution_digest, resolution, task_document, "
            "submission_signature, intended_at, created_at, incarnation, "
            "holder) VALUES (?, ?, 'sub-1', ?, 'created', ?, ?, ?, ?, NULL, "
            "?, ?, ?, 'jobs-3', NULL)",
            (job_id, WORK_A, version, json.dumps(request), digest(request),
             digest({"v": version}), json.dumps({"template": version}),
             json.dumps({"kind": "submit"}), NOW, NOW))
        return version

    # -- the implementation round, with a REAL retained handoff --------------

    def retained_implementation(self, attempt_id, *, generation, document,
                                outputs=None, result_id=None, head=None):
        """Retain one IMPLEMENTATION result manifest carrying a handoff claim.

        The shape is `ReviewResultCase.retained`'s, with the producer's own
        participant and the handoff-capable template's own declared outputs.
        """
        from baton_v12.worker_manager import retain_manifest

        def one(name, metadata, kind="directory-result"):
            entries = [{"path": f"{name}.txt", "bytes": 3,
                        "content_digest": "sha256:" + "6" * 64}]
            content = {"entries": entries, "entry_count": 1, "total_bytes": 3,
                       "tree_digest": digest(entries)}
            return {"name": name, "type": kind, "status": "present",
                    "content_manifest": content,
                    "artifact": {"artifact_id": f"artifact-{name}-{attempt_id}",
                                 "media_type": "text/plain", "bytes": 3,
                                 "content_digest": content["tree_digest"],
                                 "locator":
                                     f"file:///var/lib/baton/{attempt_id}/{name}"},
                    "result_metadata": metadata}

        composed = outputs if outputs is not None else [
            one("proposal", {}, kind="git-change-proposal"),
            one(native_handoffs.HANDOFF_OUTPUT,
                {} if document is None
                else {native_handoff.HANDOFF_SCHEMA: document})]
        held = dict(
            driver._result_vector(),
            result_id=result_id or ("result-" + attempt_id),
            assignment_ref={"work_ref": {"authority_uuid": self.AUTHORITY,
                                         "work_id": WORK_A},
                            "participant": WRITER, "generation": generation},
            outputs=composed)
        held.pop("manifest_digest")
        held["manifest_digest"] = digest(held)
        kept = retain_manifest(self.control, held, "resultManifest")["digest"]
        self.control._connection.execute(
            "UPDATE outputs SET manifest_digest = ?, result_id = ? "
            "WHERE runtime_attempt_id = ?",
            (kept, held["result_id"], attempt_id))
        return kept, held

    def implementation_round(self, number=1, *, based=None, frozen=True):
        """A granted writer, a completed attempt and a REAL frozen result.

        The checkpoint is NOT frozen here: whether one is frozen, and whether
        anything is published, is the ENDING's decision and that is what the
        cases below are about.
        """
        attempt = self.attempt(f"writer-attempt-{number}", number, WRITER,
                               f"writer-principal-{number}")
        # THE INPUT IDENTITY A REAL `record_attempt` FIXES AT THE START. It is
        # the admitted task and specification digest the request carries and
        # the answer is bound to, so an attempt without one is not a Job this
        # path can continue -- which is why it is a row here rather than a
        # value the host composes.
        self.control._connection.execute(
            "UPDATE attempts SET input_digest = ?, policy_digest = ? "
            "WHERE runtime_attempt_id = ?",
            (TASK_DIGEST, POLICY_DIGEST, attempt))
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"], attempt_id=attempt,
            generation=number, worker_id=f"impl-worker-{number}",
            profile=self.profile, based_checkpoint_id=based)
        self.completed(attempt)
        if frozen:
            self.frozen_output(attempt)
        return {"attempt_id": attempt, "writer": writer,
                "generation": number}

    def frozen_output(self, attempt):
        """The frozen summary and artifact rows a real freeze would have left.

        `DriverCase.completed` writes the review role's pair; this writes the
        handoff-capable implementation role's, which is `proposal` and
        `handoff`.
        """
        self.control._connection.execute(
            "UPDATE attempts SET output = 'frozen', verification = 'passed' "
            "WHERE runtime_attempt_id = ?", (attempt,))
        self.control._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES (?, ?, "
            "'completed', ?, ?, ?)",
            (attempt, "result-" + attempt, "sha256:" + "1" * 64,
             "freeze-" + attempt, NOW))
        for name in ("proposal", native_handoffs.HANDOFF_OUTPUT):
            self.control._connection.execute(
                "INSERT INTO output_artifacts (runtime_attempt_id, "
                "output_name, artifact_id, media_type, bytes, content_digest, "
                "locator) VALUES (?, ?, ?, 'text/plain', 1, ?, ?)",
                (attempt, name, f"artifact-{name}-{attempt}",
                 "sha256:" + "6" * 64, f"custody/{attempt}/{name}"))
        return attempt

    # -- the acts under test -------------------------------------------------

    def frozen_checkpoint(self, round_):
        return freeze_checkpoint(
            self.control, writer_id=round_["writer"]["writer_id"],
            generation=round_["generation"], profile=self.profile,
            port=self.port(WRITER))

    def classified(self, round_):
        return native_handoffs.classified_handoff(self.control,
                                                  round_["attempt_id"])

    def port_for(self, participant, job_id="job-a"):
        session = (self.producer if participant == WRITER else self.answerer)
        return native_handoffs.HandoffPort(self.control, session,
                                           job_id=job_id)

    def yielded(self, number=1, *, kind=native_handoff.CLARIFICATION_KIND,
                recipient=REVIEWER, based=None):
        """One implementation round that really yields: classify, freeze the
        checkpoint, commit the message, record the yield."""
        round_ = self.implementation_round(number, based=based)
        checkpoint = self.frozen_checkpoint(round_)
        document = handoff_request(checkpoint["evidence"]["head"], kind=kind,
                                   recipient=recipient)
        self.retained_implementation(round_["attempt_id"],
                                     generation=number, document=document)
        classified = self.classified(round_)
        requested = self.port_for(WRITER).request(
            attempt_id=round_["attempt_id"], handoff=classified)
        native_handoffs.cross_bound(classified, checkpoint)
        live = episodes.live_of(self.jobs, "job-a/implementation")
        record = native_handoffs.record_yield(
            self.jobs, stage_id="job-a/implementation",
            episode=live["episode"], attempt_id=round_["attempt_id"],
            kind=classified["kind"], message_id=requested["message_id"],
            handoff_digest=classified["handoff_digest"],
            checkpoint_id=checkpoint["checkpoint_id"],
            continuation_digest=requested["continuation_digest"],
            task_digest=requested["task_digest"],
            destination=requested["destination"],
            continuation=CONTINUATION_TEXT)
        return {"round": round_, "checkpoint": checkpoint,
                "document": document, "classified": classified,
                "message": requested, "record": record,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "episode": live["episode"]}

    def answered(self, held, *, disposition="answer"):
        """The configured reviewer's own invocation and its committed reply."""
        number = held["round"]["generation"]
        attempt = self.attempt(f"response-attempt-{number}", number, REVIEWER,
                               f"response-principal-{number}")
        attached = review_driver.prepare_review(
            self.control, checkpoint_id=held["checkpoint_id"],
            attempt_id=attempt, generation=number,
            reviewer_worker_id=f"response-worker-{number}",
            profile=self.profile)
        self.completed(attempt, review=True)
        document = handoff_response(held["message"]["message_id"],
                                    held["classified"]["handoff_digest"],
                                    held["message"]["checkpoint_ref"],
                                    disposition=disposition)
        self.retained_response(attempt, generation=number, document=document)
        self.delivered(attempt)
        response = native_handoffs.classified_response(self.control, attempt)
        reply = self.port_for(REVIEWER).answer(attempt_id=attempt,
                                               response=response)
        recorded = review_cycles.record_response(
            self.control, attachment_id=attached["attachment_id"],
            disposition=document["disposition"],
            response_digest=response["handoff_digest"], profile=self.profile,
            port=self.port(REVIEWER))
        return {"attempt_id": attempt, "attachment": attached,
                "document": document, "response": response, "reply": reply,
                "record": recorded}

    def delivered(self, attempt_id, *, role="review", stage_id="job-a/review",
                  job_id="job-a"):
        """The host's own record of what THIS attempt was delivered beside
        its task: the context the composition composes and journals under
        the attempt at preparation (review 2026-11-20T19-39-15Z R3)."""
        live = episodes.live_of(self.jobs, stage_id)
        document = native_handoffs.delivered_context(
            self.jobs, self.control, self.authority, role=role,
            job_id=job_id, stage_id=stage_id, episode=live["episode"])
        if document is not None:
            native_handoffs.record_delivery(self.control,
                                            attempt_id=attempt_id,
                                            document=document)
        return document

    def retained_response(self, attempt_id, *, generation, document,
                          verdict_claim=None, participant=REVIEWER):
        from baton_v12.worker_manager import retain_manifest

        def one(name, metadata):
            entries = [{"path": f"{name}.txt", "bytes": 3,
                        "content_digest": "sha256:" + "6" * 64}]
            content = {"entries": entries, "entry_count": 1, "total_bytes": 3,
                       "tree_digest": digest(entries)}
            return {"name": name, "type": "directory-result",
                    "status": "present", "content_manifest": content,
                    "artifact": {"artifact_id": f"artifact-{name}-{attempt_id}",
                                 "media_type": "text/plain", "bytes": 3,
                                 "content_digest": content["tree_digest"],
                                 "locator":
                                     f"file:///var/lib/baton/{attempt_id}/{name}"},
                    "result_metadata": metadata}

        composed = [
            one("findings", {} if verdict_claim is None else
                {review_driver.REVIEW_CLAIM_NAMESPACE: verdict_claim}),
            one("logs", {}),
            one(native_handoffs.RESPONSE_OUTPUT,
                {} if document is None
                else {native_handoff.HANDOFF_SCHEMA: document})]
        held = dict(
            driver._result_vector(), result_id="result-" + attempt_id,
            assignment_ref={"work_ref": {"authority_uuid": self.AUTHORITY,
                                         "work_id": WORK_A},
                            "participant": participant,
                            "generation": generation},
            outputs=composed)
        held.pop("manifest_digest")
        held["manifest_digest"] = digest(held)
        kept = retain_manifest(self.control, held, "resultManifest")["digest"]
        self.control._connection.execute(
            "UPDATE outputs SET manifest_digest = ?, result_id = ? "
            "WHERE runtime_attempt_id = ?",
            (kept, held["result_id"], attempt_id))
        return kept, held

    # -- views ---------------------------------------------------------------

    def acting(self, *, frozen=None):
        """The canonical-operations stand-in the projection reads through.

        `FakeOperations` is this package's own strict stand-in -- exactly the
        members `delegation.OPERATIONS` names -- and `frozen` is how a case
        says "the manager's own answer for this stage is a COMPLETED frozen
        result". That is the observation the ordinary projection reads as a
        completed stage, which is precisely what the yield has to override.
        """
        from tests.job_manager.fixtures import FakeOperations

        acts = FakeOperations(authority_uuid=self.AUTHORITY)
        if frozen is not None:
            acts.frozen(frozen, "completed")
        return acts

    def states(self, *, frozen=None):
        return {stage_id.split("/")[-1]: entry["state"] for stage_id, entry
                in stage_states(self.jobs, self.acting(frozen=frozen)).items()}

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception


class TheClassificationHappensBeforePublication(HandoffCase):
    """Classify typed terminal evidence and enforce success-versus-yield
    BEFORE proposal publication, review-for-acceptance attachment, completed
    projection or satisfied stage dependency."""

    def ending(self, document, *, publication=None, capable=True,
               handoff=..., outputs=None):
        """One real implementation ending over a REAL retained handoff.

        The result manifest is retained BEFORE the ending runs, because the
        freeze answers the attempt's own frozen result -- so the classification
        reads the document this case actually sealed.
        """
        round_ = self.implementation_round(1, frozen=False)
        checkpoint_head = self.profile.held.get(1)
        self.frozen_output(round_["attempt_id"])
        self.retained_implementation(round_["attempt_id"], generation=1,
                                     document=document, outputs=outputs)
        seam = publication if publication is not None else _Publication()
        port = (self.port_for(WRITER) if handoff is ... else handoff)
        with _implementation_endings() as recorded:
            answered = review_driver.end_implementation(
                self.control, self.port(WRITER),
                driver._Adapter("runtime-" + round_["attempt_id"]),
                seam, attempt_id=round_["attempt_id"],
                disposition="completed", terminal=None,
                writer_id=round_["writer"]["writer_id"], generation=1,
                profile=self.profile,
                retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64, proposal=None,
                handoff=port, handoff_capable=capable)
        del checkpoint_head
        return round_, seam, answered, recorded

    def yielding_ending(self, *, kind=native_handoff.CLARIFICATION_KIND,
                        publication=None):
        """The same ending, over a request whose claimed head is the one the
        freeze will actually produce.

        THE HEAD IS THE PROFILE'S OWN, because the cross-binding is real: the
        host compares the worker's claimed head against the checkpoint it
        freezes, so a fixture that made one up would be proving that refusal
        instead of this path.
        """
        return self.ending(handoff_request(self.next_head(), kind=kind),
                           publication=publication)

    def next_head(self):
        """The head the fake profile WILL mint for the line's next freeze.

        Derived from the profile's own rule (`Profile.freeze` names the head
        after the revision) and the line's own current revision, so this case
        predicts the cross-binding rather than patching the profile to agree.
        """
        line = review_cycles.line_of(self.control, self.line["line_id"])
        return f"{line['revision'] + 1:040x}"

    def test_a_final_submission_publishes_exactly_as_it_always_did(self):
        _round, seam, answered, recorded = self.ending(handoff_final())
        self.assertEqual(len(seam.calls), 1)
        self.assertEqual(answered["handoff"]["kind"],
                         native_handoff.FINAL_KIND)
        self.assertIsNone(answered["requested"])
        self.assertNotIn("outcome", answered)
        self.assertIsNotNone(answered["checkpoint_id"])
        # AND THE CLASSIFICATION RAN BEFORE THE PUBLICATION, in the order the
        # mandated host handling requires.
        self.assertLess(recorded.index("classify"), len(recorded))

    def test_a_clarification_request_publishes_NOTHING(self):
        """THE WHOLE RULE IN ONE ASSERTION: a completed worker invocation
        carrying a validated handoff never enters the legacy completed-stage
        publication path."""
        _round, seam, answered, _recorded = self.yielding_ending()
        self.assertEqual(seam.calls, [])
        self.assertIsNone(answered["published"])
        self.assertEqual(answered["outcome"],
                         native_handoffs.YIELD_OUTCOME)
        self.assertEqual(answered["handoff"]["kind"],
                         native_handoff.CLARIFICATION_KIND)
        self.assertIsNotNone(answered["requested"]["message_id"])

    def test_an_in_scope_FINDING_request_takes_the_same_branch(self):
        _round, seam, answered, _recorded = self.yielding_ending(
            kind=native_handoff.FINDING_KIND)
        self.assertEqual(seam.calls, [])
        self.assertEqual(answered["outcome"],
                         native_handoffs.YIELD_OUTCOME)
        self.assertEqual(answered["handoff"]["kind"],
                         native_handoff.FINDING_KIND)

    def test_a_yield_still_freezes_the_exact_retained_checkpoint(self):
        """A yielded checkpoint ... is retained evidence, not an acceptance
        proposal, and does not have to pass final verification to ask a
        question."""
        _round, _seam, answered, _recorded = self.yielding_ending()
        checkpoint = review_cycles.checkpoint_of(self.control,
                                                 answered["checkpoint_id"])
        self.assertEqual(checkpoint["state"], "frozen")
        self.assertEqual(answered["requested"]["checkpoint_ref"],
                         checkpoint["evidence"]["head"])

    def test_an_undeclared_handoff_HOLDS_rather_than_publishing(self):
        """Undeclared, mixed, missing or foreign output holds." The refusal
        stops the ending BEFORE the publication seam is reached."""
        seam = _Publication()
        caught = self.refusal(self.ending, None, publication=seam)
        self.assertIn("carries no", str(caught))
        self.assertEqual(seam.calls, [])

    def test_a_MISSING_handoff_output_HOLDS(self):
        """The declared output answered `missing-optional` is an invocation
        that declared nothing about what it was."""
        seam = _Publication()
        caught = self.refusal(
            self.ending, handoff_final(), publication=seam,
            outputs=[{"name": native_handoffs.HANDOFF_OUTPUT,
                      "type": "directory-result", "status": "missing-optional",
                      "content_manifest": None, "artifact": None,
                      "result_metadata": {}}])
        self.assertIn("not present", str(caught))
        self.assertEqual(seam.calls, [])

    def test_a_foreign_handoff_revision_HOLDS(self):
        seam = _Publication()
        caught = self.refusal(self.ending,
                              dict(handoff_final(),
                                   schema="baton.native-handoff/2"),
                              publication=seam)
        self.assertIn("another revision", str(caught))
        self.assertEqual(seam.calls, [])

    def test_a_RESPONSE_on_the_handoff_output_is_the_wrong_declaration(self):
        seam = _Publication()
        caught = self.refusal(
            self.ending,
            handoff_response("msg-1", "sha256:" + "1" * 64, "checkpoint-1"),
            publication=seam)
        self.assertIn("wrong output", str(caught))
        self.assertEqual(seam.calls, [])

    def test_a_LEGACY_TEMPLATE_reaches_no_branch_at_all(self):
        """A Job resolved against `/1` or `/2` has no handoff branch, so an
        extra output it somehow produced changes nothing about its ending --
        which is what preserves every already admitted version."""
        _round, seam, answered, recorded = self.ending(
            handoff_request("whatever"), capable=False)
        self.assertEqual(len(seam.calls), 1)
        self.assertIsNone(answered["handoff"])
        self.assertIsNone(answered["requested"])
        self.assertNotIn("outcome", answered)

    def test_a_capable_job_with_no_seam_refuses_before_the_stop(self):
        caught = self.refusal(self.ending, handoff_final(),
                              handoff=object())
        self.assertIn("native handoff request seam", str(caught))


class AYieldIsNeverTaskSuccess(HandoffCase):

    def test_the_invocation_completed_and_the_STAGE_did_not(self):
        """THE TWO FACTS, SIDE BY SIDE. The worker's disposition IS
        `completed` -- the invocation finished -- and the stage is not."""
        held = self.yielded()
        self.assertEqual(
            self.control._connection.execute(
                "SELECT worker_disposition FROM attempts WHERE "
                "runtime_attempt_id = ?",
                (held["round"]["attempt_id"],)).fetchone()[0], "completed")
        self.assertEqual(self.states()["implementation"],
                         native_handoffs.AWAITING_STATE)

    def test_the_yield_is_read_BEFORE_the_completed_frozen_disposition(self):
        """THE BRANCH ORDER, PROVED FROM BOTH SIDES. With the manager's own
        answer set to a completed frozen result and NO yield record, the stage
        projects `completed`; with the yield committed, the same observation
        projects `awaiting-answer`. The order of the two branches is the whole
        difference, and a projection that read the disposition first would
        satisfy the dependent's gate on a question.
        """
        stage_id = "job-a/implementation"
        round_ = self.implementation_round(1)
        self.frozen_checkpoint(round_)
        self.assertEqual(self.states(frozen=stage_id)["implementation"],
                         "completed")
        del round_
        self.setUp()
        self.yielded()
        self.assertEqual(self.states(frozen=stage_id)["implementation"],
                         native_handoffs.AWAITING_STATE)

    def test_the_awaiting_state_is_not_completed_exceptional_or_a_verdict(self):
        held = self.yielded()
        state = self.states()["implementation"]
        for forbidden in ("completed", "exceptional", "changes-requested",
                          "accepted"):
            self.assertNotEqual(state, forbidden)
        self.assertEqual(state, "awaiting-answer")
        del held

    def test_NO_VERDICT_AND_NO_RECEIPT_EXISTS_ANYWHERE(self):
        held = self.yielded()
        self.assertEqual(
            self.control._connection.execute(
                "SELECT count(*) FROM checkpoint_verdicts").fetchone()[0], 0)
        self.assertEqual(
            self.authority_rows("SELECT count(*) FROM receipt"), 0)
        self.assertEqual(
            self.authority_rows("SELECT count(*) FROM proposal"), 0)
        del held

    def authority_rows(self, statement):
        import sqlite3

        connection = sqlite3.connect(
            os.path.join(self.root, "authority.sqlite3"))
        try:
            return connection.execute(statement).fetchone()[0]
        finally:
            connection.close()

    def test_the_exact_retained_checkpoint_is_frozen_and_named(self):
        """A yielded checkpoint is RETAINED EVIDENCE: it is frozen exactly like
        a submitted one, and the message names it."""
        held = self.yielded()
        checkpoint = review_cycles.checkpoint_of(self.control,
                                                 held["checkpoint_id"])
        self.assertEqual(checkpoint["state"], "frozen")
        self.assertEqual(held["record"]["checkpoint_id"],
                         held["checkpoint_id"])
        self.assertEqual(held["message"]["checkpoint_ref"],
                         checkpoint["evidence"]["head"])

    def test_the_worker_claimed_head_is_cross_bound_to_what_was_frozen(self):
        round_ = self.implementation_round(1)
        checkpoint = self.frozen_checkpoint(round_)
        self.retained_implementation(
            round_["attempt_id"], generation=1,
            document=handoff_request("not-the-frozen-head"))
        classified = self.classified(round_)
        caught = self.refusal(native_handoffs.cross_bound, classified,
                              checkpoint)
        self.assertIn("actually retained", str(caught))

    def test_the_yield_record_names_the_admitted_template_version(self):
        held = self.yielded()
        self.assertEqual(held["record"]["template_version"], TEMPLATE)
        self.assertTrue(native_handoffs.handoff_capable(self.jobs, "job-a"))

    def test_a_yield_is_refused_for_a_job_whose_template_is_legacy(self):
        self.template_job(version="baton.v12.job-template.implementation-"
                                  "review/1")
        self.assertFalse(native_handoffs.handoff_capable(self.jobs, "job-a"))
        round_ = self.implementation_round(1)
        caught = self.refusal(
            native_handoffs.record_yield, self.jobs,
            stage_id="job-a/implementation", episode=1,
            attempt_id=round_["attempt_id"],
            kind=native_handoff.CLARIFICATION_KIND, message_id="msg-1",
            handoff_digest="sha256:" + "1" * 64,
            checkpoint_id="checkpoint-1",
            continuation_digest=CONTINUATION_DIGEST,
            task_digest="sha256:" + "3" * 64, destination=REVIEWER,
            continuation=CONTINUATION_TEXT)
        self.assertIn("not handoff-capable", str(caught))

    def test_a_FINAL_SUBMISSION_is_never_recorded_as_a_yield(self):
        round_ = self.implementation_round(1)
        caught = self.refusal(
            native_handoffs.record_yield, self.jobs,
            stage_id="job-a/implementation", episode=1,
            attempt_id=round_["attempt_id"],
            kind=native_handoff.FINAL_KIND, message_id="msg-1",
            handoff_digest="sha256:" + "1" * 64,
            checkpoint_id="checkpoint-1",
            continuation_digest=CONTINUATION_DIGEST,
            task_digest="sha256:" + "3" * 64, destination=REVIEWER,
            continuation=CONTINUATION_TEXT)
        self.assertIn("A final submission is not a yield", str(caught))

    def test_an_exact_retry_replays_the_yield_and_the_message(self):
        held = self.yielded()
        again = native_handoffs.record_yield(
            self.jobs, stage_id="job-a/implementation",
            episode=held["episode"],
            attempt_id=held["round"]["attempt_id"],
            kind=held["classified"]["kind"],
            message_id=held["message"]["message_id"],
            handoff_digest=held["classified"]["handoff_digest"],
            checkpoint_id=held["checkpoint_id"],
            continuation_digest=held["message"]["continuation_digest"],
            task_digest=held["message"]["task_digest"],
            destination=held["message"]["destination"],
            continuation=CONTINUATION_TEXT)
        self.assertEqual(again, held["record"])
        self.assertEqual(len(self.authority.work_messages(WORK_A)), 1)

    def test_a_record_belonging_to_another_stage_is_refused_not_adopted(self):
        """A SIGNATURE IS NOT OWNERSHIP: a well-made record copied to this
        identity is proved to be this stage's rather than merely well made."""
        held = self.yielded()
        self.jobs._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(dict(held["record"], stage_id="job-a/review")),
             native_handoffs.yield_operation_id("job-a/implementation",
                                                held["episode"])))
        caught = self.refusal(native_handoffs.yield_of, self.jobs,
                              "job-a/implementation", held["episode"])
        self.assertIn("proved to be this stage's", str(caught))


class TheDependencyWindowOpensOnlyForAResponse(HandoffCase):

    def gates(self, *, frozen=None):
        held = stage_states(self.jobs, self.acting(frozen=frozen))
        from baton_v12.job_manager.projection import gates_of

        return {stage_id.split("/")[-1]:
                gates_of(entry["stage"], held)
                for stage_id, entry in held.items()}

    def test_before_the_yield_commits_the_review_gate_is_SHUT(self):
        round_ = self.implementation_round(1)
        self.frozen_checkpoint(round_)
        self.assertFalse(all(one["open"] for one in self.gates()["review"]))
        self.assertEqual(self.states()["review"], "blocked")

    def test_the_committed_yield_opens_the_review_stage_for_a_response(self):
        self.yielded()
        self.assertTrue(all(one["open"] for one in self.gates()["review"]))
        self.assertEqual(self.states()["review"], "queued")
        # AND THE PREDECESSOR IS STILL NOT COMPLETED, which is the half that
        # makes this not dependency success.
        self.assertEqual(self.gates()["review"][0]["state"],
                         native_handoffs.AWAITING_STATE)

    def test_an_implementation_stage_never_opens_for_a_response(self):
        self.yielded()
        self.assertEqual(self.gates()["implementation"], [])

    def test_the_yielded_stage_owes_no_admission_and_no_claim(self):
        self.yielded()
        owed = {one["stage_id"]: one["act"]
                for one in owed_acts(self.jobs, self.acting())}
        self.assertNotIn("job-a/implementation", owed)
        self.assertEqual(owed.get("job-a/review"), "admit")

    def test_the_window_CLOSES_once_the_continuation_commits(self):
        held = self.yielded()
        self.answered(held)
        native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        self.assertFalse(all(one["open"] for one in self.gates()["review"]))


class AResponseIsNotAVerdict(HandoffCase):

    def test_a_response_records_no_verdict_and_makes_nothing_eligible(self):
        held = self.yielded()
        self.answered(held)
        self.assertEqual(
            self.control._connection.execute(
                "SELECT count(*) FROM checkpoint_verdicts").fetchone()[0], 0)
        self.assertEqual(
            self.control._connection.execute(
                "SELECT count(*) FROM integration_eligibility"
            ).fetchone()[0], 0)

    def test_the_line_is_held_for_a_continuation_and_not_by_a_verdict(self):
        held = self.yielded()
        self.answered(held)
        line = review_cycles.line_of(self.control, self.line["line_id"])
        self.assertEqual(line["state"], review_cycles.CONTINUATION_READY)
        self.assertEqual(line["current_checkpoint_id"],
                         held["checkpoint_id"])
        self.assertIsNotNone(review_cycles.continuation_hold_of(
            self.control, held["checkpoint_id"]))

    def test_an_escalation_admits_no_writer_at_all(self):
        held = self.yielded()
        self.answered(held, disposition="escalate")
        line = review_cycles.line_of(self.control, self.line["line_id"])
        self.assertEqual(line["state"], "review-ready")
        self.assertIsNone(review_cycles.continuation_hold_of(
            self.control, held["checkpoint_id"]))

    def test_a_result_that_both_answers_and_judges_is_AMBIGUOUS(self):
        """One invocation answers once." A reviewer cannot answer a question
        and give an accepted technical review in one turn."""
        held = self.yielded()
        attempt = self.attempt("response-attempt-1", 1, REVIEWER,
                               "response-principal-1")
        review_driver.prepare_review(
            self.control, checkpoint_id=held["checkpoint_id"],
            attempt_id=attempt, generation=1,
            reviewer_worker_id="response-worker-1", profile=self.profile)
        self.completed(attempt, review=True)
        evidence = held["checkpoint"]["evidence"]
        self.retained_response(
            attempt, generation=1,
            document=handoff_response(held["message"]["message_id"],
                                      held["classified"]["handoff_digest"],
                                      held["message"]["checkpoint_ref"]),
            verdict_claim={"verdict": "accepted", "base": evidence["base"],
                           "head": evidence["head"], "tree": evidence["tree"]})
        caught = self.refusal(native_handoffs.classified_response,
                              self.control, attempt)
        self.assertIn("one invocation answers once", str(caught))

    def test_a_review_that_declares_no_response_is_an_ordinary_review(self):
        held = self.yielded()
        attempt = self.attempt("response-attempt-1", 1, REVIEWER,
                               "response-principal-1")
        review_driver.prepare_review(
            self.control, checkpoint_id=held["checkpoint_id"],
            attempt_id=attempt, generation=1,
            reviewer_worker_id="response-worker-1", profile=self.profile)
        self.completed(attempt, review=True)
        self.retained_response(attempt, generation=1, document=None)
        self.assertFalse(
            native_handoffs.declares_response(self.control, attempt))

    def test_a_declared_response_selects_the_response_branch(self):
        held = self.yielded()
        answered = self.answered(held)
        self.assertTrue(native_handoffs.declares_response(
            self.control, answered["attempt_id"]))


class TheContinuationIsTheSameAdmittedTask(HandoffCase):

    def resumed(self):
        held = self.yielded()
        answered = self.answered(held)
        opened = native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        return held, answered, opened

    def test_the_task_digest_is_unchanged_across_the_whole_path(self):
        held, answered, opened = self.resumed()
        self.assertEqual(opened["task_digest"],
                         held["message"]["task_digest"])
        self.assertEqual(
            self.authority.work_message(
                answered["reply"]["message"]["message_id"])["task_digest"],
            held["message"]["task_digest"])

    def test_both_stages_get_FRESH_episodes_that_carry_nothing_over(self):
        held, _answered, _opened = self.resumed()
        live = episodes.live_of(self.jobs, "job-a/implementation")
        self.assertEqual(live["episode"], held["episode"] + 1)
        self.assertIsNone(native_handoffs.yield_of(
            self.jobs, "job-a/implementation", live["episode"]))
        self.assertEqual(self.states()["implementation"], "queued")

    def test_the_continuation_names_the_reply_and_the_request(self):
        _held, answered, opened = self.resumed()
        self.assertEqual(opened["message_id"],
                         answered["reply"]["message"]["message_id"])
        self.assertEqual(opened["request_id"],
                         answered["reply"]["request"]["message_id"])

    def test_the_resumed_writer_is_based_on_the_exact_retained_checkpoint(self):
        held, _answered, _opened = self.resumed()
        line = review_cycles.line_of(self.control, self.line["line_id"])
        self.assertEqual(line["current_checkpoint_id"],
                         held["checkpoint_id"])
        resumed = self.implementation_round(2, based=held["checkpoint_id"])
        self.assertEqual(
            review_cycles.writer_of(
                self.control,
                resumed["writer"]["writer_id"])["based_checkpoint_id"],
            held["checkpoint_id"])

    def test_ONE_continuation_and_the_second_is_refused(self):
        """The allowance is ONE resolved continuation per Job. An exact retry
        of the committed one is not a second (R2, below); a second YIELD on
        the resumed episode asking for another is, and it is refused by the
        allowance and holds."""
        held, _answered, _opened = self.resumed()
        live = episodes.live_of(self.jobs, "job-a/implementation")
        native_handoffs.record_yield(
            self.jobs, stage_id="job-a/implementation",
            episode=live["episode"], attempt_id="writer-attempt-2",
            kind=held["classified"]["kind"],
            message_id=held["message"]["message_id"],
            handoff_digest=held["classified"]["handoff_digest"],
            checkpoint_id=held["checkpoint_id"],
            continuation_digest=held["message"]["continuation_digest"],
            task_digest=held["message"]["task_digest"],
            destination=held["message"]["destination"],
            continuation=CONTINUATION_TEXT)
        caught = self.refusal(native_handoffs.advance_continuation,
                              self.jobs, self.control, self.authority,
                              job_id="job-a")
        self.assertIn("permits 1 resolved continuation", str(caught))
        self.assertEqual(
            job_control.continuations_used_in(self.jobs._connection,
                                              "job-a"), 1)
        self.assertEqual(episodes.live_of(
            self.jobs, "job-a/implementation")["episode"], live["episode"])

    def test_an_exhausted_allowance_HOLDS_and_reports_honestly(self):
        held = self.yielded()
        self.answered(held)
        with mock.patch.dict(job_control.CONTINUATIONS,
                             {HANDOFF_PROFILE: 0}):
            caught = self.refusal(native_handoffs.advance_continuation,
                                  self.jobs, self.control, self.authority,
                                  job_id="job-a")
        self.assertIn("permits 0 resolved continuation", str(caught))
        self.assertEqual(self.states()["implementation"],
                         native_handoffs.AWAITING_STATE)

    def test_a_continuation_spends_NO_CORRECTION_ROUND(self):
        """The two allowances are two counts: a continuation is invisible to
        the correction account and a correction is invisible to this one."""
        _held, _answered, _opened = self.resumed()
        self.assertEqual(
            job_control.rounds_used_in(self.jobs._connection, "job-a"), 0)
        self.assertEqual(
            job_control.continuations_used_in(self.jobs._connection,
                                              "job-a"), 1)
        # AND A ZERO-CORRECTION PROFILE IS STILL ZERO-CORRECTION.
        caught = self.refusal(job_control.refuse_round,
                              self.jobs._connection, "job-a")
        self.assertIn("permits 0 correction round", str(caught))

    def test_an_actual_second_invocation_returns_the_committed_receipt(self):
        """Review 2026-11-20T19-39-15Z R2. The exact second call of the public
        act -- what a crashed ending's re-entry makes after the continuation
        committed -- is answered by the journal: the same receipt, nothing
        spent twice, nothing opened twice. The previous version of this case
        never made the second call."""
        held = self.yielded()
        self.answered(held)
        first = native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        again = native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        self.assertEqual(again, first)
        self.assertEqual(again["episode"], held["episode"])
        self.assertEqual(again["continued_at"], first["continued_at"])
        self.assertEqual(
            job_control.continuations_used_in(self.jobs._connection,
                                              "job-a"), 1)
        self.assertEqual(self.jobs._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = ?",
            (native_handoffs.CONTINUE_KIND,)).fetchone()[0], 1)
        for stage_id in ("job-a/implementation", "job-a/review"):
            self.assertEqual(episodes.live_of(self.jobs, stage_id)["episode"],
                             held["episode"] + 1)

    def test_an_ESCALATION_resumes_nothing(self):
        held = self.yielded()
        self.answered(held, disposition="escalate")
        caught = self.refusal(native_handoffs.advance_continuation,
                              self.jobs, self.control, self.authority,
                              job_id="job-a")
        self.assertIn("escalation leaves the execution held", str(caught))
        self.assertEqual(self.states()["implementation"],
                         native_handoffs.AWAITING_STATE)

    def test_an_UNANSWERED_request_resumes_nothing(self):
        self.yielded()
        caught = self.refusal(native_handoffs.advance_continuation,
                              self.jobs, self.control, self.authority,
                              job_id="job-a")
        self.assertIn("has no reply", str(caught))

    def test_a_cancelled_job_resumes_nothing(self):
        held = self.yielded()
        self.answered(held)
        self.cancel()
        caught = self.refusal(native_handoffs.advance_continuation,
                              self.jobs, self.control, self.authority,
                              job_id="job-a")
        self.assertIn("cancel", str(caught).lower())
        self.assertEqual(
            job_control.continuations_used_in(self.jobs._connection,
                                              "job-a"), 0)

    def test_a_job_past_its_deadline_resumes_nothing(self):
        held = self.yielded()
        self.answered(held)
        later = self.after(job_control.PROFILES[HANDOFF_PROFILE]
                           ["job_seconds"] + 60)
        caught = self.refusal(native_handoffs.advance_continuation,
                              self.jobs, self.control, self.authority,
                              job_id="job-a", now=later)
        self.assertIn("deadline", str(caught))

    def test_the_original_deadlines_are_PRESERVED_by_a_continuation(self):
        """It resets no stage or Job clock." The deadline a continuation
        resumes under is the one the Job was admitted with."""
        before = job_control.evaluate(self.jobs._connection, "job-a", NOW)
        _held, _answered, _opened = self.resumed()
        after = job_control.evaluate(self.jobs._connection, "job-a", NOW)
        self.assertEqual(after["job"]["origin"], before["job"]["origin"])
        self.assertEqual(after["job"]["deadline_at"],
                         before["job"]["deadline_at"])
        self.assertEqual(after["profile"], HANDOFF_PROFILE)
        self.assertEqual(after["continuations"],
                         {"allowance": 1, "used": 1})

    def cancel(self):
        """One operator cancellation, through the accepted owner."""
        return cancellation.request(
            self.jobs, job_id="job-a", reason="the operator stops this Job")

    def after(self, seconds):
        from datetime import datetime, timedelta, timezone

        origin = datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc)
        moment = origin + timedelta(seconds=seconds)
        return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
                + f"{moment.microsecond // 1000:03d}Z")

    def test_a_reply_naming_another_task_digest_resumes_nothing(self):
        held = self.yielded()
        answered = self.answered(held)
        reply = answered["reply"]["message"]["message_id"]
        import sqlite3

        self.authority.dispose()
        connection = sqlite3.connect(
            os.path.join(self.root, "authority.sqlite3"))
        connection.execute(
            "UPDATE work_message SET task_digest = ? WHERE message_id = ?",
            ("sha256:" + "e" * 64, reply))
        connection.commit()
        connection.close()
        self.authority = Authority.open(
            os.path.join(self.root, "authority.sqlite3"),
            expected_authority_uuid=self.AUTHORITY, clock=self.clock)
        caught = self.refusal(native_handoffs.advance_continuation,
                              self.jobs, self.control, self.authority,
                              job_id="job-a")
        self.assertIn("same admitted task", str(caught))


class TheReviewStageAnsweredIsNotACompletedReview(HandoffCase):
    """W385331: the review-side record, and what it keeps from happening.

    A reviewer's response invocation is `completed` and the review STAGE is
    not a completed review: a projection that read the frozen disposition
    would open the next stage's gate on a question nobody answered with a
    verdict.
    """

    def recorded(self, held, answered):
        live = episodes.live_of(self.jobs, "job-a/review")
        return native_handoffs.record_answer(
            self.jobs, stage_id="job-a/review", episode=live["episode"],
            attempt_id=answered["attempt_id"],
            message_id=answered["reply"]["message"]["message_id"],
            request_id=held["message"]["message_id"],
            disposition=answered["document"]["disposition"],
            checkpoint_id=held["checkpoint_id"])

    def test_an_escalated_review_projects_answered_and_owes_nothing(self):
        held = self.yielded()
        answered = self.answered(held, disposition="escalate")
        record = self.recorded(held, answered)
        self.assertEqual(record["disposition"],
                         native_handoff.ESCALATE_DISPOSITION)
        states = self.states(frozen="job-a/review")
        self.assertEqual(states["review"], native_handoffs.ANSWERED_STATE)
        self.assertNotEqual(states["review"], "completed")
        owed = {one["stage_id"] for one in owed_acts(self.jobs, self.acting())}
        self.assertNotIn("job-a/review", owed)
        self.assertEqual(native_handoffs.answer_of(
            self.jobs, "job-a/review", 1), record)

    def test_the_record_is_the_review_stages_own_and_replays(self):
        held = self.yielded()
        answered = self.answered(held)
        first = self.recorded(held, answered)
        again = self.recorded(held, answered)
        self.assertEqual(first, again)
        caught = self.refusal(
            native_handoffs.record_answer, self.jobs,
            stage_id="job-a/implementation", episode=1,
            attempt_id=answered["attempt_id"],
            message_id=answered["reply"]["message"]["message_id"],
            request_id=held["message"]["message_id"],
            disposition="answer", checkpoint_id=held["checkpoint_id"])
        self.assertIn("recorded against the review stage", str(caught))

    def test_the_continuation_leaves_the_answer_on_the_episode_it_ended(self):
        held = self.yielded()
        answered = self.answered(held)
        self.recorded(held, answered)
        native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        self.assertIsNotNone(native_handoffs.answer_of(
            self.jobs, "job-a/review", 1))
        self.assertIsNone(native_handoffs.answer_of(
            self.jobs, "job-a/review", 2))
        self.assertEqual(self.states()["review"], "blocked")
        self.assertEqual(self.states()["implementation"], "queued")


class AResponseReEntersBehindADestroyedRuntime(HandoffCase):
    """W385331: the historical re-entry of the response record.

    The composed ending answers once; a later step of the same conclude can
    defer, and the next tick re-enters behind a runtime that is already gone.
    What answers it is the response this store committed, proved against the
    operands it is asked with again.
    """

    def test_the_committed_response_answers_the_re_entry(self):
        held = self.yielded()
        answered = self.answered(held)
        self.control._connection.execute(
            "UPDATE attempts SET execution_runtime = 'destroyed' WHERE "
            "runtime_attempt_id = ?", (answered["attempt_id"],))
        again = review_cycles.record_response(
            self.control, attachment_id=answered["attachment"]["attachment_id"],
            disposition=answered["document"]["disposition"],
            response_digest=answered["response"]["handoff_digest"],
            profile=self.profile, port=self.port(REVIEWER))
        self.assertEqual(again, answered["record"])

    def test_a_different_answer_behind_the_same_identity_is_refused(self):
        held = self.yielded()
        answered = self.answered(held)
        self.control._connection.execute(
            "UPDATE attempts SET execution_runtime = 'destroyed' WHERE "
            "runtime_attempt_id = ?", (answered["attempt_id"],))
        caught = self.refusal(
            review_cycles.record_response, self.control,
            attachment_id=answered["attachment"]["attachment_id"],
            disposition="escalate",
            response_digest=answered["response"]["handoff_digest"],
            profile=self.profile, port=self.port(REVIEWER))
        self.assertIn("differs from the one this re-entry", str(caught))

    def test_a_destroyed_runtime_with_no_committed_response_is_refused(self):
        held = self.yielded()
        number = held["round"]["generation"]
        attempt = self.attempt(f"response-attempt-{number}", number, REVIEWER,
                               f"response-principal-{number}")
        attached = review_driver.prepare_review(
            self.control, checkpoint_id=held["checkpoint_id"],
            attempt_id=attempt, generation=number,
            reviewer_worker_id=f"response-worker-{number}",
            profile=self.profile)
        self.completed(attempt, review=True)
        self.control._connection.execute(
            "UPDATE attempts SET execution_runtime = 'destroyed' WHERE "
            "runtime_attempt_id = ?", (attempt,))
        caught = self.refusal(
            review_cycles.record_response, self.control,
            attachment_id=attached["attachment_id"], disposition="answer",
            response_digest="sha256:" + "4" * 64, profile=self.profile,
            port=self.port(REVIEWER))
        self.assertIn("committed response", str(caught))


class TheDeliveredContextIsReadFromOwners(HandoffCase):
    """W385331: what an attempt is told, composed from committed records."""

    def test_a_fresh_implementation_is_told_only_its_recipient(self):
        document = native_handoffs.delivered_context(
            self.jobs, self.control, self.authority, role="implementation",
            job_id="job-a", stage_id="job-a/implementation", episode=1)
        self.assertEqual(document["schema"], native_handoffs.CONTEXT_SCHEMA)
        self.assertEqual(document["recipient"], REVIEWER)
        self.assertIsNone(document["continuation"])

    def test_a_review_over_a_yield_is_told_the_pending_request(self):
        held = self.yielded()
        document = native_handoffs.delivered_context(
            self.jobs, self.control, self.authority, role="review",
            job_id="job-a", stage_id="job-a/review", episode=1)
        self.assertEqual(document["request"]["message_id"],
                         held["message"]["message_id"])
        self.assertEqual(document["checkpoint"]["reference"],
                         held["message"]["checkpoint_ref"])
        self.assertEqual(document["checkpoint"]["digest"],
                         digest(held["checkpoint"]["evidence"]))

    def test_an_ordinary_review_is_told_nothing(self):
        round_ = self.implementation_round(1)
        self.frozen_checkpoint(round_)
        self.assertIsNone(native_handoffs.delivered_context(
            self.jobs, self.control, self.authority, role="review",
            job_id="job-a", stage_id="job-a/review", episode=1))

    def test_a_continuation_is_told_the_exact_correspondence(self):
        held = self.yielded()
        answered = self.answered(held)
        native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        document = native_handoffs.delivered_context(
            self.jobs, self.control, self.authority, role="implementation",
            job_id="job-a", stage_id="job-a/implementation", episode=2)
        continuation = document["continuation"]
        self.assertEqual(continuation["request"]["message_id"],
                         held["message"]["message_id"])
        self.assertEqual(continuation["reply"]["message_id"],
                         answered["reply"]["message"]["message_id"])
        self.assertEqual(continuation["checkpoint_id"], held["checkpoint_id"])
        # AND THE RETAINED CONTINUATION ITSELF (R1), re-proved against the
        # digest the committed request names.
        self.assertEqual(continuation["text"], CONTINUATION_TEXT)
        self.assertEqual(digest_of_bytes(continuation["text"].encode("utf-8")),
                         continuation["request"]["continuation_digest"])
        self.assertIsNotNone(native_handoffs.context_bytes(document))

    def test_a_tampered_retained_continuation_is_refused_not_delivered(self):
        held = self.yielded()
        self.answered(held)
        native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a")
        self.jobs._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(dict(held["record"],
                             continuation="do something else entirely\n")),
             native_handoffs.yield_operation_id("job-a/implementation",
                                                held["episode"])))
        caught = self.refusal(
            native_handoffs.delivered_context, self.jobs, self.control,
            self.authority, role="implementation", job_id="job-a",
            stage_id="job-a/implementation", episode=2)
        self.assertIn("does not digest to", str(caught))

    def test_a_legacy_job_is_composed_no_context(self):
        self.template_job(version="baton.v12.job-template.implementation-"
                                  "review/1")
        self.assertIsNone(native_handoffs.delivered_context(
            self.jobs, self.control, self.authority, role="implementation",
            job_id="job-a", stage_id="job-a/implementation", episode=1))

    def test_an_unconfigured_routing_refuses_before_a_turn_is_spent(self):
        self.authority.set_policy(work_messages.ROUTING_POLICY, None)
        caught = self.refusal(
            native_handoffs.delivered_context, self.jobs, self.control,
            self.authority, role="implementation", job_id="job-a",
            stage_id="job-a/implementation", episode=1)
        self.assertIn("no native handoff routing", str(caught))


class TheContinuationRetryIsBoundToItsOriginalYield(HandoffCase):
    """Review 2026-11-20T19-39-15Z R2: the retry, the interior fault, and the
    serving side's own question, each against the ORIGINAL yield."""

    def advance(self, **named):
        return native_handoffs.advance_continuation(
            self.jobs, self.control, self.authority, job_id="job-a", **named)

    def spent(self):
        return job_control.continuations_used_in(self.jobs._connection,
                                                 "job-a")

    def live(self, kind):
        return episodes.live_of(self.jobs, f"job-a/{kind}")["episode"]

    def test_a_retry_after_cancellation_returns_the_committed_receipt(self):
        """What was committed is history: a later cancellation closes the
        Job to NEW continuations and changes nothing about the one that
        already happened, which the retry is still owed."""
        held = self.yielded()
        self.answered(held)
        first = self.advance()
        cancellation.request(self.jobs, job_id="job-a",
                             reason="the operator stops this Job")
        self.assertEqual(self.advance(), first)
        self.assertEqual(self.spent(), 1)
        self.assertEqual(self.live("implementation"), held["episode"] + 1)

    def test_a_retry_past_the_deadline_returns_the_committed_receipt(self):
        held = self.yielded()
        self.answered(held)
        first = self.advance()
        later = TheContinuationIsTheSameAdmittedTask.after(
            self, job_control.PROFILES[HANDOFF_PROFILE]["job_seconds"] + 60)
        again = self.advance(now=later)
        self.assertEqual(again, first)
        # AND THE ORIGINAL INSTANT STANDS: a replay does not re-stamp it.
        self.assertEqual(again["continued_at"], NOW)

    def test_a_fault_inside_the_write_leaves_both_episodes_live_and_the_retry_commits_once(self):
        """The interior cut: a fault after the first row moved and before the
        transaction committed. Nothing is half-written -- both episodes are
        still the live pair, nothing is spent, the line is still held -- and
        the retry commits exactly one continuation on the same yield."""
        held = self.yielded()
        self.answered(held)
        real = native_handoffs.documents.stage_episode
        calls = []

        def faulting(**members):
            calls.append(members["stage_id"])
            if len(calls) == 1:
                raise RuntimeError("the manager died mid-transaction")
            return real(**members)

        with mock.patch.object(native_handoffs.documents, "stage_episode",
                               faulting):
            with self.assertRaises(RuntimeError):
                self.advance()
        self.assertEqual(self.spent(), 0)
        self.assertEqual(self.jobs._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = ?",
            (native_handoffs.CONTINUE_KIND,)).fetchone()[0], 0)
        for kind in ("implementation", "review"):
            self.assertEqual(self.live(kind), held["episode"])
            row = episodes.episode_of(self.jobs, f"job-a/{kind}",
                                      held["episode"])
            self.assertIsNone(row["ended_state"])
        self.assertEqual(self.states()["implementation"],
                         native_handoffs.AWAITING_STATE)
        self.assertEqual(review_cycles.line_of(
            self.control, self.line["line_id"])["state"],
            review_cycles.CONTINUATION_READY)
        opened = self.advance()
        self.assertEqual(opened["episode"], held["episode"])
        self.assertEqual(self.spent(), 1)
        self.assertEqual(self.live("implementation"), held["episode"] + 1)
        self.assertEqual(self.advance(), opened)

    def test_the_serving_side_question_is_answered_by_request_identity(self):
        held = self.yielded()
        self.answered(held)
        request_id = held["message"]["message_id"]
        self.assertIsNone(native_handoffs.continuation_for_request(
            self.jobs, job_id="job-a", request_id=request_id))
        opened = self.advance()
        self.assertEqual(native_handoffs.continuation_for_request(
            self.jobs, job_id="job-a", request_id=request_id), opened)
        self.assertIsNone(native_handoffs.continuation_for_request(
            self.jobs, job_id="job-a", request_id="some-other-request"))

    def test_a_retry_whose_yield_was_rewritten_refuses_rather_than_replays(self):
        """Changed operands under the committed identity collide; a retry is
        the SAME continuation or it is nothing."""
        held = self.yielded()
        self.answered(held)
        first = self.advance()
        self.jobs._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(dict(held["record"], checkpoint_id="checkpoint-x")),
             native_handoffs.yield_operation_id("job-a/implementation",
                                                held["episode"])))
        caught = self.refusal(self.advance)
        self.assertNotIn("recorded no yield", str(caught))
        self.assertEqual(self.spent(), 1)
        self.assertEqual(self.live("implementation"), first["episode"] + 1)


class AReplyIsBoundToTheRequestItWasDelivered(HandoffCase):
    """Review 2026-11-20T19-39-15Z R3: before ANY answer commits, the reply is
    held to the review attempt's fixed assignment and to the exact pending
    request the host delivered that attempt. Every refusal below commits no
    reply and no transition."""

    OTHER_WORK = "0000000a-W2"
    OTHER_PRODUCER = "baton.other-producer"
    STRANGER = "baton.other-reviewer"

    def response_attempt(self, held, *, participant=REVIEWER, deliver=True,
                         document=None, name="response"):
        number = held["round"]["generation"]
        attempt = self.attempt(f"{name}-attempt-{number}", number, participant,
                               f"{name}-principal-{number}")
        review_driver.prepare_review(
            self.control, checkpoint_id=held["checkpoint_id"],
            attempt_id=attempt, generation=number,
            reviewer_worker_id=f"{name}-worker-{number}",
            profile=self.profile)
        self.completed(attempt, review=True)
        if document is None:
            document = handoff_response(held["message"]["message_id"],
                                        held["classified"]["handoff_digest"],
                                        held["message"]["checkpoint_ref"])
        self.retained_response(attempt, generation=number, document=document,
                               participant=participant)
        if deliver:
            self.delivered(attempt)
        return attempt

    def refused_answer(self, held, attempt, *, port=None):
        response = native_handoffs.classified_response(self.control, attempt)
        port = self.port_for(REVIEWER) if port is None else port
        caught = self.refusal(port.answer, attempt_id=attempt,
                              response=response)
        self.nothing_committed(held)
        return str(caught)

    def nothing_committed(self, held):
        self.assertIsNone(self.authority.work_message_reply(
            held["message"]["message_id"]))
        self.assertEqual(len(self.authority.work_messages(WORK_A)), 1)
        self.assertEqual(self.authority.pending_handoff_requests(WORK_A)[0]
                         ["message_id"], held["message"]["message_id"])

    def other_request(self, held):
        """Another Work's request, addressed to the SAME reviewer, who holds
        a grant on both: the reviewer's own probe (foreign-request-3)."""
        self.authority.create_work(self.OTHER_WORK, "impl",
                                   operation_id="op-create-other",
                                   contract="baton.v12.contract/1")
        scope = self.authority.project_work(self.OTHER_WORK)["scope"]
        self.authority.grant_capability(REVIEWER,
                                        work_messages.ANSWER_CAPABILITY,
                                        scope=scope)
        self.authority.add_route_handler("impl", self.OTHER_PRODUCER)
        producer = self.authority.session(self.OTHER_PRODUCER)
        assignment = producer.claim({"work_id": self.OTHER_WORK,
                                     "operation_id": "op-claim-other"})
        original = held["message"]
        return producer.request_handoff({
            "expect": assignment["assignment"],
            "operation_id": "other-request", "message_id": "other-request",
            "job_id": "other-job", "kind": original["kind"],
            "body": original["body"],
            "handoff_digest": original["handoff_digest"],
            "task_digest": original["task_digest"],
            "checkpoint_ref": original["checkpoint_ref"],
            "continuation_digest": original["continuation_digest"],
            "destination": REVIEWER})

    def test_a_response_citing_another_works_request_is_refused_by_the_host(self):
        held = self.yielded()
        other = self.other_request(held)
        attempt = self.response_attempt(
            held, document=handoff_response(other["message_id"],
                                            other["handoff_digest"],
                                            other["checkpoint_ref"]))
        said = self.refused_answer(held, attempt)
        self.assertIn("exact pending request it was asked", said)
        self.assertIsNone(self.authority.work_message_reply(
            other["message_id"]))

    def test_the_authority_refuses_the_same_reply_for_the_wrong_work(self):
        """The second binding, the Authority's own: a reply naming Work A's
        assignment cannot answer Work B's request however the host spelled
        the rest."""
        held = self.yielded()
        other = self.other_request(held)
        document = handoff_response(other["message_id"],
                                    other["handoff_digest"],
                                    other["checkpoint_ref"])
        from baton_v12.authority import Refusal

        with self.assertRaises(Refusal) as caught:
            self.answerer.answer_handoff({
                "operation_id": "respond-by-hand", "message_id": "reply-x",
                "reply_to": other["message_id"], "disposition": "response",
                "body": document,
                "handoff_digest": native_handoff.handoff_digest(document),
                "request_digest": other["handoff_digest"],
                "checkpoint_ref": other["checkpoint_ref"],
                "effect": "continuation", "detail": {},
                "work_id": WORK_A, "job_id": "job-a"})
        self.assertIn("never another Work's", str(caught.exception))
        self.assertIsNone(self.authority.work_message_reply(
            other["message_id"]))
        self.nothing_committed(held)

    def test_an_unsolicited_response_from_an_ordinary_review_is_refused(self):
        held = self.yielded()
        attempt = self.response_attempt(held, deliver=False)
        said = self.refused_answer(held, attempt)
        self.assertIn("unsolicited", said)

    def test_a_stale_request_digest_is_refused(self):
        held = self.yielded()
        attempt = self.response_attempt(
            held, document=handoff_response(held["message"]["message_id"],
                                            "sha256:" + "f" * 64,
                                            held["message"]["checkpoint_ref"]))
        said = self.refused_answer(held, attempt)
        self.assertIn("version of the question", said)

    def test_another_checkpoint_is_refused(self):
        held = self.yielded()
        attempt = self.response_attempt(
            held, document=handoff_response(held["message"]["message_id"],
                                            held["classified"]["handoff_digest"],
                                            "0" * 40))
        said = self.refused_answer(held, attempt)
        self.assertIn("exact retained checkpoint", said)

    def test_a_request_of_another_job_is_refused(self):
        held = self.yielded()
        attempt = self.response_attempt(held)
        said = self.refused_answer(held, attempt,
                                   port=self.port_for(REVIEWER, job_id="job-b"))
        self.assertIn("answers the Job that asked", said)

    def test_another_participants_session_cannot_commit_this_reply(self):
        held = self.yielded()
        attempt = self.response_attempt(held)
        said = self.refused_answer(held, attempt, port=self.port_for(WRITER))
        self.assertIn("answering session acts for", said)

    def test_an_attempt_fixed_to_a_participant_the_question_was_not_addressed_to_is_refused(self):
        held = self.yielded()
        self.authority.add_route_handler("rview", self.STRANGER)
        self.authority.grant_capability(self.STRANGER,
                                        work_messages.ANSWER_CAPABILITY,
                                        scope=self.scope)
        attempt = self.response_attempt(held, participant=self.STRANGER,
                                        name="stranger")
        stranger = native_handoffs.HandoffPort(
            self.control, self.authority.session(self.STRANGER),
            job_id="job-a")
        said = self.refused_answer(held, attempt, port=stranger)
        self.assertIn("addressed to", said)

    def test_the_delivery_record_is_one_per_attempt_and_replays(self):
        held = self.yielded()
        attempt = self.response_attempt(held)
        first = native_handoffs.delivered_of(self.control, attempt)
        self.assertEqual(first["request"]["message_id"],
                         held["message"]["message_id"])
        self.assertEqual(self.delivered(attempt), first)
        caught = self.refusal(
            native_handoffs.record_delivery, self.control,
            attempt_id=attempt, document=dict(first, job_id="job-z"))
        self.assertIn("different", str(caught))
        self.assertIsNone(native_handoffs.delivered_of(self.control,
                                                       "never-prepared"))


class TheRetainedContinuationIsReadOutOfCustody(HandoffCase):
    """Review 2026-11-20T19-39-15Z R1: the exact bytes, out of accepted
    custody, proved against the frozen measurement and the committed digest."""

    def custody(self, text=CONTINUATION_TEXT, *, name="continuation.txt",
                accepted=True, link=False):
        root = tempfile.mkdtemp(dir=self.root)
        raw = text.encode("utf-8")
        place = os.path.join(root, name)
        if link:
            with open(place + ".target", "wb") as writing:
                writing.write(raw)
            os.symlink(place + ".target", place)
        else:
            with open(place, "wb") as writing:
                writing.write(raw)
        entry = {"path": name, "bytes": len(raw),
                 "content_digest": digest_of_bytes(raw)}
        content = {"entries": [entry], "entry_count": 1,
                   "total_bytes": len(raw), "tree_digest": digest([entry])}
        output = {"name": role_contract.HANDOFF_OUTPUT,
                  "type": "directory-result", "status": "present",
                  "content_manifest": content,
                  "artifact": {"artifact_id": "artifact-handoff-1",
                               "media_type": "text/plain", "bytes": len(raw),
                               "content_digest": content["tree_digest"],
                               "locator": "file:///var/lib/baton/x/handoff"},
                  "result_metadata": {}}
        receipt = {"custody": "accepted" if accepted else "rejected",
                   "artifacts": [{"artifact_id": "artifact-handoff-1",
                                  "custody_locator": "file://" + root}]}
        return root, {"outputs": [output]}, receipt

    def classified(self, digest_=CONTINUATION_DIGEST):
        document = handoff_request("a" * 40)
        document["continuation"] = {"reference": CONTINUATION_REFERENCE,
                                    "digest": digest_}
        return {"handoff": document}

    def test_the_exact_bytes_are_read_and_proved(self):
        _root, result, receipt = self.custody()
        self.assertEqual(native_handoffs.retained_continuation(
            result, receipt, self.classified()), CONTINUATION_TEXT)

    def test_a_missing_continuation_refuses(self):
        root, result, receipt = self.custody()
        os.unlink(os.path.join(root, "continuation.txt"))
        caught = self.refusal(native_handoffs.retained_continuation,
                              result, receipt, self.classified())
        self.assertIn("not in accepted custody", str(caught))

    def test_a_tampered_continuation_refuses(self):
        root, result, receipt = self.custody()
        with open(os.path.join(root, "continuation.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("finish something else\n")
        caught = self.refusal(native_handoffs.retained_continuation,
                              result, receipt, self.classified())
        self.assertIn("differs from the frozen custody", str(caught))

    def test_a_continuation_the_request_did_not_name_refuses(self):
        _root, result, receipt = self.custody()
        caught = self.refusal(native_handoffs.retained_continuation,
                              result, receipt,
                              self.classified("sha256:" + "d" * 64))
        self.assertIn("the request was about", str(caught))

    def test_a_link_in_custody_is_not_followed(self):
        _root, result, receipt = self.custody(link=True)
        caught = self.refusal(native_handoffs.retained_continuation,
                              result, receipt, self.classified())
        self.assertIn("not in accepted custody", str(caught))

    def test_custody_that_is_not_accepted_refuses(self):
        _root, result, receipt = self.custody(accepted=False)
        caught = self.refusal(native_handoffs.retained_continuation,
                              result, receipt, self.classified())
        self.assertIn("ACCEPTED custody", str(caught))

    def test_a_yield_records_only_the_continuation_its_request_names(self):
        round_ = self.implementation_round(1)
        caught = self.refusal(
            native_handoffs.record_yield, self.jobs,
            stage_id="job-a/implementation", episode=1,
            attempt_id=round_["attempt_id"],
            kind=native_handoff.CLARIFICATION_KIND, message_id="msg-1",
            handoff_digest="sha256:" + "1" * 64,
            checkpoint_id="checkpoint-1",
            continuation_digest=CONTINUATION_DIGEST,
            task_digest="sha256:" + "3" * 64, destination=REVIEWER,
            continuation="a note the request never named\n")
        self.assertIn("exact continuation the request was about",
                      str(caught))


class TheHoldIsRecordedOnceAndRereadForever(HandoffCase):

    def test_one_durable_pending_escalation_per_request(self):
        held = self.yielded()
        answered = self.answered(held, disposition="escalate")
        first = native_handoffs.record_hold(
            self.jobs, stage_id="job-a/implementation",
            episode=held["episode"],
            message_id=answered["reply"]["message"]["message_id"],
            request_id=held["message"]["message_id"],
            destination=answered["reply"]["message"]["destination"],
            checkpoint_id=held["checkpoint_id"])
        again = native_handoffs.record_hold(
            self.jobs, stage_id="job-a/implementation",
            episode=held["episode"],
            message_id=answered["reply"]["message"]["message_id"],
            request_id=held["message"]["message_id"],
            destination=answered["reply"]["message"]["destination"],
            checkpoint_id=held["checkpoint_id"])
        self.assertEqual(first, again)
        self.assertEqual(first["destination"], OWNER)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (native_handoffs.HOLD_KIND,)).fetchone()[0], 1)
        self.assertEqual(
            native_handoffs.hold_of(self.jobs, "job-a/implementation",
                                    held["episode"]), first)

    def test_the_escalation_goes_to_the_owner_and_not_to_the_reviewer(self):
        held = self.yielded()
        answered = self.answered(held, disposition="escalate")
        self.assertEqual(answered["reply"]["message"]["destination"], OWNER)
        self.assertNotEqual(answered["reply"]["message"]["destination"],
                            REVIEWER)
        self.assertEqual(len(self.authority.handoff_escalations(WORK_A)), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
