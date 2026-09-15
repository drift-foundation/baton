"""Prove exact publication survives a cut before preparation intent commits."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import TheComposedJobTraversesReviewAndAcceptance
from tools import integration_worker, stage_execution


class PublicationCut(TheComposedJobTraversesReviewAndAcceptance):
    def serving(self, **members):
        return super().serving(integration_preparation=True, **members)

    def runTest(self):
        held = self.reviewed()
        with mock.patch.object(integration_worker.PreparationExecution, "decide", side_effect=RuntimeError("review cut before intent")):
            with self.assertRaisesRegex(RuntimeError, "review cut before intent"):
                for _ in range(5):
                    sweep(held.job, held.composed, now=fixtures.NOW)
        root = Path(held.composed.deployment.integration_root) / stage_execution.INTEGRATION_BUNDLE_HOME
        def snapshot():
            return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}
        before = snapshot()
        self.assertTrue(before)
        report = sweep(held.job, held.composed, now=fixtures.NOW)
        messages = [str((act.get("detail") or {}).get("message", "")) for act in report["acts"]]
        self.assertTrue(any("does not resolve" in message for message in messages), messages)
        self.assertFalse(any("already exists" in message for message in messages), messages)
        self.assertEqual(snapshot(), before)
        print(json.dumps({"published_file_count": len(before), "publication_bytes_unchanged": True, "next_admission_messages": messages}), flush=True)


result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([PublicationCut()]))
sys.exit(not result.wasSuccessful())
