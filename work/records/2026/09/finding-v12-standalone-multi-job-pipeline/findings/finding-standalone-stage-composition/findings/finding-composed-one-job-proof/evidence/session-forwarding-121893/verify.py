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
report = {}
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
        (root / ("candidate-" + path.name)).write_text(candidate)
        (root / (path.name + ".patch")).write_text("".join(difflib.unified_diff(base.splitlines(True), candidate.splitlines(True), fromfile="a/" + name, tofile="b/" + name)))
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
    report["preserved_existing_code_and_assertions"] = True
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TheWorkerSessionForwardsGateDischarge)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report.update(tests=result.testsRun, successful=result.wasSuccessful())
    assert result.wasSuccessful()


signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 9.8)
try:
    verify()
except BaseException:
    report["error"] = traceback.format_exc()
    raise
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["output"] = stream.getvalue()
    report["seconds"] = time.monotonic() - start
    with (root / "verification.json").open("x") as output:
        json.dump(report, output, indent=2)
    print(json.dumps(report, indent=2))
