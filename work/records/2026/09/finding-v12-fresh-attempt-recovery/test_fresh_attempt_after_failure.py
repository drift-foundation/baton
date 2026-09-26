"""W266337 stage 3: a FAILED Job round, settled, then a fresh attempt that wins.

Owner 269130 and thread T266337: through supported interfaces fail one small
disposable Job, settle its resources, then complete a FRESH isolated attempt with
correct effects and result attribution -- one bounded runnable command, real
affected machinery, a deterministic provider and an accurately labelled controlled
adapter.

THREE CLASSES, AND WHAT EACH ONE IS FOR. They are not interchangeable and the
module says so here rather than leaving a reader to infer it:

  `AFailedRoundSettlesAndAFreshAttemptSucceeds` -- the JOB-LAYER correction
  bookkeeping, on the accepted `DriverCase`. Real `advance_correction`, real
  endings, real readers; its attempt rows and frozen outputs are that fixture's
  own documented shortcut, so NO runtime is started on this path and nothing here
  is evidence about a run. Review 2026-09-25T21-28-53Z is right that this proves
  correction bookkeeping and not a failed run; it is kept as supplementary.

  `AFailedRunSettlesAndAFreshRunSucceeds` -- the RUNTIME AND RESOURCE schedule.
  A real reservation, the real lane interlock, the real abandonment and cleanup,
  the real quiescence-gate discharge, a real fresh run and a really accepted
  frozen result with its artifact bytes read back from the store.

  `AGatedJobRecoversAndItsSuccessorSucceeds` -- the two composed on ONE identity
  chain: a Job on a correction episode, that episode's attempt really started and
  really abandoned, both supported recoveries, the ordinary replacement, and the
  successor's WHOLE ENDING -- `review_driver.end_implementation`, then the fenced
  routing, then the quiescence-gate discharge that ending's own fence owes, and
  only then the Job's settlement.

WHAT IS REAL: a real `JobStore` and `ControlStore` on a disposable temporary root,
a real development line, the real offer/claim/activation path, real runtime starts
through `request_runtime_start`, the real `abandon_attempt`,
`discharge_abandoned_quiescence_gate`, `restore_abandoned_correction`,
`episodes.restart_abandoned_correction`, `sweep`, `output.request_freeze`,
`request_intake`, the real `review_driver.end_implementation` with every operation
it composes, the real `discharge_quiescence_gate`, and the real Job-side ending
records.

THE CONTROLLED AND SIMULATED PARTS, NAMED AS THE THREAD REQUIRES. Every engine is
a FAKE adapter. Every authority is a deterministic in-process session -- including
its fence, its gate discharge, the assignment it answers for a recovered
generation and its FENCED ROUTING, whose modelled and unmodelled halves
`routes_fenced` names one by one. The integration PUBLICATION is a seam that
records when it was asked and publishes nothing anywhere. The checkpoint profile
is deterministic with no version control behind it. The worker's output bytes are
written by this module as a stand-in for a worker, and its claimed completion
envelope is derived from those bytes rather than chosen. No fake attests that a
real container ran, stopped or produced anything; none attests that a real
authority fenced, routed or released a Work; and none attests that any candidate
was published.

AND ONE ROUND IS EXPLICIT PRIOR HISTORY. The composed class's round 1 -- its
writer, its worker completion, its reviewer and that reviewer's frozen output -- is
fixture setup standing in for a round this Job had already finished, exactly as
review 2026-09-25T22-18-41Z authorizes. It is labelled at every step and none of
it is counted as newly executed proof.

WHAT THIS STILL DOES NOT CLAIM, stated up front: no two-Job adoption, no
preserved-run recovery, no live provider or daemon evidence, no deadline expiry,
and no resolution of the `uncertain` runtime state.

AND ONE READER THIS MODULE DELIBERATELY DOES NOT ASSERT THROUGH.
`projection.stage_states` is the Job's own status view, and its `_ending_owed`
rule is the consumer of the settlement above -- but it derives every stage's
observation through a canonical OPERATIONS surface, and the only one available
here is `FakeOperations`, whose observations are values a case sets rather than
reads. Asserting a stage `completed` through it would be asserting what this
module had just written into a fake. So the Job-side completion is measured
through `ending.pending_endings` and `ending.ending_of`, which read this store's
own stage and episode rows -- and `pending_endings` is precisely the reader
review 2026-09-26T00-26-46Z probed and found empty while the ending was owed.
"""
import hashlib
import os
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal               # noqa: E402
from baton_v12.job_manager import episodes                     # noqa: E402
from baton_v12.job_manager.documents import \
    CORRECTION_ENDINGS                                         # noqa: E402

from baton_v12.contracts.canonical import digest                # noqa: E402
from baton_v12.worker_manager import activate_assignment        # noqa: E402
from baton_v12.worker_manager.manifests import retain_manifest  # noqa: E402

from tests.manager import input_roots                           # noqa: E402
from tests.manager.disk_roots import disk_backed_under           # noqa: E402
from baton_v12.worker_manager import (AuthorityPort,             # noqa: E402
                                      ControlStore, certify_profile)
from baton_v12.worker_manager.workspaces import \
    configure_workspace_storage                                 # noqa: E402
from baton_v12.worker_manager import frozen_output_of, output    # noqa: E402
from baton_v12.worker_manager.attempts import (                # noqa: E402
    reconcile_runtime, request_runtime_start)
from baton_v12.worker_manager.output import freeze_operation    # noqa: E402
from baton_v12.worker_manager.workspaces import \
    assignment_workspace                                        # noqa: E402
import baton_v12.worker_manager as worker_manager              # noqa: E402

from baton_v12.job_manager import (JobStore, attempting as              # noqa: E402
                                   job_attempting, live_of, stage_rows,
                                   submit, sweep)
from baton_v12.job_manager import ending                        # noqa: E402
from baton_v12.job_manager.documents import EXCLUSION_ENDINGS   # noqa: E402
from baton_v12.worker_manager.intake import request_intake      # noqa: E402
from baton_v12.worker_manager import (create_line,              # noqa: E402
                                      freeze_checkpoint, grant_writer,
                                      line_of, record_verdict, writer_of)
from baton_v12.worker_manager import review_cycles          # noqa: E402
from baton_v12.worker_manager.review_cycles import \
    restore_abandoned_correction                                # noqa: E402
from baton_v12.worker_manager.source_boundary import \
    nominate_source                                             # noqa: E402
from baton_v12.job_manager.review_driver import (               # noqa: E402
    end_implementation, prepare_implementation, prepare_review)
from baton_v12.worker_manager import claimed_offers_for         # noqa: E402

import tests.manager.test_attempts as runtime                  # noqa: E402
from tests.job_manager.fixtures import (FakeOperations, job,    # noqa: E402
                                        stage, submission)
from tests.job_manager.test_review_driver import (              # noqa: E402
    DriverCase, Port as DriverPort, Profile as CheckpointProfile)

FRESH = "attempt-2"
RETENTION = "sha256:" + "7" * 64

# The composed Job recovery's own names. BASE is the accepted line fixtures'
# declared base; the stage id is the one a Job submission composes.
BASE = "a" * 40
STAGE = "job-a/implementation"
PRIOR_WRITER = "prior-writer-attempt"
PRIOR_REVIEWER = "prior-review-attempt"


