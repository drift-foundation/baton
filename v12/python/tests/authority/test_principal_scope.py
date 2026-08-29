"""W16821 — the principal/scope authority seam, and the schema-2 boundary.

W16793 found that one `team.member` string served as route endpoint, session
identity, authorization principal, capability grantee, claim-capacity key,
Handler and audit actor.  This module holds the correction to its acceptance:

  * two endpoint addresses map to ONE principal, and the second concurrent
    claim is refused by the shared slot;
  * a different endpoint, route or scope string cannot CHOOSE or WIDEN the
    principal or the effective scope;
  * claim and receipt evidence expose the endpoint separately from principal,
    effective scope, role, grant provenance and policy generation;
  * direct M2 grants are representable, and inherited/masked provenance is a
    shape the store admits and this cut refuses to produce;
  * a schema-1 store is refused READ-ONLY, byte for byte, with the operator
    told to initialize a fresh one (approver ruling M33752).

EVERY CASE DRIVES THE PRODUCTION SEAM.  Nothing here reimplements the mapping
or asserts against a value this module computed: the principal comes out of
`Core.principal_of`, the decision out of `Core.authorize`, and the evidence out
of the rows the transitions actually wrote.
"""

import os
import pathlib
import sqlite3
import tempfile
import unittest
from uuid import uuid4

from baton_v12.authority import Authority, Refusal, V11, V12
from baton_v12.authority.principals import (DEPLOYMENT_SCOPE, DIRECT, GRANTS,
                                            M2_GRANTS, AuthorizationDecision,
                                            check_grant_provenance,
                                            check_principal, check_scope,
                                            principal_for_endpoint)
from baton_v12.authority.schema import (META_AUTHORITY_UUID,
                                        META_SCHEMA_VERSION, META_STORE_KIND,
                                        SCHEMA_VERSION, STORE_KIND)

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
CLAUDE_ALIAS = "review.claude"
GEMINI = "baton.gemini"
ROUTE = "impl"
OTHER_ROUTE = "rview"
NOW = "2026-08-24T04:00:00.000Z"

ONE_PERSON = "principal:sl"
OTHER_SCOPE = "scope:platform"


class SeamCase(unittest.TestCase):
    """One disposable authority per case, owned and cleaned by the fixture."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w16821-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self._operations = 0

    def op(self):
        self._operations += 1
        return f"op-{self._operations}"

    def work(self, work_id=WORK, *, route=ROUTE, handlers=(CLAUDE,),
             scope=None, contract=V12):
        self.core.create_work(work_id, route, contract=contract, scope=scope, operation_id=("create-" + str(work_id))[:160])
        for participant in handlers:
            self.core.add_route_handler(route, participant)
        return work_id

    def rows(self, sql, *args):
        return self.core._store.all(sql, *args)

    def claim_event(self, work_id=WORK):
        """The claim event, out of the PUBLIC projection.

        Every case here reads the decision through this rather than through
        SQL: the acceptance is about what a consumer can see, and a case
        reading the column proves the column.
        """
        found = [row for row in self.authority.assignment_events(work_id)
                 if row["cause"] == "claimed"]
        self.assertEqual(len(found), 1, found)
        return found[0]

    def proposed(self, work_id=WORK, *, actor=CLAUDE, proposal_id="p-1"):
        """One claimed Work carrying one published proposal."""
        self.core.claim(work_id, actor, operation_id=self.op())
        self.core.publish(
            self.authority.assignment_of(work_id), proposal_id=proposal_id,
            result_id="r-1", result_digest="d" * 8, candidate_digest="c" * 8,
            input_digest="i" * 8, policy_digest="y" * 8,
            operation_id=self.op())
        return proposal_id


class OnePrincipalTwoAddresses(SeamCase):
    """The acceptance's positive case."""

    def test_two_endpoints_bound_to_one_principal_share_one_claim_slot(self):
        """THE WHOLE CORRECTION, in one case.

        Before this, `baton.claude` and `review.claude` were two participants
        and therefore two claim slots: one person could hold two live claims by
        being addressed differently, and §10.2's deployment-wide capacity was a
        limit the person it limits could opt out of.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.work(OTHER, route=OTHER_ROUTE, handlers=(CLAUDE_ALIAS,))
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON)
        # MEASURED, not assumed: the mapping is what the authority says it is.
        self.assertEqual(self.authority.principal_of(CLAUDE), ONE_PERSON)
        self.assertEqual(self.authority.principal_of(CLAUDE_ALIAS), ONE_PERSON)
        self.assertEqual(self.authority.endpoints_of(ONE_PERSON),
                         sorted([CLAUDE, CLAUDE_ALIAS]))

        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        with self.assertRaises(Refusal) as caught:
            self.core.claim(OTHER, CLAUDE_ALIAS, operation_id=self.op())
        # THE REASON IS PINNED, not just the refusal: a second claim refused
        # for some unrelated precondition would look identical here.
        self.assertIn("holds", str(caught.exception))
        self.assertIn(WORK, str(caught.exception))
        self.assertIn("across every endpoint address", str(caught.exception))
        # And the second Work is untouched -- no Handler, no slot moved.
        self.assertIsNone(self.authority.project_work(OTHER)["handler"])
        self.assertEqual(self.authority.slot_holder_of_principal(ONE_PERSON),
                         WORK)

    def test_the_slot_is_visible_through_either_address(self):
        """Asking by address answers about the PRINCIPAL.

        A read that answered "nothing" for an address whose person is holding a
        Work through their other address would be the capacity leak reappearing
        as a projection.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(self.authority.slot_holder(CLAUDE), WORK)
        self.assertEqual(self.authority.slot_holder(CLAUDE_ALIAS), WORK)

    def test_two_unbound_endpoints_are_two_principals_and_two_slots(self):
        """The default mapping is one principal per address, unchanged.

        This is the behaviour the deployment had before the correction, and it
        is the CONTROL for the case above: if unbound addresses also shared a
        slot, that case would pass without the binding doing anything.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.work(OTHER, route=OTHER_ROUTE, handlers=(GEMINI,))
        self.assertEqual(self.authority.principal_of(CLAUDE),
                         principal_for_endpoint(CLAUDE))
        self.assertNotEqual(self.authority.principal_of(CLAUDE),
                            self.authority.principal_of(GEMINI))
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.core.claim(OTHER, GEMINI, operation_id=self.op())
        self.assertEqual(self.authority.project_work(OTHER)["handler"], GEMINI)

    def test_one_principal_grants_reach_every_address_it_holds(self):
        """A capability is the PRINCIPAL's, so a second address has it too."""
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON)
        self.authority.grant_capability(CLAUDE, "verify")
        self.assertTrue(self.authority.holds_capability(CLAUDE_ALIAS, "verify"))
        self.assertEqual(self.authority.capabilities_of(CLAUDE_ALIAS),
                         ["verify"])
        # Revoked through EITHER address, because there is one grant.
        self.authority.revoke_capability(CLAUDE_ALIAS, "verify")
        self.assertFalse(self.authority.holds_capability(CLAUDE, "verify"))

    def test_an_endpoint_holding_a_claim_cannot_be_rebound(self):
        """Rebinding under a live claim would move occupied capacity."""
        self.work(WORK, handlers=(CLAUDE,))
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        with self.assertRaises(Refusal) as caught:
            self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.assertIn("holds a live claim", str(caught.exception))
        self.assertEqual(self.authority.principal_of(CLAUDE),
                         principal_for_endpoint(CLAUDE))


