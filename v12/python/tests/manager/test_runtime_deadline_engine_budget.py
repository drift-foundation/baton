"""Deterministic supervisor/fixture coverage; never calls Docker or a real child."""
import json
import hashlib
import io
import signal
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from .test_runtime_deadline_engine import DeadlineDocker, gate


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class Docker:
    def __init__(self, clock):
        self.clock = clock
        self.live = {"foreign": {"Id": "f" * 64, "Name": "/foreign", "Config": {"Labels": {}}}}
        self.commands = []
        self.cost = 0.25
        self.fail_remove = False
        self.creation_fault = False
        self.before_create = None

    def __call__(self, command, *, capture_output, timeout):
        self.commands.append((command, timeout, self.clock()))
        if self.cost > timeout:
            self.clock.now += timeout
            raise subprocess.TimeoutExpired(command, timeout)
        self.clock.now += self.cost
        status, out, err = 0, b"", b""
        if command[1] in ("create", "run"):
            name = command[command.index("--name") + 1]
            if self.before_create:
                self.before_create(name)
            label = command[command.index("--label") + 1].split("=", 1)
            self.live[name] = {"Id": str(len(self.live)) * 64, "Name": "/" + name,
                               "Config": {"Labels": dict([label])}}
            if self.creation_fault:
                raise subprocess.TimeoutExpired(command, timeout)
        elif command[1:3] == ["container", "inspect"]:
            name = command[-1]
            if name in self.live:
                out = json.dumps([self.live[name]]).encode()
            else:
                status, out, err = 1, b"[]\n", ("Error response from daemon: No such container: " + name + "\n").encode()
        elif command[1:3] == ["rm", "--force"]:
            if self.fail_remove:
                status, err = 1, b"daemon refused removal"
            else:
                for name, row in list(self.live.items()):
                    if row["Id"] == command[-1]:
                        del self.live[name]
        else:
            raise AssertionError("unselected fake Docker command: " + repr(command))
        return subprocess.CompletedProcess(command, status, out, err)


class Process:
    def __init__(self, clock, *, duration=3, code=0, resist_term=False, resist_kill=False):
        self.clock, self.duration, self.code = clock, duration, code
        self.resist_term, self.resist_kill = resist_term, resist_kill
        self.actions = []
        self.stopped = False

    def wait(self, timeout):
        if self.stopped:
            self.clock.now += 0.1
            return -9
        if self.duration > timeout:
            self.clock.now += timeout
            raise subprocess.TimeoutExpired("owned-child", timeout)
        self.clock.now += self.duration
        return self.code

    def terminate(self):
        self.actions.append("terminate")
        self.stopped = not self.resist_term

    def kill(self):
        self.actions.append("kill")
        self.stopped = not self.resist_kill

    def group_alive(self):
        return not self.stopped

    def release(self, timeout):
        if self.group_alive():
            raise RuntimeError("fake group still live")
        return self.wait(timeout)


