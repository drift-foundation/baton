"""Reviewer probe: real managed apply must bind the tree actually verified.

Reuses the selected deterministic whole-composition fixture in memory. Only
the disposable fixture harness and its expected imported text differ. Product
and test files are unchanged; Git mutations stay in fixture repositories.
"""
import inspect
import json
import ast
import unittest
from pathlib import Path
from unittest import mock

from tests.tools.test_managed_apply import AnOrdinaryManagedIntegration
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
from tools import integration_bundle

HARNESS = '''import json, pathlib, subprocess
if 'apply-scratch' in str(pathlib.Path.cwd()):
    before = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    subprocess.run(['git', 'checkout', '--quiet', '--detach', 'HEAD^'], check=True)
    after = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert before != after
    assert not subprocess.check_output(['git', 'status', '--porcelain'])
    (pathlib.Path.cwd().parent / 'checked-revision.json').write_text(json.dumps({'before': before, 'after': after}))
'''


class ReviewProbe(unittest.TestCase):
    def test_clean_head_drift_is_currently_accepted(self):
        original = AnOrdinaryManagedIntegration.complete
        source = 'class Fixture:\n' + inspect.getsource(original)
        # Keep every success/gate/receipt/root assertion in the selected case.
        source = source.replace('if failed else None\n', 'if failed else ' + repr(HARNESS) + '\n')
        source = source.replace('"print(\'the corrected harness\')\\n"', repr(HARNESS))
        namespace = dict(original.__globals__)
        parsed = ast.parse(source)
        module = ast.Module(body=parsed.body[0].body, type_ignores=[])
        exec(compile(module, __file__ + ':fixture', 'exec'), namespace)
        observations, reports = [], []
        complete = OneManagedPreparationCompletes.complete
        retained = integration_bundle.retained_apply_report

        def run_fixture(case, *args, **kwargs):
            adopted = kwargs['completed']
            def observe(world, held, prepared):
                answer = adopted(world, held, prepared)
                observations.append(json.loads((Path(world.root) / 'apply-scratch' / 'checked-revision.json').read_text()))
                return answer
            return complete(case, *args, **dict(kwargs, completed=observe))

        def collect(*args, **kwargs):
            answer = retained(*args, **kwargs)
            reports.append(answer[0])
            return answer

        with mock.patch.object(OneManagedPreparationCompletes, 'complete', run_fixture), mock.patch.object(integration_bundle, 'retained_apply_report', collect):
            namespace['complete'](self)
        self.assertEqual(len(observations), 1)
        self.assertNotEqual(observations[0]['before'], observations[0]['after'])
        self.assertTrue(reports)
        self.assertTrue(all(report['unchanged'] and report['status'] == 0 and report['candidate'] == observations[0]['before'] for report in reports))
        print(json.dumps({'confirmed_defect': 'clean HEAD drift accepted as unchanged', 'actual': observations[0], 'reported': reports[-1], 'full_fixture_success_assertions': 'passed'}, sort_keys=True))


unittest.main(defaultTest='ReviewProbe')
