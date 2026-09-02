import unittest

from probe import permission_boundary_marker


class TheWorkerCanRunItsOwnVerification(unittest.TestCase):
    def test_the_marker_names_the_ruled_boundary(self):
        self.assertEqual(permission_boundary_marker(), "worker-container")


if __name__ == "__main__":
    unittest.main()
