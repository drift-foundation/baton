"""Diagnostic only: observe exact preparation retry on disposable owners."""
import unittest
from tests.job_manager.test_managed_integration_capacity import ThePreparationIsCoordinatedEndToEnd

class ResumeBoundary(unittest.TestCase):
    def test_exact_retry_of_prepared_sequence(self):
        fixture = ThePreparationIsCoordinatedEndToEnd()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.addCleanup(fixture.tearDown)
        store, stage, allocation, execution, held = fixture.prepared()
        try:
            execution.prepare(
                orchestration_id=fixture.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                request=fixture.request(), plan=fixture.plan(stage, **fixture.FRESH),
                execution_work_id=fixture.EXECUTION_WORK,
                execution_route=fixture.CHILD_ROUTE,
                policy_digest=fixture.POLICY, profile_name="reference",
                accept=fixture.accepting(), contract=fixture.CONTRACT)
        except Exception as error:
            print(type(error).__name__ + ": " + str(error), flush=True)
            raise

if __name__ == "__main__":
    unittest.main(verbosity=2)
