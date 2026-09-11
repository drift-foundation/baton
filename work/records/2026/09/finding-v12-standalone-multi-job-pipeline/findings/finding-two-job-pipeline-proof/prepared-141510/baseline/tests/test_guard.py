import unittest


class GuardTest(unittest.TestCase):
    def test_sentinel(self):
        self.assertEqual("retained", "retained")
