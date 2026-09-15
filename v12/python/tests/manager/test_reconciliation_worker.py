"""W161230 slice 1: the fenced-before-start proof, at its own owner.

WHY THESE CASES ARE IN THIS FILE. The approved slice-1 scope names exactly four
new test paths, and this is the only one under `tests/manager/` -- which is
where the Worker Manager's owners are tested and where `test_attempts.py`
already lives. `unstarted_cancellation_of` is a Worker Manager owner, so its
cases belong beside them rather than in an integration or tools module. The
file's name anticipates the reconciliation worker of a later slice; if the
reviewer would rather these moved, they move as a unit.

WHAT IS PROVED HERE. A capacity owner that must end a member which was
cancelled before it ever ran has exactly one honest question to ask, and the
reader answers it or refuses. Every case below drives the REAL owners --
`issue_offer`, `accept_offer`, `submit_claim`, `activate_assignment`,
`request_runtime_start`, `request_cancellation` -- over a temporary store and
the existing fake Authority session and adapter. Nothing is stubbed that the
proof depends on.

The fixtures are the existing ones, reused unchanged: `AttemptCase` from
`test_attempts.py` and `FakeSession` from `test_offers.py`.
"""
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts as owner
from baton_v12.worker_manager import documents
from baton_v12.worker_manager.attempts import (
    activate_assignment, request_cancellation, request_runtime_start,
    unstarted_cancellation_of)
from baton_v12.worker_manager.store import manager_signature

from .test_attempts import ATTEMPT, Adapter, Agent, AttemptCase, WORK


