"""W2845 cut 5 — the participant-bound session, and the two faces.

The obligations: sessions are MINTED and not constructed; the actor on every
receipt and the claimant on every claim come from the BINDING; a supplied
`actor` or `participant` is REFUSED rather than ignored; every mutation takes one
exact owned operand document; the transition and read surface is enumerated
rather than derived; and a session reaches no configuration, no store, no path
and no way to mint another.

Catalog E's session half, and the honest Python trust claim: these cases inspect
the SUPPORTED, EXPORTED surface and the deployment wiring.  They do not pretend
that a leading underscore is a capability boundary -- a determined trusted
in-process module can read `_core`, and saying otherwise would be a false
guarantee dressed as a test.
"""

import os
import tempfile
import unittest

from baton_v12.authority import (Authority, CAPABILITIES, Refusal,
                                 SESSION_READS, SESSION_TRANSITIONS, Session,
                                 V12)
from baton_v12.authority.identity import GATE_QUIESCENCE, gate_token

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
GEMINI = "baton.gemini"
ROUTE = "impl"
NOW = "2026-08-24T07:00:00.000Z"

DIGESTS = {"result_id": "result-1", "result_digest": "sha256:result-1",
           "candidate_digest": "sha256:candidate-1",
           "input_digest": "sha256:input-1",
           "policy_digest": "sha256:policy-1"}


class SessionCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-authority-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.claude = self.authority.session(CLAUDE)
        self.gemini = self.authority.session(GEMINI)
        self._ops = 0

    def op(self, label="op"):
        self._ops += 1
        return f"{label}.{self._ops}"

    def work(self, work_id=WORK, *, contract=V12, handlers=(CLAUDE, GEMINI)):
        self.authority.create_work(
            work_id, ROUTE, contract=contract,
            operation_id=("create-" + work_id)[:160])
        for participant in handlers:
            self.authority.add_route_handler(ROUTE, participant)
        return work_id


