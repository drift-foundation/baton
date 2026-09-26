"""W266329 stage 1: RESERVE BEFORE LAUNCH, proved on the real start path.

Owner 266361 selects exactly this: one bounded runnable command, real disposable
stores and a controlled adapter, proving committed ownership before the external
start, transaction exit before adapter entry, and the positive, contention and
failure effects. No live provider, no deployed store, no broad suite.

WHAT IS REAL: `attempts.request_runtime_start` itself, a real `ControlStore` on a
disposable temporary file, the real journal, the real lane. WHAT IS CONTROLLED:
the adapter, which is the accepted `tests.manager.test_attempts.Adapter` plus one
subclass that records what the ruling forbids. No daemon, container or image is
reached, so a timeout here proves nothing about an engine -- which is why the
reservation exists.

THE PROOF OF "TRANSACTION EXIT BEFORE EXTERNAL I/O" IS NOT A FLAG READ IN THE
SAME CONNECTION. A second real handle, opened on the same file at the moment the
adapter is entered, must already SEE the committed state. Another connection
cannot see an uncommitted write, so its view is what makes the exit a fact rather
than an assertion about a boolean.

AND THE REVIEW'S CORRECTION IS ENCODED RATHER THAN ASSUMED. Review
2026-09-25T13-52-41Z: my preparation wrongly said a replay of
`request_runtime_start` returns its committed document. It does not -- the public
function refuses a non-`not-started` axis (`attempts.py:1415`). The JOURNAL
replays; the PUBLIC REQUEST does not. Both halves are asserted here.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from unittest.mock import patch                                 # noqa: E402

from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import ControlStore               # noqa: E402
from baton_v12.worker_manager import attempt_runtime_of         # noqa: E402
from baton_v12.worker_manager import attempts as attempts_module  # noqa: E402
from baton_v12.worker_manager.attempts import \
    request_runtime_start                                       # noqa: E402
from baton_v12.worker_manager.store import manager_signature    # noqa: E402

from tests.manager.test_attempts import (ATTEMPT, Adapter,      # noqa: E402
                                         NOW,
                                         TheRuntimeIsStartedOnceAndReconciled)


class WatchingAdapter(Adapter):
    """The accepted controlled adapter, asked what the ruling forbids.

    It records, at the exact moment `start` is entered: whether the manager's own
    connection still has a transaction open, and what a SECOND real handle on the
    same store file can already see. Everything else is the accepted fake.
    """

    def __init__(self, store, path):
        super().__init__()
        self._store = store
        self._path = path
        self.entered = []

    def start(self, operands):
        self.entered.append({
            "in_transaction": self._store._connection.in_transaction,
            "second_handle_sees": self._witnessed(),
            "operation": operands.get("operation_id"),
        })
        return super().start(operands)

    def _witnessed(self):
        """What another connection can read WHILE this call is in flight."""
        other = ControlStore.open(self._path, incarnation="witness-1",
                                  clock=lambda: NOW)
        try:
            return attempt_runtime_of(other, ATTEMPT)["execution_runtime"]
        finally:
            other.close()


class TheReservationIsCommittedBeforeTheLaunch(
        TheRuntimeIsStartedOnceAndReconciled):
    """Stage 1's proofs, on the real `request_runtime_start`.

    Inherits the accepted start fixture -- `delivered()` composes a real input
    root and the attempt recorded against that exact manifest, which is what
    this boundary compares -- so the reservation under test is the one the
    accepted path performs rather than a shape this module invented.
    """

    def watching(self):
        return WatchingAdapter(self.store, self.path)

    def start_operands(self, adapter):
        """The labels the manager actually handed the adapter."""
        [submitted] = adapter.started
        return submitted

    # -- transaction exit before external I/O --------------------------------

    def test_the_transaction_is_closed_before_the_adapter_is_entered(self):
        """THE RULING'S FIRST SENTENCE, measured at the boundary itself."""
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()

        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT, inputs=inputs)

        self.assertEqual(answer["decision"], "attached")
        self.assertEqual(len(adapter.entered), 1, adapter.entered)
        seen = adapter.entered[0]
        # NO TRANSACTION IS OPEN on the acting connection...
        self.assertFalse(seen["in_transaction"],
                         "a database transaction was open across the start")
        # ...AND THE COMMIT IS A FACT, because another connection sees it. An
        # uncommitted write is invisible to a second handle, so this is the
        # assertion that cannot be satisfied by an early flag.
        self.assertEqual(seen["second_handle_sees"], "start-requested")

    # -- the positive path ---------------------------------------------------

    def test_the_positive_path_reserves_then_starts_exactly_once(self):
        """One submission, and the reservation is the journalled act it names."""
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()

        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT, inputs=inputs)

        self.assertEqual(answer["decision"], "attached")
        self.assertEqual(len(adapter.started), 1, adapter.started)
        submitted = self.start_operands(adapter)
        # THE ADAPTER IS TOLD THE OPERATION IDENTITY, which is what makes both
        # sides settle one act rather than two adjacent ones.
        attempt = attempts_module._require_attempt(self.store, ATTEMPT)
        self.assertEqual(submitted["operation_id"],
                         attempts_module._start_operation_id(attempt))
        self.assertIn("labels", submitted)

    # -- contention ----------------------------------------------------------

    def test_a_second_request_refuses_without_a_second_submission(self):
        """THE RESERVATION IS THE EXCLUSION, and it is not re-enterable.

        The axis refusal at `attempts.py:1415` is what a competing or repeated
        caller meets, and the measurement that matters is that the ENGINE saw
        nothing new: a refusal after a second submission would be worthless.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        self.assertEqual(len(adapter.started), 1)

        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)

        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertEqual(len(adapter.started), 1,
                         "a second submission crossed to the adapter")

    def test_a_competing_handle_is_refused_by_the_same_reservation(self):
        """A SECOND MANAGER, on its own handle, meets the committed record.

        SQLite binds a connection to its opening thread, so a second manager is
        a second handle; this one is opened here and asks for the same start.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)

        other = ControlStore.open(self.path, incarnation="manager-2",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        contender = self.watching()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(other, contender, attempt_id=ATTEMPT,
                                  inputs=inputs)

        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertEqual(contender.started, [],
                         "the competing handle reached the adapter")
        self.assertEqual(len(adapter.started), 1)

    # -- failure after the reservation ---------------------------------------

    def test_a_faulting_adapter_leaves_the_reservation_committed(self):
        """THE POINT OF RESERVING FIRST: the record outlives the failure.

        The adapter faults AFTER the commit. Three things must hold, and the
        third is the one I had wrong: the reservation was already committed when
        the adapter was entered; the fault is re-raised UNCHANGED, because the
        manager has no account of what it was; and the manager SETTLES by asking
        the adapter what exists rather than assuming nothing does. With this fake
        reporting the container it was asked to create, the settled axis is
        `running` -- a runtime reconciled, not a runtime lost. My first version of
        this case expected `start-requested`/`uncertain` and was measuring its own
        assumption instead of `attempts.py:1543-1560`.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()
        fault = RuntimeError("the fixture faulted the start")
        adapter.start_failure = fault

        with self.assertRaises(RuntimeError) as raised:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertIs(raised.exception, fault,
                      "the manager replaced the fault with its own guess")

        self.assertEqual(len(adapter.started), 1, adapter.started)
        # THE RESERVATION WAS COMMITTED BEFORE THE EXTERNAL CALL, witnessed by a
        # second handle at the moment of entry rather than inferred afterwards.
        self.assertEqual(adapter.entered[0]["second_handle_sees"],
                         "start-requested")
        self.assertFalse(adapter.entered[0]["in_transaction"])
        # AND THE MANAGER ASKED THE ENGINE rather than settling blind. Review
        # 2026-09-25T14-12-41Z: my first version of this was satisfied by
        # `adapter.started` alone, which is true by this point in every case, so
        # it measured nothing. The fake records every `observe(runtime_id)` call,
        # so the reconciliation query is asserted directly.
        self.assertTrue(adapter.observed,
                        "the fault was settled without observing the runtime")
        other = ControlStore.open(self.path, incarnation="witness-2",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        self.assertEqual(
            attempt_runtime_of(other, ATTEMPT)["execution_runtime"], "running")
        # AND A RETRY DOES NOT RE-SUBMIT.
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(len(adapter.started), 1,
                         "a retry after a failed start submitted again")

    def test_a_contender_during_the_first_start_does_not_launch_again(self):
        """CONTENTION BEFORE THE FIRST ADAPTER RETURN, which the sequential
        cases above do not reach.

        The contender arrives while caller A is still INSIDE `adapter.start`,
        after A's reservation committed. It must be refused before the engine,
        and the measurement is that its own adapter recorded nothing.
        """
        inputs, _given, _assignment = self.delivered()
        contender = self.watching()
        outcomes = []

        adapter = self.watching()
        original = adapter.start

        def racing(operands):
            if not outcomes:
                other = ControlStore.open(self.path, incarnation="contender-1",
                                          clock=lambda: NOW)
                try:
                    try:
                        outcomes.append(("answered", request_runtime_start(
                            other, contender, attempt_id=ATTEMPT,
                            inputs=inputs)))
                    except ContractRefusal as refusal:
                        outcomes.append(("refused", refusal.code))
                finally:
                    other.close()
            return original(operands)

        adapter.start = racing
        answer = request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                       inputs=inputs)

        self.assertEqual(answer["decision"], "attached")
        self.assertEqual(outcomes, [("refused", "already-terminal")], outcomes)
        self.assertEqual(contender.started, [],
                         "the contender reached the adapter")
        self.assertEqual(len(adapter.started), 1)

    def test_the_stale_caller_reconciles_instead_of_submitting(self):
        """THE OTHER SIDE OF THE CORRECTION: what the loser ANSWERS.

        The reviewer's immutable regression asserts that a caller suspended
        after its preliminary axis read submits nothing once another manager has
        reserved. This asserts the rest of that outcome: the loser does not
        raise, it RECONCILES -- deciding what exists by identity rather than
        assuming its own intent was carried out -- and exactly one runtime was
        ever created.
        """
        inputs, _given, _assignment = self.delivered()
        other = ControlStore.open(self.path, incarnation="winner-1",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        loser, winner = self.watching(), Adapter("runtime-winner")
        held = attempts_module._plan_agrees
        once = []
        answers = {}

        def interleave(adapter, attempt_id, inputs):
            held(adapter, attempt_id, inputs)
            if not once:
                once.append(True)
                answers["winner"] = request_runtime_start(
                    other, winner, attempt_id=ATTEMPT, inputs=inputs)

        with patch.object(attempts_module, "_plan_agrees", interleave):
            answers["loser"] = request_runtime_start(
                self.store, loser, attempt_id=ATTEMPT, inputs=inputs)

        self.assertEqual(once, [True], "the interleaving never ran")
        # THE WINNER STARTED EXACTLY ONE RUNTIME; THE LOSER STARTED NONE.
        self.assertEqual(len(winner.started), 1)
        self.assertEqual(loser.started, [],
                         "the stale caller submitted after the reservation")
        # AND THE LOSER ANSWERED BY RECONCILING, so it asked the engine what
        # exists rather than raising or inventing an outcome.
        self.assertTrue(loser.observed or loser.listing is not None,
                        f"the loser answered without asking: {answers}")
        self.assertIn("decision", answers["loser"])

    # -- the instrument itself ------------------------------------------------

    def test_a_second_handle_cannot_see_an_uncommitted_write(self):
        """THE POSITIVE CONTROL, so the proof above is not self-confirming.

        Every case here rests on one claim about the witness: a second handle
        sees committed state and NOT uncommitted state. If that were false,
        `second_handle_sees == "start-requested"` would prove nothing at all. So
        this holds a real write open in a transaction and shows the witness still
        reads the OLD value -- which is what makes the same read, taken at adapter
        entry, evidence that the transaction had already exited.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        settled = attempt_runtime_of(self.store, ATTEMPT)["execution_runtime"]

        other = ControlStore.open(self.path, incarnation="witness-3",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        connection = self.store._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "UPDATE attempts SET execution_runtime = ? "
                "WHERE runtime_attempt_id = ?", ("uncertain", ATTEMPT))
            # THE WRITER SEES ITS OWN UNCOMMITTED WRITE...
            self.assertEqual(
                attempt_runtime_of(self.store, ATTEMPT)["execution_runtime"],
                "uncertain")
            # ...AND THE WITNESS DOES NOT.
            self.assertEqual(
                attempt_runtime_of(other, ATTEMPT)["execution_runtime"],
                settled)
        finally:
            connection.execute("ROLLBACK")
        self.assertEqual(
            attempt_runtime_of(self.store, ATTEMPT)["execution_runtime"],
            settled)

    # -- the distinction the review demanded ---------------------------------

    def test_the_journal_replays_while_the_public_request_refuses(self):
        """PUBLIC REQUEST REPLAY IS NOT JOURNAL REPLAY.

        My preparation said a replay of `request_runtime_start` answers its
        committed document. Review 2026-09-25T13-52-41Z is right that it does
        not: the public function refuses a non-`not-started` axis. The JOURNAL
        does replay the same identity and signature. Both are asserted, because
        conflating them is what made the plan wrong.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = self.watching()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        submitted = self.start_operands(adapter)
        attempt = attempts_module._require_attempt(self.store, ATTEMPT)
        operation_id = attempts_module._start_operation_id(attempt)

        # THE JOURNAL: the identity and signature answer the committed act.
        # THE EXACT OPERANDS, read from the source rather than guessed: my first
        # attempt omitted `operation_id` and the store refused it by §4.2 --
        # "reusing an id with different operands changes nothing" -- which is
        # itself the journal keeping one identity to one act.
        signature = manager_signature("runtime.start",
                                      {"attempt_id": ATTEMPT,
                                       "labels": submitted["labels"],
                                       "operation_id": operation_id})
        found, record = self.store.replay(operation_id, signature,
                                          kind="runtime.start")
        self.assertTrue(found, "the journal did not replay the committed start")
        self.assertEqual(record["attempt_id"], ATTEMPT)

        # THE PUBLIC REQUEST: refuses, and submits nothing.
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertEqual(len(adapter.started), 1)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases defined in THIS module.

    It inherits the accepted start fixture, whose own cases belong to that
    suite;
    re-running them here would inflate this stage's evidence with another
    module's.
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
