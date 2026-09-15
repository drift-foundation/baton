import io
import unittest
from types import SimpleNamespace
from tests.tools import test_job_viewer as author
from tools import job_viewer as view

class DrillThreshold(author.ViewerCase):
    def test_artifact_banner_uses_selected_interval(self):
        doc, artifact, _ = author.TheDrillDownIsWiredAndUsesLocatorSemantics.published(self)
        viewer = view.JobViewer(lambda: doc, interval=5,
            clock=lambda: self.now,
            wall=lambda: author._epoch(doc["observed_at"]) + 3)
        out = io.StringIO()
        args = SimpleNamespace(job="job-a", stage="job-a/implementation", artifact="result")
        self.assertEqual(view._drilled(viewer, args, out), 0)
        self.assertIn("the retained result", out.getvalue())
        self.assertNotIn("!! STALE", out.getvalue())

unittest.main(verbosity=2)
