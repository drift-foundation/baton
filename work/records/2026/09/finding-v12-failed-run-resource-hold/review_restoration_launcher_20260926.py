"""Reviewer271429: deterministic profile overlap and bounded local child evidence.

Selected only this module plus existing restoration/lock/prelock dossier selectors.
No model, engine, deployed store or real Git commands. Descendant exits on its own.
"""
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

from baton_v12.checkpoint_profiles import GitCheckpointProfile
from tools.stage_execution import restoration_launcher


class LauncherReview(unittest.TestCase):
    def test_overlapping_restore_keeps_its_launcher(self):
        calls = []
        answer = {"returncode": 0, "stdout": "", "stderr": ""}
        profile = GitCheckpointProfile(
            lambda argv: calls.append(("ordinary", argv)) or answer,
            launcher=lambda argv: calls.append(("covered", argv)) or answer)
        entered = threading.Event()
        resume = threading.Event()
        errors = []

        def body(repository, evidence):
            if repository == "A":
                entered.set()
                if not resume.wait(3):
                    raise RuntimeError("schedule timed out")
            profile._run((repository,), "review controlled effect")

        profile._restored_checkpoint = body

        def first():
            try:
                profile.restore_checkpoint("A", {})
            except BaseException as error:
                errors.append(error)

        worker = threading.Thread(target=first)
        worker.start()
        try:
            self.assertTrue(entered.wait(3))
            profile.restore_checkpoint("B", {})
        finally:
            resume.set()
            worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(calls, [("covered", ("B",)), ("covered", ("A",))])

    def test_failed_record_does_not_leave_same_group_effect(self):
        with tempfile.TemporaryDirectory(prefix="w257624-launch-review-") as root:
            ready = Path(root) / "ready"
            effect = Path(root) / "effect"
            program = """
import os, sys, time
ready, effect = sys.argv[1:]
if os.fork() == 0:
    for fd in (0, 1, 2):
        os.close(fd)
    with open(ready, 'w') as stream:
        stream.write(str(os.getpgrp()))
    time.sleep(0.25)
    with open(effect, 'w') as stream:
        stream.write('surviving effect')
    os._exit(0)
time.sleep(2)
"""
            def record(kind, payload):
                if kind == "group":
                    deadline = time.monotonic() + 2
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(0.005)
                    self.assertTrue(ready.exists())
                    self.assertEqual(int(ready.read_text()), payload["group"])
                    raise RuntimeError("controlled failed record")

            with self.assertRaisesRegex(RuntimeError, "controlled failed record"):
                restoration_launcher(record)((sys.executable, "-c", program,
                                               str(ready), str(effect)))
            time.sleep(0.4)  # Bounded fixture child finishes naturally before cleanup.
            self.assertFalse(effect.exists(), "same-group descendant wrote after launcher refusal")


if __name__ == "__main__":
    unittest.main()
