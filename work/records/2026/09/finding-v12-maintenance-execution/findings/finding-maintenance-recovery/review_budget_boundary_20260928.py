"""Reviewer boundary probe; simulated custody, real normalize_directory wrapper."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from baton_v12.worker_manager import custody, oci

class BudgetBoundary(unittest.TestCase):
    def test_work_exhaustion_preserves_cleanup_and_vector_caps(self):
        seen = []
        remaining = [7]
        def engine(argv, *, seconds):
            seen.append((argv[1], seconds))
            return {"status": 0, "stdout": "", "stderr": ""}
        adapter = SimpleNamespace(run=engine, engine="docker", custodian_image_digest="sha256:" + "c" * 64)
        def simulated_act(engine_name, port, **kwargs):
            for verb in ("run", "create", "start", "wait", "logs"):
                port([engine_name, verb], seconds=11)
            port([engine_name, "logs"], seconds=2)
            remaining[0] = 0
            port([engine_name, "start"], seconds=11)
            for verb in ("ps", "inspect", "stop", "rm"):
                port([engine_name, verb], seconds=11)
            port([engine_name, "rm"], seconds=2)
        with patch.object(custody, "custody_act", simulated_act):
            oci.OciAdapter.normalize_directory(adapter, None, assignment_id="probe", which="workspace", seconds=lambda: remaining[0], reclaim=lambda: 3)
        self.assertEqual(seen, [(v, 7) for v in ("run", "create", "start", "wait", "logs")] + [("logs", 2), ("start", 0)] + [(v, 3) for v in ("ps", "inspect", "stop", "rm")] + [("rm", 2)])

if __name__ == "__main__":
    unittest.main()
