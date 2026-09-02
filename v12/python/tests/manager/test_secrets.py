"""W6630 — §13: the one deliberate secret stays off every durable surface.

`work/records/2026/08/finding-v12-manager-section-13-security/`.

THE ACCEPTANCE, and every case below belongs to one of its lines:

  - the walk, at any depth, over every durable and public surface;
  - both halves — named members and known values, with CONTAINMENT for
    values;
  - assignment-scoped delivery authority; secrets never in protocol identity;
  - bounded diagnostics that cannot themselves leak;
  - restart and cancellation semantics that FORGET rather than persist.

THE ONE AN IMPLEMENTER IS MOST LIKELY TO MISS is containment. An interpolated
refusal message carries the bearer just as durably as a bare member does, so a
refusal that quotes an operand is a durable surface like a label, a log line, a
store row or an artifact. Several cases below exist only for that.

AND THE SWEEP IS ENUMERATED, NOT PROBED, IN BOTH HALVES. The acceptance names
durable AND public surfaces, and a first version of this file derived only the
durable one — which review [P1] showed was not a narrowing on paper but a live
gap: `manager_signature` returned protocol identity carrying a live bearer and
`seal_refusal` returned a portable diagnostic carrying one, both refused only
by a later SQL write that the caller had already got ahead of.

So there are two derived universes. `EveryDurableWriterIsGuarded` reads every
INSERT and UPDATE from the AST. `EveryPublicSurfaceIsAccountedFor` reads every
exported callable from `__all__` — the package's own promise — and requires
each to be in exactly one declared class, with the constructing ones PROBED
against a live bearer so their entries are facts rather than claims. A public
constructor added later without a walk fails the gate rather than waiting for
somebody to think of probing it.
"""

import ast
import inspect
import json
import os
import pathlib
import sqlite3
import tempfile
import threading
import unittest

import baton_v12.worker_manager as worker_manager
from baton_v12 import contracts
from baton_v12.contracts import errors, secrets
from baton_v12.contracts.errors import (DEFECT_REDACTED,
                                        SECRET_LEAK_MESSAGE)
from baton_v12.contracts import (ContractRefusal, MESSAGE_LIMIT,
                                 SECRET_MEMBERS,
                                 check_manifest_structure,
                                 check_no_durable_secret, digest,
                                 forget_secret, held_secret, live_secret,
                                 remember_secret)
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      accept_offer, certify_profile,
                                      issue_offer, manager_signature,
                                      schema, seal_refusal)

from .test_offers import (FakeSession, NOW, PROFILE, UUID, WHO, WORK,
                          fake_claim_signature)
# THE INTERROGATION WORLD, borrowed rather than rebuilt. Reaching
# `record_inquiry_answer` needs an accepted offer, a recorded attempt, an
# activated assignment, an open session and an adopted provider identity — and
# a second copy of that setup here would be a second thing to keep true.
from .test_interrogation import ATTEMPT, Agent, InterrogationCase

BEARER = "bearer-" + "9" * 40
PACKAGE = pathlib.Path(worker_manager.__file__).resolve().parent


class SecretCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-secrets-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        certify_profile(self.store, "runtime", "reference", PROFILE)
        self.session = FakeSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)
        # NOTHING IS LIVE AT REST. A registry that leaked an entry between
        # cases would make a later one pass for the wrong reason.
        self.addCleanup(self.assertFalse, live_secret(BEARER))


# -- the registry ------------------------------------------------------------

class TheRegistryHoldsOnlyWhatIsLive(SecretCase):

    def test_a_value_is_live_only_while_it_is_held(self):
        self.assertFalse(live_secret(BEARER))
        with held_secret(BEARER):
            self.assertTrue(live_secret(BEARER))
        self.assertFalse(live_secret(BEARER))

    def test_registrations_nest_and_the_inner_release_frees_nothing(self):
        """An outer owner holding a bearer and an inner scope using the same
        value are two registrations of ONE value. Presence cannot express
        shared ownership; a count can."""
        with held_secret(BEARER):
            with held_secret(BEARER):
                self.assertTrue(live_secret(BEARER))
            self.assertTrue(live_secret(BEARER),
                            "the inner scope freed the outer owner's value")
        self.assertFalse(live_secret(BEARER))

    def test_an_act_that_raises_still_forgets(self):
        """However the act ends. A bearer left registered by a failure would
        make every later durable write refuse a value nobody holds."""
        with self.assertRaises(ValueError):
            with held_secret(BEARER):
                raise ValueError("the act failed")
        self.assertFalse(live_secret(BEARER))

    def test_the_release_answers_about_the_value_not_about_the_call(self):
        """An unbalanced release of a value that is already gone has nothing
        to decrement, and reporting "still live" there would contradict the
        guard, which correctly permits it."""
        self.assertIs(forget_secret(BEARER), False)
        remember_secret(BEARER)
        remember_secret(BEARER)
        self.assertIs(forget_secret(BEARER), True)
        self.assertIs(forget_secret(BEARER), False)
        self.assertFalse(live_secret(BEARER))

    def test_a_remembered_secret_is_non_empty_text(self):
        for spoiled in ("", None, 1, b"bytes", ["a"]):
            with self.subTest(value=spoiled):
                with self.assertRaises(ContractRefusal) as caught:
                    remember_secret(spoiled)
                self.assertEqual(caught.exception.code, "schema")

    def test_the_count_survives_concurrent_owners(self):
        """A manager may serve several threads, and a count two of them
        increment is a count that loses one unless the arithmetic is
        guarded."""
        started = threading.Barrier(8)

        def hold():
            started.wait()
            with held_secret(BEARER):
                pass

        threads = [threading.Thread(target=hold) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertFalse(live_secret(BEARER),
                         "a concurrent release left the value live")


class RestartAndCancellationForget(SecretCase):

    def test_the_registry_is_process_state_and_persists_nothing(self):
        """Restart semantics, asserted rather than asserted-about: a bearer
        held during an act reaches no column of the store, so a fresh process
        starts knowing nothing."""
        with held_secret(BEARER):
            pass
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        tables = [row[0] for row in beside.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")]
        for table in tables:
            with self.subTest(table=table):
                rows = beside.execute(f"SELECT * FROM {table}").fetchall()
                self.assertNotIn(BEARER, json.dumps(rows, default=str))

    def test_a_cancelled_act_leaves_no_registration_behind(self):
        with self.assertRaises(KeyboardInterrupt):
            with held_secret(BEARER):
                raise KeyboardInterrupt
        self.assertFalse(live_secret(BEARER))


# -- the walk ----------------------------------------------------------------

class BothHalvesAreNeededAndNeitherImpliesTheOther(SecretCase):

    def test_a_member_named_for_a_secret_is_refused_whatever_it_holds(self):
        """The name says the value is one. Nothing is registered here, so
        this half is proved to stand on its own."""
        for member in SECRET_MEMBERS:
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    check_no_durable_secret({member: "anything at all"},
                                            what="a durable row")
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "secret-leak"))

    def test_the_named_members_are_matched_case_insensitively(self):
        for member in ("Authorization", "CLAIM_TOKEN", "Private_Key"):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal):
                    check_no_durable_secret({member: "x"}, what="a durable row")

    def test_a_live_value_is_refused_whatever_member_it_arrives_in(self):
        """A leak does not depend on what the leaking member was called."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                check_no_durable_secret({"diagnostic": BEARER},
                                        what="a durable row")
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_neither_half_is_enough_on_its_own(self):
        """A name-only check reads as a leak boundary while being a naming
        convention; a value-only check misses the member whose name says the
        value is a secret."""
        check_no_durable_secret({"diagnostic": BEARER}, what="a durable row")
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                check_no_durable_secret({"diagnostic": BEARER},
                                        what="a durable row")
        check_no_durable_secret({"note": "nothing secret"},
                                what="a durable row")
        with self.assertRaises(ContractRefusal):
            check_no_durable_secret({"password": "nothing registered"},
                                    what="a durable row")


class TheValueTestIsContainment(SecretCase):

    def test_an_interpolated_bearer_is_a_leak(self):
        """THE ONE MOST LIKELY TO BE MISSED. A refusal message that quoted an
        operand carries the bearer just as durably as a bare member does."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                check_no_durable_secret(
                    {"message": f"offer 'o-1' does not carry {BEARER!r}"},
                    what="a sealed refusal")
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_equality_would_have_missed_it(self):
        """Stated as the property rather than as prose: the leaking string is
        not the bearer, it CONTAINS it."""
        carrier = f"...{BEARER}..."
        self.assertNotEqual(carrier, BEARER)
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                check_no_durable_secret(carrier, what="a durable surface")

    def test_a_bare_string_surface_is_walked(self):
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                check_no_durable_secret(BEARER, what="a label")


class ItIsAWalkAtAnyDepth(SecretCase):

    def test_a_bearer_nested_in_a_copied_body_is_as_durable_as_one_at_the_root(
            self):
        deep = {"a": {"b": [{"c": {"d": [BEARER]}}]}}
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                check_no_durable_secret(deep, what="a journalled result")

    def test_a_named_member_nested_deep_is_refused_too(self):
        deep = {"a": [{"b": {"authorization": "x"}}]}
        with self.assertRaises(ContractRefusal):
            check_no_durable_secret(deep, what="a journalled result")

    def test_a_bearer_used_as_a_KEY_is_refused(self):
        """Canonical JSON stores a key as durably as a value."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                check_no_durable_secret({BEARER: "harmless"},
                                        what="a durable row")

    def test_values_that_carry_no_text_are_not_walked_into(self):
        check_no_durable_secret({"n": 1, "f": 1.5, "b": True, "z": None,
                                 "list": [1, None], "tuple": (1, 2)},
                                what="a durable row")

    def test_a_value_with_behaviour_is_not_interrogated(self):
        """A rule whose whole job is to decide without running anything does
        not read the members of a value that carries its own class. That is
        the accepting owner's job, and it already refused it."""

        class Hostile:
            def __getattr__(self, name):
                raise AssertionError("the walk read a member with behaviour")

            def __iter__(self):
                raise AssertionError("the walk iterated a value with behaviour")

        with held_secret(BEARER):
            check_no_durable_secret({"opaque": Hostile()}, what="a durable row")


# -- the surfaces ------------------------------------------------------------

class TheJournalIsADurableSurface(SecretCase):

    def journalling(self, **operands):
        def run():
            self.store.transact(
                "op-leak", "probe.kind",
                manager_signature("probe.kind", operands),
                lambda connection: dict(operands))
        return run

    def test_a_bearer_in_an_operations_signature_is_refused(self):
        """Secrets never reach protocol identity: the signature is the full
        effective signature of an operation's operands."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                self.journalling(note=BEARER)()
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_bearer_in_a_journalled_result_is_refused(self):
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                self.store.transact(
                    "op-result", "probe.kind",
                    manager_signature("probe.kind", {}),
                    lambda connection: {"echo": BEARER})
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_bearer_in_a_durable_refusal_is_refused(self):
        """A DURABLE refusal is sealed into the journal, so its message is a
        durable surface. This is where §13 meets bounded diagnostics."""
        def leaking(connection):
            raise ContractRefusal("policy", "retention",
                                  f"held because of {BEARER}", durable=True)

        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                self.store.transact("op-refusal", "probe.kind",
                                    manager_signature("probe.kind", {}),
                                    leaking)
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_nothing_of_the_refused_act_survives(self):
        """The guard runs inside the write, so a leak takes the act's writes
        with it rather than leaving the row uncommitted and the effect done."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                self.journalling(note=BEARER)()
        self.assertIsNone(self.store.operation_record("op-leak"))

    def test_an_ordinary_operation_is_untouched(self):
        self.journalling(note="ordinary")()
        self.assertIsNotNone(self.store.operation_record("op-leak"))


