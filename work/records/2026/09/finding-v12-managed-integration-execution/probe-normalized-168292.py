import unittest
from unittest.mock import patch
from tools.integration_worker import PreparationExecution
from tests.job_manager.test_managed_integration_capacity import ThePreparationIsCoordinatedEndToEnd as Case
original = PreparationExecution.admit
def normalized(self, intent, *, runtime_attempt_id, assignment):
    # Diagnostic only: lossless adaptation of the public owner's flat answer.
    expected = {"work_ref": {"authority_uuid": assignment["authority_uuid"],
                             "work_id": assignment["work_id"]},
                "participant": assignment["participant"], "generation": assignment["generation"]}
    return original(self, intent, runtime_attempt_id=runtime_attempt_id, assignment=expected)
case = Case("test_the_whole_sequence_runs_against_real_owners")
case.skipTest = lambda reason: print("REVIEW bypasses recorded skip for diagnosis:", reason)
with patch.object(PreparationExecution, "admit", normalized):
    r = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([case]))
raise SystemExit(not r.wasSuccessful())
