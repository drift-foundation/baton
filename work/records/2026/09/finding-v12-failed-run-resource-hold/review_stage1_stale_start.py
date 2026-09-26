"""W266329 reviewer: one deterministic same-attempt reservation contender.

Selected before execution: test_reserve_before_launch (author's seven cases)
and this single case, real disposable fixture/controlled adapters only.
No daemon, provider, deployed store or stage-2 release activity.
Pause caller A after its preliminary axis read, complete caller B on a second
real handle, then resume A. A journal replay must not launch a second runtime.
"""
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager import attempts
from tests.manager.test_attempts import (
    ATTEMPT, NOW, Adapter, TheRuntimeIsStartedOnceAndReconciled,
)


class StaleStart(TheRuntimeIsStartedOnceAndReconciled):
    def test_stale_precheck_cannot_submit_after_other_manager_reserved(self):
        inputs, _, _ = self.delivered()
        other = ControlStore.open(self.path, incarnation='stage1-contender',
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        first, second = Adapter('runtime-first'), Adapter('runtime-second')
        original = attempts._plan_agrees
        entered = False
        outcomes = []

        def interleave(adapter, attempt_id, inputs):
            nonlocal entered
            original(adapter, attempt_id, inputs)
            if not entered:
                entered = True
                outcomes.append(attempts.request_runtime_start(
                    other, second, attempt_id=ATTEMPT, inputs=inputs))

        with patch.object(attempts, '_plan_agrees', interleave):
            try:
                outcomes.append(attempts.request_runtime_start(
                    self.store, first, attempt_id=ATTEMPT, inputs=inputs))
            except ContractRefusal as refused:
                outcomes.append({'refused': refused.code})
        self.assertEqual(len(second.started), 1)
        self.assertEqual(len(first.started), 0,
                         f'stale caller submitted after reservation: {outcomes}')


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([StaleStart(
        'test_stale_precheck_cannot_submit_after_other_manager_reserved')])


if __name__ == '__main__':
    unittest.main()