class ProtocolIdentityAndPortableRefusalsArePublicSurfaces(SecretCase):

    def test_a_malformed_public_document_cannot_quote_the_live_bearer_it_is_made_of(
            self):
        """An ownership/type diagnostic is itself a public surface.

        `check_no_durable_secret` only traverses exact built-ins, so it is safe
        on a raw caller operand. Waiting until `boundaries.document` has
        accepted a dict lets that boundary quote an exact string bearer while
        refusing the malformed top-level shape. Both public doors below put
        their §13 walk after that same boundary.
        """
        doors = {
            "certify_agent_session_profile":
                lambda: worker_manager.certify_agent_session_profile(
                    self.store, BEARER),
            "record_inquiry_answer":
                lambda: worker_manager.record_inquiry_answer(
                    self.store, operation_id="inquiry-malformed",
                    answer=BEARER),
        }
        with held_secret(BEARER):
            for name, door in doors.items():
                with self.subTest(door=name):
                    with self.assertRaises(ContractRefusal) as caught:
                        door()
                    self.assertEqual(
                        (caught.exception.code,
                         BEARER in caught.exception.message),
                        ("secret-leak", False))

    def test_a_live_bearer_never_becomes_a_manager_signature(self):
        """The journal guard is too late for protocol identity: the exported
        signature builder must not first serialize the bearer and hand that
        representation to its caller."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                manager_signature("probe.kind", {"note": BEARER})
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_portable_refusal_cannot_carry_an_interpolated_bearer(self):
        """Sealing is the point a diagnostic becomes a portable document.
        Rejecting it only when a later journal write happens leaves the
        exported sealing surface itself able to return the leak."""
        refusal = ContractRefusal(
            "policy", "retention", f"held because of {BEARER}", durable=True)
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                seal_refusal(refusal)
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_reviving_untrusted_text_cannot_construct_a_bearer_diagnostic(
            self):
        """The public revival door accepts caller text, not necessarily bytes
        previously walked by this process. Its output is the same portable
        diagnostic surface in the other direction."""
        sealed = json.dumps({
            "category": "policy", "code": "retention",
            "message": f"held because of {BEARER}", "durable": True})
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                worker_manager.revive_refusal(sealed)
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_profile_is_rewalked_before_the_read_surface_returns_it(self):
        """A guard on the write path cannot see a later hand edit. The public
        read already revalidates shape and digest for that reason; §13 must be
        part of the same read-side trust boundary."""
        profile = _profile_carrying(BEARER)
        self.store._connection.execute(
            "INSERT INTO profiles (kind, name, digest, body, certified_at, "
            "withdrawn_at) VALUES ('agent-session', ?, ?, ?, ?, NULL)",
            (profile["profile_id"], profile["document_digest"],
             json.dumps(profile), NOW))
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                worker_manager.certified_agent_session_profile(
                    self.store, profile["document_digest"])
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_hand_edited_journal_row_cannot_leave_either_public_read(self):
        """The journal is the same receiving trust domain as profiles.

        `_record` walking bytes on the way in cannot establish §13 for bytes
        read after a later store edit. Both public doors share
        `_operation_row`, so the receiving boundary must re-walk the adopted
        row before either the row projection or replay can return it.
        """
        signature = manager_signature("probe.kind", {})
        self.store.transact(
            "op-hand-edited", "probe.kind", signature,
            lambda connection: {"body": "ordinary"})
        self.store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps({"body": f"the token is {BEARER}"}),
             "op-hand-edited"))

        reads = {
            "operation_record":
                lambda: self.store.operation_record("op-hand-edited"),
            "replay":
                lambda: self.store.replay(
                    "op-hand-edited", signature, kind="probe.kind"),
        }
        with held_secret(BEARER):
            for name, read in reads.items():
                with self.subTest(surface=name):
                    with self.assertRaises(ContractRefusal) as caught:
                        read()
                    self.assertEqual(caught.exception.code, "secret-leak")


class EveryAdoptedRowIsWalkedOnTheWayOut(SecretCase):
    """Third review [P1], generalized as its required correction 2 asks.

    The fix is not in each public reader, because "each reader" is a list
    somebody maintains. Every adopted row in this manager comes through
    `boundaries.row`, so the walk is there and a projection added tomorrow is
    covered tomorrow. These cases prove the rule is REACHED from the public
    doors rather than merely written.
    """

    def edited(self, statement, *operands):
        self.store._connection.execute(statement, operands)

    def test_a_hand_edited_offer_cannot_leave_the_claimed_offers_read(self):
        """`offers` is a persisted-row projection like the journal, and its
        columns are free text a later edit can fill."""
        issue_offer(self.store, self.port, offer_id="offer-13",
                    work_id=WORK, runtime_attempt_id="attempt-1",
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-ordinary")
        accept_offer(self.store, self.port, offer_id="offer-13",
                     decision="accept", bearer="bearer-ordinary", now=NOW,
                     runtime_attempt_id="attempt-1",
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        worker_manager.submit_claim(self.store, self.port,
                                    offer_id="offer-13")
        self.edited("UPDATE offers SET input_digest = ? WHERE offer_id = ?",
                    f"sha256:{BEARER}", "offer-13")
        self.assertTrue(
            worker_manager.claimed_offers_for(self.store, "attempt-1"),
            "the fixture reached no claimed offer, so nothing was adopted")
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                worker_manager.claimed_offers_for(self.store, "attempt-1")
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_the_secret_walk_precedes_column_diagnostics_that_quote_values(
            self):
        """The guard must be the first content rule at the row crossing.

        An invalid instant is otherwise refused by the column owner first,
        whose bounded diagnostic identifies the offending value. If that
        value is the live bearer, the refusal itself becomes the public leak
        §13 exists to prevent.
        """
        signature = manager_signature("probe.kind", {})
        self.store.transact(
            "op-invalid-secret", "probe.kind", signature,
            lambda connection: {"body": "ordinary"})
        self.edited(
            "UPDATE operations SET settled_at = ? WHERE operation_id = ?",
            BEARER, "op-invalid-secret")
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                self.store.operation_record("op-invalid-secret")
        self.assertNotIn(BEARER, caught.exception.message)
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_forgotten_value_stays_readable_and_replayable(self):
        """Required correction 3, and the reason the rule is DYNAMIC.

        A secret this process is no longer holding is absent from the live
        registry, so its row is still readable — which is what keeps an exact
        durable replay of an old operation from failing on the retry merely
        because it once quoted something sensitive."""
        signature = manager_signature("probe.kind", {})
        self.store.transact(
            "op-forgotten", "probe.kind", signature,
            lambda connection: {"body": "ordinary"})
        self.edited("UPDATE operations SET result = ? WHERE operation_id = ?",
                    json.dumps({"body": f"the token was {BEARER}"}),
                    "op-forgotten")
        self.assertFalse(live_secret(BEARER),
                         "the fixture is not testing what it says")
        found, value = self.store.replay("op-forgotten", signature,
                                         kind="probe.kind")
        self.assertTrue(found)
        self.assertEqual(value, {"body": f"the token was {BEARER}"})
        self.assertIsNotNone(self.store.operation_record("op-forgotten"))

    def test_the_bearer_the_issue_path_returns_is_not_a_persisted_column(self):
        """Why the central walk cannot collide with the one deliberate
        disclosure. `issue_offer` answers with the bearer to the caller
        entitled to it and holds it LIVE across that act — and the offer row
        stores a VERIFIER and never the bearer, so no adopted row can be
        carrying it while it is held."""
        self.assertNotIn("bearer", schema.OFFER_COLUMNS)
        answer = issue_offer(
            self.store, self.port, offer_id="offer-14", work_id=WORK,
            runtime_attempt_id="attempt-1",
            input_digest="sha256:" + "1" * 64,
            policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE,
            profile_name="reference", mint_bearer=lambda: BEARER)
        self.assertEqual(answer["bearer"], BEARER)
        row = self.store._connection.execute(
            "SELECT * FROM offers WHERE offer_id = 'offer-14'").fetchone()
        self.assertNotIn(BEARER, json.dumps(
            {key: row[key] for key in row.keys()}))

    def test_no_public_door_quotes_a_live_bearer_before_it_walks(self):
        """Fourth review [P1], generalized to every door that QUOTES.

        The finding was about `boundaries.row`, and the shape is not specific
        to it: a validator that names the value it rejects will interpolate a
        secret into a public diagnostic if it runs before the walk. Each door
        below is given a spoiled operand carrying the live bearer, and each
        must answer `secret-leak` with a message that does not contain it.
        """
        signature = manager_signature("probe.kind", {})
        self.store.transact("op-order", "probe.kind", signature,
                            lambda connection: {"body": "ordinary"})
        self.edited("UPDATE operations SET settled_at = ? "
                    "WHERE operation_id = ?", BEARER, "op-order")
        profile = _profile_carrying(BEARER)
        self.edited(
            "INSERT INTO profiles (kind, name, digest, body, certified_at, "
            "withdrawn_at) VALUES ('agent-session', ?, ?, ?, ?, NULL)",
            profile["profile_id"], profile["document_digest"],
            json.dumps(dict(profile, session_capabilities="not a list")), NOW)
        doors = {
            "operation_record":
                lambda: self.store.operation_record("op-order"),
            "certified_agent_session_profile":
                lambda: worker_manager.certified_agent_session_profile(
                    self.store, profile["document_digest"]),
            "revive_refusal":
                lambda: worker_manager.revive_refusal(json.dumps({
                    "category": "not-a-category", "code": "retention",
                    "message": f"held because of {BEARER}", "durable": True})),
            "certify_agent_session_profile":
                lambda: worker_manager.certify_agent_session_profile(
                    self.store,
                    dict(_profile_carrying(BEARER),
                         session_capabilities="not a list")),
        }
        with held_secret(BEARER):
            for name, door in doors.items():
                with self.subTest(door=name):
                    with self.assertRaises(ContractRefusal) as caught:
                        door()
                    self.assertEqual(caught.exception.code, "secret-leak",
                                     caught.exception.message)
                    self.assertNotIn(BEARER, caught.exception.message)

    def test_the_shape_still_decides_when_nothing_is_held(self):
        """The ordering refuses a LEAK earlier; it does not swallow the
        structural fault. With no secret live, each door still answers with
        the schema refusal it always did."""
        profile = dict(_profile_carrying("ordinary"),
                       session_capabilities="not a list")
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.certify_agent_session_profile(self.store, profile)
        self.assertNotEqual(caught.exception.code, "secret-leak")
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.revive_refusal(json.dumps({
                "category": "not-a-category", "code": "retention",
                "message": "ordinary", "durable": True}))
        self.assertNotEqual(caught.exception.code, "secret-leak")

    def test_the_walk_is_reached_by_the_row_boundary_and_not_by_a_reader(self):
        """The anti-circularity half: the guard is at the ONE crossing, so a
        reader that never learned about §13 is covered anyway. Driven through
        a projection whose own module names no secret rule at all."""
        source = pathlib.Path(
            worker_manager.__file__).resolve().parent / "offers.py"
        body = source.read_text(encoding="utf-8")
        self.assertNotIn("check_no_durable_secret(", body.split(
            "def claimed_offers_for")[-1],
            "claimed_offers_for grew its own walk; this case is about the "
            "one at the row boundary covering readers that have none")


class ARecordedAnswerIsWalkedAtItsOwnBoundary(InterrogationCase):
    """Re-review [P1]'s re-audit, as a case rather than a corrected comment.

    `record_inquiry_answer` is a durable writer that does NOT go through
    `transact`, so the journal walk its sweep entry credited never ran on it —
    and the entry said it did. A reason is evidence only when it describes the
    path that actually runs, which is the finding this class holds.
    """

    def setUp(self):
        super().setUp()
        self.addCleanup(self.assertFalse, live_secret(BEARER))

    def asked(self, operation_id):
        worker_manager.inquire(
            self.store, self.port, Agent(), attempt_id=ATTEMPT,
            posture="execution", session_epoch=1,
            operation_id=operation_id, deadline_seconds=30,
            question="how is it going?")
        return operation_id

    def recorded(self, operation_id):
        return self.store._connection.execute(
            "SELECT answer, outcome FROM interrogations "
            "WHERE operation_id = ?", (operation_id,)).fetchone()

    def test_an_answer_carrying_a_live_bearer_never_reaches_the_row(self):
        self.asked("inquire-13")
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                worker_manager.record_inquiry_answer(
                    self.store, operation_id="inquire-13",
                    answer={"body": f"the token is {BEARER}"})
        self.assertEqual(caught.exception.code, "secret-leak")
        found = self.recorded("inquire-13")
        self.assertIsNone(found["answer"],
                          "the refused answer still reached the column")
        self.assertNotEqual(found["outcome"], "answered")

    def test_a_member_named_for_a_secret_is_refused_by_its_name(self):
        """The walk's other half, on this surface: `diagnostics` is free
        caller structure, so a member NAMED for a secret is refused whether or
        not this process is holding one."""
        self.asked("inquire-14")
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.record_inquiry_answer(
                self.store, operation_id="inquire-14",
                answer={"body": "done",
                        "diagnostics": {"claim_token": "anything"}})
        self.assertEqual(caught.exception.code, "secret-leak")
        self.assertIsNone(self.recorded("inquire-14")["answer"])

    def test_an_ordinary_answer_is_recorded_unchanged(self):
        """The guard refuses a leak and nothing else."""
        self.asked("inquire-15")
        worker_manager.record_inquiry_answer(
            self.store, operation_id="inquire-15",
            answer={"body": "halfway through the second gate"})
        found = self.recorded("inquire-15")
        self.assertEqual(json.loads(found["answer"]),
                         {"body": "halfway through the second gate"})
        self.assertEqual(found["outcome"], "answered")


class TheManifestCompositeIsTheTrustEntry(SecretCase):

    def test_the_named_half_is_unreachable_through_a_manifest_and_why(self):
        """MEASURED, not assumed. Inside a frozen manifest there is nowhere a
        member named for a secret can legally sit: every object is
        `additionalProperties: false` except `extensions`, whose
        `propertyNames` pattern requires a reverse-DNS namespace with an
        explicit version — so `authorization` is refused by the SCHEMA before
        §13 is reached.

        That makes the value half the one §13 actually adds here, and the name
        half is proved directly against the walk instead. This case pins the
        reliance: if the schema ever stops carrying it, the gate says so
        rather than leaving a half of §13 quietly unenforced at this
        surface.
        """
        vector = _published_input()
        spoiled = _resealed(dict(vector, extensions={"authorization": "x"}))
        with self.assertRaises(ContractRefusal) as caught:
            check_manifest_structure(spoiled, "inputManifest",
                                     what="an input manifest")
        self.assertEqual(caught.exception.code, "schema")
        # And a namespaced extension whose VALUE carries the bearer is the
        # half that does reach §13 here.
        carrying = _resealed(dict(vector,
                                  extensions={"baton.test/1": BEARER}))
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                check_manifest_structure(carrying, "inputManifest",
                                         what="an input manifest")
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_a_manifest_carrying_a_live_bearer_is_refused(self):
        vector = _published_input()
        spoiled = _resealed(dict(vector, manifest_id=f"id-{BEARER}"))
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                check_manifest_structure(spoiled, "inputManifest",
                                         what="an input manifest")
            self.assertEqual(caught.exception.code, "secret-leak")

    def test_the_published_vector_still_passes(self):
        owned = check_manifest_structure(_published_input(), "inputManifest",
                                         what="an input manifest")
        self.assertEqual(owned["schema"], "baton.worker-manifest/input")


class TheBearerIsHeldForTheActsThatSpendIt(SecretCase):

    def issued(self, offer_id="offer-1"):
        return issue_offer(
            self.store, self.port, offer_id=offer_id, work_id=WORK,
            runtime_attempt_id="attempt-1",
            input_digest="sha256:" + "1" * 64,
            policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE,
            profile_name="reference", mint_bearer=lambda: BEARER)

    def test_issuing_answers_with_the_bearer_and_stores_the_verifier(self):
        """The bearer rides back with the RESULT deliberately: holding it
        across that return would make the manager refuse to answer with the
        one value the caller is entitled to."""
        record = self.issued()
        self.assertEqual(record["bearer"], BEARER)
        self.assertEqual(record["verifier"], digest(BEARER))
        self.assertNotIn(BEARER, _dump(self.path))

    def test_the_bearer_is_live_while_the_issue_act_journals(self):
        """Proved from inside the act: a mint that also tries to journal the
        bearer is refused, which it could not be if the value were not
        registered for exactly this scope."""
        seen = []

        def minting():
            seen.append(live_secret(BEARER))
            return BEARER

        self.assertFalse(live_secret(BEARER))
        issue_offer(self.store, self.port, offer_id="offer-2", work_id=WORK,
                    runtime_attempt_id="attempt-1",
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=minting)
        self.assertEqual(seen, [False], "the mint ran inside the hold")
        self.assertFalse(live_secret(BEARER),
                         "the bearer stayed live past its act")

    def test_accepting_holds_the_bearer_and_leaves_nothing_behind(self):
        self.issued()
        accept_offer(self.store, self.port, offer_id="offer-1",
                     decision="accept", bearer=BEARER, now=NOW,
                     runtime_attempt_id="attempt-1",
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        self.assertFalse(live_secret(BEARER))
        self.assertNotIn(BEARER, _dump(self.path))

    def test_a_decline_that_carries_the_bearer_is_refused_before_it_settles(self):
        """`reason` is caller prose that reaches a durable column and rides the
        settlement's signature, and the containment case that scope existed for
        was a decline explaining itself by QUOTING the bearer.

        W33937 refuses that decision one step earlier, as the bearer-carrying
        decline it is (`integrity/schema`), so the settlement it would have
        journalled never happens. THE SECRET NEVER BECOMES LIVE ON THIS PATH,
        and that is the correction rather than a gap in it: a decline hands
        this manager no bearer, so there is nothing to register for a walk to
        hold the settlement against.
        """
        self.issued()
        with self.assertRaises(ContractRefusal) as caught:
            accept_offer(self.store, self.port, offer_id="offer-1",
                         decision="decline", bearer=BEARER, now=NOW,
                         runtime_attempt_id="attempt-1",
                         work_ref={"authority_uuid": UUID, "work_id": WORK},
                         reason=f"the worker rejected {BEARER}")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertFalse(live_secret(BEARER))
        # THE REFUSAL IS A PUBLIC SURFACE and the store is a durable one. The
        # decline carried the secret twice over -- as the operand and inside
        # the prose -- and neither copy reaches either.
        self.assertNotIn(BEARER, str(caught.exception))
        self.assertNotIn(BEARER, _dump(self.path))

    def test_declining_holds_no_bearer_and_leaves_nothing_behind(self):
        """The positive half: a bearer-free decline settles the offer and
        consumes its verifier without the secret being handed over at all."""
        self.issued()
        settled = accept_offer(self.store, self.port, offer_id="offer-1",
                               decision="decline", now=NOW,
                               runtime_attempt_id="attempt-1",
                               work_ref={"authority_uuid": UUID,
                                         "work_id": WORK},
                               reason="the worker is busy")
        self.assertEqual(settled["state"], "declined")
        self.assertFalse(live_secret(BEARER))
        self.assertNotIn(BEARER, _dump(self.path))

    def test_a_bearer_that_is_not_text_still_refuses_as_a_capability(self):
        """Registering it would answer a different question: a value that
        cannot be a live secret is refused by the possession check as the
        capability failure it is."""
        self.issued()
        with self.assertRaises(ContractRefusal) as caught:
            accept_offer(self.store, self.port, offer_id="offer-1",
                         decision="accept", bearer=None, now=NOW,
                         runtime_attempt_id="attempt-1",
                         work_ref={"authority_uuid": UUID, "work_id": WORK})
        self.assertEqual(caught.exception.code, "capability")


# -- the sweep: enumerated, not probed ---------------------------------------

# Durable writers whose §13 coverage comes from somewhere other than the
# journal, each naming it. An entry here is a decision somebody made, and it is
# checked to name a writer that exists.
COVERED_ELSEWHERE = {
    # W32649: the runtime lane. Every column it writes is either derived from
    # the assignment's own authority-owned identity -- the four lane parts and
    # the digest over them -- or composed by this manager from the operation it
    # is journalling. No caller operand reaches any of them, and the occupancy
    # happens inside the start transaction whose signature is walked.
    ("lanes.py", "_occupy_lane", "runtime_lanes"):
        "the four identity parts come off the activated attempt row, which was "
        "written from the authority's closed claim result; the reason is this "
        "manager's own sentence about the operation it is committing",
    # W33936 review [P1]: the deployment's configured workspace group. The
    # only value written is an integer this manager has already proved is a
    # group id it holds, and it rides the act's manager signature into the
    # journal, which is walked.
    ("workspaces.py", "configure_workspace_group", "meta"):
        "a validated group id, written by a deployment act whose signature "
        "the journal walks",
    # W36540 round eight added `configure_workspace_storage` in the shape of
    # the group's act directly above and did not carry this registration with
    # it, so a durable writer this Work introduced has sat uncovered ever
    # since -- the same omission as the boundary label round nine corrected,
    # and the same lesson: a mirrored pattern does not bring its obligations
    # along. The rationale is the group's own, one operand over: the only
    # value written is a path `check_workspace_storage` has already proved
    # absolute and containable, and it rides
    # `manager_signature("workspace-storage.configure", {"place": place})`
    # into the journal the sweep walks.
    ("workspaces.py", "configure_workspace_storage", "meta"):
        "a validated absolute store root, written by a deployment act whose "
        "signature the journal walks",
    ("store.py", "ControlStore._initialize", "meta"):
        "this build's own schema marker and version, written once at creation "
        "from constants -- no caller operand reaches it",
    ("manifests.py", "_retain_canonical", "manifests"):
        "the bytes are a document `check_manifest_structure` has already "
        "walked; retaining them is storing what §13 accepted",
    ("offers.py", "_settle_terminal", "offers"):
        "every column it writes rides the settlement's manager signature into "
        "the journal, which is walked",
    ("offers.py", "_record_claim", "offers"):
        "the same",
    ("offers.py", "certify_profile", "meta"):
        "the same: certification is journalled and its signature carries the "
        "kind, the name and the digest -- and it writes `meta`, not "
        "`profiles`, because a runtime certification is a digest under a "
        "composed key rather than a filed body",
    ("offers.py", "issue_offer", "offers"):
        "written inside the issue act, whose journal row is walked with the "
        "bearer live",
    ("offers.py", "accept_offer", "offers"):
        "the same, for the acceptance act",
    # W61599: the liveness projection. Two values are written and neither is
    # anything a caller composed: the count is a whole number this manager
    # proved, and the instant is `store._now()` -- the same clock the journal
    # stamps its own rows from. No worker byte, no provider text and no path
    # reaches either column, which is the whole reason the projection is a
    # length rather than a sample of what was read.
    ("attempts.py", "observe_activity", "attempts"):
        "a proved non-negative count and this manager's own instant; no "
        "caller text and no observed content reaches either column",
    ("attempts.py", "record_attempt", "attempts"):
        "written inside the journalled record act",
    ("attempts.py", "activate_assignment", "attempts"):
        "written inside the journalled activation act",
    ("attempts.py", "_decide", "attempts"):
        "an observation's axis and value are closed vocabularies and its "
        "source identity rides the observation digest; no free text reaches "
        "this row",
    ("attempts.py", "_decide", "observations"):
        "the same",
    ("attempts.py", "_attach", "attempts"):
        "written inside the journalled reconciliation act",
    ("handshake.py", "certify_agent_session_profile", "profiles"):
        "the body is an agent-session document this build validated and then "
        "walked; see the case below that drives it",
    ("sessions.py", "_open", "agent_sessions"):
        "written inside the journalled opening act",
    ("sessions.py", "adopt_provider_session", "agent_sessions"):
        "a provider session id is an owned identity and the row carries no "
        "free text",
    ("sessions.py", "_observe_session_state_in", "agent_sessions"):
        "a closed vocabulary of nine states",
    ("posture_slots.py", "_occupy_slot", "posture_slots"):
        "closed vocabularies and an owned epoch; the reason column is NULL "
        "on this path",
    ("posture_slots.py", "_release_slot_in", "posture_slots"):
        "the reason rides the act that established the evidence",
    ("posture_slots.py", "_require_slot_recovery_in", "posture_slots"):
        "the same",
    ("output.py", "_record", "outputs"):
        "written inside the journalled record act, from a result document "
        "`check_manifest_structure` has walked",
    ("output.py", "_record", "output_artifacts"):
        "the same",
    ("interrogation.py", "_ask", "interrogations"):
        "written inside the journalled request act, whose signature carries "
        "the question and every binding and is walked at construction",
    # RENAMED under W6627's third review correction: the public door owns its
    # caller's observation and `_settle` performs the move over a reading
    # somebody has already owned, so the durable writer is the private half.
    # ALIGNED WITH THE PATH THAT PERFORMS THE WALK, which W6627's fourth
    # review required: the previous reason credited OWNERSHIP for the free
    # adapter document, and ownership is not `check_no_durable_secret`. A
    # diagnostic named `claim_token` was owned, accepted and persisted.
    ("interrogation.py", "_settle", "interrogations"):
        "a closed outcome vocabulary, an instant, and an observation walked "
        "by `_observation` — the one owner both the fresh adapter path and "
        "the exported settlement reach — before either can persist it",
    # NOT COVERED ELSEWHERE, and the correction is the point. This entry used
    # to say the answer rode the same journalled signature `_ask` walked. It
    # does not: an answer arrives at its own boundary long after the request,
    # and `record_inquiry_answer` writes through a direct UPDATE rather than
    # `transact`. Re-review [P1] asked for exactly this re-audit — a reason is
    # evidence only when it describes the path that actually runs — and the
    # writer is guarded at its own boundary now.
    ("interrogation.py", "record_inquiry_answer", "interrogations"):
        "GUARDED IN PLACE: `record_inquiry_answer` walks the answer before it "
        "opens the transaction, because this act does not go through the "
        "journal the older reason credited",
    ("interrogation.py", "publish_inquiry_answer", "interrogations"):
        "one instant, written after the answer it publishes",
    # W6629's three. Both writers are PRIVATE and each has exactly one door:
    # `record_intake` reaches `_seal` and `decide_retention` reaches `_retain`,
    # and both go through `store.transact`. The journal row is written inside
    # that transaction and before the COMMIT, and it carries the full
    # effective signature AND the byte-stable result -- so a bearer in either
    # is refused with the action's own writes still inside the transaction
    # that takes them back. The reason names the path that actually runs,
    # which is what the two interrogation entries above were corrected for.
    ("intake.py", "_seal", "intakes"):
        "written inside the journalled `intake.record` act, whose signature "
        "carries the adapter's whole collection and whose result is the "
        "receipt this row records -- including the composed `why`, which is "
        "the one column here built rather than adopted",
    ("intake.py", "_seal", "intake_artifacts"):
        "the same act and the same walked result: every custody locator this "
        "row holds is a member of that receipt",
    ("intake.py", "_retain", "retentions"):
        "written inside the journalled `output.retain` act, whose signature "
        "carries the artifact ids, the disposition and the policy digest -- "
        "and those operands went through `retain_operation`'s own walk before "
        "the transaction was ever opened",
}


# THE PUBLIC HALF, in two classes with one rule each. Every exported callable
# is in exactly one of them, and the universe is `__all__` rather than either
# table — an inventory that starts from the guards the code already performs
# cannot discover a missing one.
#
# CONSTRUCTS_A_PORTABLE_ARTEFACT: the operation RETURNS text or a document
# built from caller operands, so §13 has to run before it answers. Each is
# probed below.
CONSTRUCTS_A_PORTABLE_ARTEFACT = {
    "manager_signature":
        "returns protocol identity — the canonical text an operation's "
        "operands are compared as",
    "seal_refusal":
        "returns the portable refusal document; sealing is the point a "
        "diagnostic becomes one",
    "retain_manifest":
        "walks the document through the manifest composite before filing it",
    "certify_agent_session_profile":
        "walks the profile before its bytes are filed",
    "load_manifest":
        "re-walks what it hands back: a store nobody validates on the way out "
        "is a store where a hand edit outlives every guard on the way in",
    # -- MOVED HERE by re-review [P1]. Both were classified prose-only on
    # reasons that described a NARROWER internal caller than the public path
    # that actually runs.
    "revive_refusal":
        "a public receiving door for arbitrary sealed text: the walk that "
        "made the old reason true is the JOURNAL's, on the replay path, whose "
        "input this build wrote — this one's input is whatever a caller holds",
    "certified_agent_session_profile":
        "the read-side trust boundary. It exists because a write-side guard "
        "cannot see a later store edit, and §13 was the one rule left out of "
        "that argument",
    # -- W6629: intake, retention and cleanup --------------------------------
    #
    # THE FOUR DERIVED IDENTITIES. Each is handed the caller's ATTEMPT MAPPING
    # and answers with an operation id and a signature digest composed from
    # it, so `manager_signature`'s own reason applies here unchanged: an
    # operation identity is portable, and a guard at the eventual write runs
    # after the caller already holds it. MEASURED RATHER THAN REASONED -- until
    # these walked their operands, a live bearer in an attempt row's own id
    # came straight back out inside the returned operation id.
    "collect_operation":
        "returns the `output.collect` identity, derived from the attempt it "
        "is handed",
    "intake_operation": "the same, for `intake.record`",
    "retain_operation":
        "the same, for `output.retain` -- and the retention policy digest is "
        "free caller text that rides the identity rather than only the "
        "signature",
    "destroy_operation":
        "the same, for `runtime.destroy`, over both of the digests "
        "`runtimeDestroyBody` fixes",
    # THE TWO READ-SIDE DOORS, for `certified_agent_session_profile`'s reason
    # rather than a new one: a write-side guard cannot see a later store edit.
    # One of these hands back the digest a destroy is AUTHORIZED by, which is
    # the strongest form that argument takes anywhere in this package.
    "intake_receipt_of":
        "hands back a custody receipt and the digest that authorizes a "
        "destroy, assembled out of rows this process did not write",
    "retentions_of":
        "hands back the retention decisions, and a decision is written under "
        "its own operation and can be edited in the store without the intake "
        "row changing at all",
}

# RETURNS_NOTHING_A_CALLER_DID_NOT_ALREADY_HAVE: the operation answers with this
# build's own closed documents over values it owned, with no free caller text
# composed into a durable or portable artefact — or it deliberately returns the
# secret to the one party entitled to it.
RETURNS_NO_CONSTRUCTED_ARTEFACT = {
    # W32649. Both answer with values read from the attempt row and the lane
    # table -- an assignment identity, a holder's attempt id and this manager's
    # own reason -- and construct nothing a caller supplied any part of.
    # W32648. `authorize_failed_start_cleanup` answers the same
    # `cleanup.settled` document the receipt-authorized ending does, composed
    # from an observation the adapter made and this manager's own axis values;
    # `failed_start_destroy_operation` derives an identity and a signature
    # digest, and its own `check_no_durable_secret` runs at the constructor for
    # the reason every other operation identity's does.
    "authorize_failed_start_cleanup":
        "answers the frozen cleanup ending, from an adapter observation and "
        "this manager's own axis values",
    "failed_start_destroy_operation":
        "derives an operation identity and walks it for §13 at the "
        "constructor, exactly as `destroy_operation` does",
    # W44716. The fourth ending, and the same statement as the other three:
    # what comes back is composed from an adapter observation, this manager's
    # own axis values and the authority's own closed fence answer. The
    # operator's `reason` is durable text this manager was handed and stores;
    # it is walked for §13 at `manager_signature` when the declaration is
    # committed, exactly as every other operand-bearing signature is.
    "abandon_attempt":
        "answers the frozen cleanup ending beside the authority's own fence "
        "answer and this manager's committed declaration, from an adapter "
        "observation and this manager's own axis values",
    # W32576. The same three statements, one ending further along.
    "authorize_refused_session_cleanup":
        "answers the frozen cleanup ending, from an adapter observation and "
        "this manager's own axis values",
    "refused_session_destroy_operation":
        "derives an operation identity and walks it for §13 at the "
        "constructor, exactly as `destroy_operation` does",
    "unsupported_version_operation_id":
        "derives one identity from the four-part session reference and "
        "answers that text",
    "settle_unsupported_version":
        "answers the manager's own refusal record, composed from the "
        "persisted session's certified profile and a refusal this manager "
        "derived rather than one it was handed",
    "configure_workspace_group":
        "records one validated group id; the answer is that integer",
    "configured_workspace_group":
        "answers the recorded group as a capability holding one integer",
    "WorkspaceGroup": "an immutable capability over one validated group id",
    "lane_reference": "projects four authority-owned identity parts off the "
                      "attempt row; there is no operand to construct from",
    "runtime_lane": "the same, plus who holds the lane and what blocks it",
    "attempt_activity_of": "projects the two liveness numbers off the attempt "
                           "row; there is no operand to construct from and no "
                           "observed content is reachable from either value",
    "observe_activity": "answers that same projection after writing a count "
                        "it proved and an instant it took from the store's "
                        "own clock; nothing the observed child produced is "
                        "carried, held or returned",
    "attempt_runtime_of": "projects four runtime axes off the attempt row "
                          "plus the assignment document activation fixed, so "
                          "a recovery can branch on durable manager state and "
                          "hold its editable grants against that identity in "
                          "ONE atomic read; the assignment is `documents."
                          "assignment` composed of owned row values and no "
                          "bearer is reachable from any of it",
    "label_context": "projects the two label members off the activated row; "
                     "there is no operand to construct from",
    "AuthorityPort": "a capability wrapper; it constructs no document",
    "ControlStore": "opens a store; it constructs no document",
    "issue_offer":
        "DELIBERATELY answers with the bearer, to the one caller entitled to "
        "it — holding it across that return would make this manager refuse to "
        "answer with the value it was asked for",
    "accept_offer": "closed documents over owned values; the durable half is "
                    "the journal, which is walked with the bearer live",
    "settle_claim": "the same",
    "submit_claim": "the same",
    "expire_overdue": "the same",
    "recover_on_restart": "the same",
    "certify_profile": "answers with the kind, name and digest it was given",
    # THE RE-AUDIT REQUIRED CORRECTION 2 ASKED FOR. Every reason below that
    # says "adopted rows" now means the rows are walked where they cross out
    # of the store, not merely that their columns hold their shapes. The walk
    # is in `boundaries.row` rather than in each reader, because "each reader"
    # is a list somebody maintains and a projection added tomorrow would be
    # outside it.
    "claimed_offers_for":
        "adopted rows, each column owned by its contract and the whole row "
        "walked at the receiving boundary",
    "claim_operation_id": "a derivation over already-owned values",
    "record_attempt": "closed documents over owned values",
    "activate_assignment": "the same",
    "observe": "a closed axis vocabulary and its own answer",
    "request_runtime_start": "the same",
    "reconcile_runtime": "the same",
    "request_cancellation": "the same; the adapter settlements ride back "
                            "uninterpreted and reach no durable surface here",
    # W61984. The already-quiescent finalization answers this manager's own
    # committed decision -- every member of it derived from the attempt row --
    # beside the authority's own closed fence answer. The operator's `reason`
    # is durable text this manager was handed and stores; it is walked for §13
    # at `manager_signature` when the decision is committed, exactly as every
    # other operand-bearing signature is. Nothing the worker produced is read,
    # carried or returned, because this operation makes no engine call at all.
    "finalize_quiescent_assignment":
        "answers this manager's committed finalization record beside the "
        "authority's own closed fence answer, over values derived from the "
        "attempt row",
    "open_agent_session": "closed documents over owned values",
    "adopt_provider_session": "the same",
    "observe_session_state": "the same",
    "close_agent_session": "the same",
    "handle_transport_loss": "the same",
    "reconcile_agent_session": "the same",
    "agent_sessions_of": "the same",
    "posture_slot": "the same",
    "release_slot": "closed documents over owned values",
    "require_slot_recovery": "the same",
    "request_freeze":
        "answers with a closed request document over the attempt's own owned "
        "identities and a closed disposition; the sealed material arrives at "
        "`record_frozen_result`, not here",
    # WALKED, but not probed HERE, and the difference is worth naming. Its
    # sealed operand goes through the manifest composite -- so §13 runs before
    # anything durable happens -- but the walk sits behind a precondition that
    # the named attempt exists, so a probe in this file would be refused for
    # the earlier reason and prove nothing. The composite is driven directly by
    # `TheManifestCompositeIsTheTrustEntry` below, and this operation's own
    # ordering is `test_output`'s to hold.
    "record_frozen_result":
        "its sealed operand goes through the manifest composite, which walks "
        "it before anything durable happens; the composite is probed directly "
        "and this operation's precondition ordering is test_output's",
    "frozen_output_of": "the same",
    "freeze_operation": "two digests derived from an owned row",
    # W6629's FOUR JOURNALLED DOORS. Each composes text it did not own -- the
    # adapter's collection, the caller's retention policy digest -- and each
    # walks it before it answers. The walk is probed DIRECTLY above rather
    # than here: `manager_signature` for the two intake doors, and
    # `retain_operation` and `destroy_operation` for the two policy ones. A
    # probe in this file would be refused for the missing attempt first and
    # would prove nothing, which is `record_frozen_result`'s situation
    # exactly -- so the bearer-live drives are `test_intake`'s, one per door,
    # against the fixture that can actually reach them.
    "request_intake":
        "its own construction is `collect_operation`, which is probed above, "
        "and what it returns is `record_intake`'s answer",
    "record_intake":
        "the adapter's whole collection rides `manager_signature`, which is "
        "probed above -- and it is signed before anything about today is "
        "consulted, so the walk cannot be got past by moving an axis",
    "decide_retention":
        "the policy digest it composes into its answer went through "
        "`retain_operation`'s walk before the journal was asked",
    "authorize_cleanup":
        "the same through `destroy_operation`, over the intake receipt digest "
        "as well as the policy one",

    "negotiate_acp": "the wire version and this build's own capability "
                     "constants",
    "check_client_capabilities": "answers about a document and constructs none",
    "permits_session_transition": "a boolean over two closed vocabularies",
    "satisfies_runtime_quiescence_gate": "a constant false",
    "reprompt_after_transport_loss": "always refuses; it returns nothing",
    "transport_reachability_reidentifies": "a constant false",
    # W6627's interrogation split. None of these composes free caller text
    # into a durable or portable artefact of its own: the request is
    # journalled through the operation signature, which the §13 constructor
    # guard already walks, and the answers are closed documents over owned
    # values.
    "probe": "closed documents over owned values; the durable half is the "
             "journalled request, whose signature is walked at construction",
    "inquire": "the same, and its question rides the same signature",
    "settle_interrogation": "one closed outcome vocabulary and its own answer",
    "record_inquiry_answer":
        "walks the answer at its own boundary — see the durable sweep above, "
        "where this writer's old reason was the second false one this "
        "re-review found — and answers with the row's own closed view",
    "publish_inquiry_answer": "publishes an answer §13 already walked; what it "
                              "returns is the row's own closed view",
    "interrogation_of": "the same, for one row",
    "interrogations_of": "the same",
    # -- THE PUBLIC METHODS OF THE EXPORTED CLASSES ------------------------
    #
    # Re-review [P1] required these to be enumerated rather than covered by
    # their class's one entry. Each reason describes THIS method's own public
    # path — the defect the same review found in two prose-only entries above
    # was a reason that described a narrower internal caller.
    #
    # The port FORWARDS. Every member hands its operands to the injected
    # session and answers with what came back, owned as the injected value it
    # is. Nothing here composes caller text into an artefact this manager
    # constructs and returns, which is what §13's public half is about; what
    # travels OUTBOUND to the authority is the authority's to own, and what a
    # caller may put in an operand is decided where that operand entered.
    "AuthorityPort.project_work": "forwards a Work id and answers with the "
                                  "session's own projection, owned as injected",
    "AuthorityPort.assignment_of": "the same, for one live assignment",
    "AuthorityPort.slot_holder": "the same, for one participant's holder",
    "AuthorityPort.claim": "the same, for the authority's claim answer",
    "AuthorityPort.cancel": "the same; the fence is a closed value and no "
                            "document is built here",
    "AuthorityPort.settle_operation":
        "answers with the session's own settlement, owned member by member "
        "against a closed variant set; nothing is composed",
    "AuthorityPort.publish_answer":
        "forwards an answer this manager already journalled and answers with "
        "the reference the session returned, owned as injected",
    "AuthorityPort.claim_signature":
        "the AUTHORITY's derivation, consumed rather than recomputed; this "
        "returns exactly what it was handed",
    # The store's own surface. `_record` is the durable writer and is swept by
    # `EveryDurableWriterIsGuarded`; these are the read and boundary halves.
    "ControlStore.open": "opens or initializes a database and answers with the "
                         "handle; it constructs no document",
    "ControlStore.close": "returns nothing at all",
    "ControlStore.transact":
        "answers with what the CALLER's action returned. The signature and the "
        "result are journalled through `_record`, which walks them with the "
        "bearer live before a byte is written",
    # THIRD REVIEW [P1]. Both reasons credited column adoption and `_record`'s
    # write-side walk, and neither establishes §13 for the bytes LEAVING the
    # read: a later store edit can put a live bearer into `operations.result`
    # after the writer's walk has run. Both doors share `_operation_row`, and
    # the row boundary itself walks now — see
    # `EveryAdoptedRowIsWalkedOnTheWayOut`.
    "ControlStore.replay":
        "returns the recorded JSON byte-stably from a row `boundaries.row` "
        "walks at the receiving boundary; a value this process is no longer "
        "holding is absent from the registry, so an old operation stays "
        "replayable",
    "ControlStore.operation_record":
        "a fresh document over an adopted journal row — every column owned by "
        "its contract AND the whole row walked where it crosses out of the "
        "store",
}


class EveryPublicSurfaceIsAccountedFor(SecretCase):
    """The public half of the sweep, derived from `__all__`.

    §13 names durable AND public surfaces. A guard that runs only at the SQL
    write is too late for an operation that RETURNS a constructed artefact:
    the caller has the leak before any row is written, which is the defect
    review [P1] found in the first version of this file.
    """

    def exported(self):
        """Every callable a holder of this package can reach through
        `__all__` — INCLUDING the public methods of an exported class.

        Re-review [P1]: counting a class as one surface meant
        `ControlStore.operation_record`, `replay` and `transact` could be
        added or changed without this gate noticing. Exporting the class is
        what makes its methods callable public surfaces; classifying only its
        constructor enumerates none of them."""
        found = set()
        for name in worker_manager.__all__:
            member = getattr(worker_manager, name)
            if isinstance(member, type):
                found.add(name)
                found.update(
                    f"{name}.{attribute}" for attribute in dir(member)
                    if not attribute.startswith("_")
                    and callable(getattr(member, attribute, None)))
            elif callable(member):
                found.add(name)
        return found

    def test_every_exported_callable_is_in_exactly_one_class(self):
        exported = self.exported()
        classed = (set(CONSTRUCTS_A_PORTABLE_ARTEFACT)
                   | set(RETURNS_NO_CONSTRUCTED_ARTEFACT))
        self.assertEqual(sorted(exported - classed), [],
                         "exported surfaces with no §13 accounting")
        self.assertEqual(sorted(classed - exported), [],
                         "accounted surfaces that are not exported")
        both = (set(CONSTRUCTS_A_PORTABLE_ARTEFACT)
                & set(RETURNS_NO_CONSTRUCTED_ARTEFACT))
        self.assertEqual(sorted(both), [], "classed twice")

    def test_the_universe_is_not_read_from_either_table(self):
        """The rule that makes a sweep worth having, restated for this half:
        a surface with no accounting must be discoverable."""
        self.assertGreater(len(self.exported()), 40)
        self.assertIn("manager_signature", self.exported())

    def test_an_exported_class_does_not_hide_its_public_methods(self):
        """`__all__` exports the class, but callers use its public methods.
        Treating the class as one surface means a new method cannot make this
        gate fail, which is the exact future-gap property the sweep exists to
        prevent."""
        self.assertTrue(callable(worker_manager.ControlStore.operation_record))
        self.assertIn("ControlStore.operation_record", self.exported())

    def test_the_method_universe_is_derived_and_not_listed(self):
        """The anti-circularity half, for the methods. The names come from
        `dir()` on the exported class, so a method added tomorrow is in the
        universe tomorrow — and both classes are asserted, so an enumeration
        that silently covered one of them fails."""
        exported = self.exported()
        for owner in ("AuthorityPort", "ControlStore"):
            found = getattr(worker_manager, owner)
            reached = {name for name in exported
                       if name.startswith(f"{owner}.")}
            self.assertEqual(
                reached,
                {f"{owner}.{attribute}" for attribute in dir(found)
                 if not attribute.startswith("_")
                 and callable(getattr(found, attribute, None))},
                f"{owner} hides public methods from the sweep")
            self.assertGreaterEqual(len(reached), 4, owner)

    def constructing_probes(self):
        """One drive per constructing surface, with the bearer LIVE."""
        vector = _published_input()
        carrying = _resealed(dict(vector, manifest_id=f"id-{BEARER}"))
        return {
            "manager_signature":
                lambda: manager_signature("probe.kind", {"note": BEARER}),
            "seal_refusal":
                lambda: worker_manager.seal_refusal(ContractRefusal(
                    "policy", "retention", f"held because of {BEARER}",
                    durable=True)),
            "retain_manifest":
                lambda: worker_manager.retain_manifest(
                    self.store, carrying, "inputManifest"),
            "certify_agent_session_profile":
                lambda: worker_manager.certify_agent_session_profile(
                    self.store, _profile_carrying(BEARER)),
            "load_manifest":
                lambda: worker_manager.load_manifest(
                    self.store, _file_carrying(self.path, carrying),
                    "inputManifest"),
            # Re-review [P1]'s two. Both are RECEIVING doors whose reasons
            # previously described a narrower internal caller, so both are
            # driven here through the real exported operation.
            "revive_refusal":
                lambda: worker_manager.revive_refusal(json.dumps({
                    "category": "policy", "code": "retention",
                    "message": f"held because of {BEARER}", "durable": True})),
            "certified_agent_session_profile":
                self.reading_back_a_hand_edited_profile,
            # W6629's four derived identities. Two carry the bearer in the
            # ATTEMPT's own id, which is the leak that was measured, and two
            # carry it in the free digest operand that rides the identity --
            # different vectors into the same construction, so a walk that
            # covered only the attempt would still fail this.
            "collect_operation":
                lambda: worker_manager.collect_operation(
                    _attempt_carrying(BEARER)),
            "intake_operation":
                lambda: worker_manager.intake_operation(
                    _attempt_carrying(BEARER)),
            "retain_operation":
                # W6629 review [P1]: the artifact set and disposition joined
                # this identity, because one policy deciding differently about
                # two artifacts produced one id and two signatures. The probe
                # drives the real four-operand surface.
                lambda: worker_manager.retain_operation(
                    _attempt_carrying(None), f"sha256:{BEARER}",
                    ["artifact-1"], "retain"),
            "destroy_operation":
                lambda: worker_manager.destroy_operation(
                    _attempt_carrying(None), f"sha256:{BEARER}",
                    "sha256:" + "7" * 64),
            # And the two read-side doors, driven the way the profile one is:
            # through bytes the write path would have refused.
            "intake_receipt_of": self.reading_back_a_hand_edited_intake,
            "retentions_of": self.reading_back_a_hand_edited_retention,
        }

    def reading_back_a_hand_edited_intake(self):
        """The custody read-side probe.

        The attempt is RECORDED through the real door -- an intake receipt is
        derived from its attempt and compared against the stored operation id,
        so a fabricated attempts row would be refused for that mismatch and
        would prove nothing about §13. What is hand-edited is the one column
        the receipt composes rather than adopts: `why`, which `_seal` builds
        out of the live assignment it found.
        """
        attempt_id = "attempt-1"
        worker_manager.record_attempt(
            self.store, attempt_id=attempt_id, adapter_name="acp",
            adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE,
            policy_digest="sha256:" + "2" * 64)
        found = self.store._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone()
        attempt = {name: found[name] for name in schema.ATTEMPT_COLUMNS}
        self.store._connection.execute(
            "INSERT INTO intakes (runtime_attempt_id, receipt_digest, "
            "result_id, manifest_digest, custody, why, recoverable, "
            "collect_operation_id, intake_operation_id, sealed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (attempt_id, "sha256:" + "0" * 64, "result-1",
             "sha256:" + "1" * 64, "quarantined",
             f"collected under {BEARER}", 0,
             worker_manager.collect_operation(attempt)["operation_id"],
             worker_manager.intake_operation(attempt)["operation_id"], NOW))
        return worker_manager.intake_receipt_of(self.store, attempt_id)

    def reading_back_a_hand_edited_retention(self):
        """The retention read-side probe, and it needs NO attempt at all --
        which is the point of it being separate. A retention decision is
        written under its own operation, so the row that can be edited
        underneath this manager is not the intake row."""
        self.store._connection.execute(
            "INSERT INTO retentions (runtime_attempt_id, artifact_id, "
            "disposition, retention_policy_digest, retain_operation_id, "
            "decided_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("attempt-1", "artifact-1", "retain", f"sha256:{BEARER}",
             "output.retain:" + "0" * 64, NOW))
        return worker_manager.retentions_of(self.store, "attempt-1")

    def reading_back_a_hand_edited_profile(self):
        """The read-side probe. The row is written BEHIND the write guard,
        because a profile carrying a live bearer cannot be certified through
        the public path — which is exactly why the read side needs its own
        walk: the store can hold what the door refused."""
        profile = _profile_carrying(BEARER)
        self.store._connection.execute(
            "INSERT INTO profiles (kind, name, digest, body, certified_at, "
            "withdrawn_at) VALUES ('agent-session', ?, ?, ?, ?, NULL)",
            (profile["profile_id"], profile["document_digest"],
             json.dumps(profile), NOW))
        return worker_manager.certified_agent_session_profile(
            self.store, profile["document_digest"])

    def test_every_constructing_surface_refuses_a_live_bearer(self):
        """The entries above are FACTS rather than claims. Each drives the
        real exported operation and requires the closed §13 pair."""
        probes = self.constructing_probes()
        self.assertEqual(sorted(probes),
                         sorted(CONSTRUCTS_A_PORTABLE_ARTEFACT))
        for name, run in sorted(probes.items()):
            with self.subTest(surface=name):
                self.setUp()
                with held_secret(BEARER):
                    with self.assertRaises(ContractRefusal) as caught:
                        run()
                self.assertEqual(caught.exception.code, "secret-leak",
                                 caught.exception.message)

    def test_the_public_sweep_can_actually_fail(self):
        """Every surface is accounted for today, so relaxing the check changes
        no verdict — measured. The way to test a guard with nothing to catch
        is to hand it something."""
        fabricated = "invented_public_surface"
        self.assertNotIn(fabricated, CONSTRUCTS_A_PORTABLE_ARTEFACT)
        self.assertNotIn(fabricated, RETURNS_NO_CONSTRUCTED_ARTEFACT)
        self.assertNotIn(fabricated, self.exported())


# -- bounded diagnostics: the crossing, and the sweep that drives it ----------

class TheRefusalConstructorIsTheOneCrossing(SecretCase):
    """§13's containment rule where every diagnostic becomes durable.

    Fifth review [P1] named two public doors whose shape diagnostic quoted a
    live bearer before their walk, and asked for a re-audit of the other
    public document owners. The re-audit was a MEASUREMENT rather than a
    reading — `NoPublicRefusalQuotesALiveBearer` below is that measurement,
    kept — and it found thirty leaking surfaces rather than two. Ordering the
    walk at each door corrects the two and leaves twenty-eight, and the next
    door written joins them.

    So the rule is at the crossing every diagnostic passes through instead.
    `ContractRefusal` already owns its message as durable text: it decides the
    message is text, that it is encodable, and that it is bounded. "A bounded
    diagnostic cannot itself leak" is the same kind of rule as those three.
    """

    def test_a_refusal_quoting_a_live_bearer_cannot_be_constructed(self):
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("refused", "precondition",
                                f"attempt {BEARER} is not open")
        self.assertEqual(caught.exception.code, "secret-leak")
        self.assertNotIn(BEARER, caught.exception.message)

    def test_the_substitution_keeps_the_durability_it_replaced(self):
        """A leak found while composing a diagnostic does not un-write what
        the raising site had already written. A durable refusal replaced by a
        non-durable one would tell a caller nothing happened."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("policy", "retention",
                                f"held because of {BEARER}", durable=True)
        self.assertTrue(caught.exception.durable)
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("policy", "retention",
                                f"held because of {BEARER}")
        self.assertFalse(caught.exception.durable)

    def test_the_substitute_is_proved_by_containment_and_never_exempted(self):
        """SIXTH REVIEW [P1] REPLACED THIS ASSERTION, and the old one was the
        defect.

        It required a refusal whose message IS the substitute prose to be
        constructed unchanged while that prose was registered live — which is
        exactly the equality exemption the review refuted. Equality is the
        wrong test for a containment rule: the registry admits any non-empty
        value, so a live bearer can be a SUBSTRING of the constant, and the
        exempt replacement then carried the whole live value out.

        The replacement passes the same containment test as everything else
        now, so a live value it would contain makes it give way.
        """
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("integrity", "schema", f"this is {BEARER}")
        substitute = caught.exception.message
        self.assertEqual(substitute, SECRET_LEAK_MESSAGE)
        with held_secret(substitute):
            with self.assertRaises(ContractRefusal) as refused:
                ContractRefusal("integrity", "secret-leak", substitute)
        self.assertNotIn(substitute, refused.exception.message)

    def test_the_replacement_gives_way_to_an_empty_message_and_not_to_a_leak(
            self):
        """The fallback is the ONE string a non-empty value cannot be
        contained in, and `remember_secret` refuses an empty value — so it is
        safe by construction rather than by inspection. What must NOT give way
        is the closed pair: the code is the diagnostic, and the prose is the
        part that can be spent."""
        piece = SECRET_LEAK_MESSAGE[:32]
        with held_secret(piece):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("policy", "retention",
                                f"held because of {piece}", durable=True)
        self.assertEqual(caught.exception.message, "")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "secret-leak"))
        self.assertTrue(caught.exception.durable,
                        "the empty fallback lost the durability it replaced")

    def test_an_empty_message_is_accepted_because_it_can_carry_nothing(self):
        """The terminal case, stated as its own fact. If this ever refused,
        the fallback above would have no bottom."""
        with held_secret(BEARER):
            refusal = ContractRefusal("integrity", "secret-leak", "")
        self.assertEqual(refusal.message, "")

    def test_the_prose_is_still_used_when_it_carries_nothing_live(self):
        """The other half: giving way is the exception, not the rule. An
        ordinary leak still gets the readable diagnostic."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("integrity", "schema", f"this is {BEARER}")
        self.assertEqual(caught.exception.message, SECRET_LEAK_MESSAGE)

    def test_one_snapshot_answers_both_questions(self):
        """The message and the replacement are one decision. Asking the
        registry twice would let it move between the two answers, and a
        replacement proved clean under a view nobody used is not proved."""
        seen = []
        real = secrets._snapshot

        def counted():
            seen.append(1)
            return real()

        secrets._snapshot = counted
        try:
            with held_secret(BEARER):
                with self.assertRaises(ContractRefusal):
                    ContractRefusal("integrity", "schema", f"is {BEARER}")
        finally:
            secrets._snapshot = real
        # One for the leaking message and its replacement together, and one
        # for the replacement's own construction. Never one per question.
        self.assertEqual(len(seen), 2, seen)

    def test_the_substitute_cannot_quote_a_live_bearer_substring(self):
        """Containment applies to the replacement too, not only equality.

        A claim token may be any 32-character string, including a substring
        of this build's constant prose. Exempting the whole replacement from
        the guard must not let that live value leave in the replacement.
        """
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("integrity", "schema", f"this is {BEARER}")
        bearer = caught.exception.message[:32]
        self.assertEqual(len(bearer), 32)
        with held_secret(bearer):
            with self.assertRaises(ContractRefusal) as caught:
                ContractRefusal("integrity", "schema", f"this is {bearer}")
        self.assertNotIn(bearer, caught.exception.message)

    def test_an_ordinary_refusal_is_untouched(self):
        """The other half. With nothing held, the diagnostic the raising site
        wrote is the diagnostic the caller gets — a correction that turned
        every refusal into `secret-leak` would be a different defect with a
        green gate."""
        refusal = ContractRefusal("refused", "precondition",
                                  f"attempt {BEARER} is not open")
        self.assertEqual(refusal.code, "precondition")
        self.assertIn(BEARER, refusal.message)

    def test_a_forgotten_bearer_stops_being_a_leak(self):
        """The dynamic rule, restated for diagnostics: the guard refuses a
        value this process is HOLDING. A spent bearer is absent from the
        registry, so an old refusal quoting it still constructs and an exact
        durable replay still answers."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal):
                ContractRefusal("policy", "retention", f"was {BEARER}")
        self.assertEqual(
            ContractRefusal("policy", "retention", f"was {BEARER}").code,
            "retention")

    def test_the_message_owner_s_other_rules_still_fire(self):
        """The §13 rule is added to that owner, not substituted for it."""
        with self.assertRaises(AssertionError):
            ContractRefusal("integrity", "schema", 7)
        with self.assertRaises(AssertionError):
            ContractRefusal("integrity", "schema", "x" * (MESSAGE_LIMIT + 1))
        with self.assertRaises(AssertionError):
            ContractRefusal("integrity", "schema", "ordinary", durable="yes")

    def test_the_pair_assertions_cannot_quote_a_live_bearer(self):
        """The constructor's own earlier diagnostics are public text too.

        Category and code are raising-site assertions, but that taxonomy does
        not permit the assertion itself to carry a currently live value. The
        centralized crossing must cover checks that precede message acceptance
        as well as an otherwise valid refusal message.
        """
        for category, code in ((BEARER, "schema"),
                               ("integrity", BEARER)):
            with self.subTest(field="category" if category == BEARER
                              else "code"):
                with held_secret(BEARER):
                    with self.assertRaises(AssertionError) as caught:
                        ContractRefusal(category, code, "ordinary")
                self.assertNotIn(BEARER, str(caught.exception))


    def test_an_ordinary_bad_pair_is_still_quoted_verbatim(self):
        """PROVED, NOT SUPPRESSED. A misspelled category is a build defect
        and quoting it is the whole use of this message; only a value the
        registry says is live gives way."""
        with self.assertRaises(AssertionError) as caught:
            ContractRefusal("integrty", "schema", "ordinary")
        self.assertIn("integrty", str(caught.exception))
        with self.assertRaises(AssertionError) as caught:
            ContractRefusal("integrity", "shcema", "ordinary")
        self.assertIn("shcema", str(caught.exception))

    def test_a_live_pair_operand_gives_way_to_a_sentence_that_says_so(self):
        """It gives way to an explanation rather than to silence: a reader
        has to be able to tell a redaction from a missing value."""
        with held_secret(BEARER):
            with self.assertRaises(AssertionError) as caught:
                ContractRefusal(BEARER, "schema", "ordinary")
        self.assertNotIn(BEARER, str(caught.exception))
        self.assertIn("§13", str(caught.exception))
        self.assertIn("frozen error categories", str(caught.exception),
                      "the assertion stopped saying what was wrong")

    def test_a_pair_operand_that_is_not_text_is_named_by_its_type(self):
        """The same rule `name_value` follows: a value with behaviour is
        described from inert facts and never rendered."""
        class Hostile:
            def __repr__(self):
                raise RuntimeError("a caller's code ran inside a diagnostic")

        with self.assertRaises(AssertionError) as caught:
            ContractRefusal(Hostile(), "schema", "ordinary")
        self.assertIn("Hostile", str(caught.exception))

    def test_a_live_bearer_containing_pair_operand_gives_way_too(self):
        """CONTAINMENT, here as everywhere. An invalid category that merely
        CONTAINS a live value carries it just as durably as one that is it."""
        with held_secret(BEARER):
            with self.assertRaises(AssertionError) as caught:
                ContractRefusal(f"integrity-{BEARER}", "schema", "ordinary")
        self.assertNotIn(BEARER, str(caught.exception))

    def test_the_pair_and_the_message_share_one_snapshot(self):
        """One construction, one view of the registry. Two reads could
        disagree about the same value between the pair check and the
        message check."""
        seen = []
        real = secrets._snapshot

        def counted():
            seen.append(1)
            return real()

        secrets._snapshot = counted
        try:
            with held_secret(BEARER):
                with self.assertRaises(AssertionError):
                    ContractRefusal(BEARER, "schema", f"and {BEARER}")
        finally:
            secrets._snapshot = real
        self.assertEqual(len(seen), 1,
                         f"the registry was read {len(seen)} times for one "
                         f"construction")

    def test_pair_ownership_precedes_membership_and_runs_no_caller_hash(self):
        """`_rejected` cannot own a malformed pair operand after membership.

        Mapping and set membership hash their question. A caller-controlled
        value can therefore run or raise before the new safe diagnostic is
        reached, replacing the promised raising-site assertion with an
        exception carrying whatever text the caller chose.
        """
        class Hostile:
            def __hash__(self):
                raise RuntimeError(BEARER)

        for category, code in ((Hostile(), "schema"),
                               ("integrity", Hostile())):
            with self.subTest(field="category" if category != "integrity"
                              else "code"):
                with held_secret(BEARER):
                    with self.assertRaises(AssertionError) as caught:
                        ContractRefusal(category, code, "ordinary")
                self.assertNotIn(BEARER, str(caught.exception))

    def test_pair_redactions_are_themselves_proved_by_containment(self):
        """Safe provenance is not safe content.

        The preferred redaction and an inert type name are both build-owned,
        but either may CONTAIN a currently live value just as the sixth
        review's preferred refusal message did. The assertion that leaves the
        constructor must prove its composed text, not only its input string.
        """
        redaction = ("a string §13 will not let this build quote, because the "
                     "registry says it is live")
        redaction_bearer = redaction[:32]
        type_bearer = "S" * 32
        SecretNamedType = type(type_bearer, (), {})
        for name, bearer, category in (
                ("redaction", redaction_bearer, redaction_bearer),
                ("type name", type_bearer, SecretNamedType())):
            with self.subTest(source=name):
                with held_secret(bearer):
                    with self.assertRaises(AssertionError) as caught:
                        ContractRefusal(category, "schema", "ordinary")
                self.assertNotIn(bearer, str(caught.exception))

    def test_message_and_durability_type_assertions_do_not_consult_metaclass(
            self):
        """The later constructor assertions are pre-guard diagnostics too.

        This module already owns a type-name helper that bypasses metaclass
        dispatch. Reading `type(value).__name__` here instead lets caller code
        choose the text, including a currently live bearer.
        """
        reads = []

        class Meta(type):
            def __getattribute__(self, name):
                if name == "__name__":
                    reads.append(name)
                    return BEARER
                return super().__getattribute__(name)

        class Hostile(metaclass=Meta):
            pass

        for field in ("message", "durable"):
            with self.subTest(field=field):
                before = len(reads)
                with held_secret(BEARER):
                    with self.assertRaises(AssertionError) as caught:
                        if field == "message":
                            ContractRefusal("integrity", "schema", Hostile())
                        else:
                            ContractRefusal("integrity", "schema", "ordinary",
                                            durable=Hostile())
                self.assertEqual(len(reads), before,
                                 "a rejected value ran its metaclass")
                self.assertNotIn(BEARER, str(caught.exception))


    def test_every_assertion_in_the_constructor_goes_through_the_one_owner(
            self):
        """THE CONSTRUCTION, read from the source rather than trusted.

        Eighth review [P1] asked for constructor assertions to be covered by
        construction rather than by one exemption per reproduction. This is
        what makes that checkable: every `raise AssertionError` inside
        `ContractRefusal.__init__` must pass its text through `_defect`, so a
        diagnostic added tomorrow is proved tomorrow instead of becoming the
        next reproduction.
        """
        source = pathlib.Path(errors.__file__).resolve()
        tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
        found = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef)
                    and node.name == "ContractRefusal"):
                continue
            for method in node.body:
                if not (isinstance(method, ast.FunctionDef)
                        and method.name == "__init__"):
                    continue
                for inner in ast.walk(method):
                    if not (isinstance(inner, ast.Raise)
                            and isinstance(inner.exc, ast.Call)
                            and isinstance(inner.exc.func, ast.Name)
                            and inner.exc.func.id == "AssertionError"):
                        continue
                    argument = inner.exc.args[0] if inner.exc.args else None
                    owned = (isinstance(argument, ast.Call)
                             and isinstance(argument.func, ast.Name)
                             and argument.func.id == "_defect")
                    found.append((inner.lineno, owned))
        self.assertGreaterEqual(len(found), 5,
                                "the constructor's assertions moved; this "
                                "case is about all of them")
        self.assertEqual([at for at, owned in found if not owned], [],
                         "an AssertionError leaves the constructor without "
                         "its text being proved against the live registry")

    def test_no_assertion_in_the_constructor_names_a_type_unsafely(self):
        """`type(x).__name__` consults a caller-controlled metaclass, which
        this module has refused to do since W6782. The helper exists; the
        constructor has to use it."""
        source = pathlib.Path(errors.__file__).resolve()
        tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
        unsafe = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef)
                    and node.name == "ContractRefusal"):
                continue
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Attribute)
                        and inner.attr == "__name__"):
                    unsafe.append(inner.lineno)
        self.assertEqual(unsafe, [],
                         "the constructor reads __name__ through ordinary "
                         "attribute lookup, which runs a metaclass")

    def test_a_pair_operand_with_a_hostile_hash_never_runs(self):
        """Shape before membership. `x in mapping` hashes x, and `__hash__`
        is caller code — so the check meant to OWN the operand was running
        it, and an unhashable one escaped as a raw TypeError."""
        class Hostile:
            def __hash__(self):
                raise RuntimeError("a caller's hash ran inside the owner")

        class Unhashable:
            __hash__ = None

        for what in (Hostile(), Unhashable(), ["integrity"], 7):
            for field in ("category", "code"):
                with self.subTest(kind=type(what).__name__, field=field):
                    pair = {"category": "integrity", "code": "schema"}
                    pair[field] = what
                    with self.assertRaises(AssertionError) as caught:
                        ContractRefusal(pair["category"], pair["code"], "ok")
                    self.assertIn(field, str(caught.exception))

    def test_the_defect_text_gives_way_whole_when_its_own_words_are_live(self):
        """Safe provenance is not safe content. A redaction sentence and a
        type name are text this build owns, and a live value may equal a
        substring of either."""
        piece = DEFECT_REDACTED[:32]
        with held_secret(piece):
            with self.assertRaises(AssertionError) as caught:
                ContractRefusal("integrity", "schema", 7)
        self.assertNotIn(piece, str(caught.exception))

    def test_a_live_type_name_cannot_leave_in_an_assertion(self):
        """The review's own example: a build-owned class name can itself be
        the currently live value."""
        class Bearer:
            pass

        Bearer.__qualname__ = Bearer.__name__ = "b" * 40
        with held_secret("b" * 40):
            with self.assertRaises(AssertionError) as caught:
                ContractRefusal("integrity", "schema", Bearer())
        self.assertNotIn("b" * 40, str(caught.exception))

    def test_an_ordinary_defect_still_reads_as_one(self):
        """The other half, for all five assertions: with nothing live, each
        says what is wrong in its own words."""
        cases = [
            (("integrty", "schema", "ok"), "frozen error categories"),
            (("integrity", "shcema", "ok"), "pairing is closed"),
            ((7, "schema", "ok"), "category"),
            (("integrity", "schema", 7), "is text"),
            (("integrity", "schema", "x" * (MESSAGE_LIMIT + 1)), "at most"),
        ]
        for operands, fragment in cases:
            with self.subTest(operands=operands[:2]):
                with self.assertRaises(AssertionError) as caught:
                    ContractRefusal(*operands)
                self.assertIn(fragment, str(caught.exception))
        with self.assertRaises(AssertionError) as caught:
            ContractRefusal("integrity", "schema", "ok", durable="yes")
        self.assertIn("Boolean", str(caught.exception))


