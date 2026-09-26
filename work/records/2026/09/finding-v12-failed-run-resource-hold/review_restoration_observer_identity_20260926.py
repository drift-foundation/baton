"""Reviewer272198: deterministic observer-domain uncertainty, no kernel mutation.

An ESRCH in an unqualified PID view is not absence in the issuing PID view.
Only the signal-zero observation is mocked; no process is created or signalled.
"""
import os
import unittest
from unittest import mock
from tools.stage_execution import restoration_cessation


class ObserverIdentity(unittest.TestCase):
    def test_absence_without_issuing_domain_proof_is_unknown(self):
        number = os.getpgrp() + 1000000
        record = {"group": number, "leader": number, "started": 17}
        # This is the exact emitted record shape: no boot, host or PID-view identity.
        # Model a probe in a different view where the recorded live group is invisible.
        with mock.patch("os.killpg", side_effect=ProcessLookupError):
            self.assertEqual(restoration_cessation()(record), "unknown")


if __name__ == "__main__":
    unittest.main()
