"""W2845 cut 3 — the operation journal, its two kinds of refusal, settlement,
restart, and races between real processes.

The obligations: the four durable states of one operation identity, with
UNSUBMITTED being the ABSENCE of a row; effectively-once over the FULL effective
operands including the prose; an ordinary refusal that writes nothing and stays
retryable versus a durable one that is itself a committed outcome; retirement
answered BEFORE the operands, because retirement is a property of the identity;
settlement authority that is asserted rather than inherited; and an unanswerable
lookup that settles nothing.

The races are run in SPAWNED PROCESSES against one store file, because a
competing claim has to lose by being REFUSED inside a transaction -- which is a
decision -- rather than by failing to get a transaction at all, which is an
error.  Two threads in one interpreter would share a connection and prove
neither.
"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

from baton_v12.authority import Authority, Refusal, V12, claim_signature
from baton_v12.authority.identity import (GATE_QUIESCENCE, gate_token,
                                          signature_of)

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
GEMINI = "baton.gemini"
ROUTE = "impl"
NOW = "2026-08-24T05:00:00.000Z"

class JournalCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-authority-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core

    def work(self, work_id=WORK, *, contract=V12, handlers=(CLAUDE,)):
        self.core.create_work(work_id, ROUTE, contract=contract, operation_id=("create-" + str(work_id))[:160])
        for participant in handlers:
            self.core.add_route_handler(ROUTE, participant)
        return work_id


class EffectivelyOnce(JournalCase):

    def test_an_exact_repeat_replays_and_performs_nothing_twice(self):
        self.work()
        # W16823: THE WHOLE RESULT, because that is what the journal retains
        # and what a replay must reproduce.  A retry that reproduced the fence
        # and recomposed the decision would answer what the act WOULD be
        # authorized under now rather than what it was performed under.
        first = self.core.claim(WORK, CLAUDE, operation_id="op-1")
        second = self.core.claim(WORK, CLAUDE, operation_id="op-1")
        self.assertEqual(second, first)
        # ONE claim happened.  Without the journal the second call would have
        # refused ("already claimed"), which looks similar and is the opposite
        # answer: a retry must SUCCEED with the first outcome.
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed"])
        self.assertEqual(self.core.project_work(WORK)["generation_counter"], 1)
        record = self.core.operation_record("op-1")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["result"], first)
        self.assertEqual(record["signature"], claim_signature(WORK, CLAUDE))

    def test_a_reused_id_with_different_operands_collides(self):
        self.work(WORK)
        self.work(OTHER)
        self.core.claim(WORK, CLAUDE, operation_id="op-1")
        for what, call in [
                ("another Work",
                 lambda: self.core.claim(OTHER, CLAUDE, operation_id="op-1")),
                ("another participant",
                 lambda: self.core.claim(WORK, GEMINI, operation_id="op-1"))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                self.assertIn("different operands", str(caught.exception))
        # And the other Work was not touched by the collision.
        self.assertIsNone(self.core.assignment_of(OTHER))

    def test_the_prose_rides_the_signature(self):
        # Reusing one operation id with different DURABLE TEXT is a refusal
        # rather than a silent replay of somebody else's result -- which is only
        # true if the text is part of the signature.  This is the case that says
        # so at the boundary rather than in the signature helper.
        assignment = self.core.claim(self.work(), CLAUDE, operation_id="claim-1")["assignment"]
        self.core.end(assignment, operation_id="end-1", reason="finished")
        with self.assertRaises(Refusal) as caught:
            self.core.end(assignment, operation_id="end-1",
                          reason="abandoned")
        self.assertIn("different operands", str(caught.exception))
        # The FIRST prose is what is durable, and the replay returns it.
        self.assertEqual(self.core.assignment_events(WORK)[-1]["reason"],
                         "finished")
        self.assertEqual(
            self.core.end(assignment, operation_id="end-1",
                          reason="finished")["cause"], "release")

    def test_every_mutating_transition_needs_an_operation_id(self):
        assignment = self.core.claim(self.work(), CLAUDE, operation_id="claim-1")["assignment"]
        for what, call in [
                ("claim", lambda: self.core.claim(OTHER, CLAUDE,
                                                  operation_id="")),
                ("end", lambda: self.core.end(assignment, operation_id=None)),
                ("cancel", lambda: self.core.cancel(assignment,
                                                    operation_id=7)),
                ("pass", lambda: self.core.pass_work(
                    assignment, to_route="rview", operation_id="")),
                ("reject_plan", lambda: self.core.reject_plan(
                    assignment, plan_digest="sha256:p", operation_id=None)),
                ("install_gate", lambda: self.core.install_gate(
                    WORK, gate=gate_token(GATE_QUIESCENCE, "1"),
                    expect=assignment, operation_id="")),
                ("satisfy_gate", lambda: self.core.satisfy_gate(
                    WORK, gate="x", evidence={}, operation_id=None))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    call()
        # Nothing moved, and no row was written under an id nobody named.
        self.assertEqual(self.core.assignment_of(WORK), assignment)

    def test_each_transition_has_its_own_signature_space(self):
        # A release and a cancellation of the same assignment are DIFFERENT
        # operations, so one operation id cannot mean both.
        assignment = self.core.claim(self.work(), CLAUDE, operation_id="claim-1")["assignment"]
        self.core.end(assignment, operation_id="op-2")
        with self.assertRaises(Refusal):
            self.core.cancel(assignment, operation_id="op-2", reason="lost")
        self.assertNotEqual(
            signature_of("end", {"expect": assignment, "disposition": "release",
                                 "reason": None}),
            signature_of("cancel", {"expect": assignment, "reason": None}))


class GapsIFoundByProbingMyOwnCut(JournalCase):
    """Probed before handing over, because cut 2's review found seven things a
    passing suite did not."""

    # Review [P1]: I stated the opaque-id rule in one place and CALLED IT FROM
    # ONE SITE.  Replay enforced it; settlement and both journal reads used the
    # weaker text check.  So the table below is driven through ALL FOUR paths --
    # a rule is applied where it is called, not where it is written.
    INVALID_IDS = [
        ("a megabyte", "y" * 1_000_000),
        ("161 characters", "y" * 161),
        ("one with a space", "op 1"),
        ("one with a slash", "op/1"),
        ("one starting with a dash", "-op"),
        ("one starting with a dot", ".op"),
        ("an empty one", ""),
        ("a number", 7),
        ("none", None),
        ("unencodable text", "op\ud800"),
    ]
    VALID_IDS = ["op-1", "claim.1", "a" * 160,
                 "550e8400-e29b-41d4-a716-446655440000",
                 "baton.claude:claim:7"]

    def test_every_journal_path_holds_one_opaque_id_rule(self):
        self.work()
        for what, operation_id in self.INVALID_IDS:
            for path, call in [
                    ("claim/replay",
                     lambda oid: self.core.claim(WORK, CLAUDE,
                                                 operation_id=oid)),
                    ("settle_operation",
                     lambda oid: self.core.settle_operation(
                         oid, signature="sig", reason="deadline",
                         disposition="timeout", may_retire=True)),
                    ("operation_result",
                     lambda oid: self.core.operation_result(oid)),
                    ("operation_record",
                     lambda oid: self.core.operation_record(oid))]:
                with self.subTest(what=what, path=path):
                    with self.assertRaises(Refusal):
                        call(operation_id)
        # NOTHING was minted under any of them -- settlement used to WRITE the
        # retirement, so an invalid identity became a durable primary key that
        # replay then refused to look at.
        self.assertIsNone(self.core.assignment_of(WORK))
        # W29400: the Work's own CREATION is a journalled operation now, so
        # "nothing was minted" is stated against the paths this case probes
        # rather than against an empty table. The creation row is not under
        # any of them and its presence is the point of that Work.
        self.assertEqual(
            [one["operation_id"] for one in
             self.authority._core._store.all(
                 "SELECT operation_id FROM operation")],
            ["create-" + WORK])
        # And every id a caller legitimately uses satisfies it, on every path.
        for operation_id in self.VALID_IDS:
            with self.subTest(operation_id=operation_id[:20]):
                self.assertIsNone(self.core.operation_result(operation_id))
                self.assertIsNone(self.core.operation_record(operation_id))
                self.core.claim(WORK, CLAUDE, operation_id=operation_id)
                self.assertIsNotNone(self.core.operation_result(operation_id))
                self.core.end(self.core.assignment_of(WORK),
                              operation_id=f"end.{operation_id[:20]}")

    def test_retirement_precedence_holds_for_a_valid_identity(self):
        # The other half of the P1: with ONE rule, settlement and replay agree
        # that the identity exists, so a claim under a retired id REPLAYS the
        # bound retirement reason instead of refusing on shape and never seeing
        # it.  Two authority paths, one answer.
        self.work()
        self.core.settle_operation("op-1", signature="a-different-signature",
                                   reason="deadline passed",
                                   disposition="timeout", may_retire=True)
        with self.assertRaises(Refusal) as caught:
            self.core.claim(WORK, CLAUDE, operation_id="op-1")
        self.assertIn("deadline passed", str(caught.exception))
        self.assertEqual(self.core.operation_record("op-1")["state"], "retired")
        self.assertIsNone(self.core.assignment_of(WORK))

    def test_a_lying_clock_stops_a_transition_before_the_journal(self):
        # The instant is taken BEFORE the journal is touched, so a clock that
        # answers the wrong shape refuses without leaving an operation row --
        # which would otherwise be a durable record stamped with nonsense.
        self.work()
        self.core._clock = lambda: "banana"
        with self.assertRaises(Refusal):
            self.core.claim(WORK, CLAUDE, operation_id="op-1")
        self.core._clock = lambda: NOW
        self.assertIsNone(self.core.operation_record("op-1"))
        self.assertIsNone(self.core.assignment_of(WORK))
        # And the id is still usable, because an ordinary refusal writes nothing.
        self.assertIsNotNone(self.core.claim(WORK, CLAUDE, operation_id="op-1"))


class TwoKindsOfRefusal(JournalCase):

    def test_an_ordinary_refusal_writes_nothing_and_stays_retryable(self):
        self.work()
        stale = {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                 "participant": CLAUDE, "generation": 9}
        with self.assertRaises(Refusal):
            self.core.end(stale, operation_id="op-1")
        # UNSUBMITTED is the ABSENCE of a row, and an ordinary refusal leaves
        # the identity unsubmitted -- so the same id is usable when the
        # precondition later holds.
        self.assertIsNone(self.core.operation_record("op-1"))
        assignment = self.core.claim(WORK, CLAUDE, operation_id="claim-1")["assignment"]
        answer = self.core.end(assignment, operation_id="op-1")
        self.assertEqual(answer["cause"], "release")
        self.assertEqual(self.core.operation_record("op-1")["state"],
                         "committed")

    def test_a_durable_refusal_keeps_its_writes_and_is_replayed(self):
        # No cut-3 TRANSITION raises a durable refusal -- the stale-target
        # integration that does is cut 4 -- so this exercises the store
        # primitive directly.  The mechanism has to be proved where it lives, or
        # cut 4 arrives on an untested savepoint.
        store = self.authority._core._store
        attempts = []

        def action():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)",
                      f"attempt-{len(attempts)}", "1")
            attempts.append(1)
            raise Refusal("the target moved", durable=True)

        with self.assertRaises(Refusal):
            store.replay("op-1", "sig", action, at=NOW)
        # WHAT IT WROTE SURVIVED, because the refusal itself is a committed
        # outcome, and the refusal is bound to the identity.
        self.assertEqual(len(store.all("SELECT key FROM policy")), 1)
        record = store.operation_record("op-1")
        self.assertEqual(record["state"], "refused")
        self.assertEqual(record["detail"], "the target moved")
        # AND THE RETRY REPLAYS THE REFUSAL rather than appending a second
        # attempt -- which is the whole difference from the ordinary kind.
        with self.assertRaises(Refusal) as caught:
            store.replay("op-1", "sig", action, at=NOW)
        self.assertEqual(str(caught.exception), "the target moved")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(len(store.all("SELECT key FROM policy")), 1)

    def test_an_ordinary_refusal_rolls_back_what_it_wrote(self):
        store = self.authority._core._store

        def action():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)",
                      "partial", "1")
            raise Refusal("no", durable=False)

        with self.assertRaises(Refusal):
            store.replay("op-1", "sig", action, at=NOW)
        self.assertEqual(store.all("SELECT key FROM policy"), [])
        self.assertIsNone(store.operation_record("op-1"))

    def test_a_fault_takes_the_whole_transaction_down_and_records_nothing(self):
        # An operation whose failure we cannot DESCRIBE is not one we may record
        # an outcome for.  So a non-Refusal is not journalled at all, and the
        # identity stays unsubmitted.
        store = self.authority._core._store

        def action():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)",
                      "partial", "1")
            raise RuntimeError("a fault")

        with self.assertRaises(RuntimeError):
            store.replay("op-1", "sig", action, at=NOW)
        self.assertEqual(store.all("SELECT key FROM policy"), [])
        self.assertIsNone(store.operation_record("op-1"))
        # And the store is usable afterwards.
        store.replay("op-2", "sig", lambda: "ok", at=NOW)
        self.assertEqual(store.operation_record("op-2")["result"], "ok")


class FourStates(JournalCase):

    def test_one_identity_is_durably_in_exactly_one_of_four_states(self):
        store = self.authority._core._store
        self.work()
        # UNSUBMITTED is the absence of a row.
        self.assertIsNone(self.core.operation_record("unsubmitted"))
        self.assertIsNone(self.core.operation_result("unsubmitted"))
        # COMMITTED.
        self.core.claim(WORK, CLAUDE, operation_id="committed")
        self.assertEqual(self.core.operation_record("committed")["state"],
                         "committed")
        self.assertIsNotNone(self.core.operation_result("committed"))
        # REFUSED, which exists only when the refusal itself wrote something.
        with self.assertRaises(Refusal):
            store.replay("refused", "sig",
                         lambda: (_ for _ in ()).throw(
                             Refusal("kept", durable=True)), at=NOW)
        self.assertEqual(self.core.operation_record("refused")["state"],
                         "refused")
        # A refused identity has no RESULT: `operation_result` answers only for
        # a committed one, while the RECORD stays readable for the audit.
        self.assertIsNone(self.core.operation_result("refused"))
        # RETIRED.
        self.core.settle_operation("retired", signature="sig",
                                   reason="deadline", disposition="timeout",
                                   may_retire=True)
        self.assertEqual(self.core.operation_record("retired")["state"],
                         "retired")
        self.assertIsNone(self.core.operation_result("retired"))


class Retirement(JournalCase):

    def test_retirement_is_answered_before_the_operands(self):
        # §4 makes retirement a property of the operation IDENTITY rather than
        # of one request's operands.  A stale submitter must learn the identity
        # is DEAD, not that its operands disagree -- those are different facts
        # and only one of them is true.
        self.work()
        self.core.settle_operation("op-1", signature="some-other-signature",
                                   reason="deadline passed",
                                   disposition="timeout", may_retire=True)
        with self.assertRaises(Refusal) as caught:
            self.core.claim(WORK, CLAUDE, operation_id="op-1")
        self.assertIn("deadline passed", str(caught.exception))
        self.assertNotIn("different operands", str(caught.exception))
        # And nothing committed under the dead identity.
        self.assertIsNone(self.core.assignment_of(WORK))

    def test_a_retirement_binds_its_signature_reason_and_disposition(self):
        answer = self.core.settle_operation(
            "op-1", signature="sig", reason="deadline passed",
            disposition="timeout", may_retire=True)
        self.assertEqual(answer, {"kind": "retired",
                                  "record": {"reason": "deadline passed",
                                             "disposition": "timeout"}})
        record = self.core.operation_record("op-1")
        self.assertEqual(record["signature"], "sig")
        self.assertEqual(record["detail"], {"reason": "deadline passed",
                                            "disposition": "timeout"})
        # BINDING THE DISPOSITION is what stops the next caller, arriving on
        # whatever entry path it happens to be on, from relabelling a settlement
        # timeout as a refused claim.  A second settlement observes the first.
        again = self.core.settle_operation("op-1", signature="sig",
                                          reason="other", disposition="other",
                                          may_retire=True)
        self.assertEqual(again["record"]["disposition"], "timeout")

    def test_a_retirement_records_why_and_what_it_causes_or_refuses(self):
        for what, kwargs in [
                ("no reason", {"disposition": "timeout"}),
                ("no disposition", {"reason": "deadline"}),
                ("neither", {})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.settle_operation("op-1", signature="sig",
                                               may_retire=True, **kwargs)
        self.assertIsNone(self.core.operation_record("op-1"))


class Settlement(JournalCase):

    def test_settlement_authority_is_asserted_and_never_inherited(self):
        # The frozen host defaulted `may_retire` to true, so OMITTING the
        # operand retired an unsubmitted claim on the spot.  Retirement kills a
        # live authorization, so a caller with no positive evidence that the
        # operation is over -- a timeout before its deadline -- may only OBSERVE.
        answer = self.core.settle_operation("op-1", signature="sig")
        self.assertEqual(answer, {"kind": "live", "record": None})
        self.assertIsNone(self.core.operation_record("op-1"))
        # And the identity is still usable, which is the point of observing.
        self.work()
        self.core.claim(WORK, CLAUDE,
                        operation_id="op-2")
        for what, value in [("a string", "yes"), ("a number", 1),
                            ("none", None)]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.settle_operation("op-3", signature="sig",
                                               may_retire=value)

    def test_a_committed_operation_always_wins_the_settlement_race(self):
        self.work()
        # W16823: the settlement answers with the COMMITTED RESULT, whole.
        assignment = self.core.claim(WORK, CLAUDE, operation_id="op-1")
        answer = self.core.settle_operation(
            "op-1", signature=claim_signature(WORK, CLAUDE),
            reason="deadline", disposition="timeout", may_retire=True)
        # A read that says "not committed" proves only its own instant, so this
        # is not lookup-then-write: the re-read INSIDE the settlement finds
        # anything that committed while the lookup was in flight.
        self.assertEqual(answer, {"kind": "committed", "result": assignment})
        self.assertEqual(self.core.operation_record("op-1")["state"],
                         "committed")

    def test_a_settlement_of_different_operands_fails_closed(self):
        # An id alone proves only that SOMETHING committed under it, so a record
        # with different operands is a COLLISION: it adopts nothing and
        # overwrites nothing.
        self.work()
        self.core.claim(WORK, CLAUDE, operation_id="op-1")
        with self.assertRaises(Refusal) as caught:
            self.core.settle_operation("op-1", signature="a-different-thing",
                                       reason="deadline",
                                       disposition="timeout", may_retire=True)
        self.assertIn("different operands", str(caught.exception))
        record = self.core.operation_record("op-1")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["signature"], claim_signature(WORK, CLAUDE))

    def test_an_unanswerable_lookup_settles_nothing(self):
        # "I could not ask" must never be read as "it did not commit".  A
        # settlement that proceeded on an unanswerable lookup would retire a
        # live authorization on no evidence at all.
        self.core.set_lookup_available(False)
        with self.assertRaises(Refusal) as caught:
            self.core.settle_operation("op-1", signature="sig",
                                       reason="deadline",
                                       disposition="timeout", may_retire=True)
        self.assertIn("unavailable", str(caught.exception))
        self.assertIsNone(self.core.operation_record("op-1"))
        with self.assertRaises(Refusal):
            self.core.operation_result("op-1")
        self.core.set_lookup_available(True)
        self.assertIsNone(self.core.operation_result("op-1"))
        self.assertEqual(
            self.core.settle_operation("op-1", signature="sig",
                                       reason="deadline",
                                       disposition="timeout",
                                       may_retire=True)["kind"], "retired")


    def test_the_authority_settles_the_largest_signature_it_can_produce(self):
        """Cut 3 raised the settlement-signature cap; this is its measurement.

        The ruling was: no settlement-only length limit, because settlement must
        compare the EXACT canonical signature the authority itself produced and
        the contract carries no system-wide text bound.  That was reasoning; this
        is the number.

        A legitimate `activity` idempotency key of 100,000 characters is accepted
        and journalled, and the signature the authority derives from it is
        100,185 characters long.  So a settlement cap anywhere below that refuses
        a settlement of an operation THE AUTHORITY COMMITTED -- which is worse
        than the unbounded operand, because the caller could no longer settle an
        identity it can no longer submit under either.

        The bound therefore does not belong here.  It belongs on durable text
        system-wide, where the same 100,000 characters entered in the first
        place, and that is the broader operand ruling this points at.
        """
        self.work()
        assignment = self.core.claim(WORK, CLAUDE, operation_id="op-1")["assignment"]
        key = "k" * 100_000
        self.core.activity(assignment, key=key)
        signature = signature_of("activity", {"expect": assignment, "key": key})
        self.assertGreater(len(signature), 100_000)
        # The authority produced it, so the authority settles it: a cap below
        # this length would fail this exact call.
        answer = self.core.settle_operation("op-2", signature=signature)
        self.assertEqual(answer, {"kind": "live", "record": None})
        # And the collision rule still holds at that size -- one character of
        # difference in a 100,185-character signature is still different
        # operands, so length is not what makes the comparison work.
        with self.assertRaises(Refusal) as caught:
            self.core.settle_operation(
                "op-1", signature=signature, reason="deadline",
                disposition="timeout", may_retire=True)
        self.assertIn("different operands", str(caught.exception))


class Restart(JournalCase):

    def reopen(self):
        self.authority.dispose()
        self.authority = Authority.open(self.path,
                                        expected_authority_uuid=UUID,
                                        clock=lambda: NOW)
        self.core = self.authority._core
        return self.authority

    def test_a_restart_before_the_claim_leaves_it_claimable(self):
        self.work()
        self.reopen()
        self.assertTrue(self.core.project_work(WORK)["ready"])
        assignment = self.core.claim(WORK, CLAUDE, operation_id="op-1")["assignment"]
        self.assertEqual(assignment["generation"], 1)

    def test_a_restart_after_the_claim_replays_it_rather_than_repeating(self):
        self.work()
        # W16823: the whole result survives the restart, decision included.
        first = self.core.claim(WORK, CLAUDE, operation_id="op-1")
        self.reopen()
        self.assertEqual(self.core.claim(WORK, CLAUDE, operation_id="op-1"),
                         first)
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed"])
        self.assertEqual(self.core.project_work(WORK)["generation_counter"], 1)

    def test_everything_the_journal_holds_survives_a_restart(self):
        store = self.authority._core._store
        self.work()
        self.authority.certify_contract(V12, "reference")
        assignment = self.core.claim(WORK, CLAUDE, operation_id="claim-1")["assignment"]
        self.core.cancel(assignment, operation_id="cancel-1", reason="lost")
        self.core.settle_operation("retired-1", signature="sig",
                                   reason="deadline", disposition="timeout",
                                   may_retire=True)
        with self.assertRaises(Refusal):
            store.replay("refused-1", "sig",
                         lambda: (_ for _ in ()).throw(
                             Refusal("kept", durable=True)), at=NOW)
        self.reopen()
        # Fences, gates, contracts, retirements, refusals and events.
        self.assertEqual(self.core.fenced_generations(WORK), [1])
        self.assertEqual(self.core.project_work(WORK)["gate"]["kind"],
                         GATE_QUIESCENCE)
        self.assertTrue(self.authority.is_certified(V12))
        self.assertEqual(self.core.operation_record("retired-1")["state"],
                         "retired")
        self.assertEqual(self.core.operation_record("refused-1")["state"],
                         "refused")
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed", "cancelled"])
        self.core.assert_invariants(WORK)

    def test_two_works_keep_separate_journals_and_separate_state(self):
        self.work(WORK)
        self.work(OTHER)
        self.core.add_route_handler(ROUTE, GEMINI)
        one = self.core.claim(WORK, CLAUDE, operation_id="op-1")
        two = self.core.claim(OTHER, GEMINI, operation_id="op-2")
        self.core.cancel(one["assignment"], operation_id="op-3",
                         reason="lost")
        self.reopen()
        self.assertEqual(self.core.fenced_generations(WORK), [1])
        self.assertEqual(self.core.fenced_generations(OTHER), [])
        self.assertEqual(self.core.assignment_of(OTHER), two["assignment"])
        self.assertIsNone(self.core.assignment_of(WORK))
        self.assertEqual(self.core.operation_record("op-1")["result"], one)
        self.assertEqual(self.core.operation_record("op-2")["result"], two)


CHILD = textwrap.dedent('''
    import json, os, sys, time
    # NO sys.path SURGERY.  Review [P2]: both child scripts unconditionally
    # prepended the repository `src`, so under the INSTALLED gate the children
    # ran source code while the parent used the wheel -- and a packaging skew in
    # claim, replay or settlement would have passed the gate that claims to
    # exercise the whole installed layout.  The child inherits the gate's own
    # import path (`PYTHONPATH=src` for the source stage, empty plus the venv
    # interpreter for the installed one) and REPORTS where it imported from, so
    # the parent can check that they agree.
    from baton_v12.authority import Authority, Refusal
    import baton_v12.authority as package
    path, role, operation_id, participant = sys.argv[1:5]
    report = {"role": role, "participant": participant,
              "origin": os.path.dirname(os.path.abspath(package.__file__))}
    try:
        authority = Authority.open(path, clock=lambda: "2026-08-24T05:00:00.000Z")
        try:
            core = authority._core
            # A REAL barrier, not a head start.  Each child announces that it
            # is loaded and connected, and only when the parent has seen every
            # one of them does it release them together -- otherwise the
            # children merely start at different times and the "race" is a
            # sequence with extra steps.
            open(path + ".ready." + role, "wb").close()
            start = path + ".start"
            while not os.path.exists(start):
                time.sleep(0.001)
            answer = core.claim("0123abcd-W7", participant,
                                operation_id=operation_id)
            report["outcome"] = "claimed"
            # W16823: the closed result, and the child reports the FENCE'S
            # generation out of it.
            report["generation"] = answer["assignment"]["generation"]
        finally:
            authority.dispose()
    except Refusal as refusal:
        report["outcome"] = "refused"
        report["why"] = str(refusal)
    except BaseException as failure:
        report["outcome"] = "faulted"
        report["why"] = f"{type(failure).__name__}: {failure}"
    print(json.dumps(report))
''')


class RealProcessRaces(JournalCase):
    """Spawned processes against one store file.

    A competing claim must lose by being REFUSED inside a transaction, which is
    a decision, not by failing to get a transaction at all, which is an error.
    Two threads in one interpreter would share a connection and prove neither.
    """

    def race(self, children, script=CHILD):
        source = script
        script = os.path.join(self.root, "child.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(source)
        self.authority.dispose()
        # `sys.executable` and the inherited environment together decide which
        # package the child imports: the source gate exports `PYTHONPATH=src`,
        # and the installed gate exports an empty one and runs the venv
        # interpreter.  The child is told the store path and nothing about
        # imports.
        running = [
            subprocess.Popen(
                [sys.executable, script, self.path, role, operation_id,
                 participant],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for role, operation_id, participant in children]
        # Wait for EVERY child to be loaded and connected, then release them
        # together.  A barrier the parent trips before the children arrive is
        # not a barrier.
        deadline = time.monotonic() + 60
        expected = {role for role, _op, _who in children}
        while True:
            ready = {name.rsplit(".", 1)[-1] for name in os.listdir(self.root)
                     if ".ready." in name}
            if expected <= ready:
                break
            if time.monotonic() > deadline:
                for child in running:
                    child.kill()
                self.fail(f"children never reached the barrier: {ready}")
            time.sleep(0.001)
        open(self.path + ".start", "wb").close()
        reports = []
        for child in running:
            out, err = child.communicate(timeout=60)
            self.assertEqual(child.returncode, 0, err)
            reports.append(json.loads(out.strip().splitlines()[-1]))
        self.authority = Authority.open(self.path,
                                        expected_authority_uuid=UUID,
                                        clock=lambda: NOW)
        self.core = self.authority._core
        # THE CHILDREN MUST HAVE RUN THE SAME PACKAGE AS THIS PARENT.  Without
        # this, the installed gate's race cases prove something about the source
        # tree while claiming to prove something about the wheel.
        import baton_v12.authority as package
        parent = os.path.dirname(os.path.abspath(package.__file__))
        for report in reports:
            self.assertEqual(report.get("origin"), parent,
                             f"child {report.get('role')} imported "
                             f"{report.get('origin')}, parent uses {parent}")
        return reports

    def test_competing_claims_produce_one_winner_and_reasoned_losers(self):
        self.work(WORK, handlers=(CLAUDE, GEMINI, "baton.slaw"))
        reports = self.race([("a", "op-a", CLAUDE),
                             ("b", "op-b", GEMINI),
                             ("c", "op-c", "baton.slaw")])
        outcomes = sorted(report["outcome"] for report in reports)
        # The child reports are the diagnostic: a faulted child would say so
        # here rather than hiding inside a count.
        self.assertNotIn("faulted", outcomes, reports)
        self.assertEqual(outcomes.count("claimed"), 1, reports)
        self.assertEqual(outcomes.count("refused"), 2, reports)
        winner = next(r for r in reports if r["outcome"] == "claimed")
        self.assertEqual(winner["generation"], 1)
        self.assertEqual(self.core.assignment_of(WORK)["participant"],
                         winner["participant"])
        # THE LOSERS LOST BY DECISION.  Every refusal names a reason, and none
        # of them is a database-busy error.
        for report in reports:
            if report["outcome"] == "refused":
                self.assertIn("claim", report["why"].lower(), report)
                self.assertNotIn("locked", report["why"].lower(), report)
        self.core.assert_invariants(WORK)

    def test_one_fixed_operation_id_across_processes_commits_once(self):
        self.work(WORK, handlers=(CLAUDE,))
        reports = self.race([("a", "fixed-op", CLAUDE),
                             ("b", "fixed-op", CLAUDE),
                             ("c", "fixed-op", CLAUDE)])
        self.assertNotIn("faulted", [r["outcome"] for r in reports], reports)
        # ALL THREE SUCCEED, and that is the point: the same operation with the
        # same operands is effectively-once, so the later arrivals REPLAY the
        # first outcome rather than being refused for a race they did not lose.
        self.assertEqual([r["outcome"] for r in reports],
                         ["claimed", "claimed", "claimed"], reports)
        self.assertEqual({r["generation"] for r in reports}, {1}, reports)
        # And exactly one claim happened.
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed"])
        self.assertEqual(self.core.project_work(WORK)["generation_counter"], 1)
        self.core.assert_invariants(WORK)


SETTLER = textwrap.dedent('''
    import json, os, sys, time
    # NO sys.path SURGERY, for the reason above.
    from baton_v12.authority import Authority, Refusal, claim_signature
    import baton_v12.authority as package
    path, role, operation_id, participant = sys.argv[1:5]
    report = {"role": role,
              "origin": os.path.dirname(os.path.abspath(package.__file__))}
    try:
        authority = Authority.open(path, clock=lambda: "2026-08-24T05:00:00.000Z")
        try:
            core = authority._core
            open(path + ".ready." + role, "wb").close()
            while not os.path.exists(path + ".start"):
                time.sleep(0.001)
            if role == "claimer":
                answer = core.claim("0123abcd-W7", participant,
                                    operation_id=operation_id)
                report["outcome"] = "claimed"
                report["generation"] = answer["assignment"]["generation"]
            else:
                answer = core.settle_operation(
                    operation_id,
                    signature=claim_signature("0123abcd-W7", participant),
                    reason="deadline", disposition="timeout", may_retire=True)
                report["outcome"] = "settled"
                report["kind"] = answer["kind"]
        finally:
            authority.dispose()
    except Refusal as refusal:
        report["outcome"] = "refused"
        report["why"] = str(refusal)
    except BaseException as failure:
        report["outcome"] = "faulted"
        report["why"] = f"{type(failure).__name__}: {failure}"
    print(json.dumps(report))
''')


class SettlementRace(RealProcessRaces):

    def test_a_claim_and_a_settlement_agree_on_one_story(self):
        # The two orders are BOTH correct, and what must never happen is a
        # third: a retired identity whose claim also committed, or a committed
        # claim the settlement then buried.  Whichever wins the write lock, the
        # durable state has to tell ONE story.
        self.work(WORK, handlers=(CLAUDE,))
        reports = self.race([("claimer", "op-1", CLAUDE),
                             ("settler", "op-1", CLAUDE)], script=SETTLER)
        self.assertNotIn("faulted", [r["outcome"] for r in reports], reports)
        record = self.core.operation_record("op-1")
        self.assertIn(record["state"], ("committed", "retired"), reports)
        claimer = next(r for r in reports if r["role"] == "claimer")
        settler = next(r for r in reports if r["role"] == "settler")
        if record["state"] == "committed":
            # The claim got there first, so the settlement OBSERVED it -- a
            # committed operation always wins the settlement race.
            self.assertEqual(claimer["outcome"], "claimed", reports)
            self.assertEqual(settler["kind"], "committed", reports)
            self.assertEqual(self.core.assignment_of(WORK)["participant"],
                             CLAUDE)
        else:
            # The settlement got there first, so the identity was dead by the
            # time the claim arrived and NOTHING committed under it.
            self.assertEqual(settler["kind"], "retired", reports)
            self.assertEqual(claimer["outcome"], "refused", reports)
            self.assertIsNone(self.core.assignment_of(WORK))
            self.assertEqual(
                [event["cause"] for event in self.core.assignment_events(WORK)],
                [])
        self.core.assert_invariants(WORK)


if __name__ == "__main__":
    unittest.main()
