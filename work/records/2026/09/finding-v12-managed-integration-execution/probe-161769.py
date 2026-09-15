"""Independent projection-boundary and committed-start replay checks."""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts as owner
from tests.manager.test_attempts import ATTEMPT, Adapter, Agent, AttemptCase
from tests.manager.test_reconciliation_worker import TheFencedBeforeStartProof


class ProjectionReview(AttemptCase):
    cancelled = TheFencedBeforeStartProof.cancelled
    fenced = TheFencedBeforeStartProof.fenced

    def test_foreign_work_projection_refuses(self):
        self.cancelled()
        self.session._work["work_id"] = "foreign-work"
        with self.assertRaises(ContractRefusal):
            owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)

    def test_missing_work_identity_refuses(self):
        self.cancelled()
        self.session._work.pop("work_id", None)
        with self.assertRaises(ContractRefusal):
            owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)

    def test_noninteger_generation_refuses(self):
        self.cancelled()
        self.session._work["work_id"] = self.expect()["work_ref"]["work_id"]
        for generation in (True, 1.0):
            with self.subTest(generation=repr(generation)):
                self.fenced(generation=generation)
                with self.assertRaises(ContractRefusal):
                    owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)

    def test_malformed_fences_refuse_through_contract_boundary(self):
        self.cancelled()
        self.session._work["work_id"] = self.expect()["work_ref"]["work_id"]
        for fences in ([{"generation": "7"}, {"generation": 8}],
                       [{"generation": 1, "cause": "cancelled"}],
                       [{"generation": 1, "cause": "cancelled", "reason": None},
                        {"generation": 1, "cause": "cancelled", "reason": None}]):
            with self.subTest(fences=fences):
                self.session._work["fenced_generations"] = fences
                with self.assertRaises(ContractRefusal):
                    owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)

    def test_exact_committed_start_replay_still_refuses_proof(self):
        self.claimed()
        owner.activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                                  expect=self.expect())
        adapter = Adapter()
        seen = []
        original = adapter.start
        def delayed(operands):
            owner.request_cancellation(self.store, self.port, Agent(), Adapter(),
                                       attempt_id=ATTEMPT)
            self.fenced()
            self.session._work["work_id"] = self.expect()["work_ref"]["work_id"]
            row = self.store.operation_record(operands["operation_id"])
            def forbidden_action(connection):
                self.fail("A committed start replay executed its action")
            replay = self.store.transact(operands["operation_id"], "runtime.start",
                                         row["signature"], forbidden_action)
            self.assertEqual(replay["attempt_id"], ATTEMPT)
            self.assertIsNone(self.row()["runtime_id"])
            with self.assertRaises(ContractRefusal) as caught:
                owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)
            self.assertIn("committed a runtime start", str(caught.exception))
            seen.append(True)
            return original(operands)
        adapter.start = delayed
        with self.assertRaises(ContractRefusal):
            owner.request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(seen, [True])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProjectionReview)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
