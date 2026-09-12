"""Fresh identities and preserved accepted behavior; no host or model execution."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import deployment
from offline_fixture import documents_in_fixture
import run as runner

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'prepared-149854'
CREATED = '2026-09-12T04:59:54.280Z'
RULING = 'M141636/return150004; run9 preparation and exactly one operator attempt after required input checks and genuine execution bindings authorized; no agent model execution or automatic retry'


class Run9PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='w71879-150007-public-bootstrap-'))
        print('Retained offline public bootstrap:', cls.root, flush=True)
        (cls.root / 'OFFLINE-ONLY.txt').write_text('Public bootstrap/schema tests only. Not host validation or execution.\n')
        cls.facts = deployment.bootstrap(cls.root / 'authority.sqlite3')
        cls.config = cls.root / 'documents'
        cls.hashes = documents_in_fixture(cls.config, json.loads((HERE / 'offline-images.json').read_text()), cls.facts)

    def test_public_bootstrap_and_all_execution_bindings_use_fresh_namespace(self):
        self.assertEqual('c71879b3000000000000000000000001', self.facts['authority_uuid'])
        self.assertEqual(24, self.facts['policy_generation'])
        self.assertEqual(9, len(self.facts['principals']))
        for actor, principal in self.facts['principals'].items():
            self.assertEqual('principal:w71879-run9-' + actor, principal)
        self.assertEqual({name: 'c71879b3-W' + str(i) for i, name in enumerate(('a', 'b', 'verification', 'review', 'approval'), 1)}, deployment.WORKS)
        config = json.loads((self.config / 'stage-execution.json').read_text())
        self.assertEqual('/home/sl/.local/state/baton/v12/w71879-run9', str(deployment.RUN))
        self.assertEqual(str(self.root / 'offline-run/target'), config['integration_target'])
        self.assertEqual(str(self.root / 'offline-run/integration-workspace'), config['integration_workspace'])
        self.assertEqual('w71879-run9', json.loads((self.config / 'submission.json').read_text())['submission_id'])
        self.assertEqual(8, len(list((self.config / 'workers').glob('*.json'))))
        for path in self.config.rglob('*'):
            if path.is_file():
                self.assertNotIn('w71879-run8', path.read_text())
                self.assertNotIn('c71879b2', path.read_text())
        for argv in (runner.PREFIX, runner.SERVE, runner.STATUS):
            self.assertEqual('w71879-run9', argv[argv.index('--incarnation') + 1])
        self.assertEqual(CREATED, deployment.CREATED)

    def test_tasks_policies_and_report_contract_preserve_accepted_behavior(self):
        for name, task in deployment.task_documents().items():
            old = json.loads((PRIOR / 'tasks' / (name + '.json')).read_text())
            old['task_id'] = old['task_id'].replace('run8', 'run9')
            self.assertEqual(old, task)
            self.assertEqual(task, json.loads((HERE / 'tasks' / (name + '.json')).read_text()))
        for name, policy in deployment.policy_documents().items():
            old = json.loads((PRIOR / 'policies' / (name + '.json')).read_text().replace('w71879-run8', 'w71879-run9'))
            if name == 'policy': old['ruling'] = RULING
            self.assertEqual(old, policy)
            self.assertEqual(policy, json.loads((HERE / 'policies' / (name + '.json')).read_text()))
        instructions = (self.config / 'integration-instructions.txt').read_bytes()
        self.assertEqual('4b3160e825f6d4f166fc5fc8477f8d85f3190420ba402dcfb780f01df7be9f76', hashlib.sha256(instructions).hexdigest())
        self.assertEqual((PRIOR / 'candidate-images.json').read_bytes(), (HERE / 'offline-images.json').read_bytes())

    def test_deployment_runner_and_all_four_helpers_preserve_accepted_behavior(self):
        old = (PRIOR / 'deployment.py').read_text()
        expected = old.replace('run8', 'run9').replace('c71879b2000000000000000000000001', 'c71879b3000000000000000000000001').replace('2026-09-12T03:32:20.835Z', CREATED).replace('M141636/return149484; run9 preparation and exactly one operator attempt after independent input review authorized; no agent model execution or automatic retry', RULING).replace('w71879-149488-validation-', 'w71879-150007-validation-')
        self.assertEqual(expected, (HERE / 'deployment.py').read_text())
        expected_runner = (PRIOR / 'run.py').read_text().replace('w71879-run8', 'w71879-run9')

        self.assertEqual(expected_runner, (HERE.parent / 'prepared-150007/run.py').read_text())
        self.assertIn('evaluate(claims, exclusions', (HERE / 'run.py').read_text())
        for name in ('target_posture.py', 'failure_observation.py', 'test_provider_detail.py'):
            self.assertEqual((PRIOR / name).read_bytes(), (HERE / name).read_bytes())
        self.assertIn("(HERE / 'run.py', HERE / 'deployment.py', HERE / 'target_posture.py', HERE / 'failure_observation.py', HERE / 'accounting.py')", (HERE / 'run.py').read_text())

    def test_operator_recipe_preserves_fresh_only_guards_and_fixed_host_posture(self):
        expected = (PRIOR / 'operator-prepare.sh').read_text().replace('run8', 'run9').replace('prepared-149488/target_posture.py', 'prepared-150007/target_posture.py')
        self.assertEqual(expected, (HERE / 'operator-prepare.sh').read_text())
        for guard in ('test ! -e "$run9_root"', 'test ! -L "$run9_root"', '65532:1001', 'chmod 0644', 'git clone --no-hardlinks', 'w71879-run1/source'):
            self.assertIn(guard, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
