"""W275617 G1 — the shared resource token, proved on real disposable stores.

THE ONE BOUNDED SELECTOR for this Work. Real `ControlStore` instances in this
fixture's own temporary directories, a controlled engine boundary, no live Docker,
no provider, no deployed store, and no process created or signalled.

Milestone 1's properties only. Generation exclusion beyond gen2, renewal-versus-
expiry arbitration, lost replies, restart reconciliation and engine-failure holds
are later G1 steps and are NOT asserted here -- review 2026-09-26T13:29:00Z is
explicit that the first milestone is bounded and not the acceptance boundary.
"""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import tokens
from baton_v12.worker_manager.store import ControlStore


class SharedResourceToken(unittest.TestCase):

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-tokens-")
        self.addCleanup(root.cleanup)
        self.root = root.name
        self.store = self.opened("control")

    def opened(self, name):
        store = ControlStore.open(
            os.path.join(self.root, f"{name}.sqlite3"),
            incarnation=f"tokens-{name}",
            clock=lambda: self.instant)
        self.addCleanup(store.close)
        return store

    instant = "2026-09-26T13:00:00.000Z"

    # -- the conflict domain is the resource -----------------------------------

    def test_two_attempts_of_one_resource_share_one_conflict_domain(self):
        """THE CORRECTION REVIEW 13:29:00Z REQUIRED, asserted rather than described.

        My dossier proposed a domain "derived from an attempt". That would have given
        the same workspace a different domain per attempt, so two attempts could each
        hold it -- an escape hatch wearing an identity's clothes. The domain names the
        RESOURCE, so both attempts resolve to the same string and the second is
        refused while the first is outstanding.
        """
        domain = tokens.domain_of("workspace", "line-7/workspace")
        self.assertEqual(domain, tokens.domain_of("workspace", "line-7/workspace"))
        first = tokens.acquire(self.store, domain, operation="runtime.start:a",
                               execution="attempt-a", attempt="attempt-a")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.acquire(self.store, domain, operation="runtime.start:b",
                           execution="attempt-b", attempt="attempt-b")
        self.assertIn("is owned by token generation 1", caught.exception.message)
        self.assertIn("attempt-a", caught.exception.message)
        self.assertEqual(first["generation"], 1)
        self.assertEqual(first["attempt"], "attempt-a")

    def test_an_unrelated_resource_proceeds_while_one_is_held(self):
        """NOT ONE GLOBAL LOCK. TOK-1: "Unrelated resources may progress concurrently."""
        held = tokens.domain_of("workspace", "line-7/workspace")
        other = tokens.domain_of("workspace", "line-9/workspace")
        tokens.acquire(self.store, held, operation="runtime.start:a",
                       execution="attempt-a")
        beside = tokens.acquire(self.store, other, operation="runtime.start:c",
                               execution="attempt-c")
        self.assertEqual(beside["generation"], 1)
        self.assertEqual(len(tokens.outstanding(self.store, held)), 1)
        self.assertEqual(len(tokens.outstanding(self.store, other)), 1)

    def test_a_resource_kind_cannot_smuggle_a_separator(self):
        """Two resources must not collide through a composed kind."""
        with self.assertRaises(ContractRefusal):
            tokens.domain_of("workspace:line-7", "workspace")

    # -- reserve before launch, and the effects gate ---------------------------

    def test_effects_are_withheld_until_the_container_is_bound(self):
        """THE CONCRETE GATE, which review 13:29:00Z asked for by name.

        Journalling before the start and binding after the reply is not enough on its
        own: the container may exist in between. So exposing the resource is its own
        positive question, and it answers False until THIS generation has a bound
        container -- which is what stops a late or lost start reply from reaching the
        governed mount.
        """
        domain = tokens.domain_of("workspace", "line-7/workspace")
        token = tokens.acquire(self.store, domain, operation="runtime.start:a",
                               execution="attempt-a", attempt="attempt-a")
        self.assertFalse(tokens.effects_permitted(self.store, token),
                         "no container is bound yet, so nothing may be exposed")
        tokens.journal_launch(self.store, token, "launch:a")
        self.assertFalse(tokens.effects_permitted(self.store, token),
                         "a journalled launch is not a bound execution")
        tokens.bind_container(self.store, token, "container-1", launch="launch:a")
        self.assertTrue(tokens.effects_permitted(self.store, token))
        self.assertEqual(
            tokens.token_of(self.store, domain, 1)["container"], "container-1")

    def test_a_container_from_another_launch_cannot_be_bound(self):
        """The binding is typed to the journalled launch, not to any reply that arrives."""
        domain = tokens.domain_of("workspace", "line-7/workspace")
        token = tokens.acquire(self.store, domain, operation="runtime.start:a",
                               execution="attempt-a")
        tokens.journal_launch(self.store, token, "launch:a")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.bind_container(self.store, token, "container-x",
                                  launch="launch:somebody-else")
        self.assertIn("not the launch this token journalled", caught.exception.message)
        self.assertFalse(tokens.effects_permitted(self.store, token))

    # -- confirmed termination before the return -------------------------------

    def test_the_return_requires_confirmed_termination_of_that_container(self):
        """TOK-5 AS AMENDED (DESIGN 7f504a5e): confirmed termination precedes handoff.

        The amendment I reviewed at W274875 extends this to NORMAL handoffs and says a
        naturally exited container qualifies only after the same positive checks. So
        anything short of "gone, with no writable helper surviving" refuses, and the
        resource stays held -- including when the answer is merely unknown.
        """
        domain = tokens.domain_of("workspace", "line-7/workspace")
        token = tokens.acquire(self.store, domain, operation="runtime.start:a",
                               execution="attempt-a")
        tokens.journal_launch(self.store, token, "launch:a")
        tokens.bind_container(self.store, token, "container-1", launch="launch:a")
        for what, answer in (("an unknown stop", {"stopped": False, "helpers": []}),
                             ("a surviving helper",
                              {"stopped": True, "helpers": ["writer-1"]})):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    tokens.returned(self.store, token, cessation=answer)
                self.assertEqual(caught.exception.code, "quiescence-unknown")
                self.assertIn("container-1", caught.exception.message)
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "the resource stays held while cessation is unproven")

    def test_a_confirmed_return_frees_the_resource_for_the_next_generation(self):
        """AND THE OTHER HALF: proven cessation hands the resource on as generation 2."""
        domain = tokens.domain_of("workspace", "line-7/workspace")
        first = tokens.acquire(self.store, domain, operation="runtime.start:a",
                               execution="attempt-a", attempt="attempt-a")
        tokens.journal_launch(self.store, first, "launch:a")
        tokens.bind_container(self.store, first, "container-1", launch="launch:a")
        tokens.returned(self.store, first, cessation={"stopped": True, "helpers": []})
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        self.assertFalse(tokens.effects_permitted(self.store, first),
                         "a returned token authorizes nothing further")
        second = tokens.acquire(self.store, domain, operation="runtime.start:b",
                                execution="attempt-b", attempt="attempt-b")
        self.assertEqual(second["generation"], 2)
        self.assertNotEqual(second["owner"], first["owner"])

    def test_a_stale_owner_cannot_return_or_bind(self):
        """A finished generation 1 must not release a live generation 2."""
        domain = tokens.domain_of("workspace", "line-7/workspace")
        token = tokens.acquire(self.store, domain, operation="runtime.start:a",
                               execution="attempt-a")
        impostor = dict(token, owner="somebody-elses-owner")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.returned(self.store, impostor,
                            cessation={"stopped": True, "helpers": []})
        self.assertEqual(caught.exception.code, "identity-mismatch")
        with self.assertRaises(ContractRefusal):
            tokens.journal_launch(self.store, impostor, "launch:impostor")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    # -- the rule this Work's own machinery must obey --------------------------

    def test_no_filesystem_call_happens_inside_a_token_transaction(self):
        """DB-1 ASKED AT THE SYSCALLS, the same way W270664's selector asks it.

        Every step here is database work by construction, so this is a regression
        guard rather than a discovery: if a later eligibility predicate or identity
        check reaches a filesystem, this fails.
        """
        domain = tokens.domain_of("workspace", "line-7/workspace")
        observed = []
        honest = {name: getattr(os, name) for name in
                  ("stat", "lstat", "open", "scandir", "unlink", "rmdir")}

        def watching(name):
            def call(*args, **kwargs):
                observed.append((name, self.store._connection.in_transaction))
                return honest[name](*args, **kwargs)
            return call

        for name in honest:
            setattr(os, name, watching(name))
        try:
            token = tokens.acquire(self.store, domain, operation="runtime.start:a",
                                   execution="attempt-a")
            tokens.journal_launch(self.store, token, "launch:a")
            tokens.bind_container(self.store, token, "container-1", launch="launch:a")
            tokens.returned(self.store, token,
                            cessation={"stopped": True, "helpers": []})
        finally:
            for name, call in honest.items():
                setattr(os, name, call)
        self.assertEqual([one for one in observed if one[1]], [],
                         "no filesystem call may run inside a token transaction")

    def test_an_eligibility_predicate_can_refuse_before_acquisition(self):
        """EXISTING HOLDS ARE NOT IGNORED just because this is the first consumer.

        Review 13:29:00Z: "Do not silently ignore existing line/custody/launch holds
        merely because this is the first shared-token consumer." The resource's own
        owner supplies a pure-database predicate, it runs INSIDE the admitting
        transaction, and its refusal prevents the acquisition rather than following it.
        """
        domain = tokens.domain_of("workspace", "line-7/workspace")
        asked = []

        def held(connection):
            asked.append(connection.in_transaction)
            return "a custody hold stands over this resource"

        with self.assertRaises(ContractRefusal) as caught:
            tokens.acquire(self.store, domain, operation="runtime.start:a",
                           execution="attempt-a", eligible=held)
        self.assertIn("a custody hold stands", caught.exception.message)
        self.assertEqual(asked, [True],
                         "the predicate must decide inside the admitting transaction")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "a refused eligibility check acquires nothing")


if __name__ == "__main__":
    unittest.main()
