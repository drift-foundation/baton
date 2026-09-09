"""Offline tests: no live Baton mutation, Docker, network provider or model."""
import copy
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from tools import codex_copilot_notifier as notifier


class NotifierTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(baton="/explicit/baton", baton_config="/explicit/baton.json", observer="baton.slaw", prompt_participant="baton.prompt", target="prompt", socket="/explicit/socket", state_file="/explicit/state", timeout_seconds=2, poll_seconds=30)
        self.rows = [dict(id="a-W1", title="First", last_change_seq=4, message_count=1, progress={"children": 0}, route={"endpoint": "baton.ops"})]
        self.obligations = []
        self.incidents = []
        self.runtimes = []
        self.calls = []
        self.status = {"instanceId": "bridge-1", "targets": {"prompt": dict(participant="baton.prompt", role="prompt", threadId="thread-1", connected=True, deliverable=True, status="idle", queueDepth=0)}}
        self.response = {"accepted": True}

    def read(self, config, verb, *operands):
        self.calls.append((verb, operands))
        results = {"actionable-work": {"rows": self.rows, "next_after": None}, "obligations": self.obligations, "incidents": {"rows": self.incidents}, "runtime": {"participants": self.runtimes}}
        return {"authority_uuid": "authority", "result": copy.deepcopy(results[verb])}

    def request(self, config, payload):
        if payload.get("control") == "copilot-status":
            return self.status
        self.calls.append(payload)
        return self.response

    def poll(self, state=None):
        return notifier.poll(self.config, state or {}, self.read, self.request)

    def test_accept_then_deduplicate_and_ignore_volatile_status(self):
        state, result = self.poll()
        self.assertEqual(result["status"], "accepted")
        self.rows[0].update(new=12, agent={"since": "later"}, pickup="overdue")
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        event = next(c for c in self.calls if isinstance(c, dict))
        self.assertNotIn("action", event)
        self.assertNotIn("First", event["details"])

    def test_changed_discussion_or_handoff_notifies(self):
        state, _ = self.poll()
        self.rows[0]["message_count"] += 1
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.rows[0]["last_change_seq"] += 1
        self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_busy_coalesces_and_drops_resolved_before_sending(self):
        self.status["targets"]["prompt"]["status"] = "active"
        state, result = self.poll()
        self.assertEqual(result["status"], "waiting-for-prompt")
        self.assertEqual(state["seen"], {})
        self.rows = []
        self.status["targets"]["prompt"]["status"] = "idle"
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        self.assertFalse(any(isinstance(c, dict) for c in self.calls))

    def test_refusal_and_disconnect_do_not_acknowledge(self):
        self.response = {"accepted": False, "reason": "copilot-busy"}
        state, result = self.poll()
        self.assertEqual(state["seen"], {})
        self.assertEqual(result["status"], "not-accepted")
        with self.assertRaises(OSError):
            notifier.poll(self.config, state, self.read, lambda *_: (_ for _ in ()).throw(OSError()))

    def test_restart_and_thread_change_reconcile(self):
        state, _ = self.poll()
        self.status["instanceId"] = "bridge-2"
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.status["targets"]["prompt"]["threadId"] = "new-thread"
        self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_wrong_participant_or_role_refuses(self):
        for field, wrong in (("participant", "pc.prompt"), ("role", "rview")):
            with self.subTest(field=field):
                original = self.status["targets"]["prompt"][field]
                self.status["targets"]["prompt"][field] = wrong
                with self.assertRaises(ValueError):
                    self.poll()
                self.status["targets"]["prompt"][field] = original

    def test_obligations_filter_by_resolved_handler_not_whole_team(self):
        self.rows = []
        self.obligations = [dict(seq=42, work="a-W2", owed_by={"endpoint": "baton.ops", "handlers": ["slaw"]}), dict(seq=43, owed_by={"endpoint": "baton.impl", "handlers": ["claude"]})]
        state, _ = self.poll()
        self.assertEqual(list(state["seen"]), ["obligation:42"])

    def test_due_trial_generation_is_distinct(self):
        self.rows = []
        self.obligations = [dict(flavor="due_trial", work="a-W3", trial=1, deadline_generation=1, owed_by={"endpoint": "baton.ops", "handlers": ["slaw"]})]
        state, _ = self.poll()
        self.obligations[0]["deadline_generation"] = 2
        self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_pagination_passes_opaque_token_and_authority_mismatch_refuses(self):
        def read(config, verb, *operands):
            value = self.read(config, verb, *operands)
            if verb == "actionable-work" and "after=opaque-token" not in operands:
                value["result"]["next_after"] = "opaque-token"
            return value
        notifier.attention(self.config, read)
        self.assertIn(("actionable-work", ("limit=100", "after=opaque-token")), self.calls)
        def changed_authority(config, verb, *operands):
            value = self.read(config, verb, *operands)
            if verb == "obligations":
                value["authority_uuid"] = "different"
            return value
        with self.assertRaises(ValueError):
            notifier.attention(self.config, changed_authority)

    def test_cli_is_standalone_readonly_and_checks_envelope(self):
        value = dict(protocol_version=11, participant="baton.slaw", authority_uuid="authority", result=[])
        with patch.object(notifier.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(value)
            notifier.baton_read(self.config, "obligations")
            self.assertEqual(run.call_args.args[0], ["/explicit/baton", "--config", "/explicit/baton.json", "--participant", "baton.slaw", "obligations"])
            self.assertNotIn("shell", run.call_args.kwargs)
            with self.assertRaises(ValueError):
                notifier.baton_read(self.config, "claim", "work=W1")
            run.return_value.stdout = json.dumps({**value, "participant": "other"})
            with self.assertRaises(ValueError):
                notifier.baton_read(self.config, "obligations")

    def test_state_survives_reload_with_private_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cursor.json"
            state, _ = self.poll()
            notifier.save_state(path, state)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.poll(json.loads(path.read_text()))[1]["status"], "unchanged")

    def test_unix_socket_wire_uses_one_json_line(self):
        with tempfile.TemporaryDirectory() as temp:
            config = {**self.config, "socket": str(Path(temp) / "events.sock")}
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(config["socket"])
                server.listen()
                received = []
                def serve():
                    conn, _ = server.accept()
                    with conn:
                        with conn.makefile("rb") as incoming:
                            received.append(json.loads(incoming.readline()))
                        conn.sendall(b'{"accepted":true}\n')
                thread = threading.Thread(target=serve)
                thread.start()
                self.assertEqual(notifier.bridge_request(config, {"target": "prompt"}), {"accepted": True})
                thread.join(timeout=2)
                self.assertFalse(thread.is_alive())
                self.assertEqual(received, [{"target": "prompt"}])

    def test_config_and_dry_run_never_send_or_write(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(self.config))
            with patch.object(notifier, "attention", return_value=("authority", {"work:a-W1": {}})), patch.object(notifier, "bridge_request") as send, patch.object(notifier, "save_state") as save, patch("builtins.print"):
                self.assertEqual(notifier.main(["--config", str(path), "--dry-run"]), 0)
                send.assert_not_called()
                save.assert_not_called()
            path.write_text(json.dumps({**self.config, "socket": "relative"}))
            with self.assertRaises(ValueError):
                notifier.read_config(path)


