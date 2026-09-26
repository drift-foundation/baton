"""Revalidate prior lock schedules with the new explicit store operand."""
from pathlib import Path
import unittest
from unittest import mock

from baton_v12.worker_manager import ControlStore, workspaces
from tests.manager.test_review_cycles import NOW
from review_restoration_lock_identity_20260926 import LockIdentity


class PinnedLockIdentity(LockIdentity):
    def setUp(self):
        super().setUp()
        store = ControlStore.open(str(Path(self.storage) / 'control.sqlite3'),
                                  incarnation='review-lock-identity', clock=lambda: NOW)
        self.addCleanup(store.close)
        original = workspaces.hold_restoration_lock
        patch = mock.patch.object(workspaces, 'hold_restoration_lock',
            side_effect=lambda storage, line: original(storage, line, control=store))
        patch.start()
        self.addCleanup(patch.stop)


def load_tests(loader, standard, pattern):
    return loader.loadTestsFromTestCase(PinnedLockIdentity)
