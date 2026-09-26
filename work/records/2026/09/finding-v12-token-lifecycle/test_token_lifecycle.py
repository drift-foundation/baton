"""W275774 child A — the connected token lifecycle, with the four transferred defects fixed.

Child A's OWN selector, per reroute 275794. The parent Work's selector
(`finding-v12-shared-resource-token/test_shared_resource_token.py`, 1c1490e3) is a
read-only historical input: its cessation documents no longer satisfy the typed
contract, which is the correction rather than a regression.

Real disposable `ControlStore` instances in this fixture's own temporary directories,
a controlled engine boundary, no live Docker, no provider, no process signalled.
"""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import tokens
from baton_v12.worker_manager.store import ControlStore


class TokenLifecycle(unittest.TestCase):

    instant = "2026-09-26T14:00:00.000Z"

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-token-a-")
        self.addCleanup(root.cleanup)
        self.root = root.name
        self.store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="token-a", clock=lambda: self.instant)
        self.addCleanup(self.store.close)
        self.domain = tokens.domain_of("workspace", "line-7/workspace")

    def held(self, *, operation="runtime.start:a", execution="attempt-a",
             attempt="attempt-a", seconds=900):
        return tokens.acquire(self.store, self.domain, operation=operation,
                              execution=execution, attempt=attempt, seconds=seconds)

    def launched(self, token, container="container-1", launch="launch:a"):
        tokens.journal_launch(self.store, token, launch)
        tokens.bind_container(self.store, token, container, launch=launch)
        return {"domain": token["domain"], "generation": token["generation"],
                "launch": launch, "container": container,
                "stopped": True, "helpers": []}

    # -- the exclusion, and the resource-shaped domain -------------------------

    def test_two_attempts_of_one_resource_share_one_domain_and_the_second_refuses(self):
        first = self.held()
        with self.assertRaises(ContractRefusal) as caught:
            self.held(operation="runtime.start:b", execution="attempt-b",
                      attempt="attempt-b")
        self.assertIn("is owned by token generation 1", caught.exception.message)
        self.assertEqual(first["generation"], 1)

    def test_an_unrelated_resource_proceeds(self):
        self.held()
        beside = tokens.acquire(self.store, tokens.domain_of("workspace", "line-9/ws"),
                                operation="runtime.start:c", execution="attempt-c")
        self.assertEqual(beside["generation"], 1)

    # -- (3) replay by operation ------------------------------------------------

    def test_the_same_operation_resolves_to_its_own_acquisition(self):
        """DEFECT 3, from parent review 13:41:00Z: a retry allocated a NEW generation, so
        one operation could come to own two. The retry now answers the original."""
        first = self.held()
        again = self.held()
        self.assertEqual(again["generation"], first["generation"])
        self.assertEqual(again["owner"], first["owner"])
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)

    def test_a_different_operation_is_still_refused_while_one_is_outstanding(self):
        """The replay path must not become a way past the exclusion."""
        self.held()
        with self.assertRaises(ContractRefusal):
            self.held(operation="runtime.start:other", execution="attempt-a")

    # -- (2) the lifecycle, not only the owner ---------------------------------

    def test_a_returned_generation_cannot_bind_a_container_late(self):
        """DEFECT 2: `_owning` checked the original owner only, so the rightful owner of a
        DEAD token could still bind afterwards -- exactly what TOK-11 forbids."""
        # RETURNED WITHOUT A LAUNCH, so the late journal_launch reaches MY lifecycle check
        # rather than the journal's one-act-per-identity collision. Measured: returning a
        # LAUNCHED token and then re-journalling hit "already recorded with a different
        # kind or signature" first -- also a correct refusal, but it proves the journal's
        # rule and not this one, so the case is staged to isolate the check it is about.
        token = self.held()
        tokens.returned(self.store, token,
                        cessation={"domain": self.domain, "generation": 1,
                                   "launch": None, "container": None,
                                   "stopped": True, "helpers": []})
        with self.assertRaises(ContractRefusal) as caught:
            tokens.journal_launch(self.store, token, "launch:late")
        self.assertIn("has been returned", caught.exception.message)

    def test_an_expired_generation_cannot_bind_or_return(self):
        token = self.held(seconds=1)
        self.instant = "2026-09-26T15:00:00.000Z"
        for what, act in (
            ("a late launch", lambda: tokens.journal_launch(self.store, token, "l:x")),
            ("a late return", lambda: tokens.returned(
                self.store, token,
                cessation={"domain": self.domain, "generation": 1, "launch": None,
                           "container": None, "stopped": True, "helpers": []})),
        ):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                self.assertIn("expired at", caught.exception.message)

    # -- (1) typed, exact, non-truthy cessation --------------------------------

    def test_a_truthy_string_is_not_a_confirmed_termination(self):
        """DEFECT 1, the sharpest one: `stopped="false"` passed the old conditional."""
        token = self.held()
        evidence = dict(self.launched(token), stopped="false")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.returned(self.store, token, cessation=evidence)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertIn("not the boolean True", caught.exception.message)
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)

    def test_evidence_about_another_execution_is_refused(self):
        """DEFECT 1: the document carried no binding to the token it was offered for."""
        token = self.held()
        evidence = dict(self.launched(token), container="container-somebody-else")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.returned(self.store, token, cessation=evidence)
        self.assertEqual(caught.exception.code, "identity-mismatch")
        self.assertIn("not evidence about this one", caught.exception.message)

    def test_a_surviving_helper_still_holds_the_resource(self):
        token = self.held()
        evidence = dict(self.launched(token), helpers=["writer-1"])
        with self.assertRaises(ContractRefusal) as caught:
            tokens.returned(self.store, token, cessation=evidence)
        self.assertEqual(caught.exception.code, "quiescence-unknown")

    def test_an_unresolved_launch_cannot_be_returned_as_if_nothing_ran(self):
        """DEFECT 1's third hole: an UNBOUND return skipped the check entirely, so a
        journalled launch whose outcome nobody knows was returned as clean."""
        token = self.held()
        tokens.journal_launch(self.store, token, "launch:a")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.returned(self.store, token,
                            cessation={"domain": self.domain, "generation": 1,
                                       "launch": "launch:a", "container": None,
                                       "stopped": True, "helpers": []})
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertIn("UNKNOWN", caught.exception.message)

    def test_a_confirmed_return_hands_the_resource_to_the_next_generation(self):
        first = self.held()
        tokens.returned(self.store, first, cessation=self.launched(first))
        self.assertEqual(tokens.outstanding(self.store, self.domain), [])
        second = self.held(operation="runtime.start:b", execution="attempt-b",
                           attempt="attempt-b")
        self.assertEqual(second["generation"], 2)

    def test_an_exact_replay_of_the_return_does_not_change_its_signature(self):
        """DEFECT 3's other half: `settled_at` put a fresh clock in SIGNED operands, so an
        exact replay computed a different signature and collided with itself."""
        token = self.held()
        evidence = self.launched(token)
        first = tokens.returned(self.store, token, cessation=evidence)
        self.instant = "2026-09-26T14:30:00.000Z"
        again = tokens.returned(self.store, token, cessation=evidence)
        self.assertEqual(first, again)

    # -- the gate, and the rule this module must obey --------------------------

    def test_effects_are_withheld_until_a_container_is_bound(self):
        token = self.held()
        self.assertFalse(tokens.effects_permitted(self.store, token))
        tokens.journal_launch(self.store, token, "launch:a")
        self.assertFalse(tokens.effects_permitted(self.store, token))
        tokens.bind_container(self.store, token, "container-1", launch="launch:a")
        self.assertTrue(tokens.effects_permitted(self.store, token))

    def test_no_external_call_happens_inside_a_token_transaction(self):
        """DEFECT 4 INCLUDED: `uuid.uuid4()` ran inside BEGIN IMMEDIATE, and OS randomness
        is external to the database decision. It is drawn before the lock now, so this
        watches `os.urandom` as well as the filesystem."""
        observed = []
        honest = {name: getattr(os, name) for name in
                  ("stat", "lstat", "open", "scandir", "urandom")}

        def watching(name):
            def call(*args, **kwargs):
                observed.append((name, self.store._connection.in_transaction))
                return honest[name](*args, **kwargs)
            return call

        for name in honest:
            setattr(os, name, watching(name))
        try:
            token = self.held()
            evidence = self.launched(token)
            tokens.returned(self.store, token, cessation=evidence)
        finally:
            for name, call in honest.items():
                setattr(os, name, call)
        self.assertEqual([one for one in observed if one[1]], [],
                         "no external call may run inside a token transaction")


if __name__ == "__main__":
    unittest.main()