class NoPublicRefusalQuotesALiveBearer(SecretCase):
    """THE RE-AUDIT FIFTH REVIEW [P1] ASKED FOR, kept as a gate.

    The universe is `__all__` and the exported classes' public methods — the
    same derivation `EveryPublicSurfaceIsAccountedFor` uses, asserted equal to
    it below so the two cannot drift. Every surface is DRIVEN with the live
    bearer in every operand it takes, and none of them may answer with a
    diagnostic containing it.

    This is a probe rather than an inventory on purpose. The reason a fifth
    review was needed is that four rounds of reasoning about which doors quote
    their operands produced four incomplete answers; handing every door a
    spoiled operand and reading what comes back produces a fact.
    """

    def drivers(self):
        """One call per public surface, with the bearer in every operand.

        `store` and `port` take the fixture's own, because a surface that
        refuses its store before reading anything else proves nothing about
        the diagnostic it builds for the operand under test. `ControlStore.open`
        takes a real temporary path for the same reason — and because naming a
        database after the secret would be its own §13 failure.
        """
        drivers = {}
        for name in sorted(worker_manager.__all__):
            member = getattr(worker_manager, name)
            if isinstance(member, type):
                # THE CLASS ITSELF IS A SURFACE. `__all__` exports it, so
                # constructing one is a public call that builds diagnostics
                # about the operands it was handed.
                drivers[name] = self.driver(member)
                for attribute in sorted(dir(member)):
                    if attribute.startswith("_"):
                        continue
                    bound = getattr(member, attribute, None)
                    if not callable(bound):
                        continue
                    owner = {"ControlStore": self.store,
                             "AuthorityPort": self.port}[name]
                    drivers[f"{name}.{attribute}"] = self.driver(
                        getattr(owner, attribute)
                        if attribute != "open" else member.open,
                        opening=(attribute == "open"))
            elif callable(member):
                drivers[name] = self.driver(member)
        return drivers

    def driver(self, member, opening=False):
        signature = inspect.signature(member)
        args, kwargs = [], {}
        for parameter in signature.parameters.values():
            if parameter.kind in (parameter.VAR_POSITIONAL,
                                  parameter.VAR_KEYWORD):
                continue
            if parameter.name == "store":
                value = self.store
            elif parameter.name == "port":
                value = self.port
            elif opening and parameter.name == "path":
                value = os.path.join(self._root.name, "probe.sqlite3")
            else:
                value = BEARER
            if (parameter.kind == parameter.KEYWORD_ONLY
                    or parameter.default is not parameter.empty):
                kwargs[parameter.name] = value
            else:
                args.append(value)
        return lambda: member(*args, **kwargs)

    def test_the_universe_agrees_with_the_public_inventory(self):
        """One derivation, read twice. A surface this sweep cannot reach would
        be a surface the inventory accounts for and nobody drives."""
        inventory = EveryPublicSurfaceIsAccountedFor("exported")
        inventory.setUp()
        self.assertEqual(sorted(self.drivers()), sorted(inventory.exported()))

    def test_no_public_surface_answers_with_a_bearer_in_its_diagnostic(self):
        """The measurement. Thirty of these answered with the bearer in the
        message before the crossing guard existed."""
        refused = 0
        for name, drive in sorted(self.drivers().items()):
            with self.subTest(surface=name):
                self.setUp()
                with held_secret(BEARER):
                    try:
                        drive()
                    except ContractRefusal as refusal:
                        refused += 1
                        self.assertNotIn(BEARER, refusal.message, name)
                    except Exception as raised:
                        # A raw exception escaping is a DIFFERENT defect and
                        # not this Work's to fix; one carrying the bearer is
                        # this Work's, because §13 is about the text, not
                        # about which type carried it.
                        self.assertNotIn(BEARER, str(raised), name)
        self.assertGreater(refused, 25, "the sweep drove nothing that refused")

    def test_the_sweep_can_actually_fail(self):
        """A gate with nothing to catch is tested by handing it something. The
        stand-in is built the way the leaking doors built theirs: a diagnostic
        naming the operand it rejects, composed while the bearer is live."""
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                try:
                    raise ContractRefusal("integrity", "schema",
                                          f"this is {BEARER}")
                except ContractRefusal as refusal:
                    self.assertNotIn(BEARER, refusal.message)
                    raise
        self.assertEqual(caught.exception.code, "secret-leak")


