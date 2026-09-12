"""Bounded deployment checks; synthetic observations are not integration proof.

Real prompt, Git read/witness, CLI parsing, observation factory and projection.
No serving factory, real-run store, provider, Git history/index mutation or retry.
"""
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import deployment
from offline_fixture import documents_in_fixture
import run as runner
import integration_workload as workload
from tools import job_manager, stage_execution
from baton_v12.job_manager import projection
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager.workspaces import configure_workspace_group
import test_stats_observation as fixtures

HERE = Path(__file__).resolve().parent


class ObservedStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='w71879-152826-correction-fixtures-'))
        print('Retained bounded correction fixtures:', cls.root, flush=True)
        (cls.root / 'OFFLINE-ONLY.txt').write_text('Synthetic inputs and copied Git source. Not actual run10 inputs, provider attribution, owner settlement or host state.\n')
        facts = {'authority_uuid': deployment.UUID, 'policy_generation': 24,
                 'principals': {actor: 'principal:w71879-run10-' + actor for actor in deployment.ACTORS},
                 'fixture_scope': 'synthetic constructor parameters only'}
        cls.config = cls.root / 'documents'
        documents_in_fixture(cls.config, json.loads((HERE / 'offline-images.json').read_text()), facts)
        cls.instructions = (cls.config / 'integration-instructions.txt').read_bytes()
        cls.prompt = workload.compose_prompt(instructions=cls.instructions, bundle_root='/input/source',
            target_root='/target', report_place='/tmp/SYNTHETIC-report.json',
            assignment={'attempt_id': 'synthetic', 'canonical_target_id': 'synthetic-target', 'entry_id': 'synthetic-entry', 'fence': 1},
            assignment_digest='sha256:' + 'a' * 64, bundle_digest='sha256:' + 'b' * 64, rows=[], authority=[], scope=[], documents=[])
        (cls.root / 'SYNTHETIC-prompt.txt').write_text(cls.prompt)

    def test_real_prompt_preserves_contract_and_adds_explicit_safe_git_reads(self):
        prior = (HERE.parent / 'prepared-146538/frozen-config/integration-instructions.txt').read_bytes()
        self.assertTrue(self.instructions.startswith(prior))
        self.assertIn('every Git read must use git --no-optional-locks', self.prompt)
        self.assertIn('git --no-optional-locks status --porcelain', self.prompt)
        self.assertIn('refresh the index even when nothing is staged', self.prompt)
        self.assertIn('do not stage, commit, reset', self.prompt)
        self.assertIn('repair the index', self.prompt)
        self.assertIn('Do not change version-control state in any way', self.prompt)
        self.assertIn('end the provider turn', self.prompt)
        self.assertIn('baton.integration-report/1', self.prompt)

    def test_instructed_git_reads_preserve_real_repository_witness(self):
        # Copy ordinary existing source files without using git init/clone,
        # staging or any mutable Git operation. Never touch a real run target.
        source = Path('/home/sl/.local/state/baton/v12/w71879-run1/source')  # Original retained baseline; fresh run10 does not exist.
        target = self.root / 'copied-source'
        shutil.copytree(source, target)
        index_before = (target / '.git/index').read_bytes()
        with (target / 'demo/greeting.py').open('a') as stream:
            stream.write('\n# Offline worktree edit to require an actual status/diff observation.\n')
        holder = os.open(target, os.O_RDONLY | os.O_DIRECTORY)
        try:
            before = workload._repository_witness(holder)
            outputs = []
            for args in (['status', '--porcelain'], ['diff', '--', 'demo/greeting.py']):
                argv = ['git', '--no-optional-locks', '-c', 'safe.directory=' + str(target), '-C', str(target), *args]
                result = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=True)
                self.assertTrue(result.stdout)
                outputs.append({'argv': argv, 'stdout': result.stdout, 'status': result.returncode})
            self.assertEqual(before, workload._repository_witness(holder))
            self.assertEqual(index_before, (target / '.git/index').read_bytes())
            (self.root / 'safe-read-witness.json').write_text(json.dumps({'scope': 'copied offline fixture only; not writer attribution', 'witness_unchanged': True, 'index_sha256': hashlib.sha256(index_before).hexdigest(), 'reads': outputs}, indent=2))
        finally:
            os.close(holder)

    def test_actual_status_command_parses_observer_and_exact_config(self):
        argv = runner.STATUS
        self.assertEqual('/usr/bin/env', argv[0])
        self.assertIn('BATON_V12_STAGE_EXECUTION_CONFIG=' + str(runner.CONFIG / 'stage-execution.json'), argv)
        self.assertNotIn('--operations', argv)
        self.assertEqual('tools.stage_execution:observing_factory', argv[argv.index('--observe') + 1])
        with mock.patch.object(job_manager, '_status', return_value=0) as observed:
            job_manager.main(argv[argv.index('tools.job_manager') + 1:], stream=io.StringIO())
        taken = observed.call_args.args[0]
        self.assertEqual(str(runner.RUN / 'control.sqlite3'), taken.control)
        self.assertEqual('tools.stage_execution:observing_factory', taken.observe)
        self.assertEqual(str(runner.RUN / 'jobs.sqlite3'), taken.store)
        self.assertEqual('w71879-run10', taken.incarnation)

    def test_selected_real_factory_loads_config_and_has_no_serving_actions(self):
        name = runner.STATUS[runner.STATUS.index('--observe') + 1]
        # Same environment key, a labelled temporary config value; all real
        # configuration and source-nomination validators remain active.
        # Explicit fixture group only, with no workspace allocation or host
        # posture claim. Use the public control owner, never a raw store row.
        control = ControlStore.open(str(self.root / 'observer-control.sqlite3'), incarnation='offline-observer', clock=lambda: '2026-09-11T19:30:01.000Z')
        self.addCleanup(control.close)
        self.assertNotEqual(0, os.getgid())
        configure_workspace_group(control, os.getgid())
        with mock.patch.dict(os.environ, {stage_execution.CONFIG_ENV: str(self.config / 'stage-execution.json')}), ExitStack() as guards:
            for owner, method in ((stage_execution, 'factory'), (stage_execution, 'operations_from'),
                                  (stage_execution.Authority, 'open'), (stage_execution.Authority, 'session'),
                                  (stage_execution.scheduler, 'activate_pool')):
                guards.enter_context(mock.patch.object(owner, method, side_effect=AssertionError('observer reached serving ' + method)))
            reader = job_manager._observation_from(name, object(), control)
            self.assertIsInstance(reader, stage_execution.StageObservation)
            self.assertEqual(deployment.UUID, reader.given['authority_uuid'])
            self.assertIsNone(reader.observe_integration({'kind': 'implementation'}))
            for act in ('launch', 'dispatch', 'conclude', 'claim', 'refresh_runtime', 'recover'):
                self.assertIsNone(getattr(reader, act, None))

    def test_real_projection_distinguishes_completed_held_and_answered(self):
        for account, state in (('completed', 'completed'), ('held', 'exceptional'), ('answered', 'answering')):
            with self.subTest(account=account):
                # Labelled synthetic owner-account inputs, real projection.
                self.assertEqual(state, projection._integrating({'state': account}, {'execution_runtime': 'quiescent', 'runtime_id': 'synthetic-runtime'}))

    def test_held_projection_never_satisfies_actual_runner_terminal_criterion(self):
        fixture = fixtures.RunnerTests('test_incomplete_jobs_do_not_become_terminal_from_gap')
        if not hasattr(fixtures.RunnerTests, 'retained'):
            fixtures.RunnerTests.setUpClass()
        held_state = projection._integrating({'state': 'held'}, {'execution_runtime': 'quiescent'})
        original_jobs = fixtures.jobs
        def held_jobs(_state):
            result = original_jobs('completed')
            result['jobs'][0]['stages'][-1]['state'] = held_state
            return result
        with mock.patch.object(fixtures, 'jobs', side_effect=held_jobs):
            result = fixture.exercise(terminal=False)
        self.assertIsNotNone(result.error)
        self.assertFalse(result.result['terminal_both'])
        self.assertTrue(result.samples)
        self.assertEqual('exceptional', result.samples[0]['status']['jobs'][0]['stages'][-1]['state'])
        self.assertGreater(result.stopped.call_count, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
