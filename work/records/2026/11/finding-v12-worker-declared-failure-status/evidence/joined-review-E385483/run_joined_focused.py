"""Joined focused selection: every module/class the three accepted inputs verified with, minus the two deep cases (run separately under the confined Git exception) and minus tests.manager.test_boundary_inventory, whose probes initialise fixture Git repositories outside that exception (run 1 shows exactly its 8 probe failures under the no-Git shim)."""
import unittest, json
names = ('tests.tools.test_job_observation', 'tests.tools.test_job_viewer', 'tests.job_manager.test_status', 'tests.manager.test_exchange',
         'tests.manager.test_claude_agent.ProviderInvocationTiming', 'tests.manager.test_attempt_failure_cause', 'tests.tools.test_attempt_diagnostics',
         'tests.tools.test_stage_execution.TheTraversedTargetPostureIsExplicit',
         'tests.manager.test_oci_integration.TheTargetPostureIsProvedAndNeverRepaired')
excluded = []
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite): yield from flatten(item)
        else: yield item
suite = unittest.TestSuite()
for test in flatten(unittest.defaultTestLoader.loadTestsFromNames(names)):
    if '.TheRealObservationReaderReachesTheView.' in test.id(): excluded.append(test.id())
    else: suite.addTest(test)
print(json.dumps({'modules': names, 'excluded': excluded}), flush=True)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'ran': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)}))
raise SystemExit(not result.wasSuccessful())
