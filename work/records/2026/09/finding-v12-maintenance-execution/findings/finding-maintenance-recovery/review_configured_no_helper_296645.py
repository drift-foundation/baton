"""Current successor: sentinel remains effective even if dead helper is removed.
Historical probe stays immutable; create=True forbids any late dynamic lookup too.
"""
"""Fake-boundary regression: capability presence does not authorize normalization."""
import unittest
from unittest import mock
from tests.manager.test_maintenance import TheORDINARYEndingCompletesWithNoHelperOrItHolds, intake_module

class ConfiguredNoHelper(unittest.TestCase):
    def test_configured_custodian_is_not_automatic_authority(self):
        case = TheORDINARYEndingCompletesWithNoHelperOrItHolds()
        case.setUp()
        self.addCleanup(case.doCleanups)
        adapter = case.adapter(custodian=True)
        with mock.patch.object(intake_module(), "_normalized", create=True, side_effect=AssertionError("automatic normalization reached despite owner zero-helper selection")):
            case.ending(adapter)

if __name__ == "__main__":
    unittest.main()
