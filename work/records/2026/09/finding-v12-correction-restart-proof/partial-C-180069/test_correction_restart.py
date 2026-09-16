"""Selected C proof; deterministic subprocesses and a simulated OCI engine."""
import json
import os
from pathlib import Path
import unittest

from tests.tools import correction_restart_trace as proof


class UsefulCorrection(unittest.TestCase):
    def test_useful_correction_reaches_managed_target(self):
        world = proof.World()
        self.addCleanup(world.doCleanups)
        world.setUp()
        artifact = world.run_scenario()
        self.assertEqual(proof.validate(artifact), [])
        if os.environ.get("BATON_C_EVIDENCE"):
            Path(os.environ["BATON_C_EVIDENCE"]).write_text(json.dumps(artifact, indent=2) + "\n")
