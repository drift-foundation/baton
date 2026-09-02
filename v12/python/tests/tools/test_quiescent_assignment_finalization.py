"""W61984 -- finalizing a v12 assignment whose runtime is ALREADY QUIESCENT.

`work/records/2026/09/finding-v12-quiescent-assignment-finalization/`.

THE INTERVAL THIS COVERS. W52821 run5b left the manager holding four durable
facts at once: worker disposition `unable`, the exact execution runtime
positively observed `quiescent`, frozen output in custody, and the assignment
STILL LIVE at the authority. `intake.authorize_cleanup` refused -- correctly --
because the fixed assignment was live, and nothing between "do not pass an
unverified candidate" and "cleanup requires the assignment to be over" could
end it. The claim slot stayed held for an execution that had already stopped.

WHAT IS PINNED HERE, and each of these is a separate case below:

  * an operator-triggered finalization ends the exact live assignment and
    frees the participant's claim slot, deriving the four-part assignment, the
    exact runtime identity and the recorded terminal disposition from this
    manager's own row rather than from any caller operand;
  * every recorded terminal worker disposition reaches it and `none` does not;
  * it makes NO agent call and NO runtime-stop call -- it takes neither
    capability, so it cannot -- and decides nothing about output, custody,
    retention, verification, review, approval, integration or cleanup;
  * the Work stays behind `runtime-quiescence:<generation>`, because a
    quiescent runtime is not an absent one;
  * an exact retry replays, a changed operand collides, and a crash between
    the committed decision and the fence reissues the SAME authority act;
  * the journal is a RECEIVING trust domain, so every call after the one that
    committed fences from bytes read back out of SQLite: a replayed
    `attempt.finalize-intent` that has been corrupted or substituted is proved
    as it crosses back in, and the refusal arrives before any `port.cancel`;
  * a wrong identity or a non-quiescent state refuses BEFORE the authority is
    asked and before anything durable is written;
  * `request_cancellation` is unchanged for a RUNNING attempt -- fence, then
    the agent, then the runtime; and
  * the dogfood deployment exposes exactly one explicit mode for this, and an
    ordinary run's failed verification never reaches it.

NO DAEMON AND NO CREDENTIAL. Everything here runs against the real control
store, the real authority port and this suite's own fake authority session --
which is what makes it worth running on every change rather than only where
Docker is reachable.
"""

import inspect
import json
import os
import sqlite3
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PYTHON = os.path.dirname(os.path.dirname(_HERE))
# BOTH ROOTS, AND THE PACKAGE'S OWN FIRST. `tests` and `tools` are reached from
# `v12/python`; `baton_v12` lives under `src`, and naming it explicitly is what
# makes this file prove THIS tree rather than whatever copy happens to be
# installed in the interpreter that ran it.
for _root in (_PYTHON, os.path.join(_PYTHON, "src")):
    if _root not in sys.path:
        sys.path.insert(0, _root)

from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import (activate_assignment,     # noqa: E402
                                      AuthorityPort,
                                      ControlStore,
                                      finalize_quiescent_assignment,
                                      observe, request_cancellation,
                                      request_runtime_start,
                                      satisfies_runtime_quiescence_gate)
from baton_v12.worker_manager import attempts                   # noqa: E402
from baton_v12.worker_manager.schema import DISPOSITIONS        # noqa: E402

from tests.manager.test_attempts import (ATTEMPT, Adapter,      # noqa: E402
                                         Agent, AttemptCase)
from tests.manager.test_offers import (NOW, UUID, WHO,          # noqa: E402
                                       WORK, fake_claim_signature)
from tools import dogfood_operator                              # noqa: E402

# THE MANAGER'S OWN JOURNAL KIND for this decision, named once. A case that
# spelled it twice would agree with itself until one of the two was edited.
KIND = "attempt.finalize-quiescent"

REASON = ("the worker answered and the exact runtime is quiescent; the "
          "operator is ending the assignment")


