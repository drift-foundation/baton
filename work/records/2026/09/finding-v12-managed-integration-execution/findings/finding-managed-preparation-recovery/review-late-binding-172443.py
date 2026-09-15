"""Check the existing failed-start API after public late reconciliation.

Reuse definitions from this claim's uncertainty probe without running its suite.
Only disposable fixture owners are changed through their ordinary APIs.
"""
from pathlib import Path

probe = Path(__file__).with_name('review-uncertain-recovery-172443.py')
definitions = probe.read_text().partition('\nwith mock.patch.object(attempts,')[0]
exec(compile(definitions, str(probe), 'exec'))

from tools.integration_worker import ManagedPreparation
from baton_v12.contracts import ContractRefusal

original_failed = ManagedPreparation._failed_start
captured = []


def capture(instance, intent, held):
    captured.append((intent, held))
    return original_failed(instance, intent, held)


class Binding(Research):
    def ended_after_failed_start(self, held, preparation, processes, uncertainty,
                                 orchestration, *args):
        capacity = integration_capacity_of(held.job, orchestration)
        attempt = next(m['execution_attempt_id'] for m in capacity['members']
                       if m['phase'] == 'prepare')
        before = attempts.attempt_start_failure_of(held.control, attempt)
        attempts.reconcile_runtime(held.control, adapters[-1], attempt_id=attempt)
        current = attempt_runtime_of(held.control, attempt)
        with self.assertRaises(ContractRefusal) as refused:
            original_failed(preparation, *captured[-1])
        after = attempts.attempt_start_failure_of(held.control, attempt)
        print(json.dumps({
            'proof': 'late-runtime-binding-versus-immutable-failed-start-receipt',
            'receipt_runtime_id': before['runtime_id'],
            'reconciled_runtime_id': current['runtime_id'],
            'reconciled_execution_runtime': current['execution_runtime'],
            'receipt_unchanged': before == after,
            'refusal': str(refused.exception),
            'worker_returncodes': [p.poll() for p in processes],
        }, sort_keys=True), flush=True)
        self.assertIsNone(before['runtime_id'])
        self.assertIsNotNone(current['runtime_id'])
        self.assertEqual(before, after)
        self.assertIn('record is what authorizes', str(refused.exception))


with mock.patch.object(attempts, '_settled_and_recorded', uncertain_once), \
     mock.patch.object(ManagedPreparation, '_failed_start', capture):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        Binding('test_a_start_that_failed_after_creating_a_runtime_is_ended'),
    ]))
raise SystemExit(not result.wasSuccessful())
