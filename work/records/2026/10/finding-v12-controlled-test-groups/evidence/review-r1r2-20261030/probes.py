"""Independent R1 matrix and R2 scoped-provenance probes, no real engines/Git writes."""
import importlib
import json
import pathlib
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path.cwd()))
from tools import parallel_test as runner, source_identity

with tempfile.TemporaryDirectory(prefix="review-r1r2-") as home:
    root = pathlib.Path(home)
    lines = ["import unittest", "class Matrix(unittest.TestCase):"]
    expected = {"failed": [], "errors": [], "required_skipped": []}
    for shape, arguments in [("message", "'diagnostic (x) [y]'"), ("parameters", "x=1"), ("both", "'diagnostic (x) [y]', x=1")]:
        for outcome, statement, category in [("failure", "self.fail('probe')", "failed"), ("error", "raise ValueError('probe')", "errors"), ("skip", "self.skipTest('probe')", "required_skipped")]:
            name = f"test_{shape}_{outcome}"
            lines.extend([f"    def {name}(self):", f"        with self.subTest({arguments}):", f"            {statement}"])
            expected[category].append("review_matrix.Matrix." + name)
    (root / "review_matrix.py").write_text("\n".join(lines) + "\n")
    sys.path.insert(0, home)
    importlib.invalidate_caches()
    ids = sorted(one for values in expected.values() for one in values)
    plan = root / "plan.json"
    report = root / "report.json"
    plan.write_text(json.dumps({"ids": ids, "report": str(report)}))
    code = runner.run_shard(str(plan))
    answer = json.loads(report.read_text())
    answer["label"] = "independent-matrix"
    ledger = runner.account(ids, [answer], optional={})
    assert code == 1 and not ledger["ok"]
    assert ledger["executed"] == ids and not ledger["passed"]
    for category, wanted in expected.items():
        assert sorted(ledger[category]) == sorted(wanted), (category, ledger)
    assert not ledger["stray_errors"] and not ledger["unaccounted"] and not ledger["uncollected"]
    print(json.dumps({"r1": "PASS", "matrix": ledger}, indent=2))

    # Simulate exactly the read-only git status boundary. The Git parser itself
    # is covered by the six disposable-repository tests in focused.log.
    (root / "v12").mkdir()
    code_file = root / "v12/source.py"
    outside = root / "work/records/fixture.py"
    outside.parent.mkdir(parents=True)
    code_file.write_text("candidate A\n")
    outside.write_text("fixture A\n")
    with patch.object(source_identity, "_git", return_value=b"a" * 40 + b"\n"), patch.object(source_identity, "changed_paths", return_value=[("M", "v12/source.py")]):
        before = source_identity.identity(home, ["v12"])
        code_file.write_text("candidate B\n")
        after_code = source_identity.identity(home, ["v12"])
        assert before["content_digest"] != after_code["content_digest"]
        outside.write_text("fixture B\n")
        after_fixture = source_identity.identity(home, ["v12"])
        assert after_code["content_digest"] == after_fixture["content_digest"]
        print(json.dumps({"r2_same_status_bytes": "PASS", "out_of_scope_fixture_change_detected": False,
                          "before": before["content_digest"], "after_code": after_code["content_digest"],
                          "after_fixture": after_fixture["content_digest"]}, indent=2))
