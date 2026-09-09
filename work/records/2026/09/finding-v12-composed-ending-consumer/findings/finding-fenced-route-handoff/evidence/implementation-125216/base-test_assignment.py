"""W2845 cut 2 — the generation-bearing claim, the deployment-wide slot, and
every Handler-clear path.

Ported from the frozen Node authority's assignment catalog by OBLIGATION.  The
obligations are §4's full four-part identity, §10.1's never-reused generation
counter, §10.2's one live claim per participant across the whole deployment, and
the ruling that cancellation fences the exact generation AND ends the assignment
in one transaction.

WHAT CUT 2 DOES NOT COVER, on purpose: the operation journal, replay,
retirement, settlement and real-process races.  Those are cut 3, and the
transitions here take no `operation_id` -- accepting one before the journal
exists would be an operand with no mechanism behind it.
"""

import os
import sqlite3
import tempfile
import unittest

from baton_v12.authority import Authority, Refusal, V11, V12
from baton_v12.authority.core import (CAPABILITIES, Core, RELEASE_DISPOSITIONS,
                                      UNCLAIMED_PHASES)
from baton_v12.authority.identity import (GATE_PLAN_REVISION, GATE_QUIESCENCE,
                                          MAX_SAFE_INTEGER, gate_token)

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
GEMINI = "baton.gemini"
ROUTE = "impl"

# A deterministic clock, so an event's instant is a FACT of the test rather than
# of when it ran.  It is a bootstrap operand precisely so this is possible.
NOW = "2026-08-24T04:00:00.000Z"


