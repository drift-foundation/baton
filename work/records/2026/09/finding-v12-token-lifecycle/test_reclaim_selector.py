"""W275774 — the manager-reclaim selector is exactly true or false.

Review 2026-09-27T01-49-32Z reproduced the defect with two inputs and scheduled exact
bool validation: `reclaiming` selects the ONE exception to a holder's expiry and
revocation refusals, so a truthy value of another type silently bought a privilege the
caller never asked for. These cases cover the reviewer's two inputs and the rest of the
shapes a caller can actually pass, and -- the half that matters as much -- they pin the
two MODES that must not change: `False`/default is the ordinary holder and `True` is the
supported manager settlement.

Run standalone: the class inherits the accepted lifecycle fixture, so whole-module
discovery would re-run that suite's cases here as well.
"""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import tokens

from test_token_lifecycle import TokenLifecycle

EXPIRED = "2026-09-26T15:00:00.000Z"
MALFORMED = ("false", "true", "", 0, 1, -1, 0.0, None, [], [True], {}, {"reclaiming": True},
             object())


class TheReclaimSelectorIsExactlyBoolean(TokenLifecycle):
    """One expired, launched, bound generation per case, and one malformed request."""

    def expired(self):
        token = self.held(seconds=1)
        evidence = self.launched(token)
        self.instant = EXPIRED
        return token, evidence

    def fresh(self):
        """A new store AND the fixture's own clock again.

        MEASURED, and it caught one of these cases passing for the wrong reason:
        `instant` is a CLASS attribute and the base `setUp` does not reset the
        instance one, so re-preparing without dropping it left the clock at
        `EXPIRED` -- and the next acquisition minted a token expiring one second
        AFTER that, which an ordinary holder may of course return. The subject of
        these cases is the selector, so each input starts from the same state.
        """
        self.__dict__.pop("instant", None)
        self.setUp()

    def released(self, evidence):
        """`release`'s own three-member cessation input, not `returned`'s document."""
        return {name: evidence[name] for name in ("container", "stopped", "helpers")}

    def releasing(self, **named):
        return tokens.release(self.store, "line-7/workspace", "workspace",
                              execution="attempt-a", operation="runtime.start:a",
                              **named)

    # -- every malformed shape refuses, and nothing moves -----------------------

    def test_no_malformed_selector_returns_an_expired_generation(self):
        for offered in MALFORMED:
            with self.subTest(reclaiming=repr(offered)):
                token, evidence = self.expired()
                refusal = self.refusal(
                    lambda: tokens.returned(self.store, token, cessation=evidence,
                                            reclaiming=offered))
                self.assertEqual((refusal.category, refusal.code),
                                 ("integrity", "schema"))
                self.assertIn("exactly true or false", refusal.message)
                self.assertEqual(
                    len(tokens.outstanding(self.store, self.domain)), 1,
                    "a malformed request returned the resource anyway")
                self.fresh()

    def test_no_malformed_selector_releases_an_expired_generation(self):
        for offered in MALFORMED:
            with self.subTest(reclaiming=repr(offered)):
                _token, evidence = self.expired()
                refusal = self.refusal(
                    lambda: self.releasing(cessation=self.released(evidence),
                                           reclaiming=offered))
                self.assertEqual((refusal.category, refusal.code),
                                 ("integrity", "schema"))
                self.assertEqual(
                    len(tokens.outstanding(self.store, self.domain)), 1)
                self.fresh()

    def test_a_repeated_malformed_request_refuses_again(self):
        """THE REPLAY HALF. A malformed request must not become answerable by
        having been made before: nothing durable is written for it, so the second
        one is refused for the same reason rather than replaying an act."""
        token, evidence = self.expired()
        for _ in range(2):
            refusal = self.refusal(
                lambda: tokens.returned(self.store, token, cessation=evidence,
                                        reclaiming="false"))
            self.assertEqual(refusal.code, "schema")
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)

    def test_the_selector_is_refused_before_the_cessation_is_even_read(self):
        """Ordering, because the reviewer's own V1 probe passed vacuously on an
        earlier refusal: a malformed selector must be refused ahead of the
        evidence, so the answer names the selector rather than the document."""
        token, _evidence = self.expired()
        refusal = self.refusal(
            lambda: tokens.returned(self.store, token, cessation={"nonsense": 1},
                                    reclaiming=1))
        self.assertIn("exactly true or false", refusal.message)

    # -- and the two modes that must not change --------------------------------

    def test_the_ordinary_holder_still_cannot_return_after_expiry(self):
        for offered in ({}, {"reclaiming": False}):
            with self.subTest(**offered):
                token, evidence = self.expired()
                refusal = self.refusal(
                    lambda: tokens.returned(self.store, token, cessation=evidence,
                                            **offered))
                self.assertEqual(refusal.category, "refused")
                self.assertEqual(
                    len(tokens.outstanding(self.store, self.domain)), 1)
                self.fresh()

    def test_the_manager_settlement_still_returns_it(self):
        token, evidence = self.expired()
        answered = tokens.returned(self.store, token, cessation=evidence,
                                   reclaiming=True)
        self.assertEqual(answered["generation"], token["generation"])
        self.assertEqual(tokens.outstanding(self.store, self.domain), [])

    def test_the_governed_release_selector_is_the_same_boundary(self):
        """The governance family's own return validates it too, so a caller
        reaching it through `Governance.release` is refused at the same place."""
        token, evidence = self.expired()
        governance = tokens.workspace_governance()
        attempt = {"runtime_attempt_id": "attempt-a",
                   "workspace_device": 1, "workspace_inode": 2}
        refusal = self.refusal(
            lambda: governance.release(self.store, attempt,
                                       operation="runtime.start:a",
                                       cessation=self.released(evidence),
                                       reclaiming="true"))
        self.assertIn("exactly true or false", refusal.message)
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)

    def refusal(self, call):
        with self.assertRaises(ContractRefusal) as caught:
            call()
        return caught.exception


if __name__ == "__main__":
    suite = unittest.TestSuite(
        TheReclaimSelectorIsExactlyBoolean(name) for name in
        sorted(TheReclaimSelectorIsExactlyBoolean.__dict__)
        if name.startswith("test_"))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
