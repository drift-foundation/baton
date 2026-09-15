import io
import unittest
from pathlib import Path
from tests.tools import test_job_viewer as author
from tools import job_viewer as view

class RequiredBehavior(author.ViewerCase):
    def test_rereading_unchanged_snapshot_does_not_make_it_fresh(self):
        doc = self.document()
        viewer = view.JobViewer(lambda: doc, clock=lambda: self.now)
        viewer.refresh()
        self.now += 60
        viewer.refresh()
        self.assertIn("!! STALE", "\n".join(view.render_list(viewer.snapshot, now=self.now)))

    def test_malformed_refresh_preserves_last_good_disconnected_view(self):
        reads = iter([self.document(), b"{"])
        viewer = view.JobViewer(lambda: next(reads), clock=lambda: self.now)
        viewer.refresh()
        viewer.refresh()
        self.assertFalse(viewer.snapshot.connected)
        self.assertIn("JOB job-a", "\n".join(view.render_list(viewer.snapshot, now=self.now)))

    def test_local_file_uri_locator_uses_supported_local_locator_semantics(self):
        target = Path(self.root.name) / "retained-result.log"
        target.write_text("retained result")
        self.assertEqual(view.read_locator({"locator": target.as_uri()}), "retained result")

    def test_known_worker_and_assignment_are_visible(self):
        doc = self.document()
        doc["jobs"][0]["stages"][0]["runtime"] = {
            "runtime_id": "runtime-proof-a", "execution_runtime": "local",
            "assignment": {"worker_id": "worker-proof-a", "assignment_id": "assignment-proof-a", "incarnation_id": "incarnation-proof-a"},
            "activity": None}
        shown = "\n".join(view.render_detail(self.snapshot(doc), "job-a", now=self.now))
        self.assertIn("worker-proof-a", shown)
        self.assertIn("assignment-proof-a", shown)

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromModule(author),
    unittest.defaultTestLoader.loadTestsFromTestCase(RequiredBehavior)])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