class FailureNotificationTests(unittest.TestCase):
    # Reuse the transport fixtures, not the inherited test cases.
    read = NotifierTests.read
    request = NotifierTests.request
    poll = NotifierTests.poll

    def setUp(self):
        NotifierTests.setUp(self)
        self.rows = []  # A stranded implementation claim is not operator Work.
        self.failed = dict(action_owner="baton.slaw", state="failed", incarnation="lease-1", session="session-1", work="a-W110935", episode=114003, cause="internal", since="2026-09-07T22:36:22Z")
        self.incident = dict(participant="baton.claude", incident=36, open=True, first_ts="2026-09-07T22:36:22Z", category="other", **{k: v for k, v in self.failed.items() if k not in {"state", "since"}})

    def add_runtime(self, **changes):
        self.runtimes = [dict(participant="baton.claude", runtime={**self.failed, **changes})]

    def events(self):
        return [c for c in self.calls if isinstance(c, dict)]

    def test_stranded_claim_incident_notifies_without_operator_work(self):
        self.incidents = [self.incident]
        state, result = self.poll()
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[0]["details"])["changed"], ["incident:36"])
        self.incident.update(latest_ts="later", occurrences=99, detail="private diagnostic")
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        self.assertNotIn("private diagnostic", json.dumps(self.events()))

    def test_runtime_without_incident_notifies_and_heartbeats_do_not(self):
        self.add_runtime(detail="private diagnostic")
        state, result = self.poll()
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[0]["details"])["changed"], ["runtime:baton.claude"])
        self.runtimes[0]["runtime"].update(last_contact="later", expires_at="later", stale=True, facts=[{"age_seconds": 300}])
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        self.assertNotIn("private diagnostic", json.dumps(self.events()))

    def test_simultaneous_failure_and_incident_emit_one_locator(self):
        self.add_runtime()
        self.incidents = [self.incident]
        state, result = self.poll()
        self.assertEqual(result["changed"], 1)
        self.assertEqual(json.loads(self.events()[0]["details"])["changed"], ["incident:36"])
        self.assertEqual(len(state["seen"]), 2)
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")

    def test_late_incident_is_covered_by_accepted_runtime_across_reload(self):
        self.add_runtime()
        state, _ = self.poll()
        self.incidents = [self.incident]
        state, result = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(result["status"], "unchanged")
        self.assertIn("incident:36", state["seen"])
        self.assertEqual(len(self.events()), 1)

    def test_late_runtime_and_incident_dismissal_do_not_duplicate(self):
        self.incidents = [self.incident]
        state, _ = self.poll()
        self.add_runtime()
        state, result = self.poll(state)
        self.assertEqual(result["status"], "unchanged")
        self.incidents = []
        state, result = self.poll(state)
        self.assertEqual(result["status"], "unchanged")
        self.assertNotIn("incident:36", state["seen"])

    def test_owner_filter_is_exact_for_both_sources(self):
        self.incidents = [{**self.incident, "action_owner": "pc.slaw"}, {**self.incident, "open": False}]
        self.add_runtime(action_owner="pc.slaw")
        self.assertEqual(self.poll()[1]["status"], "unchanged")

    def test_nonfailed_states_are_not_alerts(self):
        for state in ("idle", "working", "offline", "waiting"):
            with self.subTest(state=state):
                self.add_runtime(state=state)
                self.assertEqual(self.poll()[1]["status"], "unchanged")

    def test_recurrence_after_recovery_notifies_with_same_work_and_session(self):
        self.add_runtime()
        self.incidents = [self.incident]
        state, _ = self.poll()
        self.add_runtime(state="working")
        state, result = self.poll(state)
        self.assertEqual(result["status"], "unchanged")
        self.add_runtime(since="2026-09-07T22:40:00Z")
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["runtime:baton.claude"])
        self.incidents.append({**self.incident, "incident": 37, "first_ts": "2026-09-07T22:40:01Z"})
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")

    def test_new_failure_between_polls_notifies(self):
        self.add_runtime()
        state, _ = self.poll()
        self.add_runtime(since="2026-09-07T22:40:00Z")
        self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_new_incident_after_dismissal_is_not_hidden_by_old_runtime(self):
        self.add_runtime()
        self.incidents = [self.incident]
        state, _ = self.poll()
        self.incidents = []
        state, _ = self.poll(state)
        self.incidents = [{**self.incident, "incident": 37, "first_ts": "2026-09-07T22:40:00Z"}]
        state, result = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["incident:37"])

    def test_other_episode_or_session_incidents_are_not_hidden(self):
        for field, value in (("episode", 114108), ("session", "other"), ("incarnation", "other"), ("cause", "credential"), ("work", "a-W2")):
            with self.subTest(field=field):
                self.add_runtime()
                self.incidents = [{**self.incident, field: value}]
                self.assertEqual(self.poll()[1]["changed"], 2)

    def test_missing_correlation_never_hides_incident(self):
        self.add_runtime(incarnation=None)
        self.incidents = [{**self.incident, "incarnation": None}]
        self.assertEqual(self.poll()[1]["changed"], 2)

    def test_busy_failure_recovery_prunes_without_alert(self):
        self.add_runtime()
        self.status["targets"]["prompt"]["status"] = "active"
        state, result = self.poll()
        self.assertEqual(result["status"], "waiting-for-prompt")
        self.assertEqual(state["seen"], {})
        self.add_runtime(state="idle")
        self.status["targets"]["prompt"]["status"] = "idle"
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        self.assertEqual(self.events(), [])

    def test_rejected_correlated_advisory_remains_pending(self):
        self.add_runtime()
        self.incidents = [self.incident]
        self.response = {"accepted": False}
        state, result = self.poll()
        self.assertEqual(result["status"], "not-accepted")
        self.assertEqual(state["seen"], {})
        self.response = {"accepted": True}
        self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_failed_read_or_foreign_authority_never_sends(self):
        for verb in ("incidents", "runtime"):
            for failure in ("read", "authority"):
                with self.subTest(verb=verb, failure=failure):
                    def read(config, command, *operands):
                        if command == verb and failure == "read":
                            raise RuntimeError("unavailable")
                        result = self.read(config, command, *operands)
                        if command == verb:
                            result["authority_uuid"] = "foreign"
                        return result
                    with self.assertRaises((RuntimeError, ValueError)):
                        notifier.poll(self.config, {}, read, self.request)
                    self.assertEqual(self.events(), [])

    def expire_runtime(self, **changes):
        self.add_runtime(**dict(state="unknown", provenance="derived", stale=True, cause=None, since="2026-09-07T22:38:00Z", **changes))

    def test_accepted_failure_survives_expiry_reload_and_identical_renewal(self):
        self.add_runtime()
        state, _ = self.poll()
        accepted = copy.deepcopy(state)
        self.expire_runtime()
        state, result = self.poll(state)
        self.assertEqual(result, {"status": "unchanged", "attention": 0})
        self.assertEqual(state, accepted)
        self.add_runtime(last_contact="2026-09-07T22:39:00Z")
        # Even an accepting transport past its dedup window must receive no retry.
        state, result = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(len(self.events()), 1)

    def test_unrelated_delivery_during_expiry_preserves_accepted_failure(self):
        self.add_runtime()
        state, _ = self.poll()
        accepted_runtime = state["seen"]["runtime:baton.claude"]
        self.expire_runtime()
        self.rows = [dict(id="a-W2", last_change_seq=7)]
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["work:a-W2"])
        self.assertEqual(state["seen"]["runtime:baton.claude"], accepted_runtime)
        self.add_runtime()
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        self.assertEqual(len(self.events()), 2)

    def test_paired_expiry_dismissal_renewal_and_new_incident(self):
        self.add_runtime()
        self.incidents = [self.incident]
        state, _ = self.poll()
        accepted_pair = copy.deepcopy(state["paired"])
        self.expire_runtime()
        self.incidents = []
        self.rows = [dict(id="a-W2", last_change_seq=7)]
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertNotIn("incident:36", state["seen"])
        self.assertEqual(state["paired"], accepted_pair)
        self.add_runtime()
        state, result = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(len(self.events()), 2)
        self.incidents = [{**self.incident, "incident": 37, "first_ts": "2026-09-07T22:40:00Z"}]
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["incident:37"])

    def test_expiry_never_acknowledges_rejected_or_busy_attention(self):
        for delivery in ("rejected", "busy"):
            for paired in (False, True):
                with self.subTest(delivery=delivery, paired=paired):
                    self.setUp()
                    self.add_runtime()
                    self.incidents = [self.incident] if paired else []
                    self.response = {"accepted": delivery != "rejected"}
                    self.status["targets"]["prompt"]["status"] = "active" if delivery == "busy" else "idle"
                    state, _ = self.poll()
                    self.assertEqual(state["seen"], {})
                    self.expire_runtime()
                    state, _ = self.poll(state)
                    self.assertEqual(state["seen"], {})
                    self.assertEqual(state["paired"], {})
                    self.add_runtime()
                    self.response = {"accepted": True}
                    self.status["targets"]["prompt"]["status"] = "idle"
                    state, result = self.poll(state)
                    self.assertEqual(result["status"], "accepted")
                    self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["incident:36" if paired else "runtime:baton.claude"])
                    self.assertEqual(self.poll(state)[1]["status"], "unchanged")

    def test_only_derived_expiry_preserves_memory_and_recovery_allows_failure(self):
        for ending in ("reported-unknown", "working", "offline", "absent", "other-owner"):
            with self.subTest(ending=ending):
                self.setUp()
                self.add_runtime()
                self.incidents = [self.incident]
                state, _ = self.poll()
                self.expire_runtime()
                state, _ = self.poll(state)
                if ending == "absent":
                    self.runtimes = []
                elif ending == "other-owner":
                    self.expire_runtime(action_owner="pc.slaw")
                else:
                    self.add_runtime(state="unknown" if ending == "reported-unknown" else ending, provenance="reported", stale=False)
                state, result = self.poll(state)
                self.assertEqual(result["status"], "unchanged")
                self.assertNotIn("runtime:baton.claude", state["seen"])
                self.assertEqual(state["paired"], {})
                self.add_runtime(since="2026-09-07T22:40:00Z")
                self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_stale_replacement_does_not_cover_its_failed_report(self):
        self.add_runtime()
        self.incidents = [self.incident]
        state, _ = self.poll()
        self.expire_runtime(incarnation="lease-2")
        state, result = self.poll(state)
        self.assertEqual(result["status"], "unchanged")
        self.add_runtime(incarnation="lease-2")
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["runtime:baton.claude"])
        self.assertEqual(state["paired"], {})

    def test_first_observed_expiry_is_not_attention_or_acceptance(self):
        self.expire_runtime()
        state, result = self.poll()
        self.assertEqual(result, {"status": "unchanged", "attention": 0})
        self.assertEqual(state["seen"], {})
        self.assertEqual(state["paired"], {})
        self.assertEqual(self.events(), [])
        self.add_runtime()
        self.assertEqual(self.poll(state)[1]["status"], "accepted")

    def test_new_failure_transition_after_expiry_notifies(self):
        self.add_runtime()
        state, _ = self.poll()
        self.expire_runtime()
        state, _ = self.poll(state)
        self.add_runtime(since="2026-09-07T22:40:00Z")
        self.assertEqual(self.poll(state)[1]["status"], "accepted")
        self.assertNotEqual(self.events()[0]["id"], self.events()[1]["id"])


