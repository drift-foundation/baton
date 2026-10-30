"""Independent disposable unittest outcomes through the real result and accountant.

Run with the prepared Python, from v12/python. No engine or provider execution.
"""
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from tools.parallel_test import StartedResult, account


class Good(unittest.TestCase):
    def test_one(self):
        pass


class SetupError(Good):
    @classmethod
    def setUpClass(cls):
        raise RuntimeError("fixture failure")


class SetupSkip(Good):
    @classmethod
    def setUpClass(cls):
        raise unittest.SkipTest("fixture unavailable")


class ModuleCase(Good):
    pass


class TeardownError(Good):
    @classmethod
    def tearDownClass(cls):
        raise RuntimeError("cleanup failure")


class MessageSubtest(Good):
    def test_one(self):
        with self.subTest("named diagnostic"):
            self.fail("expected probe failure")


def exercise(cls):
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
    ids = [test.id() for test in suite]
    result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=StartedResult).run(suite)
    report = {"label": cls.__name__, "executed": result.started,
              "errors": [{"id": t.id(), "trace": trace} for t, trace in result.errors],
              "failures": [{"id": t.id(), "trace": trace} for t, trace in result.failures],
              "skipped": [{"id": t.id(), "reason": reason} for t, reason in result.skipped]}
    ledger = account(ids, [report], optional={})
    return ledger


results = {cls.__name__: exercise(cls) for cls in (Good, SetupError, SetupSkip, TeardownError, MessageSubtest)}
assert results["Good"]["ok"]
for name in ("SetupError", "SetupSkip"):
    assert not results[name]["ok"]
    assert not results[name]["passed"]
    assert results[name]["unaccounted"] == results[name]["collected"]
assert not results["TeardownError"]["ok"]
assert results["TeardownError"]["fixture_errors"]
print(json.dumps(results, indent=2))
# Expected property: even a message-bearing subtest failure belongs to its
# collected parent. Current B0 accounting violates this; retain the evidence.
bad = results["MessageSubtest"]
if bad["passed"] or bad["failed"] != bad["collected"]:
    print("REPRODUCED: message-bearing subtest failure also counts its parent as passed")
else:
    print("Message-bearing subtest accounting is correct")
