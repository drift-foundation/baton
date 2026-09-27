"""Independent W285464 mount-boundary probe; fake engine only."""
import os
import unittest
from tests.manager.test_maintenance import TheOrdinaryALLOCATIONHappensInsideTheExecution

class AllocationMountBoundary(TheOrdinaryALLOCATIONHappensInsideTheExecution):
    def test_allocation_mount_excludes_sibling_attempt(self):
        attempt, answer = self.allocating()
        self.assertTrue(answer.ok, answer.diagnostic)
        argv = self.vector('create')
        mounts = [a for a in argv if a.startswith('type=bind,')]
        self.assertEqual(len(mounts), 1)
        source = dict(part.split('=', 1) for part in mounts[0].split(','))['source']
        sibling = os.path.join(self.storage, 'attempt-1')
        self.assertTrue(os.path.isdir(sibling))
        self.assertNotEqual(os.path.commonpath((source, sibling)), source,
                            'writable maintenance bind exposes sibling attempt; name discipline is not mount exclusion')

if __name__ == '__main__':
    suite = unittest.TestSuite([AllocationMountBoundary('test_allocation_mount_excludes_sibling_attempt')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
