"""Probe full measured/committed byte equality independently of Git status.

The existing disposable LineCase owns setup and cleanup. No engine/provider.
Run from v12/python with PYTHONPATH=src.
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "v12/python"))
from tests.manager import test_claude_agent as fixture


class TrackedBytes(fixture.LineCase):
    def test_measured_tracked_bytes_match_even_when_status_hides_the_edit(self):
        # An index flag is not a history mutation and does not dirty entry.
        self.git("update-index", "--assume-unchanged", "preflight.py")
        payload = "verified payload\n"
        fake = self.provider(edits={
            "preflight.py": payload,
            "harness.py": "from pathlib import Path\nassert Path('preflight.py').read_text() == 'verified payload\\n'\n",
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
        committed = self.git("cat-file", "blob",
                             f"{self.claim(answered)['head']}:preflight.py")
        print(json.dumps({"disposition": answered["disposition"],
                          "verification": self.result()["verification"],
                          "changed_paths": self.result()["changed_paths"],
                          "measured_bytes": payload,
                          "committed_bytes": committed}))
        self.assertEqual(committed, payload,
                         "path equality passed while verified tracked bytes differ")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TrackedBytes))
    sys.exit(not result.wasSuccessful())