class EveryDurableWriterIsGuarded(unittest.TestCase):
    """The sweep, DERIVED rather than remembered.

    An inventory that begins with the guards the code already performs cannot
    discover a missing one — it reports a clean sweep over exactly the writers
    that already have coverage. So the universe here is every INSERT and
    UPDATE statement in the manager package, read from the AST, and coverage is
    looked up against that rather than the other way round.
    """

    def writers(self):
        """(module, lexical site, table) for every durable write."""
        found = set()
        for source in sorted(PACKAGE.rglob("*.py")):
            tree = ast.parse(source.read_text(encoding="utf-8"), str(source))

            def walk(node, prefix=""):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef,
                                          ast.AsyncFunctionDef)):
                        for piece in ast.walk(child):
                            table = self.written_table(piece)
                            if table is not None:
                                found.add((source.name,
                                           f"{prefix}{child.name}", table))
                    elif isinstance(child, ast.ClassDef):
                        walk(child, f"{prefix}{child.name}.")
            walk(tree)
        return found

    @staticmethod
    def written_table(node):
        """The table this call WRITES, or None if it is not a write."""
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute" and node.args):
            return None
        pieces, stack = [], [node.args[0]]
        while stack:
            item = stack.pop(0)
            if isinstance(item, ast.Constant) and type(item.value) is str:
                pieces.append(item.value)
            elif isinstance(item, ast.BinOp):
                stack[:0] = [item.left, item.right]
            elif isinstance(item, ast.JoinedStr):
                stack[:0] = list(item.values)
        text = " ".join(pieces)
        words = text.replace("(", " ").split()
        if not words:
            return None
        head = words[0].upper()
        if head == "INSERT":
            at = next((index for index, word in enumerate(words)
                       if word.upper() == "INTO"), None)
            return None if at is None else words[at + 1]
        if head == "UPDATE":
            return words[1]
        return None

    def test_the_universe_is_not_read_from_the_coverage_table(self):
        """The rule that makes a sweep worth having: a writer with no coverage
        must be discoverable, so the universe cannot be derived from the
        coverage."""
        writers = self.writers()
        self.assertGreater(len(writers), 15, writers)
        self.assertIn(("store.py", "ControlStore._record", "operations"),
                      writers)

    def test_every_durable_writer_is_covered(self):
        uncovered = sorted(entry for entry in self.writers()
                           if entry not in COVERED_ELSEWHERE
                           and entry != ("store.py", "ControlStore._record",
                                         "operations"))
        self.assertEqual(uncovered, [],
                         "durable writers with no §13 coverage")

    def test_no_declared_coverage_is_stale(self):
        """A list of exceptions nobody compares to the code is a list of
        things somebody remembered."""
        writers = self.writers()
        for entry in sorted(COVERED_ELSEWHERE):
            with self.subTest(entry=entry):
                self.assertIn(entry, writers)

    def test_the_journal_writer_is_the_one_that_walks(self):
        """The single point every mutating act passes through, named here so
        the coverage table above can say "the journal" and mean something."""
        source = (PACKAGE / "store.py").read_text(encoding="utf-8")
        record = source.split("def _record(")[1].split("\n    def ")[0]
        self.assertIn("check_no_durable_secret", record)

    def test_the_sweep_can_actually_fail(self):
        """Nothing is uncovered today, so relaxing the check changes no
        verdict — measured. The way to test a guard with nothing to catch is
        to hand it something."""
        fabricated = ("nowhere.py", "invented", "table")
        self.assertNotIn(fabricated, COVERED_ELSEWHERE)
        self.assertNotIn(fabricated, self.writers())