class EngineBudget(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"
        self.clock = Clock()
        for patcher in (mock.patch.object(gate.time, "sleep", side_effect=self.advance_clock),
                        mock.patch.object(gate.time, "monotonic", side_effect=self.clock)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.docker = Docker(self.clock)
        self.process = Process(self.clock)
        self.names = ["runtime-one", "custodian-one", "sibling-one"]

    def advance_clock(self, seconds):
        self.clock.now += seconds

    def factory(self, command, **kwargs):
        root = Path(kwargs["env"]["BATON_W32577_GATE_DIR"])
        self.assertEqual(kwargs["env"]["TMPDIR"], str(root / "fixtures"))
        control = gate.ChildControl(root, clock=self.clock, runner=self.docker)
        self.inventory = control.inventory
        self.docker.before_create = lambda name: self.assertIn(name, self.inventory.names())
        for name in self.names:
            control.docker(["create", "--name", name, "selected-image"])
        return self.process

    def run_gate(self, factory=None):
        return gate.supervise(self.root, ["selected-python", "selected-case"], clock=self.clock,
                              runner=self.docker, process_factory=factory or self.factory, env={})

    def test_normal_body_cleans_exact_runtime_custodian_and_sibling_and_retains_inventory(self):
        result = self.run_gate()
        self.assertTrue(result["ok"])
        self.assertEqual(set(result["cleanup"]["resolved"]), set(self.names))
        self.assertEqual(set(self.inventory.names()), set(self.names))
        self.assertEqual(set(self.docker.live), {"foreign"})
        self.assertEqual(self.process.actions, ["terminate", "kill"])
        self.assertEqual(result["elapsed"], self.clock() - 1000)
        self.assertEqual(sum(row["elapsed"] for row in result["phases"].values()), result["elapsed"])
        receipt = json.loads((self.root / "result.json").read_text())
        self.assertFalse(receipt["ok"])
        self.assertTrue(receipt["candidate_ok"])
        self.assertEqual(receipt["status"], "incomplete-awaiting-supervisor-exit")
        self.assertEqual(gate.completion_exit(result, clock=self.clock, output=io.StringIO()), 0)
        for command, timeout, started in self.docker.commands:
            self.assertLessEqual(timeout, 30)
            self.assertLess(started + timeout, 1180)
            self.assertNotIn("foreign", command)

    def test_supported_absence_variants_before_and_after_immutable_id_removal(self):
        inventory = SimpleNamespace(run_id="selected-run", names=lambda: ["selected-name"])
        owned = json.dumps([{"Id": "a" * 64, "Name": "/selected-name",
                             "Config": {"Labels": {gate.LABEL: inventory.run_id}}}]).encode()
        for prefix in (b"Error response from daemon: No such container: ", b"Error: No such container: "):
            for stdout in (b"", b"\n", b"[]", b"[]\n"):
                for present in (False, True):
                    with self.subTest(prefix=prefix, stdout=stdout, present=present):
                        absent = subprocess.CompletedProcess([], 1, stdout, prefix + b"selected-name\n")
                        responses = ([subprocess.CompletedProcess([], 0, owned, b""),
                                      subprocess.CompletedProcess([], 0, b"a" * 64 + b"\n", b"")]
                                     if present else []) + [absent]
                        calls = SimpleNamespace(run=mock.Mock(side_effect=responses))
                        result = gate.cleanup(inventory, calls, 1050)
                        self.assertEqual(result, {"resolved": ["selected-name"], "unresolved": [], "errors": []})
                        commands = [["docker", "container", "inspect", "selected-name"]]
                        if present:
                            commands += [["docker", "rm", "--force", "a" * 64], commands[0]]
                        self.assertEqual(calls.run.call_args_list, [mock.call(command, 1050) for command in commands])

    def test_absence_refuses_wrong_status_name_diagnostic_and_stdout(self):
        inventory = SimpleNamespace(run_id="selected-run", names=lambda: ["selected-name"])
        stderr = b"Error response from daemon: No such container: selected-name\n"
        cases = [(status, b"[]\n", stderr) for status in (0, 2, -9, True, 1.0)]
        cases += [(1, stdout, stderr) for stdout in (b"[", b"[{}]", b"null", b"{}", b"[]\nextra", b"\xff")]
        cases += [(1, b"[]\n", diagnostic) for diagnostic in (
            stderr.replace(b"selected-name", b"selected-name-extra"),
            stderr.replace(b"selected-name", b"different-name"),
            b"permission denied while trying to connect to the Docker daemon socket",
            b"Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?",
            b"Error response from daemon: unknown diagnostic: selected-name\n",
            stderr + b"additional error\n", b"warning\n" + stderr, stderr + b"\xff",
            b"Error: No such container: different-name\n", b"")]
        for status, stdout, diagnostic in cases:
            with self.subTest(status=status, stdout=stdout, diagnostic=diagnostic):
                calls = SimpleNamespace(run=mock.Mock(return_value=subprocess.CompletedProcess([], status, stdout, diagnostic)))
                result = gate.cleanup(inventory, calls, 1050)
                self.assertEqual(result["resolved"], [])
                self.assertEqual(result["unresolved"], ["selected-name"])
                self.assertEqual(len(result["errors"]), 1)
                calls.run.assert_called_once_with(["docker", "container", "inspect", "selected-name"], 1050)

    def test_retained_owner_responses_replay_exact_cleanup_without_docker(self):
        source = Path(gate.__file__).parent / "owner-execution-164414" / "run"
        digests = (
            "43463c6164b60e9d4b50ddd01bc3e9ecc4c94fca2a4c1133a707de64a00e8d78",
            "0d9b74feb2c8b79af82ff162889aa1976ece3b2708b5fad523b9667dc84e7464",
            "6d4eb8bf965b30636f230007a94dcc9478f613229900c8d0f02b6c547152c81d",
            "ad4ea8d76420dddf9373014fdc25ed4c6358533c61d5a7f3e81062afa9437653",
            "990f547a1bb032df2e4dd7a2711489630b086b429bbdf9ca19b45a1cd1fe4718",
            "3c6060438c411dec564b50234e3b6e6e5c60da2bd9baae49b3b520cdaeb5e087",
        )
        records = []
        for index, digest in enumerate(digests, 1):
            raw = (source / f"parent-call-{index}.json").read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            records.append(json.loads(raw))
        names = {row["command"][-1] for row in records if row["command"][1:3] == ["container", "inspect"]}
        self.assertEqual(len(names), 4)
        self.root.mkdir()
        (self.root / "names").mkdir()
        inventory = gate.Inventory(self.root / "names", "6eb2ab1bec5a4b92bb2d69fbe5db1a71")
        for name in names:
            inventory.register(name)
        remaining = iter(records)
        def replay(command, *, capture_output, timeout):
            row = next(remaining)
            self.assertEqual(command, row["command"])
            self.assertTrue(capture_output)
            self.assertGreater(timeout, 0)
            return subprocess.CompletedProcess(command, row["returncode"], row["stdout"].encode(), row["stderr"].encode())
        calls = gate.Calls(self.root, gate.Budget(clock=self.clock), runner=replay)
        result = gate.cleanup(inventory, calls, 1050)
        self.assertEqual(set(result["resolved"]), names)
        self.assertEqual(result["unresolved"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(calls.sequence, 6)
        self.assertEqual(list(remaining), [])
        self.assertEqual(self.docker.commands, [])

    def test_body_timeout_stops_owned_child_then_uses_reserved_cleanup(self):
        self.process.duration = 500
        result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertIn("TimeoutExpired", result["body_error"])
        self.assertEqual(self.process.actions, ["terminate", "kill"])
        self.assertEqual(set(result["cleanup"]["resolved"]), set(self.names))
        self.assertEqual(set(self.docker.live), {"foreign"})
        self.assertLess(result["elapsed"], 180)

    def test_term_resistance_uses_kill_and_reap_within_five_seconds(self):
        self.process.duration = 500
        self.process.resist_term = True
        result = self.run_gate()
        self.assertEqual(self.process.actions, ["terminate", "kill"])
        self.assertEqual(result["reap_errors"], [])
        self.assertLess(result["elapsed"], 180)
        self.assertEqual(result["cleanup"]["unresolved"], [])

    def test_unreaped_child_never_races_cleanup_and_inventory_survives(self):
        self.process.duration = 500
        self.process.resist_term = self.process.resist_kill = True
        result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertTrue(result["reap_errors"])
        self.assertEqual(set(result["cleanup"]["unresolved"]), set(self.names))
        self.assertFalse(any(command[1] == "rm" for command, _, _ in self.docker.commands))

    def test_uncertain_creation_remains_registered_and_can_be_cleaned(self):
        def factory(command, **kwargs):
            control = gate.ChildControl(kwargs["env"]["BATON_W32577_GATE_DIR"], clock=self.clock, runner=self.docker)
            self.inventory = control.inventory
            self.docker.before_create = lambda name: self.assertIn(name, self.inventory.names())
            self.docker.creation_fault = True
            with self.assertRaises(subprocess.TimeoutExpired):
                control.docker(["run", "--name", "uncertain-runtime", "image"])
            self.process.code = 1
            return self.process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(result["body_returncode"], 1)
        self.assertEqual(result["cleanup"]["resolved"], ["uncertain-runtime"])
        self.assertEqual(set(self.docker.live), {"foreign"})

    def test_body_failure_and_cleanup_failure_are_both_retained(self):
        self.process.code = 7
        self.docker.fail_remove = True
        result = self.run_gate()
        self.assertEqual(result["body_returncode"], 7)
        self.assertFalse(result["ok"])
        self.assertEqual(set(result["cleanup"]["unresolved"]), set(self.names))
        self.assertEqual(len(result["cleanup"]["errors"]), 3)
        self.assertEqual(set(self.inventory.names()), set(self.names))

    def test_lost_create_reply_and_current_absence_retain_unresolved_name(self):
        def factory(command, **kwargs):
            def lost(command, **operands):
                raise subprocess.TimeoutExpired(command, operands["timeout"])
            control = gate.ChildControl(kwargs["env"]["BATON_W32577_GATE_DIR"], clock=self.clock, runner=lost)
            with self.assertRaises(subprocess.TimeoutExpired):
                control.docker(["create", "--name", "maybe-still-creating", "image"])
            self.process.code = 1
            return self.process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(result["cleanup"]["unresolved"], ["maybe-still-creating"])
        self.assertIn("creation outcome unresolved", result["cleanup"]["errors"][0])

    def test_pending_create_guard_survives_killed_child_without_final_record(self):
        def factory(command, **kwargs):
            control = gate.ChildControl(kwargs["env"]["BATON_W32577_GATE_DIR"], clock=self.clock, runner=self.docker)
            control.inventory.register("pending-create")
            gate.durable(self.root / "child-call-1.json", {
                "command": ["docker", "create", "--name", "pending-create", "image"], "state": "running"})
            self.process.duration = 500
            return self.process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(result["cleanup"]["unresolved"], ["pending-create"])

    def test_cleanup_children_share_one_fifty_second_reserve(self):
        def factory(command, **kwargs):
            process = self.factory(command, **kwargs)
            self.docker.cost = 29
            return process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        cleanup_calls = self.docker.commands[3:]
        self.assertLessEqual(len(cleanup_calls), 2)
        self.assertLessEqual(result["phases"]["cleanup"]["elapsed"], 50)
        self.assertTrue(result["cleanup"]["unresolved"])
        self.assertLess(cleanup_calls[-1][1], 30)

    def test_foreign_same_name_is_never_removed_even_when_inventory_registered_it(self):
        def factory(command, **kwargs):
            process = self.factory(command, **kwargs)
            self.docker.live["runtime-one"]["Config"]["Labels"] = {gate.LABEL: "another-run"}
            return process
        result = self.run_gate(factory)
        self.assertEqual(result["cleanup"]["unresolved"], ["runtime-one"])
        self.assertIn("runtime-one", self.docker.live)
        foreign_id = self.docker.live["runtime-one"]["Id"]
        self.assertFalse(any(command[1] == "rm" and command[-1] == foreign_id
                             for command, _, _ in self.docker.commands))

    def test_same_name_replacement_after_inspection_survives_immutable_id_removal(self):
        original = self.docker.__call__
        def runner(command, **kwargs):
            if command[1] == "rm" and "runtime-one" in self.docker.live:
                previous = self.docker.live["runtime-one"]
                if command[-1] == previous["Id"]:
                    self.docker.live["runtime-one"] = {"Id": "e" * 64, "Name": "/runtime-one", "Config": {"Labels": {}}}
            return original(command, **kwargs)
        result = gate.supervise(self.root, ["selected"], clock=self.clock, runner=runner,
                                process_factory=self.factory, env={})
        self.assertFalse(result["ok"])
        self.assertIn("runtime-one", result["cleanup"]["unresolved"])
        self.assertEqual(self.docker.live["runtime-one"]["Id"], "e" * 64)

    def test_absence_requires_exact_daemon_answer_not_connection_failure(self):
        def denied(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, b"[]", b"permission denied")
        result = gate.supervise(self.root, ["selected"], clock=self.clock, runner=denied,
                                process_factory=self.factory, env={})
        self.assertFalse(result["ok"])
        self.assertEqual(set(result["cleanup"]["unresolved"]), set(self.names))

    def test_body_budget_refuses_before_launch_and_total_caps_later_phases(self):
        budget = gate.Budget(clock=self.clock)
        self.clock.now = 1118
        with self.assertRaises(TimeoutError):
            budget.allowance(budget.body_end)
        self.clock.now = 1174
        self.assertEqual(budget.phase_end("cleanup"), 1175)
        with self.assertRaises(TimeoutError):
            budget.allowance(budget.phase_end("cleanup"))
        self.assertEqual(budget.phase_end("account"), 1179)
        self.clock.now = 1179
        self.assertEqual(budget.phase_end("account"), 1180)

    def test_durable_registration_failure_prevents_creation(self):
        self.root.mkdir()
        (self.root / "names").mkdir()
        gate.durable(self.root / "config.json", {"run_id": "run", "start": self.clock()})
        control = gate.ChildControl(self.root, clock=self.clock, runner=self.docker)
        with mock.patch.object(gate, "durable", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                control.docker(["run", "--name", "runtime", "image"])
        self.assertEqual(self.docker.commands, [])

    def test_missing_name_or_corrupt_inventory_refuses_without_foreign_removal(self):
        def factory(command, **kwargs):
            control = gate.ChildControl(kwargs["env"]["BATON_W32577_GATE_DIR"], clock=self.clock, runner=self.docker)
            with self.assertRaises(ValueError):
                control.docker(["run", "image"])
            (control.inventory.root / "broken.json").write_text("{")
            return self.process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["cleanup"]["unresolved"])
        self.assertEqual(self.docker.commands, [])

    def test_new_run_directory_cannot_adopt_old_inventory(self):
        self.root.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_gate()
        self.assertEqual(self.docker.commands, [])

    def test_slow_guard_persistence_cannot_launch_a_child_on_stale_allowance(self):
        original = gate.durable
        def durable(path, value, **kwargs):
            original(path, value, **kwargs)
            if Path(path).name == "body-guard.json":
                self.clock.now += 119
        with mock.patch.object(gate, "durable", side_effect=durable):
            result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertIn("TimeoutError", result["body_error"])
        self.assertEqual(self.docker.commands, [])

    def test_expired_cleanup_reserve_launches_no_docker_child(self):
        def factory(command, **kwargs):
            process = self.factory(command, **kwargs)
            process.duration = 174
            # Model a broken/late child wait returning after its allowed deadline.
            def wait(timeout):
                self.clock.now = 1175
                return 0
            process.wait = wait
            return process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(len(self.docker.commands), 3)
        self.assertEqual(set(result["cleanup"]["unresolved"]), set(self.names))

    def test_final_accounting_overrun_is_not_success(self):
        original = gate.durable
        def durable(path, value, **kwargs):
            original(path, value, **kwargs)
            if Path(path).name == "result.json" and kwargs.get("exclusive"):
                self.clock.now += 6
        with mock.patch.object(gate, "durable", side_effect=durable):
            result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertIn("accounting_error", result)

    def test_owned_wrapper_keeps_leader_identity_until_descendant_killed(self):
        leader = SimpleNamespace(pid=12345, args=["fake"], exited=False, descendant=True, released=False)
        signals = []
        def status(*args):
            self.assertFalse(leader.released)
            self.assertTrue(args[2] & gate.os.WNOWAIT)
            return SimpleNamespace(si_status=0, si_code=gate.os.CLD_EXITED) if leader.exited else None
        def killpg(pid, number):
            self.assertEqual(pid, leader.pid)
            self.assertFalse(leader.released)
            signals.append(number)
            leader.exited = True
            if number == signal.SIGKILL:
                leader.descendant = False
        def release(timeout):
            self.assertFalse(leader.descendant)
            leader.released = True
            return -9
        leader.wait = release
        with mock.patch.object(gate.subprocess, "Popen", return_value=leader), \
                mock.patch.object(gate.os, "waitid", side_effect=status), \
                mock.patch.object(gate.os, "killpg", side_effect=killpg), \
                mock.patch.object(gate.OwnedProcess, "group_alive", side_effect=lambda: leader.descendant):
            self.process = gate.OwnedProcess(["fake"])
            result = self.run_gate()
            with self.assertRaises(RuntimeError):
                self.process.kill()
        self.assertEqual(signals, [signal.SIGTERM, signal.SIGKILL])
        self.assertTrue(leader.released)
        self.assertFalse(leader.descendant)
        self.assertEqual(set(result["cleanup"]["resolved"]), set(self.names))

    def test_normal_leader_exit_still_settles_its_owned_group(self):
        self.process.group_alive = mock.Mock(return_value=False)
        # The normal body return must still enter the stop/group-settlement path.
        result = self.run_gate()
        self.assertTrue(result["ok"])
        self.assertEqual(self.process.actions, ["terminate", "kill"])

    def test_no_time_after_term_retains_names_without_racing_descendant(self):
        self.process.duration = 500
        def terminate():
            self.process.actions.append("terminate")
            self.clock.now = 1124.9
        self.process.terminate = terminate
        result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertEqual(self.process.actions, ["terminate"])
        self.assertEqual(set(result["cleanup"]["unresolved"]), set(self.names))
        self.assertFalse(any(command[1] == "rm" for command, _, _ in self.docker.commands))

    def test_lost_leader_wait_ownership_never_signals_recycled_group(self):
        leader = SimpleNamespace(pid=12345, args=["fake"])
        with mock.patch.object(gate.subprocess, "Popen", return_value=leader), \
                mock.patch.object(gate.os, "waitid", side_effect=ChildProcessError("already reaped elsewhere")), \
                mock.patch.object(gate.os, "killpg") as signals:
            self.process = gate.OwnedProcess(["fake"])
            result = self.run_gate()
        signals.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(set(result["cleanup"]["unresolved"]), set(self.names))

    def test_owned_group_scan_distinguishes_live_members_zombies_and_foreign_groups(self):
        proc = Path(self.temp.name) / "proc-fixture"
        proc.mkdir()
        for pid, state, group in ((12345, "Z", 12345), (12346, "S", 12345), (54321, "S", 54321)):
            (proc / str(pid)).mkdir()
            (proc / str(pid) / "stat").write_text(f"{pid} (fake process) {state} 1 {group} {group} 0\n")
        leader = SimpleNamespace(pid=12345, args=["fake"])
        with mock.patch.object(gate.subprocess, "Popen", return_value=leader), \
                mock.patch.object(gate.os, "waitid", return_value=SimpleNamespace(si_status=0, si_code=gate.os.CLD_EXITED)), \
                mock.patch.object(gate, "Path", side_effect=lambda value: proc if value == "/proc" else Path(value)):
            process = gate.OwnedProcess(["fake"])
            self.assertTrue(process.group_alive())
            (proc / "12346" / "stat").write_text("12346 (fake process) Z 1 12345 12345 0\n")
            self.assertFalse(process.group_alive())

    def test_owned_group_scan_refuses_a_session_mismatch(self):
        proc = Path(self.temp.name) / "proc-fixture"
        (proc / "12345").mkdir(parents=True)
        (proc / "12345" / "stat").write_text("12345 (fake) S 1 12345 999 0\n")
        leader = SimpleNamespace(pid=12345, args=["fake"])
        with mock.patch.object(gate.subprocess, "Popen", return_value=leader), \
                mock.patch.object(gate.os, "waitid", return_value=None), \
                mock.patch.object(gate, "Path", side_effect=lambda value: proc if value == "/proc" else Path(value)):
            process = gate.OwnedProcess(["fake"])
            with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                process.group_alive()

    def test_partial_diagnostics_preserve_error_but_clean_known_owned_resources(self):
        def factory(command, **kwargs):
            process = self.factory(command, **kwargs)
            (self.root / "child-call-1.json").write_text("{")
            process.code = 1
            return process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(set(result["cleanup"]["resolved"]), set(self.names))
        self.assertEqual(result["cleanup"]["unresolved"], [])
        self.assertTrue(any("JSONDecodeError" in error for error in result["cleanup"]["errors"]))
        self.assertEqual(len(list(self.root.glob("child-create-intent-*.json"))), 3)
        self.assertEqual(set(self.docker.live), {"foreign"})

    def test_damaged_diagnostics_cannot_settle_absent_uncertain_creation(self):
        def factory(command, **kwargs):
            process = self.factory(command, **kwargs)
            (self.root / "child-call-1.json").write_text("")
            del self.docker.live["runtime-one"]
            return process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(result["cleanup"]["unresolved"], ["runtime-one"])
        self.assertEqual(set(result["cleanup"]["resolved"]), {"custodian-one", "sibling-one"})

    def test_interrupted_atomic_diagnostic_replacement_preserves_guard_and_intent(self):
        def factory(command, **kwargs):
            control = gate.ChildControl(kwargs["env"]["BATON_W32577_GATE_DIR"], clock=self.clock, runner=self.docker)
            with mock.patch.object(gate.os, "replace", side_effect=OSError("replace interrupted")):
                with self.assertRaises(OSError):
                    control.docker(["create", "--name", "interrupted-replace", "image"])
            self.assertEqual(json.loads((self.root / "child-call-1.json").read_text())["state"], "running")
            self.assertEqual(json.loads((self.root / "child-create-intent-1.json").read_text())["name"], "interrupted-replace")
            self.process.code = 1
            return self.process
        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(result["cleanup"]["resolved"], ["interrupted-replace"])
        self.assertEqual(set(self.docker.live), {"foreign"})

    def test_last_accounting_write_is_in_exit_outcome_and_never_persists_success(self):
        original = gate.durable
        def durable(path, value, **kwargs):
            original(path, value, **kwargs)
            if Path(path).name == "result.json" and not kwargs.get("exclusive"):
                self.clock.now += 181
        with mock.patch.object(gate, "durable", side_effect=durable):
            result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertGreater(result["elapsed"], 180)
        self.assertEqual(result["elapsed"], self.clock() - 1000)
        self.assertFalse(json.loads((self.root / "result.json").read_text())["ok"])
        self.assertEqual(gate.completion_exit(result, clock=self.clock, output=io.StringIO()), 1)

    def test_final_output_flush_is_inside_authoritative_exit_decision(self):
        result = self.run_gate()
        self.assertTrue(result["ok"])
        class Output(io.StringIO):
            def flush(inner):
                self.clock.now += 6
        output = Output()
        self.assertEqual(gate.completion_exit(result, clock=self.clock, output=output), 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])
        self.assertEqual(result["elapsed"], self.clock() - 1000)
        self.assertFalse(result["ok"])

    def test_final_evidence_write_failure_leaves_only_incomplete_receipt(self):
        original = gate.durable
        def durable(path, value, **kwargs):
            if Path(path).name == "result.json" and not kwargs.get("exclusive"):
                raise OSError("final evidence unavailable")
            return original(path, value, **kwargs)
        with mock.patch.object(gate, "durable", side_effect=durable):
            result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertIn("final evidence unavailable", result["accounting_error"])
        self.assertFalse(json.loads((self.root / "result.json").read_text())["ok"])

    def test_fixture_engineport_and_direct_sibling_use_the_same_registration_boundary(self):
        self.root.mkdir()
        (self.root / "names").mkdir()
        gate.durable(self.root / "config.json", {"run_id": "fixture-run", "start": self.clock()})
        control = gate.ChildControl(self.root, clock=self.clock, runner=self.docker)
        fixture = DeadlineDocker("test_reached_fence_exact_removal_providers_custody_and_discharge")
        fixture.made, fixture.engine_calls, fixture.trace = [], [], []
        with mock.patch.object(DeadlineDocker, "control", control, create=True):
            fixture.spawn(["docker", "create", "--name", "runtime", "image"])
            fixture.spawn(["docker", "run", "--name", "custodian", "image"])
            fixture.docker(["run", "--name", "sibling", "image"])
        self.assertEqual(set(control.inventory.names()), {"runtime", "custodian", "sibling"})
        for name in control.inventory.names():
            self.assertEqual(self.docker.live[name]["Config"]["Labels"][gate.LABEL], "fixture-run")

    def test_fixture_retains_local_evidence_without_racing_parent_container_cleanup(self):
        self.root.mkdir()
        fixture = DeadlineDocker("test_reached_fence_exact_removal_providers_custody_and_discharge")
        fixture.control = mock.Mock(root=self.root)
        fixture.store = mock.Mock()
        fixture.home = str(self.root / "fixtures" / "attempt")
        destructive = mock.Mock()
        fixture.addCleanup(destructive)
        self.assertTrue(fixture.doCleanups())
        destructive.assert_not_called()
        fixture.store.close.assert_called_once_with()
        self.assertEqual(json.loads((self.root / "fixture-retained.json").read_text())["home"], fixture.home)


def load_tests(loader, tests, pattern):
    # Importing the real fixture supplies methods only; never select its engine test.
    return loader.loadTestsFromTestCase(EngineBudget)
