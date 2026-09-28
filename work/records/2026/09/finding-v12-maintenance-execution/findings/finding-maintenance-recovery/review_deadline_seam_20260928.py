"""Independent W285465 deadline no-helper and before-destroy capability controls."""
import unittest
from baton_v12.contracts import ContractRefusal
from tests.manager.test_runtime_deadlines import Deadlines

class DeadlineSeam(unittest.TestCase):
    def setUp(self):
        self.case = Deadlines('test_before_boundary_then_exact_reached_is_observation_only')
        self.case.setUp()
        self.addCleanup(self.case.tearDown)
        self.case.started()
        self.case.reached()

    def test_listing_without_custodian_can_finish(self):
        c = self.case
        c.adapter.normalize_directory = None
        c.adapter.custodian_image_digest = None
        answer = c.advance()
        self.assertIsNotNone(answer['discharge'])
        c.assert_lane_released()

    def test_missing_listing_refuses_before_destroy(self):
        c = self.case
        c.adapter.surviving_helpers = None
        with self.assertRaises(ContractRefusal):
            c.advance()
        self.assertEqual(c.adapter.removed, [], 'deadline destroyed before validating writer listing')
        c.assert_lane_held()

if __name__ == '__main__':
    unittest.main()
