"""Deterministic supervisor/fixture coverage; never calls Docker or a real child."""
import json
from pathlib import Path
import subprocess
import tempfile
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
                status, out, err = 1, b"[]\n", ("Error: No such container: " + name + "\n").encode()
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


class EngineBudget(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"
        self.clock = Clock()
        self.docker = Docker(self.clock)
        self.process = Process(self.clock)
        self.names = ["runtime-one", "custodian-one", "sibling-one"]

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
        self.assertEqual(self.process.actions, [])
        self.assertEqual(result["elapsed"], self.clock() - 1000)
        self.assertEqual(sum(row["elapsed"] for row in result["phases"].values()), result["elapsed"])
        self.assertEqual(json.loads((self.root / "result.json").read_text()), result)
        for command, timeout, started in self.docker.commands:
            self.assertLessEqual(timeout, 30)
            self.assertLess(started + timeout, 1180)
            self.assertNotIn("foreign", command)

    def test_body_timeout_stops_owned_child_then_uses_reserved_cleanup(self):
        self.process.duration = 500
        result = self.run_gate()
        self.assertFalse(result["ok"])
        self.assertIn("TimeoutExpired", result["body_error"])
        self.assertEqual(self.process.actions, ["terminate"])
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
        self.assertLessEqual(result["elapsed"], 3.75 + 50)
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
