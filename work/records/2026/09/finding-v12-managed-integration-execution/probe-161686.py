"""Independent deterministic review; temporary fixture stores only."""
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts as owner
from baton_v12.worker_manager import documents
from baton_v12.worker_manager.store import manager_signature
from tests.manager.test_attempts import ATTEMPT, Adapter, Agent, AttemptCase


class EvidenceAndRaceReview(AttemptCase):
    def activated(self):
        self.claimed()
        owner.activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                                  expect=self.expect())

    def cancel(self):
        owner.request_cancellation(self.store, self.port, Agent(), Adapter(),
                                   attempt_id=ATTEMPT)
        self.session.live_assignment = None

    def test_absent_authority_record_cannot_prove_the_named_cancellation(self):
        self.activated()
        self.cancel()
        # Fault at the normal Authority session boundary: no evidence for the
        # named operation. The fake cancellation reply alone is not a read.
        self.session.operation_record = mock.Mock(return_value=None)
        with self.assertRaises(ContractRefusal):
            owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)

    def test_foreign_committed_intent_cannot_prove_this_attempt(self):
        self.activated()
        attempt = self.row()
        operation_id = owner._cancel_operation_id(attempt)
        foreign = dict(self.expect(), generation=999)
        self.store.transact(operation_id, "attempt.cancel",
                            manager_signature("attempt.cancel", {"foreign": True}),
                            lambda connection: documents.cancel_intent(
                                attempt_id="foreign-attempt", assignment=foreign,
                                authority_operation_id="foreign-operation", reason=None))
        # Model independently received cancellation-axis and absent-assignment
        # observations, through the real local owner rather than raw SQL.
        owner.observe(self.store, attempt_id=ATTEMPT,
                      axis="execution_runtime", value="cancel-requested")
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal):
            owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)

    def test_stale_start_pre_read_loses_to_cancellation_axis(self):
        self.activated()
        adapter = Adapter()
        original = owner._plan_agrees
        def interleave(*args):
            original(*args)
            self.cancel()
        with mock.patch.object(owner, "_plan_agrees", side_effect=interleave):
            with self.assertRaises(ContractRefusal):
                owner.request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(adapter.started, [])
        self.assertEqual(owner.unstarted_cancellation_of(
            self.store, self.port, ATTEMPT)["state"], documents.FENCED_BEFORE_START)

    def test_committed_start_delayed_at_adapter_refuses_without_row_edits(self):
        self.activated()
        adapter = Adapter()
        original = adapter.start
        observed = []
        def delayed(operands):
            self.cancel()
            self.assertIsNone(self.row()["runtime_id"])
            self.assertEqual(self.row()["execution_runtime"], "cancel-requested")
            with self.assertRaises(ContractRefusal) as caught:
                owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)
            self.assertIn("committed a runtime start", str(caught.exception))
            observed.append(True)
            return original(operands)
        adapter.start = delayed
        # Later reconciliation also refuses a running observation after the
        # cancellation; that does not negate the earlier journal-only proof.
        with self.assertRaises(ContractRefusal):
            owner.request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(observed, [True])


if __name__ == "__main__":
    unittest.main(verbosity=2)