class NothingAnOperandSaysCanWidenIt(SeamCase):
    """The acceptance's negative case."""

    def test_no_exported_surface_takes_a_principal_for_the_actor(self):
        """A caller names an ENDPOINT and the authority resolves it.

        Checked against the surface itself rather than by reading the code: if
        a later cut added a `principal=` operand to a transition or to the
        session mint, this is where it would be noticed.
        """
        import inspect

        from baton_v12.authority.api import Authority as Face
        from baton_v12.authority.session import Session

        for holder in (Face, Session):
            for name, method in vars(holder).items():
                if name.startswith("_") or not callable(method):
                    continue
                try:
                    parameters = set(inspect.signature(method).parameters)
                except (TypeError, ValueError):
                    continue
                if name in ("bind_endpoint", "endpoints_of",
                            "slot_holder_of_principal"):
                    # The three configuration surfaces whose SUBJECT is a
                    # principal.  None of them is an actor operand: they say
                    # which identity to bind, read or ask about, and none of
                    # them performs an act attributed to it.
                    continue
                self.assertNotIn("principal", parameters,
                                 f"{holder.__name__}.{name}")

    def test_a_second_endpoint_cannot_claim_another_principals_identity(self):
        """Acting through an address bound to somebody else attributes the act
        to THAT somebody, and cannot borrow a third identity.

        Read through the PUBLIC projection.  Review [P1]: the first spelling
        of this case reached into raw SQL, so it established the column and not
        the evidence boundary the acceptance names.
        """
        self.work(WORK, handlers=(CLAUDE, GEMINI))
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.core.claim(WORK, GEMINI, operation_id=self.op())
        event = self.claim_event(WORK)
        self.assertEqual(event["assignment_ref"]["participant"], GEMINI)
        self.assertEqual(event["decision"]["endpoint"], GEMINI)
        self.assertEqual(event["decision"]["principal"],
                         principal_for_endpoint(GEMINI))
        self.assertNotEqual(event["decision"]["principal"], ONE_PERSON)

    def test_the_effective_scope_comes_off_the_work_and_not_the_caller(self):
        """A Work created in one scope authorizes in that scope, whoever
        claims it and through whatever route."""
        self.work(WORK, handlers=(CLAUDE,), scope=OTHER_SCOPE)
        self.assertEqual(self.authority.project_work(WORK)["scope"],
                         OTHER_SCOPE)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(self.claim_event(WORK)["decision"]["effective_scope"],
                         OTHER_SCOPE)

    def test_a_route_spelling_is_not_a_scope(self):
        """§2 of the correction boundary: the scope is never derived from the
        route, the repository or the participant spelling.

        Two Works on DIFFERENT routes, created without a scope, land in the
        SAME deployment scope -- which is what "not derived from the route"
        means, stated as a measurement rather than as an intention.
        """
        self.work(WORK, route=ROUTE, handlers=(CLAUDE,))
        self.work(OTHER, route=OTHER_ROUTE, handlers=(GEMINI,))
        self.assertEqual(self.authority.project_work(WORK)["scope"],
                         DEPLOYMENT_SCOPE)
        self.assertEqual(self.authority.project_work(OTHER)["scope"],
                         DEPLOYMENT_SCOPE)

    def test_a_grant_in_one_scope_does_not_authorize_another(self):
        """Direct grants are scoped, and a decision in a different scope is
        not carried by them."""
        self.authority.grant_capability(CLAUDE, "verify", scope=OTHER_SCOPE)
        self.assertTrue(self.authority.holds_capability(CLAUDE, "verify",
                                                        scope=OTHER_SCOPE))
        self.assertFalse(self.authority.holds_capability(CLAUDE, "verify"))
        self.assertIsNone(self.core.authorize(CLAUDE, capability="verify"))

    def test_a_participant_address_is_refused_where_a_principal_is_required(
            self):
        """The grammars do not overlap, which is what stops the substitution
        that caused the incompatibility."""
        for wrong in (CLAUDE, "scope:deployment", "", None, "principal:"):
            with self.subTest(wrong=wrong):
                with self.assertRaises(Refusal):
                    check_principal(wrong)
        for wrong in (CLAUDE, ONE_PERSON, "", None, "scope:"):
            with self.subTest(wrong=wrong):
                with self.assertRaises(Refusal):
                    check_scope(wrong)
        with self.assertRaises(Refusal):
            self.authority.bind_endpoint(CLAUDE, CLAUDE)

    def test_a_principal_is_bounded_by_whatever_bounds_its_endpoint(self):
        """A wide but legitimate address stays claimable.

        The first cut of the grammar capped a principal at the frozen
        `opaqueId` length, and `check_participant` caps nothing -- so a wide
        endpoint produced a principal the authority refused, and a valid
        participant became unclaimable with a refusal naming a value the caller
        never supplied.  This is that defect, kept.
        """
        wide = "baton." + "q" * 5000
        self.work(WORK, handlers=(wide,))
        self.core.claim(WORK, wide, operation_id=self.op())
        self.assertEqual(self.authority.project_work(WORK)["handler"], wide)
        self.assertEqual(self.authority.slot_holder(wide), WORK)


