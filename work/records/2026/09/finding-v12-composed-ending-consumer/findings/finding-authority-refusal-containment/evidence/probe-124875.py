"""Budget1s: reproduce concrete claim refusal through the serving sweep."""
import json
import time
from baton_v12.authority import Refusal
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import ComposedOneJobCase

start = time.monotonic()
case = ComposedOneJobCase()
case.setUp()
out = {}
try:
    held = case.implemented()
    for step in range(4):
        try:
            sweep(held.job, held.composed, now=fixtures.NOW)
        except Refusal as refusal:
            out = {"tick": step + 1, "type": type(refusal).__module__ + "." + type(refusal).__name__, "message": str(refusal), "code": refusal.code, "durable": refusal.durable, "is_contract_refusal": isinstance(refusal, ContractRefusal)}
            break
    assert out, "expected the reported concrete route refusal"
finally:
    case.doCleanups()
out["elapsed_seconds"] = time.monotonic() - start
print(json.dumps(out, indent=2))
