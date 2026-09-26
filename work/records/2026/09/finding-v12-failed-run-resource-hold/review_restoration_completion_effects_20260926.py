"""Reviewer271562: selected disposable real-store/fake-profile completion schedule.

Finite local Python child, no Git/provider/engine/deployed state. Child stays in group.
"""
from pathlib import Path
import sys
import time
import unittest

import test_restore_outside_the_lock as author
from tools.stage_execution import restoration_launcher, restoration_cessation


class CompletionEffects(author.RestoreOutsideTheLock):
    def test_completion_does_not_release_while_recorded_group_can_write(self):
        self.abandoned()
        root = Path(self.temporary.name)
        release = root / "review-release"
        effect = root / "review-late-effect"
        program = """
import os, sys, time
release, effect = sys.argv[1:]
if os.fork() == 0:
    for fd in (0, 1, 2): os.close(fd)
    deadline = time.monotonic() + 2
    while not os.path.exists(release) and time.monotonic() < deadline:
        time.sleep(0.005)
    if os.path.exists(release):
        with open(effect, 'w') as stream: stream.write('late effect')
    os._exit(0)
"""
        honest = self.profile.restore_checkpoint
        def restoring(repository, evidence, *, runner=None):
            result = runner((sys.executable, "-c", program, str(release), str(effect)))
            self.assertEqual(result["returncode"], 0)
            return honest(repository, evidence)
        self.profile.restore_checkpoint = restoring
        answered = self.restore(launcher=restoration_launcher)
        recovery = author.review_cycles._restore_operation_id(author.RESTORE_KIND, author.ABANDONED, 2)
        launches = author.review_cycles._launched_commands(self.store, recovery, 1)
        state = restoration_cessation()(launches[0][1]["observed"])
        release.write_text("completion already returned")
        deadline = time.monotonic() + 2
        while not effect.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertTrue(effect.exists(), "fixture descendant did not produce controlled effect")
        time.sleep(0.03)
        self.assertFalse(answered["state"] == "correction-ready" and state == "running",
                         "line released while recorded group could still write after completion")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([CompletionEffects(
        "test_completion_does_not_release_while_recorded_group_can_write")])
