"""The identification plan may be uncertain about a KNOWN runtime."""
import importlib.util
from pathlib import Path
import unittest
from baton_v12.worker_manager import attempts
s = importlib.util.spec_from_file_location('connected', Path(__file__).with_name('test_connected_lifecycle.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
class ExactUnknown(unittest.TestCase):
    def test_known_runtime_uncertainty_is_not_positive_nonlaunch(self):
        case = m.TheGovernedStartAndItsOwnEnding()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.attempt()
        class Unknown:
            def list(self, labels):
                return []
            def observe(self, runtime_id):
                return {'runtime_id': runtime_id, 'state': 'uncertain', 'why': 'engine cannot establish exact state'}
        plan = attempts._identify(case.store, Unknown(), m.ATTEMPT)
        self.assertEqual(plan['decision'], 'uncertain')
        self.assertIn('runtime-1', plan['why'])
        self.assertEqual(attempts._proved_non_launch(plan)['decision'], 'uncertain',
                         'an uncertain exact runtime observation must not become positive absence')
if __name__ == '__main__':
    unittest.main()
