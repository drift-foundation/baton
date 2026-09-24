"""D1: replay retained declarations through image-matched source, no provider.

Only temporary copies are writable. The repaired-declaration control stops at
_read_task; it proves admission past the original fault, not a successful Job.
"""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RETAINED = Path('/home/sl/baton-instances/two-jobs-251156')
ARTIFACT = HERE.parent / 'finding-v12-single-implementation-proof/IMAGE-ARTIFACT-244216.json'
FAULT = 'a implementation turn writes proposal and this assignment declares no proposal'


class TaskBoundaryReached(Exception):
    pass


class StartupBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix='w257627-source-')
        cls.addClassCleanup(cls.scratch.cleanup)
        image = json.loads(ARTIFACT.read_text())
        stage = Path(cls.scratch.name)
        for name, expected in image['all_worker_files'].items():
            relative = name.removeprefix('opt/baton/')
            candidates = [ROOT / 'v12/worker' / relative, ROOT / 'v12/python/src/baton_v12' / relative]
            source = next(p for p in candidates if p.is_file())
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise AssertionError(f'image source drift: {source}')
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        # Fresh source-only tree: -B alone would not prevent stale cache loads.
        sys.path.insert(0, str(stage))
        cls.addClassCleanup(sys.path.remove, str(stage))
        cls.agent = importlib.import_module('claude_agent')
        cls.worker = importlib.import_module('baton_worker')
        for module in (cls.agent, cls.worker, sys.modules['source_profiles'], sys.modules['source_profiles.checkout']):
            if not Path(module.__file__).is_relative_to(stage):
                raise AssertionError(f'unexpected import origin: {module.__file__}')
        outcome = json.loads((RETAINED / 'run/outcome.json').read_text())
        cls.attempts = outcome['admitted_attempts']
        if len(cls.attempts) != 2:
            raise AssertionError('expected the exact two retained attempts')

    def inputs(self, attempt):
        launch = RETAINED / 'run/launch' / attempt
        inputs = RETAINED / 'run/workspaces' / attempt / 'inputs'
        return launch, inputs, json.loads((launch / 'launch.json').read_text()), json.loads((inputs / 'input.json').read_text())['outputs']

    def test_original_declarations_fail_before_task_or_provider(self):
        for attempt in self.attempts:
            with self.subTest(attempt=attempt):
                _, _, seen, declared = self.inputs(attempt)
                child = Mock(side_effect=AssertionError('provider must not start'))
                with patch.object(self.agent, '_read_task') as task:
                    with self.assertRaises(self.agent.TaskRefusal) as raised:
                        self.agent.ClaudeAgent(run=child).work(seen, declared)
                    self.assertEqual(str(raised.exception), FAULT)
                    task.assert_not_called()
                child.assert_not_called()

    def test_real_exchange_reproduces_the_exact_terminal(self):
        for attempt in self.attempts:
            with self.subTest(attempt=attempt), tempfile.TemporaryDirectory(prefix='w257627-exchange-') as temporary:
                launch, inputs, seen, _ = self.inputs(attempt)
                stage = Path(temporary)
                shutil.copytree(inputs, stage / 'input')
                shutil.copytree(launch / 'command', stage / 'command')
                (stage / 'events').mkdir()
                (stage / 'output').mkdir()
                child = Mock(side_effect=AssertionError('provider must not start'))
                with patch.object(self.worker, 'INPUT_ROOT', str(stage / 'input')), patch.object(self.worker, 'OUTPUT_ROOT', str(stage / 'output')):
                    result = self.worker.serve_exchange(self.agent.ClaudeAgent(run=child), seen, seen['session'], str(stage / 'command'), str(stage / 'events'), sleep=Mock(side_effect=AssertionError('command must be present')))
                self.assertEqual(result, 1)
                for name in ('terminal.json', 'state-describe.json', 'state-work.json'):
                    self.assertEqual(json.loads((stage / 'events' / name).read_text()), json.loads((launch / 'events' / name).read_text()))
                child.assert_not_called()

    def test_adding_proposal_alone_still_refuses_required_review_outputs(self):
        _, _, seen, declared = self.inputs(self.attempts[0])
        proposal = dict(copy.deepcopy(declared[0]), name='proposal', path='proposal')
        with self.assertRaisesRegex(self.agent.TaskRefusal, "output 'findings' is declared required"):
            self.agent.ClaudeAgent(run=Mock(side_effect=AssertionError('provider'))).work(seen, [proposal, *declared])

    def test_union_with_optional_other_stage_outputs_reaches_task_boundary(self):
        for attempt in self.attempts:
            with self.subTest(attempt=attempt):
                _, _, seen, declared = self.inputs(attempt)
                proposal = dict(copy.deepcopy(declared[0]), name='proposal', path='proposal', required=False)
                control = [proposal, *(dict(one, required=False) for one in declared)]
                child = Mock(side_effect=AssertionError('provider must not start'))
                with patch.object(self.agent, '_read_task', side_effect=TaskBoundaryReached) as task:
                    with self.assertRaises(TaskBoundaryReached):
                        self.agent.ClaudeAgent(run=child).work(seen, control)
                    task.assert_called_once_with()
                child.assert_not_called()


if __name__ == '__main__':
    unittest.main()
