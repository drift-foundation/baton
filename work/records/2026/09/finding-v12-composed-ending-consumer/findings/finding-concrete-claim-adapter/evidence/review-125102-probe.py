"""Budget1s: does the diagnostic fallback preserve unrelated failures?"""
import json
import time
from unittest import mock
from baton_v12.authority import Refusal
from tools import single_worker

started = time.monotonic()
real_constructor = single_worker.ContractRefusal
results = []
for failure in (KeyboardInterrupt("stop"), MemoryError("allocation"), RuntimeError("constructor defect")):
    first = [True]
    def construct(*args, **kwargs):
        if first[0]:
            first[0] = False
            raise failure
        return real_constructor(*args, **kwargs)
    with mock.patch.object(single_worker, "ContractRefusal", side_effect=construct):
        try:
            answer = single_worker._claim_refusal(Refusal("wrong route"))
        except BaseException as propagated:
            results.append({"injected": type(failure).__name__, "propagated_identically": propagated is failure})
        else:
            results.append({"injected": type(failure).__name__, "suppressed": True, "replacement": [answer.category, answer.code]})
print(json.dumps({"results": results, "elapsed_seconds": time.monotonic() - started}, indent=2))