class TheDecisionRidesTheAct(SeamCase):
    """The acceptance's evidence case."""

    def test_a_claim_records_endpoint_principal_scope_grant_and_generation(
            self):
        self.work(WORK, handlers=(CLAUDE,), scope=OTHER_SCOPE)
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        generation = self.authority.policy_generation()
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        event = self.claim_event(WORK)
        # SIX SEPARATE FACTS where there used to be one string, and all six
        # through the projection a consumer actually reads.
        self.assertEqual(event["assignment_ref"]["participant"], CLAUDE)
        self.assertEqual(event["decision"], {
            "endpoint": CLAUDE, "principal": ONE_PERSON,
            "effective_scope": OTHER_SCOPE, "role": ROUTE, "grant": DIRECT,
            "policy_generation": generation})
        self.assertNotEqual(event["decision"]["endpoint"],
                            event["decision"]["principal"])

    def test_an_authority_act_records_no_decision(self):
        """A fence or a release is the authority acting on its own behalf.

        The provenance columns are nullable precisely so those rows do not have
        to invent a principal, which is the inference this correction forbids.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.core.end(self.authority.assignment_of(WORK),
                      operation_id=self.op())
        released = [row for row in self.authority.assignment_events(WORK)
                    if row["cause"] != "claimed"]
        self.assertTrue(released)
        for row in released:
            self.assertIsNone(row["decision"], row["cause"])

    def test_the_decision_seam_answers_a_decision_and_not_a_boolean(self):
        self.work(WORK, handlers=(CLAUDE,))
        decision = self.core.authorize(CLAUDE, route=ROUTE)
        self.assertIsInstance(decision, AuthorizationDecision)
        self.assertEqual(decision.as_document(), {
            "endpoint": CLAUDE,
            "principal": principal_for_endpoint(CLAUDE),
            "effective_scope": DEPLOYMENT_SCOPE,
            "role": ROUTE,
            "grant": DIRECT,
            "policy_generation": self.authority.policy_generation()})
        # An unconfigured route is no decision at all, not a decision saying no:
        # a caller cannot record provenance for an act that was refused.
        self.assertIsNone(self.core.authorize(GEMINI, route=ROUTE))

    def test_a_decision_names_one_question(self):
        with self.assertRaises(Refusal):
            self.core.authorize(CLAUDE)
        with self.assertRaises(Refusal):
            self.core.authorize(CLAUDE, route=ROUTE, capability="verify")

    def test_a_decision_cannot_be_edited_after_it_is_answered(self):
        self.work(WORK, handlers=(CLAUDE,))
        decision = self.core.authorize(CLAUDE, route=ROUTE)
        for attribute in ("principal", "effective_scope", "grant"):
            with self.subTest(attribute=attribute):
                with self.assertRaises(Refusal):
                    setattr(decision, attribute, "principal:someone-else")

    def test_every_configuration_act_advances_the_generation(self):
        """A decision names the configuration it was taken under, so a
        configuration that moved without advancing it would let an act claim a
        configuration that had already changed."""
        acts = [
            lambda: self.authority.certify_contract("baton.v12-assignment-1"),
            lambda: self.authority.withdraw_certification(
                "baton.v12-assignment-1"),
            lambda: self.authority.permit_contract_transition("a", "b"),
            lambda: self.authority.set_policy("canonical_target", "base-2"),
            lambda: self.authority.grant_capability(CLAUDE, "verify"),
            lambda: self.authority.revoke_capability(CLAUDE, "verify"),
            lambda: self.authority.add_route_handler(ROUTE, GEMINI),
            lambda: self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON),
        ]
        for act in acts:
            before = self.authority.policy_generation()
            act()
            self.assertEqual(self.authority.policy_generation(), before + 1,
                             act)


class GrantProvenance(SeamCase):
    """Direct grants now; the shape admits what M6 will need."""

    def test_this_cut_produces_direct_provenance_only(self):
        self.assertEqual(M2_GRANTS, (DIRECT,))
        with self.assertRaises(Refusal):
            check_grant_provenance("inherited")
        with self.assertRaises(Refusal):
            check_grant_provenance("masked")

    def test_the_durable_column_admits_inherited_and_masked(self):
        """The SHAPE, proved against the store rather than against the
        docstring: a column that could not hold an inherited grant would have
        to be migrated to gain one, and the correction boundary says it must
        admit them now."""
        self.authority.grant_capability(CLAUDE, "verify")
        principal = self.authority.principal_of(CLAUDE)
        connection = self.core._store._db
        for provenance in GRANTS:
            with self.subTest(provenance=provenance):
                connection.execute(
                    "INSERT OR REPLACE INTO capability (principal_id, "
                    "capability, scope, provenance, granted_at) "
                    "VALUES (?, 'verify', ?, ?, ?)",
                    (principal, DEPLOYMENT_SCOPE, provenance, NOW))
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT OR REPLACE INTO capability (principal_id, capability, "
                "scope, provenance, granted_at) "
                "VALUES (?, 'verify', ?, 'invented', ?)",
                (principal, DEPLOYMENT_SCOPE, NOW))

    def test_a_stored_provenance_this_cut_cannot_produce_is_refused_on_read(
            self):
        """READ WIDE, WRITE NARROW -- and the read still refuses to hand out a
        decision this cut has no resolver for.

        A row saying `inherited` is a row somebody put there ahead of the M6
        resolver.  Answering a decision from it would be claiming an
        inheritance walk that does not exist.
        """
        self.authority.grant_capability(CLAUDE, "verify")
        self.core._store._db.execute(
            "UPDATE capability SET provenance = 'inherited'")
        with self.assertRaises(Refusal) as caught:
            self.core.authorize(CLAUDE, capability="verify")
        self.assertIn("resolves no grant hierarchy", str(caught.exception))

    def test_the_refusals_name_exactly_the_vocabularies_they_enforce(self):
        """The messages spell the vocabularies out as literals, so this holds
        the literals to the constants."""
        with self.assertRaises(Refusal) as caught:
            check_grant_provenance("invented")
        for one in GRANTS:
            self.assertIn(one, str(caught.exception))
        with self.assertRaises(Refusal) as caught:
            check_grant_provenance(GRANTS[1])
        for one in M2_GRANTS:
            self.assertIn(one, str(caught.exception))

    def test_a_receipt_carries_the_decision_beside_its_actor(self):
        self.authority.grant_capability(CLAUDE, "verify")
        self.work(WORK, handlers=(CLAUDE,))
        self.proposed()
        self.core.verify(proposal_id="p-1", verification_id="v-1",
                         actor=CLAUDE, observation="passed",
                         operation_id=self.op())
        receipt = self.authority.receipt("p-1", "verification")
        self.assertEqual(receipt["actor"], CLAUDE)
        self.assertEqual(receipt["decision"], {
            "endpoint": CLAUDE, "principal": principal_for_endpoint(CLAUDE),
            "effective_scope": DEPLOYMENT_SCOPE, "role": "verify",
            "grant": DIRECT,
            "policy_generation": self.authority.policy_generation()})


class SchemaTwoIsACleanInitializationBoundary(unittest.TestCase):
    """Approver ruling M33752, as a measurement.

    A schema-1 store is this build's own older product.  It is refused
    read-only, it is not interpreted, and the operator is told what to do.
    """

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w16821-schema-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name

    def schema_one(self, name="old.sqlite3"):
        """A store recording THIS product at the PREVIOUS schema version.

        Built by hand, because the whole point is that this build cannot
        create one: there is no downgrade path and adding one to make a test
        convenient would be adding the migration the ruling excludes.
        """
        path = os.path.join(self.root, name)
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, "
                           "value TEXT NOT NULL)")
        for key, value in ((META_STORE_KIND, STORE_KIND),
                           (META_SCHEMA_VERSION, str(SCHEMA_VERSION - 1)),
                           (META_AUTHORITY_UUID, UUID)):
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (key, value))
        connection.execute("CREATE TABLE work (work_id TEXT PRIMARY KEY, "
                           "route TEXT NOT NULL)")
        connection.execute("INSERT INTO work (work_id, route) VALUES (?, ?)",
                           (WORK, ROUTE))
        connection.close()
        return path

    def test_the_older_store_is_refused_and_the_operator_is_told_what_to_do(
            self):
        path = self.schema_one()
        with self.assertRaises(Refusal) as caught:
            Authority.open(path)
        message = str(caught.exception)
        self.assertIn("does not migrate", message)
        self.assertIn("remove it and initialize a fresh one", message)
        self.assertIn("separate product Work", message)

    def test_the_refusal_changes_not_one_byte(self):
        path = self.schema_one()
        with open(path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(Refusal):
            Authority.open(path)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before,
                             "the refusal modified the older store")
        # And no journal or write-ahead file was created beside it, which is
        # the half a byte comparison of the main file cannot see.
        self.assertFalse(os.path.exists(path + "-wal"))
        self.assertFalse(os.path.exists(path + "-journal"))

    def test_no_part_of_the_new_schema_is_applied_to_it(self):
        """A partial upgrade is the outcome the whole non-adopting design
        exists to prevent, and a refusal that grew three tables first would be
        exactly that."""
        path = self.schema_one()
        with self.assertRaises(Refusal):
            Authority.open(path)
        connection = sqlite3.connect(path)
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        connection.close()
        self.assertEqual(tables, {"meta", "work"})

    def test_its_rows_are_not_read_or_reinterpreted(self):
        """The refusal is decided from the META marker alone.

        Proved by making the rest of the file unreadable as SQL: if the open
        path touched anything but `meta`, this would fault rather than refuse.
        """
        path = self.schema_one()
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("DROP TABLE work")
        connection.execute("CREATE TABLE work (surprise TEXT)")
        connection.close()
        with self.assertRaises(Refusal) as caught:
            Authority.open(path)
        self.assertIn("does not migrate", str(caught.exception))

    def test_a_fresh_store_beside_it_is_the_supported_path(self):
        """The operator-directed remedy, run.

        The older file is left exactly where it was: the ruling permits this
        build to refuse a store it cannot read, and not to delete somebody's
        database because it decided the contents were expendable.
        """
        old = self.schema_one()
        fresh = os.path.join(self.root, "fresh.sqlite3")
        with Authority.create(fresh, authority_uuid=UUID) as face:
            self.assertEqual(face.authority_uuid, UUID)
            self.assertEqual(face.policy_generation(), 1)
        self.assertTrue(os.path.exists(old))

    def test_a_newer_store_is_refused_the_same_way(self):
        path = os.path.join(self.root, "newer.sqlite3")
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, "
                           "value TEXT NOT NULL)")
        for key, value in ((META_STORE_KIND, STORE_KIND),
                           (META_SCHEMA_VERSION, str(SCHEMA_VERSION + 1)),
                           (META_AUTHORITY_UUID, UUID)):
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (key, value))
        connection.close()
        with self.assertRaises(Refusal) as caught:
            Authority.open(path)
        self.assertIn("in either direction", str(caught.exception))

    def test_reopening_a_store_does_not_rewind_its_configuration_generation(
            self):
        """The generation is not seeded at open.

        A seed that ran on every open would rewind a reconfigured deployment to
        1, and every decision already recorded would name a configuration later
        than the store claims to be at.
        """
        path = os.path.join(self.root, "kept.sqlite3")
        with Authority.create(path, authority_uuid=UUID) as face:
            face.grant_capability(CLAUDE, "verify")
            face.grant_capability(GEMINI, "review")
            reached = face.policy_generation()
        self.assertGreater(reached, 1)
        with Authority.open(path) as face:
            self.assertEqual(face.policy_generation(), reached)


if __name__ == "__main__":
    unittest.main()


class EveryCapabilityDoorDecidesInTheTargetsScope(SeamCase):
    """W16821 review [P0], kept.

    `_require_capability` defaulted its scope to the deployment's, so every
    receipt and every close resolved in `scope:deployment` whatever scope its
    target belonged to.  An actor granted the capability only in the target's
    own scope was refused; an actor granted it deployment-wide succeeded, and
    the act then RECORDED `scope:deployment` as the scope it had been
    authorized in -- a false provenance, which is worse than the refusal.

    Every door is exercised both ways, because a fix applied at one door is a
    fix at one door.
    """

    def platform_proposal(self):
        self.work(WORK, handlers=(CLAUDE,), scope=OTHER_SCOPE)
        return self.proposed()

    def doors(self):
        """Each capability-bearing door, as a callable that USES it."""
        return [
            ("verify", lambda actor: self.core.verify(
                proposal_id="p-1", verification_id=f"v-{uuid4()}",
                actor=actor, observation="passed",
                operation_id=self.op())),
            ("review", lambda actor: self.core.review(
                proposal_id="p-1", review_id=f"r-{uuid4()}", actor=actor,
                disposition="accepted", operation_id=self.op())),
            ("approve", lambda actor: self.core.approve(
                proposal_id="p-1", approval_id=f"a-{uuid4()}", actor=actor,
                disposition="approved", operation_id=self.op(),
                policy_generation=1)),
        ]

    def test_a_grant_in_the_targets_scope_authorizes_each_door(self):
        """IN ORDER, because the doors have an order.

        Review requires a passed verification and approval requires an
        accepted review -- ORDINARY refusals raised after the capability
        check.  A positive case that opened each door alone would be refused
        by the sequence rather than authorized by the grant, which is a
        different fact.
        """
        self.platform_proposal()
        for capability, call in self.doors():
            with self.subTest(capability=capability):
                self.authority.grant_capability(GEMINI, capability,
                                                scope=OTHER_SCOPE)
                call(GEMINI)
        for kind in ("verification", "review", "approval"):
            self.assertIsNotNone(self.authority.receipt("p-1", kind), kind)

    def test_a_deployment_grant_does_not_authorize_a_scoped_target(self):
        """And each is refused BY THE CAPABILITY DOOR, not by the sequence.

        `review` and `approve` also have ordering preconditions here, and a
        case that accepted any refusal would pass on those without the scope
        rule doing anything.  The message is pinned to the capability, which is
        also what shows the door runs before the ordering checks.
        """
        for capability, call in self.doors():
            with self.subTest(capability=capability):
                self.setUp()
                self.platform_proposal()
                self.authority.grant_capability(GEMINI, capability)
                with self.assertRaises(Refusal) as caught:
                    call(GEMINI)
                self.assertIn("does not hold", str(caught.exception))
                self.assertIn(capability, str(caught.exception))

    def test_each_receipt_records_the_targets_scope_and_not_the_deployments(
            self):
        self.platform_proposal()
        for capability, call in self.doors():
            self.authority.grant_capability(GEMINI, capability,
                                            scope=OTHER_SCOPE)
            call(GEMINI)
        for kind in ("verification", "review", "approval"):
            with self.subTest(kind=kind):
                receipt = self.authority.receipt("p-1", kind)
                self.assertEqual(receipt["decision"]["effective_scope"],
                                 OTHER_SCOPE, receipt)

    def test_close_decides_in_the_works_own_scope(self):
        self.work(WORK, handlers=(CLAUDE,), scope=OTHER_SCOPE)
        self.authority.grant_capability(GEMINI, "close")
        with self.assertRaises(Refusal) as caught:
            self.core.close(WORK, operation_id=self.op(),
                            outcome="satisfying", rationale="done",
                            actor=GEMINI)
        self.assertIn("does not hold the close capability",
                      str(caught.exception))
        self.assertEqual(self.authority.project_work(WORK)["status"], "open")

        self.authority.grant_capability(GEMINI, "close", scope=OTHER_SCOPE)
        self.core.close(WORK, operation_id=self.op(), outcome="satisfying",
                        rationale="done", actor=GEMINI)
        self.assertEqual(self.authority.project_work(WORK)["status"], "closed")

    def test_integration_decides_in_the_works_own_scope(self):
        self.platform_proposal()
        for capability, call in self.doors():
            self.authority.grant_capability(GEMINI, capability,
                                            scope=OTHER_SCOPE)
            call(GEMINI)
        self.authority.grant_capability(GEMINI, "integrate")
        with self.assertRaises(Refusal) as caught:
            self.core.integrate(proposal_id="p-1", integration_id="i-1",
                                actor=GEMINI, operation_id=self.op())
        self.assertIn("does not hold the integrate capability",
                      str(caught.exception))
        self.authority.grant_capability(GEMINI, "integrate",
                                        scope=OTHER_SCOPE)
        self.core.integrate(proposal_id="p-1", integration_id="i-2",
                            actor=GEMINI, operation_id=self.op())
        self.assertEqual(
            self.authority.receipt("p-1", "integration")["decision"]
            ["effective_scope"], OTHER_SCOPE)

    def test_every_capability_door_names_the_scope_it_decides_in(self):
        """THE GUARD, over this module's own source.

        A default scope is what caused the defect, and a door added later could
        reintroduce it by simply not passing one -- which no behavioural case
        would notice until somebody wrote a cross-scope case for that
        particular door.  So every call site is required to name a scope,
        checked lexically.
        """
        import ast

        import baton_v12.authority.core as module

        core = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(core)
        calls = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and getattr(node.func, "attr", "") == "_require_capability"]
        self.assertTrue(calls, "the guard found no call sites to hold")
        for node in calls:
            with self.subTest(line=node.lineno):
                names = {keyword.arg for keyword in node.keywords}
                self.assertIn("scope", names,
                              f"core.py:{node.lineno} authorizes without "
                              f"naming the scope it decides in")


class TheDecisionIsRetainedForEveryAuthorizedAct(SeamCase):
    """W16821 review [P0], kept."""

    def test_an_unclaimed_close_retains_and_projects_its_decision(self):
        """The act that used to persist nothing at all.

        A Work closed without ever being claimed writes no assignment event, so
        the first cut's four columns had nowhere to live and the close left
        behind no statement of who was permitted to perform it.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.authority.grant_capability(GEMINI, "close")
        generation = self.authority.policy_generation()
        answer = self.core.close(WORK, operation_id=self.op(),
                                 outcome="satisfying", rationale="done",
                                 actor=GEMINI)
        expected = {"endpoint": GEMINI,
                    "principal": principal_for_endpoint(GEMINI),
                    "effective_scope": DEPLOYMENT_SCOPE, "role": "close",
                    "grant": DIRECT, "policy_generation": generation}
        self.assertEqual(answer["decision"], expected)
        self.assertEqual(
            self.authority.project_work(WORK)["close_decision"], expected)
        self.assertEqual(self.authority.decision_of("close", WORK), expected)

    def test_an_open_work_has_no_close_decision(self):
        """The control: `close_decision` is a fact, not a shape that is always
        filled."""
        self.work(WORK, handlers=(CLAUDE,))
        self.assertIsNone(
            self.authority.project_work(WORK)["close_decision"])

    def test_a_durably_refused_integration_attempt_carries_its_decision(self):
        """The one act in this door that survives its own refusal.

        It journals an attributable actor and its operation identity COMMITS,
        so an attempt with no decision is a durable record of somebody being
        allowed to do something with nothing saying what allowed them.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.proposed()
        for capability, disposition, identity in (
                ("verify", "passed", "v-1"), ("review", "accepted", "r-1"),
                ("approve", "approved", "a-1")):
            self.authority.grant_capability(CLAUDE, capability)
        self.core.verify(proposal_id="p-1", verification_id="v-1",
                         actor=CLAUDE, observation="passed",
                         operation_id=self.op())
        self.core.review(proposal_id="p-1", review_id="r-1", actor=CLAUDE,
                         disposition="accepted", operation_id=self.op())
        self.core.approve(proposal_id="p-1", approval_id="a-1", actor=CLAUDE,
                          disposition="approved", operation_id=self.op(),
                          policy_generation=1)
        self.authority.grant_capability(CLAUDE, "integrate")
        # THE CANONICAL TARGET MOVES under the proposal, which is the durable
        # refusal this case exists for.
        self.authority.set_policy("canonical_target", "base-moved")
        with self.assertRaises(Refusal):
            self.core.integrate(proposal_id="p-1", integration_id="i-1",
                                actor=CLAUDE, operation_id=self.op())
        attempts = self.authority.integration_attempts("p-1")
        self.assertEqual(len(attempts), 1, attempts)
        self.assertEqual(attempts[0]["actor"], CLAUDE)
        self.assertEqual(attempts[0]["reason"], "stale-target")
        self.assertEqual(attempts[0]["decision"]["principal"],
                         principal_for_endpoint(CLAUDE))
        self.assertEqual(attempts[0]["decision"]["role"], "integrate")

    def test_an_assignment_derived_act_exposes_the_claim_it_ran_under(self):
        """Activity, contract events and proposals are carried out UNDER an
        assignment somebody already authorized.

        They join to the claim's decision through the full exact assignment
        identity rather than copying it, and the projection exposes the same
        complete typed decision.
        """
        self.work(WORK, handlers=(CLAUDE,), scope=OTHER_SCOPE)
        self.proposed()
        assignment = self.authority.assignment_of(WORK)
        self.core.activity(assignment, key="did-a-thing")
        claim = self.claim_event(WORK)["decision"]
        self.assertEqual(self.authority.activities(WORK)[0]["decision"], claim)
        self.assertEqual(self.authority.proposal("p-1")["decision"], claim)
        self.assertEqual(claim["effective_scope"], OTHER_SCOPE)

    def test_history_survives_release_reconfiguration_and_close(self):
        """AND IS NOT RE-DERIVED.

        After the assignment is released, the endpoint is rebound to another
        principal and the configuration generation has moved on, the retained
        decision must still say what the act was performed under -- not what it
        would be authorized as now.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.proposed()
        before = self.claim_event(WORK)["decision"]
        self.assertEqual(before["principal"], principal_for_endpoint(CLAUDE))

        self.core.end(self.authority.assignment_of(WORK),
                      operation_id=self.op())
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.authority.grant_capability(GEMINI, "close")
        self.core.close(WORK, operation_id=self.op(), outcome="satisfying",
                        rationale="done", actor=GEMINI)

        # The mapping and the generation have BOTH moved.
        self.assertEqual(self.authority.principal_of(CLAUDE), ONE_PERSON)
        self.assertGreater(self.authority.policy_generation(),
                           before["policy_generation"])
        # And the history is unchanged, through every projection that carries
        # it, including one restart.
        self.assertEqual(self.claim_event(WORK)["decision"], before)
        self.assertEqual(self.authority.proposal("p-1")["decision"], before)
        self.authority.dispose()
        self.authority = Authority.open(self.path)
        self.core = self.authority._core
        self.assertEqual(self.claim_event(WORK)["decision"], before)

    def test_a_decision_is_never_rewritten(self):
        self.work(WORK, handlers=(CLAUDE,))
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        event = self.claim_event(WORK)
        with self.assertRaises(Refusal) as caught:
            self.core._record_decision(
                "claim", str(event["seq"]),
                self.core.authorize(CLAUDE, route=ROUTE))
        self.assertIn("never rewritten", str(caught.exception))


