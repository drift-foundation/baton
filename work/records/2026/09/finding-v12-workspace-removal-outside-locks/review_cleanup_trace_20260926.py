"""Capture call stacks without linecache I/O for lstats under the cleanup lock."""
import os
import sys
import unittest
from unittest import mock

from baton_v12.worker_manager import intake
from tests.manager.test_intake import ATTEMPT, RETENTION, Custodian
from review_cleanup_io_20260926 import CleanupIO


class CleanupTrace(CleanupIO):
    def test_trace_locked_lstats(self):
        self.prepared()
        honest = os.lstat
        stacks = []

        def observed(*args, **kwargs):
            if self.store._connection.in_transaction:
                frame = sys._getframe(1)
                chain = []
                while frame is not None:
                    if "/baton_v12/" in frame.f_code.co_filename:
                        chain.append(f"{frame.f_code.co_filename.rsplit('/', 1)[-1]}:{frame.f_lineno}:{frame.f_code.co_name}")
                    frame = frame.f_back
                stacks.append(" <- ".join(chain))
            return honest(*args, **kwargs)

        with mock.patch.object(os, "lstat", side_effect=observed):
            intake.authorize_cleanup(self.store, self.port, Custodian(),
                                     attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertFalse(stacks, "\n".join(stacks))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([CleanupTrace("test_trace_locked_lstats")])
