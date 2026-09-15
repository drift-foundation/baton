import unittest

from demo.greeting import greet


class GreetingTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_surrounding_spaces(self):
        self.assertEqual(greet(" Ada "), "Hello,  Ada !")
