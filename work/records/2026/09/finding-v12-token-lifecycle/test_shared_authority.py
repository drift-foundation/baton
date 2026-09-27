"""W275774 — SHARED durable authority, and a storage root that says whose it is.

SUPERSEDED INTERPRETATION, RECORDED HERE RATHER THAN REMOVED. Owner 278980/279004 and
DESIGN HOST-8 as amended at 279031 remove the deployment this file was written for: two
active Host managers over one workspace/DB is MISCONFIGURATION and must refuse startup,
so the "two managers, one journal" reading below is obsolete. Review 21:08:45Z is also
right that these are SEQUENTIAL same-store connection tests and not startup-process
exclusion.

WHAT THEY STILL MEASURE, and why they stay: that the token journal and `BEGIN IMMEDIATE`
exclude a held resource across independent connections and transactions, that unrelated
progress is unaffected, and that a return on one connection is visible to the other.
That is WITHIN-INSTANCE journal safety and it is true regardless of how many managers a
deployment is allowed to run.

AND THE MARKER'S DISPOSITION. `.baton-workspace-authority` refuses a DIFFERENT control
store over one workspace root at configuration time and PERMITS same-store callers, so
it is not the HOST-8 guard and is not offered as one -- `test_instance_guard.py` is that.
The marker is kept because the configuration it refuses is still misconfiguration under
HOST-8, and it refuses it earlier and with a clearer account than a lock can.

Review 20:57:02Z stated the gap exactly: "Device/inode in independent stores is not
shared authority; per-store siblings do not prove cross-manager exclusion." Every
earlier proof in this dossier ran sequential calls over ONE `ControlStore` handle, so
none of it established either half of this:

  1. THE EXCLUSION ACROSS CONNECTIONS. Two `ControlStore` handles on one database file
     are two connections with two transactions, and the exclusion has to be the journal
     and `BEGIN IMMEDIATE` rather than one caller's memory of what it read. Driven here
     through the real `attempts.request_runtime_start` on the SECOND connection, over
     the object the FIRST connection's attempt holds.
  2. THE DEPLOYMENT THAT CANNOT SHARE. Two managers with one storage root and TWO
     control stores each hold their own token journal, so the resource they are both
     writing to is excluded by nobody. `workspaces.configure_workspace_storage` now
     binds the root to the control store whose journal governs it and REFUSES a second
     authority -- so managers over one root share one store, which is what makes the
     exclusion real, or they do not share the root.

SINGLE HOST, which is the selected scope: the marker names an absolute path on this
host and is not a distributed lease. Real disposable stores and real allocations; no
live engine, no provider, no container created or signalled.
"""
import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, request_runtime_start
from baton_v12.worker_manager import attempts, tokens, workspaces

import test_connected_lifecycle as connected


