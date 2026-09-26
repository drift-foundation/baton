"""Stage2 selected reviewer schedule: reconcile while start has not returned.

Real disposable stores, controlled adapter only. Select this one case plus the
author stage2 module and accepted stage1 pair; no daemon or deployed resources.
"""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, abandon_attempt
from baton_v12.worker_manager import attempts
import tests.manager.test_attempts as accepted
from test_delayed_launch_release import ADelayedSubmitterKeepsTheResource, ATTEMPT, RETENTION


class PendingSubmitter(ADelayedSubmitterKeepsTheResource):
    def test_other_manager_cannot_release_before_submitter_returns(self):
        adapter, order = self.prepared()
        other = ControlStore.open(self.path, incarnation='review-canceller',
                                  clock=lambda: accepted.NOW)
        self.addCleanup(other.close)
        original = adapter.start
        seen = {}

        def paused_start(operands):
            # The external start created its runtime, but the submitting call
            # is still on the stack and has not completed or been terminated.
            answer = original(operands)
            seen['cancel'] = attempts.request_cancellation(
                other, self.port, accepted.Agent(), adapter,
                attempt_id=ATTEMPT, reason='cancel while submit is pending')
            seen['reconcile'] = attempts.reconcile_runtime(
                other, adapter, attempt_id=ATTEMPT)
            try:
                seen['ending'] = abandon_attempt(
                    other, self.port, adapter, attempt_id=ATTEMPT,
                    reason='another manager observed the runtime',
                    retention_policy_digest=RETENTION)
            except ContractRefusal as refusal:
                seen['ending'] = {'refused': refusal.code}
            seen['holders_before_return'] = self.lane_holders()
            return answer

        adapter.start = paused_start
        try:
            attempts.request_runtime_start(self.store, adapter,
                                           attempt_id=ATTEMPT)
        except ContractRefusal as refusal:
            seen['late_return'] = refusal.code
        self.assertEqual(seen['holders_before_return'], [ATTEMPT],
                         f'other manager released a pending submitter: {seen}')


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([PendingSubmitter(
        'test_other_manager_cannot_release_before_submitter_returns')])
