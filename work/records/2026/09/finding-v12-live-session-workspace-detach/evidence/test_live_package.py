"""Offline W106673 failure-boundary tests. No Docker, provider or real source."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock
import uuid
import sys

sys.dont_write_bytecode = True

import host_runner as base
import live_controller as controller
import live_supervisor as wire
import real_session_contract as contract

SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


class StreamTests(unittest.TestCase):
    def test_partial_line_does_not_escape_deadline(self):
        read, write = os.pipe()
        try:
            os.write(write, b'{"partial":')
            with self.assertRaisesRegex(wire.Refusal, "stream-timeout"):
                wire.Lines(read).next(time.monotonic() + 0.01)
        finally:
            os.close(read)
            os.close(write)

    def test_coalesced_frames_and_invalid_json(self):
        read, write = os.pipe()
        try:
            os.write(write, b'{"one":1}\n{"two":2}\nnot json\n')
            lines = wire.Lines(read)
            self.assertEqual(lines.next(time.monotonic() + 1), {"one": 1})
            self.assertEqual(lines.next(time.monotonic() + 1), {"two": 2})
            with self.assertRaisesRegex(wire.Refusal, "stream-json"):
                lines.next(time.monotonic() + 1)
        finally:
            os.close(read)
            os.close(write)

    def test_oversized_frame_refuses_before_json(self):
        lines = wire.Lines(123)
        lines.buffer = b"x" * (wire.MAX_LINE + 1) + b"\n"
        with self.assertRaisesRegex(wire.Refusal, "stream-line-bound"):
            lines.next(time.monotonic() + 1)

    def test_total_stream_bound(self):
        read, write = os.pipe()
        try:
            os.write(write, b"{}\n")
            lines = wire.Lines(read)
            lines.count = wire.MAX_STREAM
            with self.assertRaisesRegex(wire.Refusal, "stream-total-bound"):
                lines.next(time.monotonic() + 1)
        finally:
            os.close(read)
            os.close(write)

    def good_result(self):
        return dict(type="result", subtype="success", is_error=False, session_id=SESSION,
                    num_turns=2, total_cost_usd=0.01, result="PRIVATE-OUTPUT-CANARY")

    def test_result_checks_and_projection(self):
        good = self.good_result()
        self.assertNotIn("PRIVATE", json.dumps(wire.result_projection(good, SESSION)))
        for field, value in (("is_error", True), ("is_error", None), ("subtype", "error_max_turns"),
                             ("session_id", str(uuid.uuid4())), ("num_turns", 9), ("num_turns", True),
                             ("total_cost_usd", float("nan")), ("total_cost_usd", 1.1)):
            with self.subTest(field=field, value=value), self.assertRaises(wire.Refusal):
                wire.result_projection(dict(good, **{field: value}), SESSION)

    def supervisor(self, frames):
        supervisor = wire.Supervisor()
        supervisor.session = SESSION
        supervisor.limit = 2
        supervisor.deadline = time.monotonic() + 30
        supervisor.send = mock.Mock()
        supervisor.identity = mock.Mock(return_value=dict(cli_pid=13, cli_start="123", session=SESSION,
                                                          actual_model=wire.ACTUAL_MODEL, cli_version=wire.VERSION))
        supervisor.lines = mock.Mock(buffer=b"")
        supervisor.lines.next.side_effect = frames
        return supervisor

    def test_turn_discards_text_and_requires_actual_init(self):
        frames = [dict(type="assistant", message={"content": "PRIVATE-OUTPUT-CANARY"}),
                  dict(type="system", subtype="init", session_id=SESSION, model=wire.ACTUAL_MODEL), self.good_result()]
        supervisor = self.supervisor(frames)
        result = supervisor.turn(dict(prompt="fixed task"))
        self.assertEqual(result["event"], "complete")
        self.assertNotIn("PRIVATE", json.dumps(result))
        sent = supervisor.send.call_args.args[0]
        self.assertEqual(sent["session_id"], SESSION)
        self.assertEqual(sent["message"], dict(role="user", content="fixed task"))
        with self.assertRaisesRegex(wire.Refusal, "actual-model-unobserved"):
            self.supervisor([self.good_result()]).turn(dict(prompt="fixed task"))

    def test_model_session_and_unexpected_control_refuse(self):
        for frame in (dict(type="system", subtype="init", session_id=SESSION, model="other"),
                      dict(type="system", subtype="init", session_id=str(uuid.uuid4()), model=wire.ACTUAL_MODEL),
                      dict(type="control_request", request={"secret": "CANARY"})):
            with self.subTest(frame=frame), self.assertRaises(wire.Refusal):
                self.supervisor([frame]).turn(dict(prompt="fixed task"))

    def test_no_fifth_turn_or_implicit_resume(self):
        supervisor = self.supervisor([])
        supervisor.turns = 2
        with self.assertRaisesRegex(wire.Refusal, "user-turn-limit"):
            supervisor.turn(dict(prompt="extra"))
        for resume in (False, True):
            arguments = wire.argv(SESSION, resume)
            self.assertEqual(arguments[-2:], ["--resume" if resume else "--session-id", SESSION])
            self.assertNotIn("--continue", arguments)
            self.assertIn("--max-turns", arguments)
            self.assertIn("--max-budget-usd", arguments)


class CustodyTests(unittest.TestCase):
    def test_export_is_closed_and_excludes_session_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "retained"
            root.mkdir()
            export = Path(directory) / "export"
            export.mkdir()
            (root / "result.json").write_text('{"outcome":"inconclusive"}')
            (root / "private-resources.json").write_text('{"not-exportable":"PRIVATE"}')
            (root / "session-private").mkdir()
            (root / "session-private/transcript").write_text("PRIVATE")
            with mock.patch.object(controller.tempfile, "mkdtemp", return_value=str(export)), \
                    mock.patch.object(controller, "USER", os.getuid()):
                self.assertEqual(controller.export_evidence(root), export)
            self.assertEqual({p.name for p in export.iterdir()}, {"result.json", "PROVENANCE.json"})
            self.assertNotIn("PRIVATE", "".join(p.read_text() for p in export.iterdir()))
            proof = json.loads((export / "PROVENANCE.json").read_text())
            self.assertEqual(proof["files"]["result.json"], hashlib.sha256((root / "result.json").read_bytes()).hexdigest())

    def test_unexpected_tool_or_changed_parent_namespace_refuses(self):
        good = [dict(pid=10, parent=1, namespace=[1, 2]), dict(pid=11, parent=10, namespace=[1, 2])]
        controller.check_tree(good, 10, 11, [1, 2])
        for facts in (good + [dict(pid=12, parent=11, namespace=[1, 2])],
                      [good[0], dict(good[1], parent=1)], [good[0], dict(good[1], namespace=[1, 3])]):
            with self.subTest(facts=facts), self.assertRaises(wire.Refusal):
                controller.check_tree(facts, 10, 11, [1, 2])

    def test_reader_is_never_called_before_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = controller.Fixture.__new__(controller.Fixture)
            fixture.gate = base.Gate(Path(directory) / "gate.json", {"identity": "pinned"})
            fixture.workspace = Path(directory)
            fixture.workspace_pin = base.pin(directory)
            with mock.patch.object(controller, "read_artifacts") as read:
                with self.assertRaises(RuntimeError):
                    fixture.consume(None, "a" * 32, False)
                read.assert_not_called()
            fixture.gate.intent()
            reload = base.Gate(fixture.gate.path)
            with self.assertRaises(RuntimeError):
                reload.admit()
            receipt = reload.stopped(dict(container_stopped=True))
            reload.consume(receipt)
            with self.assertRaises(RuntimeError):
                reload.consume(receipt)

    def test_file_boundary_rejects_link_extra_fifo_and_large_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "solution.py"
            path.write_bytes(contract.INITIAL)
            self.assertEqual(controller.read_artifacts(root, base.pin(root)), {"solution.py": contract.INITIAL})
            outside = root / "extra"
            outside.write_text("private")
            with self.assertRaisesRegex(wire.Refusal, "artifact-path-set"):
                controller.read_artifacts(root, base.pin(root))
            outside.unlink()
            path.unlink()
            path.symlink_to("/nonexistent")
            with self.assertRaises(OSError):
                controller.read_artifacts(root, base.pin(root))
            path.unlink()
            os.mkfifo(path)
            with self.assertRaisesRegex(wire.Refusal, "artifact-file-boundary"):
                controller.read_artifacts(root, base.pin(root))
            path.unlink()
            path.write_bytes(b"x" * 4097)
            with self.assertRaisesRegex(wire.Refusal, "artifact-file-boundary"):
                controller.read_artifacts(root, base.pin(root))

    def test_shutdown_stops_even_when_cli_has_failed(self):
        fixture = controller.Fixture.__new__(controller.Fixture)
        fixture.container = "a" * 64
        fixture.pidfd = None
        fixture.nonce = "attempt"
        fixture.gate = None
        fixture.credentials = mock.Mock()
        fixture.event = mock.Mock()
        fixture.inspect = mock.Mock(side_effect=[{"State": {"Running": True}}, {"State": {"Running": False, "Pid": 0}}])
        fixture.quiescent = mock.Mock(side_effect=AssertionError("dead CLI must not gate shutdown"))
        with mock.patch.object(controller, "docker") as docker:
            fixture.shutdown()
            docker.assert_called_once_with("stop", "--time", "3", "a" * 64)
        fixture.credentials.release.assert_called_once_with("attempt", True)
        fixture.quiescent.assert_not_called()

    def test_unconfirmed_shutdown_keeps_credentials(self):
        fixture = controller.Fixture.__new__(controller.Fixture)
        fixture.container = "a" * 64
        fixture.pidfd = None
        fixture.credentials = mock.Mock()
        fixture.inspect = mock.Mock(return_value={"State": {"Running": True, "Pid": 10}})
        with mock.patch.object(controller, "docker"), self.assertRaisesRegex(wire.Refusal, "shutdown-unconfirmed"):
            fixture.shutdown()
        fixture.credentials.release.assert_not_called()


class CredentialTests(unittest.TestCase):
    def test_runtime_snapshot_rechecks_source_before_import_or_source_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            source = repo / "v12/python/tools/user_credentials.py"
            source.parent.mkdir(parents=True)
            source.write_text("ORIGINAL")
            manifest = dict(files={"v12/python/tools/user_credentials.py": hashlib.sha256(b"ORIGINAL").hexdigest()})
            retained = root / "retained"
            retained.mkdir()
            with mock.patch.object(controller, "REPO", repo):
                snapshot = controller.snapshot_runtime(retained, manifest)
                source.write_text("CHANGED")
                self.assertEqual((snapshot / "tools/user_credentials.py").read_text(), "ORIGINAL")
                second = root / "second"
                second.mkdir()
                with self.assertRaisesRegex(wire.Refusal, "runtime-copy-drift"):
                    controller.snapshot_runtime(second, manifest)

    def test_source_effective_identity_is_restored_on_refusal(self):
        fixture = controller.Credentials.__new__(controller.Credentials)
        fixture.reader = mock.Mock(side_effect=ValueError("private canary"))
        with mock.patch.object(os, "geteuid", return_value=0), mock.patch.object(os, "seteuid") as change:
            with self.assertRaises(ValueError):
                fixture.provider("claude", "w106673-owner-source")
            self.assertEqual(change.call_args_list, [mock.call(1000), mock.call(0)])

    def test_existing_reader_materializer_and_teardown_with_artificial_source(self):
        # Exercise the real APIs with this ordinary test user's own file/group.
        import sys
        sys.path.insert(0, str(controller.REPO / "v12/python/src"))
        from baton_v12.worker_manager import credentials, workspaces
        from baton_v12.worker_manager.store import ControlStore
        spec = importlib.util.spec_from_file_location("test_fixture_sources", controller.REPO / "v12/python/tools/user_credentials.py")
        sources = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sources)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "artificial-source"
            source.write_text("W106673-OFFLINE-ARTIFICIAL-CANARY")
            source.chmod(0o600)
            registry = root / "sources.json"
            registry.write_text(json.dumps(dict(schema=sources.SCHEMA, sources=[dict(provider="claude", reference="w106673-owner-source", path=str(source))])))
            registry.chmod(0o600)
            store = ControlStore.open(str(root / "fixture.sqlite3"), incarnation="offline-fixture", clock=controller.fixture_now)
            try:
                workspaces.configure_workspace_group(store, os.getgid())
                fixture = controller.Credentials.__new__(controller.Credentials)
                fixture.reader = sources.UserCredentialSources(str(registry), max_bearer=credentials.MAX_BEARER)
                fixture.home = credentials.CredentialHome(str(root / "manager"))
                fixture.group = workspaces.configured_workspace_group(store)
                fixture.deliveries = {}
                with mock.patch.object(controller, "USER", os.geteuid()):
                    delivery = fixture.materialize("offline-attempt")
                slot = Path(delivery.mounts()[0][0])
                self.assertEqual(slot.read_text(), "W106673-OFFLINE-ARTIFICIAL-CANARY")
                self.assertEqual(slot.stat().st_mode & 0o777, 0o640)
                self.assertEqual(delivery.mounts()[0][1], "/run/baton/credentials/claude")
                with self.assertRaisesRegex(wire.Refusal, "credential-release-before-shutdown"):
                    fixture.release("offline-attempt", False)
                self.assertTrue(slot.exists())
                fixture.release("offline-attempt", True)
                self.assertFalse(slot.exists())
                self.assertEqual(source.read_text(), "W106673-OFFLINE-ARTIFICIAL-CANARY")
                self.assertFalse(fixture.deliveries)
            finally:
                store.close()


class PairTests(unittest.TestCase):
    def test_lost_create_reply_preserves_delivery_and_exports_failure(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credential = mock.Mock(deliveries={"attempt": object()})
            fixture = mock.Mock(container=None, pidfd=None, gate=None, stopped=False,
                                delivery=object(), create_started=True, nonce="attempt")
            def failed_pair(root, network, credentials, deadline, fixtures):
                fixtures.append(fixture)
                raise wire.Refusal("docker-refused")
            image = dict(Id=controller.IMAGE, Config={"Volumes": {}})
            network = dict(Name="bridge", Driver="bridge", Scope="local", Internal=False,
                           Id="b" * 64, Options={"com.docker.network.bridge.default_bridge": "true"})
            with mock.patch.object(controller, "audit", return_value={"limitations": []}), \
                    mock.patch.object(controller, "digest", return_value="manifest"), \
                    mock.patch.object(controller, "docker", side_effect=[json.dumps([image]), json.dumps([network])]), \
                    mock.patch.object(controller, "snapshot_runtime", return_value=root), \
                    mock.patch.object(controller, "Credentials", return_value=credential), \
                    mock.patch.object(controller, "execute_pair", side_effect=failed_pair), \
                    mock.patch.object(controller, "export_evidence", return_value=root / "export"), \
                    mock.patch.object(controller.tempfile, "mkdtemp", return_value=str(root)), \
                    mock.patch.object(controller.os, "geteuid", return_value=0), \
                    mock.patch.object(controller.os, "setgroups"), mock.patch.object(controller.os, "umask"), \
                    mock.patch.object(controller.signal, "signal"), mock.patch.object(controller.signal, "setitimer"), \
                    mock.patch.object(controller.base, "libc_calls"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(controller.run(), 1)
            credential.release.assert_not_called()
            fixture.shutdown.assert_not_called()
            result = json.loads((root / "result.json").read_text())
            self.assertFalse(result["cleanup_confirmed"])
            self.assertEqual(result["cleanup"], [dict(nonce="attempt", confirmed=False)])
            self.assertEqual(result["outcome"], "failed-or-inconclusive")

    def test_exact_four_turn_pair_restores_old_session_after_stop_and_review(self):
        instances = []
        class FakeFixture:
            def __init__(self, root, name, network, credentials, deadline, workspace=None, session_home=None, session=None, resume=False):
                self.name, self.resume = name, resume
                self.workspace = workspace or root / name
                if workspace is None:
                    self.workspace.mkdir()
                self.workspace_pin = base.pin(self.workspace)
                self.session_home = session_home or self.workspace / "uncreated-session"
                self.session = session or str(uuid.uuid4())
                self.stopped = False
                self.gate = base.Gate(root / (name + "-gate.json"), {"name": name})
                self.cli_fd = 99
                self.turns = []
                instances.append(self)
                if resume:
                    self_first = instances[-2]
                    assert self_first.stopped and self_first.gate.value["phase"] == "reviewed"
                    assert session == self_first.session and workspace == self_first.workspace
            def start(self): pass
            def event(self, *args, **kwargs): pass
            def process_identity(self): return [self.name, "actual-process"]
            def turn(self, prompt):
                self.turns.append(prompt)
                require_phase = self.gate.value["phase"]
                assert require_phase == "attached"
                now = time.monotonic_ns()
                return now, now, dict(session=self.session, actual_model=wire.ACTUAL_MODEL)
            def detach(self):
                self.gate.intent()
                return self.gate.revoked({"mount_absent": True})
            def shutdown(self):
                self.stopped = True
                return self.gate.stopped({"container_stopped": True})
            def consume(self, receipt, token, corrected):
                self.gate.consume(receipt)
                assert len(token) == 32
                return True
            def attach(self): self.gate.admit()
            def quiescent(self): pass
            def finish(self): pass
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(controller, "Fixture", FakeFixture), \
                mock.patch.object(controller.time, "sleep"), mock.patch.object(controller.select, "select", return_value=([], [], [])):
            result = controller.execute_pair(Path(directory), "network", object(), time.monotonic() + 900, [])
        self.assertEqual(result["outcome"], "live-pair-passed")
        self.assertEqual([len(f.turns) for f in instances], [2, 1, 1])
        self.assertEqual(instances[0].turns[0], instances[1].turns[0])
        self.assertEqual(instances[0].turns[1], contract.CORRECTION)
        self.assertEqual(instances[2].turns[0], contract.CORRECTION)
        self.assertTrue(all(f.stopped for f in instances))


if __name__ == "__main__":
    unittest.main(verbosity=2)
