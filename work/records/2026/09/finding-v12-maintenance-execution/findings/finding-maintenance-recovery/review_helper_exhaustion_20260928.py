import unittest
from tests.job_manager.test_tool import _running_governed_attempt, job_manager
from baton_v12.contracts.errors import ContractRefusal

class ExhaustedRead(unittest.TestCase):
    def test_exhausted_allowance_does_not_cross_to_engine(self):
        case = _running_governed_attempt(self)
        seen = []
        def engine(argv, *, seconds=None):
            seen.append((list(argv), seconds))
            return {"status": 0, "stdout": "", "stderr": ""}
        adapter = job_manager._ReclaimAdapter("docker", engine, custodian_image_digest="sha256:" + "c" * 64)
        try:
            adapter.surviving_helpers(case["store"], assignment_id="attempt-1", reclaim=lambda: 0)
        except ContractRefusal:
            pass
        self.assertEqual(seen, [], "zero allowance must refuse before engine invocation")

if __name__ == "__main__":
    unittest.main()
