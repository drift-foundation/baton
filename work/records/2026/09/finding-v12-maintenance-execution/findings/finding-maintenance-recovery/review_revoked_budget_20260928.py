"""Deterministic connected revoked-ending budget regression; no live engine."""
import unittest
from unittest.mock import patch
from tests.job_manager.test_tool import _running_governed_attempt, job_manager
from baton_v12.worker_manager import intake

class RevokedBudget(unittest.TestCase):
    def test_helper_observations_respect_supplied_reclaim_allowance(self):
        case = _running_governed_attempt(self)
        vectors = []
        def engine(argv, *, seconds=None):
            vectors.append((list(argv), seconds))
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "", "stderr": "Error: No such container: " + argv[-1]}
            return {"status": 0, "stdout": "", "stderr": ""}
        original = intake.settle_revoked_resource
        def bounded(*args, **kwargs):
            kwargs.update(seconds=7, reclaim=3)
            return original(*args, **kwargs)
        with patch.object(intake, "settle_revoked_resource", side_effect=bounded):
            answer = job_manager._reclaiming(case["store"], "docker", engine, "sha256:" + "c" * 64)(now="2026-08-24T01:00:00.000Z")
        self.assertEqual(answer["reclaimed"][0]["ending"]["settled"], "returned")
        self.assertFalse(any(v[0][1] in ("create", "run", "start") for v in vectors))
        reads = [seconds for argv, seconds in vectors if argv[1] == "ps"]
        self.assertTrue(reads)
        self.assertTrue(all(value is not None and value <= 3 for value in reads), reads)

if __name__ == "__main__":
    unittest.main()
