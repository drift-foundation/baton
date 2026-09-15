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


def load_helper(name):
    selected = importlib.util.spec_from_file_location('synthetic_ab_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(selected)
    selected.loader.exec_module(module)
    return module


class FinalCommittedView(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-final-view-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / 'target'
        shutil.copytree(HERE / 'fixtures/baseline', self.target)
        self.helper = load_helper('final_view')
        self.git('init', '-b', 'main')
        self.git('add', '.')
        self.git('commit', '-m', 'baseline')
        original_index = (self.target / '.git/index').read_bytes()
        self.data = provider.fixture()
        for changes in (self.data['a'], self.data['b']):
            for name, body in changes.items():
                (self.target / name).write_text(body)
        self.git('add', '.')
        self.git('commit', '-m', 'committed A and B')
        self.commit = self.git('rev-parse', 'HEAD').strip()
        # Model ref-only import: the commit is current while checkout/index
        # still reflect the earlier A file import. Only this disposable fixture.
        for name, body in self.data['baseline'].items():
            (self.target / name).write_text(self.data['a'].get(name, body))
        for name in self.data['b']:
            if name not in self.data['baseline']:
                (self.target / name).unlink()
        (self.target / '.git/index').write_bytes(original_index)
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()

    def git(self, *args):
        done = subprocess.run(['git', '--no-optional-locks', '-C', str(self.target),
            '-c', 'user.name=Synthetic test', '-c', 'user.email=test@baton.invalid',
            '-c', 'core.hooksPath=/dev/null', *args], capture_output=True, text=True,
            env=dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null'), timeout=10)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    @staticmethod
    def persist(path, value):
        path.write_text(json.dumps(value))

    def test_committed_A_B_tests_run_and_stale_checkout_is_preserved(self):
        before = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.assertFalse((self.target / 'check_hours.py').exists())
        result = self.helper.verify_view(self.target, self.root / 'final-view', self.evidence,
            expected_commit=self.commit, timeout=lambda: 10, persist=self.persist)
        self.assertEqual(result['commit'], self.commit)
        self.assertEqual(result['tree'], self.git('rev-parse', 'HEAD^{tree}').strip())
        self.assertTrue(result['clean'])
        self.assertEqual([one['status'] for one in result['checks']], [0, 0, 0])
        self.assertIn('test_hours', (self.evidence / 'final-tests.log').read_text())
        self.assertIn('test_empty', (self.evidence / 'final-tests.log').read_text())
        self.assertEqual(before, {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob('*') if p.is_file()})

    def test_foreign_canonical_commit_refuses_before_export(self):
        view = self.root / 'foreign-view'
        with self.assertRaisesRegex(RuntimeError, 'Authority canonical target'):
            self.helper.committed_view(self.target, view, expected_commit='0' * 40, timeout=lambda: 10)
        self.assertFalse(view.exists())

    def test_verification_mutation_cannot_be_called_clean(self):
        actual = subprocess.run
        def run(argv, **options):
            answer = actual(argv, **options)
            if argv[0] == 'python3':
                (Path(options['cwd']) / 'uncommitted.txt').write_text('unexpected test output')
            return answer
        with patch.object(subprocess, 'run', run), self.assertRaisesRegex(RuntimeError, 'changed the committed view'):
            self.helper.verify_view(self.target, self.root / 'final-view', self.evidence,
                expected_commit=self.commit, timeout=lambda: 10, persist=self.persist)
        self.assertFalse(json.loads((self.evidence / 'final-view.json').read_text())['clean'])


class ScenarioEarlyFailures(unittest.TestCase):
    def test_disk_default_preflight_precedes_build_and_records_refusal(self):
        scenario = load_helper('scenario')
        from baton_v12.contracts import ContractRefusal
        with tempfile.TemporaryDirectory(prefix='synthetic-root-test-') as home:
            with patch.object(Path, 'home', return_value=Path(home)), patch.object(os, 'getgroups', return_value=[1001]), \
                    patch.object(sys, 'argv', ['scenario.py']), patch.object(scenario, 'images') as build, \
                    patch('baton_v12.worker_manager.source_boundary.check_disk_backed', side_effect=ContractRefusal('policy', 'denied', 'tmpfs refuses')):
                with self.assertRaises(ContractRefusal):
                    scenario.main()
            build.assert_not_called()
            [root] = (Path(home) / '.local/state/baton/v12').iterdir()
            recorded = json.loads((root / 'scenario-result.json').read_text())
            self.assertIn('tmpfs refuses', recorded['failure'])
            self.assertFalse(recorded['live_provider'])
            self.assertFalse((root / 'authority.sqlite3').exists())

    def test_preparation_and_start_failures_need_exact_current_assignment(self):
        import copy
        failure = load_helper('failure_observation')
        fixed = {'generation': 1, 'participant': 'worker-a', 'work_ref': {'authority_uuid': 'authority', 'work_id': 'work-a'}}
        stage = {'kind': 'implementation', 'job_id': 'job-a', 'stage_id': 'job-a/implementation', 'work_id': 'work-a',
                 'attempt_id': 'attempt-current', 'episode': 1,
                 'runtime': {'runtime_id': None, 'assignment': fixed},
                 'allocation': {'assignment_id': 'attempt-current', 'stage_id': 'job-a/implementation', 'episode': 1, 'participant': 'worker-a'},
                 'receipts': [{'act': 'claim', 'state': 'performed', 'episode': 1, 'stage_id': 'job-a/implementation', 'detail': {'result': {'assignment': fixed}}}],
                 'episodes': [{'attempt_id': 'attempt-current', 'episode': 1, 'incarnation': 'run', 'ended_at': None}]}
        status = {'observed_at': '2026-09-12T15:00:00.000Z', 'jobs': [{'job_id': 'job-a', 'submission_id': 'run', 'stages': [stage]}]}
        owned = {'attempt_id': 'attempt-current', 'expect': fixed, 'runtime_id': None,
                 'failure': {'category': 'policy', 'code': 'denied', 'message': 'disk-backed workspace required'}}
        for member, ending in [('attempt_preparation_failure_of', 'preparation-failed'), ('attempt_start_failure_of', 'start-failed')]:
            with patch.object(failure, 'attempt_preparation_failure_of', return_value=None), patch.object(failure, 'attempt_start_failure_of', return_value=None):
                with patch.object(failure, member, return_value=owned):
                    found = failure._first_failure(status, authority_uuid='authority', incarnation='run', works={'a': 'work-a'}, control=object())
                self.assertEqual(found['ending'], ending)
                self.assertEqual(found['owner_failure'], owned)
                self.assertIsNone(found['runtime_id'])
                foreign = copy.deepcopy(owned)
                foreign['expect']['generation'] = 2
                with patch.object(failure, member, return_value=foreign):
                    self.assertIsNone(failure._first_failure(status, authority_uuid='authority', incarnation='run', works={'a': 'work-a'}, control=object()))
                stale = copy.deepcopy(status)
                stale['jobs'][0]['stages'][0]['episodes'][0]['ended_at'] = 'ended'
                with patch.object(failure, member, return_value=owned):
                    self.assertIsNone(failure._first_failure(stale, authority_uuid='authority', incarnation='run', works={'a': 'work-a'}, control=object()))


if __name__ == '__main__':
    unittest.main()