class AFailedRoundSettlesAndAFreshAttemptSucceeds(DriverCase):
    """Stage 3's schedule, on the accepted round-driving machinery."""

    KINDS = ("implementation", "review")

    def episode_identities(self, kind):
        """The live episode's own identities, which must not carry over."""
        live = self.live(kind)
        return {"episode": live["episode"], "offer_id": live["offer_id"],
                "attempt_id": live["attempt_id"]}

    # -- the failure, the settlement, and the fresh attempt -------------------

    def test_a_failed_round_is_settled_and_a_fresh_round_completes(self):
        """THE WHOLE STAGE IN ONE SCHEDULE, measured at each step.

        Round 1 is REVIEWED AND SENT BACK -- a decided failure, not an abandoned
        offer -- then `advance_correction` settles both episodes through the
        supported interface, and round 2 runs to an ACCEPTED verdict on fresh
        identities.
        """
        before = {}
        first = self.round(1, "changes-requested")
        for kind in self.KINDS:
            before[kind] = self.episode_identities(kind)
            self.assertEqual(before[kind]["episode"], 1)
        self.assertEqual(first["verdict"]["disposition"], "changes-requested")

        # THE SUPPORTED SETTLEMENT. Both episodes end, and they end with the
        # correction's own ending rather than being quietly replaced.
        answered = self.correct(first)

        for kind in self.KINDS:
            history = self.history(kind)
            self.assertEqual(len(history), 2, history)
            self.assertEqual(history[0]["ended_state"], CORRECTION_ENDINGS[0])
            self.assertIsNone(history[1]["ended_state"])
            self.assertEqual(answered[kind]["episode"], 2)
            # FRESH IDENTITIES: nothing about the failed episode is reused.
            after = self.episode_identities(kind)
            self.assertEqual(after["episode"], 2)
            self.assertNotEqual(after["offer_id"], before[kind]["offer_id"])
            self.assertNotEqual(after["attempt_id"],
                                before[kind]["attempt_id"])

        # AND THE FRESH ROUND COMPLETES, based on the failed round's checkpoint,
        # with the accepting verdict this Job was waiting for.
        second = self.round(2, "accepted", based=first["checkpoint_id"])
        self.assertEqual(second["verdict"]["disposition"], "accepted")
        self.assertNotEqual(second["checkpoint_id"], first["checkpoint_id"])

    def test_the_result_is_attributed_to_the_fresh_attempt_only(self):
        """CORRECT RESULT ATTRIBUTION, which is the stage's actual subject.

        The accepted result must belong to round 2's own attempt and checkpoint.
        The failed round stays auditable and keeps its own -- a recovery that
        credited the new result to the old attempt, or lost the old record, would
        pass a "it eventually succeeded" test and still be wrong.
        """
        first = self.round(1, "changes-requested")
        self.correct(first)
        second = self.round(2, "accepted", based=first["checkpoint_id"])

        # THE TWO ROUNDS ARE DISTINCT EVERYWHERE THEY ARE NAMED.
        self.assertNotEqual(second["writer"]["writer_id"],
                            first["writer"]["writer_id"])
        self.assertNotEqual(second["attachment"]["attachment_id"],
                            first["attachment"]["attachment_id"])
        self.assertNotEqual(second["verdict_id"], first["verdict_id"])
        # THE ACCEPTED VERDICT NAMES ROUND 2's CHECKPOINT, not round 1's.
        self.assertEqual(second["verdict"]["checkpoint_id"],
                         second["checkpoint_id"])
        self.assertNotEqual(second["verdict"]["checkpoint_id"],
                            first["checkpoint_id"])
        # AND THE FAILED ROUND IS STILL THERE, with its own verdict intact.
        self.assertEqual(first["verdict"]["disposition"], "changes-requested")
        self.assertEqual(first["verdict"]["checkpoint_id"],
                         first["checkpoint_id"])
        for kind in self.KINDS:
            history = self.history(kind)
            self.assertEqual([one["episode"] for one in history], [1, 2])
            self.assertEqual(history[0]["ended_state"], CORRECTION_ENDINGS[0])

    def test_each_round_keeps_its_own_frozen_result(self):
        """ISOLATION AND ATTRIBUTION, read from content that actually exists.

        MY FIRST VERSION OF THIS CASE WAS VACUOUS AND I CAUGHT IT BEFORE
        DELIVERY. It compared `receipts_of` before and after the correction --
        but in this fixture that reader answers an EMPTY mapping for every
        episode, so the assertion was `{} == {}` and proved nothing about
        isolation. I am recording that rather than quietly deleting it, because
        "the test passed" was exactly the wrong reason to keep it.

        This asks the supported result reader instead, over rows the fixture
        really writes: each review attempt's own frozen output. Two rounds, two
        distinct results, and the failed round's result is still readable after
        the fresh one exists.
        """
        from baton_v12.worker_manager import frozen_output_of

        first = self.round(1, "changes-requested")
        stale = frozen_output_of(self.control, "review-attempt-1")
        self.assertIsNotNone(stale, "the fixture wrote no result to attribute")
        self.assertEqual(stale["result_id"], "result-review-attempt-1")

        self.correct(first)
        self.round(2, "accepted", based=first["checkpoint_id"])

        fresh = frozen_output_of(self.control, "review-attempt-2")
        self.assertEqual(fresh["result_id"], "result-review-attempt-2")
        self.assertNotEqual(fresh["result_id"], stale["result_id"])
        # AND THE FAILED ROUND'S RESULT IS NEITHER OVERWRITTEN NOR DESTROYED:
        # the record stays auditable, which is the other half of attribution.
        kept = frozen_output_of(self.control, "review-attempt-1")
        self.assertEqual(kept["result_id"], stale["result_id"])
        self.assertEqual(kept, stale)

    # -- the settlement is not re-enterable ------------------------------------

    def test_the_settlement_is_one_act_however_many_times_it_is_asked(self):
        """THE SUPPORTED INTERFACE IS EFFECTIVELY ONCE.

        A recovery that opened a third episode on a repeated call would hand the
        same Job two live successors, which is the overlap every stage of this
        campaign exists to prevent.
        """
        first = self.round(1, "changes-requested")
        once = self.correct(first)
        again = self.correct(first)

        self.assertEqual(again, once)
        for kind in self.KINDS:
            self.assertEqual(len(self.history(kind)), 2)
            self.assertEqual(self.live(kind)["episode"], 2)

    def test_a_correction_needs_the_failed_round_that_earned_it(self):
        """AND IT IS NOT AVAILABLE ON DEMAND.

        The settlement is authorized by the verdict and checkpoint of the round
        that was actually sent back. Asking with another round's verdict is
        refused, so "start a fresh attempt" is never a way around a review.
        """
        first = self.round(1, "changes-requested")
        self.correct(first)
        second = self.round(2, "accepted", based=first["checkpoint_id"])

        # THE ACCEPTED ROUND EARNS NO CORRECTION, and the refusal is asserted by
        # its exact reason rather than by its type: a case that accepts ANY
        # refusal here would pass just as happily on an unrelated precondition.
        with self.assertRaises(ContractRefusal) as caught:
            episodes.advance_correction(
                self.jobs, self.control, job_id="job-a",
                line_id=self.line["line_id"],
                checkpoint_id=second["checkpoint_id"],
                verdict_id=second["verdict_id"])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("only 'changes-requested' asks for another round",
                      caught.exception.message)
        for kind in self.KINDS:
            self.assertEqual(len(self.history(kind)), 2)
            self.assertEqual(self.live(kind)["episode"], 2)


GENERATED = b"the fresh attempt wrote this\n"


