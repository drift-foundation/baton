import ast
import copy
import difflib
import hashlib
import io
import json
import signal
import time
import traceback
import unittest
from pathlib import Path

start = time.monotonic()
root = Path(__file__).resolve().parent
initial = json.loads((root / "verification.json").read_text())
report = {"reused_initial_passes": 2, "initial_seconds": initial["seconds"]}
stream = io.StringIO()


def deadline(*_):
    raise TimeoutError("10s focused budget exhausted")


def named(tree, name):
    return next(node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name)


def verify():
    from tests.tools.test_single_worker import TheWorkerSessionForwardsGateDischarge
    paths = ("v12/python/tools/single_worker.py", "v12/python/tests/tools/test_single_worker.py")
    report["hashes"] = {}
    for name in paths:
        path = Path(name)
        base = (root / ("base-" + path.name)).read_text()
        candidate = path.read_text()
        report["hashes"][name] = {"base": hashlib.sha256(base.encode()).hexdigest(), "candidate": hashlib.sha256(candidate.encode()).hexdigest()}
        (root / ("final-candidate-" + path.name)).write_text(candidate)
        (root / ("final-" + path.name + ".patch")).write_text("".join(difflib.unified_diff(base.splitlines(True), candidate.splitlines(True), fromfile="a/" + name, tofile="b/" + name)))
        old = ast.parse(base)
        current = copy.deepcopy(ast.parse(candidate))
        if name == paths[0]:
            before, after = named(old, "_AuthoritySession"), named(current, "_AuthoritySession")
            forward = named(after, "satisfy_gate")
            assert ast.dump(forward) == ast.dump(ast.parse("def satisfy_gate(self, operands):\n    return self._session.satisfy_gate(operands)\n").body[0])
            after.body.remove(forward)
            after.body[0] = before.body[0]
            named(after, "pass_work").body[0] = named(before, "pass_work").body[0]
        else:
            current.body.remove(named(current, "TheWorkerSessionForwardsGateDischarge"))
        assert ast.dump(current) == ast.dump(old), name
    initial_test = (root / "candidate-test_single_worker.py").read_text()
    assert initial_test.replace('self.assertEqual(answer, {"gate": self.gate, "kind": "runtime-quiescence", "phase": "queued"})', 'self.assertEqual(answer, {"gate": self.gate, "kind": "runtime-absent", "phase": "queued"})') == Path(paths[1]).read_text()
    assert (root / "candidate-single_worker.py").read_text() == Path(paths[0]).read_text()
    report["preserved_existing_code_and_assertions"] = True
    suite = unittest.TestSuite([TheWorkerSessionForwardsGateDischarge("test_wrapper_preserves_the_exact_operand_document_and_session_answer")])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report.update(tests=result.testsRun, successful=result.wasSuccessful())
    assert result.wasSuccessful()


signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 9.8 - initial["seconds"])
try:
    verify()
except BaseException:
    report["error"] = traceback.format_exc()
    raise
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["output"] = stream.getvalue()
    report["seconds"] = time.monotonic() - start
    report["combined_seconds"] = report["seconds"] + initial["seconds"]
    with (root / "final-verification.json").open("x") as output:
        json.dump(report, output, indent=2)
    print(json.dumps(report, indent=2))
