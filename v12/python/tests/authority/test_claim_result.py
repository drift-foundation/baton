"""W16823 — the closed claim result, and why the bare assignment was not one.

W16793 found the Worker Manager treating one endpoint address as every
identity below the authority.  W16821 corrected the AUTHORITY: it separated the
principal from the endpoint, gave Work an authority-owned effective scope, and
retained an authorization decision beside each act it authorized.  What it did
not do -- because consuming it was separate Work -- is let the claimant SEE the
decision its own claim was taken under.

`claim` answered `{work_ref, participant, generation}`.  The decision was
reachable only by picking a claim event out of `assignment_events` and matching
on that four-part identity, and W16821's own re-review had already refused that
join inside the authority as "not an exact identity": a v11 assignment mints no
generation, so a release and a reclaim through one endpoint are two acts whose
identities are equal.  A consumer matching on the answer cannot say which of
its own claims it just made, and this module measures that rather than asserts
it.

Approver rulings M34905 and M35002 settle the shape and the version:

  * the answer is `{assignment, claim_event, decision}` -- the UNCHANGED
    four-part fence, the exact immutable act identity, and W16821's decision
    vocabulary byte for byte;
  * the operation journal retains the whole document, so an exact retry, a
    restart and a lost-result settlement all reproduce the ORIGINAL bytes
    rather than recomposing them against today's configuration;
  * authority schema 4 is the clean initialization boundary, because a
    schema-3 journal can hold the old bare answer.

EVERY CASE DRIVES THE PRODUCTION SEAM.  Nothing here rebuilds the decision or
compares against a value this module computed: the result comes out of
`Core.claim`, the retained decision out of `Core.decision_of`, and the version
refusal out of `Authority.open`.
"""

import os
import sqlite3
import tempfile
import unittest

from baton_v12.authority import Authority, Refusal, V11, V12
from baton_v12.authority.identity import claim_signature
from baton_v12.authority.principals import (DEPLOYMENT_SCOPE, DIRECT,
                                            principal_for_endpoint)
from baton_v12.authority.schema import (META_AUTHORITY_UUID,
                                        META_SCHEMA_VERSION, META_STORE_KIND,
                                        SCHEMA_VERSION, STORE_KIND)

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
CLAUDE_ALIAS = "review.claude"
ROUTE = "impl"
OTHER_ROUTE = "rview"
NOW = "2026-08-24T04:00:00.000Z"
ONE_PERSON = "principal:sl"
WORK_SCOPE = "scope:platform"

RESULT = ("assignment", "claim_event", "decision")
DECISION = ("endpoint", "principal", "effective_scope", "role", "grant",
            "policy_generation")


class ClaimResultCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w16823-")
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


class TheAnswerIsThreeFactsAndNotOne(ClaimResultCase):
    """The positive, and every member measured against its own source."""

    def test_the_result_carries_the_fence_the_act_and_the_decision(self):
        self.work(scope=WORK_SCOPE)
        result = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(sorted(result), sorted(RESULT))
        # THE FENCE IS UNCHANGED. §4's four parts, exactly as `assignment_of`
        # projects them -- this Work weakens nothing about the fence and the
        # comparison is against the authority's own live projection rather
        # than against a literal.
        self.assertEqual(result["assignment"],
                         self.authority.assignment_of(WORK))
        # THE ACT IDENTITY is the claim event this claim wrote, and the proof
        # is that the retained decision is reachable BY it.
        self.assertEqual(sorted(result["decision"]), sorted(DECISION))
        self.assertEqual(
            self.authority.decision_of("claim", str(result["claim_event"])),
            result["decision"])
        # AND THE DECISION SAYS THE TWO THINGS THAT WERE CONFLATED. The
        # endpoint is the address; the principal is who acted; the scope is the
        # WORK's, not the deployment's.
        self.assertEqual(result["decision"]["endpoint"], CLAUDE)
        self.assertEqual(result["decision"]["principal"],
                         principal_for_endpoint(CLAUDE))
        self.assertEqual(result["decision"]["effective_scope"], WORK_SCOPE)
        self.assertEqual(result["decision"]["role"], ROUTE)
        self.assertEqual(result["decision"]["grant"], DIRECT)
        self.assertEqual(result["decision"]["policy_generation"],
                         self.authority.policy_generation())

    def test_the_claim_event_is_the_event_this_claim_wrote(self):
        """NAMED, rather than searched for.

        The event the result names is the one claim event in the history, and
        the assignment reference on it is this claim's own.
        """
        self.work()
        result = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        claims = [event for event in self.authority.assignment_events(WORK)
                  if event["cause"] == "claimed"]
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["seq"], result["claim_event"])
        self.assertEqual(claims[0]["assignment_ref"], result["assignment"])

    def test_the_deployment_scope_is_the_default_and_is_said_so(self):
        self.work()
        result = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(result["decision"]["effective_scope"],
                         DEPLOYMENT_SCOPE)


