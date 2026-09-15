"""Reviewer-only diagnosis; no product/test source edits. Run under supervisor."""
import pathlib, sys, unittest
from unittest import mock
here = pathlib.Path(__file__).resolve().parent
repository = pathlib.Path('/home/sl/src/baton')
source = (here / 'restart-attempt-170659.py').read_text()
fixed = sys.argv[1] == 'fixed'
if fixed:
    source = source.replace('original_admit = preparation.admit', 'original_admit = type(preparation).admit')
    source = source.replace('return original_admit(*args)', 'return original_admit(instance, *args)')
# Final assertions must query the current composition, too.
source = source.replace('reopened.append(preparation)', 'reopened.append(preparation)\n                    deployment = held.composed.deployment\n                    runtime = preparation._runtime')
namespace = {'__name__': 'review_restart_probe', '__file__': str(repository / 'v12/python/tests/tools/test_managed_preparation.py')}
exec(compile(source, namespace['__file__'], 'exec'), namespace)
case_type = namespace['OneManagedPreparationCompletes']

def reopen(self, case, held, held_runtime, engine, live):
    import sqlite3
    retired = held.composed
    old_authority = retired.deployment.authority
    old_job, old_control = held.job, held.control
    held_runtime[0].close()
    retired.close()
    old_job.close()
    old_control.close()
    with self.assertRaises(sqlite3.ProgrammingError):
        old_authority.project_work(case.work)
    job, control, composed = case.serving()
    self.assertIsNot(composed.deployment.authority, old_authority)
    self.assertIsNot(job, old_job)
    self.assertIsNot(control, old_control)
    self.assertIsNotNone(composed.deployment.authority.project_work(case.work))
    held.job, held.control, held.composed = job, control, composed
    preparation = composed.deployment._integration_operations._preparation
    runtime = preparation._runtime
    runtime.engine_run = engine
    held_runtime[0] = runtime
    self.preparing = preparation.started
    live[0] = preparation
    return preparation

names = sys.argv[2:] or ['test_a_restart_before_work_creation_resumes_one_child_work']
with mock.patch.object(case_type, 'reopen', reopen):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(case_type(n) for n in names))
raise SystemExit(not result.wasSuccessful())