class TheGrantProjectionCarriesScopeAndProvenance(SeamCase):
    """W16821 review [P1], kept."""

    def test_two_scoped_grants_are_two_distinguishable_entries(self):
        self.authority.grant_capability(CLAUDE, "verify")
        self.authority.grant_capability(CLAUDE, "verify", scope=OTHER_SCOPE)
        self.assertEqual(self.authority.grants_of(CLAUDE), [
            {"capability": "verify", "scope": DEPLOYMENT_SCOPE,
             "provenance": DIRECT},
            {"capability": "verify", "scope": OTHER_SCOPE,
             "provenance": DIRECT}])

    def test_the_compatibility_projection_is_distinct_names_and_says_so(self):
        """`['verify', 'verify']` was not information; it was the scope column
        missing."""
        self.authority.grant_capability(CLAUDE, "verify")
        self.authority.grant_capability(CLAUDE, "verify", scope=OTHER_SCOPE)
        self.authority.grant_capability(CLAUDE, "close")
        self.assertEqual(self.authority.capabilities_of(CLAUDE),
                         ["close", "verify"])

    def test_a_name_held_in_some_scope_authorizes_nothing_by_itself(self):
        """The reason the flattened projection is a helper and not the answer:
        it is true and it does not decide anything."""
        self.authority.grant_capability(CLAUDE, "verify", scope=OTHER_SCOPE)
        self.assertIn("verify", self.authority.capabilities_of(CLAUDE))
        self.assertIsNone(self.core.authorize(CLAUDE, capability="verify"))
        self.assertIsNotNone(
            self.core.authorize(CLAUDE, capability="verify",
                                scope=OTHER_SCOPE))