class TheEventIsWhatTheFenceCannotBe(ClaimResultCase):
    """The measurement the whole member exists for.

    W16821's re-review refused a `(work, participant, generation)` join inside
    the authority.  This proves the same thing on the answer a consumer holds,
    because that is where the manager would otherwise have to make it.
    """

    def test_two_claims_through_one_v11_endpoint_have_equal_fences(self):
        self.work(contract=V11)
        first = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.core.end(first["assignment"], operation_id=self.op())
        second = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        # THE FENCES ARE EQUAL, which is not a defect -- a v11 assignment
        # mints no generation and §4 says so.
        self.assertEqual(first["assignment"], second["assignment"])
        self.assertIsNone(first["assignment"]["generation"])
        # AND THE ACTS ARE NOT, which is the whole point of the member.
        self.assertNotEqual(first["claim_event"], second["claim_event"])
        # Each act keeps its OWN decision, so a consumer holding the event can
        # name which claim it made; one holding the fence alone cannot.
        self.assertEqual(
            self.authority.decision_of("claim", str(first["claim_event"])),
            first["decision"])
        self.assertEqual(
            self.authority.decision_of("claim", str(second["claim_event"])),
            second["decision"])

    def test_a_reclaim_after_a_policy_change_keeps_the_earlier_decision(self):
        """A decision is what was answered AT THE ACT.

        The first claim is taken under one policy generation.  A configuration
        act bumps it, the Work is reclaimed, and the first act's decision is
        unchanged -- read back through the event the first result named.
        """
        self.work(contract=V11)
        first = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.core.end(first["assignment"], operation_id=self.op())
        self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON)
        second = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertGreater(second["decision"]["policy_generation"],
                           first["decision"]["policy_generation"])
        self.assertEqual(
            self.authority.decision_of("claim", str(first["claim_event"])),
            first["decision"])


class TwoAddressesOnePrincipal(ClaimResultCase):
    """The acceptance's multi-endpoint positive, on the ANSWER.

    W16821 proved the shared claim slot.  What this adds is that the two
    endpoints' claims REPORT one principal, which is what a consumer needs to
    avoid deriving two identities from two spellings.
    """

    def test_two_endpoints_report_one_principal_and_two_endpoints(self):
        self.work(WORK, handlers=(CLAUDE,))
        self.work(OTHER, route=OTHER_ROUTE, handlers=(CLAUDE_ALIAS,))
        self.authority.bind_endpoint(CLAUDE, ONE_PERSON)
        self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON)
        mine = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        # The slot is principal-keyed, so the second claim needs the first to
        # end -- which is W16821's acceptance and is unchanged here.
        self.core.end(mine["assignment"], operation_id=self.op())
        theirs = self.core.claim(OTHER, CLAUDE_ALIAS, operation_id=self.op())
        self.assertNotEqual(mine["assignment"]["participant"],
                            theirs["assignment"]["participant"])
        self.assertNotEqual(mine["decision"]["endpoint"],
                            theirs["decision"]["endpoint"])
        self.assertEqual(mine["decision"]["principal"], ONE_PERSON)
        self.assertEqual(theirs["decision"]["principal"], ONE_PERSON)


class TheWholeResultIsWhatReplayReproduces(ClaimResultCase):
    """The journal retains the document, not a member of it."""

    def test_an_exact_retry_returns_the_original_bytes(self):
        self.work(scope=WORK_SCOPE)
        first = self.core.claim(WORK, CLAUDE, operation_id="claim-1")
        second = self.core.claim(WORK, CLAUDE, operation_id="claim-1")
        self.assertEqual(second, first)
        record = self.core.operation_record("claim-1")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["result"], first)

    def test_a_restart_replays_the_decision_and_does_not_recompose_it(self):
        """THE POINT OF RETAINING IT RATHER THAN REBUILDING IT.

        The authority is closed and reopened, and the configuration MOVES in
        between.  A replay that recomposed the decision would answer what the
        act would be authorized under now; the journal answers what it was
        performed under.
        """
        self.work()
        first = self.core.claim(WORK, CLAUDE, operation_id="claim-1")
        self.authority.dispose()
        self.authority = Authority.open(self.path, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self.authority.bind_endpoint(CLAUDE_ALIAS, ONE_PERSON)
        replayed = self.core.claim(WORK, CLAUDE, operation_id="claim-1")
        self.assertEqual(replayed, first)
        self.assertLess(replayed["decision"]["policy_generation"],
                        self.authority.policy_generation())

    def test_a_lost_result_settles_with_the_whole_committed_document(self):
        self.work()
        result = self.core.claim(WORK, CLAUDE, operation_id="claim-1")
        answer = self.core.settle_operation(
            "claim-1", signature=claim_signature(WORK, CLAUDE),
            reason="the manager lost this claim's result",
            disposition="settlement-expired", may_retire=True)
        self.assertEqual(answer["kind"], "committed")
        self.assertEqual(answer["result"], result)


class SchemaFourIsACleanInitializationBoundary(unittest.TestCase):
    """Approver ruling M35002, as a measurement.

    NO TABLE CHANGED, which is exactly why the bump has to be measured rather
    than inferred from a diff.  A schema-3 operation journal can hold the old
    bare assignment as a committed claim result, and this build would hand it
    to a consumer reading it as the closed document.
    """

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w16823-schema-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name

    def test_the_version_is_four(self):
        self.assertEqual(SCHEMA_VERSION, 4)

    def previous(self, name="old.sqlite3"):
        """A store recording THIS product at the PREVIOUS schema version.

        Built by hand, because this build cannot create one: there is no
        downgrade path, and adding one to make a case convenient would be
        adding the migration the ruling excludes.
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
        connection.close()
        return path

    def test_the_older_store_is_refused_and_the_operator_is_told_what_to_do(
            self):
        path = self.previous()
        with self.assertRaises(Refusal) as caught:
            Authority.open(path)
        message = str(caught.exception)
        self.assertIn("does not migrate", message)
        self.assertIn("remove it and initialize a fresh one", message)

    def test_the_refusal_changes_not_one_byte(self):
        path = self.previous()
        with open(path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(Refusal):
            Authority.open(path)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before)


if __name__ == "__main__":
    unittest.main()