class AuthorityCase(unittest.TestCase):
    """Every store and root is owned by its fixture and cleaned by it."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-authority-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        # `Core` is PRIVATE implementation.  Cut 2 drives it directly because
        # the participant-bound session that will expose the enumerated subset
        # of it is cut 5; testing it from the package's own tests is not the
        # same as exposing it.
        self.core = self.authority._core

    def work(self, work_id=WORK, *, contract=V12, route=ROUTE, phase="queued",
             gate=None, handlers=(CLAUDE,)):
        self.core.create_work(work_id, route, contract=contract, phase=phase, operation_id=("create-" + str(work_id))[:160],
                              gate=gate)
        for participant in handlers:
            self.core.add_route_handler(route, participant)
        return work_id

    def op(self, label="op"):
        """A fresh operation id.  Cut 3 requires one on every transition."""
        self._ops = getattr(self, "_ops", 0) + 1
        return f"{label}-{self._ops}"

    def claimed(self, work_id=WORK, participant=CLAUDE, **kwargs):
        self.work(work_id, **kwargs)
        # W16823: the claim answers a CLOSED RESULT now -- assignment, exact
        # claim event and the decision it was authorized under.  This fixture's
        # callers want the FENCE, so it names the member rather than every
        # caller learning the result's shape.
        return self.core.claim(
            work_id, participant,
            operation_id=self.op("claim"))["assignment"]


class Creation(AuthorityCase):

    def test_a_work_is_created_unclaimed(self):
        projected = self.core.create_work(WORK, ROUTE, contract=V12, operation_id=("create-" + str(WORK))[:160])
        self.assertEqual(projected["work_id"], WORK)
        self.assertEqual(projected["phase"], "queued")
        self.assertIsNone(projected["handler"])
        self.assertIsNone(projected["assignment"])
        self.assertEqual(projected["generation_counter"], 0)
        self.assertTrue(projected["ready"])
        self.core.assert_invariants(WORK)

    def test_active_is_not_a_phase_a_work_can_be_created_in(self):
        # The frozen host accepted `phase="active"` and committed a
        # Handler-null active row, which its invariant check then reported after
        # the corruption was already durable.  INVARIANTS ARE A BACKSTOP; the
        # transition is where an impossible state is refused.
        with self.assertRaises(Refusal):
            self.core.create_work(WORK, ROUTE, phase="active", operation_id=("create-" + str(WORK))[:160])
        # And the refusal wrote nothing, so the id is still free.
        self.assertEqual(sorted(UNCLAIMED_PHASES), ["block", "parked", "queued"])
        self.core.create_work(WORK, ROUTE, phase="queued", operation_id=("create-" + str(WORK))[:160])

    def test_a_gate_and_a_phase_are_one_cross_product(self):
        # A gate is a REASON the Work cannot run, so a gate without `block` and
        # a `block` without a gate are both states nobody can act on or explain.
        for what, phase, gate in [
                ("block with no gate", "block", None),
                ("a gate outside block", "queued",
                 gate_token(GATE_QUIESCENCE, "1")),
                ("an untyped gate", "block", "just-a-string"),
                ("an unknown gate kind", "block", "invented:1"),
                ("a gate with no detail", "block", f"{GATE_QUIESCENCE}:"),
                ("an unknown phase", "invented", None)]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    named = f"0123abcd-W{abs(hash(what)) % 900 + 99}"
                    self.core.create_work(named, ROUTE, phase=phase,
                                          gate=gate,
                                          operation_id=("create-" + named)[:160])
        # And the pairing that IS coherent is accepted.
        projected = self.core.create_work(
            WORK, ROUTE, phase="block", gate=gate_token(GATE_QUIESCENCE, "1"),
            operation_id=("create-" + WORK)[:160])
        self.assertEqual(projected["gate"],
                         {"token": f"{GATE_QUIESCENCE}:1",
                          "kind": GATE_QUIESCENCE, "detail": "1"})
        self.assertFalse(projected["ready"])

    def test_one_work_id_is_created_once(self):
        self.core.create_work(WORK, ROUTE, operation_id=("create-" + str(WORK))[:160])
        with self.assertRaises(Refusal):
            self.core.create_work(WORK, "other-route", operation_id=("create-" + str(WORK))[:160])
        self.assertEqual(self.core.project_work(WORK)["route"], ROUTE)


class Claiming(AuthorityCase):

    def test_the_first_v12_generation_is_one_and_the_counter_never_reuses(self):
        # §10.1: the counter is never decremented or reused.  Three claims of
        # one Work mint 1, 2, 3 -- and the ended generations stay ended.
        self.work()
        seen = []
        for _ in range(3):
            assignment = self.core.claim(
                WORK, CLAUDE, operation_id=self.op())["assignment"]
            seen.append(assignment["generation"])
            self.core.end(assignment, operation_id=self.op())
        self.assertEqual(seen, [1, 2, 3])
        self.assertEqual(self.core.project_work(WORK)["generation_counter"], 3)

    def test_a_v11_claim_mints_no_generation(self):
        self.work(contract=V11)
        assignment = self.core.claim(
            WORK, CLAUDE, operation_id=self.op())["assignment"]
        self.assertIsNone(assignment["generation"])
        self.assertEqual(self.core.project_work(WORK)["generation_counter"], 0)
        self.core.assert_invariants(WORK)

    def test_the_assignment_is_the_full_four_part_identity(self):
        assignment = self.claimed()
        self.assertEqual(assignment, {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": CLAUDE, "generation": 1})
        # A projection carries the same identity and never a bare participant.
        self.assertEqual(self.core.project_work(WORK)["assignment"], assignment)

    def test_a_claim_is_refused_for_every_reason_it_should_be(self):
        self.work(handlers=(CLAUDE,))
        for what, prepare, participant in [
                ("a route that does not resolve to them", lambda: None, GEMINI),
                ("a Work already claimed",
                 lambda: self.core.claim(WORK, CLAUDE, operation_id=self.op()), CLAUDE)]:
            with self.subTest(what=what):
                prepare()
                with self.assertRaises(Refusal):
                    self.core.claim(WORK, participant, operation_id=self.op())

    def test_blocked_and_parked_work_cannot_be_claimed(self):
        for what, phase, gate in [
                ("blocked", "block", gate_token(GATE_QUIESCENCE, "1")),
                ("parked", "parked", None)]:
            with self.subTest(what=what):
                work_id = f"0123abcd-W{10 + len(what)}"
                self.work(work_id, phase=phase, gate=gate)
                with self.assertRaises(Refusal):
                    self.core.claim(work_id, CLAUDE, operation_id=self.op())
                self.assertIsNone(self.core.assignment_of(work_id))

    def test_one_participant_holds_one_claim_across_the_whole_deployment(self):
        # §10.2.  The slot is keyed by PARTICIPANT, not by Work: making it per
        # Work is the bug the table shape forbids.
        self.work(WORK)
        self.work(OTHER)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(self.core.slot_holder(CLAUDE), WORK)
        with self.assertRaises(Refusal):
            self.core.claim(OTHER, CLAUDE, operation_id=self.op())
        # The second Work is untouched -- the refusal happened inside the
        # transaction, so nothing about it moved.
        self.assertIsNone(self.core.assignment_of(OTHER))
        self.core.assert_invariants(OTHER)
        # And another participant is unaffected: the limit is per participant.
        self.core.add_route_handler(ROUTE, GEMINI)
        self.core.claim(OTHER, GEMINI, operation_id=self.op())
        self.assertEqual(self.core.slot_holder(GEMINI), OTHER)

    def test_capacity_is_checked_inside_the_transaction(self):
        # Checking it only where an offer was issued would make it ADVISORY,
        # and an advisory limit on live claims is not a limit.  Proof: the slot
        # row is written by the same transaction as the Handler, so a Work whose
        # claim was refused for capacity holds no slot and has no Handler.
        self.work(WORK)
        self.work(OTHER)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        with self.assertRaises(Refusal):
            self.core.claim(OTHER, CLAUDE, operation_id=self.op())
        connection = sqlite3.connect(self.path)
        slots = connection.execute(
            "SELECT participant, work_id FROM claim_slot").fetchall()
        connection.close()
        self.assertEqual(slots, [(CLAUDE, WORK)])


class EndingAnAssignment(AuthorityCase):

    def test_every_handler_clear_path_goes_through_one_helper(self):
        # The catalog obligation: EVERY Handler-clear path.  Each row ends the
        # assignment, clears the Handler and the live generation, frees the
        # deployment-wide slot, and appends exactly one event naming the cause.
        paths = [
            ("release", lambda a: self.core.end(a, operation_id=self.op()), "queued", None, False),
            ("recovered",
             lambda a: self.core.end(a, disposition="recovered", operation_id=self.op()), "queued",
             None, False),
            ("pass", lambda a: self.core.pass_work(a, to_route="rview", operation_id=self.op()),
             "queued", None, False),
            ("cancelled", lambda a: self.core.cancel(a, reason="lost", operation_id=self.op()),
             "block", f"{GATE_QUIESCENCE}:1", True),
            ("plan-rejected",
             lambda a: self.core.reject_plan(a, plan_digest="sha256:plan", operation_id=self.op()),
             "block", f"{GATE_PLAN_REVISION}:sha256:plan", False),
            ("gate-arrival",
             lambda a: self.core.install_gate(
                 a["work_ref"]["work_id"],
                 gate=gate_token(GATE_QUIESCENCE, "9"), expect=a, operation_id=self.op()),
             "block", f"{GATE_QUIESCENCE}:9", False),
        ]
        for index, (cause, ending, phase, gate, fenced) in enumerate(paths):
            with self.subTest(cause=cause):
                work_id = f"0123abcd-W{100 + index}"
                assignment = self.claimed(work_id)
                answer = ending(assignment)
                self.assertEqual(answer["cause"], cause)
                projected = self.core.project_work(work_id)
                self.assertIsNone(projected["handler"])
                self.assertIsNone(projected["live_generation"])
                self.assertIsNone(projected["assignment"])
                self.assertEqual(projected["phase"], phase)
                self.assertEqual(
                    None if projected["gate"] is None
                    else projected["gate"]["token"], gate)
                self.assertIsNone(self.core.slot_holder(CLAUDE))
                # THE HISTORY IS THE WHOLE LIFE: claimed, then ended.  W151's
                # transition table requires the claim event, and without it the
                # journal said who lost the Work and never who took it.
                events = self.core.assignment_events(work_id)
                self.assertEqual([event["cause"] for event in events],
                                 ["claimed", cause])
                # And EVERY event carries the full four-part identity, not
                # three quarters of one in separate columns.
                for event in events:
                    self.assertEqual(event["assignment_ref"], {
                        "work_ref": {"authority_uuid": UUID,
                                     "work_id": work_id},
                        "participant": CLAUDE, "generation": 1})
                    self.assertEqual(event["at"], NOW)
                self.assertIs(events[0]["fenced"], False)
                self.assertIs(events[1]["fenced"], fenced)
                self.assertEqual(events[0]["phase"], "active")
                self.assertEqual(events[1]["phase"], phase)
                # THE COUNTER IS NEVER CHANGED BY AN ENDING.  Only `claim`
                # mints, and §10.1 says the counter is never decremented.
                self.assertEqual(projected["generation_counter"], 1)
                self.core.assert_invariants(work_id)

    def test_an_ending_needs_the_exact_identity(self):
        assignment = self.claimed()
        for what, expected in [
                ("no assignment at all", None),
                ("a later generation",
                 {**assignment, "generation": assignment["generation"] + 1}),
                ("another participant",
                 {**assignment, "participant": GEMINI}),
                ("another Work",
                 {"work_ref": {"authority_uuid": UUID, "work_id": OTHER},
                  "participant": CLAUDE, "generation": 1}),
                ("another authority",
                 {"work_ref": {"authority_uuid": "f" * 32, "work_id": WORK},
                  "participant": CLAUDE, "generation": 1})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.end(expected, operation_id=self.op())
        # AND THE CALLER IS TOLD WHICH FACT APPLIES.  A foreign authority is a
        # different mistake from a stale generation, and "stale" would send
        # somebody to re-read state that was never the problem.  Asserted
        # because otherwise the specific refusal is indistinguishable from the
        # generic one and can be deleted without any case noticing.
        with self.assertRaises(Refusal) as caught:
            self.core.end({"work_ref": {"authority_uuid": "f" * 32,
                                        "work_id": WORK},
                           "participant": CLAUDE, "generation": 1}, operation_id=self.op())
        self.assertIn("authority", str(caught.exception))
        # The live assignment survived every one of them.
        self.assertEqual(self.core.assignment_of(WORK), assignment)

    def test_a_stale_same_participant_successor_is_still_stale(self):
        # §8 exists because participant equality is insufficient: the same
        # participant may release generation 1 and immediately claim
        # generation 2, and the FIRST assignment is stale even though the
        # participant is identical.
        first = self.claimed()
        self.core.end(first, operation_id=self.op())
        second = self.core.claim(
            WORK, CLAUDE, operation_id=self.op())["assignment"]
        self.assertEqual(second["generation"], 2)
        with self.assertRaises(Refusal) as caught:
            self.core.end(first, operation_id=self.op())
        self.assertIn("stale", str(caught.exception))
        self.assertEqual(self.core.assignment_of(WORK), second)

    def test_a_fenced_generation_is_told_so_rather_than_told_it_is_stale(self):
        # "Stale assignment" and "your generation was ended and fenced" are
        # different facts, and a late worker deserves the one that applies:
        # the second means the assignment is gone for good, not that it lost a
        # race it might win on retry.
        assignment = self.claimed()
        self.core.cancel(assignment, reason="lost the runtime", operation_id=self.op())
        with self.assertRaises(Refusal) as caught:
            self.core.end(assignment, operation_id=self.op())
        self.assertIn("fenced", str(caught.exception))
        self.assertEqual(self.core.fenced_generations(WORK), [1])

    def test_a_release_derives_its_own_outcome(self):
        # The frozen host took caller-supplied `phase` and `gate` here, so
        # `end(..., phase="active")` committed a Handler-null active row through
        # the public boundary.  There is no operand to supply now, which is a
        # stronger statement than validating one.
        assignment = self.claimed()
        with self.assertRaises(TypeError):
            self.core.end(assignment, phase="active", operation_id=self.op())
        self.assertEqual(sorted(RELEASE_DISPOSITIONS), ["recovered", "release"])
        for disposition in ("cancelled", "plan-rejected", "pass", "", None):
            with self.subTest(disposition=disposition):
                with self.assertRaises(Refusal):
                    self.core.end(assignment, disposition=disposition, operation_id=self.op())
        self.assertEqual(self.core.assignment_of(WORK), assignment)

    def test_a_pass_moves_the_route_and_ends_the_assignment_together(self):
        assignment = self.claimed()
        answer = self.core.pass_work(assignment, to_route="rview",
                                     comment="over to you", operation_id=self.op())
        self.assertEqual(answer["route"], "rview")
        projected = self.core.project_work(WORK)
        self.assertEqual(projected["route"], "rview")
        self.assertIsNone(projected["handler"])
        # And the route move is not committed when the ending refuses, because
        # both are one transaction.
        self.core.add_route_handler("rview", CLAUDE)
        second = self.core.claim(
            WORK, CLAUDE, operation_id=self.op())["assignment"]
        with self.assertRaises(Refusal):
            self.core.pass_work(assignment, to_route="somewhere-else", operation_id=self.op())
        self.assertEqual(self.core.project_work(WORK)["route"], "rview")
        self.assertEqual(self.core.assignment_of(WORK), second)


class Cancellation(AuthorityCase):

    def test_the_fence_and_the_ending_are_one_transaction(self):
        assignment = self.claimed()
        answer = self.core.cancel(assignment, reason="runtime lost", operation_id=self.op())
        self.assertTrue(answer["fenced"])
        self.assertEqual(answer["gate"], f"{GATE_QUIESCENCE}:1")
        # The fence, the ending, the freed slot and the gate all landed.
        self.assertEqual(self.core.fenced_generations(WORK), [1])
        self.assertIsNone(self.core.assignment_of(WORK))
        self.assertIsNone(self.core.slot_holder(CLAUDE))
        self.assertEqual(self.core.project_work(WORK)["gate"]["kind"],
                         GATE_QUIESCENCE)
        self.core.assert_invariants(WORK)

    def test_the_slot_is_freed_immediately_and_only_the_replacement_waits(self):
        # The participant's one global claim slot is freed at once, so they can
        # work elsewhere; it is the REPLACEMENT on this Work that waits, behind
        # the typed gate the cancellation installed.
        self.work(WORK)
        self.work(OTHER)
        assignment = self.core.claim(
            WORK, CLAUDE, operation_id=self.op())["assignment"]
        self.core.cancel(assignment, reason="lost", operation_id=self.op())
        self.assertIsNone(self.core.slot_holder(CLAUDE))
        self.core.claim(OTHER, CLAUDE, operation_id=self.op())
        self.assertEqual(self.core.slot_holder(CLAUDE), OTHER)
        with self.assertRaises(Refusal):
            self.core.claim(WORK, GEMINI, operation_id=self.op())

    def test_a_v11_assignment_cannot_be_cancelled(self):
        # Under v11 there is no generation, so "fence the exact generation AND
        # end the assignment" would fence nothing and install a gate naming no
        # generation.  HALF A GUARANTEE SPELLED LIKE A WHOLE ONE IS WORSE THAN A
        # REFUSAL.
        assignment = self.claimed(contract=V11)
        self.assertIsNone(assignment["generation"])
        with self.assertRaises(Refusal) as caught:
            self.core.cancel(assignment, reason="lost", operation_id=self.op())
        self.assertIn("v12", str(caught.exception))
        # Nothing moved: no fence, no gate, and the assignment is still live.
        self.assertEqual(self.core.fenced_generations(WORK), [])
        self.assertIsNone(self.core.project_work(WORK)["gate"])
        self.assertEqual(self.core.assignment_of(WORK), assignment)


class Gates(AuthorityCase):

    def test_a_gate_arrival_on_unclaimed_work_ends_nothing(self):
        self.work()
        answer = self.core.install_gate(
            WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op(), reason="waiting")
        self.assertIsNone(answer["assignment"])
        self.assertEqual(self.core.project_work(WORK)["phase"], "block")
        # Nothing was ever claimed, so there is no assignment history at all.
        self.assertEqual(self.core.assignment_events(WORK), [])

    def test_a_gate_arrival_over_a_live_assignment_must_name_it(self):
        # A scheduler event that silently discarded a live assignment is
        # precisely the uncentralized ending this contract exists to prevent.
        assignment = self.claimed()
        with self.assertRaises(Refusal) as caught:
            self.core.install_gate(WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op())
        # The message is the point: "name the exact assignment" tells the caller
        # what to do, and the generic "an assignment identity is a document"
        # that the inner compare-and-swap would produce does not.
        self.assertIn("live assignment", str(caught.exception))
        self.assertEqual(self.core.assignment_of(WORK), assignment)
        # And the MISSING operand is not the null one: asserting "there is no
        # assignment" when there is one is a different mistake and gets a
        # different answer, not a silent ending.
        with self.assertRaises(Refusal):
            self.core.install_gate(WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op(),
                                   expect=None)
        self.assertEqual(self.core.assignment_of(WORK), assignment)

    def test_an_unreachable_runtime_is_not_a_dead_one(self):
        # §10.8.  Only POSITIVE absence, or an explicitly pinned
        # certified-isolation clause, releases the replacement.
        assignment = self.claimed()
        self.core.cancel(assignment, reason="lost", operation_id=self.op())
        gate = f"{GATE_QUIESCENCE}:1"
        for what, evidence in [
                ("silence", {}),
                ("an unreachable runtime", {"kind": "runtime-unreachable"}),
                ("absence naming no runtime", {"kind": "runtime-absent"}),
                ("absence naming an empty runtime",
                 {"kind": "runtime-absent", "runtime": ""}),
                ("an uncertified isolation claim",
                 {"kind": "certified-isolation-policy", "policy": "p"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence=evidence, operation_id=self.op())
                self.assertEqual(self.core.project_work(WORK)["phase"], "block")
        # Positive absence, naming the exact runtime it observed, releases it.
        answer = self.core.satisfy_gate(
            WORK, gate=gate,
            evidence={"kind": "runtime-absent", "runtime": "runtime-7"}, operation_id=self.op())
        self.assertEqual(answer["phase"], "queued")
        projected = self.core.project_work(WORK)
        self.assertIsNone(projected["gate"])
        self.assertTrue(projected["ready"])
        self.assertEqual(len(self.core.gate_evidence(WORK)), 1)
        self.core.assert_invariants(WORK)

    def test_a_pinned_isolation_clause_is_the_other_way_through(self):
        assignment = self.claimed()
        self.core.cancel(assignment, reason="lost", operation_id=self.op())
        gate = f"{GATE_QUIESCENCE}:1"
        # A PINNED CLAUSE IS AN IDENTITY, NOT A YES.  `True` made "pinned"
        # mean "somebody once said yes", and the evidence then only had to be
        # truthy -- so neither side named anything.  This correction takes that
        # one representation decision: the policy holds the clause, and the
        # evidence must name that clause.
        self.authority.set_policy("isolation_certified", True)
        with self.assertRaises(Refusal) as caught:
            self.core.satisfy_gate(WORK, gate=gate, evidence={
                "kind": "certified-isolation-policy", "policy": "clause-3"}, operation_id=self.op())
        # AND THE OPERATOR IS TOLD WHOSE MISTAKE IT IS.  "No clause is pinned"
        # points at the configuration; "this evidence names a clause the
        # deployment has not pinned" points at the evidence.  They are different
        # problems with different owners, so the refusal that distinguishes them
        # has to be asserted or it can be deleted without anything noticing.
        self.assertIn("rather than a yes", str(caught.exception))
        self.authority.set_policy("isolation_certified", "clause-3")
        for what, evidence in [
                ("no clause named", {"kind": "certified-isolation-policy"}),
                ("a clause that is not text",
                 {"kind": "certified-isolation-policy", "policy": {"a": 1}}),
                ("ANOTHER deployment's clause",
                 {"kind": "certified-isolation-policy", "policy": "clause-9"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence=evidence, operation_id=self.op())
        self.core.satisfy_gate(WORK, gate=gate, evidence={
            "kind": "certified-isolation-policy", "policy": "clause-3"}, operation_id=self.op())
        self.assertIsNone(self.core.project_work(WORK)["gate"])

    def test_a_plan_revision_gate_cannot_be_satisfied_by_the_rejected_plan(self):
        assignment = self.claimed()
        self.core.reject_plan(assignment, plan_digest="sha256:first", operation_id=self.op())
        gate = f"{GATE_PLAN_REVISION}:sha256:first"
        for what, evidence in [
                ("no revised plan", {"kind": "revised-plan"}),
                ("the wrong evidence kind",
                 {"kind": "runtime-absent", "runtime": "r"}),
                ("THE SAME PLAN AGAIN",
                 {"kind": "revised-plan", "plan_digest": "sha256:first"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence=evidence, operation_id=self.op())
        self.core.satisfy_gate(WORK, gate=gate, evidence={
            "kind": "revised-plan", "plan_digest": "sha256:second"}, operation_id=self.op())
        self.assertIsNone(self.core.project_work(WORK)["gate"])

    def test_a_contract_runtime_gate_needs_a_certified_profile(self):
        self.work(WORK, contract="v12-assignment-1")
        self.core.install_gate(
            WORK, gate=gate_token("contract-runtime", "v12-assignment-1"), operation_id=self.op())
        gate = "contract-runtime:v12-assignment-1"
        with self.assertRaises(Refusal):
            self.core.satisfy_gate(WORK, gate=gate,
                                   evidence={"kind": "certified-profile",
                                             "profile": "reference"}, operation_id=self.op())
        self.authority.certify_contract("v12-assignment-1", "reference")
        # AND THE JOURNALLED PROOF NAMES WHICH PROFILE.  Recording only "a
        # certified profile exists" leaves the evidence unable to say which one
        # was relied on, which is the whole point of keeping it.
        for what, evidence in [
                ("no profile named", {"kind": "certified-profile"}),
                ("a profile that is not text",
                 {"kind": "certified-profile", "profile": 7}),
                ("a profile that is not the certified one",
                 {"kind": "certified-profile", "profile": "some-other"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence=evidence, operation_id=self.op())
        self.core.satisfy_gate(WORK, gate=gate,
                               evidence={"kind": "certified-profile",
                                         "profile": "reference"}, operation_id=self.op())
        self.assertIsNone(self.core.project_work(WORK)["gate"])

    def test_only_the_gate_actually_holding_the_work_can_be_satisfied(self):
        assignment = self.claimed()
        self.core.cancel(assignment, reason="lost", operation_id=self.op())
        for what, gate in [
                ("a different generation", f"{GATE_QUIESCENCE}:2"),
                ("a different kind", f"{GATE_PLAN_REVISION}:x"),
                ("nonsense", "not-a-gate")]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence={
                        "kind": "runtime-absent", "runtime": "r"}, operation_id=self.op())
        self.assertEqual(self.core.project_work(WORK)["phase"], "block")


class Configuration(AuthorityCase):

    def test_a_deployment_grants_only_the_capabilities_the_contract_names(self):
        for capability in CAPABILITIES:
            self.authority.grant_capability(CLAUDE, capability)
        self.assertEqual(self.authority.capabilities_of(CLAUDE),
                         sorted(CAPABILITIES))
        for what in ("configure", "", None, 7, "CLOSE"):
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.authority.grant_capability(CLAUDE, what)
        self.authority.revoke_capability(CLAUDE, "close")
        self.assertFalse(self.authority.holds_capability(CLAUDE, "close"))
        # A capability nobody can take away is not a capability, and a
        # participant is a validated identity rather than any string.
        with self.assertRaises(Refusal):
            self.authority.grant_capability("not-a-participant", "close")

    def test_policy_is_owned_data_and_round_trips(self):
        self.assertEqual(self.authority.canonical_target(), "base-1")
        self.authority.set_policy("canonical_target", "base-2")
        self.assertEqual(self.authority.canonical_target(), "base-2")
        self.authority.set_policy("shape", {"a": [1, True, None]})
        self.assertEqual(self.authority.policy("shape"), {"a": [1, True, None]})
        self.assertIsNone(self.authority.policy("absent"))
        self.assertEqual(self.authority.policy("absent", "fallback"), "fallback")
        # A policy VALUE is a durable document, so it is owned like any operand.
        with self.assertRaises(Refusal):
            self.authority.set_policy("shape", object())

    def test_certification_and_permitted_transitions_are_configured_facts(self):
        self.assertFalse(self.authority.is_certified(V12))
        self.authority.certify_contract(V12, "reference")
        self.assertTrue(self.authority.is_certified(V12))
        self.authority.withdraw_certification(V12)
        self.assertFalse(self.authority.is_certified(V12))
        self.assertFalse(self.authority.permits_contract_transition(V11, V12))
        self.authority.permit_contract_transition(V11, V12)
        self.assertTrue(self.authority.permits_contract_transition(V11, V12))
        self.assertFalse(self.authority.permits_contract_transition(V12, V11))


class Invariants(AuthorityCase):

    def test_the_backstop_holds_across_every_cut_2_path(self):
        assignment = self.claimed()
        self.core.assert_invariants(WORK)
        for ending in (lambda: self.core.end(assignment, operation_id=self.op()),):
            ending()
        self.core.assert_invariants(WORK)

    def test_the_backstop_catches_what_no_transition_can_write(self):
        # An invariant that nothing can violate is untested, so this reaches
        # PAST the transitions -- straight into the store, which is exactly the
        # door the public faces do not have -- and corrupts the row the way a
        # bug would.  The backstop then has to notice.
        assignment = self.claimed()
        connection = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(connection.close)
        for what, statement in [
                ("a Handler on a queued Work",
                 "UPDATE work SET phase = 'queued' WHERE work_id = ?"),
                ("a live generation that is not the counter",
                 "UPDATE work SET live_generation = 99 WHERE work_id = ?"),
                ("a gate outside block",
                 "UPDATE work SET gate = 'runtime-quiescence:1' WHERE work_id = ?")]:
            with self.subTest(what=what):
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(statement, (WORK,))
                connection.execute("COMMIT")
                with self.assertRaises(AssertionError):
                    self.core.assert_invariants(WORK)
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE work SET phase = 'active', live_generation = 1, "
                    "gate = NULL WHERE work_id = ?", (WORK,))
                connection.execute("COMMIT")
        self.core.assert_invariants(WORK)
        self.assertEqual(self.core.assignment_of(WORK), assignment)

    def test_a_fenced_generation_stays_inside_the_minted_range(self):
        assignment = self.claimed()
        self.core.cancel(assignment, reason="lost", operation_id=self.op())
        self.core.assert_invariants(WORK)
        connection = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(connection.close)
        connection.execute(
            "INSERT INTO fenced_generation (work_id, generation, cause, "
            "fenced_at) VALUES (?, 99, 'invented', ?)", (WORK, NOW))
        with self.assertRaises(AssertionError):
            self.core.assert_invariants(WORK)


class Restart(AuthorityCase):
    """Durability, without the journal -- that is cut 3's."""

    def test_the_state_a_transition_wrote_survives_a_reopen(self):
        assignment = self.claimed()
        self.core.cancel(assignment, reason="runtime lost", operation_id=self.op())
        self.authority.dispose()
        reopened = Authority.open(self.path, expected_authority_uuid=UUID,
                                  clock=lambda: NOW)
        self.addCleanup(reopened.dispose)
        projected = reopened.project_work(WORK)
        self.assertIsNone(projected["handler"])
        self.assertEqual(projected["phase"], "block")
        self.assertEqual(projected["gate"]["token"], f"{GATE_QUIESCENCE}:1")
        self.assertEqual(projected["generation_counter"], 1)
        self.assertEqual(reopened.fenced_generations(WORK), [1])
        self.assertEqual([event["cause"]
                          for event in reopened.assignment_events(WORK)],
                         ["claimed", "cancelled"])
        self.assertIsNone(reopened.slot_holder(CLAUDE))
        reopened.assert_invariants(WORK)
        # And the counter still does not reuse across the restart.
        reopened.project_work(WORK)


