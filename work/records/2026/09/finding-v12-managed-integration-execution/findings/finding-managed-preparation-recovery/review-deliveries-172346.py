"""Inspect delivery lifecycle after the candidate's known failed-start ending.

Reads lifecycle metadata and path presence only, before fixture teardown.
Uses the existing deterministic engine boundary and its owned worker cleanup.
"""
import json
import pathlib
import unittest

from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
from baton_v12.job_manager.integration_capacity import integration_capacity_of


class Research(OneManagedPreparationCompletes):
    def ended_after_failed_start(self, held, preparation, processes, uncertainty,
                                 orchestration, *args):
        super().ended_after_failed_start(held, preparation, processes, uncertainty,
                                        orchestration, *args)
        capacity = integration_capacity_of(held.job, orchestration)
        attempt = next(m['execution_attempt_id'] for m in capacity['members']
                       if m['phase'] == 'prepare')
        worker = preparation._runtime.operations[attempt]._worker
        state = worker.credential_home.read_state(attempt)
        credential_root = pathlib.Path(worker.credential_home.volatile_root(attempt))
        launch_root = pathlib.Path(worker.given['launch_home'], attempt)
        observed = {
            'proof': 'delivery-state-after-product-failed-start-ending',
            'credential_lifecycle': state,
            'credential_root_present': credential_root.exists(),
            'launch_root_present': launch_root.exists(),
            'worker_returncodes': [p.poll() for p in processes],
        }
        print(json.dumps(observed, sort_keys=True), flush=True)
        self.assertFalse(credential_root.exists(), 'ended failed start retained credential delivery')
        self.assertFalse(launch_root.exists(), 'ended failed start retained launch delivery')


result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
    Research('test_a_start_that_failed_after_creating_a_runtime_is_ended'),
]))
raise SystemExit(not result.wasSuccessful())
