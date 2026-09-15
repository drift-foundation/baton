import io
import unittest
from tests.tools import test_job_viewer as author
from tools import job_viewer as view

class RequiredBehavior(author.ViewerCase):
    def test_configured_interval_reaches_the_rendered_warning(self):
        doc = self.document()
        viewer = view.JobViewer(lambda: doc, interval=5, clock=lambda: self.now,
                                wall=lambda: author._epoch(doc["observed_at"]) + 3,
                                sleeper=lambda _: None)
        output = io.StringIO()
        viewer.run(ticks=1, stream=output)
        self.assertNotIn("!! STALE", output.getvalue())

    def test_real_scheduler_assignment_fields_are_displayed(self):
        doc = self.document()
        # Members of scheduler.allocation_of, not the invented allocation_id.
        doc["jobs"][0]["stages"][0]["allocation"] = {
            "assignment_id": "assignment-proof-168169",
            "worker_id": "worker-proof-168169", "generation": 3,
            "participant": "baton.worker", "allocation_state": "reserved"}
        shown = "\n".join(view.render_detail(self.snapshot(doc), "job-a", now=self.now))
        self.assertIn("assignment-proof-168169", shown)
        self.assertIn("worker-proof-168169", shown)

    def test_schema_named_malformed_refresh_keeps_last_good_view(self):
        doc = self.document()
        invalid = {**doc, "jobs": [None]}
        reads = iter([doc, invalid, doc])
        viewer = view.JobViewer(lambda: next(reads), clock=lambda: self.now,
                                sleeper=lambda _: None)
        output = io.StringIO()
        viewer.run(ticks=3, stream=output)
        self.assertIn("!! DISCONNECTED", output.getvalue())
        self.assertEqual(viewer.reads, 3)
        self.assertTrue(viewer.snapshot.connected)

    def test_initial_disconnection_in_detail_retries(self):
        reads = iter([b"{", self.document()])
        viewer = view.JobViewer(lambda: next(reads), clock=lambda: self.now,
                                sleeper=lambda _: None)
        output = io.StringIO()
        render = lambda snapshot, **kw: view.render_detail(snapshot, "job-a", **kw)
        viewer.run(ticks=2, render=render, stream=output)
        self.assertIn("!! DISCONNECTED", output.getvalue())
        self.assertIn("JOB job-a", output.getvalue())
        self.assertEqual(viewer.reads, 2)

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromModule(author),
    unittest.defaultTestLoader.loadTestsFromTestCase(RequiredBehavior)])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
