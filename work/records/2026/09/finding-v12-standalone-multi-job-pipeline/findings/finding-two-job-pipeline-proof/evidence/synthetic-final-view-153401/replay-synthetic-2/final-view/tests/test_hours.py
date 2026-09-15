import unittest

from demo.units import hours_to_seconds


class HoursTest(unittest.TestCase):
    def test_hours(self):
        for value in (0, 1, 2):
            with self.subTest(value=value):
                self.assertEqual(hours_to_seconds(value), value * 3600)