class FinalizationCase(AttemptCase):
    """An attempt in exactly the state run5b was in when cleanup refused."""

    def quiescent(self, disposition="unable", attempt_id=ATTEMPT):
        """A started attempt whose worker ANSWERED and whose runtime stopped.

        The two observations are made in the order the world makes them: the
        runtime is seen to have finished, and the worker's terminal answer is
        recorded. Neither is this operation's to perform -- it reads both.
        """
        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter, attempt_id=attempt_id)
        observe(self.store, attempt_id=attempt_id, axis="execution_runtime",
                value="quiescent")
        observe(self.store, attempt_id=attempt_id, axis="worker_disposition",
                value=disposition)
        return attempt_id

    def running(self, value="running", attempt_id=ATTEMPT):
        """A started attempt whose execution runtime is NOT quiescent."""
        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter, attempt_id=attempt_id)
        if value != "running":
            observe(self.store, attempt_id=attempt_id,
                    axis="execution_runtime", value=value)
        observe(self.store, attempt_id=attempt_id, axis="worker_disposition",
                value="unable")
        return attempt_id

    def finalize(self, attempt_id=ATTEMPT, reason=REASON, port=None):
        return finalize_quiescent_assignment(
            self.store, self.port if port is None else port,
            attempt_id=attempt_id, reason=reason)

    # -- what the world can be asked, without reaching into a derivation ------

    def journalled(self):
        """Every journal row this decision wrote, read from a second handle.

        BY KIND rather than by a derived identity: a case that recomputed the
        operation id would be asserting the derivation against itself.
        """
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            return [{key: row[key] for key in row.keys()}
                    for row in beside.execute(
                        "SELECT * FROM operations WHERE kind = ?",
                        (KIND,)).fetchall()]
        finally:
            beside.close()

    def fences(self):
        """Every authority act this session was asked to perform."""
        return [operands for name, operands in self.session.calls
                if name == "cancel"]

    def axes(self, attempt_id=ATTEMPT):
        """The lifecycle axes finalization must not touch."""
        row = self.row(attempt_id)
        return {axis: row[axis] for axis in
                ("output", "proposal", "verification", "technical_review",
                 "approval", "integration", "cleanup", "consent_runtime",
                 "execution_runtime", "worker_disposition")}

    def restarted(self, incarnation="manager-2"):
        """A NEW manager over the SAME control store -- the restart itself."""
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation=incarnation,
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        return self.store

    def never(self):
        """The ordinary capability builder, which an explicit ending must not
        reach. A lambda that raised would be a promise; this is a fixture."""
        def refuse(given):                                 # pragma: no cover
            raise AssertionError("the ordinary capabilities were built for an "
                                 "explicit finalization")
        return refuse


