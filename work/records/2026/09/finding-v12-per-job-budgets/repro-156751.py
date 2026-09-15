"""Run the 15 affected tests with only the two planned setup operands added.

The repository test source is not edited. The exact proposed diff and module
digest are retained; all original assertions execute against current product.
"""
import difflib
import hashlib
import json
import pathlib
import sys
import types
import unittest

record = pathlib.Path(__file__).parent
source = pathlib.Path('/home/sl/src/baton/v12/python/tests/tools/test_single_worker.py')
original = source.read_text()
anchor = ('            transport=single_worker.exchange.EXCHANGE_TRANSPORT,\n'
          '            workspace_group=single_worker.configured_workspace_group(control))')
replacement = ('            transport=single_worker.exchange.EXCHANGE_TRANSPORT,\n'
               '            job_execution=single_worker.job_execution_reader(job)(\n'
               '                job_id=stage["job_id"], attempt_id=attempt_id,\n'
               '                runtime_input_digest=self.config["input_manifest"]["manifest_digest"],\n'
               '                runtime_policy_digest=self.config["policy_digest"]),\n'
               '            workspace_group=single_worker.configured_workspace_group(control))')
assert original.count(anchor) == 2, 'fixture sites moved; do not guess'
changed = original.replace(anchor, replacement)
(record / 'fixture-156751.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(keepends=True), changed.splitlines(keepends=True),
    fromfile='a/v12/python/tests/tools/test_single_worker.py',
    tofile='b/v12/python/tests/tools/test_single_worker.py')))
print(json.dumps({'original_sha256': hashlib.sha256(original.encode()).hexdigest(),
                  'proposed_sha256': hashlib.sha256(changed.encode()).hexdigest(),
                  'changed_setup_sites': 2}), flush=True)
module = types.ModuleType('_w156162_review_fixture')
module.__file__ = str(source)
sys.modules[module.__name__] = module
exec(compile(changed, str(source), 'exec'), module.__dict__)
suite = unittest.TestSuite()
for name in ('AFaultedTerminalSurvivesTheContainerThatWroteIt',
             'TheAnsweredEndingRunsThroughTheRealOwners'):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, name)))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