class TheAuthORITYIsSharedOrTheRootIsNot(connected.TheGovernedStartAndItsOwnEnding):
    """One storage root, and the two ways a second manager can meet it."""

    def carried(self, source, target):
        """The object moved from one assignment's position to the next."""
        homes = [os.path.dirname(self.workspace_of(one))
                 for one in (source, target)]
        modes = [os.stat(one).st_mode & 0o7777 for one in homes]
        for one in homes:
            os.chmod(one, 0o700)
        place = self.workspace_of(target)
        try:
            os.rename(place, place + ".own")
            os.rename(self.workspace_of(source), place)
        finally:
            for one, mode in zip(homes, modes):
                os.chmod(one, mode)

    def beside_connection(self, incarnation="manager-2"):
        """A SECOND connection to this manager's own control store.

        Not a second store: that is the case below, and it is the one that refuses.
        This is the shape a deployment that shares its authority actually has --
        two managers, one journal -- and it is what the exclusion has to hold across.
        """
        second = ControlStore.open(self.path, incarnation=incarnation,
                                   clock=self.store._clock)
        self.addCleanup(second.close)
        return second

    # -- 1. the exclusion, across two connections ------------------------------

    def test_a_SECOND_CONNECTION_is_excluded_from_the_held_object(self):
        """THE CROSS-MANAGER CASE, with two real rows and two real connections.

        The first attempt's governed start holds the object on connection one. The
        second attempt -- a real authorized row over a different Work, so the runtime
        LANE cannot be what refuses -- takes its governed start on connection TWO, and
        is refused by the token. Nothing crossed to the engine on that connection.
        """
        self.attempt()
        domain = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(connected.BESIDE, offer_id="offer-2",
                                 work_id=connected.OTHER_JOB)
        self.carried_over(connected.BESIDE)
        self.pin(connected.BESIDE, inputs)
        second = self.beside_connection()
        self.assertNotEqual(id(second._connection), id(self.store._connection),
                            "the case is worthless if both calls share a connection")
        beside = connected.Counting("runtime-2")
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(
                second, beside, attempt_id=connected.BESIDE, inputs=inputs,
                govern=tokens.workspace_governance(control=second))
        self.assertIn("is owned by token generation 1", caught.exception.message)
        self.assertEqual(beside.started, [],
                         "the second manager never reached the engine")
        # AND THE FIRST CONNECTION STILL HOLDS IT, unchanged by the attempt.
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["execution"] for one in held],
                         [connected.ATTEMPT])
        self.assertEqual(tokens.outstanding(second, domain), held,
                         "both connections read one journal")

    def test_a_SECOND_CONNECTION_may_proceed_over_its_own_object(self):
        """Unrelated progress, across connections: an exclusion that stopped this
        would be a global lock wearing a resource token's name."""
        self.attempt()
        mine = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(connected.BESIDE, offer_id="offer-2",
                                 work_id=connected.OTHER_JOB)
        theirs = tokens.domain_of("workspace",
                                  self.pin(connected.BESIDE, inputs))
        self.assertNotEqual(mine, theirs)
        second = self.beside_connection()
        beside = connected.Counting("runtime-2")
        request_runtime_start(second, beside, attempt_id=connected.BESIDE,
                              inputs=inputs,
                              govern=tokens.workspace_governance(control=second))
        self.assertEqual(len(beside.admissions), 1)
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(second, theirs)], [1])
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(self.store, mine)], [1])

    def test_the_RETURN_on_one_connection_frees_the_other(self):
        """The whole point of sharing one journal: the second manager proceeds the
        moment the first one's ending returns the resource, and not before.

        AND THE LOSER STAYS TERMINAL, which this case had to be rewritten to respect.
        My first version retried the SAME second attempt after the return and was
        refused with "execution is 'destroyed'" -- correctly: a refused reservation is
        recorded as a proved non-launch by this claim's own correction, and review
        19:13:42Z ruled same-attempt automatic retry out of scope. So the manager that
        lost proceeds with a FRESH attempt, which is what a deployment actually does,
        and the loser is asserted still terminal.
        """
        self.retained_ready("discard-after-intake")
        domain = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(connected.BESIDE, offer_id="offer-2",
                                 work_id=connected.OTHER_JOB)
        self.carried_over(connected.BESIDE)
        self.pin(connected.BESIDE, inputs)
        second = self.beside_connection()
        # BEFORE: refused on the second connection, over the held object.
        with self.assertRaises(ContractRefusal):
            request_runtime_start(
                second, connected.Counting("runtime-2"),
                attempt_id=connected.BESIDE, inputs=inputs,
                govern=tokens.workspace_governance(control=second))
        # THE FIRST MANAGER'S OWN ENDING, on connection one.
        self.ended()
        self.ending(tokens.workspace_governance())
        self.assertEqual(tokens.outstanding(second, domain), [],
                         "the return is visible on the other connection")
        # AND A FRESH ATTEMPT ON THE SECOND CONNECTION NOW PROCEEDS.
        fresh = "attempt-fresh"
        others = self.authorized(fresh, offer_id="offer-3",
                                 work_id="43c55d4b-W1441")
        self.carried(connected.BESIDE, fresh)
        self.pin(fresh, others)
        beside = connected.Counting("runtime-3")
        request_runtime_start(second, beside, attempt_id=fresh, inputs=others,
                              govern=tokens.workspace_governance(control=second))
        held = tokens.outstanding(second, domain)
        self.assertEqual([one["generation"] for one in held], [2])
        self.assertEqual(held[0]["execution"], fresh)
        # THE LOSER IS STILL TERMINAL, and that is the ruled behaviour.
        self.assertEqual(self.row_of(connected.BESIDE)["execution_runtime"],
                         "destroyed")

    # -- 2. the deployment that cannot share -----------------------------------

    def test_the_root_NAMES_the_control_store_that_governs_it(self):
        """The marker is written by the deployment's own configuring act."""
        self.assertEqual(
            workspaces.claimed_workspace_authority(self.storage),
            self.store.database,
            "configuring a storage root binds it to this manager's journal")

    def test_a_SECOND_CONTROL_STORE_over_one_root_is_REFUSED(self):
        """THE FAIL-CLOSED DEPLOYMENT, which is the other half of shared authority.

        Two control stores over one storage root hold two token journals, and the
        resource they are both writing to is excluded by neither. So the second
        deployment's own configuring act refuses, naming both stores -- before any
        attempt exists, let alone two runtimes over one workspace.
        """
        beside = os.path.join(os.path.dirname(self.path), "beside.sqlite3")
        other = ControlStore.open(beside, incarnation="manager-other",
                                  clock=self.store._clock)
        self.addCleanup(other.close)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.configure_workspace_storage(other, self.storage)
        self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(caught.exception.code, "denied")
        self.assertIn("share one control store", caught.exception.message)
        # AND THE FIRST CLAIM IS UNTOUCHED.
        self.assertEqual(workspaces.claimed_workspace_authority(self.storage),
                         self.store.database)

    def test_the_SAME_control_store_re_affirming_the_root_is_a_NO_OP(self):
        """A second handle on one store is the sharing shape, not the conflict: it
        matches the claim and commits, which is what lets two managers share."""
        second = self.beside_connection("manager-affirming")
        workspaces.configure_workspace_storage(second, self.storage)
        self.assertEqual(workspaces.claimed_workspace_authority(self.storage),
                         self.store.database)
        self.assertEqual(
            workspaces.configured_workspace_storage(second).place,
            self.storage, "and the frozen answer still mints")

    def test_a_ROOT_CLAIMED_BY_ANOTHER_STORE_fails_closed_on_READ_too(self):
        """A claim that arrives AFTER a manager configured is caught on the read that
        mints the custody root, which is the last moment before an act would use it.

        The marker is rewritten here by hand ON PURPOSE: no production path can bind an
        already-bound root, so the only way to reach this state is the one a foreign
        process would create -- and what is asserted is this manager's refusal to mint a
        storage answer over it, not how the bytes got there.
        """
        import json
        with open(os.path.join(self.storage,
                               workspaces.WORKSPACE_AUTHORITY_MARKER),
                  "wb") as writing:
            writing.write(json.dumps(
                {"schema": workspaces.WORKSPACE_AUTHORITY_SCHEMA,
                 "control_store": "/somewhere/else/control.sqlite3"}).encode())
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.configured_workspace_storage(self.store)
        self.assertEqual(caught.exception.code, "denied")
        self.assertIn("is not the one this manager would acquire from",
                      caught.exception.message)

    def test_an_UNREADABLE_claim_is_not_an_absent_one(self):
        """"I could not tell" must not become "nobody else is here"."""
        with open(os.path.join(self.storage,
                               workspaces.WORKSPACE_AUTHORITY_MARKER),
                  "wb") as writing:
            writing.write(b"not a document")
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.claimed_workspace_authority(self.storage)
        self.assertEqual(caught.exception.category, "integrity")

    def test_the_MARKER_does_not_become_an_assignment_directory(self):
        """It lives in the storage root beside the assignment homes, so the sibling
        rule that decides a governed identity must not see it as one."""
        self.attempt()
        self.assertTrue(os.path.exists(
            os.path.join(self.storage, workspaces.WORKSPACE_AUTHORITY_MARKER)))
        self.assertEqual(
            self.pinned,
            workspaces.governed_resource_identity(self.store,
                                                  connected.ATTEMPT),
            "the marker changes no governed identity")


if __name__ == "__main__":
    unittest.main()
