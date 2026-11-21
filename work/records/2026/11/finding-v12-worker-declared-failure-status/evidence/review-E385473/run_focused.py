"""Focused presentation/projection suite; excludes two deep worker-execution cases.
Those cases invoke fixture Git and require full worker packaging inputs, outside
this no-Git-mutation implementation verification boundary. Prior failures retained.
"""
import unittest,json
modules=('tests.manager.test_attempt_failure_cause','tests.tools.test_attempt_diagnostics','tests.tools.test_job_observation','tests.tools.test_job_viewer')
excluded=[]
def flatten(suite):
 for item in suite:
  if isinstance(item,unittest.TestSuite):yield from flatten(item)
  else:yield item
suite=unittest.TestSuite()
for test in flatten(unittest.defaultTestLoader.loadTestsFromNames(modules)):
 if '.TheRealObservationReaderReachesTheView.' in test.id():excluded.append(test.id())
 else:suite.addTest(test)
print(json.dumps({'excluded':excluded}),flush=True)
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
