"""Reviewer probe of a zero-exit apply that changes its private worktree.

Runs a bounded variant of the selected composition fixture in memory. It reads
the real ending, projection and queue owners after the fixture's normal final
failure assertion detects incomplete settlement. No product/test file edits.
"""
import ast
import inspect
import json
import unittest
from unittest import mock

from tests.tools.test_managed_apply import AnOrdinaryManagedIntegration
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
from tools import integration_bundle
from baton_v12.integration import reconciliation, queue
from baton_v12.job_manager.integration_capacity import integration_capacity_of, failed_integration_of
from baton_v12.worker_manager import attempt_runtime_of

HARNESS = "import pathlib\nif 'apply-scratch' in str(pathlib.Path.cwd()): pathlib.Path('unexpected-file.txt').write_text('changed')\n"


class ReviewProbe(unittest.TestCase):
    def test_cleaned_known_failure_has_no_final_outcome(self):
        original = AnOrdinaryManagedIntegration.complete
        source = 'class Fixture:\n' + inspect.getsource(original)
        tree = ast.parse(source)
        method = tree.body[0].body[0]
        for node in ast.walk(method):
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'body' for target in node.targets):
                node.value = ast.copy_location(ast.Constant(HARNESS), node.value)
            if isinstance(node, ast.Constant) and node.value == 200:
                node.value = 20
        namespace = dict(original.__globals__)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), __file__ + ':fixture', 'exec'), namespace)
        original_complete = OneManagedPreparationCompletes.complete
        observations, reports = [], []
        original_report = integration_bundle.retained_apply_report

        def complete(case, *args, **kwargs):
            callback = kwargs['completed']
            def observed(world, held, prepared):
                with self.assertRaises(AssertionError) as failed:
                    callback(world, held, prepared)
                deployment = held.composed.deployment
                result_id = prepared['managed_result_id']
                capacity = integration_capacity_of(held.job, result_id)
                root = capacity['root']
                member = next(one for one in capacity['members'] if one['phase'] == 'apply')
                attempt = member['execution_attempt_id']
                observations.append({'root': root['lifecycle'], 'member': member,
                    'failure': failed_integration_of(held.job, root['stage_id'], root['episode']),
                    'runtime': attempt_runtime_of(held.control, attempt),
                    'lease': queue.lease_of(deployment.integration, 'managed-lease:' + attempt),
                    'publication': reconciliation.publication_of(deployment.integration, result_id, 'apply'),
                    'state': world.states(held.job, held.composed)['integration'],
                    'fixture_assertion': str(failed.exception)[:200]})
            return original_complete(case, *args, **dict(kwargs, completed=observed))

        def retained(*args, **kwargs):
            answer = original_report(*args, **kwargs)
            reports.append(answer[0])
            return answer

        with mock.patch.object(OneManagedPreparationCompletes, 'complete', complete), mock.patch.object(integration_bundle, 'retained_apply_report', retained):
            namespace['complete'](self, failed=True)
        self.assertEqual(len(observations), 1)
        held = observations[0]
        self.assertTrue(reports)
        self.assertTrue(all(report['status'] == 0 and report['unchanged'] is False for report in reports))
        self.assertEqual(held['member']['state'], 'ended')
        self.assertEqual(held['member']['outcome'], 'failed')
        self.assertEqual(held['runtime']['execution_runtime'], 'destroyed')
        self.assertIn(held['runtime']['cleanup'], ('complete', 'retained'))
        self.assertEqual(held['lease']['state'], 'released')
        self.assertEqual(held['lease']['ending'], {'outcome': 'entry-refused'})
        self.assertIsNone(held['publication'])
        self.assertIsNone(held['failure'])
        self.assertEqual(held['root'], 'open')
        self.assertNotEqual(held['state'], 'completed')
        print(json.dumps({'confirmed_defect': 'known dirty apply cannot settle', 'root': held['root'], 'stage': held['state'],
            'member': held['member']['outcome'], 'runtime': held['runtime']['execution_runtime'], 'cleanup': held['runtime']['cleanup'],
            'lease': held['lease']['state'], 'failure': held['failure'], 'publication': held['publication'], 'report': reports[-1]}, sort_keys=True))


unittest.main(defaultTest='ReviewProbe')
