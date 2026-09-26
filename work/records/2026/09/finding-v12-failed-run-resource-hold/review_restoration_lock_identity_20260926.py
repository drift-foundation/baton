"""Lock-object identity checks on disposable files, no deployed resources."""
import os
from pathlib import Path
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces


class LockIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='review-restoration-lock-')
        self.addCleanup(self.temp.cleanup)
        self.storage = self.temp.name
        self.line = 'review-line'
        self.place = Path(workspaces.restoration_lock_path(self.storage, self.line))

    def test_replaced_lock_path_cannot_admit_second_holder(self):
        with workspaces.hold_restoration_lock(self.storage, self.line) as first:
            self.assertTrue(first)
            prior = self.place.stat().st_ino
            self.place.rename(self.place.with_suffix('.original'))
            try:
                with workspaces.hold_restoration_lock(self.storage, self.line) as second:
                    self.assertNotEqual(self.place.stat().st_ino, prior)
                    self.assertFalse(second, 'first holder is still live on the prior inode')
            except ContractRefusal:
                pass

    def test_symlink_is_not_accepted_as_lock_object(self):
        self.place.parent.mkdir(parents=True, exist_ok=True)
        target = Path(self.storage) / 'unrelated-file'
        target.write_text('preserve')
        self.place.symlink_to(target)
        try:
            with workspaces.hold_restoration_lock(self.storage, self.line) as acquired:
                self.assertFalse(acquired, 'lock entry followed a symlink')
        except (ContractRefusal, OSError):
            pass


if __name__ == '__main__':
    unittest.main()
