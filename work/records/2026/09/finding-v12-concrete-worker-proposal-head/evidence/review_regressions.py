"""Distinct W105575 review probes; existing fixture owns all private Git setup.

Run from v12/python with PYTHONPATH=src. No provider, engine or network call.
Only this class is loaded, so successful existing suites are not rerun.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "v12/python"))
from tests.manager import test_claude_agent as fixture


class ReviewRegressions(fixture.LineCase):
    def test_verified_dependency_cannot_be_omitted_from_commit(self):
        fake = self.provider(edits={
            ".gitignore": "ignored-data.txt\n",
            "ignored-data.txt": "needed\n",
            "harness.py": "from pathlib import Path\nassert Path('ignored-data.txt').read_text() == 'needed\\n'\n",
        })

        def run(argv, **options):
            if argv[0] == fixture.claude_agent.PROVIDER_PROGRAM:
                return fake(argv, **options)
            if argv[0] == "git":
                return subprocess.run(argv, env=self.environment(), **options)
            return subprocess.run(argv, **options)

        try:
            answered = fixture.ClaudeAgent(run=run, home=self.scratch).work(
                {"contract": "the frozen task"}, list(fixture.DECLARED))
        except fixture.TaskRefusal:
            return
        head = self.claim(answered)["head"]
        present = subprocess.run(
            ["git", "-C", self.outputs, "cat-file", "-e",
             f"{head}:ignored-data.txt"], capture_output=True,
            env=self.environment(), timeout=30)
        print(json.dumps({"probe": "ignored_dependency",
                          "disposition": answered["disposition"],
                          "verification": self.result()["verification"],
                          "committed_paths": self.result()["changed_paths"],
                          "dependency_in_commit": present.returncode == 0}))
        self.assertEqual(present.returncode, 0,
                         "completed verified candidate omits its required file")

    def test_index_hook_does_not_run(self):
        marker = os.path.join(self.home, "index-hook-ran")
        hook = os.path.join(self.outputs, ".git", "hooks", "post-index-change")
        self.write(hook, f"#!/bin/sh\nprintf ran >> '{marker}'\n")
        os.chmod(hook, 0o755)
        answered = self.worked(edits={"harness.py": "print('changed')\n"})
        print(json.dumps({"probe": "index_hook",
                          "disposition": answered["disposition"],
                          "hook_ran": os.path.exists(marker)}))
        self.assertFalse(os.path.exists(marker),
                         "worker Git operation ran a repository hook")

    def test_noop_correction_does_not_retain_prior_bundle(self):
        first = self.worked(edits={"harness.py": "print('first')\n"})
        self.completed(first)
        self.frozen(1)
        old = Path(self.proposal("objects.bundle")).read_bytes()
        second = self.worked(edits={})
        bundle = Path(self.proposal("objects.bundle"))
        print(json.dumps({"probe": "noop_correction",
                          "disposition": second["disposition"],
                          "metadata": second["outputs"][0]["result_metadata"],
                          "head": self.result()["head"],
                          "old_bundle_survives": bundle.exists() and bundle.read_bytes() == old}))
        self.assertFalse(bundle.exists(), "no-op correction retains prior objects.bundle")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReviewRegressions)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
