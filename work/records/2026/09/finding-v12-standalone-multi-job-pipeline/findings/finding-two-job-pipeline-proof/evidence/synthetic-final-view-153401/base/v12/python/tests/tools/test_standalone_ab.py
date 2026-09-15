"""Fast feedback for the synthetic provider; full Docker scenario is operator-run."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
HERE = REPO / 'v12/testing/standalone_ab'
spec = importlib.util.spec_from_file_location('synthetic_ab_provider', HERE / 'provider.py')
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


class SyntheticProvider(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-ab-unit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        shutil.copytree(HERE / 'fixtures/baseline', self.source)
        self.data = provider.fixture()

    def prompt(self, role):
        tasks = (role,) if role in ('a', 'b') else ('a', 'b')
        return ('[BATON-SYNTHETIC standalone-ab-v1 role=' + role + ']\n' +
                '\n'.join((HERE / ('fixtures/task-' + name + '.md')).read_text() for name in tasks) +
                '\nEdit files here directly.')

    def test_real_provider_subprocess_writes_only_A_scope_and_tests_pass(self):
        before = {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        done = subprocess.run([sys.executable, str(HERE / 'provider.py'), '--print',
            '--dangerously-skip-permissions', '--output-format', 'json', self.prompt('a')],
            cwd=self.source, capture_output=True, text=True, timeout=10)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn('SIMULATED', json.loads(done.stdout)['result'])
        after = {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        self.assertEqual({name for name in before if before[name] != after[name]}, set(self.data['a']))
        self.assertEqual(set(before), set(after))
        provider.verify(self.source, 'check_greeting.py')

    def test_B_check_fails_original_and_passes_isolated_and_merged(self):
        (self.source / 'check_hours.py').write_text(self.data['b']['check_hours.py'])
        with self.assertRaises(subprocess.CalledProcessError):
            provider.verify(self.source, 'check_hours.py')
        (self.source / 'check_hours.py').unlink()
        provider.answer(self.prompt('b'), self.source)
        provider.verify(self.source, 'check_hours.py')
        self.assertEqual((self.source / 'demo/greeting.py').read_text(), self.data['baseline']['demo/greeting.py'])
        for name, body in self.data['a'].items():
            (self.source / name).write_text(body)
        provider.verify(self.source, 'check_hours.py')
        provider.verify(self.source, 'check_greeting.py')

    def test_unknown_task_or_drift_refuses_before_writes(self):
        before = (self.source / 'demo/greeting.py').read_bytes()
        for prompt in ('unknown task', self.prompt('unknown'), self.prompt('approval')):
            with self.subTest(prompt=prompt), self.assertRaises(ValueError):
                provider.answer(prompt, self.source)
        (self.source / 'demo/units.py').write_text('foreign baseline\n')
        with self.assertRaisesRegex(ValueError, 'incompatible scenario tree'):
            provider.answer(self.prompt('a'), self.source)
        self.assertEqual((self.source / 'demo/greeting.py').read_bytes(), before)

    def test_original_review_checks_actual_tree_and_writes_ordinary_report(self):
        provider.answer(self.prompt('a'), self.source)
        room = self.root / 'review'
        room.mkdir()
        prompt = ('You are reviewing a change on a read-only source tree at ' + str(self.source) +
                  '. Do not modify anything.\n' + self.prompt('a') +
                  '\nWhen you are done, write your decision to review-report.json as a JSON object.')
        provider.answer(prompt, room)
        report = json.loads((room / 'review-report.json').read_text())
        self.assertEqual(report['schema'], 'baton.review-report/1')
        self.assertEqual(report['verdict'], 'accepted')
        self.assertIn('SIMULATED', report['findings'])
        (self.source / 'demo/greeting.py').write_text(self.data['baseline']['demo/greeting.py'])
        with self.assertRaises(ValueError):
            provider.answer(prompt, room)

    def test_derived_judges_bind_current_candidate_and_causal_checks(self):
        for changes in (self.data['a'], self.data['b']):
            for name, body in changes.items():
                (self.source / name).write_text(body)
        causal = {name: {'status': 1 if name == 'base' else 0,
                         'output': "ImportError: cannot import name 'hours_to_seconds'" if name == 'base' else 'passed',
                         'command': ['python3', 'check_hours.py'],
                         'test_digest': 'sha256:' + hashlib.sha256(self.data['b']['check_hours.py'].encode()).hexdigest()}
                  for name in ('base', 'isolated', 'combined')}
        actual = subprocess.run
        def run(argv, **options):
            if argv[0] == 'git':
                return subprocess.CompletedProcess(argv, 0, 'current-fixture-head\n', '')
            return actual(argv, **options)
        for role in ('verification', 'review', 'approval'):
            room = self.root / role
            room.mkdir()
            subject = {'kind': role, 'candidate': 'current-fixture-head', 'causal_observations': causal}
            (self.root / 'judgment.json').write_text(json.dumps(subject))
            prompt = ('You are reviewing a change on a read-only source tree at ' + str(self.source) +
                      '. Do not modify anything.\n' + self.prompt(role) +
                      '\nWhen you are done, write your decision to review-report.json as a JSON object.')
            with patch.object(subprocess, 'run', run):
                provider.answer(prompt, room)
                self.assertEqual(json.loads((room / 'review-report.json').read_text())['verdict'], 'accepted')
                subject['candidate'] = 'stale-head'
                (self.root / 'judgment.json').write_text(json.dumps(subject))
                with self.assertRaisesRegex(ValueError, 'candidate differs'):
                    provider.answer(prompt, room)

    def test_integration_copies_exact_blobs_and_reports_current_operands(self):
        module_spec = importlib.util.spec_from_file_location('integration_contract', REPO / 'v12/worker/integration_contract.py')
        contract = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(contract)
        bundle = self.root / 'bundle'
        (bundle / 'blobs').mkdir(parents=True)
        rows = []
        for name, body in self.data['a'].items():
            blob = hashlib.sha256(body.encode()).hexdigest()
            (bundle / 'blobs' / blob).write_text(body)
            rows.append({'path': name, 'operation': 'edit', 'candidate': {'mode': '100644', 'blob': blob}})
        report = self.root / 'integration-report.json'
        assignment, digest = 'sha256:' + '1' * 64, 'sha256:' + '2' * 64
        prompt = (self.prompt('integrator') + '\nThe approved evidence bundle is mounted read-only at ' + str(bundle) +
                  '.\nThe target is ' + str(self.source) + ' and it is the only tree you may change.\n' +
                  'Write your bounded baton.integration-report/1 report to ' + str(report) + ' and write no other file.\n' +
                  'The assignment it answers is ' + assignment + '.\nIts measured identity is ' + digest + '.')
        # Unit scope supplies a parsed bundle; production read_bundle and the
        # workload still validate real bundles in the full container scenario.
        with patch.dict(sys.modules, {'integration_contract': contract}), patch.object(contract, 'read_bundle', return_value={'envelope': {'paths': rows}}):
            provider.answer(prompt, self.root)
        taken = json.loads(report.read_text())
        self.assertEqual(taken['assignment_digest'], assignment)
        self.assertEqual(taken['bundle_digest'], digest)
        self.assertEqual(taken['paths'], sorted(self.data['a']))
        self.assertEqual(taken['verification']['status'], 0)
        contract.check_report(report.read_bytes())
        self.assertEqual((self.source / 'demo/units.py').read_text(), self.data['baseline']['demo/units.py'])

    def test_rendered_configuration_is_real_isolated_and_networkless(self):
        settings = {'authority_uuid': 'ab123456000000000000000000000001', 'base': 'a' * 40,
                    'tree': 'b' * 40, 'created_at': '2026-09-12T15:00:00.000Z',
                    'provider_base': 'sha256:' + 'c' * 64,
                    'images': {'provider': 'sha256:' + 'd' * 64, 'integration': 'sha256:' + 'e' * 64}}
        (self.root / 'settings.json').write_text(json.dumps(settings))
        (self.root / 'image-context-manifest.json').write_text('{}\n')
        script = '''import json,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import deployment as d
facts=d.bootstrap(d.RUN/'authority.sqlite3')
d.CONFIG.mkdir()
d.documents(d.CONFIG,d.SETTINGS['images'],facts)
print(d.CONFIG)
'''
        done = subprocess.run([sys.executable, '-c', script, str(HERE)], cwd=REPO / 'v12/python',
            env=dict(os.environ, BATON_AB_RUN_ROOT=str(self.root), PYTHONPATH='src:.', PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, timeout=15)
        self.assertEqual(done.returncode, 0, done.stderr)
        config = json.loads((self.root / 'config/stage-execution.json').read_text())
        self.assertEqual(config['authority_uuid'], settings['authority_uuid'])
        workers = [one['deployment'] for one in config['workers']]
        workers += [one['deployment'] for one in config['result_judgment_workers']['job-b'].values()]
        self.assertEqual(len(workers), 8)
        self.assertTrue(all(one['network'] == 'none' for one in workers))
        self.assertTrue(all(one['credential_sources'] == str(self.root / 'credential-sources.json') for one in workers))
        submission = json.loads((self.root / 'config/submission.json').read_text())
        self.assertEqual(submission['submission_id'], settings['authority_uuid'])
        self.assertEqual({one['job_id'] for one in submission['jobs']}, {'job-a', 'job-b'})


if __name__ == '__main__':
    unittest.main()
