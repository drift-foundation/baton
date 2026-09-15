"""Independent adoption identity checks; disposable public-owner fixtures."""
import unittest
from tests.integration import test_managed_storage as cases

class AdoptionBindings(unittest.TestCase):
    def setUp(self):
        self.fixture = cases.ThePreparationIsAdoptedFromWhatItCollected()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.ended()

    def test_unchanged_collected_preparation_adopts(self):
        held = self.fixture.adopt(self.store)
        self.assertEqual(held["source"], self.fixture.request()["source"])

    def test_foreign_task_digest_refuses(self):
        task = self.fixture.task(self.store, task_digest="sha256:" + "f" * 64)
        with self.assertRaises(cases.ContractRefusal):
            held = self.fixture.adopt(self.store, task=task)
            recorded = cases.managed_result_of(self.fixture.coordinated(), held["managed_result_id"])
            print("ADOPTED foreign task digest: " + recorded["phases"]["prepare"]["task"]["task_digest"], flush=True)

    def test_foreign_submission_candidate_refuses(self):
        submission = self.fixture.submission(source_candidate="f" * 40)
        with self.assertRaises(cases.ContractRefusal):
            held = self.fixture.adopt(self.store, submission=submission)
            recorded = cases.managed_result_of(self.fixture.coordinated(), held["managed_result_id"])
            print("ADOPTED submission source candidate: " + recorded["source_candidate"], flush=True)
            print("REQUEST source candidate: " + self.fixture.request()["source"]["candidate"], flush=True)

if __name__ == "__main__":
    unittest.main(verbosity=2)
