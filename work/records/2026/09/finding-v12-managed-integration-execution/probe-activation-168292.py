import unittest
from tests.job_manager.test_managed_integration_capacity import ThePreparationIsCoordinatedEndToEnd as Case
case = Case("test_the_whole_sequence_runs_against_real_owners")
# Isolated reviewer reproduction: reach the currently skipped body, preserving assertions.
case.skipTest = lambda reason: print("REVIEW bypasses recorded skip for diagnosis:", reason)
r = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([case]))
raise SystemExit(not r.wasSuccessful())
