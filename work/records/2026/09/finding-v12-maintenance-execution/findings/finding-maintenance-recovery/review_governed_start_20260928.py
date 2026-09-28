"""Real custody path, author fake engine; require it to reach activation."""
import unittest
from tests.manager.test_maintenance import TheGOVERNEDCustodyActBindsBeforeItActivates

class GovernedStart(TheGOVERNEDCustodyActBindsBeforeItActivates):
    def test_successful_create_reaches_start(self):
        answered, order, governed = self.governed()
        self.assertIn("start", order, answered.diagnostic)
        self.assertEqual([one[1] for one in governed], ["created", "started"])

if __name__ == "__main__":
    unittest.main(defaultTest="GovernedStart.test_successful_create_reaches_start")
