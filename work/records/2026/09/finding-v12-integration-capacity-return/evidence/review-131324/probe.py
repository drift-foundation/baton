"""Independent W131187 controls; retained review evidence, not product tests."""
import unittest
from tests.job_manager.test_scheduling import CapacityReturnsWhenAnIntegrationCompletes, JobStore, UUID, scheduler


class Independent(CapacityReturnsWhenAnIntegrationCompletes):
    def test_historical_completion_survives_later_uncertainty(self):
        attempt, allocation = self.integrating()
        held = self.projected(attempt, allocation)
        held[attempt['stage_id']]['observed']['runtime']['execution_runtime'] = 'uncertain'
        scheduler.reconcile_allocations(self.jobs, held)
        self.assertEqual(self.settled(attempt)['release_reason'], 'integration-completed')

    def test_foreign_stage_completion_does_not_release(self):
        self.keeps_capacity('foreign-stage', stage_id='other/integration')

    def test_reopened_reader_preserves_release_and_retry(self):
        attempt, allocation = self.integrating()
        held = self.projected(attempt, allocation)
        scheduler.reconcile_allocations(self.jobs, held)
        self.jobs.close()
        self.jobs = JobStore.open(self.job_path, authority_uuid=UUID, incarnation='review-reopened', clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.assertEqual(self.settled(attempt)['release_reason'], 'integration-completed')
        self.assertEqual(scheduler.reconcile_allocations(self.jobs, held), [])


if __name__ == '__main__':
    from tests.tools.test_stage_execution import TwoBoundJobsTraverseServingAndCorrection
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Independent)
    suite.addTest(TwoBoundJobsTraverseServingAndCorrection('test_a_completed_integration_returns_the_integrator_to_the_next_job'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
