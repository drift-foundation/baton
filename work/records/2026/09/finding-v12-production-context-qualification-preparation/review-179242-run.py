"""Independent focused tests and model diagnostic contradiction observations."""
import importlib.util
import json
from pathlib import Path
import sys
import threading
import unittest

record = Path(__file__).resolve().parent
sys.path.insert(0, str(record / "evidence"))
import test_qualification as tests
c = tests.c
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
if not result.wasSuccessful():
    raise SystemExit(1)

spec = importlib.util.spec_from_file_location("prior_contract", record / "candidate-178875/qualification_contract.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
absent = object()
models = [absent, None, False, 1, [], {}, c.ACTUAL_MODEL, "private-other-model"]
usages = [absent, None, False, 1, [], {}, {c.ACTUAL_MODEL: {}}, {"private-other": {}}, {c.ACTUAL_MODEL: {}, "private-other": {}}, {str(n): {} for n in range(9)}]
matrix = 0
for model in models:
    for usage in usages:
        value = {"type": "result", "subtype": "success", "is_error": False, "session_id": "99eb5f81-572c-4a52-a20b-030aa7023ead"}
        if model is not absent:
            value["model"] = model
        if usage is not absent:
            value["modelUsage"] = usage
        old = prior.projection(c.encoded(value), value["session_id"])
        new = c.projection(c.encoded(value), value["session_id"])
        assert all(new[key] == val for key, val in old.items())
        assert c.consistent(new)
        matrix += 1

# These deliberately malformed worker records exercise the actual arm guard.
# They assert the observed defect, not the behavior needed for acceptance.
observations = []
for label, forged in (
    ("expected-only-with-two-keys", {"model_usage_keys": 2}),
    ("expected-only-with-overflow", {"model_usage_keys": 8, "model_usage_keys_capped": True}),
    ("overflow-below-cap", {"model_usage_keys_capped": True}),
    ("usage-present-but-member-absent", {"members": ["type", "subtype", "is_error", "session_id"]}),
):
    case = tests.Controller()
    case.setUp()
    try:
        fake, outcome = case.execute(forged_terminal=forged)
        terminal = outcome["arms"][0]["terminal"]
        observation = {"case": label, "forged": forged, "outcome": outcome["outcome"], "containers": len(fake.containers), "consistent": c.consistent(terminal), "actual_model": terminal["actual_model"], "model_usage_diagnostic": terminal["model_usage_diagnostic"], "model_usage_keys": terminal["model_usage_keys"], "model_usage_keys_capped": terminal["model_usage_keys_capped"]}
        assert observation["outcome"] == "qualified" and observation["consistent"] is True and observation["containers"] == 2
        observations.append(observation)
    finally:
        case.doCleanups()
live = [t.name for t in threading.enumerate() if t is not threading.main_thread()]
print(json.dumps({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "unchanged_projection_vectors": matrix, "contradiction_observations": observations, "live_threads": live}), flush=True)
assert not live
