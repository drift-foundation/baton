"""Offline W119521 review probe; no live CLI, socket, process or cursor use.

Run from repository root: python3 <this path>.
"""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root))
from tools.test_codex_copilot_notifier import ObligationReminderTests


def run(all_seen=False):
    case = ObligationReminderTests()
    case.setUp()
    case.config["obligation_reminder_seconds"] = 300
    case.config["poll_seconds"] = 300
    case.obligations = [case.obligation(i) for i in range(60)]
    state, _ = case.poll()
    if all_seen:
        # Establish both batches before expiry, then observe ordinary due polls.
        case.now = 1001
        state, _ = case.poll(state)
        assert len(state["seen"]) == 60
    rounds = []
    for instant in (1301, 1601, 1901):
        case.now = instant
        state, answer = case.poll(state)
        event = case.events()[-1]
        rounds.append({"time": instant, "status": answer["status"],
                       "offered": json.loads(event["details"])["changed"],
                       "accepted_count": len(state["seen"])})
    repeated = set(rounds[0]["offered"])
    assert len(repeated) == 50
    assert all(set(row["offered"]) == repeated for row in rounds)
    omitted = sorted(set("obligation:" + str(i) for i in range(60)) - repeated)
    assert len(omitted) == 10
    if all_seen:
        assert all(state["obligation_reminders"][k]["accepted_at"] == 1001
                   for k in omitted)
    else:
        assert all(k not in state["seen"] for k in omitted)
    return {"all_initially_seen": all_seen, "rounds": rounds,
            "permanently_omitted_under_repeated_schedule": omitted}


paths = ("tools/codex_copilot_notifier.py", "tools/test_codex_copilot_notifier.py",
         "tools/CODEX-COPILOT-NOTIFIER.md")
print(json.dumps({"candidate_sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                                        for p in paths},
                  "new_obligation_starvation": run(),
                  "due_reminder_starvation": run(all_seen=True)}, indent=2))
