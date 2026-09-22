"""Independent bounded W177936 feedback review; fake engine/provider only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from tests.manager.test_claude_context import RestoredCorrectionBoundary
from baton_v12.worker_manager import provider_context as context


class FeedbackReview(unittest.TestCase):
    def test_fifo_open_blocks_before_type_refusal(self):
        with tempfile.TemporaryDirectory(prefix="w177936-feedback-fifo-") as root:
            os.mkfifo(Path(root) / "feedback", 0o600)
            child = """import sys
from unittest import mock
import tests.manager.test_claude_agent
import claude_agent
agent = claude_agent.ClaudeAgent(run=lambda *a, **k: None)
with mock.patch.object(claude_agent, 'CONTEXT_ROOT', sys.argv[1]):
    print('entering-feedback-read', flush=True)
    agent._context_feedback({'mode': 'restore'})
"""
            started = time.monotonic()
            try:
                answer = subprocess.run([sys.executable, "-c", child, root],
                                        capture_output=True, text=True, timeout=2)
            except subprocess.TimeoutExpired as failure:
                self.assertIn(b"entering-feedback-read", failure.stdout)
                print(json.dumps({"probe": "fifo", "observed": "blocked-before-type-check",
                                  "seconds": time.monotonic() - started,
                                  "cleanup": "subprocess.run killed and waited for child"}), flush=True)
            else:
                self.fail(f"Expected current FIFO hang; exited {answer.returncode}: {answer.stderr}")

    def test_bound_correction_survives_manager_reopen(self):
        case = RestoredCorrectionBoundary()
        self.addCleanup(case.doCleanups)
        case.setUp()
        held, first, reviewer, second = case.corrected_ready()
        bound = context.context_invocation_of(held.control, second)
        roots = case.mounted(held.composed, "implementation", second)
        job, control, composed = case.reopen(held.job, held.control, held.composed)
        case.drive(job, composed, "implementation", "waiting")
        worker = case.worker_of(composed, "implementation")
        stage = {"job_id": "job-a", "attempt_id": second}
        worker.stage.prepare_context(worker, stage)
        self.assertEqual(context.context_invocation_of(control, second), bound)
        self.assertEqual(case.turn(control, "implementation", second,
                                   roots,
                                   edits={"harness.py": "print('correction round')\n"}), 0)
        case.drive(job, composed, "implementation", "completed")
        calls = [json.loads(line) for line in case.calls.read_text().splitlines()]
        self.assertEqual(len(calls), 2)
        self.assertIn("THE REVIEW'S FINDINGS:\n" + case.FINDINGS, calls[1]["argv"][-1])
        print(json.dumps({"probe": "reopen", "observed": "same-bound-feedback-served-once"}), flush=True)


if __name__ == "__main__":
    unittest.main(defaultTest="FeedbackReview", verbosity=2)