class TheAgentSessionProfileIsWalked(SecretCase):

    def test_a_certified_profile_carrying_a_live_bearer_is_refused(self):
        from .test_handshake import acp_profile
        body = acp_profile()
        spoiled = dict(body, mcp_servers=[BEARER])
        spoiled.pop("document_digest")
        spoiled["document_digest"] = digest(spoiled)
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                worker_manager.certify_agent_session_profile(self.store,
                                                             spoiled)
            self.assertEqual(caught.exception.code, "secret-leak")


# -- helpers -----------------------------------------------------------------

_VECTORS = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
            / "2026" / "08" / "finding-v12-isolated-agent-workers"
            / "findings" / "finding-v12-worker-contract" / "findings"
            / "finding-worker-control-api-manifests" / "evidence"
            / "vectors.json")


def _published_input():
    published = json.loads(_VECTORS.read_text(encoding="utf-8"))
    for case in published["valid"]:
        document = case["document"]
        if document.get("schema") == "baton.worker-manifest/input":
            return document
    raise AssertionError("the published vectors carry no input manifest")


def _resealed(document):
    body = {name: value for name, value in document.items()
            if name != "manifest_digest"}
    return {**body, "manifest_digest": digest(body)}


def _attempt_carrying(bearer):
    """A caller's attempt mapping, optionally with a live bearer in its own id.

    The four intake operation identities take an ATTEMPT rather than an attempt
    id and derive protocol identity from it, so no store is needed to drive
    them -- and no store is WANTED either: what these prove is that the
    construction walks what it was handed, and a fixture that could only
    produce clean attempts would prove it against material the leak cannot
    reach.

    Every column `ATTEMPT_COLUMNS` names is present because the exported
    operations require the whole set, and the nullable ones stay null: the
    assignment fixes are absent, so the derivation runs its no-assignment path
    and the walk still covers the id and the operands.
    """
    attempt = {name: None for name in schema.ATTEMPT_COLUMNS}
    attempt.update({
        "runtime_attempt_id": ("attempt-1" if bearer is None
                               else f"attempt-{bearer}"),
        "adapter_name": "acp",
        "adapter_digest": "sha256:" + "a" * 64,
        "profile_digest": PROFILE,
        "created_at": NOW,
        "observation_seq": 0,
    })
    return attempt


