"""Run the selected unittest IDs unchanged, recording successful subtests too."""
import json, os, sys, unittest
from pathlib import Path
snapshot = Path(os.environ["W384944_SNAPSHOT"])
sys.path[:0] = [str(snapshot / "v12/python/src"), str(snapshot / "v12/python")]
loader = unittest.TestLoader()
suite = loader.loadTestsFromNames(sys.argv[1:])
def ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from ids(item)
        else:
            yield item.id()
expected = list(ids(suite))
class LedgerResult(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.started_ids = []
        self.passed_ids = []
        self.subtests = []
    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)
    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)
    def addSubTest(self, test, subtest, err):
        self.subtests.append({"parent": test.id(), "id": subtest.id(), "outcome": "passed" if err is None else "failed" if issubclass(err[0], test.failureException) else "error"})
        super().addSubTest(test, subtest, err)
result = unittest.TextTestRunner(verbosity=2, resultclass=LedgerResult).run(suite)
ledger = {"collected": expected, "started": result.started_ids, "passed": result.passed_ids, "failed": [test.id() for test, _ in result.failures], "errors": [test.id() for test, _ in result.errors], "skipped": [(test.id(), why) for test, why in result.skipped], "expected_failures": [test.id() for test, _ in result.expectedFailures], "unexpected_successes": [test.id() for test in result.unexpectedSuccesses], "subtests": result.subtests, "unaccounted": sorted(set(expected) - set(result.started_ids)), "duplicates": len(result.started_ids) - len(set(result.started_ids))}
Path(os.environ["W384944_LEDGER"]).write_text(json.dumps(ledger, indent=2) + "\n")
sys.exit(0 if result.wasSuccessful() and not ledger["unaccounted"] and not ledger["duplicates"] and not ledger["skipped"] else 1)
