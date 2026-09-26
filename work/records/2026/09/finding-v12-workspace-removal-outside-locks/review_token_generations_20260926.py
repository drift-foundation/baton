"""Independent token generation and delayed-binding regressions."""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from test_removal_outside_the_lock import RemovalOutsideTheLock


class TokenGenerations(RemovalOutsideTheLock):
    def cease_first(self, bound=True):
        self.attempt_roots("assignment-t")
        first = self.a_token(seconds=1)
        if bound:
            workspaces.bind_token_container(self.store, "assignment-t", first["ordinal"],
                                            first, "container-first")
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        workspaces.revoke_expired_token(self.store, "assignment-t", first["ordinal"],
            lambda container: {"stopped": True, "helpers": []})
        return first

    def test_live_second_generation_excludes_third(self):
        self.cease_first()
        second = self.a_token()
        self.assertFalse(workspaces.token_of(self.store, "assignment-t", second["ordinal"])["expired"])
        with self.assertRaises(ContractRefusal):
            self.a_token()

    def test_revoked_unbound_generation_cannot_bind_after_replacement(self):
        first = self.cease_first(bound=False)
        self.a_token()
        with self.assertRaises(ContractRefusal):
            workspaces.bind_token_container(self.store, "assignment-t", first["ordinal"],
                                            first, "late-container")

    def test_string_stop_answer_is_not_positive_cessation(self):
        self.attempt_roots("assignment-t")
        first = self.a_token(seconds=1)
        workspaces.bind_token_container(self.store, "assignment-t", first["ordinal"],
                                        first, "container-first")
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        with self.assertRaises(ContractRefusal):
            workspaces.revoke_expired_token(self.store, "assignment-t", first["ordinal"],
                lambda container: {"stopped": "false", "helpers": []})


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(TokenGenerations(name) for name in (
        "test_live_second_generation_excludes_third",
        "test_revoked_unbound_generation_cannot_bind_after_replacement",
        "test_string_stop_answer_is_not_positive_cessation"))