class GapsIFoundByProbingMyOwnCut(AuthorityCase):
    """Three things the 36 cases above all passed without noticing.

    The review of cut 1 made the point that my gate passing proves the rules I
    thought of.  So before handing cut 2 over I probed it the way a reviewer
    would, and it found these.  They are corrected and pinned here rather than
    left for somebody else to find.
    """

    def test_a_supplied_expect_is_compared_even_on_an_unclaimed_work(self):
        # The frozen host takes the unclaimed branch FIRST and never looks at
        # `expect`, so a caller passing a stale identity to a Work that had
        # since been released got SUCCESS and believed it had performed a
        # compare-and-swap.  An operand supplied and ignored is the defect this
        # contract keeps naming.
        assignment = self.claimed()
        self.core.end(assignment, operation_id=self.op())
        self.assertIsNone(self.core.assignment_of(WORK))
        with self.assertRaises(Refusal):
            self.core.install_gate(WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op(),
                                   expect=assignment)
        self.assertEqual(self.core.project_work(WORK)["phase"], "queued")
        # Absent still means "I did not say", and asserting `None` about a Work
        # that really has no assignment is a true assertion and is honoured.
        self.core.install_gate(WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op())
        self.assertEqual(self.core.project_work(WORK)["phase"], "block")

    def test_a_clock_that_lies_about_the_shape_writes_nothing(self):
        # `_now` validated that the configured clock answered NONEMPTY TEXT, and
        # a clock answering `banana` wrote `banana` into a durable `created_at`.
        # "Validated UTC text" has to mean the SHAPE or it means nothing.
        for what, answer in [("garbage text", "banana"),
                             ("a date with no milliseconds",
                              "2026-08-24T04:00:00Z"),
                             ("a local time", "2026-08-24 04:00:00.000"),
                             ("an integer", 7),
                             ("empty text", ""),
                             ("none", None)]:
            with self.subTest(what=what):
                path = os.path.join(self.root, f"clock-{abs(hash(what))}.sqlite3")
                authority = Authority.create(path, authority_uuid=UUID,
                                             clock=lambda answer=answer: answer)
                self.addCleanup(authority.dispose)
                with self.assertRaises(Refusal):
                    authority.create_work(WORK, ROUTE, operation_id=("create-" + str(WORK))[:160])
                connection = sqlite3.connect(path)
                rows = connection.execute("SELECT created_at FROM work").fetchall()
                connection.close()
                self.assertEqual(rows, [], what)

    def test_a_clock_that_FAULTS_is_a_fault_and_still_writes_nothing(self):
        # Deliberately NOT converted into a Refusal.  The clock is a trusted
        # bootstrap collaborator, and an act whose failure we cannot describe is
        # not one we may record an outcome for -- so the fault propagates and
        # the transaction takes nothing with it.  What must hold either way is
        # that the store is unchanged.
        def explode():
            raise RuntimeError("the clock faulted")

        path = os.path.join(self.root, "faulting-clock.sqlite3")
        authority = Authority.create(path, authority_uuid=UUID, clock=explode)
        self.addCleanup(authority.dispose)
        with self.assertRaises(RuntimeError):
            authority.create_work(WORK, ROUTE, operation_id=("create-" + str(WORK))[:160])
        connection = sqlite3.connect(path)
        rows = connection.execute("SELECT work_id FROM work").fetchall()
        connection.close()
        self.assertEqual(rows, [])
        # And the store is still usable, which a rollback that left the
        # transaction open would not be.
        working = Authority.open(path, clock=lambda: NOW)
        self.addCleanup(working.dispose)
        working.create_work(WORK, ROUTE, operation_id=("create-" + str(WORK))[:160])
        working.assert_invariants(WORK)


