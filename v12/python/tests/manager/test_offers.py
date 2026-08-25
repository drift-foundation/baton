"""W4 cut C — the offer and the claim, against a strict fake session.

PLAN item 4bd. Every case here is about one question: after a crash, can the
next incarnation tell what actually happened?

THE FAKE IS STRICT ON PURPOSE. A permissive one would let the manager call
things the real session does not have and pass anyway -- which is the opposite
of what a port is for. It answers exactly the five members `AuthorityPort` names
and records what it was asked.
"""

import os
import sqlite3
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      OFFER_TTL_SECONDS, SETTLE_SECONDS,
                                      accept_offer, certify_profile,
                                      claim_operation_id, expire_overdue,
                                      issue_offer, recover_on_restart,
                                      settle_claim, submit_claim)

NOW = "2026-08-24T00:00:00.000Z"
LATER = "2026-08-24T00:01:00.000Z"
MUCH_LATER = "2026-08-24T00:10:00.000Z"
WORK = "0000000a-W1"
UUID = "0" * 31 + "a"
WHO = "baton.claude"
PROFILE = "sha256:" + "b" * 64


class FakeSession:
    """Exactly the five members the port names, and a record of every call."""

    def __init__(self, participant=WHO, work=None, held=None):
        self.participant = participant
        self._work = work if work is not None else {
            "status": "open", "phase": "queued", "handler": None, "gate": None,
            "authority_uuid": UUID}
        self._held = held
        self.calls = []
        self.claim_answer = {"work_ref": {"authority_uuid": UUID,
                                          "work_id": WORK},
                             "participant": participant, "generation": 1}
        self.settle_answer = {"kind": "live", "record": None}
        # Cut D: the authority's own live-assignment projection, in the shape
        # the authority answers with.
        self.live_assignment = {"work_ref": {"authority_uuid": UUID,
                                             "work_id": WORK},
                                "participant": participant, "generation": 1}
        # What the authority answers when it fences a generation, ends the
        # assignment and installs the typed quiescence gate -- one transaction,
        # one document.
        self.fence_answer = {"cause": "cancelled",
                             "assignment": dict(self.live_assignment),
                             "phase": "block",
                             "gate": "runtime-quiescence:1",
                             "fenced": True}

    def project_work(self, work_id):
        self.calls.append(("project_work", work_id))
        return self._work

    def slot_holder(self, participant):
        self.calls.append(("slot_holder", participant))
        return self._held

    def assignment_of(self, work_id):
        self.calls.append(("assignment_of", work_id))
        return self.live_assignment

    def cancel(self, operands):
        self.calls.append(("cancel", dict(operands)))
        if isinstance(self.fence_answer, BaseException):
            raise self.fence_answer
        return self.fence_answer

    def claim(self, operands):
        self.calls.append(("claim", dict(operands)))
        if isinstance(self.claim_answer, BaseException):
            raise self.claim_answer
        return self.claim_answer

    def settle_operation(self, operands):
        self.calls.append(("settle_operation", dict(operands)))
        return self.settle_answer


def fake_claim_signature(work_id, participant):
    # Stands in for the authority's own derivation. The manager consumes it and
    # never recomputes it, so a fake proves the manager USES what it is given.
    return f"claim-signature({work_id},{participant})"


class OfferCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-worker-manager-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "control.sqlite3")
        self.instants = [NOW]
        self.store = self.open_store()
        self.session = FakeSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)
        certify_profile(self.store, "runtime", "reference", PROFILE)
        self.minted = []

    def open_store(self, incarnation="manager-1"):
        store = ControlStore.open(self.path, incarnation=incarnation,
                                  clock=lambda: self.instants[-1])
        self.addCleanup(store.close)
        return store

    def mint(self, bearer="bearer-1"):
        def mint_bearer():
            self.minted.append(bearer)
            return bearer
        return mint_bearer

    def issue(self, offer_id="offer-1", bearer="bearer-1", **overrides):
        operands = dict(offer_id=offer_id, work_id=WORK,
                        runtime_attempt_id="attempt-1",
                        input_digest="sha256:" + "1" * 64,
                        policy_digest="sha256:" + "2" * 64,
                        profile_digest=PROFILE, profile_name="reference",
                        mint_bearer=self.mint(bearer))
        operands.update(overrides)
        return issue_offer(self.store, self.port, **operands)

    def accept(self, offer_id="offer-1", bearer="bearer-1", now=NOW,
               decision="accept", **overrides):
        operands = dict(offer_id=offer_id, decision=decision, bearer=bearer,
                        now=now, runtime_attempt_id="attempt-1",
                        work_ref={"authority_uuid": UUID, "work_id": WORK})
        operands.update(overrides)
        return accept_offer(self.store, self.port, **operands)

    def row(self, offer_id="offer-1"):
        found = self.store._connection.execute(
            "SELECT * FROM offers WHERE offer_id = ?", (offer_id,)).fetchone()
        return None if found is None else {k: found[k] for k in found.keys()}