class TheQuiescentAssignmentIsEndedAndNothingElseIs(FinalizationCase):
    """The normal case, and the whole of what it is allowed to do."""

    def test_the_exact_live_assignment_is_fenced_from_the_managers_own_row(
            self):
        self.quiescent()

        answer = self.finalize()

        intent = answer["intent"]
        self.assertEqual(intent["attempt_id"], ATTEMPT)
        self.assertEqual(intent["assignment"], self.expect())
        self.assertEqual(intent["runtime_id"], "runtime-1")
        self.assertEqual(intent["decision"], "finalized")
        self.assertEqual(intent["worker_disposition"], "unable")
        self.assertEqual(intent["reason"], REASON)
        self.assertIs(answer["fenced"]["fenced"], True)
        self.assertEqual(answer["fenced"]["assignment"], self.expect())

    def test_the_authority_is_asked_exactly_once_under_its_own_identity(self):
        """§4.2: success at one boundary does not imply success at the other,
        so the fence carries an identity that is nobody else's."""
        self.quiescent()

        answer = self.finalize()

        self.assertEqual(len(self.fences()), 1)
        asked = self.fences()[0]
        self.assertEqual(asked["expect"], self.expect())
        self.assertEqual(asked["reason"], REASON)
        self.assertEqual(asked["operation_id"],
                         answer["intent"]["authority_operation_id"])
        self.assertTrue(asked["operation_id"].startswith(
            "authority.finalize-quiescent:"), asked["operation_id"])

    def test_the_authority_identity_is_not_a_cancellations_or_an_abandonments(
            self):
        """A finalization must not be able to replay either of the two endings
        that already exist, and neither may replay it."""
        self.quiescent()

        asked = self.finalize()["intent"]["authority_operation_id"]

        self.assertNotIn("attempt.cancel", asked)
        self.assertNotIn("abandon", asked)
        self.assertEqual(self.journalled()[0]["kind"], KIND)

    def test_it_takes_no_agent_and_no_runtime_capability(self):
        """THE PROOF IS THE SIGNATURE, not a promise in a docstring. An
        operation handed neither boundary cannot call either one."""
        taken = list(inspect.signature(
            finalize_quiescent_assignment).parameters)

        self.assertEqual(taken, ["store", "port", "attempt_id", "reason"])

    def test_no_runtime_is_stopped_and_no_agent_is_asked(self):
        self.quiescent()
        agent = Agent()
        # WHAT THE SETUP ALREADY ASKED THE ENGINE, snapshotted rather than
        # assumed empty: `request_runtime_start` legitimately observes the
        # runtime it just started, so the claim here is that finalization adds
        # NOTHING to that history -- not that the history is empty.
        before = list(self.adapter.observed)

        self.finalize()

        self.assertEqual(self.adapter.stopped, [])
        self.assertEqual(self.adapter.observed, before)
        self.assertEqual(agent.cancelled, [])
        # AND THE AXIS IS NOT RE-ANNOUNCED EITHER. `request_cancellation`
        # records `cancel-requested` because it is about to order a stop; this
        # orders nothing, so the recorded observation stays what was observed.
        self.assertEqual(self.row()["execution_runtime"], "quiescent")

    def test_no_output_custody_or_lifecycle_axis_moves(self):
        """Freeing the claim slot is not accepting the proposal. Nothing here
        decides whether the retained output is trustworthy, importable or
        disposable, and the axes that would say so are untouched."""
        self.quiescent()
        before = self.axes()

        self.finalize()

        self.assertEqual(self.axes(), before)
        self.assertEqual(before["cleanup"], "pending")
        self.assertEqual(before["output"], "open")

    def test_the_work_stays_behind_the_runtime_quiescence_gate(self):
        """The assignment ends and the WORK does not become claimable: a
        quiescent runtime still exists, and only positive absence satisfies
        the gate the authority installs."""
        self.quiescent()

        fenced = self.finalize()["fenced"]

        self.assertEqual(fenced["phase"], "block")
        self.assertEqual(fenced["gate"], "runtime-quiescence:1")
        self.assertIs(satisfies_runtime_quiescence_gate("agent-quiescent"),
                      False)
        # AND THE RUNTIME IS STILL THERE TO BE PROVED ABSENT LATER.
        self.assertEqual(self.row()["runtime_id"], "runtime-1")
        self.assertEqual(self.row()["execution_runtime"], "quiescent")


