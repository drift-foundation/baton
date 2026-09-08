"""Targeted stale-lease probe through real notifier.poll, no socket/CLI/live turn."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
sys.path.insert(0, str(REPO))
from tools.test_codex_copilot_notifier import FailureNotificationTests


def stale_failure():
    fixture = FailureNotificationTests("run")
    fixture.setUp()
    fixture.add_runtime()
    first, accepted = fixture.poll()
    fixture.add_runtime(state="unknown", cause=None, stale=True,
                        since="2026-09-07T22:38:00Z")
    expired, expiry = fixture.poll(first)
    # Canonical runtime_state with an identical report preserves changed_ts
    # while renewing an expired lease: same failure, no intervening recovery.
    fixture.add_runtime(last_contact="2026-09-07T22:39:00Z")
    fixture.response = {"accepted": False, "reason": "duplicate"}
    retried, duplicate = fixture.poll(expired)
    fixture.response = {"accepted": True}
    final, after_window = fixture.poll(retried)
    events = fixture.events()
    return {"initial": accepted, "expired": expiry,
            "seen_after_expiry": expired["seen"],
            "same_failure_renewal": duplicate,
            "same_failure_after_bridge_dedup_window": after_window,
            "delivery_attempt_count": len(events),
            "all_attempts_same_event_id": len({event["id"] for event in events}) == 1,
            "locators": [json.loads(event["details"])["changed"] for event in events]}


def real_recovery_control():
    fixture = FailureNotificationTests("run")
    fixture.setUp()
    fixture.add_runtime()
    state, _ = fixture.poll()
    fixture.add_runtime(state="working")
    state, recovery = fixture.poll(state)
    fixture.add_runtime(since="2026-09-07T22:40:00Z")
    state, recurrence = fixture.poll(state)
    return {"recovery": recovery, "new_failure": recurrence,
            "distinct_ids": len({event["id"] for event in fixture.events()}) == 2}


result = {"stale_lease": stale_failure(), "reported_recovery_control": real_recovery_control(),
          "transport": "in-process test seam models bridge duplicate refusal then acceptance after its finite dedup window; no real advisory sent"}
(HERE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