class AFailedRunSettlesAndAFreshRunSucceeds(
        runtime.TheRuntimeIsStartedOnceAndReconciled):
    """THE COMPOSED SCHEDULE, on the supported runtime, resource and output
    interfaces -- nothing inserted.

    Review 2026-09-25T21-28-53Z: the Job-layer class above uses a fixture that
    INSERTS completed attempts and frozen outputs, so it proves correction
    bookkeeping and not an actual run. Review 2026-09-25T21-36-31Z then asked for
    this schedule to reach a real accepted output rather than stopping at a
    recorded disposition. Every step below is a supported call:

        request_runtime_start          the real reservation (stage 1)
        the successor's start          refused by the real lane interlock
        abandon_attempt                the real settlement, which releases
        request_runtime_start again    the fresh run, on its own identity
        reconcile_runtime              a real positive quiescent observation
        output.request_freeze          the real acceptance of real bytes

    AND NO IDENTITY CORRECTION TURNED OUT TO BE NEEDED, which I am recording
    because I first built one. The freeze reaches §4's rule that a Work id carries
    its authority's 8-character prefix. `tests.manager.test_offers` pairs
    authority `0*31 + "a"` with Work `0000000a-W1`, which does NOT satisfy it --
    that pair simply never reaches the validator in its own suite. But
    `delivered()`, the path this class uses, builds its assignment from
    `VALID_WORK` = authority `43c55d4b...` with Work `43c55d4b-W1439`, which does.
    So the fix was to use the delivered path, not to rewrite identities, and the
    validator is untouched either way.

    WHAT IS SIMULATED, named: the engine is the accepted FAKE adapter and the
    authority is the fixture's deterministic session. The worker's output bytes
    are written by this module -- a stand-in for a worker, labelled as such --
    and the sealing adapter derives its manifest FROM those bytes rather than
    asserting numbers, so what the manager accepts describes what is on disk.
    """

    def delivered_as(self, attempt_id, offer_id, generation=1):
        """A second delivered attempt, because the accepted helper takes one.

        `TheRuntimeIsStartedOnceAndReconciled.delivered` hard-codes
        `offer_id="offer-1"`, so calling it twice collides at §4.2 -- one
        identity, different operands. This mirrors its sequence with the offer
        parameterised and nothing else changed: the same supported calls in the
        same order, so the second attempt is delivered the way the first is.

        WHAT IT DELIBERATELY DOES NOT TOUCH IS THE WORK PROJECTION. Review
        2026-09-25T21-56-23Z: my earlier version reset `_work` to
        queued/gate=None here, which ERASED the quiescence gate the abandonment
        had just installed instead of settling it -- "setting the projection is
        not proof the gate was settled". The projection is now moved by exactly
        two things: the fake's fence (which installs the gate) and the fake's own
        accepted `satisfy_gate` (which clears it). So this helper can only deliver
        a successor into a Work the authority has really released.
        """
        work_ref = dict(self.VALID_WORK)
        live = {"work_ref": dict(work_ref), "participant": runtime.WHO,
                "generation": generation}
        # WHICH WORK THE PROJECTION IS ABOUT, and nothing else about it. The
        # accepted session is constructed around another suite's identities, so a
        # standalone delivery needs the authority, scope and route of the Work
        # this class actually assigns. `status`, `phase`, `handler` and `gate` are
        # CARRIED OVER rather than written, so a held gate survives this helper.
        self.session._work = dict(
            self.session._work, authority_uuid=work_ref["authority_uuid"],
            scope=runtime.SCOPE, route=runtime.ROUTE)
        self.session.claim_answer = {"assignment": dict(live),
                                     "claim_event": generation,
                                     "decision": runtime.decision()}
        self.session.live_assignment = dict(live)
        given, assignment = input_roots.documents(
            work_ref=work_ref, participant=runtime.WHO, generation=generation,
            runtime_attempt_id=attempt_id)
        runtime.issue_offer(self.store, self.port, offer_id=offer_id,
                            work_id=work_ref["work_id"],
                            runtime_attempt_id=attempt_id,
                            input_digest=given["manifest_digest"],
                            policy_digest="sha256:" + "2" * 64,
                            profile_digest=runtime.PROFILE,
                            profile_name="reference",
                            mint_bearer=lambda: "bearer-2")
        runtime.accept_offer(self.store, self.port, offer_id=offer_id,
                             decision="accept", bearer="bearer-2",
                             now=runtime.NOW, runtime_attempt_id=attempt_id,
                             work_ref=dict(work_ref))
        runtime.record_attempt(self.store, attempt_id=attempt_id,
                               adapter_name="acp",
                               adapter_digest=runtime.ADAPTER,
                               profile_digest=runtime.PROFILE,
                               input_digest=given["manifest_digest"],
                               policy_digest="sha256:" + "2" * 64)
        # THE MANAGER RETAINS THE INPUT MANIFEST, which the freeze compares the
        # declared outputs against: "a validator can prove a document is
        # internally well formed; it cannot compare it with a document it never
        # sees." `delivered()` composes the root without retaining it, because
        # its own cases never reach that comparison.
        retain_manifest(self.store, given, "inputManifest")
        runtime.submit_claim(self.store, self.port, offer_id=offer_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=dict(live))
        storage = input_roots.storage_under(self)
        inputs = assignment_workspace(self.group, storage, attempt_id)["inputs"]
        runtime.compose_input_root(
            inputs, given, assignment,
            assignment=dict(assignment["assignment_ref"]),
            runtime_attempt_id=attempt_id)
        return inputs

    def fences_faithfully(self):
        """The fake authority's fence, APPLIED the way the real one applies it.

        Review 2026-09-25T21-56-23Z's correction, and the reason my earlier
        schedule could not prove a recovery. The accepted `FakeSession.cancel`
        returns a fence document and changes nothing: the assignment it says it
        ended keeps answering as live, and the gate it says it installed is
        nowhere. `authority/core.py:_end_assignment` does all three in one
        transaction -- end the assignment, move the Work to `block`, and install
        `runtime-quiescence:<generation>` -- so this models exactly that and
        nothing else.

        THE ANSWER IS DERIVED FROM WHAT WAS ASKED, which also retires the hack
        this replaces: the accepted fixture builds its fence answer at
        construction from another suite's identities, and my first version
        patched that answer by hand. Composing it from the cancellation's own
        `expect` makes it correct by construction for whatever generation is
        being fenced -- and the port still owns and compares every member of it.

        FIXTURE SETUP, NOT EVIDENCE: a fake cannot attest that a real authority
        fenced anything. What the cases below measure is what the MANAGER does
        when the authority behaves this way, which is the half under test.
        """
        session = self.session

        def cancel(operands):
            session.calls.append(("cancel", dict(operands)))
            expect = operands["expect"]
            gate = f"runtime-quiescence:{expect['generation']}"
            answer = {"cause": "cancelled", "assignment": dict(expect),
                      "phase": "block", "gate": gate, "fenced": True}
            session.fence_answer = answer
            session._work = dict(session._work, phase="block", gate=gate,
                                 handler=None)
            session.live_assignment = None
            return dict(answer)

        session.cancel = cancel

        # AND THE OTHER END OF THE FENCE ANSWERS THE EVIDENCE'S KIND. The
        # accepted `satisfy_gate` already models the authority's two rules -- the
        # token must be the one holding the Work, and a committed identity
        # replays -- and it is left to do exactly that. What it composes from is
        # `discharge_answer`, whose default carries the GATE's kind; the real
        # authority answers the kind of the evidence it accepted
        # (`authority/core.py:1746`), and an abandonment's evidence is positive
        # absence. This measured the difference: the act refused
        # "the authority answered evidence kind 'runtime-quiescence' ... and this
        # act requires 'runtime-absent'", which is the product holding a fake to
        # the authority's own contract.
        accepted_discharge = session.satisfy_gate

        def satisfy_gate(operands):
            return dict(accepted_discharge(operands),
                        kind=operands["evidence"]["kind"])

        session.satisfy_gate = satisfy_gate

    def projection(self):
        """The Work as the authority now projects it -- phase and gate."""
        return {"phase": self.session._work["phase"],
                "gate": self.session._work["gate"]}

    def custodian(self, runtime_id):
        """The accepted abandonment-capable fake, with its minted id chosen."""
        adapter = runtime.ExplicitAbandonmentFencesBeforeItRemoves.Custodian([])
        adapter.runtime_id = runtime_id
        return adapter

    def lane_holders(self):
        """The real lane rows, read from a connection nothing here owns."""
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            return [row[0] for row in
                    beside.execute("SELECT holder FROM runtime_lanes")]
        finally:
            beside.close()

    def generated(self, attempt_id):
        """Bytes a worker would have produced, written where its output lives."""
        roots = assignment_workspace(self.group, self.storage, attempt_id)
        place = os.path.join(roots["workspace"], "proposal")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "answer.txt"), "wb") as writing:
            writing.write(GENERATED)
        return os.path.join(place, "answer.txt")

    def sealing_for(self, attempt_id, written):
        """A controlled adapter that seals what is ACTUALLY on disk.

        The manifest is derived by reading the file, so the bytes the manager
        accepts are the bytes the run produced. A fixture that asserted the
        numbers instead could agree with nothing.
        """
        answer, size, content, _terminal = self.sealed_document(
            attempt_id, written)

        class Sealing(runtime.ExplicitAbandonmentFencesBeforeItRemoves
                      .Custodian):
            def seal(inner, operands):
                inner.order.append("seal")
                return answer

        adapter = Sealing([])
        adapter.runtime_id = self.row(attempt_id)["runtime_id"]
        return adapter, size, content

    def sealed_document(self, attempt_id, written):
        """THE SEALED RESULT ITSELF, derived by reading the bytes on disk.

        Split out of `sealing_for` so the composed ending below can hand the
        SAME document to an adapter carrying the whole surface an
        `end_implementation` types, rather than keeping a second spelling of
        one manifest. Nothing about its derivation changed.
        """
        with open(written, "rb") as reading:
            body = reading.read()
        content = "sha256:" + hashlib.sha256(body).hexdigest()
        entries = [{"path": os.path.basename(written), "bytes": len(body),
                    "content_digest": content}]
        row = self.row(attempt_id)
        document_outputs = [
            {"name": "proposal", "type": "directory-result",
             "status": "present", "result_metadata": {},
             "content_manifest": {
                 "entries": entries, "entry_count": len(entries),
                 "total_bytes": len(body),
                 "tree_digest": digest(entries)},
             "artifact": {"artifact_id": "artifact-" + attempt_id,
                          "media_type": "text/plain",
                          "bytes": len(body),
                          "content_digest": content,
                          "locator": "file://" + written}}]
        document = {
            "version": {"major": 1, "minor": 0},
            "manifest_id": "result-manifest-" + attempt_id,
            "created_at": runtime.NOW, "extensions": {},
            "schema": "baton.worker-manifest/result",
            "result_id": "result-" + attempt_id,
            "assignment_ref": {
                "work_ref": {"authority_uuid": row["authority_uuid"],
                             "work_id": row["work_id"]},
                "participant": row["assignment_participant"],
                "generation": row["assignment_generation"]},
            "input_manifest_digest": row["input_digest"],
            "policy_digest": row["policy_digest"],
            "disposition": "completed",
            "outputs": document_outputs,
            "evidence": [],
            "freeze_operation": dict(freeze_operation(row)),
            "manager_observed_at": runtime.NOW,
            # THE WORKER'S OWN COMPLETION ENVELOPE, MEASURED RATHER THAN
            # CHOSEN. Review 2026-09-26T00-26-46Z asks for a measured output
            # identity at the terminal correlation, and this is the identity
            # that correlation compares: `_correlated` holds the worker's
            # claimed envelope digest against the one the MANAGER validated out
            # of the sealed result, so a constant on both sides would make that
            # comparison agree with itself. Derived from the outputs this
            # document describes, which are derived from the bytes on disk.
            "completion_manifest_digest": digest(document_outputs)}
        answer = {**document, "manifest_digest": digest(document)}
        return (answer, len(body), content,
                document["completion_manifest_digest"])

    def failed_and_settled(self):
        """FAIL ONE RUN AND SETTLE IT -- up to, and NOT including, its gate.

        What this leaves is the state a declared abandonment really leaves: the
        runtime removed, the lane free, the generation FENCED and the Work held
        at `runtime-quiescence:1`. That is where the recovery this stage is about
        actually begins, and every case below starts from here rather than from a
        projection somebody rewrote.
        """
        inputs, _given, _assignment = self.delivered()
        first = self.custodian("runtime-failed")
        started = request_runtime_start(self.store, first,
                                        attempt_id=runtime.ATTEMPT,
                                        inputs=inputs)
        self.assertEqual(started["runtime_id"], "runtime-failed")
        self.assertEqual(self.lane_holders(), [runtime.ATTEMPT])

        # NO FRESH RUN WHILE THE FAILED ONE HOLDS THE RESERVATION -- stage 2's
        # interlock, reused rather than restated. The successor is delivered at
        # the generation that is live NOW, so what refuses it is the lane and not
        # a stale assignment.
        blocked_inputs = self.delivered_as("attempt-3", "offer-3")
        blocked = self.custodian("runtime-blocked")
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, blocked, attempt_id="attempt-3",
                                  inputs=blocked_inputs)
        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.assertEqual(blocked.started, [])

        # THE CONTROLLED FAILURE, SETTLED THROUGH THE SUPPORTED ENDING, with the
        # authority fencing the way a real one fences.
        self.fences_faithfully()
        answered = worker_manager.abandon_attempt(
            self.store, self.port, first, attempt_id=runtime.ATTEMPT,
            reason="the worker never answered",
            retention_policy_digest=RETENTION)
        self.assertEqual((answered["cleanup"]["cleanup"],
                          answered["cleanup"]["state"]), ("retained", "absent"))
        self.assertEqual([one["runtime_id"] for one in first.abandoned],
                         ["runtime-failed"])
        self.assertEqual(self.lane_holders(), [])

        # THE GENERATION IS REALLY ENDED AND THE WORK IS REALLY HELD. Review
        # 2026-09-25T21-48-53Z: the accepted session used to report an assignment
        # fenced and keep answering it as live, so my first schedule ran the
        # fresh attempt on the very generation the abandonment had fenced.
        self.assertIsNone(self.session.live_assignment)
        self.assertEqual(self.projection(),
                         {"phase": "block", "gate": "runtime-quiescence:1"})

        # THE FAILED GENERATION PUBLISHED NOTHING, and never will: its attempt
        # was abandoned rather than completed, so there is no result of its own
        # to accept. (The typed refusal for publishing ON an ended generation is
        # asserted in its own case below, where the attempt IS quiescent and the
        # liveness check is the boundary reached.)
        self.assertIsNone(frozen_output_of(self.store, runtime.ATTEMPT))
        return answered

    def discharge(self, attempt_id=None, policy=RETENTION):
        """THE SUPPORTED GATE SETTLEMENT, on the real operation."""
        return worker_manager.discharge_abandoned_quiescence_gate(
            self.store, self.port,
            attempt_id=runtime.ATTEMPT if attempt_id is None else attempt_id,
            retention_policy_digest=policy)

    def test_the_abandonment_discharges_the_gate_it_installed(self):
        """THE RECEIPT, AND THAT IT IS THIS ABANDONMENT'S OWN.

        Review 2026-09-25T21-56-23Z probed my previous schedule and found
        `abandoned_gate_discharge_of` answering None after it "succeeded": the
        abandonment fenced and cleaned up, and nothing ever carried its absence
        proof to the gate that fence installed. A recovery that skips this leaves
        the generation held at the authority forever.
        """
        settled = self.failed_and_settled()
        # NOTHING IS OWED YET AND NOTHING IS CLAIMED -- the reader the review
        # probed, measured before the act rather than asserted about it.
        self.assertIsNone(worker_manager.abandoned_gate_discharge_of(
            self.store, runtime.ATTEMPT))

        receipt = self.discharge()

        # THE RECEIPT NAMES THE ATTEMPT, THE FENCED GENERATION, ITS GATE AND THE
        # EXACT RUNTIME THE ABANDONMENT OBSERVED ABSENT.
        self.assertEqual(receipt["attempt_id"], runtime.ATTEMPT)
        self.assertEqual(receipt["gate"], "runtime-quiescence:1")
        self.assertEqual(receipt["assignment"]["generation"], 1)
        self.assertEqual(receipt["assignment"]["work_ref"],
                         dict(self.VALID_WORK))
        self.assertEqual(receipt["runtime_id"], "runtime-failed")
        self.assertEqual(receipt["evidence"],
                         {"kind": "runtime-absent", "runtime": "runtime-failed"})
        self.assertEqual(receipt["retention_policy_digest"], RETENTION)
        # AND IT IS EARNED BEHIND THIS REMOVAL, not behind any removal: the
        # cleanup operation it carries is the one the abandonment committed.
        committed = worker_manager.abandonment_cleanup_of(
            self.store, attempt_id=runtime.ATTEMPT,
            retention_policy_digest=RETENTION)
        self.assertEqual(receipt["cleanup_operation"],
                         committed["cleanup"]["operation"])
        self.assertEqual(committed["cleanup"]["operation"],
                         settled["cleanup"]["operation"])
        # THE AUTHORITY'S OWN ANSWER IS WHAT WAS JOURNALLED, and it says the
        # Work is released.
        self.assertEqual(receipt["authority_receipt"]["phase"], "queued")
        self.assertEqual(receipt["authority_receipt"]["gate"],
                         "runtime-quiescence:1")
        # THE AUTHORITY REALLY MOVED, with the absence evidence in its journal --
        # the fake's accepted `satisfy_gate` compares the token against the one
        # holding the Work, so this transition is the gate's own and not a reset.
        self.assertEqual(self.projection(), {"phase": "queued", "gate": None})
        self.assertEqual(self.session.gate_evidence,
                         [{"kind": "runtime-absent", "runtime": "runtime-failed"}])
        # AND THE PUBLIC READER NOW ANSWERS THE SAME RECEIPT.
        self.assertEqual(worker_manager.abandoned_gate_discharge_of(
            self.store, runtime.ATTEMPT), receipt)
        # ASKING AGAIN IS THE SAME ACT (§4.2): the receipt replays and the
        # authority is not asked a second time.
        self.assertEqual(self.discharge(), receipt)
        self.assertEqual(len(self.session.gate_evidence), 1)

    def test_no_successor_is_admitted_before_the_gate_is_discharged(self):
        """THE NEGATIVE, at the product's own admission boundary.

        A recovery is not "the old run is gone"; it is the old generation
        RELEASED. While the quiescence gate holds, the manager's own offer
        boundary refuses to admit any successor -- which is what makes erasing
        that gate in a fixture a way to pass a test that the deployment would
        fail.
        """
        self.failed_and_settled()
        with self.assertRaises(ContractRefusal) as caught:
            self.delivered_as(FRESH, "offer-2", generation=2)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("an offer is issued only against open, queued, "
                      "unclaimed, ungated Work", caught.exception.message)
        self.assertIn("runtime-quiescence:1", caught.exception.message)
        # AND NOTHING WAS RECORDED FOR THE SUCCESSOR, so the refusal is a
        # closed door rather than a half-delivered attempt.
        self.assertIsNone(self.row(FRESH))

        # THE SAME DELIVERY, AFTER THE SUPPORTED DISCHARGE, IS ADMITTED -- so
        # what refused above was the gate and not the delivery.
        self.discharge()
        self.delivered_as(FRESH, "offer-2", generation=2)
        self.assertEqual(self.row(FRESH)["assignment_generation"], 2)

    def test_a_failed_run_settles_and_a_fresh_run_is_accepted(self):
        """FAIL, SETTLE, DISCHARGE, RUN AGAIN, AND HAVE THE OUTPUT ACCEPTED."""
        self.failed_and_settled()

        # THE GATE THE FENCE INSTALLED IS SETTLED THROUGH THE SUPPORTED
        # OPERATION, and only then is a successor admissible at all.
        self.assertIsNone(worker_manager.abandoned_gate_discharge_of(
            self.store, runtime.ATTEMPT))
        receipt = self.discharge()
        self.assertEqual(receipt["runtime_id"], "runtime-failed")
        self.assertEqual(self.projection(), {"phase": "queued", "gate": None})

        # THE FRESH LIVE GENERATION, obtained the way a recovery does: the
        # authority answers a NEW assignment, generation 2, and the fresh attempt
        # is delivered and claimed against THAT. Deterministic fixture setup,
        # standing in for the authority's own act.
        fresh_inputs = self.delivered_as(FRESH, "offer-2", generation=2)

        # THE FRESH RUN, on its own runtime, to a positive quiescent observation.
        fresh = self.custodian("runtime-fresh")
        opened = request_runtime_start(self.store, fresh, attempt_id=FRESH,
                                       inputs=fresh_inputs)
        self.assertEqual(opened["runtime_id"], "runtime-fresh")
        fresh.observation = {"state": "quiescent", "why": "it finished",
                             "mounts": None}
        reconcile_runtime(self.store, fresh, attempt_id=FRESH,
                          minted="runtime-fresh")
        runtime.observe(self.store, attempt_id=FRESH,
                        axis="worker_disposition", value="completed")

        # AND ITS OUTPUT IS ACCEPTED THROUGH THE SUPPORTED FREEZE, over bytes
        # that are really on disk.
        written = self.generated(FRESH)
        sealing, size, content = self.sealing_for(FRESH, written)
        frozen = output.request_freeze(self.store, self.port, sealing,
                                       attempt_id=FRESH,
                                       disposition="completed")

        # ATTRIBUTED BYTES: the accepted result names the fresh attempt and
        # describes exactly what that run wrote.
        self.assertEqual(self.row(FRESH)["output"], "frozen")
        kept = frozen_output_of(self.store, FRESH)
        self.assertEqual(kept["result_id"], "result-" + FRESH)
        # THE STORE'S OWN ARTIFACT ROW, not my helper's local numbers -- review
        # 2026-09-25T21-48-53Z asked for exactly that distinction.
        [artifact] = kept["artifacts"]
        self.assertEqual(artifact["bytes"], len(GENERATED))
        self.assertEqual(artifact["content_digest"],
                         "sha256:" + hashlib.sha256(GENERATED).hexdigest())
        self.assertEqual(artifact["content_digest"], content)
        self.assertEqual(artifact["bytes"], size)
        # AND THE FAILED RUN HAS NO RESULT AT ALL, while staying auditable.
        self.assertIsNone(frozen_output_of(self.store, runtime.ATTEMPT))
        failed = self.row(runtime.ATTEMPT)
        self.assertEqual(failed["runtime_id"], "runtime-failed")
        self.assertEqual(failed["cleanup"], "retained")
        self.assertEqual(failed["worker_disposition"], "none")
        self.assertEqual(self.row(FRESH)["runtime_id"], "runtime-fresh")
        self.assertEqual(self.lane_holders(), [FRESH])


    def test_a_result_declaring_the_old_generation_is_refused(self):
        """OLD-GENERATION REJECTION, at the real acceptance boundary.

        The recovered attempt runs and completes on the live generation, and then
        its sealed result declares the SUPERSEDED one. The bytes are identical;
        only the assignment reference is stale. Accepting that would let a
        fenced generation publish through a live attempt.
        """
        fresh_inputs = self.delivered_as(FRESH, "offer-2", generation=2)
        fresh = self.custodian("runtime-fresh")
        request_runtime_start(self.store, fresh, attempt_id=FRESH,
                              inputs=fresh_inputs)
        fresh.observation = {"state": "quiescent", "why": "it finished",
                             "mounts": None}
        reconcile_runtime(self.store, fresh, attempt_id=FRESH,
                          minted="runtime-fresh")
        runtime.observe(self.store, attempt_id=FRESH,
                        axis="worker_disposition", value="completed")
        written = self.generated(FRESH)
        adapter, _size, _content = self.sealing_for(FRESH, written)

        honest = adapter.seal

        def stale(operands):
            answer = honest(operands)
            body = {name: one for name, one in answer.items()
                    if name != "manifest_digest"}
            body["assignment_ref"] = {**body["assignment_ref"], "generation": 1}
            return {**body, "manifest_digest": digest(body)}

        adapter.seal = stale
        with self.assertRaises(ContractRefusal) as caught:
            output.request_freeze(self.store, self.port, adapter,
                                  attempt_id=FRESH, disposition="completed")
        # MEASURED, NOT GUESSED: I expected an integrity refusal and the
        # boundary answers `stale-assignment`, which names the fault better than
        # my guess did.
        self.assertEqual(caught.exception.category, "stale-assignment")
        # AND WHAT THE REFUSAL LEAVES BEHIND, measured rather than assumed: the
        # freeze REQUEST is journalled before the sealed result is validated, so
        # the axis rests at `freeze-requested` -- not `open`, which is what I
        # first asserted -- while NO result is recorded. The attempt is left
        # asking, not published.
        self.assertEqual(self.row(FRESH)["output"], "freeze-requested")
        self.assertIsNone(frozen_output_of(self.store, FRESH))


