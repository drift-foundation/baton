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
        self.calls = []
        self.status = {"instanceId": "bridge-1", "targets": {"prompt": dict(participant="baton.prompt", role="prompt", threadId="thread-1", connected=True, deliverable=True, status="idle", queueDepth=0)}}
        self.response = {"accepted": True}

    def read(self, config, verb, *operands):
        self.calls.append((verb, operands))
        return {"authority_uuid": "authority", "result": {"rows": copy.deepcopy(self.rows), "next_after": None} if verb == "actionable-work" else copy.deepcopy(self.obligations)}

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


if __name__ == "__main__":
    unittest.main()
