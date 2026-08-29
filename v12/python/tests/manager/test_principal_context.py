"""W16823 — the principal-aware manager context, from the claim to the label.

W16793 found the Worker Manager fencing correctly by the four-part assignment
and then treating the endpoint participant as every identity below the
authority: offers, attempts, runtime labels and sealed documents all named the
participant and nothing else.  Two endpoint addresses the authority maps to ONE
principal produced two unrelated stores and two unrelated runtime identities,
and no retained record said which scope or grant authorized an activation.

Approver rulings M34905 and M35002 settle what this manager does about it:

  * it CONSUMES the authority's closed claim result and persists the exact
    claim event and decision atomically with the claim it records;
  * it includes that context in every replay signature whose authorization
    meaning it changes;
  * it validates the closed shape and the relations it can establish -- the
    endpoint IS the assignment's participant, the scope and role ARE what this
    offer froze from the Work -- and refuses malformed or relationally
    inconsistent context before a row or a runtime exists;
  * it accepts NO caller or worker operand for any of it;
  * it labels runtimes with the principal and effective scope BESIDE the
    unchanged fence;
  * and it does NOT second-guess an internally consistent principal from its
    trusted authority, because doing so would take a duplicate
    endpoint-to-principal mapping this correction exists to prevent.

The last one is a NEGATIVE SPACE and is asserted as one: the case below drives
a different-but-consistent principal all the way through and records that the
manager persists it, which is the honest statement of the boundary rather than
a refusal nobody can implement.
"""

import os
import sqlite3
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      accept_offer, activate_assignment,
                                      certify_profile, issue_offer,
                                      record_attempt, settle_claim,
                                      submit_claim)
from baton_v12.worker_manager import attempts as attempts_module
from baton_v12.worker_manager.authority_port import (DECISION, CLAIM_RESULT,
                                                     GRANT_PROVENANCE,
                                                     PROJECTION_READ)
from baton_v12.worker_manager.schema import SCHEMA_VERSION
from baton_v12.worker_manager.store import manager_signature

from .test_offers import (FakeSession, NOW, PRINCIPAL, PROFILE, ROUTE, SCOPE,
                          UUID, WHO, WORK, decision, fake_claim_signature)

ATTEMPT = "attempt-1"
ADAPTER = "sha256:" + "a" * 64
ALIAS = "review.claude"


class ContextCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w16823-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        certify_profile(self.store, "runtime", "reference", PROFILE)
        self.session = FakeSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)

    # -- the arc, in pieces so a case can stop anywhere along it -------------

    def issued(self, offer_id="offer-1", attempt_id=ATTEMPT):
        issue_offer(self.store, self.port, offer_id=offer_id, work_id=WORK,
                    runtime_attempt_id=attempt_id,
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-1")
        accept_offer(self.store, self.port, offer_id=offer_id,
                     decision="accept", bearer="bearer-1", now=NOW,
                     runtime_attempt_id=attempt_id,
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        record_attempt(self.store, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       policy_digest="sha256:" + "2" * 64)
        return offer_id

    def claimed(self, offer_id="offer-1", attempt_id=ATTEMPT):
        self.issued(offer_id, attempt_id)
        return submit_claim(self.store, self.port, offer_id=offer_id)

    def activated(self, offer_id="offer-1", attempt_id=ATTEMPT):
        self.claimed(offer_id, attempt_id)
        return activate_assignment(
            self.store, self.port, attempt_id=attempt_id,
            expect=dict(self.session.claim_answer["assignment"]))

    def offer_row(self, offer_id="offer-1"):
        return self.read("SELECT * FROM offers WHERE offer_id = ?", offer_id)

    def attempt_row(self, attempt_id=ATTEMPT):
        return self.read(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?", attempt_id)

    def read(self, sql, *operands):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(sql, operands).fetchone()
            return None if found is None else {k: found[k]
                                               for k in found.keys()}
        finally:
            beside.close()

    def spoiled(self, **members):
        """The trusted answer, with ONE member of its decision changed."""
        answer = self.session.claim_answer
        self.session.claim_answer = dict(
            answer, decision=dict(answer["decision"], **members))
        return self.session.claim_answer


class TheContextIsPersistedWithTheClaim(ContextCase):

    def test_a_claimed_offer_retains_the_exact_event_and_decision(self):
        answer = self.claimed()
        sent = self.session.claim_answer
        # THE ANSWER CARRIES ALL THREE, so a caller is told what was recorded.
        self.assertEqual(sorted(m for m in CLAIM_RESULT), sorted(CLAIM_RESULT))
        self.assertEqual(answer["claim_event"], sent["claim_event"])
        self.assertEqual(answer["decision"], sent["decision"])
        row = self.offer_row()
        self.assertEqual(row["state"], "claimed")
        self.assertEqual(row["claim_event_seq"], sent["claim_event"])
        self.assertEqual(row["claim_principal"], sent["decision"]["principal"])
        self.assertEqual(row["claim_scope"],
                         sent["decision"]["effective_scope"])
        self.assertEqual(row["claim_role"], sent["decision"]["role"])
        self.assertEqual(row["claim_grant"], sent["decision"]["grant"])
        self.assertEqual(row["claim_policy_generation"],
                         sent["decision"]["policy_generation"])
        # THE ENDPOINT IS NOT STORED TWICE. It is this row's participant, and
        # the port proved the decision's equals it.
        self.assertNotIn("claim_endpoint", row)
        self.assertEqual(row["participant"], sent["decision"]["endpoint"])

    def test_the_offer_freezes_what_the_projection_said_about_the_work(self):
        self.issued()
        row = self.offer_row()
        self.assertEqual(row["work_scope"], SCOPE)
        self.assertEqual(row["work_route"], ROUTE)
        self.assertIn("scope", PROJECTION_READ)
        self.assertIn("route", PROJECTION_READ)

    def test_activation_carries_the_context_onto_the_attempt(self):
        self.activated()
        offer = self.offer_row()
        attempt = self.attempt_row()
        for stored, held in attempts_module.CONTEXT_COLUMNS:
            self.assertEqual(attempt[stored], offer[held], stored)
        # AND THE FENCE IS STILL THE FENCE, unweakened beside it.
        self.assertEqual(attempt["assignment_participant"], WHO)
        self.assertEqual(attempt["assignment_generation"], 1)

    def test_a_commit_this_manager_never_saw_records_the_same_context(self):
        """The other path to the same columns.

        A late-recorded commit is not a lesser record: it reaches exactly the
        columns a submitted claim's would, so it is held to exactly the same
        relations.
        """
        self.issued()
        self.session.settle_answer = {"kind": "committed",
                                      "result": self.session.claim_answer}
        answer = settle_claim(self.store, self.port, offer_id="offer-1",
                              now="2026-08-24T00:10:00.000Z")
        self.assertTrue(answer["late"])
        row = self.offer_row()
        self.assertEqual(row["state"], "claimed")
        self.assertEqual(row["claim_principal"], PRINCIPAL)
        self.assertEqual(row["claim_event_seq"],
                         self.session.claim_answer["claim_event"])

    def test_a_settlement_that_authorized_nothing_retains_no_context(self):
        """The other half of the all-or-none rule.

        A retirement adopted from another settler authorized no claim, so
        context beside it would be evidence of one that never committed.
        """
        self.issued()
        self.session.settle_answer = {
            "kind": "retired",
            "record": {"disposition": "claim-refused", "reason": "no capacity"}}
        settle_claim(self.store, self.port, offer_id="offer-1",
                     now="2026-08-24T00:10:00.000Z")
        row = self.offer_row()
        self.assertEqual(row["state"], "claim-refused")
        for column in ("claim_event_seq", "claim_principal", "claim_scope",
                       "claim_role", "claim_grant",
                       "claim_policy_generation"):
            self.assertIsNone(row[column], column)


class TwoEndpointsOnePrincipal(ContextCase):
    """The acceptance's positive, measured on this manager's own rows.

    Two managers bound to two endpoint addresses the authority maps to one
    principal.  The rows differ in the ENDPOINT and agree on the PRINCIPAL --
    which is what stops two spellings becoming two identities.
    """

    def test_the_two_offers_retain_one_principal_and_two_endpoints(self):
        self.claimed()
        mine = self.offer_row()

        other_session = FakeSession(participant=ALIAS)
        # The authority maps both addresses to one principal, so the decision
        # it answers the second claim with names the SAME principal and the
        # OTHER endpoint.
        other_session.claim_answer = dict(
            other_session.claim_answer,
            decision=decision(participant=ALIAS, principal=PRINCIPAL))
        other_port = AuthorityPort(other_session, fake_claim_signature)
        issue_offer(self.store, other_port, offer_id="offer-2", work_id=WORK,
                    runtime_attempt_id="attempt-2",
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-2")
        accept_offer(self.store, other_port, offer_id="offer-2",
                     decision="accept", bearer="bearer-2", now=NOW,
                     runtime_attempt_id="attempt-2",
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        record_attempt(self.store, attempt_id="attempt-2", adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       policy_digest="sha256:" + "2" * 64)
        submit_claim(self.store, other_port, offer_id="offer-2")
        theirs = self.offer_row("offer-2")

        self.assertNotEqual(mine["participant"], theirs["participant"])
        self.assertEqual(mine["claim_principal"], theirs["claim_principal"])

    def test_two_endpoints_produce_labels_that_agree_on_the_principal(self):
        """Correction boundary item 3, as a comparison of label sets.

        Before this the two label sets shared nothing that could relate them.
        They still differ -- they are different assignments -- but they now
        AGREE on the member that says one principal is behind both.
        """
        self.activated()
        mine = attempts_module._runtime_labels(self.attempt_row())
        self.assertEqual(mine["principal"], PRINCIPAL)
        self.assertEqual(mine["effective_scope"], SCOPE)
        self.assertEqual(mine["participant"], WHO)

        other_session = FakeSession(participant=ALIAS)
        other_session.claim_answer = dict(
            other_session.claim_answer,
            assignment=dict(other_session.claim_answer["assignment"],
                            participant=ALIAS),
            decision=decision(participant=ALIAS, principal=PRINCIPAL))
        other_session.live_assignment = dict(
            other_session.claim_answer["assignment"])
        other_port = AuthorityPort(other_session, fake_claim_signature)
        issue_offer(self.store, other_port, offer_id="offer-2", work_id=WORK,
                    runtime_attempt_id="attempt-2",
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-2")
        accept_offer(self.store, other_port, offer_id="offer-2",
                     decision="accept", bearer="bearer-2", now=NOW,
                     runtime_attempt_id="attempt-2",
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        record_attempt(self.store, attempt_id="attempt-2", adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       policy_digest="sha256:" + "2" * 64)
        submit_claim(self.store, other_port, offer_id="offer-2")
        activate_assignment(
            self.store, other_port, attempt_id="attempt-2",
            expect=dict(other_session.claim_answer["assignment"]))
        theirs = attempts_module._runtime_labels(self.attempt_row("attempt-2"))

        self.assertNotEqual(mine["participant"], theirs["participant"])
        self.assertEqual(mine["principal"], theirs["principal"])
        self.assertEqual(mine["effective_scope"], theirs["effective_scope"])


class TheContextRidesEveryReplaySignatureItChanges(ContextCase):

    def test_a_changed_context_collides_rather_than_replaying_the_claim(self):
        """One operation identity, two authorizations.

        Without the context in the signature this identity means only "this
        offer reached `claimed`", so a settlement carrying a different
        principal would REPLAY the first record -- durably attributing the
        second claim's authorization to the first claim's context.
        """
        self.claimed()
        first = manager_signature("offer.settle",
                                  {"offer_id": "offer-1", "state": "claimed",
                                   "context": self.context_of(PRINCIPAL)})
        second = manager_signature("offer.settle",
                                   {"offer_id": "offer-1", "state": "claimed",
                                    "context": self.context_of(
                                        "principal:somebody-else")})
        self.assertNotEqual(first, second)
        self.assertEqual(
            self.store.operation_record("offer.settle:offer-1")["signature"],
            first)
        # AND THE STORE REFUSES THE SECOND under the same identity, which is
        # what "collides" means here rather than a comparison of two strings.
        with self.assertRaises(ContractRefusal) as caught:
            self.store.replay("offer.settle:offer-1", second,
                              kind="offer.settle")
        self.assertEqual(caught.exception.code, "operation-collision")

    def context_of(self, principal):
        answer = self.session.claim_answer
        return {"claim_event_seq": answer["claim_event"],
                "principal": principal,
                "effective_scope": answer["decision"]["effective_scope"],
                "role": answer["decision"]["role"],
                "grant": answer["decision"]["grant"],
                "policy_generation": answer["decision"]["policy_generation"]}

    def test_an_activation_under_a_different_principal_collides(self):
        """The same rule one row later.

        The attempt's activation fixes the context, so an activation of the
        same attempt against the same fence under a DIFFERENT principal is a
        different act -- and replaying the first would keep whichever arrived
        first while answering as though it were the other.
        """
        self.activated()
        held = self.attempt_row()
        signature = manager_signature(
            "assignment.activate",
            {"attempt_id": ATTEMPT,
             "expect": dict(self.session.claim_answer["assignment"]),
             "context": {stored: held[stored]
                         for stored, _ in attempts_module.CONTEXT_COLUMNS}})
        self.assertEqual(
            self.store.operation_record(
                f"assignment.activate:{ATTEMPT}")["signature"], signature)
        moved = dict({stored: held[stored]
                      for stored, _ in attempts_module.CONTEXT_COLUMNS},
                     assignment_principal="principal:somebody-else")
        with self.assertRaises(ContractRefusal) as caught:
            self.store.replay(
                f"assignment.activate:{ATTEMPT}",
                manager_signature(
                    "assignment.activate",
                    {"attempt_id": ATTEMPT,
                     "expect": dict(self.session.claim_answer["assignment"]),
                     "context": moved}),
                kind="assignment.activate")
        self.assertEqual(caught.exception.code, "operation-collision")


class ContextThisManagerCanRefuseIsRefused(ContextCase):
    """Malformed, and relationally inconsistent.

    EVERY ONE OF THESE IS REFUSED BEFORE A ROW EXISTS, which each case proves
    rather than assumes: the offer stays `accepted` and the journal holds no
    settlement.
    """

    def refuses(self, phrase):
        with self.assertRaises(ContractRefusal) as caught:
            submit_claim(self.store, self.port, offer_id="offer-1")
        self.assertIn(phrase, caught.exception.message)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(self.offer_row()["state"], "accepted")
        self.assertIsNone(
            self.store.operation_record("offer.settle:offer-1"))

    def test_a_result_missing_any_of_the_three_facts_is_refused(self):
        for member in CLAIM_RESULT:
            with self.subTest(member=member):
                self.setUp()
                self.issued()
                self.session.claim_answer = {
                    key: value
                    for key, value in self.session.claim_answer.items()
                    if key != member}
                self.refuses("the claim answer's result")

    def test_a_decision_missing_any_member_is_refused(self):
        for member in DECISION:
            with self.subTest(member=member):
                self.setUp()
                self.issued()
                answer = self.session.claim_answer
                self.session.claim_answer = dict(
                    answer,
                    decision={key: value
                              for key, value in answer["decision"].items()
                              if key != member})
                self.refuses("the claim answer's decision")

    def test_a_claim_event_that_is_not_an_act_identity_is_refused(self):
        for what, value in [("zero", 0), ("negative", -1), ("text", "1"),
                            ("a boolean, which equals 1", True),
                            ("absent", None)]:
            with self.subTest(what=what):
                self.setUp()
                self.issued()
                self.session.claim_answer = dict(self.session.claim_answer,
                                                 claim_event=value)
                self.refuses("claim event")

    def test_a_policy_generation_that_is_not_a_generation_is_refused(self):
        for what, value in [("zero", 0), ("negative", -1), ("text", "1"),
                            ("a boolean, which equals 1", True)]:
            with self.subTest(what=what):
                self.setUp()
                self.issued()
                self.spoiled(policy_generation=value)
                self.refuses("policy generation")

    def test_a_grant_provenance_this_build_cannot_place_is_refused(self):
        for value in ("assumed", "", None, 1):
            with self.subTest(value=value):
                self.setUp()
                self.issued()
                self.spoiled(grant=value)
                self.refuses("grant provenance")
        # THE OTHER HALF: a vocabulary that refuses everything is not one.
        for value in GRANT_PROVENANCE:
            with self.subTest(accepted=value):
                self.setUp()
                self.issued()
                self.spoiled(grant=value)
                submit_claim(self.store, self.port, offer_id="offer-1")
                self.assertEqual(self.offer_row()["claim_grant"], value)

    def test_a_decision_for_another_endpoint_is_refused(self):
        """RELATIONAL, and the relation is one this manager holds itself.

        The endpoint is the assignment's participant. A decision about
        somebody else does not authorize this claim however well-formed it is.
        """
        self.issued()
        self.spoiled(endpoint=ALIAS)
        self.refuses("does not authorize this claim")

    def test_a_decision_in_another_scope_is_refused(self):
        self.issued()
        self.spoiled(effective_scope="scope:somewhere-else")
        self.refuses("is not the one this offer promised")

    def test_a_decision_for_another_route_is_refused(self):
        self.issued()
        self.spoiled(role="rview")
        self.refuses("is not this offer's")

    def test_a_late_recorded_commit_is_held_to_the_same_relations(self):
        """THE OTHER PATH REACHES THE SAME COLUMNS.

        A commit this manager never saw is recorded from the settlement's
        answer, so an unowned result there would reach exactly the columns a
        submitted claim's does. Owning only the assignment on that path would
        let a decision in another scope, or no decision at all, become this
        offer's durable authorization record -- which is the shape the claim
        path was corrected for, arriving by the door nobody was watching.
        """
        for what, spoiled in [
                ("another scope",
                 lambda answer: dict(answer, decision=dict(
                     answer["decision"], effective_scope="scope:elsewhere"))),
                ("another endpoint",
                 lambda answer: dict(answer, decision=dict(
                     answer["decision"], endpoint=ALIAS))),
                ("a grant nothing can place",
                 lambda answer: dict(answer, decision=dict(
                     answer["decision"], grant="assumed"))),
                ("no decision at all",
                 lambda answer: {key: value for key, value in answer.items()
                                 if key != "decision"}),
                ("no claim event",
                 lambda answer: {key: value for key, value in answer.items()
                                 if key != "claim_event"})]:
            with self.subTest(what=what):
                self.setUp()
                self.issued()
                self.session.settle_answer = {
                    "kind": "committed",
                    "result": spoiled(self.session.claim_answer)}
                with self.assertRaises(ContractRefusal) as caught:
                    settle_claim(self.store, self.port, offer_id="offer-1",
                                 now="2026-08-24T00:10:00.000Z")
                self.assertIn("the committed claim", caught.exception.message)
                self.assertEqual(caught.exception.category, "integrity")
                self.assertEqual(self.offer_row()["state"], "accepted")
                self.assertIsNone(
                    self.store.operation_record("offer.settle:offer-1"))

    def test_a_malformed_member_is_refused(self):
        for member in ("principal", "effective_scope", "role"):
            for value in (7, "", None):
                with self.subTest(member=member, value=value):
                    self.setUp()
                    self.issued()
                    self.spoiled(**{member: value})
                    with self.assertRaises(ContractRefusal) as caught:
                        submit_claim(self.store, self.port,
                                     offer_id="offer-1")
                    self.assertEqual(caught.exception.category, "integrity")
                    self.assertEqual(self.offer_row()["state"], "accepted")


class NothingBelowTheAuthorityChoosesTheContext(ContextCase):

    def test_no_manager_entry_point_takes_a_principal_or_scope_operand(self):
        """THE OVERRIDE IS REFUSED BY NOT EXISTING.

        A refusal case would prove a check; this proves there is nothing TO
        check, which is the stronger statement and the one the correction
        boundary asks for. Every public operation in the package is inspected,
        so an operand added later is caught here rather than by imagination.
        """
        import inspect

        import baton_v12.worker_manager as package

        forbidden = {"principal", "effective_scope", "grant",
                     "policy_generation", "claim_event"}
        for name in dir(package):
            found = getattr(package, name)
            if not callable(found) or inspect.isclass(found):
                continue
            if getattr(found, "__module__", "").split(".")[0] != "baton_v12":
                continue
            taken = set(inspect.signature(found).parameters)
            self.assertEqual(taken & forbidden, set(), f"{name} takes it")

    def test_the_activation_reads_the_context_and_takes_no_operand(self):
        """`activate_assignment` fixes the context and cannot be told it.

        `expect` is the four-part fence and stays exactly that. The context
        comes off the claimed offer row -- which the port is the only writer of
        -- so a caller reaching this function has no way to name any of it.
        """
        import inspect
        taken = set(inspect.signature(activate_assignment).parameters)
        self.assertEqual(taken, {"store", "port", "attempt_id", "expect"})
        self.activated()
        attempt = self.attempt_row()
        self.assertEqual(attempt["assignment_principal"], PRINCIPAL)

    def test_an_attempt_whose_offer_retains_no_context_is_refused(self):
        """A store written before this build, failing closed.

        Schema 12 makes a context-free `claimed` row impossible going forward,
        so this is reached by hand -- which is the only way it can be reached,
        and exactly why the refusal has to exist.
        """
        self.claimed()
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("PRAGMA ignore_check_constraints = ON")
            beside.execute("UPDATE offers SET claim_principal = NULL")
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            activate_assignment(
                self.store, self.port, attempt_id=ATTEMPT,
                expect=dict(self.session.claim_answer["assignment"]))
        self.assertIn("retains no authorization context",
                      caught.exception.message)
        self.assertIsNone(self.attempt_row()["assignment_principal"])


class WhatThisManagerDeliberatelyCannotDecide(ContextCase):
    """Approver ruling M34905's acceptance clarification, stated as a case.

    The original acceptance asked for an injected claim answer with a
    "well-formed but wrong principal" to be refused.  It is not refusable and
    the ruling supersedes it: the principal the trusted authority returns is
    the only principal fact that crosses this boundary, and calling it wrong
    would take an independent endpoint-to-principal mapping -- which would make
    this manager a second authority on the exact question the correction is
    about.

    So this records the boundary rather than a check.  A different but
    internally consistent principal is PERSISTED, and the case says why that is
    the right answer.
    """

    def test_a_consistent_principal_this_manager_did_not_expect_is_kept(self):
        self.issued()
        self.spoiled(principal="principal:somebody-the-manager-never-saw")
        submit_claim(self.store, self.port, offer_id="offer-1")
        self.assertEqual(self.offer_row()["claim_principal"],
                         "principal:somebody-the-manager-never-saw")

    def test_the_manager_holds_no_endpoint_to_principal_mapping(self):
        """The structural half, so the case above is a boundary and not a gap.

        `principal_of`, `endpoints_of` and `grants_of` are configuration on the
        authority's bootstrap face. A session that carried one would let this
        manager reconstruct the mapping, and the port names the session surface
        it accepts -- so the absence is checkable rather than merely intended.
        """
        from baton_v12.worker_manager.authority_port import SESSION_OPERATIONS
        for member in ("principal_of", "endpoints_of", "grants_of",
                       "slot_holder_of_principal", "policy_generation"):
            self.assertNotIn(member, SESSION_OPERATIONS)


class EachSchemaVersionIsACleanInitializationBoundary(ContextCase):
    """W16823 raised this store to 12; the boundary is what the case is about.

    The version NUMBER is not: W32649 has since raised it to 13, and a case
    pinning 12 would have to be edited by every later Work while proving
    nothing either of them cares about. What each version means is that the
    PREVIOUS one is refused read-only, and that is version-relative already.
    """

    def test_the_version_only_ever_rises(self):
        self.assertGreaterEqual(SCHEMA_VERSION, 12)

    def test_the_previous_store_is_refused_read_only(self):
        path = os.path.join(self._root.name, "old.sqlite3")
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, "
                           "value TEXT NOT NULL)")
        for key, value in (("store_kind",
                            "baton.v12.python.worker-manager"),
                           ("schema_version", str(SCHEMA_VERSION - 1))):
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (key, value))
        connection.close()
        with open(path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(path, incarnation="m", clock=lambda: NOW)
        self.assertIn(str(SCHEMA_VERSION - 1), caught.exception.message)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before)


if __name__ == "__main__":
    unittest.main()
