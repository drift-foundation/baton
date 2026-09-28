"""Independent HP8 probe: ordinary reconcile must perform restored identification."""
import inspect
import textwrap
import unittest
from tests.tools import test_single_worker as m
source = textwrap.dedent(inspect.getsource(m.LostTaskRepliesKeepTheExternalExecution.lost_reply))
old = 'operations._worker.refresh_runtime({"attempt_id": attempt})'
assert source.count(old) == 1
source = source.replace(old, 'reconcile(job, operations, now=fixtures.NOW)')
exec(compile(source, 'review-normal-reconcile', 'exec'), m.__dict__)
m.LostTaskRepliesKeepTheExternalExecution.lost_reply = m.lost_reply
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(m.LostTaskRepliesKeepTheExternalExecution))
raise SystemExit(not result.wasSuccessful())
