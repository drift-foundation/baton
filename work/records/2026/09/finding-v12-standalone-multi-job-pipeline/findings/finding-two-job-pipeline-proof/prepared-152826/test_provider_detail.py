"""Supported detail crosses the existing correlated report boundary, never raw text."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from failure_observation import provider_diagnostic, _supported_detail
import test_early_failure as fixtures
from test_early_failure import INCARNATION

REPO = next(p for p in Path(__file__).resolve().parents if (p / 'v12/worker').is_dir())
sys.path.insert(0, str(REPO / 'v12/python/src/baton_v12'))
import claude_agent


def detail(**changes):
    document = {'type': 'result', 'subtype': 'success', 'is_error': True,
                'terminal_reason': 'api_error', 'api_error_status': None,
                'result': claude_agent.PROVIDER_OAUTH_EXPLANATION}
    document.update(changes)
    return claude_agent._provider_diagnostic(json.dumps(document).encode(), partial=False)


class ProviderDetailTests(unittest.TestCase):
    fixture = fixtures.DiagnosticTests.fixture

    @classmethod
    def setUpClass(cls):
        if not hasattr(fixtures.DiagnosticTests, 'root'):
            fixtures.DiagnosticTests.setUpClass()
        cls.root = fixtures.DiagnosticTests.root

    def read(self, provider, review=False):
        root, failure, _ = self.fixture(provider=provider, review=review)
        return provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)

    def test_real_adapter_contract_survives_both_published_report_shapes(self):
        for review in (False, True):
            given = detail(request_id='SECRET-148870')
            answer = self.read({'status': 1, 'failure_reason': 'api-error', 'diagnostic': given}, review)
            self.assertEqual(given, answer['detail'])
            self.assertEqual('provider-reported-oauth-session-expired-refresh-failed', answer['authentication_cause'])
            self.assertIn('credential owner', answer['next_action'])
            self.assertNotIn('SECRET-148870', json.dumps(answer))

    def test_status_and_explicit_omissions_survive_without_authentication_inference(self):
        given = detail(result='SECRET-148870', api_error_status=401)
        answer = self.read({'status': 1, 'failure_reason': 'api-error', 'diagnostic': given})
        self.assertEqual(401, answer['detail']['http_status'])
        self.assertEqual('withheld', answer['detail']['explanation_status'])
        self.assertEqual('unavailable', answer['detail']['request_id_status'])
        self.assertEqual('unknown', answer['authentication_cause'])
        self.assertNotIn('SECRET-148870', json.dumps(answer))

    def test_old_reports_preserve_existing_output_and_unknown_cause(self):
        answer = self.read({'status': 1, 'failure_reason': 'api-error'})
        self.assertEqual('api-error', answer['provider_reason'])
        self.assertEqual('unknown', answer['authentication_cause'])
        self.assertNotIn('detail', answer)

    def test_unrecognized_schema_shape_members_values_and_prose_are_not_published(self):
        for key in detail():
            value = deepcopy(detail())
            value[key] = 'SECRET-148870'
            answer = self.read({'status': 1, 'failure_reason': 'api-error', 'diagnostic': value})
            self.assertNotIn('detail', answer)
            self.assertEqual('unknown', answer['authentication_cause'])
            self.assertNotIn('SECRET-148870', json.dumps(answer))
        for value in (None, [], {'SECRET-148870': 'SECRET-148870'}, dict(detail(), extra='SECRET-148870'), dict(detail(), http_status=True)):
            self.assertIsNone(_supported_detail(value))

    def test_inconsistent_or_nonfailure_reports_cannot_earn_authentication_detail(self):
        for code, reason in ((0, 'api-error'), (None, 'api-error'), (1, 'timeout'), (1, 'unclassified')):
            answer = self.read({'status': code, 'failure_reason': reason, 'diagnostic': detail()})
            self.assertNotIn('detail', answer)
            self.assertEqual('unknown', answer['authentication_cause'])
        for updates in ({'classification': 'unknown'}, {'explanation_status': 'withheld'}, {'request_id': 'SECRET-148870'}):
            self.assertIsNone(_supported_detail(dict(detail(), **updates)))