class AV11ReclaimDoesNotRewriteEarlierHistory(SeamCase):
    """W16821 re-review [P0], kept.

    A v11 assignment mints NO generation, so a release and a reclaim through
    the same endpoint are two distinct claim acts with identical
    `(work_id, participant, generation)`.  The first cut searched for the claim
    at READ time over exactly that tuple, newest first -- so the second claim
    became the apparent authorization of the first act's history, and the first
    activity's principal and policy generation changed without the act or its
    decision row being touched.

    THE V12 CASE PASSED THROUGHOUT, because generations distinguish v12 claims.
    That is why this one is separate and kept: a correction measured only on
    the contract that cannot express the defect measures nothing.
    """

    def acted(self, key):
        self.core.activity(self.authority.assignment_of(WORK), key=key)

    def test_two_v11_claims_keep_two_distinct_histories(self):
        self.work(WORK, handlers=(CLAUDE,), contract=V11)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.acted("first-act")
        first = self.authority.activities(WORK)[0]["decision"]
        self.assertEqual(first["principal"], principal_for_endpoint(CLAUDE))

        # RELEASE, REBIND, RECLAIM -- the same endpoint, a different principal.
        self.core.end(self.authority.assignment_of(WORK),
                      operation_id=self.op())
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.acted("second-act")

        claims = [event["decision"] for event in
                  self.authority.assignment_events(WORK)
                  if event["cause"] == "claimed"]
        self.assertEqual([one["principal"] for one in claims],
                         [principal_for_endpoint(CLAUDE), ONE_PERSON])
        # THE ASSIGNMENT IDENTITIES ARE EQUAL, which is what made the old join
        # ambiguous; naming that here is what stops this case from passing
        # because the two acts happened to differ some other way.
        events = [event["assignment_ref"] for event in
                  self.authority.assignment_events(WORK)
                  if event["cause"] == "claimed"]
        self.assertEqual(events[0], events[1])

        activities = self.authority.activities(WORK)
        self.assertEqual([one["action_key"] for one in activities],
                         ["first-act", "second-act"])
        self.assertEqual(activities[0]["decision"], first)
        self.assertEqual(activities[0]["decision"]["principal"],
                         principal_for_endpoint(CLAUDE))
        self.assertEqual(activities[1]["decision"]["principal"], ONE_PERSON)

    def test_the_two_histories_survive_a_reopen(self):
        """Read back from a fresh store handle, so the answer is the rows and
        not anything this process was holding."""
        self.work(WORK, handlers=(CLAUDE,), contract=V11)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.acted("first-act")
        self.core.end(self.authority.assignment_of(WORK),
                      operation_id=self.op())
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.acted("second-act")
        before = [one["decision"] for one in self.authority.activities(WORK)]

        self.authority.dispose()
        self.authority = Authority.open(self.path)
        self.core = self.authority._core
        self.assertEqual(
            [one["decision"] for one in self.authority.activities(WORK)],
            before)
        self.assertNotEqual(before[0]["principal"], before[1]["principal"])

    def test_publication_is_v12_only_so_activity_is_the_v11_derived_act(self):
        """Measured rather than assumed, because it decides what this class
        can cover.

        A v11 assignment cannot publish, so the assignment-derived act that
        CAN exist under the contract with no generation is the activity -- and
        that is the one the cases above exercise.  The proposal's own exact
        reference is covered under v12 below, where a proposal can exist.
        """
        self.work(WORK, handlers=(CLAUDE,), contract=V11)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        with self.assertRaises(Refusal) as caught:
            self.core.publish(
                self.authority.assignment_of(WORK), proposal_id="p-1",
                result_id="r-1", result_digest="d" * 8,
                candidate_digest="c" * 8, input_digest="i" * 8,
                policy_digest="y" * 8, operation_id=self.op())
        self.assertIn("v12 assignment contract", str(caught.exception))

    def test_a_v12_proposal_names_the_claim_it_was_published_under(self):
        """The same exactness for the proposal, where one can exist.

        v12 reclaims mint a new generation, so the old tuple join happened to
        answer correctly here -- which is exactly why the v11 case above is the
        one that measures the defect, and why this one measures the reference
        rather than the outcome.
        """
        self.work(WORK, handlers=(CLAUDE,))
        self.proposed()
        published = self.authority.proposal("p-1")["decision"]
        self.core.end(self.authority.assignment_of(WORK),
                      operation_id=self.op())
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(self.authority.proposal("p-1")["decision"], published)
        self.assertEqual(published["principal"],
                         principal_for_endpoint(CLAUDE))

    def test_an_act_that_cannot_name_its_claim_is_refused(self):
        """The reference is REQUIRED, not best-effort.

        An assignment-derived act whose claim this authority never journalled
        is not attributable, and writing it with a null reference would be the
        ambiguity coming back as an absence.
        """
        self.work(WORK, handlers=(CLAUDE,), contract=V11)
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        assignment = self.authority.assignment_of(WORK)
        self.core._store.run("DELETE FROM assignment_event WHERE "
                             "cause = 'claimed'")
        with self.assertRaises(Refusal) as caught:
            self.core.activity(assignment, key="orphan")
        self.assertIn("never journalled", str(caught.exception))
