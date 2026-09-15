"""One inconclusive post-fault listing, followed by ordinary exact answers.

Only the adapter's listing answer during failure settlement is simulated.
Later sweeps and all owner records remain real; no result or state is injected.
"""
import json
import unittest
from unittest import mock

from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
from baton_v12.job_manager.integration_capacity import integration_capacity_of
from baton_v12.job_manager.scheduler import allocation_of
from baton_v12.worker_manager import attempts, attempt_runtime_of
from baton_v12.worker_manager.oci import OciAdapter

original_settlement = attempts._settled_and_recorded
original_list = OciAdapter.list
faults = []
requests = []
adapters = []


def uncertain_once(store, adapter, attempt_id, failure):
    def inconclusive(instance, request):
        requests.append(request)
        adapters.append(instance)
        return []
    with mock.patch.object(OciAdapter, 'list', inconclusive):
        answer = original_settlement(store, adapter, attempt_id, failure)
    faults.append(attempt_runtime_of(store, attempt_id))
    return answer


class Research(OneManagedPreparationCompletes):
    def ended_after_failed_start(self, held, preparation, processes, uncertainty,
                                 orchestration, *args):
        capacity = integration_capacity_of(held.job, orchestration)
        members = {m['phase']: m for m in capacity['members']}
        attempt = members['prepare']['execution_attempt_id']
        current = attempt_runtime_of(held.control, attempt)
        available = original_list(adapters[-1], requests[-1])
        allocation = allocation_of(held.job, capacity['root']['root_assignment_id'])
        print(json.dumps({
            'proof': 'one-inconclusive-listing-then-exact-evidence',
            'injected_listings': len(requests),
            'at_fault': faults,
            'after_ordinary_sweeps': current,
            'later_available_runtime_ids': [r['runtime_id'] for r in available],
            'fixture_process_count': len(processes),
            'worker_returncodes': [p.poll() for p in processes],
            'prepare': members['prepare']['state'],
            'apply': members['apply']['state'],
            'root': capacity['root']['lifecycle'],
            'allocation': allocation['allocation_state'],
        }, sort_keys=True), flush=True)
        self.assertEqual(len(requests), 1)
        self.assertEqual(faults[0]['execution_runtime'], 'uncertain')
        self.assertEqual(len(available), 1)
        self.assertEqual(len(processes), 1)
        self.assertEqual(current['execution_runtime'], 'destroyed',
                         'later exact observation never reaches failed-start recovery')


with mock.patch.object(attempts, '_settled_and_recorded', uncertain_once):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        Research('test_a_start_that_failed_after_creating_a_runtime_is_ended'),
    ]))
raise SystemExit(not result.wasSuccessful())
