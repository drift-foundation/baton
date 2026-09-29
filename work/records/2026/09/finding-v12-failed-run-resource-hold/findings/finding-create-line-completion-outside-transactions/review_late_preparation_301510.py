"""Independent schedule after the early replay check; disposable fixture only."""
import unittest
from unittest import mock
from tests.manager.test_review_cycles import StableLineLifecycle
from baton_v12.worker_manager import workspaces, review_cycles

class LatePreparation(StableLineLifecycle):
    def test_creator_cannot_change_access_after_competitor_admits_writer(self):
        prove = workspaces.prove_line_integrity
        establish = workspaces.establish_line_access
        entered = False
        saved = {}
        states = []
        def interleave(*args, **kwargs):
            nonlocal entered
            if not entered:
                entered = True
                saved["line"] = self.line()
                self.writer(saved["line"]["line_id"], 1)
            return prove(*args, **kwargs)
        def observe(*args, **kwargs):
            if "line" in saved:
                states.append(review_cycles.line_of(self.store, saved["line"]["line_id"])["state"])
            return establish(*args, **kwargs)
        with mock.patch.object(workspaces, "prove_line_integrity", side_effect=interleave), mock.patch.object(workspaces, "establish_line_access", side_effect=observe):
            self.line()
        self.assertNotIn("writing", states, "stale creator performed access mutation after another creator admitted a writer")

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([LatePreparation("test_creator_cannot_change_access_after_competitor_admits_writer")]))
    raise SystemExit(not result.wasSuccessful())