class AGatedJobRecoversAndItsSuccessorSucceeds(
        AFailedRunSettlesAndAFreshRunSucceeds):
    """THE JOB COMPOSITION review 2026-09-25T22-18-41Z enumerated, in one
    schedule on ONE identity chain.

    Everything the runtime class proves stays as it is. What this adds is the
    layer above it: a Job whose implementation stage is on a CORRECTION episode,
    the tested failed attempt bound to that episode and to the line's correction
    writer, and -- after the accepted abandonment, cleanup and gate discharge --
    the two supported recoveries that give the line and the episode back, then an
    ordinary successor that really runs and whose result is really accepted.

        advance_correction              the Job selects the correction (prior)
        request_runtime_start           the correction attempt really starts
        abandon_attempt                 the real declaration and removal
        discharge_abandoned_quiescence_gate   the real gate settlement
        restore_abandoned_correction    the checkout back, the writer excluded
        restart_abandoned_correction    the unfinishable episode ended
        sweep                           the ORDINARY replacement opens one
        request_runtime_start           the successor really runs
        register_ending                 the obligation, before any cleanup
        end_implementation              THE TEN-STEP ENDING, really performed
        route_fenced                    the handoff, while the gate still holds
        discharge_quiescence_gate       the gate that ending's fence installed
        settle_ending                   and only now: the obligation is closed

    THE LAST FOUR ARE REVIEW 2026-09-26T00-26-46Z's CORRECTION. The previous
    candidate froze an output, took custody and then wrote `settle_ending`
    directly -- and that journal operation records the caller's assertion that an
    ending finished without executing or certifying any of it. Its own contract
    requires the driver's evidence, the gate discharge the recorded fence owes
    and the routing the answer earned to have succeeded first, and the reviewer's
    preserved probe measured what the shortcut left behind: cleanup pending, the
    lane still held, the line still writing at the OLD checkpoint, generation 3
    still assigned -- and `pending_endings` empty anyway. Those are this
    attempt's own ending, not a later round.

    WHAT IS PRIOR HISTORY AND THEREFORE FIXTURE SETUP, as the review authorizes
    ("Setup may stand in for the already completed prior round; label it and do
    not count that history as newly executed proof"): round 1 -- its writer
    attempt row, its worker completion, its reviewer attempt and that reviewer's
    frozen output -- is composed with the accepted driver fixture's own shortcuts
    and its own port fakes. NONE of it is counted as executed evidence here, and
    the history it stands in for is a round this Job had already finished before
    the attempt under test existed.

    WHAT IS NOT FAKED, and this is the line the review drew: the failed attempt
    itself, its runtime, its lane, its abandonment, its cleanup, its gate
    discharge, both recovery receipts, the successor's admission, its run, its
    accepted result, and its WHOLE ENDING -- the driver's ten steps, the
    discharge of the gate its checkpoint fence installed, and the Job settlement
    that closes the obligation. Every one of those is a supported operation on
    real durable records.
    """

    def setUp(self):
        # THE RUNTIME FIXTURE'S OWN SETUP, SPELLED OUT FOR ONE REASON: the line
        # boundaries this class reaches refuse a workspace on a memory
        # filesystem ("checkout, build-cache, test-artifacts, output, logs do
        # not rely on scratch"), and the accepted runtime fixture configures its
        # storage under the system temporary directory, which is a tmpfs on this
        # host. Reconfiguring afterwards is correctly refused -- "a changed store
        # is a fresh store rather than a reconfiguration" -- so the DISK-BACKED
        # root is chosen before the deployment record is written, through the
        # accepted `disk_roots` helper the line suites already use. Everything
        # else here is the accepted fixture's own sequence, in its own order.
        self._root = tempfile.TemporaryDirectory(prefix="v12-gated-job-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: runtime.NOW)
        self.addCleanup(self.store.close)
        certify_profile(self.store, "runtime", "reference", runtime.PROFILE)
        self.storage = os.path.join(disk_backed_under(self), "storage")
        os.makedirs(self.storage, exist_ok=True)
        configure_workspace_storage(self.store, self.storage)
        self.group = input_roots.configured_group(self.store)
        self.session = runtime.FakeSession()
        self.port = AuthorityPort(self.session, runtime.fake_claim_signature)

        work = dict(self.VALID_WORK)
        self.jobs = JobStore.open(
            os.path.join(self._root.name, "jobs.sqlite3"),
            authority_uuid=work["authority_uuid"], incarnation="jobs-1",
            clock=lambda: runtime.NOW)
        self.addCleanup(self.jobs.close)
        # ONE JOB WHOSE TWO STAGES NAME THE SAME WORK, which is what a line can
        # attach at all: a line is one (authority, Work) pair and its reviewer is
        # an assignment of that same Work.
        submit(self.jobs, submission("sub-1", jobs=[job("job-a", stages=[
            stage("implementation", work["work_id"]),
            stage("review", work["work_id"],
                  depends_on=[{"job_id": "job-a",
                               "kind": "implementation"}])])]))
        # THE CHECKPOINT PROFILE IS THE ACCEPTED DRIVER'S, plus the one
        # capability the restore requires -- given to this case's own instance,
        # exactly as the accepted recovery fixture does it.
        self.profile = CheckpointProfile()
        self.restore_calls = []
        self.profile.restore_checkpoint = self.restoring
        source = os.path.join(self._root.name, "source")
        os.makedirs(source, exist_ok=True)
        self.line = create_line(self.store, source=nominate_source(source),
                                declared_base=BASE, profile=self.profile,
                                authority_uuid=work["authority_uuid"],
                                work_id=work["work_id"])
        self.fences = {}

    def restoring(self, repository, evidence):
        """The profile's checkout restoration, as the accepted fixture models
        it: verify, move the checkout, and answer only a current validation.

        The calls are recorded here because the driver's Profile does not record
        them, and WHICH checkout was put back on WHICH checkpoint is the fact the
        restoration has to be measured by.
        """
        self.restore_calls.append((repository, dict(evidence)))
        self.profile.validate(repository, evidence)
        self.profile.current_revision = int(evidence["head"], 16)
        return self.profile.validate(repository, evidence, current=True)

    def fence_port(self, participant):
        """The accepted driver's own fence fake, for PRIOR-HISTORY acts only.

        Deliberately not this class's real AuthorityPort: round 1's own fences
        and quiescence settlements are the history this setup stands in for, and
        routing them through the tested authority projection would make the
        fixture's prior round change the state the recovery under test is
        measured against.
        """
        return self.fences.setdefault(participant, DriverPort(participant))

    # -- prior history, composed with the accepted fixture's shortcuts --------

    def inserted(self, attempt_id, generation, participant, principal):
        """One attempt row a runtime would have written, plus its workspace.

        The accepted `DriverCase.attempt` shortcut, spelled here because this
        class's own base is the runtime fixture: "the deployment's half,
        performed here because it is the deployment's".
        """
        work = dict(self.VALID_WORK)
        self.store._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, ?, ?, ?, 'scope', "
            "'role', 'grant', 1)",
            (attempt_id, runtime.NOW, work["work_id"],
             work["authority_uuid"], participant, generation, generation,
             principal))
        assignment_workspace(self.group, self.storage, attempt_id)
        return attempt_id

    def finished(self, attempt_id, *, review=False):
        """The prior round's worker outcome, recorded the fixture's way."""
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'quiescent', worker_disposition = 'completed' "
            "WHERE runtime_attempt_id = ?",
            ("runtime-" + attempt_id, attempt_id))
        if not review:
            return
        self.store._connection.execute(
            "UPDATE attempts SET output = 'frozen', verification = 'passed' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        self.store._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES (?, ?, "
            "'completed', ?, ?, ?)",
            (attempt_id, "result-" + attempt_id, "sha256:" + "1" * 64,
             "freeze-" + attempt_id, runtime.NOW))
        for name, filler in (("findings", "2"), ("logs", "3")):
            self.store._connection.execute(
                "INSERT INTO output_artifacts (runtime_attempt_id, "
                "output_name, artifact_id, media_type, bytes, content_digest, "
                "locator) VALUES (?, ?, ?, 'text/plain', 1, ?, ?)",
                (attempt_id, name, f"artifact-{name}-{attempt_id}",
                 "sha256:" + filler * 64, f"custody/{attempt_id}/{name}"))

    def prior_round(self):
        """ROUND ONE AS SETUP: reviewed, sent back, and the Job corrected.

        The result is the state the tested attempt is born into -- a retained
        frozen checkpoint, a `changes-requested` verdict against it, a
        correction-ready line, and a Job whose implementation stage is live on
        the correction episode that verdict earned.
        """
        writer = prepare_implementation(
            self.store, line_id=self.line["line_id"],
            attempt_id=self.inserted(PRIOR_WRITER, 1, runtime.WHO,
                                     "prior-writer-principal"),
            generation=1, worker_id="prior-worker", profile=self.profile)
        self.finished(PRIOR_WRITER)
        checkpoint = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.fence_port(runtime.WHO))
        attached = prepare_review(
            self.store, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=self.inserted(PRIOR_REVIEWER, 1, "baton.review",
                                     "prior-review-principal"),
            generation=1, reviewer_worker_id="prior-review-worker",
            profile=self.profile)
        self.finished(PRIOR_REVIEWER, review=True)
        verdict = record_verdict(
            self.store, attachment_id=attached["attachment_id"],
            disposition="changes-requested", profile=self.profile,
            port=self.fence_port("baton.review"))
        self.checkpoint_id = checkpoint["checkpoint_id"]
        # AND THE JOB'S OWN CORRECTION, which is what SELECTS this checkpoint:
        # `restart_abandoned_correction` refuses a recovery from a checkpoint
        # this Job's own handoff never chose.
        self.correction = episodes.advance_correction(
            self.jobs, self.store, job_id="job-a",
            line_id=self.line["line_id"],
            checkpoint_id=checkpoint["checkpoint_id"],
            verdict_id=verdict["verdict_id"])
        live = live_of(self.jobs, STAGE)
        self.assertEqual(live["episode"], 2)
        return live["attempt_id"]

    # -- the failed correction, on the real runtime interfaces ----------------

    def failed_correction(self):
        """THE TESTED FAILURE: the Job's correction attempt really runs and is
        really declared abandoned, and its resources are really settled."""
        attempt_id = self.prior_round()
        inputs = self.delivered_as(attempt_id, "offer-correction",
                                   generation=2)
        self.writer_id = grant_writer(
            self.store, line_id=self.line["line_id"], attempt_id=attempt_id,
            generation=2, worker_id="correction-worker", profile=self.profile,
            based_checkpoint_id=self.checkpoint_id)["writer_id"]
        adapter = self.custodian("runtime-correction")
        request_runtime_start(self.store, adapter, attempt_id=attempt_id,
                              inputs=inputs)
        self.assertEqual(self.lane_holders(), [attempt_id])
        self.fences_faithfully()
        settled = worker_manager.abandon_attempt(
            self.store, self.port, adapter, attempt_id=attempt_id,
            reason="the correction worker stopped answering",
            retention_policy_digest=RETENTION)
        self.assertEqual((settled["cleanup"]["cleanup"],
                          settled["cleanup"]["state"]),
                         ("retained", "absent"))
        self.assertEqual(self.lane_holders(), [])
        self.assertEqual(self.projection(),
                         {"phase": "block", "gate": "runtime-quiescence:2"})
        return attempt_id

    def recovered(self, attempt_id):
        """BOTH SUPPORTED RECOVERIES, in the order their receipts require."""
        self.discharge(attempt_id=attempt_id)
        self.restored = restore_abandoned_correction(
            self.store, attempt_id=attempt_id, generation=2,
            retention_policy_digest=RETENTION, profile=self.profile)
        return episodes.restart_abandoned_correction(
            self.jobs, self.store, job_id="job-a", attempt_id=attempt_id,
            generation=2)

    def attempting(self, stage_id=STAGE):
        """One stage row merged with the episode answering for it right now."""
        row = {one["stage_id"]: one for one in stage_rows(self.jobs)}[stage_id]
        return job_attempting(row, live_of(self.jobs, stage_id))

    def collecting(self, attempt_id):
        """A controlled adapter that answers the freeze it is collecting.

        Its collection is DERIVED from the frozen result this manager recorded --
        every artifact identity, digest and byte count read back out of the
        store -- so the intake compares what arrived against what was frozen
        rather than against numbers a fixture chose. The custody locator is the
        one thing a real engine would supply and a fake cannot.
        """
        answer = self.collected(attempt_id)

        class Collecting(
                runtime.ExplicitAbandonmentFencesBeforeItRemoves.Custodian):
            def collect(inner, operands):
                inner.order.append("collect")
                return answer

        return Collecting([])

    def collected(self, attempt_id):
        """WHAT A COLLECTION ANSWERS, derived from the recorded frozen result.

        Split out of `collecting` for the reason `sealed_document` is: the
        composed ending's own adapter must answer the same collection, and two
        spellings of one answer is how a fixture comes to agree with itself
        instead of with the store.
        """
        frozen = frozen_output_of(self.store, attempt_id)
        return {"result_id": frozen["result_id"],
                "artifacts": [{"artifact_id": one["artifact_id"],
                               "content_digest": one["content_digest"],
                               "bytes": one["bytes"],
                               "custody_locator":
                                   "file:///var/lib/baton/custody/"
                                   + one["artifact_id"]}
                              for one in frozen["artifacts"]]}

    # -- the successor's own supported ending ---------------------------------

    def ending_surface(self, attempt_id, written):
        """ONE adapter carrying THE WHOLE SURFACE an implementation ending types.

        Review 2026-09-26T00-26-46Z [P1]: the settlement below is not a journal
        row this module may write after a freeze and an intake -- it is the end
        of `review_driver.end_implementation`, which stops the runtime, observes
        the disposition, proves the line consumable, freezes, correlates the
        worker's envelope, takes custody, decides retention, publishes, freezes
        the checkpoint and authorizes cleanup. `_typed` proves every verb of
        that surface BEFORE the first stop, so one adapter has to carry all of
        them or the ending refuses for want of a capability rather than
        performing.

        WHICH VERBS ARE THIS MODULE'S AND WHAT EACH ONE STANDS ON. `seal`
        answers the SAME manifest `sealed_document` derives by reading the bytes
        on disk, and `collect` answers the artifacts the freeze actually
        recorded, read back out of the store -- so what the manager accepts and
        takes custody of still describes what is really there rather than
        numbers a fixture chose. `stop` answers a positive quiescent
        observation, which is what step one requires and what the accepted base
        adapter's `stop` does not answer. `retain` and `destroy` are the shape
        the accepted custody fixtures answer with, including the two provider
        lifecycle members every destroy owes. `prove_line_consumable` records
        the operands it was asked with and answers this case's own line.

        FIXTURE, AND LABELLED AS ONE: no container is stopped, nothing is
        removed from any host, and no engine is asked anything. What is real is
        every manager act between these answers, and the ORDER it performs them
        in, which `order` records so a case can measure it.
        """
        document, size, content, completion = self.sealed_document(
            attempt_id, written)
        case = self

        class Ending(runtime.ExplicitAbandonmentFencesBeforeItRemoves
                     .Custodian):

            def __init__(inner):
                super().__init__([])
                inner.consumed = []
                inner.collected_with = []
                inner.destroyed_with = []
                inner.retained = []
                inner.seals = []

            def stop(inner, operands):
                # AND THE OBSERVATION MOVES WITH IT, because step one ORDERS a
                # stop and then RECONCILES the exact runtime: an engine double
                # that answered `quiescent` to the stop and `running` to the
                # observation right after would be two engines. Measured, not
                # assumed -- `reconcile_runtime` refused
                # "execution_runtime is 'quiescent'; 'running' does not follow
                # it" until this moved.
                inner.stopped.append(dict(operands))
                inner.order.append("stop")
                inner.observation = {"state": "quiescent",
                                     "why": "the engine stopped it",
                                     "mounts": None}
                return {"state": "quiescent", "runtime_id": inner.runtime_id}

            def prove_line_consumable(inner, store, **operands):
                inner.order.append("consume")
                inner.consumed.append(dict(operands))
                return {"line_id": case.line["line_id"]}

            def seal(inner, operands):
                inner.order.append("seal")
                inner.seals.append(dict(operands))
                return document

            def collect(inner, operands):
                inner.order.append("collect")
                inner.collected_with.append(dict(operands))
                return case.collected(attempt_id)

            def retain(inner, operands):
                inner.order.append("retain")
                inner.retained.append(dict(operands))
                return True

            def destroy(inner, command):
                # AND WHAT IT LEAVES BEHIND IS GONE FROM THE ENGINE TOO, for
                # the same reason the stop moves the observation.
                inner.order.append("destroy")
                inner.destroyed_with.append(dict(command))
                inner.listing = []
                inner.observation = {"state": "absent",
                                     "why": "the engine removed it",
                                     "mounts": None}
                return {"runtime_id": command["runtime_id"],
                        "state": "absent",
                        "why": "the engine answered that this exact identity "
                               "does not exist",
                        "credentials": {"lifecycle_state": "not-delivered"},
                        "launch": {"lifecycle_state": "not-delivered"}}

        adapter = Ending()
        adapter.runtime_id = self.row(attempt_id)["runtime_id"]
        return adapter, size, content, completion

    def publishing(self):
        """The publication seam, RECORDING THE LINE STATE it was asked at.

        Modelled on the accepted driver suite's own seam, which records exactly
        this and for exactly this reason: step seven must run while the producer
        assignment is still live, and `writing` is what that looks like from the
        line. A `freezing` or later state would mean the checkpoint fence had
        already happened, which the driver's retained reproduction proves the
        Authority refuses.

        FIXTURE: this is not `integration.driver.retain_proposal` and it
        publishes nothing anywhere. It is the seam's shape, so the ending's own
        ORDER can be measured; nothing here is evidence about a candidate.
        """
        case = self

        class Publishing:

            def __init__(inner):
                inner.states = []
                inner.calls = []

            def publish(inner, **operands):
                inner.states.append(
                    line_of(case.store, case.line["line_id"])["state"])
                inner.calls.append(dict(operands))
                return {"proposal_id": "proposal-" + operands["attempt_id"],
                        "result_id": operands["result_id"]}

        return Publishing()

    def routes_fenced(self):
        """The authority's FENCED HANDOFF, modelled on `route_fenced`'s rules.

        `authority/core.py:1561`. The composed ending's routing is this act and
        not a pass: the checkpoint fence has already ended the assignment, so
        `pass_work` would refuse. What it does is change ONLY the route --
        leaving the phase, the gate and the generation exactly as the fence set
        them -- and it refuses unless the Work is at `block` holding this
        generation's quiescence gate on the route the original claim named. That
        ordering is the property the schedule below depends on, so those are the
        rules modelled here, plus the replay every authority act has.

        WHAT THIS FAKE DOES NOT MODEL, named rather than left to inference: the
        real act also proves, out of the authority's OWN journal, the committed
        cancellation record behind the named fence operation and the single
        original claim decision that authorized `from_route`. This session keeps
        no such journal -- its `cancel` is itself a fixture -- so those
        provenance checks are ABSENT here, and nothing in this module is
        evidence that a real authority would admit this handoff. What the cases
        measure is the ORDER this deployment performs, which is the half under
        test.
        """
        session = self.session
        session.routed = {}

        def route_fenced(operands):
            session.calls.append(("route_fenced", dict(operands)))
            held = session.routed.get(operands["operation_id"])
            if held is not None:
                return dict(held)
            expect = operands["expect"]
            gate = f"runtime-quiescence:{expect['generation']}"
            work = session._work
            if work["phase"] != "block" or work["gate"] != gate:
                raise ContractRefusal(
                    "refused", "precondition",
                    "fenced routing requires the original unclaimed "
                    "generation and runtime gate")
            if work["route"] != operands["from_route"]:
                raise ContractRefusal(
                    "refused", "precondition",
                    "the source route is not the unchanged route of the "
                    "original claim")
            answer = {"assignment": dict(expect),
                      "fence_operation_id": operands["fence_operation_id"],
                      "from_route": operands["from_route"],
                      "to_route": operands["to_route"],
                      "phase": work["phase"], "gate": work["gate"]}
            session._work = dict(work, route=operands["to_route"])
            session.routed[operands["operation_id"]] = answer
            return dict(answer)

        session.route_fenced = route_fenced
        return session

    def handed_off(self, answered, assignment, attempt_id, to_route):
        """W122060's routing, with EVERY OPERAND READ OFF A COMMITTED RECORD.

        The composed deployment derives these three the same way and this
        mirrors it rather than choosing any of them: the fence operation is the
        cancellation THIS ending's own checkpoint committed, read off the
        checkpoint; `from_route` is the one route this attempt's own committed
        claimed offer was authorized on -- exactly one, because a fenced handoff
        moves the Work off it; and the assignment is the ending's own.
        """
        fence = answered["checkpoint"]["fence"]["intent"]
        claimed = claimed_offers_for(self.store, attempt_id)
        self.assertEqual(len(claimed), 1)
        return self.session.route_fenced({
            "expect": dict(assignment),
            "operation_id": f"route-fenced:{attempt_id}:{to_route}",
            "fence_operation_id": fence["authority_operation_id"],
            "from_route": claimed[0]["work_route"], "to_route": to_route})

    def ran(self, attempt_id, inputs, runtime_id):
        """One real run to a positive quiescent observation and completion."""
        adapter = self.custodian(runtime_id)
        request_runtime_start(self.store, adapter, attempt_id=attempt_id,
                              inputs=inputs)
        adapter.observation = {"state": "quiescent", "why": "it finished",
                              "mounts": None}
        reconcile_runtime(self.store, adapter, attempt_id=attempt_id,
                          minted=runtime_id)
        runtime.observe(self.store, attempt_id=attempt_id,
                        axis="worker_disposition", value="completed")
        return adapter

    def test_the_gated_job_recovers_and_its_successor_is_accepted(self):
        """THE WHOLE COMPOSITION, measured at every step."""
        failed = self.failed_correction()
        episode = live_of(self.jobs, STAGE)["episode"]

        # BEFORE THE RECOVERY the Job's episode cannot be finished by anybody:
        # the attempt is gone and the episode is still live on it.
        self.assertEqual(live_of(self.jobs, STAGE)["attempt_id"], failed)
        self.assertIsNone(live_of(self.jobs, STAGE)["ended_state"])

        restarted = self.recovered(failed)

        # THE LINE CAME BACK TO THE SAME CHECKPOINT, and the old writer is out.
        line = line_of(self.store, self.line["line_id"])
        self.assertEqual(line["state"], "correction-ready")
        self.assertEqual(line["current_checkpoint_id"], self.checkpoint_id)
        self.assertEqual(writer_of(self.store, self.writer_id)["state"],
                         "revoked")
        self.assertEqual(self.restored["checkpoint_id"], self.checkpoint_id)
        # AND THE RESTORATION WAS AN ACTUAL CHECKOUT ACT, over this line's own
        # path and that checkpoint's own evidence -- not a row somebody set.
        [(repository, evidence)] = self.restore_calls
        self.assertEqual(repository, line["line_path"])
        self.assertEqual(evidence,
                         self.profile.held[self.profile.current_revision])

        # THE EPISODE IS ENDED BY THE RECOVERY AND NOTHING ELSE IS OPENED BY IT.
        self.assertEqual(restarted["ended_state"], EXCLUSION_ENDINGS[0])
        self.assertEqual(restarted["attempt_id"], failed)
        self.assertEqual(restarted["episode"], episode)
        self.assertEqual(restarted["checkpoint_id"], self.checkpoint_id)
        self.assertEqual(restarted["preparation_operation_id"],
                         self.restored["operation_id"])
        self.assertIsNone(live_of(self.jobs, STAGE))

        # AND THE ORDINARY SWEEP OPENS EXACTLY ONE SUCCESSOR, with fresh
        # identities it derives itself.
        sweep(self.jobs, FakeOperations(), now=runtime.NOW)
        successor = live_of(self.jobs, STAGE)
        self.assertEqual(successor["episode"], episode + 1)
        fresh = successor["attempt_id"]
        self.assertNotEqual(fresh, failed)

        # THE SUCCESSOR IS ADMITTED THE ORDINARY WAY, in the order a deployment
        # admits one: a new generation claimed through the offer boundary the
        # gate was blocking, then the line's writer granted from the checkpoint
        # the recovery restored -- and only then does it run.
        inputs = self.delivered_as(fresh, "offer-successor", generation=3)
        self.assertEqual(self.row(fresh)["assignment_generation"], 3)
        granted = grant_writer(
            self.store, line_id=self.line["line_id"], attempt_id=fresh,
            generation=3, worker_id="successor-worker", profile=self.profile,
            based_checkpoint_id=self.checkpoint_id)
        self.assertEqual(granted["state"], "active")
        self.assertNotEqual(granted["writer_id"], self.writer_id)
        self.assertEqual(line_of(self.store, self.line["line_id"])["state"],
                         "writing")
        adapter = self.ran(fresh, inputs, "runtime-successor")

        # THE WORKER ANSWERED FIRST, which is the order a deployment ends in:
        # the bytes exist and the container's own completion envelope is readable
        # BEFORE the obligation is registered, because the registered terminal
        # digest is the worker's claim and not this module's choice.
        written = self.generated(fresh)
        surface, size, content, completion = self.ending_surface(fresh, written)
        terminal = {"ending": "answered", "disposition": "completed",
                    "manifest_digest": completion}

        # THE JOB TAKES ON THE ENDING BEFORE ANY STEP THAT CAN REACH CLEANUP,
        # which is that record's own contract.
        live = {"work_ref": dict(self.VALID_WORK), "participant": runtime.WHO,
                "generation": 3}
        attempting = self.attempting()
        self.assertEqual(attempting["attempt_id"], fresh)
        intent = ending.register_ending(
            self.jobs, attempting, assignment=live, disposition="completed",
            terminal_manifest_digest=completion,
            retention_disposition="retain",
            retention_policy_digest=RETENTION)
        # AND THE OBLIGATION IS REALLY OWED FROM HERE, which is the reader the
        # premature settlement made lie.
        self.assertEqual(ending.pending_endings(self.jobs), [intent])

        # THE SUCCESSOR'S ENDING IS PERFORMED BY ITS OWN DRIVER, not composed
        # out of the two steps a settlement happens to name. Review
        # 2026-09-26T00-26-46Z [P1]: `settle_ending` records that an ending
        # FINISHED and certifies none of it, and its contract requires the
        # driver's evidence, the applicable gate discharge and the routing to
        # have succeeded first. So the freeze and the intake below are steps 3
        # and 5 of ten, performed by `end_implementation` along with the stop,
        # the disposition, the consumption proof, the correlation, the retention,
        # the publication, the checkpoint fence and the cleanup.
        publication = self.publishing()
        answered = end_implementation(
            self.store, self.port, surface, publication, attempt_id=fresh,
            disposition="completed", terminal=terminal,
            writer_id=granted["writer_id"], generation=3, profile=self.profile,
            retention_disposition="retain",
            retention_policy_digest=RETENTION, proposal=None)

        # THE ORDER IT ACTUALLY PERFORMED, against the module's own written-down
        # ruling rather than against my reading of it. The checkpoint and the
        # cleanup are the last two, and the publication was asked while the line
        # was still `writing` -- before the fence, which is the whole of step
        # seven's position.
        # THE ORDER IT ACTUALLY PERFORMED, measured from the engine double's
        # own record. Each verb is one of the ten steps the driver writes down:
        # `stop` is step one's quiescence, `consume` is W105982's line-readable
        # proof, `seal` is the freeze, `collect` is the intake, `retain` is the
        # retention decision and `destroy` is step nine's cleanup -- which is
        # LAST, after the checkpoint fence, and is the whole reason a settlement
        # written when the driver returns would still be premature.
        self.assertEqual(surface.order,
                         ["stop", "consume", "seal", "collect", "retain",
                          "destroy"])
        self.assertEqual(publication.states, ["writing"])
        self.assertEqual(publication.calls[0]["attempt_id"], fresh)

        # ITS RESULT IS REALLY ACCEPTED, over bytes really on disk, and the
        # artifact row is the STORE'S rather than my helper's local numbers.
        # MEASURED, NOT ASSUMED: I asserted `frozen` here and the axis rests at
        # `sealed`, because the intake this ending performed moves it on
        # (`intake.py:801`). `frozen` is where the runtime class's bare freeze
        # stops; a complete ending has taken custody as well.
        self.assertEqual(self.row(fresh)["output"], "sealed")
        kept = frozen_output_of(self.store, fresh)
        self.assertEqual(kept["result_id"], "result-" + fresh)
        self.assertEqual(answered["result_id"], kept["result_id"])
        self.assertEqual(answered["manifest_digest"], kept["manifest_digest"])
        [artifact] = kept["artifacts"]
        self.assertEqual(artifact["bytes"], len(GENERATED))
        self.assertEqual(artifact["content_digest"], content)
        self.assertEqual(artifact["bytes"], size)
        # ONE SUBMISSION FOR THE SUCCESSOR, on its own runtime.
        self.assertEqual(len(adapter.started), 1)
        self.assertEqual(self.row(fresh)["runtime_id"], "runtime-successor")
        # CUSTODY WAS TAKEN THROUGH THE REAL INTAKE, over the artifacts the
        # freeze actually recorded.
        receipt = worker_manager.intake_receipt_of(self.store, fresh)
        self.assertEqual(answered["receipt_digest"], receipt["receipt_digest"])
        self.assertEqual(receipt["result_id"], kept["result_id"])

        # THE ACTS THE PREMATURE SETTLEMENT LEFT OUTSTANDING ARE NOW DONE.
        # The reviewer's probe measured every one of these as unfinished while a
        # settlement already stood, so each is asserted here as a fact about the
        # records and not about what was passed in.
        row = self.row(fresh)
        self.assertEqual(row["cleanup"], "retained")
        self.assertEqual(row["execution_runtime"], "destroyed")
        self.assertEqual([one["runtime_id"]
                          for one in surface.destroyed_with],
                         ["runtime-successor"])
        self.assertEqual(self.lane_holders(), [])
        self.assertEqual(writer_of(self.store, granted["writer_id"])["state"],
                         "revoked")
        # THE NEW CHECKPOINT IS THIS ATTEMPT'S AND THE LINE IS AT IT, so the
        # successor's result is what the line now carries rather than the
        # failed round's restored checkpoint.
        line = line_of(self.store, self.line["line_id"])
        self.assertNotEqual(answered["checkpoint_id"], self.checkpoint_id)
        self.assertEqual(line["current_checkpoint_id"],
                         answered["checkpoint_id"])
        self.assertEqual(
            review_cycles.checkpoint_of(
                self.store, answered["checkpoint_id"])["writer_id"],
            granted["writer_id"])
        # AND THE FENCE ENDED GENERATION 3 AND GATED THE WORK, exactly as the
        # abandonment's own fence did for generation 2.
        self.assertIsNone(self.session.live_assignment)
        self.assertEqual(self.projection(),
                         {"phase": "block", "gate": "runtime-quiescence:3"})

        # THE ROUTING COMES NEXT AND THE GATE IS STILL HOLDING WHEN IT DOES,
        # which is the ordering W122060 settled: discharging first would return
        # the Work to `queued` on the route the FINISHED role is served on.
        self.routes_fenced()
        handoff = self.handed_off(answered, live, fresh, "baton.review")
        self.assertEqual(handoff["from_route"], runtime.ROUTE)
        self.assertEqual(handoff["to_route"], "baton.review")
        self.assertEqual((handoff["phase"], handoff["gate"]),
                         ("block", "runtime-quiescence:3"))
        self.assertEqual(self.session._work["route"], "baton.review")

        # AND ONLY THEN THE GATE THIS ENDING'S OWN FENCE INSTALLED, through the
        # supported manager act -- the same one stage 2's abandonment owed, now
        # owed by a SUCCESSFUL ending.
        self.assertIsNone(worker_manager.gate_discharge_of(self.store, fresh))
        discharge = worker_manager.discharge_quiescence_gate(
            self.store, self.port, attempt_id=fresh,
            retention_policy_digest=RETENTION)
        self.assertEqual(discharge["gate"], "runtime-quiescence:3")
        self.assertEqual(discharge["runtime_id"], "runtime-successor")
        # THE RECEIPT'S SHAPE IS THE ORDINARY ENDING'S, MEASURED. I asserted the
        # abandoned variant's `evidence` member and this one carries the
        # authority's answered `kind` instead; the positive absence it supplied
        # is asserted below, in the authority's own gate journal.
        self.assertEqual(discharge["kind"], "runtime-absent")
        self.assertEqual(discharge["phase"], "queued")
        # AND IT IS EARNED BEHIND THIS ENDING'S OWN CLEANUP, not any cleanup:
        # the operation it carries is the one `authorize_cleanup` committed.
        committed = worker_manager.cleanup_of(
            self.store, attempt_id=fresh, retention_policy_digest=RETENTION)
        self.assertEqual(discharge["cleanup_operation_id"],
                         committed["operation"]["operation_id"])
        self.assertEqual(self.projection(), {"phase": "queued", "gate": None})
        # THE ABSENCE EVIDENCE REACHED THE AUTHORITY'S GATE JOURNAL, naming this
        # successor's own runtime -- the second entry, beside the abandonment's.
        self.assertEqual(self.session.gate_evidence,
                         [{"kind": "runtime-absent",
                           "runtime": "runtime-correction"},
                          {"kind": "runtime-absent",
                           "runtime": "runtime-successor"}])
        self.assertEqual(worker_manager.gate_discharge_of(self.store, fresh),
                         discharge)
        # ASKING AGAIN IS THE SAME ACT (§4.2).
        self.assertEqual(worker_manager.discharge_quiescence_gate(
            self.store, self.port, attempt_id=fresh,
            retention_policy_digest=RETENTION), discharge)
        self.assertEqual(len(self.session.gate_evidence), 2)

        # AND NOW THE JOB MAY OBSERVE THAT THE ENDING FINISHED: the settlement
        # names the successor's own result, the manifest the manager froze, the
        # intake receipt that took custody of it, this attempt's new checkpoint
        # and the gate the discharge cleared -- every member read back out of a
        # committed record rather than chosen here.
        ending.settle_ending(
            self.jobs, attempting, assignment=live,
            evidence={"result_id": answered["result_id"],
                      "manifest_digest": answered["manifest_digest"],
                      "receipt_digest": answered["receipt_digest"],
                      "checkpoint_id": answered["checkpoint_id"],
                      "gate_discharge": discharge["gate"]})
        settled = ending.settlement_of(self.jobs, STAGE, episode + 1)
        self.assertEqual(settled["attempt_id"], fresh)
        self.assertEqual(settled["evidence"],
                         {"result_id": kept["result_id"],
                          "manifest_digest": kept["manifest_digest"],
                          "receipt_digest": receipt["receipt_digest"],
                          "checkpoint_id": answered["checkpoint_id"],
                          "gate_discharge": "runtime-quiescence:3"})
        self.assertEqual(settled["assignment"]["generation"], 3)
        # AND THE JOB'S OWN COMPLETION VIEW AGREES: this episode's obligation is
        # held with its settlement, and NOTHING is pending. That reader answered
        # the same empty list when the acts above were outstanding, which is
        # what made the premature settlement invalid evidence; it is true now.
        held = ending.ending_of(self.jobs, STAGE, episode + 1)
        self.assertEqual(held["intent"], intent)
        self.assertEqual(held["settlement"], settled)
        self.assertEqual(ending.pending_endings(self.jobs), [])
        # AND NOTHING OF THIS IS CREDITED TO THE FAILED EPISODE, which holds no
        # ending of its own at all.
        self.assertIsNone(ending.settlement_of(self.jobs, STAGE, episode))
        self.assertIsNone(ending.intent_of(self.jobs, STAGE, episode))

        # THE FAILED EPISODE STAYS AUDITABLE AND IS CREDITED WITH NOTHING.
        history = episodes.episodes_of(self.jobs, STAGE)
        self.assertEqual([one["ended_state"] for one in history],
                         [CORRECTION_ENDINGS[0], EXCLUSION_ENDINGS[0], None])
        self.assertEqual(history[1]["attempt_id"], failed)
        self.assertIsNone(frozen_output_of(self.store, failed))
        self.assertEqual(self.row(failed)["cleanup"], "retained")
        self.assertEqual(self.row(failed)["worker_disposition"], "none")

    def successor_ran(self, runtime_id="runtime-successor"):
        """The same prefix the case above measures step by step, composed once.

        Nothing here is this module's own shortcut: every call is one the
        successful case makes and asserts against. It exists so the negative
        below can reach the ending's own correlation boundary without restating
        a schedule that is already measured.
        """
        failed = self.failed_correction()
        self.recovered(failed)
        sweep(self.jobs, FakeOperations(), now=runtime.NOW)
        fresh = live_of(self.jobs, STAGE)["attempt_id"]
        inputs = self.delivered_as(fresh, "offer-successor", generation=3)
        granted = grant_writer(
            self.store, line_id=self.line["line_id"], attempt_id=fresh,
            generation=3, worker_id="successor-worker", profile=self.profile,
            based_checkpoint_id=self.checkpoint_id)
        self.ran(fresh, inputs, runtime_id)
        written = self.generated(fresh)
        surface, _size, _content, completion = self.ending_surface(fresh,
                                                                   written)
        return {"attempt_id": fresh, "writer_id": granted["writer_id"],
                "surface": surface, "completion": completion}

    def test_a_terminal_naming_another_envelope_stops_the_ending(self):
        """THE CORRELATION IS MEASURED, at the ending's own step four.

        Review 2026-09-26T00-26-46Z asks for a measured output identity at the
        terminal correlation, and a comparison of two constants would agree with
        itself. So the worker's claimed completion envelope is derived from the
        bytes it wrote, and this case changes ONLY that claim: the same run, the
        same bytes, the same sealed result, and a terminal naming a different
        envelope.

        AND WHAT THE REFUSAL LEAVES IS THE POINT. The freeze is step three and
        the correlation is step four, so the result is sealed and NOTHING after
        it happened -- no custody, no retention, no publication, no checkpoint
        and no cleanup. A settlement written here would close an obligation
        whose runtime is still standing.
        """
        held = self.successor_ran()
        fresh = held["attempt_id"]
        surface = held["surface"]
        other = "sha256:" + "4" * 64
        self.assertNotEqual(other, held["completion"])
        with self.assertRaises(ContractRefusal) as caught:
            end_implementation(
                self.store, self.port, surface, self.publishing(),
                attempt_id=fresh, disposition="completed",
                terminal={"ending": "answered", "disposition": "completed",
                          "manifest_digest": other},
                writer_id=held["writer_id"], generation=3,
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest=RETENTION, proposal=None)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "operation-collision"))
        self.assertIn("is not evidence about the output this manager froze",
                      caught.exception.message)
        # BOTH DIGESTS ARE NAMED, so the refusal says which claim disagreed with
        # which validation. Compared on a PREFIX because the boundary's own
        # `name_value` elides long identities -- measured, not assumed: asserting
        # the whole digest failed against the elided text.
        self.assertIn(other[:40], caught.exception.message)
        self.assertIn(held["completion"][:40], caught.exception.message)

        # THE ENDING STOPPED AT FOUR, measured from the engine double's record
        # and from the durable axes rather than from the refusal's text.
        self.assertEqual(surface.order, ["stop", "consume", "seal"])
        self.assertEqual(self.row(fresh)["output"], "frozen")
        self.assertIsNone(worker_manager.intake_receipt_of(self.store, fresh))
        self.assertEqual(self.row(fresh)["execution_runtime"], "quiescent")
        # `pending` IS THE UNSETTLED VALUE, measured -- I asserted absence and
        # the axis carries its own initial word for "nobody has ended this yet".
        self.assertEqual(self.row(fresh)["cleanup"], "pending")
        self.assertEqual(self.lane_holders(), [fresh])
        self.assertEqual(writer_of(self.store, held["writer_id"])["state"],
                         "active")
        self.assertEqual(line_of(self.store, self.line["line_id"])["state"],
                         "writing")
        self.assertEqual(self.projection(), {"phase": "queued", "gate": None})

    def test_no_episode_is_replaced_before_the_recovery_is_committed(self):
        """THE NEGATIVES, in the order the receipts are earned.

        The episode replacement is authorized by committed recoveries and never
        by the failure itself -- otherwise a Job could be handed a successor onto
        a checkout nobody restored and a generation still held at the authority.
        """
        failed = self.failed_correction()

        # NOTHING IS RESTORED YET, so the replacement refuses.
        with self.assertRaises(ContractRefusal) as caught:
            episodes.restart_abandoned_correction(
                self.jobs, self.store, job_id="job-a", attempt_id=failed,
                generation=2)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("has no completed abandoned-correction recovery",
                      caught.exception.message)

        # AND THE RESTORATION ITSELF REFUSES WHILE THE GATE IS HELD.
        with self.assertRaises(ContractRefusal) as caught:
            restore_abandoned_correction(
                self.store, attempt_id=failed, generation=2,
                retention_policy_digest=RETENTION, profile=self.profile)
        self.assertIn("has not discharged its runtime-quiescence gate",
                      caught.exception.message)

        # THE EPISODE IS STILL LIVE ON THE ABANDONED ATTEMPT, and the line is
        # still held by its writer: nothing was half-recovered.
        self.assertEqual(live_of(self.jobs, STAGE)["attempt_id"], failed)
        self.assertEqual(line_of(self.store, self.line["line_id"])["state"],
                         "writing")
        self.assertEqual(writer_of(self.store, self.writer_id)["state"],
                         "active")

        # THEN THE RECOVERIES IN ORDER, and the same replacement is answered.
        self.assertEqual(self.recovered(failed)["attempt_id"], failed)
        self.assertIsNone(live_of(self.jobs, STAGE))


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases defined in THIS module.

    `DriverCase` carries its own accepted cases; re-running them here would
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