class CutTwoReviewFindings(AuthorityCase):
    """The seven gaps the independent cut-2 review found, each reproduced first.

    Every one of them was true while all 99 cases passed, which is the same
    lesson twice: a suite proves the rules its author thought of.
    """

    def test_a_compare_and_swap_compares_the_work_it_mutates(self):
        # [P1 1] An assignment for Y satisfied the compare-and-swap and then X
        # was gated; on the live path Y WAS ENDED while X stayed untouched.  A
        # compare-and-swap that compares one object and mutates another is not
        # one -- it is two acts wearing a single operand.
        self.work(WORK)
        self.work(OTHER)
        self.core.add_route_handler(ROUTE, GEMINI)
        for what, claim_x in [("X unclaimed", False), ("X live", True)]:
            with self.subTest(what=what):
                self.setUp()
                self.work(WORK)
                self.work(OTHER)
                self.core.add_route_handler(ROUTE, GEMINI)
                x = (self.core.claim(WORK, CLAUDE, operation_id=self.op())["assignment"]
                     if claim_x else None)
                y = self.core.claim(
                    OTHER, GEMINI, operation_id=self.op())["assignment"]
                with self.assertRaises(Refusal) as caught:
                    self.core.install_gate(
                        WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op(), expect=y)
                self.assertIn(OTHER, str(caught.exception))
                # NEITHER Work moved: not the one named and not the one gated.
                self.assertEqual(self.core.project_work(WORK)["phase"],
                                 "active" if claim_x else "queued")
                self.assertIsNone(self.core.project_work(WORK)["gate"])
                self.assertEqual(self.core.assignment_of(OTHER), y)
                self.assertEqual(self.core.assignment_of(WORK), x)
        # And the same act with this Work's own identity still works.
        self.setUp()
        own_assignment = self.claimed(WORK)
        self.core.install_gate(WORK, gate=gate_token(GATE_QUIESCENCE, "1"), operation_id=self.op(),
                               expect=own_assignment)
        self.assertEqual(self.core.project_work(WORK)["phase"], "block")

    def test_the_generation_space_is_finite_and_running_out_refuses(self):
        # [P1 2] The counter was incremented and returned as an assignment
        # identity without being held to the frozen range, so a Work at the
        # boundary minted 9007199254740992 -- a generation no consumer of these
        # documents can read back.
        self.work()
        connection = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(connection.close)
        connection.execute(
            "UPDATE work SET generation_counter = ? WHERE work_id = ?",
            (MAX_SAFE_INTEGER - 1, WORK))
        # The LAST generation the range allows is still minted.
        last = self.core.claim(
            WORK, CLAUDE, operation_id=self.op())["assignment"]
        self.assertEqual(last["generation"], MAX_SAFE_INTEGER)
        self.core.end(last, operation_id=self.op())
        # And the next one refuses rather than producing an unusable number.
        with self.assertRaises(Refusal) as caught:
            self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertIn("never reused", str(caught.exception))
        # Nothing moved: no Handler, no slot, and the counter did not advance.
        projected = self.core.project_work(WORK)
        self.assertIsNone(projected["handler"])
        self.assertEqual(projected["generation_counter"], MAX_SAFE_INTEGER)
        self.assertIsNone(self.core.slot_holder(CLAUDE))
        self.core.assert_invariants(WORK)

    def test_every_durable_text_operand_goes_through_one_rule(self):
        # [P1 3] `_text` required exact nonempty `str` and stopped there, so a
        # LONE SURROGATE reached SQLite and escaped as `UnicodeEncodeError` --
        # from a route, from prose, from a plan digest, and out of `gate_token`
        # as an invalid durable token.  `own` already enforced this for
        # documents; the scalars had a weaker rule beside it, and a rule that
        # exists twice holds in one of the two places.
        bad = "x\ud800y"
        assignment = self.claimed()
        for what, call in [
                ("a route", lambda: self.core.create_work(
                OTHER, bad, operation_id=("create-" + OTHER)[:160])),
                ("a contract",
                 lambda: self.core.create_work(OTHER, ROUTE, contract=bad, operation_id=("create-" + OTHER)[:160])),
                ("a policy key", lambda: self.authority.set_policy(bad, 1)),
                ("a release reason",
                 lambda: self.core.end(assignment, reason=bad, operation_id=self.op())),
                ("a pass comment",
                 lambda: self.core.pass_work(assignment, to_route=ROUTE,
                                             comment=bad, operation_id=self.op())),
                ("a pass route",
                 lambda: self.core.pass_work(assignment, to_route=bad, operation_id=self.op())),
                ("a plan digest",
                 lambda: self.core.reject_plan(assignment, plan_digest=bad, operation_id=self.op())),
                ("a cancel reason",
                 lambda: self.core.cancel(assignment, reason=bad, operation_id=self.op())),
                ("a gate token detail",
                 lambda: gate_token(GATE_QUIESCENCE, bad)),
                ("a gate token kind", lambda: gate_token(bad, "1"))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    call()
        # The live assignment survived all of them.
        self.assertEqual(self.core.assignment_of(WORK), assignment)
        # AND ORDINARY NON-ASCII TEXT IS DATA, NOT A HAZARD.  A rule that
        # refused it would be a bug wearing a fix.
        self.core.create_work(OTHER, "révision-plan", operation_id=("create-" + str(OTHER))[:160])
        self.core.end(assignment, reason="perdu — le runtime a disparu 😀", operation_id=self.op())
        self.assertEqual(self.core.project_work(OTHER)["route"], "révision-plan")
        self.assertIn("😀", self.core.assignment_events(WORK)[-1]["reason"])

    def test_a_gate_is_discharged_by_proof_and_not_by_truthiness(self):
        # [P1 4] Every evidence check used TRUTHINESS, so a list stood for an
        # exact runtime identity and a list satisfied a plan-revision gate.
        # `[1]` is not a proof of anything; it is a value that happens not to be
        # empty.
        assignment = self.claimed()
        self.core.cancel(assignment, reason="lost", operation_id=self.op())
        gate = f"{GATE_QUIESCENCE}:1"
        for what, evidence in [
                ("a runtime that is a list",
                 {"kind": "runtime-absent", "runtime": [1]}),
                ("a runtime that is a number",
                 {"kind": "runtime-absent", "runtime": 7}),
                ("a runtime that is a document",
                 {"kind": "runtime-absent", "runtime": {"id": "r"}}),
                ("a runtime that is true",
                 {"kind": "runtime-absent", "runtime": True}),
                ("a runtime that is unencodable",
                 {"kind": "runtime-absent", "runtime": "r\ud800"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence=evidence, operation_id=self.op())
        self.assertEqual(self.core.project_work(WORK)["phase"], "block")
        self.core.satisfy_gate(WORK, gate=gate, evidence={
            "kind": "runtime-absent", "runtime": "runtime-7"}, operation_id=self.op())
        # And what was JOURNALLED is the proof itself, so a later reader can
        # see which runtime was observed rather than that one was.
        self.assertEqual(self.core.gate_evidence(WORK)[-1]["evidence"],
                         {"kind": "runtime-absent", "runtime": "runtime-7"})

    def test_a_plan_revision_needs_a_digest_and_not_merely_something(self):
        assignment = self.claimed()
        self.core.reject_plan(assignment, plan_digest="sha256:first", operation_id=self.op())
        gate = f"{GATE_PLAN_REVISION}:sha256:first"
        for what, evidence in [
                ("a digest that is a list",
                 {"kind": "revised-plan", "plan_digest": [1]}),
                ("a digest that is true",
                 {"kind": "revised-plan", "plan_digest": True}),
                ("a digest that is a document",
                 {"kind": "revised-plan", "plan_digest": {"a": 1}})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.satisfy_gate(WORK, gate=gate, evidence=evidence, operation_id=self.op())
        self.assertEqual(self.core.project_work(WORK)["phase"], "block")

    def test_the_history_is_the_whole_life_of_the_assignment(self):
        # [P1 5] Claim wrote no event, so the journal said who LOST the Work and
        # never who took it -- and the events answered in separate columns
        # rather than in the four-part identity §4 requires.
        assignment = self.claimed()
        events = self.core.assignment_events(WORK)
        self.assertEqual([event["cause"] for event in events], ["claimed"])
        self.assertEqual(events[0]["assignment_ref"], assignment)
        self.assertEqual(events[0]["phase"], "active")
        self.assertIs(events[0]["fenced"], False)
        # A second claim by the same participant appends its own claim event
        # with the NEW generation, so the two assignments are distinguishable
        # in the history -- which is the point of recording the identity.
        self.core.end(assignment, operation_id=self.op())
        second = self.core.claim(
            WORK, CLAUDE, operation_id=self.op())["assignment"]
        causes = [event["cause"] for event in self.core.assignment_events(WORK)]
        self.assertEqual(causes, ["claimed", "release", "claimed"])
        generations = [event["assignment_ref"]["generation"]
                       for event in self.core.assignment_events(WORK)]
        self.assertEqual(generations, [1, 1, 2])
        self.assertEqual(second["generation"], 2)
        # And no event answers with a bare participant.
        for event in self.core.assignment_events(WORK):
            self.assertNotIn("participant", event)
            self.assertNotIn("work_id", event)
            self.assertEqual(set(event["assignment_ref"]),
                             {"work_ref", "participant", "generation"})

    def test_a_missing_assignment_is_the_same_refusal_everywhere(self):
        # [P2 6] `cancel(None)` subscripted the normalized ABSENCE and raised
        # `TypeError` instead of the ordinary refusal every other transition
        # gives.  The COMMON precondition comes before the transition-specific
        # one: "you gave me no assignment" is true of every act.
        self.work()
        for what, call in [
                ("end", lambda: self.core.end(None, operation_id=self.op())),
                ("pass", lambda: self.core.pass_work(None, to_route="rview", operation_id=self.op())),
                ("cancel", lambda: self.core.cancel(None, operation_id=self.op())),
                ("reject_plan",
                 lambda: self.core.reject_plan(None, plan_digest="sha256:p", operation_id=self.op()))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    call()
        self.core.assert_invariants(WORK)

    def test_the_backstop_checks_both_directions_of_the_cross_product(self):
        # [P2 7] It checked gate-implies-block and nothing else, so an open Work
        # in `block` with NO gate, and one in an INVENTED phase, both returned
        # True.  A backstop that checks one direction of a cross-product is a
        # backstop for one of its two failures.
        self.work()
        connection = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(connection.close)
        for what, phase, gate in [
                ("block with no gate", "block", None),
                ("an invented phase", "invented", None),
                ("a null phase on an open Work", None, None),
                ("an untyped gate", "block", "not-a-gate"),
                ("an unknown gate kind", "block", "invented:1"),
                ("a gate with no detail", "block", f"{GATE_QUIESCENCE}:")]:
            with self.subTest(what=what):
                connection.execute(
                    "UPDATE work SET phase = ?, gate = ? WHERE work_id = ?",
                    (phase, gate, WORK))
                with self.assertRaises(AssertionError):
                    self.core.assert_invariants(WORK)
        # And the coherent pairings still pass, so the backstop has not simply
        # become a refusal.
        for phase, gate in [("queued", None), ("parked", None),
                            ("block", f"{GATE_QUIESCENCE}:1")]:
            connection.execute(
                "UPDATE work SET phase = ?, gate = ? WHERE work_id = ?",
                (phase, gate, WORK))
            self.core.assert_invariants(WORK)


class OwnedAnswers(AuthorityCase):

    def test_a_projection_is_a_fresh_document_and_not_a_live_row(self):
        assignment = self.claimed()
        first = self.core.project_work(WORK)
        first["phase"] = "tampered"
        first["assignment"]["participant"] = GEMINI
        second = self.core.project_work(WORK)
        self.assertEqual(second["phase"], "active")
        self.assertEqual(second["assignment"], assignment)
        # The answer is built of exact built-ins, so a consumer can serialize it
        # without discovering an object in the middle of it.
        import json
        self.assertEqual(json.loads(json.dumps(second)), second)

    def test_a_returned_assignment_is_not_an_alias_of_the_caller_operand(self):
        assignment = self.claimed()
        answer = self.core.end(assignment, operation_id=self.op())
        self.assertEqual(answer["assignment"], assignment)
        answer["assignment"]["participant"] = GEMINI
        self.assertEqual(assignment["participant"], CLAUDE)


if __name__ == "__main__":
    unittest.main()
