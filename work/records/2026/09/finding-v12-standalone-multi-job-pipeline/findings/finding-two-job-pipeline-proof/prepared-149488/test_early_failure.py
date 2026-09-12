"""Offline proof-runner checks; retained status is replayed, no runtime is run."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from failure_observation import first_failure, provider_diagnostic
import test_stats_observation as fixtures

HERE = Path(__file__).resolve().parent
runner = fixtures.runner
FACTS = json.loads((HERE / 'evidence/run6-status-facts.json').read_text())
FAILED = FACTS['samples'][4]['status']
INCARNATION = 'w71879-run6'
HISTORICAL_UUID = 'c71879b0000000000000000000000001'
HISTORICAL_WORKS = {name: 'c71879b0-W' + str(i) for i, name in enumerate(('a', 'b', 'verification', 'review', 'approval'), 1)}


def detect(status):
    return first_failure(status, authority_uuid=HISTORICAL_UUID, incarnation=INCARNATION, works=HISTORICAL_WORKS)


class EarlyFailureTests(unittest.TestCase):
    def test_retained_run6_first_failure_is_sample5_not_final_timeout(self):
        found = [(i, row['wall_seconds'], detect(row['status'])) for i, row in enumerate(FACTS['samples'], 1)]
        first = next(row for row in found if row[2] is not None)
        self.assertEqual((5, 8.731681402990944), first[:2])
        self.assertEqual('job-a/implementation', first[2]['stage_id'])
        self.assertEqual('unable', first[2]['disposition'])
        self.assertEqual('answered', first[2]['ending'])

    def test_review_failure_is_independently_detected_at_sample21(self):
        for i, sample in enumerate(FACTS['samples'], 1):
            status = deepcopy(sample['status'])
            if status:
                status['jobs'] = [j for j in status['jobs'] if j['job_id'] == 'job-b']
            if detect(status):
                self.assertEqual(21, i)
                self.assertEqual('job-b/review', detect(status)['stage_id'])
                break
        else:
            self.fail('retained B review failure was missed')

    def test_pending_collection_quiescence_and_success_are_not_failure(self):
        for disposition in ('completed', 'plan-rejected'):
            status = deepcopy(FAILED)
            stage = status['jobs'][0]['stages'][0]
            if disposition == 'plan-rejected':
                stage['kind'] = 'review'; stage['stage_id'] = 'job-a/review'
                stage['allocation']['stage_id'] = stage['stage_id']
                for receipt in stage['receipts']: receipt['stage_id'] = stage['stage_id']
            stage['exchange']['terminal']['disposition'] = disposition
            self.assertIsNone(detect(status))
        for state in ('waiting', 'working', 'unstarted', 'unreadable'):
            status = deepcopy(FAILED)
            stage = status['jobs'][0]['stages'][0]
            stage['exchange']['state'] = state
            stage['exchange']['terminal'] = None
            stage['runtime']['execution_runtime'] = 'quiescent'
            stage['artifacts'] = None
            self.assertIsNone(detect(status))
        self.assertIsNone(detect(None))

    def test_stale_foreign_and_uncorrelated_answers_do_not_decide_failure(self):
        mutations = [
            lambda s: s.update(canonical=False),
            lambda s: s.update(incarnation='foreign'),
            lambda s: s['jobs'][0].update(submission_id='foreign'),
            lambda s: s['jobs'][0]['stages'][0].update(attempt_id='attempt-foreign'),
            lambda s: s['jobs'][0]['stages'][0].update(episode=99),
            lambda s: s['jobs'][0]['stages'][0]['runtime']['assignment']['work_ref'].update(authority_uuid='foreign'),
            lambda s: s['jobs'][0]['stages'][0]['runtime']['assignment'].update(generation=99),
            lambda s: s['jobs'][0]['stages'][0]['exchange'].update(foreign=['untrusted']),
            lambda s: s['jobs'][0]['stages'][0]['exchange'].update(unreadable={'code': 'untrusted'}),
            lambda s: s['jobs'][0]['stages'][0]['exchange'].update(receipt=None),
            lambda s: s['jobs'][0]['stages'][0]['exchange']['command'].update(sequence_id='foreign')]
        for change in mutations:
            status = deepcopy(FAILED); change(status)
            self.assertIsNone(detect(status))

    def test_correlated_fault_cancel_and_lost_are_definitive(self):
        for ending, disposition, fault in [('faulted', None, 'agent'), ('lost', None, None), ('answered', 'cancelled', None)]:
            status = deepcopy(FAILED); exchange = status['jobs'][0]['stages'][0]['exchange']
            exchange['state'] = ending
            exchange['terminal'].update(ending=ending, disposition=disposition, fault_code=fault)
            self.assertIsNotNone(detect(status))
        status['jobs'][0]['stages'][0]['exchange']['terminal']['fault_code'] = 'TOKEN-SENTINEL'
        status['jobs'][0]['stages'][0]['exchange']['terminal']['ending'] = 'faulted'
        status['jobs'][0]['stages'][0]['exchange']['state'] = 'faulted'
        self.assertIsNone(detect(status))

    def exercise(self, **kwargs):
        if not hasattr(fixtures.RunnerTests, 'retained'):
            fixtures.RunnerTests.setUpClass()
        fixture = fixtures.RunnerTests('test_incomplete_jobs_do_not_become_terminal_from_gap')
        # Relabel an explicit synthetic copy for the fresh runner; retained facts stay exact.
        synthetic = json.loads(json.dumps(FAILED).replace(HISTORICAL_UUID, runner.UUID).replace('c71879b0-', runner.UUID[:8] + '-').replace(INCARNATION, 'w71879-run8'))
        with mock.patch.object(fixtures, 'jobs', return_value=synthetic):
            return fixture.exercise(terminal=False, **kwargs)

    def test_main_stops_before_telemetry_or_later_deadline_and_keeps_evidence(self):
        held = self.exercise(stats='watchdog')
        self.assertIsInstance(held.error, runner.RequiredAttemptFailure)
        self.assertEqual(1, len(held.samples))
        self.assertIsNone(held.samples[0]['docker_stats'])
        self.assertEqual('unable', held.result['primary_failure']['disposition'])
        self.assertEqual('samples.jsonl:1', held.result['primary_failure']['sample'])
        self.assertIn('RequiredAttemptFailure', held.result['failure'])
        self.assertFalse(held.result['terminal_both'])
        self.assertEqual(0, held.result['wall_seconds'])
        held.process_call.assert_not_called()
        self.assertGreater(held.stopped.call_count, 0)

    def test_containment_timeout_does_not_replace_primary_or_prevent_final_record(self):
        held = self.exercise(stop_error=TimeoutError('synthetic containment timeout'))
        self.assertIsInstance(held.error, runner.RequiredAttemptFailure)
        self.assertEqual('TimeoutError', held.result['serve_containment_failure'])
        self.assertEqual(['TimeoutError'], held.result['cleanup_failures'])
        self.assertIn('RequiredAttemptFailure', held.result['failure'])
        self.assertFalse(held.result['terminal_both'])

    def test_deadline_after_detection_is_secondary_and_primary_is_persisted(self):
        original = json.dumps
        def dump(value, *args, **kwargs):
            if isinstance(value, dict) and 'telemetry_skipped' in value:
                raise TimeoutError('synthetic watchdog after detection')
            return original(value, *args, **kwargs)
        with mock.patch.object(json, 'dumps', side_effect=dump):
            held = self.exercise()
        self.assertIsInstance(held.error, runner.RequiredAttemptFailure)
        self.assertEqual('TimeoutError', held.result['secondary_failure'])
        self.assertIn('RequiredAttemptFailure', held.result['failure'])
        self.assertEqual('unable', held.result['primary_failure']['disposition'])


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='w71879-147109-diagnostic-fixtures-'))
        print('Retained synthetic diagnostic fixtures:', cls.root, flush=True)

    def fixture(self, *, review=False, provider=None):
        root = self.root / str(len(list(self.root.iterdir())))
        failure = detect(FAILED)
        if review:
            failure['kind'] = 'review'
        output = 'logs' if review else 'proposal'
        path = root / 'storage' / 'line' / 'custody' / failure['attempt_id'] / output
        path.mkdir(parents=True)
        failure['artifacts'] = [{'output_name': output, 'artifact_id': failure['attempt_id'] + ':' + output, 'locator': path.as_uri()}]
        document = {'schema': 'baton.review-log/1' if review else 'baton.dogfood-proposal/2',
                    'task_id': INCARNATION + '-a', 'provider': provider or {'status': 1, 'failure_reason': 'api-error'},
                    'why': 'TOKEN-SENTINEL', 'stdout': 'TOKEN-SENTINEL', 'credential': 'TOKEN-SENTINEL'}
        report = path / ('review.json' if review else 'result.json')
        report.write_text(json.dumps(document))
        return root, failure, report

    def test_only_closed_reason_and_status_cross_report_boundary(self):
        for review in (False, True):
            root, failure, report = self.fixture(review=review)
            result = provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)
            self.assertEqual(('available', 'api-error', 1, 'unknown'), (result['availability'], result['provider_reason'], result['provider_exit_status'], result['authentication_cause']))
            self.assertNotIn('TOKEN-SENTINEL', json.dumps(result))

    def test_existing_timeout_start_error_and_unclassified_remain_distinct(self):
        for reason in ('timeout', 'start-error', 'unclassified'):
            root, failure, _ = self.fixture(provider={'status': None, 'failure_reason': reason})
            result = provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)
            self.assertEqual(reason, result['provider_reason'])
            self.assertEqual('unknown', result['authentication_cause'])

    def test_unknown_auth_spelling_and_untrusted_values_stay_unknown(self):
        for provider in ({'failure_reason': 'authentication_error', 'status': 1}, {'failure_reason': 'TOKEN-SENTINEL', 'status': 1}, {'failure_reason': 'api-error', 'status': 'TOKEN-SENTINEL'}):
            root, failure, _ = self.fixture(provider=provider)
            result = provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)
            self.assertEqual('unknown', result['provider_reason'])
            self.assertNotIn('TOKEN-SENTINEL', json.dumps(result))

    def test_missing_oversized_duplicate_malformed_or_wrong_task_is_unavailable(self):
        for content in ('{', '{"provider":{},"provider":{}}', 'x' * 65537, '{"schema":"baton.dogfood-proposal/2","task_id":"foreign"}'):
            root, failure, report = self.fixture(); report.write_text(content)
            self.assertEqual('unavailable', provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)['availability'])
        root, failure, report = self.fixture(); failure['artifacts'] = []
        self.assertEqual('unavailable', provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)['availability'])

    def test_foreign_artifact_and_symlink_reports_are_not_read(self):
        root, failure, report = self.fixture()
        failure['artifacts'][0]['artifact_id'] = 'foreign:proposal'
        with mock.patch('failure_observation._document', side_effect=AssertionError('must not read foreign locator')):
            self.assertEqual('unavailable', provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)['availability'])
        root, failure, report = self.fixture()
        private = root / 'credential-slot'; private.write_text('TOKEN-SENTINEL')
        # Preserve the ordinary fixture report; point a new custody directory
        # at private bytes via a symlink. No credential from a real run is read.
        alternate = root / 'storage' / 'another-line' / 'custody' / failure['attempt_id'] / 'proposal'; alternate.mkdir(parents=True)
        (alternate / report.name).symlink_to(private)
        failure['artifacts'][0]['locator'] = alternate.as_uri()
        self.assertEqual('unavailable', provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)['availability'])
        with mock.patch('failure_observation._document', side_effect=OSError('TOKEN-SENTINEL')):
            failure['artifacts'][0]['locator'] = report.parent.as_uri()
            self.assertNotIn('TOKEN-SENTINEL', json.dumps(provider_diagnostic(failure, run_root=root, incarnation=INCARNATION)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
