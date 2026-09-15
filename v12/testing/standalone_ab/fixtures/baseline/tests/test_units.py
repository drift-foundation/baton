import unittest

from demo.units import minutes_to_seconds


class MinutesTest(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(minutes_to_seconds(0), 0)

    def test_two(self):
        self.assertEqual(minutes_to_seconds(2), 120)
