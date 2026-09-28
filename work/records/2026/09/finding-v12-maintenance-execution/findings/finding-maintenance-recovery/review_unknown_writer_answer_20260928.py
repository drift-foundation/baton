"""Unknown writer observation is not positive absence; fake boundary only."""
import unittest
from tests.manager import test_maintenance as fixture
from baton_v12.contracts import ContractRefusal

class UnknownWriterAnswer(unittest.TestCase):
    def test_none_does_not_commit_positive_cleanup(self):
        case = fixture.TheORDINARYEndingCompletesWithNoHelperOrItHolds()
        case.setUp()
        self.addCleanup(case.doCleanups)
        adapter = case.adapter()
        adapter.surviving_helpers = lambda *args, **kwargs: None
        with self.assertRaises(ContractRefusal):
            case.ending(adapter)

if __name__ == "__main__":
    unittest.main()