class EveryRecordedTerminalDispositionReachesIt(FinalizationCase):
    """Approver ruling 2026-09-01 item 3, and the one answer it excludes."""

    def test_all_four_terminal_answers_are_finalizable(self):
        for disposition in DISPOSITIONS:
            with self.subTest(disposition=disposition):
                # A FRESH FIXTURE PER ANSWER. One attempt takes one terminal
                # answer and the runtime lane admits one execution per Work
                # and generation, so these cannot share a store.
                self.doCleanups()
                self.setUp()
                self.quiescent(disposition=disposition)

                answer = self.finalize()

                self.assertEqual(answer["intent"]["worker_disposition"],
                                 disposition)
                self.assertIs(answer["fenced"]["fenced"], True)

    def test_the_four_answers_are_the_schemas_own_and_not_a_second_list(self):
        self.assertEqual(DISPOSITIONS,
                         ("completed", "unable", "plan-rejected", "cancelled"))

    def test_a_worker_that_has_not_answered_refuses_before_the_authority(self):
        """`none` is not a terminal alternative. An attempt whose worker never
        answered has an ending of its own -- W44716's -- and relabelling it
        here would end an assignment whose worker may still be executing."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT)
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="quiescent")

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize()

        self.assertEqual(caught.exception.code, "precondition")
        self.assertIn("has not", caught.exception.message)
        self.assertEqual(self.fences(), [])
        self.assertEqual(self.journalled(), [])


class OnlyAPositivelyQuiescentRuntimeReachesIt(FinalizationCase):
    """The state gate, and where in the order it is applied."""

    def test_every_other_execution_state_refuses(self):
        for value in ("running", "cancel-requested", "stopping", "uncertain",
                      "destroyed"):
            with self.subTest(execution_runtime=value):
                self.doCleanups()
                self.setUp()
                self.running(value=value)

                with self.assertRaises(ContractRefusal) as caught:
                    self.finalize()

                self.assertIn("quiescent", caught.exception.message)
                self.assertEqual(self.fences(), [],
                                 "the authority was asked about a runtime "
                                 "that is not quiescent")
                self.assertEqual(self.journalled(), [],
                                 "a refused decision was journalled anyway")

    def test_the_refusal_leaves_every_lifecycle_axis_where_it_was(self):
        self.running(value="uncertain")
        before = self.axes()

        with self.assertRaises(ContractRefusal):
            self.finalize()

        self.assertEqual(self.axes(), before)

    def test_an_attempt_with_no_attached_runtime_has_nothing_to_name(self):
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition",
                value="unable")

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize()

        self.assertIn("no attached runtime", caught.exception.message)
        self.assertEqual(self.fences(), [])
        self.assertEqual(self.journalled(), [])

    def test_an_unactivated_attempt_has_no_generation_to_end(self):
        self.recorded()

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize()

        self.assertIn("no fixed assignment", caught.exception.message)
        self.assertEqual(self.fences(), [])

    def test_an_attempt_this_manager_never_recorded_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.finalize(attempt_id="attempt-nobody-recorded")

        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(self.fences(), [])


class TheWrongIdentityNeverReachesTheAuthority(FinalizationCase):
    """The binding, and the two ways an identity can be wrong."""

    def test_a_session_for_somebody_else_may_not_end_this_assignment(self):
        self.quiescent()
        self.session.participant = "baton.someone"
        other = AuthorityPort(self.session, fake_claim_signature)

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize(port=other)

        self.assertEqual(caught.exception.code, "capability")
        self.assertEqual(self.fences(), [])
        self.assertEqual(self.journalled(), [])

    def test_a_fence_that_ended_another_generation_is_not_this_ending(self):
        """The authority may report a well-shaped fence for a different live
        assignment; it is not evidence that THIS generation ended."""
        self.quiescent()
        self.session.fence_answer["assignment"] = self.expect(generation=2)

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize()

        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        # THE DECISION IS DURABLE AND THE FENCE IS NOT ACCEPTED. The record is
        # committed before the authority is asked precisely so a resumed call
        # reissues one act rather than forming a second decision -- so the row
        # exists, and nothing read it as evidence the assignment ended.
        self.assertEqual(len(self.journalled()), 1)

    def test_a_blank_reason_is_a_decision_nobody_made(self):
        self.quiescent()

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize(reason="   ")

        self.assertIn("blank", caught.exception.message)
        self.assertEqual(self.fences(), [])
        self.assertEqual(self.journalled(), [])

    def test_an_unbounded_reason_is_not_a_durable_sentence(self):
        self.quiescent()

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize(reason="x" * 4000)

        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "limit"))
        self.assertEqual(self.journalled(), [])

    def test_an_unstorable_reason_is_refused_at_the_boundary(self):
        self.quiescent()

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize(reason="a reason\ud800")

        self.assertIn("a finalization reason", caught.exception.message)
        self.assertEqual(self.journalled(), [])


class ItIsEffectivelyOnceAcrossRetriesAndRestarts(FinalizationCase):
    """The idempotence half: replay, collision, crash and cold start."""

    def test_an_exact_retry_replays_the_first_decision(self):
        self.quiescent()

        first = self.finalize()
        second = self.finalize()

        self.assertEqual(first["intent"], second["intent"])
        self.assertEqual(len(self.journalled()), 1,
                         "an exact retry recorded a second decision")

    def test_a_retry_reissues_the_SAME_authority_act(self):
        """A crash or restart reissues one authority act rather than starting
        a second one; the authority is effectively-once by that identity."""
        self.quiescent()

        self.finalize()
        self.finalize()

        asked = self.fences()
        self.assertEqual(len(asked), 2)
        self.assertEqual(asked[0], asked[1])

    def test_a_changed_reason_collides_instead_of_deciding_twice(self):
        self.quiescent()
        self.finalize()

        with self.assertRaises(ContractRefusal) as caught:
            self.finalize(reason="a different account of the same attempt")

        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual(len(self.journalled()), 1)
        # AND THE COLLISION IS DECIDED BEFORE THE AUTHORITY IS ASKED.
        self.assertEqual(len(self.fences()), 1)

    def test_a_crash_before_the_fence_resumes_from_the_committed_decision(
            self):
        """The decision is committed BEFORE the authority is asked, so a fault
        at the fence leaves a record naming the one act still owed."""
        self.quiescent()
        self.session.fence_answer = RuntimeError("the authority is away")

        with self.assertRaises(RuntimeError):
            self.finalize()

        self.assertEqual(len(self.journalled()), 1)
        self.session.fence_answer = {
            "cause": "cancelled", "assignment": self.expect(),
            "phase": "block", "gate": "runtime-quiescence:1", "fenced": True}

        resumed = self.finalize()

        self.assertIs(resumed["fenced"]["fenced"], True)
        self.assertEqual(len(self.journalled()), 1)
        self.assertEqual(self.fences()[0]["operation_id"],
                         self.fences()[1]["operation_id"])

    def test_a_restarted_manager_names_the_act_it_already_performed(self):
        self.quiescent()
        first = self.finalize()

        resumed = finalize_quiescent_assignment(
            self.restarted(), self.port, attempt_id=ATTEMPT, reason=REASON)

        self.assertEqual(first["intent"], resumed["intent"])
        self.assertEqual(len(self.journalled()), 1)
        self.assertEqual(self.fences()[0]["operation_id"],
                         self.fences()[1]["operation_id"])

    def test_a_restarted_manager_with_a_different_account_collides(self):
        self.quiescent()
        self.finalize()

        with self.assertRaises(ContractRefusal) as caught:
            finalize_quiescent_assignment(self.restarted(), self.port,
                                          attempt_id=ATTEMPT,
                                          reason="somebody else's sentence")

        self.assertEqual(caught.exception.code, "operation-collision")


class AReplayedDecisionIsProvedBeforeTheAuthorityIsAsked(FinalizationCase):
    """W61984 review [P1]: the journal is a RECEIVING trust domain.

    Everything above drives the call that COMMITS, where the record the fence
    is issued from is a document this build composed one line earlier. Every
    call after it -- an exact retry, a resumed crash, a restarted manager --
    fences from bytes `store.replay` read back out of SQLite instead, and
    `replay` compares the operation's kind and signature rather than its
    RESULT. So a durable surface that changed under this manager reaches the
    fence with nothing between it and the authority except
    `attempts.adopt_finalization_record` and the member comparison that follows
    it.

    Each case here rewrites the committed `attempt.finalize-intent` behind this
    build's back and requires the refusal to arrive with NO further authority
    act: the fence count is taken before the retry and required unchanged
    after it, which is what "before any `port.cancel`" means when the answer
    is a refusal rather than an ordering.
    """

    def committed_but_not_fenced(self):
        """The exact state a crash between the two boundaries leaves.

        The fence FAULTS rather than refuses, so the manager's own decision is
        committed, the assignment is still live, and the next call is the
        resumed one -- the only path on which a replayed record authorizes an
        authority act.
        """
        self.quiescent()
        self.session.fence_answer = RuntimeError("the authority is away")
        with self.assertRaises(RuntimeError):
            self.finalize()
        self.assertEqual(len(self.journalled()), 1)
        self.session.fence_answer = {
            "cause": "cancelled", "assignment": self.expect(),
            "phase": "block", "gate": "runtime-quiescence:1", "fenced": True}
        return json.loads(self.journalled()[0]["result"])

    def rewrite(self, result):
        """Other bytes under the SAME identity, kind and signature.

        Through a second handle, because what is being modelled is a durable
        surface that changed rather than an operand somebody passed. The
        signature column is left alone deliberately: a changed signature is
        already an operation collision, and the question here is what happens
        when only the RESULT differs.
        """
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("UPDATE operations SET result = ? WHERE kind = ?",
                           (json.dumps(result), KIND))
        finally:
            beside.close()

    def resuming(self):
        """What the resumed call did, and what it cost the authority."""
        before = len(self.fences())
        with self.assertRaises(ContractRefusal) as caught:
            self.finalize()
        self.assertEqual(len(self.fences()), before,
                         "a replayed record reached the authority")
        self.assertEqual(len(self.journalled()), 1)
        return caught.exception

    def test_a_replayed_record_missing_a_member_is_not_an_authorization(self):
        """The SHAPE half, at the owner the crossing has: a record short of a
        member its contract names is not a decision this manager made."""
        record = self.committed_but_not_fenced()
        self.rewrite({member: value for member, value in record.items()
                      if member != "runtime_id"})

        refusal = self.resuming()

        self.assertIn("a committed finalization record", refusal.message)
        self.assertEqual(refusal.category, "integrity")
        self.assertEqual(refusal.code, "schema")

    def test_a_replayed_record_carrying_an_unnamed_member_is_refused(self):
        """And closed the other way. An extra member means either a build this
        one was not written against or a document that is not this one, and
        ignoring it silently picks the happier reading."""
        record = self.committed_but_not_fenced()
        self.rewrite(dict(record, settled_by="somebody"))

        refusal = self.resuming()

        self.assertIn("a committed finalization record", refusal.message)
        self.assertEqual(refusal.code, "schema")

    def test_a_substituted_record_naming_another_runtime_ends_nothing(self):
        """The SUBSTITUTION half. A well-formed `attempt.finalize-intent` that
        names another container passes the shape rule and is still not the
        authorization for THIS ending."""
        record = self.committed_but_not_fenced()
        self.rewrite(dict(record, runtime_id="runtime-2"))

        refusal = self.resuming()

        self.assertIn("runtime_id", refusal.message)
        self.assertEqual(refusal.category, "integrity")
        self.assertEqual(refusal.code, "schema")

    def test_a_substituted_record_carrying_another_sentence_ends_nothing(self):
        """The reason rides the SIGNATURE, so a rewritten one is not a second
        decision -- it is a record that no longer describes the act it is being
        asked to authorize."""
        record = self.committed_but_not_fenced()
        self.rewrite(dict(record, reason="somebody else's account"))

        refusal = self.resuming()

        self.assertIn("reason", refusal.message)
        self.assertEqual(refusal.code, "schema")

    def test_a_substituted_record_naming_another_authority_act_ends_nothing(
            self):
        """The member the fence is literally issued with. A rewritten authority
        operation id would make the resumed call spend an identity the decision
        never named."""
        record = self.committed_but_not_fenced()
        self.rewrite(dict(record,
                          authority_operation_id="authority.finalize-"
                                                 "quiescent:somebody-elses"))

        refusal = self.resuming()

        self.assertIn("authority_operation_id", refusal.message)
        self.assertEqual(refusal.code, "schema")

    def test_an_untouched_replay_still_resumes(self):
        """The control, so the cases above are not passing because the resumed
        path refuses everything. The same fixture, rewritten with the bytes it
        already held, fences exactly once more."""
        record = self.committed_but_not_fenced()
        self.rewrite(record)
        before = len(self.fences())

        resumed = self.finalize()

        self.assertIs(resumed["fenced"]["fenced"], True)
        self.assertEqual(len(self.fences()), before + 1)
        self.assertEqual(len(self.journalled()), 1)

    def test_the_crossing_has_one_owner_and_it_is_not_the_caller(self):
        """The entry the review named: the store's answer is owned as it
        enters, at a site of its own, and the operation reads its members
        afterwards rather than proving them twice."""
        taken = list(inspect.signature(
            attempts.adopt_finalization_record).parameters)

        self.assertEqual(taken, ["record"])
        with self.assertRaises(ContractRefusal) as caught:
            attempts.adopt_finalization_record(7)
        self.assertIn("a committed finalization record",
                      caught.exception.message)


class TheRunningCancellationIsUnchanged(FinalizationCase):
    """The existing operation keeps its contract, which is why this is a NEW
    one rather than a weakening of that one."""

    def test_a_running_attempt_still_fences_then_asks_then_stops(self):
        order = []
        self.running()
        agent = Agent()
        agent.cancel = lambda operands: order.append("agent")
        self.adapter.stop = lambda operands: order.append("runtime")

        request_cancellation(self.store, self.port, agent, self.adapter,
                             attempt_id=ATTEMPT)

        self.assertEqual(order, ["agent", "runtime"])
        self.assertEqual(len(self.fences()), 1)

    def test_cancellation_still_takes_both_boundaries(self):
        taken = list(inspect.signature(request_cancellation).parameters)

        self.assertEqual(taken, ["store", "port", "agent", "adapter",
                                 "attempt_id", "reason"])


class TheDeploymentExposesOneExplicitModeForIt(FinalizationCase):
    """The dogfood half: an operator asks for this by name or it never runs."""

    def grants(self, **overrides):
        given = {"attempt_id": ATTEMPT,
                 "work_ref": {"authority_uuid": UUID, "work_id": WORK},
                 "participant": WHO, "generation": 1}
        given.update(overrides)
        return given

    def grants_file(self, **overrides):
        place = os.path.join(self._root.name, "grants.json")
        whole = {name: None for name in dogfood_operator.GRANT_MEMBERS}
        whole.update(self.grants(**overrides))
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(whole, writing)
        return place

    def evidence_place(self):
        return os.path.join(self._root.name, "recovery.json")

    def built(self):
        from baton_v12.worker_manager import attempt_runtime_of

        state = attempt_runtime_of(self.store, ATTEMPT)
        return lambda given: {"store": self.store, "state": state,
                              "session": self.session, "disagreement": None,
                              # THE FIXTURE'S OWN STORE IS NOT CLOSED BY THE
                              # COMMAND: this builder opened nothing.
                              "closing": ()}

    def test_the_deployment_mode_takes_no_adapter_either(self):
        taken = list(inspect.signature(
            dogfood_operator.finalize_quiescent).parameters)

        self.assertEqual(taken, ["store", "port", "given", "reason"])

    def test_it_records_the_fence_and_nothing_it_did_not_observe(self):
        self.quiescent()

        record = dogfood_operator.finalize_quiescent(
            self.store, self.port, self.grants(), reason=REASON)

        self.assertEqual(record["branch"], "quiescent-finalization")
        self.assertIs(record["resolved"], True)
        self.assertEqual(record["unresolved"], [])
        self.assertIs(record["authority_fence"]["fenced"], True)
        self.assertEqual(record["authority_fence"]["gate"],
                         "runtime-quiescence:1")
        self.assertEqual(record["authority_fence"]["worker_disposition"],
                         "unable")
        # WHAT IT MADE NO ENGINE CALL ABOUT STAYS NULL rather than being
        # filled in from an inference.
        for member in ("runtime", "cleanup", "custody", "credentials",
                       "launch", "observed_after", "zombies"):
            self.assertIsNone(record[member], member)

    def test_the_record_is_exactly_the_closed_recovery_member_set(self):
        self.quiescent()
        record = dogfood_operator.finalize_quiescent(
            self.store, self.port, self.grants(), reason=REASON)

        written = dogfood_operator.write_recovery(record,
                                                  self.evidence_place())

        with open(written, encoding="utf-8") as reading:
            self.assertEqual(sorted(json.load(reading)),
                             sorted(dogfood_operator.RECOVERY_MEMBERS))

    def test_editable_grants_naming_another_generation_end_nothing(self):
        self.quiescent()

        record = dogfood_operator.finalize_quiescent(
            self.store, self.port, self.grants(generation=2), reason=REASON)

        self.assertIs(record["resolved"], False)
        self.assertTrue(record["unresolved"])
        self.assertEqual(self.fences(), [])
        self.assertEqual(self.journalled(), [])

    def test_the_recorded_identity_is_the_managers_and_not_the_grants(self):
        self.quiescent()

        record = dogfood_operator.finalize_quiescent(
            self.store, self.port, self.grants(), reason=REASON)

        self.assertEqual(record["work_ref"],
                         {"authority_uuid": UUID, "work_id": WORK})
        self.assertEqual(record["participant"], WHO)
        self.assertEqual(record["generation"], 1)
        self.assertEqual(record["attempt_state"]["assignment"], self.expect())

    def test_a_manager_refusal_becomes_an_account_rather_than_an_ending(self):
        self.running(value="running")

        record = dogfood_operator.finalize_quiescent(
            self.store, self.port, self.grants(), reason=REASON)

        self.assertIs(record["resolved"], False)
        self.assertIn("declined to finalize", record["unresolved"][0])
        self.assertIsNone(record["authority_fence"])

    def test_the_documented_command_runs_it_and_writes_the_record(self):
        self.quiescent()
        place = self.evidence_place()

        status = dogfood_operator.main(
            ["--grants", self.grants_file(), "--evidence", place,
             "--finalize-quiescent", "--finalize-reason", REASON],
            capabilities=self.never(), finalize_capabilities=self.built())

        self.assertEqual(status, 0)
        with open(place, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertEqual(written["branch"], "quiescent-finalization")
        self.assertEqual(written["reason"], REASON)
        self.assertIs(written["resolved"], True)

    def test_the_command_refuses_without_the_operators_own_reason(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator.main(
                ["--grants", self.grants_file(),
                 "--evidence", self.evidence_place(),
                 "--finalize-quiescent"],
                capabilities=self.never(), finalize_capabilities=self.built())

        self.assertIn("--finalize-reason", str(caught.exception))

    def test_the_command_refuses_when_no_launcher_supplies_the_mode(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator.main(
                ["--grants", self.grants_file(),
                 "--evidence", self.evidence_place(),
                 "--finalize-quiescent", "--finalize-reason", REASON],
                capabilities=self.never())

        self.assertIn("finalization capability", str(caught.exception))

    def test_two_endings_in_one_command_are_two_acts_on_one_attempt(self):
        for other in ("--abandon", "--retry-handoff"):
            with self.subTest(other=other):
                with self.assertRaises(
                        dogfood_operator.OperatorRefusal) as caught:
                    dogfood_operator.main(
                        ["--grants", "unread.json", "--evidence", "out.json",
                         "--finalize-quiescent", other],
                        capabilities=self.never())
                self.assertIn("--finalize-quiescent", str(caught.exception))
                self.assertIn(other, str(caught.exception))

    def test_the_mode_refuses_an_operand_naming_material_to_deliver(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator.main(
                ["--grants", self.grants_file(),
                 "--evidence", self.evidence_place(),
                 "--credential-sources", "/home/someone/sources.json",
                 "--finalize-quiescent", "--finalize-reason", REASON],
                capabilities=self.never(), finalize_capabilities=self.built())

        self.assertIn("--credential-sources", str(caught.exception))

    def test_an_ordinary_run_never_reaches_the_finalization(self):
        """Approver ruling 2026-09-01 item 2. An `unable` result waits for an
        explicit decision, so no arc path may finalize by itself -- and the
        way to prove that is to read the arc rather than to promise it."""
        for name in ("run_dogfood_task", "compose", "_after_start", "_custody",
                     "_ended_however", "retry_handoff", "recover_abandoned",
                     "_recovering"):
            with self.subTest(function=name):
                source = inspect.getsource(getattr(dogfood_operator, name))
                self.assertNotIn("finalize_quiescent", source)

    def test_a_failed_verification_still_ends_at_the_receipt_authorized_path(
            self):
        """The still-current half of the superseded clause: failed independent
        verification never earns a review pass, and the ordinary ending is
        still the one its intake receipt authorizes."""
        source = inspect.getsource(dogfood_operator._ended_however)

        self.assertIn("authorize_cleanup", source)
        self.assertIn("abandon_attempt", source)


if __name__ == "__main__":
    unittest.main()