class Minting(SessionCase):

    def test_a_session_is_minted_and_never_constructed(self):
        self.assertIsInstance(self.claude, Session)
        self.assertEqual(self.claude.participant, CLAUDE)
        # Reaching the class through an instance is not a way to make another:
        # the mint object is module-private and exported nowhere.
        for what, arguments in [
                ("no mint", (None, None, "baton.someone")),
                ("a guessed mint", (object(), None, "baton.someone")),
                ("a truthy mint", (True, None, "baton.someone"))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    type(self.claude)(*arguments)
                self.assertIn("minted", str(caught.exception))

    def test_a_session_is_bound_to_one_named_participant(self):
        for what in ("", None, 7, "not-a-participant", "Baton.Claude"):
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.authority.session(what)

    def test_the_surface_is_enumerated_rather_than_derived(self):
        # Deriving it from `Core` would mean adding a method there silently
        # widened the runtime boundary.  A new transition is unreachable from a
        # session until somebody puts it in the table deliberately.
        self.assertEqual(list(SESSION_TRANSITIONS), sorted([
            "activity", "advance_contract", "approve", "cancel", "claim",
            "close", "end", "install_gate", "integrate", "pass_work",
            "publish", "reject_plan", "review", "satisfy_gate",
            "settle_operation", "verify",
            # W29400: the two Work-label mutations, entered deliberately.
            "label_work", "unlabel_work"]))
        self.assertEqual(list(SESSION_READS), sorted([
            "activities", "assert_invariants", "assignment_events",
            "assignment_of", "canonical_target", "contract_events",
            "fenced_generations", "gate_evidence", "integration_attempts",
            "operation_record", "operation_result", "project_work", "proposal",
            "receipt", "receipts", "slot_holder",
            # W29400: one Work's live set and its mutation history.
            "labels_of", "work_label_events"]))
        public = sorted(name for name in dir(self.claude)
                        if not name.startswith("_"))
        self.assertEqual(
            public, sorted(set(SESSION_TRANSITIONS) | set(SESSION_READS)
                           | {"participant"}))

    def test_the_two_faces_are_disjoint_by_construction(self):
        # Computed from `Core` rather than hardcoded, so a method added there
        # lands on exactly one side and the case says which.  The runtime face
        # gets transitions and reads; the configuration surface is the
        # REMAINDER, and no name is on both.
        from baton_v12.authority.core import Core
        core_public = {name for name in dir(Core) if not name.startswith("_")}
        session_public = {name for name in dir(self.claude)
                          if not name.startswith("_")} - {"participant"}
        self.assertEqual(session_public - core_public, set())
        configuration = core_public - session_public
        self.assertEqual(configuration, {
            "add_route_handler", "authority_uuid", "capabilities_of",
            "certify_contract", "create_work", "dispose", "grant_capability",
            "holds_capability", "is_certified", "permit_contract_transition",
            "permits_contract_transition", "policy", "revoke_capability",
            "set_lookup_available", "set_policy", "withdraw_certification",
            # W16821: the principal seam is CONFIGURATION, all six of it.
            # `bind_endpoint` moves an identity's claim capacity, its grants
            # and its attribution, so a session holding it would be a session
            # that could act as somebody else.  `authorize` is the decision
            # seam itself: a session that could ask it would be probing the
            # deployment's grant table without acting, and the transitions that
            # need it call it on the caller's behalf.  The four reads are here
            # rather than on the session because they answer about OTHER
            # principals and endpoints; `slot_holder` stays a session read
            # because it answers about the session's own address.
            "authorize", "bind_endpoint", "endpoints_of", "policy_generation",
            "principal_of", "slot_holder_of_principal",
            # W16821 review: `decision_of` and `grants_of` answer about acts
            # and grants a session did not perform and does not hold, which is
            # a deployment question.
            "decision_of", "grants_of",
            # W29400: `works_with_labels` is a DEPLOYMENT-WIDE inventory --
            # which Work carries which labels -- so it stays on the
            # configuration side.  The two mutations and the two per-Work reads
            # are on the session, where an attributable act belongs.
            "works_with_labels",
            # W29400 review [P0]: `work_creation` answers the act that MADE a
            # Work -- a trusted bootstrap, performed before any session could
            # exist -- so it is a configuration-side read like the two above
            # rather than something a session's own attributable acts reach.
            "work_creation"})
        self.assertEqual(session_public & configuration, set())
        # And the session module's own public names match its `__all__`, so the
        # surface claim checks rather than merely being written down.
        import baton_v12.authority.session as module
        self.assertEqual(
            sorted(name for name in vars(module)
                   if not name.startswith("_")
                   and getattr(vars(module)[name], "__module__", module.__name__)
                   == module.__name__),
            sorted(module.__all__))

    def test_a_session_reaches_no_configuration_and_no_store(self):
        # It cannot configure anything, cannot reach the authority that made it,
        # and carries no path, no store and no way to mint another.
        for name in ("certify_contract", "grant_capability", "set_policy",
                     "create_work", "add_route_handler", "session", "dispose",
                     "authority_uuid", "store", "path", "db", "core",
                     "set_lookup_available", "withdraw_certification",
                     "permit_contract_transition", "revoke_capability"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(self.claude, name), name)


class TheBindingIsTheIdentity(SessionCase):

    def test_the_claimant_is_the_binding(self):
        self.work()
        assignment = self.claude.claim({"work_id": WORK,
                                        "operation_id": self.op()})["assignment"]
        self.assertEqual(assignment["participant"], CLAUDE)
        self.assertEqual(self.authority.slot_holder(CLAUDE), WORK)
        # And gemini's session claims as gemini, on its own Work.
        self.work(OTHER)
        self.assertEqual(
            self.gemini.claim({"work_id": OTHER,
                               "operation_id": self.op()}
                              )["assignment"]["participant"],
            GEMINI)

    def test_a_supplied_identity_is_refused_and_never_dropped(self):
        # AN OPERAND THAT LOOKS AUTHORITATIVE AND IS NOT is worse than no
        # operand.  The frozen host silently DROPPED a supplied `participant` on
        # `claim`, so a caller could believe it had been honoured -- which is the
        # worst of the three possible behaviours.
        self.work()
        for name in SESSION_TRANSITIONS:
            for identity in ("actor", "participant"):
                with self.subTest(name=name, identity=identity):
                    with self.assertRaises(Refusal) as caught:
                        getattr(self.claude, name)({identity: GEMINI})
                    self.assertIn("takes its identity from the session",
                                  str(caught.exception))
        self.assertIsNone(self.authority.assignment_of(WORK))

    def test_a_session_acts_only_on_its_own_assignments(self):
        # The assignment identity authorizes the assignment-owned acts and is
        # not a secret, so a session that could act on somebody else's would
        # make the binding decorative.
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        for name, operands in [
                ("end", {"expect": mine, "operation_id": self.op()}),
                ("cancel", {"expect": mine, "operation_id": self.op()}),
                ("pass_work", {"expect": mine, "operation_id": self.op(),
                               "to_route": "rview"}),
                ("reject_plan", {"expect": mine, "operation_id": self.op(),
                                 "plan_digest": "sha256:plan"}),
                ("activity", {"expect": mine, "key": "k"}),
                ("publish", {"expect": mine, "operation_id": self.op(),
                             "proposal_id": "proposal-1", **DIGESTS}),
                ("advance_contract", {"expect": mine,
                                      "operation_id": self.op(),
                                      "expect_contract": V12,
                                      "target_contract": "v12-next",
                                      "rationale": "x"})]:
            with self.subTest(name=name):
                with self.assertRaises(Refusal) as caught:
                    getattr(self.gemini, name)(operands)
                # Both names now render through `name_of`, which quotes a
                # string -- the same helper that bounds them, so the verdict
                # reads the same and the diagnostic can no longer be a
                # megabyte of the caller's text.
                self.assertIn(f"session acts for {GEMINI!r}",
                              str(caught.exception))
                self.assertIn(f"assignment names {CLAUDE!r}",
                              str(caught.exception))
        # Claude's own assignment is untouched by every one of them.
        self.assertEqual(self.authority.assignment_of(WORK), mine)

    def test_close_is_authorized_by_capability_and_not_by_authorship(self):
        # §7 authorizes close by the close CAPABILITY, and its `expect` is a
        # compare-and-swap operand rather than proof of authorship: an approver
        # closing a Work somebody else is executing is the ORDINARY case, and
        # the identity is what stops them closing blindly.
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        self.authority.grant_capability(GEMINI, "close")
        answer = self.gemini.close({"work_id": WORK,
                                    "operation_id": self.op(),
                                    "outcome": "cancelled",
                                    "rationale": "stood down",
                                    "expect": mine})
        # The ACTOR is gemini's binding, and the assignment it ended is
        # claude's.
        self.assertEqual(answer["actor"], GEMINI)
        self.assertEqual(answer["assignment"], mine)
        self.assertEqual(self.authority.project_work(WORK)["status"], "closed")
        # And a session without the capability cannot close, even its own.
        self.work(OTHER)
        own = self.claude.claim({"work_id": OTHER, "operation_id": self.op()})["assignment"]
        with self.assertRaises(Refusal) as caught:
            self.claude.close({"work_id": OTHER, "operation_id": self.op(),
                               "outcome": "cancelled", "rationale": "mine",
                               "expect": own})
        self.assertIn("close capability", str(caught.exception))

    def test_the_receipt_actor_is_the_binding(self):
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        self.claude.publish({"expect": mine, "operation_id": self.op(),
                             "proposal_id": "proposal-1", **DIGESTS})
        for capability in CAPABILITIES:
            self.authority.grant_capability(GEMINI, capability)
        answer = self.gemini.verify({"proposal_id": "proposal-1",
                                     "verification_id": "ver-1",
                                     "observation": "passed",
                                     "operation_id": self.op()})
        self.assertEqual(answer["actor"], GEMINI)
        self.assertEqual(
            self.authority.receipt("proposal-1", "verification")["actor"],
            GEMINI)
        # A session that does not hold the capability cannot write the receipt,
        # and cannot borrow gemini's name to do it -- there is no operand for it.
        with self.assertRaises(Refusal):
            self.claude.review({"proposal_id": "proposal-1",
                                "review_id": "rev-1",
                                "disposition": "accepted",
                                "operation_id": self.op()})


class OneOwnedOperandDocument(SessionCase):

    def test_the_operands_are_taken_once_and_never_read_again(self):
        # The frozen host read `operands.expect.participant` for the binding
        # check and then handed the SAME object to the core, which read it
        # again.  A container that answers differently on the second read passed
        # the check and then acted on somebody else's assignment.  Python's
        # version of that hazard is a dict SUBCLASS, and it never enters.
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]

        class Lying(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.reads = 0

            def __getitem__(self, key):
                self.reads += 1
                if key == "expect" and self.reads > 1:
                    return {**mine, "participant": GEMINI}
                return super().__getitem__(key)

        with self.assertRaises(Refusal):
            self.claude.end(Lying({"expect": mine,
                                   "operation_id": self.op()}))
        self.assertEqual(self.authority.assignment_of(WORK), mine)
        # And a nested subclass is refused too.
        with self.assertRaises(Refusal):
            self.claude.end({"expect": Lying(mine),
                             "operation_id": self.op()})
        self.assertEqual(self.authority.assignment_of(WORK), mine)

    def test_an_operand_supplied_and_ignored_would_be_one_the_caller_chose(self):
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        for what, operands in [
                ("an invented key", {"expect": mine,
                                     "operation_id": self.op(),
                                     "phase": "active"}),
                ("a core keyword that is not in the shape",
                 {"expect": mine, "operation_id": self.op(),
                  "fence": True}),
                ("a misspelling", {"expect": mine,
                                   "operation_id": self.op(),
                                   "resaon": "typo"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    self.claude.end(operands)
                self.assertIn("does not take", str(caught.exception))
        self.assertEqual(self.authority.assignment_of(WORK), mine)

    def test_a_missing_required_operand_says_which(self):
        with self.assertRaises(Refusal) as caught:
            self.claude.claim({"work_id": WORK})
        self.assertIn("operation_id", str(caught.exception))
        with self.assertRaises(Refusal) as caught:
            self.claude.claim({})
        self.assertIn("operation_id", str(caught.exception))
        self.assertIn("work_id", str(caught.exception))

    def test_the_operands_must_be_a_document(self):
        for what, given in [("a list", [1]), ("text", "work"), ("a number", 7),
                            ("an object", object()),
                            ("a dict subclass", type("D", (dict,), {})())]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.claude.claim(given)
        # SUPERSEDED by the final review, and specifically authorized to
        # change: this case used to call explicit `None` "a legitimate operand
        # document for nothing" and expect the MISSING-MEMBER refusal.  That was
        # the wrapper silently replacing an explicitly supplied value -- in the
        # one place whose stated purpose is to refuse an operand supplied and
        # then ignored.  An explicit null is now the document rule.
        with self.assertRaises(Refusal) as caught:
            self.claude.claim(None)
        self.assertIn("one operand document", str(caught.exception))
        self.assertNotIn("needs", str(caught.exception))

    def test_the_answers_are_fresh_owned_built_ins(self):
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        mine["participant"] = "tampered"
        self.assertEqual(self.authority.assignment_of(WORK)["participant"],
                         CLAUDE)
        projected = self.claude.project_work(WORK)
        projected["status"] = "tampered"
        self.assertEqual(self.claude.project_work(WORK)["status"], "open")
        import json
        self.assertEqual(json.loads(json.dumps(self.claude.project_work(WORK))),
                         self.claude.project_work(WORK))


class FinalReviewFindings(SessionCase):
    """Public-boundary rules that the 200-case final-cut gate did not witness."""

    def test_bootstrap_collision_refusal_is_bounded_by_the_rule(self):
        huge = "0123abcd-W" + "1" * 1_000_000
        # TWO DIFFERENT ACTS, so two identities. W29400 made creation
        # effectively-once: the SAME identity would replay the first answer,
        # which is correct and is not what this case is about -- it is about a
        # second attempt to create a Work that already exists, and the bound
        # on the refusal it produces.
        self.authority.create_work(huge, ROUTE, operation_id="create-huge-1")
        with self.assertRaises(Refusal) as caught:
            self.authority.create_work(huge, ROUTE,
                                       operation_id="create-huge-2")
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertNotIn(huge, message)

    def test_capability_refusal_is_bounded_by_the_rule(self):
        huge = "baton." + "x" * 1_000_000
        session = self.authority.session(huge)
        with self.assertRaises(Refusal) as caught:
            session.verify({"proposal_id": "proposal-1",
                            "verification_id": "verification-1",
                            "observation": "passed",
                            "operation_id": self.op()})
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertNotIn(huge, message)

    def test_session_refusals_are_bounded_by_the_rule_not_caller_text(self):
        huge = "x" * 1_000_000
        foreign = {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": huge,
            "generation": 1,
        }
        for what, call in [
                ("assignment participant",
                 lambda: self.claude.end({"expect": foreign,
                                          "operation_id": self.op()})),
                ("unknown operand name",
                 lambda: self.claude.claim({"work_id": WORK,
                                            "operation_id": self.op(),
                                            huge: True}))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                message = str(caught.exception)
                self.assertLess(len(message), 500, what)
                self.assertNotIn(huge, message, what)

    def test_many_rejected_names_become_a_bounded_sample_and_a_count(self):
        # The reviewer's case uses ONE unexpected name.  The joined-set half of
        # the defect needs several, and it is the worse half: `own` admits up to
        # 512 members, so 510 unexpected names of 100,000 characters each was a
        # ~51,000,000-character refusal from a boundary that had already decided
        # to refuse.
        wide = {"work_id": WORK, "operation_id": self.op()}
        wide.update({f"{'y' * 2000}{index}": index for index in range(400)})
        with self.assertRaises(Refusal) as caught:
            self.claude.claim(wide)
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        # A sample AND a count: the count is what makes the sample honest, since
        # "does not take three things" would understate a 400-name mistake.
        self.assertIn("and 397 more", message)

    def test_the_sample_is_a_sample_only_when_there_is_more_to_show(self):
        for count, tail in [(1, False), (3, False), (4, True)]:
            with self.subTest(count=count):
                given = {"work_id": WORK, "operation_id": self.op()}
                given.update({f"extra{index}": index for index in range(count)})
                with self.assertRaises(Refusal) as caught:
                    self.claude.claim(given)
                message = str(caught.exception)
                self.assertEqual("more" in message, tail, message)
                self.assertIn("extra0", message)

    def test_the_repr_is_bounded_too(self):
        # Found by sweeping this module rather than by being told: a participant
        # has a grammar and no length, and a repr is a diagnostic that is logged
        # exactly like a refusal.
        wide = "baton." + "w" * 1_000_000
        self.authority.add_route_handler(ROUTE, wide)
        self.assertLess(len(repr(self.authority.session(wide))), 200)

    def test_a_transition_takes_exactly_one_built_in_operand_document(self):
        for what, call in [
                ("omitted", lambda: self.claude.claim()),
                ("explicit null", lambda: self.claude.claim(None)),
                ("two documents", lambda: self.claude.claim({}, {}))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                self.assertIn("one operand document", str(caught.exception))


class TheWholeSurfaceWorksThroughTheSession(SessionCase):

    def test_a_full_workflow_runs_end_to_end_through_sessions_only(self):
        # The point of cut 5: everything a runtime consumer needs is reachable
        # from a session, and nothing a consumer needs is reachable ONLY from
        # the bootstrap face.
        self.work()
        for capability in CAPABILITIES:
            self.authority.grant_capability(GEMINI, capability)
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        self.claude.activity({"expect": mine, "key": "wrote-the-file"})
        self.claude.publish({"expect": mine, "operation_id": self.op(),
                             "proposal_id": "proposal-1", **DIGESTS})
        self.gemini.verify({"proposal_id": "proposal-1",
                            "verification_id": "ver-1",
                            "observation": "passed",
                            "operation_id": self.op()})
        self.gemini.review({"proposal_id": "proposal-1", "review_id": "rev-1",
                            "disposition": "accepted",
                            "operation_id": self.op()})
        self.gemini.approve({"proposal_id": "proposal-1",
                             "approval_id": "app-1",
                             "disposition": "approved",
                             "operation_id": self.op(),
                             "policy_generation": 7})
        self.gemini.integrate({"proposal_id": "proposal-1",
                               "integration_id": "int-1",
                               "operation_id": self.op()})
        self.assertEqual(self.claude.canonical_target(),
                         DIGESTS["candidate_digest"])
        self.assertEqual([row["kind"] for row in
                          self.claude.receipts("proposal-1")],
                         ["approval", "integration", "review", "verification"])
        self.claude.end({"expect": mine, "operation_id": self.op(),
                         "reason": "done"})
        self.gemini.close({"work_id": WORK, "operation_id": self.op(),
                           "outcome": "satisfying", "rationale": "integrated"})
        self.assertEqual(self.claude.project_work(WORK)["outcome"],
                         "satisfying")
        self.claude.assert_invariants(WORK)

    def test_the_gate_and_settlement_surfaces_are_reachable(self):
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        self.claude.cancel({"expect": mine, "operation_id": self.op(),
                            "reason": "lost the runtime"})
        gate = gate_token(GATE_QUIESCENCE, "1")
        self.assertEqual(self.claude.project_work(WORK)["gate"]["token"], gate)
        self.claude.satisfy_gate({"work_id": WORK, "operation_id": self.op(),
                                  "gate": gate,
                                  "evidence": {"kind": "runtime-absent",
                                               "runtime": "runtime-7"}})
        self.assertTrue(self.claude.project_work(WORK)["ready"])
        self.assertEqual(len(self.claude.gate_evidence(WORK)), 1)
        self.assertEqual(self.claude.fenced_generations(WORK), [1])
        # Settlement, observed and then asserted.
        self.assertEqual(
            self.claude.settle_operation({"operation_id": "unused-op",
                                          "signature": "sig"})["kind"], "live")
        self.assertEqual(
            self.claude.settle_operation({"operation_id": "unused-op",
                                          "signature": "sig",
                                          "reason": "deadline",
                                          "disposition": "timeout",
                                          "may_retire": True})["kind"],
            "retired")
        self.assertEqual(self.claude.operation_record("unused-op")["state"],
                         "retired")

    def test_install_gate_over_an_unclaimed_work_needs_no_assignment(self):
        self.work()
        answer = self.claude.install_gate({"work_id": WORK,
                                           "operation_id": self.op(),
                                           "gate": gate_token(GATE_QUIESCENCE,
                                                              "1"),
                                           "reason": "waiting"})
        self.assertIsNone(answer["assignment"])
        self.assertEqual(self.claude.project_work(WORK)["phase"], "block")

    def test_every_read_answers_through_the_session(self):
        self.work()
        mine = self.claude.claim({"work_id": WORK, "operation_id": self.op()})["assignment"]
        self.claude.publish({"expect": mine, "operation_id": self.op(),
                             "proposal_id": "proposal-1", **DIGESTS})
        answers = {
            "activities": self.claude.activities(WORK),
            "assert_invariants": self.claude.assert_invariants(WORK),
            "assignment_events": self.claude.assignment_events(WORK),
            "assignment_of": self.claude.assignment_of(WORK),
            "canonical_target": self.claude.canonical_target(),
            "contract_events": self.claude.contract_events(WORK),
            "fenced_generations": self.claude.fenced_generations(WORK),
            "gate_evidence": self.claude.gate_evidence(WORK),
            "integration_attempts":
                self.claude.integration_attempts("proposal-1"),
            "labels_of": self.claude.labels_of(WORK),
            "work_label_events": self.claude.work_label_events(WORK),
            "operation_record": self.claude.operation_record("op.1"),
            "operation_result": self.claude.operation_result("op.1"),
            "project_work": self.claude.project_work(WORK),
            "proposal": self.claude.proposal("proposal-1"),
            "receipt": self.claude.receipt("proposal-1", "review"),
            "receipts": self.claude.receipts("proposal-1"),
            "slot_holder": self.claude.slot_holder(CLAUDE),
        }
        self.assertEqual(sorted(answers), list(SESSION_READS))
        self.assertEqual(answers["slot_holder"], WORK)
        self.assertEqual(answers["assignment_of"], mine)
        self.assertIsNone(answers["receipt"])
        # And a read takes exactly its operands: too many or too few refuses
        # rather than raising a TypeError from the delegate.
        for what, call in [
                ("too many", lambda: self.claude.project_work(WORK, "extra")),
                ("too few", lambda: self.claude.project_work()),
                ("none where none is wanted",
                 lambda: self.claude.canonical_target(WORK))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    call()


if __name__ == "__main__":
    unittest.main()
