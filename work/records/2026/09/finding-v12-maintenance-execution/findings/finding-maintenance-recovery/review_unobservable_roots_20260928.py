"""Unobservable roots cannot become positively absent output; fake boundary only."""
import unittest
from unittest import mock
from tests.manager import test_maintenance as fixture
from baton_v12.worker_manager import intake, custody
from baton_v12.contracts import ContractRefusal

class UnobservableRoots(unittest.TestCase):
    def setUp(self):
        self.case = fixture.TheORDINARYEndingCompletesWithNoHelperOrItHolds()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def record(self):
        return intake._record_writer_cessation(self.case.case.store, self.case.adapter(), self.case.intake.ATTEMPT,
            attempt=self.case.case.attempt_row(), operation={"operation_id":"review-unobservable"}, observed={"state":"absent"})

    def test_underivable_is_not_absent(self):
        with mock.patch.object(custody, "_derived_root", side_effect=ContractRefusal("refused", "precondition", "root identity unknown")):
            with self.assertRaises(ContractRefusal):
                self.record()

    def test_permission_denied_is_not_absent(self):
        real = intake.os.lstat
        def inaccessible(path, *args, **kwargs):
            if path == "/review-unobservable":
                raise PermissionError("cannot observe root")
            return real(path, *args, **kwargs)
        with mock.patch.object(custody, "_derived_root", return_value=("/review-unobservable", 0, None)), mock.patch.object(intake.os, "lstat", side_effect=inaccessible):
            with self.assertRaises(ContractRefusal):
                self.record()

if __name__ == "__main__":
    unittest.main()
