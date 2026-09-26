"""Reviewer-owned R2 regressions; real disposable stores, fake engine only."""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody
from baton_v12.worker_manager.store import manager_signature
from test_hold_clearance import OnlyExactSettlementClearsOneHold


class R2Counterexamples(OnlyExactSettlementClearsOneHold):
    def test_nonzero_client_answer_keeps_the_hold(self):
        control, composed, attempt_id = self.unresolved_custody("review-r2-nonzero")

        def failed_client(one, argv, mount, verb):
            one.vectors.append(list(argv))
            return one.answer(status=1, stdout="", stderr="client lost its daemon response")

        for engine in self.engines:
            engine.__class__.acting = failed_client
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed, assignment_id=attempt_id, which="result")
        [held] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(held["cleared"], "nonzero/unaccountable client answer must not clear an uncertain mutation")

    def test_prior_episode_settlement_cannot_clear_next_episode(self):
        control, composed, attempt_id, first = self.held_episode("review-r2-stale")
        old_answer = self.answered(first)
        self.clearing(control, attempt_id, first, settlement=old_answer)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed, assignment_id=attempt_id, which="result")
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 2)
        self.assertFalse(holds[1]["cleared"])
        second = holds[1]["held"]
        self.assertEqual(first["helper_identity"], second["helper_identity"])
        self.assertEqual(old_answer, self.answered(second))
        with self.assertRaises(ContractRefusal, msg="the identical old answer must not settle a new unresolved submission"):
            custody.clear_custody_hold(control, attempt_id=attempt_id, which="result", episode=1,
                                      observed="retained answer from episode zero", helper_identity=second["helper_identity"],
                                      settlement=old_answer)

    def test_reader_rejects_signed_clearance_bound_to_another_episode(self):
        control, _composed, attempt_id, first = self.held_episode("review-r2-reader")
        # Disposable malformed-record fixture: internally consistent signature,
        # wrong episode binding. No authoritative deployment store is touched.
        body = {"attempt_id": attempt_id, "root": "workspace", "episode": 9,
                "helper_identity": first["helper_identity"], "observed": "wrong binding"}
        identity = custody._hold_identity(custody.CUSTODY_CLEARED_KIND, attempt_id, "result", 0)
        control.transact(identity, custody.CUSTODY_CLEARED_KIND,
                         manager_signature(custody.CUSTODY_CLEARED_KIND, body), lambda _c: dict(body))
        with self.assertRaises(ContractRefusal, msg="a matching digest is not an exact-episode binding"):
            custody.custody_holds(control, attempt_id, "result")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(R2Counterexamples(name) for name in sorted(R2Counterexamples.__dict__) if name.startswith("test_"))


if __name__ == "__main__":
    unittest.main()
