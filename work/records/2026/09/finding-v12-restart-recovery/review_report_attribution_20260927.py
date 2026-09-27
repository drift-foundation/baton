import json
import unittest
from unittest import mock
from tests.job_manager.test_tool import _unsettled_governed_attempt
from baton_v12.worker_manager import attempts
from tools import job_manager


class ReportAttribution(unittest.TestCase):
    def test_historical_row_cannot_supply_current_tokens_attachment(self):
        case = _unsettled_governed_attempt(self)
        control = case['store']
        owner = dict(attempts._require_attempt(control, case['attempt_id']))
        # Model a historical row over this same physical resource. Only discovery
        # is supplied; the current token and its actual owner remain real store rows.
        historical = dict(owner, runtime_attempt_id='historical-attempt', runtime_id='historical-container')
        def engine(argv, **kwargs):
            return {'status': 0, 'stderr': '', 'stdout': json.dumps({'Id': case['runtime_id'], 'State': {'Running': True}})}
        with mock.patch.object(job_manager, '_governed_rows', return_value=[historical, owner]):
            result = job_manager._reclaiming(control, 'docker', engine)(now='2026-08-24T00:05:00.000Z')
        self.assertTrue(result['unresolved'])
        for report in result['unresolved']:
            self.assertEqual(report['execution'], case['attempt_id'])
            self.assertNotIn('contradicts_binding', report, 'historical runtime was attributed to current token owner')


if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReportAttribution)).wasSuccessful())
