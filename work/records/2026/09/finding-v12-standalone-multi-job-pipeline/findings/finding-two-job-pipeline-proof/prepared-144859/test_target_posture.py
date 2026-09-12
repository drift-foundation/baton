"""Focused real-filesystem posture tests; no Git repository or model is run.

Compatible fixtures explicitly use this test process's uid/gid because managed
tests cannot assume chown privileges. Production defaults are separately checked
and the real run2 target is only read for its known wrong-group refusal.
Fixtures remain under the printed temporary root for inspection.
"""

import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import unittest
from unittest import mock

import target_posture as posture
import deployment

HERE = Path(__file__).resolve().parent


def snapshot(root):
    return {str(p.relative_to(root)): (p.lstat().st_uid, p.lstat().st_gid,
            stat.S_IMODE(p.lstat().st_mode), p.read_bytes() if p.is_file() else None)
            for p in [root, *sorted(root.rglob('*'))]}


class TargetPostureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained = Path(tempfile.mkdtemp(prefix='w71879-target-posture-144859-'))
        print('Retained fixture root:', cls.retained, flush=True)

    def setUp(self):
        self.run_root = self.retained / self._testMethodName
        self.target = self.run_root / 'target'
        for rel in ('', '.git', '.git/refs', '.git/refs/heads', '.git/objects', 'demo', 'tests'):
            place = self.target / rel
            place.mkdir(parents=True, exist_ok=True)
            place.chmod(0o2775)
        for rel in ('.git/HEAD', '.git/config', '.git/index', '.git/refs/heads/main'):
            place = self.target / rel
            place.write_text('metadata fixture; not a Git repository\n')
            place.chmod(0o664)
        for rel in posture.EXISTING:
            place = self.target / rel
            place.write_text('task permission fixture\n')
            place.chmod(0o644)
        self.identity = {'worker_uid': os.geteuid(), 'workspace_gid': os.getgid()}

    def check(self):
        return posture.check_target(self.target, **self.identity)

    def test_compatible_target_is_readonly(self):
        before = snapshot(self.run_root)
        self.assertEqual('compatible', self.check()['posture'])
        self.assertEqual(before, snapshot(self.run_root))
        self.assertEqual((65532, 1001), (posture.WORKER_UID, posture.WORKSPACE_GID))

    def test_wrong_group_refuses(self):
        before = snapshot(self.run_root)
        with self.assertRaisesRegex(posture.TargetPostureError, 'expected workspace gid'):
            posture.check_target(self.target, worker_uid=os.geteuid(), workspace_gid=os.getgid() + 1)
        self.assertEqual(before, snapshot(self.run_root))

    def test_wrong_owner_refuses_despite_group_access(self):
        with self.assertRaisesRegex(posture.TargetPostureError, 'expected fixed worker uid'):
            posture.check_target(self.target, worker_uid=os.geteuid() + 1, workspace_gid=os.getgid())

    def test_git_directory_requires_setgid(self):
        (self.target / '.git/refs').chmod(0o775)
        with self.assertRaisesRegex(posture.TargetPostureError, 'inheritance'):
            self.check()

    def test_root_requires_group_write(self):
        self.target.chmod(0o2755)
        with self.assertRaisesRegex(posture.TargetPostureError, 'required 0o2770'):
            self.check()

    def test_mutable_git_metadata_requires_group_write(self):
        (self.target / '.git/config').chmod(0o644)
        with self.assertRaisesRegex(posture.TargetPostureError, 'required 0o660'):
            self.check()

    def test_affected_file_requires_worker_exact_mode(self):
        (self.target / posture.EXISTING[0]).chmod(0o664)
        with self.assertRaisesRegex(posture.TargetPostureError, 'expected worker Git-mode representation 0o644'):
            self.check()

    def test_prepare_boundaries_refuse_before_git_or_state(self):
        before = snapshot(self.run_root)
        # This managed fixture is deliberately incompatible with production
        # defaults. No fake accepted execution marker is written to any package.
        self.assertNotEqual(1001, self.target.stat().st_gid)
        with mock.patch.object(deployment, 'RUN', self.run_root), \
                mock.patch.object(deployment, 'git_read', side_effect=AssertionError('Git reached before posture')), \
                mock.patch.object(deployment, 'bootstrap', side_effect=AssertionError('Authority reached before posture')):
            for operation in (deployment.prepare, deployment.validate, deployment.render, deployment.provision):
                with self.subTest(operation=operation.__name__):
                    with self.assertRaisesRegex(posture.TargetPostureError, 'expected workspace gid 1001'):
                        operation()
        self.assertEqual(before, snapshot(self.run_root))

    def test_run_refuses_before_submit_or_engine_command(self):
        spec = importlib.util.spec_from_file_location('w71879_run_guard_test', HERE / 'run.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        # Unit-only upstream gate answers let the actual baseline/posture
        # function run. No Authority, runtime, credential or real review exists.
        approval = {'verdict': 'accepted', 'review_locator': 'unit-only fixture',
                    'config_files': {'stage-execution.json': 'unit', 'submission.json': 'unit'},
                    'reviewed_files': {str(HERE / 'run.py'): 'unit', str(HERE / 'deployment.py'): 'unit', str(HERE / 'target_posture.py'): 'unit'}}
        before = snapshot(self.run_root)
        with mock.patch.object(Path, 'read_text', return_value=json.dumps(approval)), \
                mock.patch.object(runner, 'sha', return_value='unit'), \
                mock.patch.object(runner.os, 'getgroups', return_value=[1001]), \
                mock.patch.object(runner, 'RUN', self.run_root), \
                mock.patch.object(deployment, 'RUN', self.run_root), \
                mock.patch.object(runner, 'containers', return_value=[]), \
                mock.patch.object(runner, 'command', side_effect=AssertionError('submit/engine command reached')) as command:
            with self.assertRaisesRegex(posture.TargetPostureError, 'expected workspace gid 1001'):
                runner.main()
            command.assert_not_called()
        self.assertEqual(before, snapshot(self.run_root))

    def test_git_trust_is_exact_and_process_local(self):
        before = dict(os.environ)
        env = posture.manager_git_environment(self.target)
        self.assertEqual('1', env['GIT_CONFIG_COUNT'])
        self.assertEqual('safe.directory', env['GIT_CONFIG_KEY_0'])
        self.assertEqual(str(self.target), env['GIT_CONFIG_VALUE_0'])
        self.assertEqual(before, dict(os.environ))


if __name__ == '__main__':
    started = time.monotonic()
    outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TargetPostureTests))
    result = {'tests': outcome.testsRun, 'failures': len(outcome.failures), 'errors': len(outcome.errors),
              'wall_seconds': time.monotonic() - started, 'retained_fixture_root': str(TargetPostureTests.retained),
              'positive_fixture_identity': {'uid': os.geteuid(), 'gid': os.getgid()},
              'production_identity': {'uid': 65532, 'gid': 1001},
              'scope': 'real filesystem fixtures with explicit test uid/gid; production guard refusal before side effects; no actual fixed-uid runtime or model execution'}
    (HERE / 'evidence/focused-tests.json').write_text(json.dumps(result, indent=2) + '\n')
    sys.exit(0 if outcome.wasSuccessful() else 1)
