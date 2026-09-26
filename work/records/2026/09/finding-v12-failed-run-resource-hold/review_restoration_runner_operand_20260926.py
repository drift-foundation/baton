"""Reviewer271500: selected deterministic public restoration overlap.

Fake validation/command output, real disposable directories; no Git/provider/engine.
Run alongside existing restoration, pinned-lock, prelock and old same-group case.
"""
import tempfile
import threading
import unittest

from baton_v12.checkpoint_profiles import GitCheckpointProfile


class RunnerOperandReview(unittest.TestCase):
    def test_public_restores_keep_distinct_runners_across_overlap(self):
        answer = {"returncode": 0, "stdout": "", "stderr": ""}
        calls = []
        entered = threading.Event()
        resume = threading.Event()
        errors = []
        profile = GitCheckpointProfile(lambda argv: calls.append(("ordinary", argv)) or answer)
        profile.validate = lambda repository, evidence, **kwargs: evidence
        evidence = {"head": "a" * 40}

        def runner_a(argv):
            calls.append(("A", argv))
            if not entered.is_set():
                entered.set()
                if not resume.wait(3):
                    raise RuntimeError("schedule timeout")
            return answer

        def runner_b(argv):
            calls.append(("B", argv))
            return answer

        with tempfile.TemporaryDirectory(prefix="w257624-operand-a-") as a:
            with tempfile.TemporaryDirectory(prefix="w257624-operand-b-") as b:
                def first():
                    try:
                        profile.restore_checkpoint(a, evidence, runner=runner_a)
                    except BaseException as error:
                        errors.append(error)
                worker = threading.Thread(target=first)
                worker.start()
                try:
                    self.assertTrue(entered.wait(3))
                    profile.restore_checkpoint(b, evidence, runner=runner_b)
                finally:
                    resume.set()
                    worker.join(3)
                self.assertFalse(worker.is_alive())
                self.assertEqual(errors, [])
        self.assertEqual([name for name, argv in calls], ["A", "B", "B", "A"])
        for name in ("A", "B"):
            vectors = [argv for owner, argv in calls if owner == name]
            self.assertTrue(any("reset" in argv for argv in vectors))
            self.assertTrue(any("clean" in argv for argv in vectors))


if __name__ == "__main__":
    unittest.main()
