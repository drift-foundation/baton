"""Fresh run5 packaging checks through public bootstrap and real constructors.

Temporary Authority facts are real offline preparation observations, never
production state, model reports, host posture or terminal acceptance evidence.
"""
import ast
import json
from pathlib import Path
import tempfile
import unittest

import deployment
from offline_fixture import documents_in_fixture
import run as runner

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'prepared-145615'
CREATED = '2026-09-11T18:51:56.074Z'
RULING = 'M141636/return146531; run5 preparation authorized; model execution not authorized'


class Run5PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='w71879-146538-public-bootstrap-'))
        print('Retained offline public bootstrap:', cls.root, flush=True)
        (cls.root / 'OFFLINE-ONLY.txt').write_text('Public bootstrap and real document schemas only. Not host validation or model execution.\n')
        cls.facts = deployment.bootstrap(cls.root / 'authority.sqlite3')
        cls.config = cls.root / 'documents'
        cls.hashes = documents_in_fixture(cls.config, json.loads((HERE / 'candidate-images.json').read_text()), cls.facts)

    def test_public_bootstrap_and_all_execution_bindings_use_fresh_namespace(self):
        self.assertEqual('c71879af000000000000000000000001', self.facts['authority_uuid'])
        self.assertEqual(24, self.facts['policy_generation'])
        self.assertEqual(9, len(self.facts['principals']))
        for actor, principal in self.facts['principals'].items():
            self.assertEqual('principal:w71879-run5-' + actor, principal)
        self.assertEqual({name: 'c71879af-W' + str(i) for i, name in enumerate(('a', 'b', 'verification', 'review', 'approval'), 1)}, deployment.WORKS)
        config = json.loads((self.config / 'stage-execution.json').read_text())
        self.assertEqual('/home/sl/.local/state/baton/v12/w71879-run5', str(deployment.RUN))
        self.assertEqual(str(self.root / 'offline-run/target'), config['integration_target'])
        self.assertEqual(str(self.root / 'offline-run/integration-workspace'), config['integration_workspace'])
        self.assertEqual('w71879-run5', json.loads((self.config / 'submission.json').read_text())['submission_id'])
        self.assertEqual(8, len(list((self.config / 'workers').glob('*.json'))))
        for path in self.config.rglob('*'):
            if path.is_file():
                text = path.read_text()
                self.assertNotIn('w71879-run4', text)
                self.assertNotIn('c71879ae', text)
        for argv in (runner.PREFIX, runner.SERVE):
            self.assertEqual('w71879-run5', argv[argv.index('--incarnation') + 1])
        self.assertEqual(CREATED, deployment.CREATED)

    def test_tasks_policies_images_and_report_contract_preserve_accepted_behavior(self):
        for name, task in deployment.task_documents().items():
            old = json.loads((PRIOR / 'tasks' / (name + '.json')).read_text())
            old['task_id'] = old['task_id'].replace('run4', 'run5')
            self.assertEqual(old, task)
            self.assertEqual(task, json.loads((HERE / 'tasks' / (name + '.json')).read_text()))
        for name, policy in deployment.policy_documents().items():
            old = json.loads((PRIOR / 'policies' / (name + '.json')).read_text().replace('w71879-run4', 'w71879-run5'))
            if name == 'policy':
                old['ruling'] = RULING
            self.assertEqual(old, policy)
            self.assertEqual(policy, json.loads((HERE / 'policies' / (name + '.json')).read_text()))
        self.assertEqual((PRIOR / 'evidence/generated-integration-instructions.txt').read_bytes(), (self.config / 'integration-instructions.txt').read_bytes())
        for name in ('candidate-images.json', 'image-context-manifest.json', 'target_posture.py', 'test_stats_observation.py'):
            self.assertEqual((PRIOR / name).read_bytes(), (HERE / name).read_bytes())

    def test_deployment_and_runner_differ_only_in_scheduled_identity_metadata(self):
        old = (PRIOR / 'deployment.py').read_text()
        expected = old.replace('run4', 'run5').replace('c71879ae000000000000000000000001', 'c71879af000000000000000000000001').replace('2026-09-11T15:06:04.000Z', CREATED).replace('M141636/return145258; another model run not yet authorized', RULING).replace('w71879-145261-validation-', 'w71879-146538-validation-')
        self.assertEqual(ast.dump(ast.parse(expected)), ast.dump(ast.parse((HERE / 'deployment.py').read_text())))
        self.assertEqual((PRIOR / 'run.py').read_text().replace('w71879-run4', 'w71879-run5'), (HERE / 'run.py').read_text())

    def test_operator_recipe_preserves_fresh_only_guards_and_fixed_host_posture(self):
        expected = (PRIOR / 'operator-prepare.sh').read_text().replace('run4', 'run5').replace('prepared-145261/target_posture.py', 'prepared-146538/target_posture.py')
        self.assertEqual(expected, (HERE / 'operator-prepare.sh').read_text())
        self.assertIn('test ! -e "$run5_root"', expected)
        self.assertIn('test ! -L "$run5_root"', expected)
        self.assertIn('65532:1001', expected)
        self.assertIn('chmod 0644', expected)
        self.assertIn('git clone --no-hardlinks', expected)
        self.assertIn('w71879-run1/source', expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