class TheFencedBeforeStartProof(AttemptCase):
    """The six facts, one case each, and both race orders."""

    def cancelled(self, attempt_id=ATTEMPT, started=False):
        """An activated attempt, optionally started, then really cancelled.

        THE AUTHORITY'S OWN AFTER-STATE, which the fake does not reach by
        itself: it answers whatever the session was given, so a case that
        forgot would be asking the reader to accept a Work that never recorded
        a fence and a generation the Authority still calls live. Both halves
        are modelled here -- the fenced generation in the Work projection and
        the ended assignment -- and the negatives below withhold one at a time
        on purpose.
        """
        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        self.adapter = Adapter()
        if started:
            request_runtime_start(self.store, self.adapter,
                                  attempt_id=attempt_id)
        request_cancellation(self.store, self.port, Agent(), self.adapter,
                             attempt_id=attempt_id)
        self.fenced()
        return attempt_id

    def fenced(self, generation=1, cause="cancelled", **projected):
        """What the Authority says after it fenced that generation.

        THE WORK IS NAMED. `project_work` carries `work_id` as an unread
        optional member, so a fixture that omitted it was asking the reader to
        accept a projection about no particular Work -- which is exactly what
        review 2026-09-13T15:47:57Z found the reader accepting.
        """
        held = {"work_id": WORK,
                "fenced_generations": [{"generation": generation,
                                        "cause": cause, "reason": None}]}
        held.update(projected)
        self.session._work = dict(self.session._work, **held)
        self.session.live_assignment = None

    # -- the proof itself ----------------------------------------------------

    def test_a_cancelled_attempt_that_never_started_is_proved(self):
        """THE POSITIVE, and it names what it rests on.

        The answer carries the assignment, both cancellation identities and the
        axis value, so a caller can re-derive the judgment rather than trust
        the word.
        """
        self.cancelled()
        answer = unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertEqual(answer["state"], documents.FENCED_BEFORE_START)
        self.assertEqual(answer["attempt_id"], ATTEMPT)
        self.assertEqual(answer["execution_runtime"], "cancel-requested")
        self.assertEqual(answer["assignment"], self.expect())
        self.assertTrue(answer["cancel_operation_id"].startswith(
            "attempt.cancel:"))
        self.assertEqual(answer["authority_operation_id"],
                         "authority." + answer["cancel_operation_id"])

    def test_the_answer_is_never_quiescence_or_a_runtime(self):
        """It is a different fact from `quiescent` and `destroyed`, and it
        carries no runtime identity at all -- a member that could hold one
        would invite a caller to read absence as quiescence."""
        self.cancelled()
        answer = unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertNotIn(answer["state"], ("quiescent", "destroyed"))
        self.assertNotIn("runtime_id", answer)
        self.assertEqual(
            sorted(answer),
            sorted(documents.CONTRACTS["attempt.fenced-before-start"][0]))

    def test_the_reader_changes_nothing(self):
        """A READER. The attempt row and the journal are what they were."""
        self.cancelled()
        before = self.row()
        unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertEqual(self.row(), before)
        self.assertEqual(self.adapter.started, [])

    # -- each missing fact is a refusal, and capacity stays held -------------

    def test_an_attempt_that_was_never_activated_is_refused(self):
        self.claimed()
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("no fixed assignment", str(caught.exception))

    def test_an_activated_attempt_with_no_cancellation_is_refused(self):
        """The axis is `not-started` and nothing was committed: there is
        nothing here to prove and the reader says so rather than reporting an
        attempt that merely has not run yet."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("no committed cancellation", str(caught.exception))

    def test_another_participants_session_cannot_ask(self):
        self.cancelled()
        other = type(self.port)(type(self.session)(participant="baton.other"),
                                self.port.claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, other, ATTEMPT)
        self.assertEqual(caught.exception.code, "capability")

    def test_an_attached_runtime_is_refused(self):
        """A runtime that EXISTS is ended through its own explicit
        finalization with actual exclusion evidence, not through this."""
        self.cancelled(started=True)
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("attached", str(caught.exception))

    def test_an_authority_that_answers_no_fences_at_all_is_refused(self):
        """[P1] The fence is the AUTHORITY's act, so the manager's own journal
        is not evidence of it -- and a projection that carries no fenced
        generations AT ALL is a projection that cannot answer the question,
        which is a different absence from an empty list and refuses too.

        The local cancellation below ran to completion; nothing about the
        Authority was modelled after it, which is exactly the state this case
        exists to refuse."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        request_cancellation(self.store, self.port, Agent(), Adapter(),
                             attempt_id=ATTEMPT)
        self.session._work = dict(self.session._work, work_id=WORK)
        self.session.live_assignment = None
        self.assertNotIn("fenced_generations", self.session._work)
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("carries no fenced generations", str(caught.exception))

    # -- the two race orders, and the replay that the axis cannot see --------

    def test_a_stale_start_pre_read_loses_to_the_cancellation_axis(self):
        """ORDER ONE, AT THE REAL WINDOW. The start read `not-started`, the
        cancellation committed its axis while the start was still checking the
        adapter's plan, and the start's own transaction then refuses -- so no
        operation is committed, no adapter is reached, and the proof stands.

        Review 2026-09-13T15:38:01Z [P2] asked for this interleaving rather
        than the predicate: my first form removed `runtime_id` with SQL after a
        completed start, which exercised the reader and not the race.
        """
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        adapter = Adapter()
        agreeing = owner._plan_agrees

        def interleave(*operands):
            agreeing(*operands)
            request_cancellation(self.store, self.port, Agent(), Adapter(),
                                 attempt_id=ATTEMPT)
            self.fenced()

        with mock.patch.object(owner, "_plan_agrees", side_effect=interleave):
            with self.assertRaises(ContractRefusal) as caught:
                request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(adapter.started, [])
        self.assertIn("cancel-requested", str(caught.exception))
        self.assertEqual(
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)["state"],
            documents.FENCED_BEFORE_START)

    def test_a_committed_start_delayed_at_the_adapter_refuses_the_proof(self):
        """ORDER TWO, AT THE REAL WINDOW. The start's operation committed and
        its adapter call has not returned; the cancellation lands in exactly
        that gap, so the axis reads `cancel-requested` and `runtime_id` is
        still absent -- the shape a reader looking only at the axis would call
        proved. The committed start is what refuses it, which is why that
        exclusion is not redundant with the axis.

        No row is edited: the window is entered from inside the adapter.
        """
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        adapter = Adapter()
        starting = adapter.start
        inside = []

        def delayed(operands):
            request_cancellation(self.store, self.port, Agent(), Adapter(),
                                 attempt_id=ATTEMPT)
            self.fenced()
            self.assertIsNone(self.row()["runtime_id"])
            self.assertEqual(self.row()["execution_runtime"],
                             "cancel-requested")
            with self.assertRaises(ContractRefusal) as caught:
                unstarted_cancellation_of(self.store, self.port, ATTEMPT)
            self.assertIn("committed a runtime start", str(caught.exception))
            inside.append(True)
            return starting(operands)

        adapter.start = delayed
        # The later reconciliation refuses too, because a running observation
        # after a cancellation is its own contradiction; that refusal does not
        # unmake the journal-only judgment taken above.
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(inside, [True])

    def test_a_start_after_the_cancellation_is_refused_by_the_axis(self):
        """ORDER TWO: the cancellation won.

        This is the owners' own rule rather than the reader's: the start's
        observation inside its transaction is `cancel-requested` ->
        `start-requested`, which the transition map does not contain. The
        reader's proof is only sound because that refusal exists, so it is
        asserted here.
        """
        self.cancelled()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, Adapter(), attempt_id=ATTEMPT)
        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertIn("cancel-requested", str(caught.exception))
        # AND THE PROOF STILL STANDS, because nothing committed.
        answer = unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertEqual(answer["state"], documents.FENCED_BEFORE_START)

    # -- the evidence itself, which a familiar-looking row is not -----------

    def test_a_foreign_committed_intent_cannot_prove_this_attempt(self):
        """[P1] A committed row with a familiar kind at a key this attempt
        derives is not this attempt's cancellation. It is written here through
        the REAL transaction boundary rather than by editing a row, and it
        names a foreign attempt, generation and Authority operation."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        attempt = self.row()
        self.store.transact(
            owner._cancel_operation_id(attempt), "attempt.cancel",
            manager_signature("attempt.cancel", {"foreign": True}),
            lambda connection: documents.cancel_intent(
                attempt_id="foreign-attempt",
                assignment=dict(self.expect(), generation=999),
                authority_operation_id="foreign-operation", reason=None))
        owner.observe(self.store, attempt_id=ATTEMPT,
                      axis="execution_runtime", value="cancel-requested")
        self.fenced()
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("actually names", str(caught.exception))

    def test_a_changed_signature_over_the_same_intent_is_refused(self):
        """The members can all agree and the record still be a different act:
        a signature this attempt's own operands do not produce was written
        over something else."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        attempt = self.row()
        self.store.transact(
            owner._cancel_operation_id(attempt), "attempt.cancel",
            manager_signature("attempt.cancel", {"different": "operands"}),
            lambda connection: documents.cancel_intent(
                attempt_id=ATTEMPT, assignment=self.expect(),
                authority_operation_id=owner._authority_cancel_operation_id(
                    attempt),
                reason=None))
        owner.observe(self.store, attempt_id=ATTEMPT,
                      axis="execution_runtime", value="cancel-requested")
        self.fenced()
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("signature", str(caught.exception))

    def test_an_authority_that_never_fenced_the_generation_is_refused(self):
        """[P1] ABSENCE IS NOT EVIDENCE. The local cancellation ran to
        completion and the live assignment is gone, but the Work names no
        fenced generation -- which is what a Work that never had one, and a
        projection that could not answer, both look like."""
        self.cancelled()
        self.session._work = dict(self.session._work, fenced_generations=[])
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("has not fenced generation", str(caught.exception))

    def test_a_fence_of_another_generation_is_refused(self):
        """Somebody else's generation ended is not this one's fence."""
        self.cancelled()
        self.fenced(generation=7)
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("has not fenced generation", str(caught.exception))

    def test_a_generation_both_fenced_and_live_is_refused(self):
        """Two contradictory answers from one owner, and the conservative
        reading of a contradiction is a refusal."""
        self.cancelled()
        self.session.live_assignment = {
            "work_ref": self.expect()["work_ref"],
            "participant": self.expect()["participant"], "generation": 1}
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("both fenced and live", str(caught.exception))

    def test_a_projection_of_another_work_is_refused(self):
        """[P1] Generations are LOCAL TO A WORK: another Work in the same
        Authority may have generation 1 fenced while this one has none."""
        self.cancelled()
        self.fenced(work_id="0000000a-W999")
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("a fence is a fact about one Work", str(caught.exception))

    def test_a_projection_naming_no_work_is_refused(self):
        """`project_work` treats `work_id` as unread and optional, so the
        reader has to require it rather than assume the projection is about
        the Work it asked for."""
        self.cancelled()
        self.session._work = {
            one: two for one, two in self.session._work.items()
            if one != "work_id"}
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("the projection's Work", str(caught.exception))

    def test_a_boolean_generation_is_not_generation_one(self):
        """[P1/P2] `bool` is an `int` and `True == 1`, which is exactly the
        confusion an identity must not permit."""
        self.cancelled()
        self.fenced(generation=True)
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("positive whole number", str(caught.exception))

    def test_a_fence_entry_missing_its_reason_member_is_refused(self):
        """The closed entry is generation, cause and reason. A member that is
        absent rather than null is a different document."""
        self.cancelled()
        self.session._work = dict(
            self.session._work,
            fenced_generations=[{"generation": 1, "cause": "cancelled"}])
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("reason", str(caught.exception))

    def test_one_generation_fenced_twice_is_a_contradiction(self):
        """A generation is fenced once; two entries naming one are evidence
        contradicting itself rather than a duplicate to ignore."""
        self.cancelled()
        self.session._work = dict(
            self.session._work,
            fenced_generations=[
                {"generation": 1, "cause": "cancelled", "reason": None},
                {"generation": 1, "cause": "superseded", "reason": None}])
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("fenced more than once", str(caught.exception))

    def test_a_fence_entry_carrying_an_unknown_member_is_refused(self):
        """[P2] The entry's shape is CLOSED. The first form checked the members
        it knew and rebuilt a three-member dictionary, which silently discarded
        anything else -- so a declared closed document was not closed."""
        self.cancelled()
        self.session._work = dict(
            self.session._work,
            fenced_generations=[{"generation": 1, "cause": "cancelled",
                                 "reason": None, "unrecognized": "value"}])
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("unrecognized", str(caught.exception))

    def test_an_unmatched_entry_is_owned_before_it_is_reported(self):
        """EVERY entry is validated before selection, and the diagnostic does
        not operate on values it has not owned: a list mixing "7" and 8 used to
        reach `sorted` and raise a bare TypeError instead of refusing."""
        self.cancelled()
        self.session._work = dict(
            self.session._work,
            fenced_generations=[
                {"generation": "7", "cause": "cancelled", "reason": None},
                {"generation": 8, "cause": "cancelled", "reason": None}])
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("positive whole number", str(caught.exception))

    def test_an_exact_committed_start_replays_without_running_its_action(self):
        """THE REPLAY THAT THE AXIS CANNOT SEE, driven rather than described.

        `ControlStore.transact` returns a committed operation's recorded answer
        WITHOUT running the action, so a repeat of the exact start reaches its
        adapter with nothing re-journalled and no axis move. The reader refuses
        on that committed evidence either way, which is the whole reason the
        exclusion exists beside the axis check.
        """
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        adapter = Adapter()
        starting = adapter.start
        inside = []

        def delayed(operands):
            # THE START HAS COMMITTED AND NO RUNTIME IS ATTACHED YET, which is
            # the only window where the replay's consequence is visible.
            attempt = self.row()
            self.assertIsNone(attempt["runtime_id"])
            operation_id = owner._start_operation_id(attempt)
            ran = []
            replayed = self.store.transact(
                operation_id, "runtime.start",
                manager_signature("runtime.start",
                                  {"attempt_id": ATTEMPT,
                                   "labels": owner._runtime_labels(attempt),
                                   "operation_id": operation_id}),
                lambda connection: ran.append(True))
            self.assertEqual(ran, [], "the committed action ran again")
            self.assertEqual(replayed["attempt_id"], ATTEMPT)
            request_cancellation(self.store, self.port, Agent(), Adapter(),
                                 attempt_id=ATTEMPT)
            self.fenced()
            with self.assertRaises(ContractRefusal) as caught:
                unstarted_cancellation_of(self.store, self.port, ATTEMPT)
            self.assertIn("committed a runtime start", str(caught.exception))
            inside.append(True)
            return starting(operands)

        adapter.start = delayed
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(inside, [True])

    def test_an_exact_repeat_answers_the_same_document(self):
        """A reader has no act to replay, so two asks are one answer."""
        self.cancelled()
        first = unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        request_cancellation(self.store, self.port, Agent(), Adapter(),
                             attempt_id=ATTEMPT)
        self.assertEqual(
            unstarted_cancellation_of(self.store, self.port, ATTEMPT), first)

    def test_a_cancellation_interrupted_before_its_axis_is_refused(self):
        """THE WINDOW THAT MAKES THE AXIS THE REQUIRED FACT.

        `request_cancellation` journals its intent and fences the Authority
        BEFORE `_order_quiescence` writes the axis. Interrupted in between, the
        attempt still carries `not-started` -- and a later start would be
        allowed. The intent alone is therefore not the proof, and the reader
        refuses here.
        """
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        self.session.fence_answer = RuntimeError("the authority is away")
        with self.assertRaises(RuntimeError):
            request_cancellation(self.store, self.port, Agent(), Adapter(),
                                 attempt_id=ATTEMPT)
        self.fenced()
        self.assertEqual(self.row()["execution_runtime"], "not-started")
        with self.assertRaises(ContractRefusal) as caught:
            unstarted_cancellation_of(self.store, self.port, ATTEMPT)
        self.assertIn("does not carry it", str(caught.exception))


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
