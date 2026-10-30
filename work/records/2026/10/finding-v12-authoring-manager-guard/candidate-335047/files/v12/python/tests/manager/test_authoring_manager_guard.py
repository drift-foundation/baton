"""Real process/composer/guard regression; workload and engine are deterministic.

The fixture replaces packet/image validation and the baseline workload (not the
manager composition). Guard, child_main, child_compose, operations_from,
worker_preflight, Authority, stores and the workspace guard are real.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest

from tests.tools.test_stage_execution import ServingCase


class ManagerComposition(ServingCase):
    def prepare(self, mode='normal'):
        root = Path(self.root)
        config = self.composed_document()
        # Credential bytes are never read: replace only the external provider.
        for worker in config['workers']:
            worker['deployment']['credential_sources'] = str(root / 'unused-registry')
        (root / 'config.json').write_text(json.dumps(config))
        value = {'schema': 'baton.single-implementation-packet/2', 'context': {'mode': 'fresh'}, 'run_id': 'guard-regression', 'submission': {'job_id': 'job-a'},
                 'deployment': {'authority_uuid': config['authority_uuid'],
                                'control_store': self.control_path, 'job_store': self.job_path,
                                'config_path': str(root / 'config.json')},
                 'code_boundary': self.checkout, 'outcome_path': str(root / 'outcome.json'),
                 'bounds': {'total_seconds': 5, 'cleanup_seconds': 2, 'turn_seconds': 3,
                            'implementer_invocations': 1, 'retry': False},
                 'test_mode': mode, 'test_submission': self.submission}
        (root / 'packet.json').write_text(json.dumps(value))
        return root

    def launch(self, root, *extra):
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(Path(__file__).resolve().parents[2] / 'src'), str(Path(__file__).resolve().parents[2])]), PYTHONDONTWRITEBYTECODE='1')
        output = open(root / ('outer-' + str(time.time_ns()) + '.log'), 'w+')
        child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--packet', str(root / 'packet.json'), *extra], env=env, stdout=output, stderr=subprocess.STDOUT)
        self.addCleanup(output.close)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        return child, output

    def await_file(self, path, child, output):
        deadline = time.monotonic() + 8
        while not path.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(.025)
        output.flush(); output.seek(0)
        self.assertTrue(path.exists(), self.log(output))

    def test_real_composition_admits_action_and_restart_never_reinvokes(self):
        root = self.prepare()
        child, output = self.launch(root)
        self.assertEqual(child.wait(timeout=12), 1, self.log(output))
        report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
        self.assertEqual(report['child_status'], 0)
        self.assertTrue(report['author_invocation_started'])
        self.assertEqual(report['state'], 'held')  # admitted-only is not completed output
        action = json.loads((root / 'action.json').read_text())
        self.assertTrue(action['admitted'], action)
        self.assertNotEqual(action['pid'], os.getpid())
        self.assertEqual(action['guard_pid'], action['pid'])
        first = (root / 'action.json').read_bytes()
        replay, out = self.launch(root)
        self.assertEqual(replay.wait(timeout=12), 1, self.log(out))
        self.assertEqual(first, (root / 'action.json').read_bytes())
        reports = list(root.glob('outcome.json.enforcement-*.json'))
        self.assertEqual(len(reports), 2)
        recovery = next(json.loads(p.read_text()) for p in reports if json.loads(p.read_text())['recovery_only'])
        self.assertFalse(recovery['author_invocation_started'])

    def test_blocked_author_keeps_exclusion_and_outer_deadline(self):
        root = self.prepare('blocked')
        child, output = self.launch(root)
        self.await_file(root / 'action.json', child, output)
        duplicate, dupout = self.launch(root)
        self.assertNotEqual(duplicate.wait(timeout=8), 0)
        self.assertIn('BlockingIOError', self.log(dupout))
        competitor, compout = self.launch(root, '--competitor')
        self.assertEqual(competitor.wait(timeout=8), 0, self.log(compout))
        self.assertIn('competitor refused', self.log(compout))
        self.assertEqual(child.wait(timeout=12), 1, self.log(output))
        self.assertTrue((root / 'partial.txt').exists())
        report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
        self.assertTrue(report['child_exited'])
        self.assertLess(report['elapsed_seconds'], 8)
        after, afterout = self.launch(root, '--guard-after')
        self.assertEqual(after.wait(timeout=8), 0, self.log(afterout))

    def test_author_exception_releases_process_guard_and_preserves_failure(self):
        root = self.prepare('exception')
        child, output = self.launch(root)
        self.assertEqual(child.wait(timeout=12), 1, self.log(output))
        self.assertTrue((root / 'action.json').exists(), self.log(output))
        after, out = self.launch(root, '--guard-after')
        self.assertEqual(after.wait(timeout=8), 0, self.log(out))
        report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
        self.assertEqual(report['state'], 'held')

    def test_parent_loss_kills_manager_without_inherited_workspace_guard(self):
        root = self.prepare('blocked')
        child, output = self.launch(root)
        self.await_file(root / 'action.json', child, output)
        child.kill(); child.wait(timeout=3)
        # Child PDEATHSIG releases its process-owned workspace guard; no
        # controller snapshot is upgraded into runtime cessation evidence.
        deadline = time.monotonic() + 5
        while True:
            after, out = self.launch(root, '--guard-after')
            code = after.wait(timeout=3)
            if code == 0 or time.monotonic() > deadline:
                break
            time.sleep(.05)
        self.assertEqual(code, 0, self.log(out))
        first = (root / 'action.json').read_bytes()
        recovery, out = self.launch(root)
        self.assertEqual(recovery.wait(timeout=12), 1, self.log(out))
        self.assertEqual(first, (root / 'action.json').read_bytes())

    def test_manager_loss_retains_unknown_and_restart_does_not_repeat(self):
        root = self.prepare('blocked')
        child, output = self.launch(root)
        self.await_file(root / 'action.json', child, output)
        action = json.loads((root / 'action.json').read_text())
        os.kill(action['pid'], signal.SIGKILL)
        self.assertEqual(child.wait(timeout=12), 1, self.log(output))
        report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
        self.assertIn('without final enforcement report', str(report['enforcement']['faults']))
        before = (root / 'action.json').read_bytes()
        retry, out = self.launch(root)
        self.assertEqual(retry.wait(timeout=12), 1, self.log(out))
        self.assertEqual(before, (root / 'action.json').read_bytes())

    def test_operator_stop_preserves_partial_output_and_original_envelope(self):
        root = self.prepare('blocked')
        child, output = self.launch(root)
        self.await_file(root / 'action.json', child, output)
        child.send_signal(signal.SIGTERM)
        self.assertEqual(child.wait(timeout=12), 1, self.log(output))
        report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
        self.assertEqual(report['operator_signals'], [signal.SIGTERM])
        self.assertTrue((root / 'partial.txt').exists())
        self.assertTrue(report['child_exited'])

    def test_preexisting_independent_manager_refuses_before_author_admission(self):
        root = self.prepare()
        owner, output = self.launch(root, '--hold-guard')
        self.await_file(root / 'guard-held', owner, output)
        child, out = self.launch(root)
        self.assertEqual(child.wait(timeout=12), 1, self.log(out))
        self.assertFalse((root / 'action.json').exists())
        report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
        self.assertEqual(report['state'], 'held')
        self.assertIn('another manager is already active', str(report['enforcement']))
        owner.terminate(); owner.wait(timeout=3)

    @staticmethod
    def log(output):
        output.flush(); output.seek(0)
        childlog = Path(output.name).parent / 'outcome.json.authoring.log'
        return output.read() + (childlog.read_text() if childlog.exists() else '')


def fixture_main():
    from contextlib import ExitStack
    from unittest.mock import patch
    from baton_v12.worker_manager import ControlStore, workspaces
    from baton_v12.job_manager import JobStore
    from tools import authoring_enforcement as e, single_worker
    root_source = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(root_source / 'work/records/2026/09/finding-v12-single-implementation-proof'))
    import baseline
    packet_path = sys.argv[sys.argv.index('--packet') + 1]
    value = json.loads(Path(packet_path).read_text()); root = Path(packet_path).parent
    config = json.loads((root / 'config.json').read_text())
    storage = config['workers'][0]['deployment']['workspace_storage']
    if '--hold-guard' in sys.argv:
        with ControlStore.open(value['deployment']['control_store'], incarnation='holder', clock=e.utc) as control:
            workspaces.hold_manager_instance(control, storage)
            (root / 'guard-held').write_text('held')
            time.sleep(20)
        return 0
    if '--guard-after' in sys.argv:
        with ControlStore.open(value['deployment']['control_store'], incarnation='competitor', clock=e.utc) as control:
            workspaces.hold_manager_instance(control, storage).release()
        return 0
    if '--competitor' in sys.argv:
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution
        with JobStore.open(value['deployment']['job_store'], authority_uuid=value['deployment']['authority_uuid'], incarnation='competitor', clock=e.utc) as job, ControlStore.open(value['deployment']['control_store'], incarnation='competitor', clock=e.utc) as control:
            try:
                stage_execution.operations_from(config, job, control, checkout=value['code_boundary'], credential_provider=lambda *args: 'fixture-secret')
            except ContractRefusal as error:
                assert 'another manager is already active' in str(error), str(error)
                print('competitor refused'); return 0
        raise AssertionError('independent manager admitted')

    def workload(argv, *, compose):
        from baton_v12.job_manager import submit, reconcile
        with JobStore.open(value['deployment']['job_store'], authority_uuid=value['deployment']['authority_uuid'], incarnation='author', clock=e.utc) as job, ControlStore.open(value['deployment']['control_store'], incarnation='author', clock=e.utc) as control:
            operations = compose(value, job, control, sys.stderr)
            try:
                # Real public admission action under the composed pool.
                submit(job, value['test_submission'])
                result = reconcile(job, operations, now=e.utc())
                guard = workspaces.hold_manager_instance(control, storage)
                (root / 'action.json').write_text(json.dumps({'admitted': any(act['act'] == 'admit' and act['outcome'] == 'performed' for act in result['acts']), 'acts': result['acts'], 'pid': os.getpid(), 'guard_pid': guard.pid}))
                (root / 'partial.txt').write_text('retained author output')
                if value['test_mode'] == 'exception':
                    raise RuntimeError('selected workload exception')
                if value['test_mode'] == 'blocked':
                    time.sleep(60)
                return 0
            finally:
                operations.close()

    real_process = e.Process
    def process(command, **kwargs):
        # Launch the exact production controller/child entrypoint with only
        # external fixture boundaries installed in the execed interpreter.
        marker = command.index('--packet')
        return real_process([sys.executable, '-B', str(Path(__file__).resolve()), *command[marker:]], **kwargs)
    with ExitStack() as stack:
        stack.enter_context(patch.object(baseline, 'held_packet', lambda path: json.loads(Path(path).read_text())))
        stack.enter_context(patch.object(baseline, 'verify_imported_sources', lambda packet: None))
        stack.enter_context(patch.object(baseline, 'main', workload))
        stack.enter_context(patch.object(baseline, 'verify_worker_image', lambda *args, **kwargs: None))
        stack.enter_context(patch.object(e, 'verify_controller', lambda packet: None))
        stack.enter_context(patch.object(e, 'Process', process))
        stack.enter_context(patch.object(single_worker, '_engine_run', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('no engine operation selected'))))
        stack.enter_context(patch.object(single_worker, 'UserCredentialSources', lambda *args, **kwargs: lambda *args: 'fixture-secret'))
        return e.main(sys.argv[1:])


if __name__ == '__main__':
    raise SystemExit(fixture_main())
