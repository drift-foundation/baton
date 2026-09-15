"""Desired contract checks: deterministic, no engine or model; failures are findings."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.manager.test_reconciliation_task import task, _request
from baton_v12.integration import managed_execution
from baton_v12.contracts import ContractRefusal


class RequiredContracts(unittest.TestCase):
    def test_worker_rejects_the_incomplete_request_rejected_by_its_owner(self):
        value = _request()
        with self.assertRaises(ContractRefusal):
            managed_execution.adopt_preparation_request(value)
        with tempfile.TemporaryDirectory(prefix='w166129-request-') as root:
            (Path(root) / task.REQUEST_NAME).write_text(json.dumps(value))
            with self.assertRaises(task.PreparationRefusal):
                task.read_request(root)

    def test_measure_refuses_a_symlink_instead_of_silently_omitting_it(self):
        with tempfile.TemporaryDirectory(prefix='w166129-tree-') as root:
            (Path(root) / 'data').write_text('candidate')
            (Path(root) / 'link').symlink_to('data')
            with self.assertRaises(task.PreparationRefusal):
                task.measure(root)

    def test_failed_phase_is_not_listed_as_never_run(self):
        with tempfile.TemporaryDirectory(prefix='w166129-sequence-') as root:
            states = {}
            for name in task.CAUSAL_ORDER:
                place = Path(root) / name
                place.mkdir()
                (place / task.HARNESS_NAME).write_text('pass\n')
                states[name] = {'path': str(place), 'revision': 'a' * 40}
            with patch.object(task, 'run_bounded', side_effect=[
                {'status': 0, 'tag': None, 'output': ''},
                {'status': None, 'tag': 'timeout', 'output': 'timed out'}]):
                completed, not_run, tag = task.observe(_request(), states, 1)
            self.assertEqual([row['name'] for row in completed], ['combined'])
            self.assertEqual(tag, 'timeout')
            self.assertEqual(not_run, ['isolated'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
