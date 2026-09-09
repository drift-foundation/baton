"""Budget1s: concrete session late-pass and fence replay, disposable fixture."""
import json
import time
from baton_v12.authority import Refusal
from tests.authority.test_assignment import AuthorityCase, CLAUDE, WORK

start = time.monotonic()
case = AuthorityCase()
case.setUp()
out = {}
try:
    case.work()
    session = case.authority.session(CLAUDE)
    assignment = session.claim({"work_id": WORK, "operation_id": "claim:first"})["assignment"]
    operands = {"expect": assignment, "operation_id": "cancel:first", "reason": "checkpoint"}
    out["fence"] = session.cancel(operands)
    try:
        session.pass_work({"expect": assignment, "operation_id": "late-pass", "to_route": "review"})
    except Refusal as refused:
        out["late_pass_refusal"] = str(refused)
    out["route_after_refusal"] = case.authority.project_work(WORK)["route"]
    out["discharge"] = session.satisfy_gate({"work_id": WORK, "operation_id": "discharge:first", "gate": out["fence"]["gate"], "evidence": {"kind": "runtime-absent", "runtime": "runtime:first"}})
    out["second_assignment"] = session.claim({"work_id": WORK, "operation_id": "claim:second"})["assignment"]
    out["old_fence_replays_after_second_claim"] = session.cancel(operands) == out["fence"]
    out["current_assignment"] = case.authority.project_work(WORK)["assignment"]
finally:
    case.doCleanups()
out["elapsed_seconds"] = time.monotonic() - start
print(json.dumps(out, indent=2))
