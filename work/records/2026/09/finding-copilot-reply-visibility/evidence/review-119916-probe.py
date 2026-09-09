"""Bounded offline correction review; never invokes a live notifier or socket."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root))
from tools.test_codex_copilot_notifier import ObligationReminderTests, FailureNotificationTests

names = ["test_unoffered_obligations_are_not_displaced_by_due_reminders",
         "test_due_reminders_rotate_instead_of_repeating_the_same_fifty",
         "test_the_batch_is_ordered_by_the_oldest_anchor_and_then_by_key",
         "test_new_work_and_failure_attention_lead_a_batch_of_due_reminders",
         "test_ordering_does_not_move_while_a_batch_is_unaccepted"]
output = io.StringIO()
result = unittest.TextTestRunner(stream=output, verbosity=2).run(
    unittest.TestSuite(ObligationReminderTests(name) for name in names))
assert result.wasSuccessful(), output.getvalue()

case = ObligationReminderTests()
case.setUp()
case.obligations = [case.obligation(i) for i in range(50)]
state, _ = case.poll()
failure = FailureNotificationTests()
failure.setUp()
failure.add_runtime()
case.incidents = [failure.incident]
case.runtimes = failure.runtimes
case.now = 1600
state, answer = case.poll(state)
offered = json.loads(case.events()[-1]["details"])["changed"]
assert answer["status"] == "accepted" and len(offered) == 50
assert offered[0] == "incident:36"
assert "runtime:baton.claude" not in offered
assert "runtime:baton.claude" in state["seen"]
assert "runtime:baton.claude" in state["paired"]
omitted = set("obligation:" + str(i) for i in range(50)) - set(offered)
assert len(omitted) == 1
case.now = 1900
state, _ = case.poll(state)
following = json.loads(case.events()[-1]["details"])["changed"]
assert set(following) == omitted

test = (root / "tools/test_codex_copilot_notifier.py").read_text()
start = test.index("    # W119521 review 2026-09-08T14:17:52Z [P2]:")
end = test.index("    def test_config_defaults_accepts_five_minutes", start)
prior = test[:start] + test[end:]
prior_hash = hashlib.sha256(prior.encode()).hexdigest()
assert prior_hash == "dc13e7b9e2c3957ec6112d5de7e50458c15e20183c841aeee0fd549818bba2d7", prior_hash
paths = ["tools/codex_copilot_notifier.py", "tools/test_codex_copilot_notifier.py",
         "tools/CODEX-COPILOT-NOTIFIER.md"]
report = {"claim": 119916, "candidate_sha256": {
    p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths},
    "five_new_controls": output.getvalue(), "prior_48_test_candidate_sha256": prior_hash,
    "mixed_failure": {"first_batch": offered, "following_batch": following,
                      "paired_runtime_acknowledged": True},
    "operator_socket_result": "still required by M119869; not run here"}
(Path(__file__).parent / "review-119916-audit.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
