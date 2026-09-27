"""W285464: the selected allocation must not mkdir on the host. Fake engine only."""
import unittest
from unittest import mock
from tests.manager.test_maintenance import TheOrdinaryALLOCATIONHappensInsideTheExecution

class HostAllocationBoundary(TheOrdinaryALLOCATIONHappensInsideTheExecution):
    def test_no_host_allocation_before_maintenance(self):
        with mock.patch('os.mkdir', side_effect=AssertionError('governed host mkdir before maintenance execution')):
            attempt, answer = self.allocating()
        self.assertTrue(answer.ok, answer.diagnostic)

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        HostAllocationBoundary('test_no_host_allocation_before_maintenance')]))
    raise SystemExit(not result.wasSuccessful())
