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


if __name__ == "__main__":
    unittest.main()