def _profile_carrying(bearer):
    from .test_handshake import acp_profile
    body = dict(acp_profile(), mcp_servers=[bearer])
    body.pop("document_digest")
    body["document_digest"] = digest(body)
    return body


def _file_carrying(path, document):
    """Put a document into the manifests table BEHIND this build's back.

    `load_manifest` re-walks what it hands back, and the only way to drive
    that is to file bytes the write path would have refused — which is the
    point: a store nobody validates on the way out is a store where a hand
    edit outlives every guard on the way in.
    """
    from baton_v12.contracts import canonical_bytes
    body = {name: value for name, value in document.items()
            if name != "manifest_digest"}
    key = digest(body)
    beside = sqlite3.connect(path, isolation_level=None)
    try:
        beside.execute(
            "INSERT OR REPLACE INTO manifests (digest, schema, body, "
            "retained_at) VALUES (?, ?, ?, ?)",
            (key, document["schema"],
             canonical_bytes(document).decode("utf-8"), NOW))
    finally:
        beside.close()
    return key


def _dump(path):
    beside = sqlite3.connect(path, isolation_level=None)
    try:
        tables = [row[0] for row in beside.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")]
        return json.dumps(
            {table: beside.execute(f"SELECT * FROM {table}").fetchall()
             for table in tables}, default=str)
    finally:
        beside.close()


if __name__ == "__main__":
    unittest.main()