class TheInjectedCapabilityIsTyped(OfferCase):

    def test_a_session_missing_what_the_manager_uses_is_refused(self):
        class Partial:
            participant = WHO

            def project_work(self, work_id):
                return {}

        with self.assertRaises(ContractRefusal) as caught:
            AuthorityPort(Partial(), fake_claim_signature)
        self.assertIn("slot_holder", str(caught.exception))

    def test_a_session_that_names_no_participant_is_refused(self):
        for what, participant in [("none", None), ("empty", ""),
                                  ("a number", 7)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    AuthorityPort(FakeSession(participant=participant),
                                  fake_claim_signature)
                self.assertIn("binds", str(caught.exception))

    def test_the_bound_participant_is_owned_when_the_port_receives_it(self):
        with self.assertRaises(ContractRefusal):
            AuthorityPort(FakeSession(participant="\ud800"),
                          fake_claim_signature)

    def test_the_signature_derivation_is_injected_not_optional(self):
        with self.assertRaises(ContractRefusal):
            AuthorityPort(FakeSession(), "not callable")

    def test_every_session_operation_the_port_names_is_callable(self):
        for member in ("project_work", "slot_holder", "claim",
                       "settle_operation"):
            with self.subTest(member=member):
                session = FakeSession()
                setattr(session, member, None)
                with self.assertRaises(ContractRefusal):
                    AuthorityPort(session, fake_claim_signature)

    def test_the_port_supplies_no_participant_to_the_claim(self):
        # The session takes its claimant from its BINDING and refuses a supplied
        # one, which is the whole reason an offer's participant is checked
        # against the binding rather than carried beside it.
        self.issue()
        self.accept()
        submit_claim(self.store, self.port, offer_id="offer-1")
        claim = [operands for name, operands in self.session.calls
                 if name == "claim"][0]
        self.assertEqual(sorted(claim), ["operation_id", "work_id"])


class TheParticipantIsTheBinding(OfferCase):

    def test_an_offer_naming_another_participant_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.issue(participant="baton.someone-else")
        self.assertIn("would be taken by the binding", str(caught.exception))
        self.assertIsNone(self.row())

    def test_the_offer_records_the_binding(self):
        answer = self.issue()
        self.assertEqual(answer["participant"], WHO)
        self.assertEqual(self.row()["participant"], WHO)


class WhatMustHoldBeforeEntropyIsSpent(OfferCase):

    def test_the_mint_capability_is_typed_before_authority_reads(self):
        with self.assertRaises(ContractRefusal):
            self.issue(mint_bearer=None)
        self.assertEqual(self.session.calls, [])
        self.assertIsNone(self.row())

    def test_the_injected_work_projection_is_owned_before_use(self):
        self.session._work = 7
        with self.assertRaises(ContractRefusal):
            self.issue()
        self.assertEqual(self.minted, [])
        self.assertIsNone(self.row())

    def test_the_injected_work_projection_is_a_closed_document(self):
        self.session._work["unexpected"] = "member"
        with self.assertRaises(ContractRefusal):
            self.issue()
        self.assertEqual(self.minted, [])
        self.assertIsNone(self.row())

    def test_the_injected_work_projection_owns_the_members_it_persists(self):
        self.session._work["authority_uuid"] = 7
        with self.assertRaises(ContractRefusal):
            self.issue()
        self.assertEqual(self.minted, [])
        self.assertIsNone(self.row())

    def test_a_nonpositive_ttl_is_refused_before_entropy(self):
        with self.assertRaises(ContractRefusal):
            self.issue(ttl_seconds=-1)
        self.assertEqual(self.minted, [])
        self.assertIsNone(self.row())

    def test_a_positive_ttl_must_fit_deadline_arithmetic_before_reads(self):
        with self.assertRaises(ContractRefusal):
            self.issue(ttl_seconds=10 ** 100)
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.minted, [])
        self.assertIsNone(self.row())

    def test_the_deadline_source_must_be_representable_before_reads(self):
        self.instants[-1] = "2026-99-99T99:99:99.999Z"
        with self.assertRaises(ContractRefusal):
            self.issue()
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.minted, [])
        self.assertIsNone(self.row())

    def test_cut_c_text_is_encodable_before_any_sql_read(self):
        surrogate = "\ud800"
        for operation in (
                lambda: accept_offer(
                    self.store, self.port, offer_id="offer-" + surrogate,
                    decision="accept", bearer="bearer", now=NOW,
                    runtime_attempt_id="attempt-1",
                    work_ref={"authority_uuid": UUID, "work_id": WORK}),
                lambda: expire_overdue(self.store, "2026-" + surrogate)):
            with self.subTest(operation=operation):
                with self.assertRaises(ContractRefusal):
                    operation()

    def test_every_public_offer_lookup_proves_text_before_sql(self):
        surrogate = "offer-\ud800"
        for operation in (
                lambda: submit_claim(
                    self.store, self.port, offer_id=surrogate),
                lambda: settle_claim(
                    self.store, self.port, offer_id=surrogate, now=NOW),
                lambda: expire_overdue(
                    self.store, NOW, work_id="work-\ud800")):
            with self.subTest(operation=operation):
                with self.assertRaises(ContractRefusal):
                    operation()

    def test_profile_certification_owns_key_text_before_composing_sql(self):
        for what, kind, name in [("kind", 7, "profile"),
                                 ("name", "runtime", 7)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    certify_profile(self.store, kind, name, PROFILE)

    def test_time_comparison_refuses_text_outside_the_instant_grammar(self):
        self.issue()
        with self.assertRaises(ContractRefusal):
            expire_overdue(self.store, "not-an-instant")
        self.assertEqual(self.row()["state"], "issued")

    def test_time_comparison_refuses_a_calendar_impossible_instant(self):
        self.issue()
        with self.assertRaises(ContractRefusal):
            expire_overdue(self.store, "2026-99-99T99:99:99.999Z")
        self.assertEqual(self.row()["state"], "issued")

    def test_the_work_must_be_open_queued_unclaimed_and_ungated(self):
        for what, work in [
                ("closed", {"status": "closed", "phase": "queued",
                            "handler": None, "gate": None,
                            "authority_uuid": UUID}),
                ("active", {"status": "open", "phase": "active",
                            "handler": None, "gate": None,
                            "authority_uuid": UUID}),
                ("claimed", {"status": "open", "phase": "queued",
                             "handler": WHO, "gate": None,
                             "authority_uuid": UUID}),
                ("gated", {"status": "open", "phase": "queued",
                           "handler": None, "gate": "quiescence:x",
                           "authority_uuid": UUID})]:
            with self.subTest(what=what):
                self.session._work = work
                with self.assertRaises(ContractRefusal):
                    self.issue(offer_id=f"offer-{what}")
                self.assertEqual(self.minted, [], "entropy was spent")

    def test_certification_is_unavoidable(self):
        """A check a caller can skip by not mentioning it is not a boundary.

        The frozen host's comparison was conditional on an operand being
        supplied, so omitting it issued an offer with no certification check at
        all -- and its happy-path fixtures omitted it throughout. There is no
        operand here: the control store's own record is the only fact.
        """
        store = ControlStore.open(
            os.path.join(self.root, "uncertified.sqlite3"),
            incarnation="m", clock=lambda: NOW)
        self.addCleanup(store.close)
        with self.assertRaises(ContractRefusal) as caught:
            issue_offer(store, self.port, offer_id="offer-1", work_id=WORK,
                        runtime_attempt_id="attempt-1",
                        input_digest="sha256:" + "1" * 64,
                        policy_digest="sha256:" + "2" * 64,
                        profile_digest=PROFILE, profile_name="reference",
                        mint_bearer=self.mint())
        self.assertEqual(caught.exception.code, "profile-uncertified")
        # THE REASON, not only the code. Both refusals here carry
        # `policy/profile-uncertified`, so a case reading the code alone cannot
        # tell "nothing certifies this" from "we certified something else" --
        # and a mutation removing the first branch measured zero until this
        # asserted which one answered.
        self.assertIn("nothing certifies", str(caught.exception))
        self.assertEqual(self.minted, [])

    def test_a_profile_digest_the_store_does_not_certify_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.issue(profile_digest="sha256:" + "9" * 64)
        self.assertEqual(caught.exception.code, "profile-uncertified")
        self.assertIn("has certified", str(caught.exception))
        self.assertEqual(self.minted, [])

    def test_capacity_is_checked_before_a_bearer_is_minted(self):
        self.session._held = "0000000a-W9"
        with self.assertRaises(ContractRefusal) as caught:
            self.issue()
        self.assertIn("already holds", str(caught.exception))
        self.assertEqual(self.minted, [], "a bearer was minted for a claim "
                                          "that cannot be taken")

    def test_an_exact_replay_refuses_without_minting_anything(self):
        """The bearer existed only in the process that minted it.

        The frozen host minted first, so an exact replay answered with the FIRST
        offer's durable verifier beside a newly minted bearer that does not
        derive it -- a secret the holder cannot use and cannot tell is unusable.
        """
        self.issue()
        self.assertEqual(len(self.minted), 1)
        with self.assertRaises(ContractRefusal) as caught:
            self.issue()
        self.assertIn("already issued", str(caught.exception))
        self.assertEqual(len(self.minted), 1, "a second bearer was minted")
        # THE SECRET, not the word. My first assertion looked for "bearer" and
        # the refusal legitimately says it -- a case that would have passed only
        # by the message being less clear.
        self.assertNotIn("bearer-1", str(caught.exception))


class TheOfferRecordsTheVerifierAndReturnsTheBearer(OfferCase):

    def test_the_bearer_is_returned_and_never_stored(self):
        answer = self.issue(bearer="the-secret")
        self.assertEqual(answer["bearer"], "the-secret")
        self.assertEqual(answer["verifier"], digest("the-secret"))
        stored = self.row()
        self.assertEqual(stored["verifier"], digest("the-secret"))
        self.assertNotIn("the-secret", str(stored))
        # And not in the journal either.
        record = self.store.operation_record("offer.issue:offer-1")
        self.assertNotIn("the-secret", str(record))

    def test_every_durable_operand_rides_the_signature(self):
        # An operation identity that ignores operands is not an identity: the
        # frozen host covered only (offer, work, participant), so a changed
        # policy digest REPLAYED the first offer as though it were the same
        # request.
        self.issue()
        with self.assertRaises(ContractRefusal) as caught:
            self.issue(policy_digest="sha256:" + "7" * 64)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_the_authority_is_part_of_the_offer_identity(self):
        # The frozen host's signature carried the local Work id while the row
        # persists the authority too, so reusing an issue identity against
        # ANOTHER authority read as an exact replay rather than a collision. The
        # authority a Work belongs to is as durable as the Work.
        self.issue()
        # THE SAME INSTANT, so only the authority differs. My first version also
        # advanced the clock, which changes `expires_at` -- itself a signed
        # operand -- so the collision fired for that instead and removing the
        # authority from the signature measured zero. A case that varies two
        # things measures neither.
        self.session._work = dict(self.session._work, authority_uuid="9" * 32)
        with self.assertRaises(ContractRefusal) as caught:
            self.issue()
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_concurrent_exact_issuer_is_told_it_lost(self):
        """The COMMIT MARKER, witnessed where it can actually be reached.

        The optimistic replay check answers the sequential case and two
        concurrent exact issuers both pass it -- the winner commits its verifier
        and `transact` hands the LOSER that committed record. Returning it beside
        the loser's freshly minted bearer is the unusable pair the whole step
        exists to prevent, and provenance must come from the journal rather than
        from any property of the secret.

        The window is opened on purpose, because a race that has to be timed is
        a case that passes when the timing is kind.
        """
        import sqlite3
        competitor = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(competitor.close)
        original = self.store.replay
        peeked = []

        def racing_replay(operation_id, signature, *, kind=None):
            answer = original(operation_id, signature, kind=kind)
            if operation_id == "offer.issue:offer-1" and not peeked:
                peeked.append("peeked")
                # The other manager wins, right here, with ITS bearer.
                competitor.execute(
                    "INSERT INTO offers (offer_id, work_id, authority_uuid, "
                    "participant, runtime_attempt_id, incarnation, "
                    "input_digest, policy_digest, profile_digest, verifier, "
                    "issued_at, expires_at, state) VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,'issued')",
                    ("offer-1", WORK, UUID, WHO, "attempt-1", "other",
                     "sha256:" + "1" * 64, "sha256:" + "2" * 64, PROFILE,
                     digest("their-bearer"), NOW, "2030-01-01T00:00:00.000Z"))
                competitor.execute(
                    "INSERT INTO operations (operation_id, kind, signature, "
                    "state, result, settled_at) VALUES (?,?,?,'committed',?,?)",
                    ("offer.issue:offer-1", "offer.issue", signature,
                     '{"verifier":"' + digest("their-bearer") + '"}', NOW))
            return answer

        self.store.replay = racing_replay
        with self.assertRaises(ContractRefusal) as caught:
            self.issue()
        self.assertIn("issued concurrently", str(caught.exception))
        self.assertNotIn("bearer-1", str(caught.exception))

    def test_a_boolean_ttl_is_not_a_duration(self):
        # `True` is an `int` in Python and is greater than zero, so without the
        # bool check it becomes a one-second offer -- accepted, committed and
        # expiring immediately. A mutation removing that check measured zero
        # until this case existed.
        for what, ttl in [("true", True), ("false", False)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    self.issue(offer_id=f"offer-{what}", ttl_seconds=ttl)
                self.assertEqual(self.minted, [])

    def test_one_live_offer_per_work(self):
        # `assertRaises(Exception)` is what this said first, and it passed on a
        # raw `sqlite3.IntegrityError` -- the weak assertion I have criticised
        # in other people's cases, written by me. It names the closed pair now,
        # and naming it is what found that the index violation was escaping as a
        # driver fault.
        self.issue()
        with self.assertRaises(ContractRefusal) as caught:
            self.issue(offer_id="offer-2", bearer="bearer-2")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("live offer", str(caught.exception))


class AcceptanceBindsAndConsumes(OfferCase):

    def test_acceptance_fields_are_all_frozen_or_all_absent_in_the_schema(self):
        self.issue()
        self.issue(offer_id="offer-2", bearer="bearer-2",
                   work_id="0000000a-W2")
        for what, statement, operands in [
                ("accepted without its frozen identity",
                 "UPDATE offers SET state = 'accepted' WHERE offer_id = ?",
                 ("offer-1",)),
                ("issued carrying acceptance fields",
                 "UPDATE offers SET accepted_at = ?, settle_by = ? "
                 "WHERE offer_id = ?", (NOW, LATER, "offer-2"))]:
            with self.subTest(what=what):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.store._connection.execute(statement, operands)

    def test_the_injected_claim_signature_result_is_durable_text(self):
        self.issue()
        self.port = AuthorityPort(self.session, lambda work_id, participant: None)
        with self.assertRaises(ContractRefusal):
            self.accept()
        self.assertEqual(self.row()["state"], "issued")

    def test_a_decision_naming_another_attempt_or_work_is_refused(self):
        self.issue()
        for what, overrides in [
                ("another attempt", {"runtime_attempt_id": "attempt-9"}),
                ("another work", {"work_ref": {"authority_uuid": UUID,
                                               "work_id": "0000000a-W9"}}),
                ("another authority", {"work_ref": {"authority_uuid": "9" * 32,
                                                    "work_id": WORK}})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    self.accept(**overrides)
                self.assertEqual(self.row()["state"], "issued")

    def test_a_decision_without_the_bearer_is_refused(self):
        self.issue()
        with self.assertRaises(ContractRefusal) as caught:
            self.accept(bearer="not-the-bearer")
        self.assertEqual(caught.exception.code, "capability")
        self.assertEqual(self.row()["state"], "issued")

    def test_acceptance_freezes_the_intent_and_the_claim_identity(self):
        self.issue()
        answer = self.accept()
        stored = self.row()
        self.assertEqual(stored["state"], "accepted")
        self.assertEqual(stored["verifier_spent"], 1)
        self.assertEqual(stored["intent_digest"], answer["intent_digest"])
        self.assertEqual(stored["claim_operation_id"],
                         claim_operation_id("offer-1", answer["intent_digest"]))
        # THE AUTHORITY'S OWN SIGNATURE, consumed rather than recomputed.
        self.assertEqual(stored["claim_signature"],
                         fake_claim_signature(WORK, WHO))
        self.assertEqual(stored["settle_by"], _later(NOW, SETTLE_SECONDS))

    def test_the_acceptance_deadline_fields_are_part_of_the_invariant(self):
        # The reviewer's row omits all five, and a CHECK naming only three still
        # refuses it -- so the deadline half was untested. This row carries the
        # three and omits `accepted_at` and `settle_by`, which is the shape an
        # acceptance that froze an identity it cannot settle would leave.
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._connection.execute(
                "INSERT INTO offers (offer_id, work_id, authority_uuid, "
                "participant, runtime_attempt_id, incarnation, input_digest, "
                "policy_digest, profile_digest, verifier, issued_at, "
                "expires_at, state, intent_digest, claim_operation_id, "
                "claim_signature) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,'accepted',?,?,?)",
                ("offer-half", WORK, UUID, WHO, "attempt-1", "m", "d", "d",
                 PROFILE, "v", NOW, MUCH_LATER, "intent", "claim:x", "sig"))

    def test_the_bearer_is_single_use_across_every_outcome(self):
        # A DIFFERENT WORK PER SUBTEST. My first version reused one, and the
        # one-live-offer index refused the second issue -- the rule working, and
        # my fixture asking for something the contract forbids.
        for index, (what, decision) in enumerate(
                [("acceptance", "accept"), ("decline", "decline")], start=2):
            with self.subTest(what=what):
                offer_id = f"offer-{what}"
                work_id = f"0000000a-W{index}"
                self.issue(offer_id=offer_id, bearer=f"bearer-{what}",
                           work_id=work_id)
                self.accept(offer_id=offer_id, bearer=f"bearer-{what}",
                            decision=decision,
                            work_ref={"authority_uuid": UUID,
                                      "work_id": work_id})
                self.assertEqual(self.row(offer_id)["verifier_spent"], 1)
                with self.assertRaises(ContractRefusal):
                    self.accept(offer_id=offer_id, bearer=f"bearer-{what}",
                                decision="accept",
                                work_ref={"authority_uuid": UUID,
                                          "work_id": work_id})

    def test_a_decline_cannot_be_replayed_into_an_acceptance(self):
        self.issue()
        self.accept(decision="decline", reason="busy")
        self.assertEqual(self.row()["state"], "declined")
        with self.assertRaises(ContractRefusal):
            self.accept(decision="accept")
        self.assertEqual(self.row()["state"], "declined")


class ExpiryIsASettlement(OfferCase):

    def test_a_late_decision_settles_the_row_and_still_refuses(self):
        """The frozen host threw and left the row `issued`.

        So the Work could never receive another offer, and the bearer stayed
        replayable against the single-use rule.
        """
        self.issue()
        with self.assertRaises(ContractRefusal):
            self.accept(now=MUCH_LATER)
        stored = self.row()
        self.assertEqual(stored["state"], "expired")
        self.assertEqual(stored["verifier_spent"], 1)

    def test_an_offer_nobody_answered_is_expired_by_the_managers_clock(self):
        # A bound that depends on the holder of an expired authorization
        # sending one more message is not a bound.
        self.issue()
        self.assertEqual(expire_overdue(self.store, MUCH_LATER), ["offer-1"])
        self.assertEqual(self.row()["state"], "expired")

    def test_expiry_never_destroys_an_accepted_authorization(self):
        """The frozen host's [P1]: a terminal transition that CASed from any
        state.

        Both callers act from an earlier `issued` read, and another manager can
        accept in between -- a stale expiry then destroyed the durable
        authorization and the fixed claim identity acceptance had just frozen.
        Expiry sweeps `accepted` rows too, so this is reachable rather than
        theoretical.
        """
        self.issue()
        accepted = self.accept()
        expire_overdue(self.store, MUCH_LATER)
        stored = self.row()
        self.assertEqual(stored["state"], "accepted")
        self.assertEqual(stored["claim_operation_id"],
                         accepted["claim_operation_id"])
        self.assertEqual(stored["claim_signature"], accepted["claim_signature"])

    def test_expiry_frees_the_work_for_another_offer(self):
        self.issue()
        self.instants.append(MUCH_LATER)
        second = self.issue(offer_id="offer-2", bearer="bearer-2")
        self.assertEqual(second["offer_id"], "offer-2")
        self.assertEqual(self.row("offer-1")["state"], "expired")


class TheClaimAndItsSettlement(OfferCase):

    def test_the_injected_claim_answer_is_owned_before_recording(self):
        self.issue()
        self.accept()
        self.session.claim_answer = 7
        with self.assertRaises(ContractRefusal):
            submit_claim(self.store, self.port, offer_id="offer-1")
        self.assertEqual(self.row()["state"], "accepted")

    def test_the_injected_claim_answer_owns_its_assignment_identity(self):
        for what, answer in [
                ("another participant",
                 {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                  "participant": "baton.someone-else", "generation": 1}),
                ("a non-generation",
                 {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                  "participant": WHO, "generation": "not-a-generation"})]:
            with self.subTest(what=what):
                self.setUp()
                self.issue()
                self.accept()
                self.session.claim_answer = answer
                with self.assertRaises(ContractRefusal):
                    submit_claim(self.store, self.port, offer_id="offer-1")
                self.assertEqual(self.row()["state"], "accepted")

    def test_a_claim_answer_must_name_the_offers_authority(self):
        self.issue()
        self.accept()
        self.session.claim_answer = {
            "work_ref": {"authority_uuid": "f" * 32, "work_id": WORK},
            "participant": WHO, "generation": 1}
        with self.assertRaises(ContractRefusal):
            submit_claim(self.store, self.port, offer_id="offer-1")
        self.assertEqual(self.row()["state"], "accepted")

    def test_a_late_committed_claim_must_name_the_offers_authority(self):
        self.issue()
        self.accept()
        self.session.settle_answer = {
            "kind": "committed",
            "result": {
                "work_ref": {"authority_uuid": "f" * 32,
                             "work_id": WORK},
                "participant": WHO, "generation": 1}}
        with self.assertRaises(ContractRefusal):
            settle_claim(self.store, self.port, offer_id="offer-1", now=NOW)
        self.assertEqual(self.row()["state"], "accepted")

    def test_the_injected_settlement_answer_is_owned_before_branching(self):
        self.issue()
        self.accept()
        self.session.settle_answer = 7
        with self.assertRaises(ContractRefusal):
            settle_claim(self.store, self.port, offer_id="offer-1", now=NOW)
        self.assertEqual(self.row()["state"], "accepted")

    def test_a_retirement_owns_the_reason_and_disposition_it_adopts(self):
        self.issue()
        self.accept()
        self.session.settle_answer = {
            "kind": "retired",
            "record": {"reason": 7, "disposition": "claim-refused"}}
        with self.assertRaises(ContractRefusal):
            settle_claim(self.store, self.port, offer_id="offer-1", now=NOW)
        self.assertEqual(self.row()["state"], "accepted")

    def test_a_committed_settlement_answer_requires_its_result(self):
        self.issue()
        self.accept()
        self.session.settle_answer = {"kind": "committed"}
        with self.assertRaises(ContractRefusal):
            settle_claim(self.store, self.port, offer_id="offer-1", now=NOW)
        self.assertEqual(self.row()["state"], "accepted")

    def test_an_adopted_offer_deadline_is_owned_before_it_is_compared(self):
        self.issue()
        self.accept()
        self.store._connection.execute(
            "UPDATE offers SET settle_by = ? WHERE offer_id = ?",
            ("not-an-instant", "offer-1"))
        with self.assertRaises(ContractRefusal):
            settle_claim(self.store, self.port, offer_id="offer-1", now=NOW)
        self.assertEqual(self.row()["state"], "accepted")

    def accepted(self):
        self.issue()
        return self.accept()

    def test_the_claim_records_what_the_authority_returned(self):
        # The frozen host read `result.assignment` while the session returns the
        # assignment directly -- so the authority held a live generation while
        # the manager durably recorded null. A record that disagrees with the
        # authority is worse than no record: a restart trusts it.
        accepted = self.accepted()
        answer = submit_claim(self.store, self.port, offer_id="offer-1")
        self.assertEqual(answer["assignment"], self.session.claim_answer)
        stored = self.row()
        self.assertEqual(stored["state"], "claimed")
        self.assertEqual(stored["claim_generation"], 1)
        claim = [operands for name, operands in self.session.calls
                 if name == "claim"][0]
        self.assertEqual(claim["operation_id"], accepted["claim_operation_id"])

    def test_a_claim_needs_an_accepted_offer(self):
        self.issue()
        with self.assertRaises(ContractRefusal):
            submit_claim(self.store, self.port, offer_id="offer-1")

    def test_before_the_deadline_a_lost_result_may_only_be_observed(self):
        """NO ADAPTER WRITE WHILE THE OUTCOME IS AMBIGUOUS.

        A read saying "not committed" proves only its own instant, so retiring
        early could close an identity the authority is still going to honour.
        """
        self.accepted()
        self.session.settle_answer = {"kind": "live", "record": None}
        answer = settle_claim(self.store, self.port, offer_id="offer-1",
                              now=NOW)
        self.assertFalse(answer["settled"])
        self.assertEqual(self.row()["state"], "accepted")
        asked = [operands for name, operands in self.session.calls
                 if name == "settle_operation"][0]
        self.assertFalse(asked["may_retire"])

    def test_at_the_deadline_retirement_is_permitted(self):
        self.accepted()
        settle_claim(self.store, self.port, offer_id="offer-1",
                     now=MUCH_LATER)
        asked = [operands for name, operands in self.session.calls
                 if name == "settle_operation"][0]
        self.assertTrue(asked["may_retire"])

    def test_positive_evidence_permits_immediate_retirement(self):
        self.accepted()
        settle_claim(self.store, self.port, offer_id="offer-1", now=NOW,
                     refused_evidence="the authority refused the claim")
        asked = [operands for name, operands in self.session.calls
                 if name == "settle_operation"][0]
        self.assertTrue(asked["may_retire"])
        self.assertEqual(asked["disposition"], "claim-refused")

    def test_the_frozen_signature_is_what_settles(self):
        # Passing anything else -- including nothing -- would be an operation
        # collision against a real committed claim.
        accepted = self.accepted()
        settle_claim(self.store, self.port, offer_id="offer-1", now=NOW)
        asked = [operands for name, operands in self.session.calls
                 if name == "settle_operation"][0]
        self.assertEqual(asked["signature"], accepted["claim_signature"])

    def test_a_commit_the_manager_never_saw_is_recorded_late(self):
        self.accepted()
        self.session.settle_answer = {
            "kind": "committed",
            "result": {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                       "participant": WHO, "generation": 4}}
        answer = settle_claim(self.store, self.port, offer_id="offer-1",
                              now=MUCH_LATER)
        self.assertTrue(answer["late"])
        stored = self.row()
        self.assertEqual(stored["state"], "claimed")
        self.assertEqual(stored["claim_generation"], 4)

    def test_an_existing_retirement_is_adopted_rather_than_reinvented(self):
        # Whoever retired the identity first decided what it means, and a second
        # manager inventing its own answer would give one operation two
        # meanings.
        self.accepted()
        self.session.settle_answer = {
            "kind": "retired",
            "record": {"disposition": "claim-refused", "reason": "no capacity"}}
        answer = settle_claim(self.store, self.port, offer_id="offer-1",
                              now=MUCH_LATER)
        self.assertTrue(answer["adopted"])
        self.assertEqual(self.row()["state"], "claim-refused")
        self.assertEqual(self.row()["decision_reason"], "no capacity")


class TheRestartRulesAreAsymmetric(OfferCase):

    def test_an_issued_offer_from_another_incarnation_is_abandoned(self):
        # Nothing durable says the bearer was ever delivered, and a manager that
        # honoured it would be trusting a secret it cannot account for.
        self.issue()
        self.store.close()
        successor = self.open_store(incarnation="manager-2")
        answer = recover_on_restart(successor, now=NOW)
        self.assertEqual(answer["abandoned"], ["offer-1"])
        found = successor._connection.execute(
            "SELECT state FROM offers WHERE offer_id='offer-1'").fetchone()
        self.assertEqual(found["state"], "abandoned-after-restart")

    def test_this_incarnations_own_issued_offer_is_left_alone(self):
        # Several managers coordinate through the shared store, so abandoning an
        # offer merely because this process did not mint its bearer would let
        # one live manager destroy another's work.
        self.issue()
        answer = recover_on_restart(self.store, now=NOW)
        self.assertEqual(answer["abandoned"], [])
        self.assertEqual(self.row()["state"], "issued")

    def test_an_accepted_offer_is_recoverable_across_incarnations(self):
        self.issue()
        accepted = self.accept()
        self.store.close()
        successor = self.open_store(incarnation="manager-2")
        answer = recover_on_restart(successor, now=NOW)
        self.assertEqual(answer["abandoned"], [])
        self.assertEqual(answer["recoverable"],
                         [{"offer_id": "offer-1",
                           "claim_operation_id": accepted["claim_operation_id"],
                           "settle_by": accepted["settle_by"]}])


def _later(instant, seconds):
    # The deadline boundary owns this now; the test helper follows it rather
    # than keeping a second opinion about what a deadline is.
    from baton_v12.worker_manager import boundaries
    return boundaries.deadline(instant, seconds, "a deadline")


if __name__ == "__main__":
    unittest.main()
