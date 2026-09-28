import unittest
from tests.job_manager.test_tool import _running_governed_attempt, job_manager
from baton_v12.contracts.errors import ContractRefusal

class DecliningRead(unittest.TestCase):
    def exercise(self, allowance, count):
        case = _running_governed_attempt(self)
        seen = []
        def engine(argv, *, seconds=None):
            seen.append((list(argv), seconds))
            return {"status": 0, "stdout": "", "stderr": ""}
        adapter = job_manager._ReclaimAdapter("docker", engine, custodian_image_digest="sha256:" + "c" * 64)
        with self.assertRaises(ContractRefusal):
            adapter.surviving_helpers(case["store"], assignment_id="attempt-1", reclaim=allowance)
        self.assertEqual(len(seen), count)
        self.assertTrue(all(seconds > 0 and argv[1] == "ps" for argv, seconds in seen))
    def test_exhaustion_between_vectors(self):
        values = iter([2, 0])
        self.exercise(lambda: next(values), 1)
    def test_subsecond_allowance_starts_nothing(self):
        self.exercise(lambda: 0.5, 0)

if __name__ == "__main__":
    unittest.main()