class ObligationReminderTests(unittest.TestCase):
    read = NotifierTests.read
    request = NotifierTests.request
    events = FailureNotificationTests.events

    def setUp(self):
        NotifierTests.setUp(self)
        self.rows = []
        self.now = 1000
        self.obligations = [self.obligation(42)]

    def obligation(self, seq):
        return dict(seq=seq, work="a-W2", flavor="response", status="pending", owed_by={"endpoint": "baton.ops", "handlers": ["slaw"]})

    def poll(self, state=None):
        return notifier.poll(self.config, state or {}, self.read, self.request, clock=lambda: self.now)

    def test_default_expiry_coalesces_and_successive_generations_are_distinct(self):
        self.obligations.append(self.obligation(43))
        state, _ = self.poll()
        original_id = self.events()[-1]["id"]
        self.now = 1599
        state, result = self.poll(state)
        self.assertEqual(result["status"], "unchanged")
        self.now = 1600
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["obligation:42", "obligation:43"])
        reminder_id = self.events()[-1]["id"]
        self.assertNotEqual(original_id, reminder_id)
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["generation"], 2)
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["accepted_at"], 1600)
        self.now = 2200
        self.assertEqual(self.poll(state)[1]["status"], "accepted")
        self.assertNotIn(self.events()[-1]["id"], [original_id, reminder_id])

    def test_busy_and_rejected_reminders_keep_the_timer_and_retry_identity(self):
        state, _ = self.poll()
        original = copy.deepcopy(state)
        self.now = 1600
        self.status["targets"]["prompt"]["status"] = "active"
        state, result = self.poll(state)
        self.assertEqual(result["status"], "waiting-for-prompt")
        self.assertEqual(state, original)
        self.assertEqual(len(self.events()), 1)
        self.status["targets"]["prompt"]["status"] = "idle"
        self.response = {"accepted": False, "reason": "copilot-busy"}
        state, result = self.poll(state)
        retry_id = self.events()[-1]["id"]
        self.assertEqual(result["status"], "not-accepted")
        self.assertEqual(state, original)
        self.now = 1900
        self.response = {"accepted": True}
        state, _ = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(self.events()[-1]["id"], retry_id)
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["accepted_at"], 1900)

    def test_resolution_or_lost_handler_prunes_due_reminders_before_send(self):
        for change in ("resolved", "other-handler"):
            with self.subTest(change=change):
                self.setUp()
                state, _ = self.poll()
                self.now = 1600
                if change == "resolved":
                    self.obligations = []
                else:
                    self.obligations[0]["owed_by"]["handlers"] = ["claude"]
                state, result = self.poll(state)
                self.assertEqual(result["status"], "unchanged")
                self.assertEqual(state["seen"], {})
                self.assertEqual(state.get("obligation_reminders", {}), {})
                self.assertEqual(len(self.events()), 1)

    def test_unrelated_accepted_attention_does_not_postpone_obligation(self):
        state, _ = self.poll()
        reminder = copy.deepcopy(state["obligation_reminders"]["obligation:42"])
        self.now = 1599
        self.rows = [dict(id="a-W3", last_change_seq=7)]
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(state["obligation_reminders"]["obligation:42"], reminder)
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["work:a-W3"])
        self.now = 1600
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["obligation:42"])

    def test_new_and_changed_obligations_are_immediate(self):
        state, _ = self.poll()
        self.now = 1001
        self.obligations[0]["work"] = "a-W4"
        self.obligations.append(self.obligation(43))
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["obligation:42", "obligation:43"])
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["accepted_at"], 1001)
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["generation"], 2)
        self.assertEqual(state["obligation_reminders"]["obligation:43"]["generation"], 1)

    def test_disabled_reminders_reenable_from_last_acceptance_and_allow_changes(self):
        self.config["obligation_reminder_seconds"] = 0
        state, _ = self.poll()
        self.now = 9999
        state, result = self.poll(state)
        self.assertEqual(result["status"], "unchanged")
        self.obligations.append(self.obligation(43))
        state, _ = self.poll(state)
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["accepted_at"], 1000)
        self.config["obligation_reminder_seconds"] = 300
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"], ["obligation:42"])

    def test_five_minute_interval_and_persisted_restart(self):
        self.config["obligation_reminder_seconds"] = 300
        state, _ = self.poll()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cursor.json"
            notifier.save_state(path, state)
            self.now = 1299
            self.assertEqual(self.poll(json.loads(path.read_text()))[1]["status"], "unchanged")
            self.now = 1300
            self.assertEqual(self.poll(json.loads(path.read_text()))[1]["status"], "accepted")

    def test_legacy_migration_is_one_anchor_not_a_fabricated_acceptance(self):
        state, _ = self.poll()
        del state["obligation_reminders"]
        self.now = 2000
        self.status["targets"]["prompt"]["status"] = "active"
        state, result = self.poll(state)
        record = copy.deepcopy(state["obligation_reminders"]["obligation:42"])
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(record["migration_at"], 2000)
        self.assertIsNone(record["accepted_at"])
        self.assertEqual(record["generation"], 0)
        self.now = 2500
        state, _ = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(state["obligation_reminders"]["obligation:42"], record)
        self.status["targets"]["prompt"]["status"] = "idle"
        self.rows = [dict(id="a-W3")]
        state, _ = self.poll(state)
        self.assertEqual(state["obligation_reminders"]["obligation:42"], record)
        self.now = 2600
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["accepted_at"], 2600)

    def test_trial_and_verification_attention_remain_change_based(self):
        self.obligations = [dict(seq=42, flavor="verification", work="a-W2", owed_by={"endpoint": "baton.ops", "handlers": ["slaw"]}), dict(flavor="due_trial", work="a-W3", trial=1, deadline_generation=1, owed_by={"endpoint": "baton.ops", "handlers": ["slaw"]})]
        state, _ = self.poll()
        self.now = 9999
        self.assertEqual(self.poll(state)[1]["status"], "unchanged")
        self.assertNotIn("obligation_reminders", state)

    def test_only_the_fifty_offered_obligations_get_accepted_timers(self):
        self.obligations = [self.obligation(i) for i in range(60)]
        state, _ = self.poll()
        offered = set(json.loads(self.events()[-1]["details"])["changed"])
        self.assertEqual(len(offered), 50)
        self.assertEqual(set(state["seen"]), offered)
        self.assertEqual(set(state["obligation_reminders"]), offered)
        self.now = 1001
        state, _ = self.poll(state)
        remaining = set(json.loads(self.events()[-1]["details"])["changed"])
        self.assertEqual(len(remaining), 10)
        self.assertFalse(remaining & offered)
        self.assertEqual(len(state["obligation_reminders"]), 60)
        self.assertTrue(all(state["obligation_reminders"][k]["accepted_at"] == 1000 for k in offered))

    def test_acceptance_uses_acknowledgement_time_and_transport_failure_changes_nothing(self):
        original_request = self.request

        def delayed(config, payload):
            if "control" not in payload:
                self.now += 12
            return original_request(config, payload)

        self.request = delayed
        state, _ = self.poll()
        self.assertEqual(state["obligation_reminders"]["obligation:42"]["accepted_at"], 1012)
        unchanged = copy.deepcopy(state)
        self.now = 1612

        def broken(config, payload):
            if "control" not in payload:
                raise OSError("lost acknowledgement")
            return original_request(config, payload)

        self.request = broken
        with self.assertRaises(OSError):
            self.poll(state)
        self.assertEqual(state, unchanged)

    # W119521 review 2026-09-08T14:17:52Z [P2]: the two reproduced starvation
    # scenarios, and the mixed-attention interaction they sit in.
    #
    # THE DEFECT THESE REPLACE A GAP IN. The existing sixty-obligation control
    # above polls the remainder BEFORE any reminder is due, so it never sees the
    # interaction: once accepted reminders become eligible again, a key-ordered
    # batch hands the same lexicographically first fifty back forever. Both
    # cases below run the schedule the reviewer measured -- a supported
    # 300-second reminder and poll interval, sixty obligations, three
    # consecutive due polls -- and require the omitted ten to make progress.

    def sixty_at(self, *instants, all_seen=False):
        """Three consecutive eligible polls over sixty obligations.

        Answers what each poll OFFERED, so a case can assert progress across
        them rather than the contents of any one batch.
        """
        self.config["obligation_reminder_seconds"] = 300
        self.config["poll_seconds"] = 300
        self.obligations = [self.obligation(i) for i in range(60)]
        state, _ = self.poll()
        if all_seen:
            # Establish BOTH batches before anything expires, so what follows is
            # purely the due-reminder rotation.
            self.now = 1001
            state, _ = self.poll(state)
            self.assertEqual(len(state["seen"]), 60)
        offered = []
        for instant in instants:
            self.now = instant
            state, result = self.poll(state)
            self.assertEqual(result["status"], "accepted")
            offered.append(json.loads(self.events()[-1]["details"])["changed"])
        return state, offered

    def test_unoffered_obligations_are_not_displaced_by_due_reminders(self):
        """Scenario one: ten obligations never received an INITIAL advisory.

        The first batch takes fifty; by the next eligible poll those fifty are
        due again, and a key-ordered merge handed them the whole batch a second
        and third time. New attention keeps its immediate contract, so the ten
        lead the batch instead.
        """
        state, offered = self.sixty_at(1301, 1601, 1901)
        everyone = {"obligation:" + str(one) for one in range(60)}
        self.assertEqual([len(one) for one in offered], [50, 50, 50])
        # THE TEN GET THEIR FIRST ADVISORY, and they get it at the FIRST
        # opportunity rather than eventually: they are fresh, not due.
        self.assertEqual(set(offered[0]) & (everyone - set(offered[0])), set())
        self.assertTrue(everyone - set(offered[0]) <= set(offered[1]))
        self.assertEqual(set(offered[0]) | set(offered[1]), everyone)
        self.assertEqual(set(state["seen"]), everyone)
        self.assertEqual(set(state["obligation_reminders"]), everyone)

    def test_due_reminders_rotate_instead_of_repeating_the_same_fifty(self):
        """Scenario two: all sixty were accepted first, so every item is DUE.

        A key-ordered batch left the same ten holding `accepted_at` 1001 forever
        while the other fifty advanced. Ordering by each record's own anchor is
        what rotates them: acceptance moves a record to the back, so the ten
        that waited longest lead the next eligible poll.
        """
        state, offered = self.sixty_at(1301, 1601, 1901, all_seen=True)
        everyone = {"obligation:" + str(one) for one in range(60)}
        self.assertEqual([len(one) for one in offered], [50, 50, 50])
        self.assertNotEqual(set(offered[0]), set(offered[1]))
        self.assertEqual(set(offered[0]) | set(offered[1]), everyone)
        # NOBODY IS LEFT ON THE ORIGINAL ANCHOR. The measured defect kept ten at
        # 1001 indefinitely; every record has advanced past it.
        self.assertTrue(all(record["accepted_at"] > 1001
                            for record in state["obligation_reminders"].values()))

    def test_the_batch_is_ordered_by_the_oldest_anchor_and_then_by_key(self):
        """The ordering rule itself, asked directly rather than inferred.

        Two obligations are made due with different anchors and a third shares
        one of them, so the case measures both halves: the oldest anchor leads,
        and the key breaks a tie without becoming the sort.
        """
        self.obligations = [self.obligation(one) for one in (7, 8, 9)]
        state, _ = self.poll()
        # Give `obligation:9` the oldest anchor and leave the other two equal.
        state["obligation_reminders"]["obligation:9"]["accepted_at"] = 100
        self.now = 1600
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"],
                         ["obligation:9", "obligation:7", "obligation:8"])

    def test_new_work_and_failure_attention_lead_a_batch_of_due_reminders(self):
        """The mixed case: fresh attention of every kind keeps its immediate
        contract, and due reminders follow it rather than crowding it out."""
        self.obligations = [self.obligation(one) for one in range(50)]
        state, _ = self.poll()
        self.assertEqual(
            len(json.loads(self.events()[-1]["details"])["changed"]), 50)
        self.now = 1600
        self.rows = [dict(id="a-W1", title="First", last_change_seq=4,
                          message_count=1, progress={"children": 0},
                          route={"endpoint": "baton.ops"})]
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        offered = json.loads(self.events()[-1]["details"])["changed"]
        self.assertEqual(offered[0], "work:a-W1")
        self.assertEqual(len(offered), 50)
        # AND THE DISPLACED REMINDER IS NOT LOST: it holds the oldest anchor, so
        # it leads the next eligible batch.
        self.now = 1900
        state, result = self.poll(state)
        self.assertEqual(result["status"], "accepted")
        following = json.loads(self.events()[-1]["details"])["changed"]
        self.assertEqual(set(offered[1:]) | set(following),
                         {"obligation:" + str(one) for one in range(50)})

    def test_ordering_does_not_move_while_a_batch_is_unaccepted(self):
        """Retry identity, over the new ordering. Anchors move only when an
        OFFERED locator is accepted, so a refused batch composes the same event
        again rather than reshuffling underneath the retry."""
        self.obligations = [self.obligation(one) for one in range(60)]
        state, _ = self.poll()
        self.now = 1600
        self.response = {"accepted": False, "reason": "copilot-busy"}
        state, result = self.poll(state)
        self.assertEqual(result["status"], "not-accepted")
        refused = self.events()[-1]
        state, result = self.poll(json.loads(json.dumps(state)))
        self.assertEqual(result["status"], "not-accepted")
        self.assertEqual(self.events()[-1]["id"], refused["id"])
        self.assertEqual(json.loads(self.events()[-1]["details"])["changed"],
                         json.loads(refused["details"])["changed"])

    def test_config_defaults_accepts_five_minutes_and_zero_and_refuses_invalid_values(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(self.config))
            self.assertEqual(notifier.read_config(path)["obligation_reminder_seconds"], 600)
            for value in (300, 0, 600):
                path.write_text(json.dumps({**self.config, "obligation_reminder_seconds": value}))
                self.assertEqual(notifier.read_config(path)["obligation_reminder_seconds"], value)
            for value in (-1, True, "300", None, float("nan"), float("inf")):
                with self.subTest(value=value):
                    path.write_text(json.dumps({**self.config, "obligation_reminder_seconds": value}))
                    with self.assertRaises(ValueError):
                        notifier.read_config(path)


if __name__ == "__main__":
    unittest.main()
