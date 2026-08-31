"""W9707 — the parallel test runner, proved over disposable fake suites.

`work/records/2026/08/finding-v12-parallel-test-runner/`.

A test harness that decides which tests run is the one piece of tooling whose
own failure is invisible: a runner that silently drops a shard reports green
for tests nobody executed. So the properties proved here are the ones that
would hide a mistake rather than show one — that collection loses and invents
nothing, that a module belonging to no registry STOPS the run, that
presentation is byte-identical whatever order shards finish in, that a failure
propagates, that the serial registry never overlaps anything, and that an
interrupt leaves no descendant process and no temporary directory behind.

THE SUITES ARE FAKE AND THE RUNNER IS REAL. Every case below drives
`tools/parallel_test.py` itself over a `Suite` pointed at a temporary tree it
built. Nothing re-implements the scheduler in order to assert about it, because
an assertion about a re-implementation is an assertion about the wrong program.

This module is registered PARALLEL, and it is safe there: each case owns its
own `TemporaryDirectory`, every nested run is given an explicit small `--jobs`
so a shard of this module cannot fan out across the host a second time, and the
one timing claim it makes is a 0.6-second sleep against a 0-second one rather
than a race it hopes to win.
"""

import io
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from tools.parallel_test import (METHOD_SPLIT, PARALLEL_MODULES, ROOT, RunnerRefusal,
                                 SERIAL_MODULES, Suite, main, partition, resolve_jobs)

RUNNER = pathlib.Path(__file__).resolve().parents[2] / "tools" / "parallel_test.py"

PRELUDE = """import json
import os
import pathlib
import subprocess
import sys
import time
import unittest

MARKS = pathlib.Path(%r)


def mark(name, started, ended):
    MARKS.joinpath(name + "-" + str(os.getpid())).write_text(
        json.dumps([name, started, ended]), encoding="utf-8")
"""


def case_source(marks, cls, methods, sleep=0.0, failing=(), spawn=False):
    """One fake test module: sleeps, records its interval, maybe misbehaves."""
    lines = [PRELUDE % str(marks), "", "", "class %s(unittest.TestCase):" % cls]
    for method in methods:
        lines.append("    def %s(self):" % method)
        if spawn:
            # A grandchild that outlives its test unless somebody reaps the
            # whole process group. This is the thing an interrupt has to kill.
            lines.append("        child = subprocess.Popen([sys.executable, '-c',"
                         " 'import time; time.sleep(300)'])")
            lines.append("        MARKS.joinpath('grandchild').write_text(str(child.pid),"
                         " encoding='utf-8')")
        lines.append("        started = time.time()")
        lines.append("        time.sleep(%r)" % sleep)
        lines.append("        mark(%r, started, time.time())" % ("%s.%s" % (cls, method)))
        if method in failing:
            lines.append("        self.fail('the fake suite failing on purpose')")
        else:
            lines.append("        self.assertTrue(True)")
        lines.append("")
    return "\n".join(lines)


def worker_line(output):
    """The one stdout line that reports the worker count rather than a result."""
    return [line for line in output.splitlines() if line.startswith("[parallel] jobs=")]


def without_worker_line(output):
    return [line for line in output.splitlines() if not line.startswith("[parallel] jobs=")]


def write_tree(root, modules):
    tests = root / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "__init__.py").write_text("", encoding="utf-8")
    for name, source in modules.items():
        (tests / (name + ".py")).write_text(source, encoding="utf-8")
    return tests


class FakeTreeCase(unittest.TestCase):
    """A private tree, a private marks directory, and nothing shared."""

    def setUp(self):
        self.home = tempfile.TemporaryDirectory(prefix="v12-runner-test-")
        self.addCleanup(self.home.cleanup)
        self.root = pathlib.Path(self.home.name) / "tree"
        self.marks = pathlib.Path(self.home.name) / "marks"
        self.marks.mkdir(parents=True)

    def suite(self, parallel, serial=(), method_split=()):
        return Suite(self.root, parallel, serial, method_split=method_split, pythonpath=None)

    def run_suite(self, suite, argv):
        """One in-process run, returning its exit code and its exact stdout."""
        out = io.StringIO()
        code = main(argv, suite=suite, out=out, progress=None)
        return code, out.getvalue()

    def intervals(self):
        found = []
        for path in sorted(self.marks.iterdir()):
            if path.name == "grandchild":
                continue
            name, started, ended = json.loads(path.read_text(encoding="utf-8"))
            found.append((name, started, ended))
        return found


# -- the decisions the parent makes, with no processes at all -----------------


class TheJobsBoundIsLowerOnly(unittest.TestCase):
    """`--jobs` may only ever REDUCE the host's available CPU count."""

    def test_the_default_is_every_available_cpu_capped_by_ready_shards(self):
        self.assertEqual(resolve_jobs(None, 32, 200), 32)
        self.assertEqual(resolve_jobs(None, 32, 5), 5)
        self.assertEqual(resolve_jobs(None, 32, 0), 1)

    def test_an_override_lowers_and_is_still_capped_by_ready_shards(self):
        self.assertEqual(resolve_jobs("8", 32, 200), 8)
        self.assertEqual(resolve_jobs("8", 32, 3), 3)
        self.assertEqual(resolve_jobs("1", 32, 200), 1)

    def test_raising_the_count_above_the_host_is_refused(self):
        with self.assertRaises(RunnerRefusal) as refused:
            resolve_jobs("33", 32, 200)
        self.assertIn("1..32", str(refused.exception))

    def test_the_refusal_is_against_the_host_and_never_the_shard_count(self):
        # The shard count varies with the selection; the operator's bound must
        # not, or `--jobs 8` would mean different things on different days.
        self.assertEqual(resolve_jobs("8", 32, 2), 2)
        with self.assertRaises(RunnerRefusal):
            resolve_jobs("33", 32, 2)

    def test_anything_that_is_not_a_whole_number_is_refused(self):
        for bad in ("0", "-1", "8.5", "x", "", "  ", "+8", "8_0", "0x8"):
            with self.subTest(jobs=bad):
                with self.assertRaises(RunnerRefusal):
                    resolve_jobs(bad, 32, 200)


class PartitioningLosesAndInventsNothing(unittest.TestCase):

    IDS = ("pkg.mod.Alpha.test_a", "pkg.mod.Alpha.test_b",
           "pkg.mod.Beta.test_a", "pkg.other.Gamma.test_a")

    def test_the_ordinary_shard_is_one_concrete_class(self):
        shards = partition(self.IDS, method_split=())
        self.assertEqual([shard["label"] for shard in shards],
                         ["pkg.mod.Alpha", "pkg.mod.Beta", "pkg.other.Gamma"])
        self.assertEqual(shards[0]["ids"], ["pkg.mod.Alpha.test_a", "pkg.mod.Alpha.test_b"])

    def test_a_named_class_is_split_one_test_method_per_shard(self):
        shards = partition(self.IDS, method_split=("pkg.mod.Alpha",))
        self.assertEqual([shard["label"] for shard in shards],
                         ["pkg.mod.Alpha.test_a", "pkg.mod.Alpha.test_b",
                          "pkg.mod.Beta", "pkg.other.Gamma"])
        self.assertTrue(all(len(shard["ids"]) == 1 for shard in shards[:2]))

    def test_every_collected_id_lands_in_exactly_one_shard(self):
        for split in ((), ("pkg.mod.Alpha",), ("pkg.mod.Alpha", "pkg.mod.Beta")):
            with self.subTest(split=split):
                shards = partition(self.IDS, method_split=split)
                covered = [one for shard in shards for one in shard["ids"]]
                self.assertEqual(sorted(covered), sorted(self.IDS))
                self.assertEqual(len(covered), len(set(covered)))

    def test_a_duplicate_collected_id_is_refused_rather_than_run_twice(self):
        with self.assertRaises(RunnerRefusal) as refused:
            partition(list(self.IDS) + ["pkg.mod.Alpha.test_a"])
        self.assertIn("duplicate", str(refused.exception))

    def test_the_order_does_not_depend_on_the_order_ids_arrived_in(self):
        forward = partition(self.IDS, method_split=("pkg.mod.Alpha",))
        backward = partition(list(reversed(self.IDS)), method_split=("pkg.mod.Alpha",))
        self.assertEqual(forward, backward)


# -- the registry, which is the whole safety argument -------------------------


class TheRegistryFailsClosed(FakeTreeCase):

    def test_a_module_in_neither_registry_stops_the_run(self):
        write_tree(self.root, {"test_known": case_source(self.marks, "Known", ["test_a"]),
                               "test_stranger": case_source(self.marks, "Stranger", ["test_a"])})
        code, output = self.run_suite(self.suite(("tests.test_known",)), ["--jobs", "1"])
        self.assertEqual(code, 2)
        self.assertIn("belong to no registry", output)
        self.assertIn("tests.test_stranger", output)

    def test_a_registered_module_that_is_not_in_the_tree_stops_the_run(self):
        write_tree(self.root, {"test_known": case_source(self.marks, "Known", ["test_a"])})
        code, output = self.run_suite(self.suite(("tests.test_known", "tests.test_ghost")),
                                      ["--jobs", "1"])
        self.assertEqual(code, 2)
        self.assertIn("not in the tree", output)
        self.assertIn("tests.test_ghost", output)

    def test_a_module_in_both_registries_stops_the_run(self):
        write_tree(self.root, {"test_known": case_source(self.marks, "Known", ["test_a"])})
        code, output = self.run_suite(
            self.suite(("tests.test_known",), serial=("tests.test_known",)), ["--jobs", "1"])
        self.assertEqual(code, 2)
        self.assertIn("registered more than once", output)

    def test_discovery_uses_unittests_own_pattern_and_not_a_narrower_one(self):
        # `unittest discover`'s default is `test*.py`. A registry check that
        # looked for `test_*.py` would let this file into the canonical gate
        # while reporting the registry complete.
        write_tree(self.root, {"test_known": case_source(self.marks, "Known", ["test_a"]),
                               "testnounderscore": case_source(self.marks, "Sneaky", ["test_a"])})
        code, output = self.run_suite(self.suite(("tests.test_known",)), ["--jobs", "1"])
        self.assertEqual(code, 2)
        self.assertIn("tests.testnounderscore", output)


class TheRealRegistryDescribesTheRealTree(unittest.TestCase):
    """The one case that fails when somebody adds a v12 test module.

    That failure is the POINT: it says "decide what this module owns" rather
    than letting an unreviewed module inherit the parallel phase by default.
    """

    def test_every_v12_test_module_is_registered_exactly_once(self):
        Suite(ROOT, PARALLEL_MODULES, SERIAL_MODULES).check_registry()

    def test_the_serial_modules_are_the_ones_that_own_an_engine(self):
        # W6636 added the third: `test_lifecycle_composition` builds this
        # repository's worker image AND drives a real daemon through the
        # manager's ordered lifecycle, including a case that asks the engine
        # how many containers carry one assignment's labels. Both reasons the
        # first two are serial apply to it at once.
        #
        # W26283 added the fourth: `test_output_custody_engine` runs the
        # reference worker for real and seals what it wrote, so it owns
        # containers and the built image for the same two reasons again.
        #
        # W26284 added the fifth: `test_credentials_engine` starts real
        # containers carrying a delivered credential and asks the DAEMON what
        # it recorded about them.
        #
        # W32385 added the seventh: `test_ended_runtime_adoption` restarts a
        # manager over the same store and asks the daemon whether the exact
        # ENDED container is still there, which a concurrent suite removing
        # containers would answer for it.
        #
        # W32382 added the sixth: `test_negative_race_endings` subclasses
        # W6636's composition fixture and drives the same daemon through the
        # endings the positive arc does not reach, counting containers for one
        # assignment's labels exactly as it does.
        #
        # W33935 added the eighth: `test_input_delivery` reuses W6636's engine
        # fixture, builds the same worker image and starts containers over the
        # manager's own composed argv -- and one of its cases asks the daemon
        # how many containers carry an assignment's labels, which a concurrent
        # suite creating or removing them would answer for it.
        #
        # W34998 added the ninth: `test_failed_start_destroy_engine` builds the
        # worker image and creates real containers in order to remove them,
        # so it owns the same two artefacts the eight before it do. It runs
        # straight after the image gate that produces the one it needs.
        self.assertEqual(SERIAL_MODULES,
                         ("tests.manager.test_worker_container",
                          "tests.manager.test_failed_start_destroy_engine",
                          "tests.manager.test_oci_engine",
                          "tests.manager.test_lifecycle_composition",
                          "tests.manager.test_negative_race_endings",
                          "tests.manager.test_ended_runtime_adoption",
                          "tests.manager.test_output_custody_engine",
                          "tests.manager.test_credentials_engine",
                          "tests.manager.test_refused_session_engine",
                          "tests.manager.test_custody_engine",
                          "tests.manager.test_input_delivery",
                          # W39356 added the twelfth:
                          # `test_worker_entry_engine` inherits the same
                          # composition fixture, builds the same image and
                          # drives `docker exec` against containers it started
                          # under one assignment's labels -- and one case
                          # removes a container and then asks the daemon, which
                          # a concurrent suite would answer for it.
                          "tests.manager.test_worker_entry_engine",
                          # W39357 added the thirteenth: the dogfood image
                          # gate builds an image and starts containers from
                          # it, so it owns the same two artefacts every other
                          # engine gate does.
                          "tests.manager.test_dogfood_image",
                          # W44716 added the fourteenth:
                          # `test_abandoned_attempt_engine` starts real
                          # containers and then asks the daemon whether a
                          # RUNNING one was removed, which is a question a
                          # concurrent suite could answer for it.
                          "tests.manager.test_abandoned_attempt_engine",
                          # W39358 added the fifteenth: the whole-arc gate
                          # builds the dogfood image, runs the composed arc
                          # over a real container and asks the daemon whether
                          # the runtime is gone.
                          "tests.tools.test_dogfood_arc_engine",
                          # W39358 added the sixteenth: the public-retry gate
                          # derives an image from the reference worker and
                          # drives the documented commands over real
                          # containers.
                          "tests.tools.test_dogfood_retry_engine"))
        for module in SERIAL_MODULES:
            with self.subTest(module=module):
                self.assertNotIn(module, PARALLEL_MODULES)

    def test_this_module_registered_itself(self):
        self.assertIn("tests.tools.test_parallel_runner", PARALLEL_MODULES)

    def test_every_method_split_target_is_a_real_class_in_a_parallel_module(self):
        for key in METHOD_SPLIT:
            with self.subTest(key=key):
                module = key.rsplit(".", 1)[0]
                self.assertIn(module, PARALLEL_MODULES)
                loaded = list(unittest.TestLoader().loadTestsFromName(key))
                self.assertGreater(len(loaded), 1,
                                   "splitting a class with one test buys nothing")


# -- presentation, which must not depend on when anything finished ------------


class OutputDoesNotDependOnCompletionOrder(FakeTreeCase):

    SLOW, FAST = 0.6, 0.0

    def build(self, alpha_sleep, zulu_sleep):
        write_tree(self.root, {"test_alpha": case_source(self.marks, "Alpha", ["test_a"], alpha_sleep),
                               "test_zulu": case_source(self.marks, "Zulu", ["test_a"], zulu_sleep)})
        return self.suite(("tests.test_alpha", "tests.test_zulu"))

    def test_inverting_which_shard_finishes_first_changes_nothing_in_stdout(self):
        code, slow_first = self.run_suite(self.build(self.SLOW, self.FAST), ["--jobs", "2"])
        self.assertEqual(code, 0)
        ended = {name: end for name, _, end in self.intervals()}
        self.assertGreater(ended["Alpha.test_a"], ended["Zulu.test_a"],
                           "the fake suite did not actually invert completion order")

        self.setUp()
        code, fast_first = self.run_suite(self.build(self.FAST, self.SLOW), ["--jobs", "2"])
        self.assertEqual(code, 0)
        ended = {name: end for name, _, end in self.intervals()}
        self.assertGreater(ended["Zulu.test_a"], ended["Alpha.test_a"])

        self.assertEqual(slow_first, fast_first)
        self.assertLess(slow_first.index("tests.test_alpha.Alpha"),
                        slow_first.index("tests.test_zulu.Zulu"))

    def test_one_worker_and_the_default_agree_on_ids_and_on_outcome(self):
        suite = self.build(0.0, 0.0)
        alone_code, alone = self.run_suite(suite, ["--jobs", "1"])
        self.setUp()
        suite = self.build(0.0, 0.0)
        default_code, default = self.run_suite(suite, [])
        self.assertEqual(alone_code, default_code)
        # ONE line is expected to differ, and it is the input rather than a
        # result: the `[parallel] jobs=N` line is the runner saying how many
        # workers it used, which is the whole variable under test. Normalizing
        # it is named here rather than achieved by loosening the comparison,
        # so a second line drifting apart would still fail this case.
        self.assertNotEqual(worker_line(alone), worker_line(default))
        self.assertEqual(without_worker_line(alone), without_worker_line(default))

    def test_the_collected_ids_are_the_same_at_any_worker_count(self):
        suite = self.build(0.0, 0.0)
        _, alone = self.run_suite(suite, ["--jobs", "1", "--print-ids"])
        _, default = self.run_suite(suite, ["--print-ids"])
        self.assertEqual(alone.split(), ["tests.test_alpha.Alpha.test_a",
                                         "tests.test_zulu.Zulu.test_a"])
        self.assertEqual(alone, default)


class AFailingShardIsReportedAndStopsTheLaterPhases(FakeTreeCase):

    def build(self):
        write_tree(self.root, {
            "test_good": case_source(self.marks, "Good", ["test_a"]),
            "test_bad": case_source(self.marks, "Bad", ["test_a"], failing=["test_a"]),
            "test_serial": case_source(self.marks, "Serial", ["test_a"])})
        return self.suite(("tests.test_good", "tests.test_bad"), serial=("tests.test_serial",))

    def test_the_failure_propagates_to_the_exit_code_and_the_summary(self):
        code, output = self.run_suite(self.build(), ["--jobs", "2"])
        self.assertEqual(code, 1)
        self.assertIn("[FAIL] tests.test_bad.Bad", output)
        self.assertIn("[pass] tests.test_good.Good", output)
        self.assertIn("the fake suite failing on purpose", output)
        self.assertIn("-> FAILED", output)

    def test_a_failed_parallel_phase_never_reaches_the_serial_registry(self):
        code, output = self.run_suite(self.build(), ["--jobs", "2"])
        self.assertEqual(code, 1)
        self.assertIn("the serial registry did not run", output)
        self.assertNotIn("Serial.test_a", [name for name, _, _ in self.intervals()])

    def test_a_failing_sibling_never_abandons_the_other_shards(self):
        # Drain-then-verdict: the good shard's result is present, which it
        # would not be if the runner had bailed out on the first failure.
        self.run_suite(self.build(), ["--jobs", "1"])
        ran = sorted(name for name, _, _ in self.intervals())
        self.assertEqual(ran, ["Bad.test_a", "Good.test_a"])


class TheSerialRegistryOverlapsNothing(FakeTreeCase):

    def test_serial_modules_run_after_the_parallel_phase_and_one_at_a_time(self):
        write_tree(self.root, {
            "test_pure_a": case_source(self.marks, "PureA", ["test_a"], 0.2),
            "test_pure_b": case_source(self.marks, "PureB", ["test_a"], 0.2),
            "test_serial_a": case_source(self.marks, "SerialA", ["test_a"], 0.2),
            "test_serial_b": case_source(self.marks, "SerialB", ["test_a"], 0.2)})
        suite = self.suite(("tests.test_pure_a", "tests.test_pure_b"),
                           serial=("tests.test_serial_a", "tests.test_serial_b"))
        code, output = self.run_suite(suite, ["--jobs", "2"])
        self.assertEqual(code, 0, output)

        found = {name: (start, end) for name, start, end in self.intervals()}
        self.assertEqual(sorted(found), ["PureA.test_a", "PureB.test_a",
                                         "SerialA.test_a", "SerialB.test_a"])
        for serial in ("SerialA.test_a", "SerialB.test_a"):
            for other in found:
                if other == serial:
                    continue
                with self.subTest(serial=serial, other=other):
                    self.assertFalse(found[serial][0] < found[other][1]
                                     and found[other][0] < found[serial][1],
                                     f"{serial} overlapped {other}")
        self.assertIn("[serial] 2 source modules, one at a time", output)

    def test_the_summary_reports_the_two_phases_separately(self):
        write_tree(self.root, {"test_pure": case_source(self.marks, "Pure", ["test_a"]),
                               "test_serial": case_source(self.marks, "Serial", ["test_a"])})
        code, output = self.run_suite(self.suite(("tests.test_pure",), serial=("tests.test_serial",)),
                                      ["--jobs", "1"])
        self.assertEqual(code, 0, output)
        self.assertIn("--- parallel source ---", output)
        self.assertIn("--- serial source ---", output)
        self.assertIn("parallel source: 1 tests", output)
        self.assertIn("serial source: 1 tests", output)


# -- what is left behind, which is the part nobody notices until it matters ----


class DriverCase(FakeTreeCase):
    """Runs the runner as a REAL child, with a private TMPDIR to inspect."""

    def driver(self, parallel, serial=()):
        path = pathlib.Path(self.home.name) / "driver.py"
        path.write_text("import sys\n"
                        "sys.path.insert(0, %r)\n"
                        "from tools.parallel_test import Suite, main\n"
                        "suite = Suite(%r, %r, %r, method_split=(), pythonpath=None)\n"
                        "raise SystemExit(main(sys.argv[1:], suite=suite))\n"
                        % (str(ROOT), str(self.root), tuple(parallel), tuple(serial)),
                        encoding="utf-8")
        return path

    def temp(self):
        place = pathlib.Path(self.home.name) / "tmp"
        place.mkdir(exist_ok=True)
        return place

    def launch(self, driver, argv, temp):
        environment = dict(os.environ, TMPDIR=str(temp))
        environment.pop("PYTHONPATH", None)
        return subprocess.Popen([sys.executable, str(driver)] + argv, env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                start_new_session=True)


def alive(pid):
    """True only for a process that still exists AND is not already a zombie."""
    try:
        state = pathlib.Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except (FileNotFoundError, ProcessLookupError):
        return False
    return state.rsplit(")", 1)[-1].split()[0] != "Z"


def kill_if_alive(pid):
    """Keep a failed cleanup regression from leaking the process it exposed."""
    if not alive(pid):
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class AnInterruptLeavesNothingBehind(DriverCase):

    def test_it_reaps_its_shards_descendants_and_removes_its_result_root(self):
        write_tree(self.root, {"test_spawner": case_source(self.marks, "Spawner", ["test_a"],
                                                           sleep=60, spawn=True)})
        temp = self.temp()
        child = self.launch(self.driver(("tests.test_spawner",)), ["--jobs", "1"], temp)
        self.addCleanup(lambda: child.poll() is None and child.kill())

        grandchild = self.marks / "grandchild"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not grandchild.exists():
            time.sleep(0.05)
        self.assertTrue(grandchild.exists(), "the fake suite never started its grandchild")
        pid = int(grandchild.read_text(encoding="utf-8"))
        self.assertTrue(alive(pid))

        child.send_signal(signal.SIGINT)
        child.communicate(timeout=60)
        self.assertNotEqual(child.returncode, 0, "an interrupted run must not report success")

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and alive(pid):
            time.sleep(0.05)
        self.assertFalse(alive(pid), f"the shard's descendant {pid} survived the interrupt")
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [],
                         "the runner left its disposable result root behind")

    def test_it_kills_a_term_ignoring_descendant_after_its_shard_leader_exits(self):
        grandchild = self.marks / "grandchild-ignoring-term"
        command = ("import os,pathlib,signal,time; "
                   "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                   "pathlib.Path(%r).write_text(str(os.getpid()), encoding='utf-8'); "
                   "time.sleep(300)" % str(grandchild))
        source = (PRELUDE % str(self.marks)) + (
            "\n\nclass Spawner(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        subprocess.Popen([sys.executable, '-c', %r])\n"
            "        time.sleep(60)\n" % command)
        write_tree(self.root, {"test_spawner": source})
        temp = self.temp()
        child = self.launch(self.driver(("tests.test_spawner",)), ["--jobs", "1"], temp)
        self.addCleanup(lambda: child.poll() is None and child.kill())

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not grandchild.exists():
            time.sleep(0.05)
        self.assertTrue(grandchild.exists(), "the fake suite never started its grandchild")
        pid = int(grandchild.read_text(encoding="utf-8"))
        self.addCleanup(kill_if_alive, pid)
        self.assertTrue(alive(pid))

        child.send_signal(signal.SIGINT)
        child.communicate(timeout=60)
        self.assertNotEqual(child.returncode, 0, "an interrupted run must not report success")

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and alive(pid):
            time.sleep(0.05)
        self.assertFalse(alive(pid),
                         f"the TERM-ignoring descendant {pid} survived the interrupt")

    def test_an_interrupt_during_retirement_cannot_cross_a_tracking_gap(self):
        grandchild = self.marks / "retirement-race-grandchild"
        command = ("import os,pathlib,signal,time; "
                   "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                   "pathlib.Path(%r).write_text(str(os.getpid()), encoding='utf-8'); "
                   "time.sleep(300)" % str(grandchild))
        source = (PRELUDE % str(self.marks)) + (
            "\n\nclass Spawner(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        subprocess.Popen([sys.executable, '-c', %r])\n"
            "        deadline = time.time() + 30\n"
            "        while time.time() < deadline and not pathlib.Path(%r).exists():\n"
            "            time.sleep(0.05)\n"
            "        self.assertTrue(pathlib.Path(%r).exists())\n"
            % (command, str(grandchild), str(grandchild)))
        write_tree(self.root, {"test_spawner": source})

        driver = pathlib.Path(self.home.name) / "interrupting-driver.py"
        driver.write_text(
            "import os\n"
            "import pathlib\n"
            "import signal\n"
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "from tools.parallel_test import Run, Suite, main\n"
            "suite = Suite(%r, %r, (), method_split=(), pythonpath=None)\n"
            "original = Run.signal_group\n"
            "armed = True\n"
            "def interrupt_at_signal(self, pgid, which):\n"
            "    global armed\n"
            "    if armed and which == signal.SIGKILL and pathlib.Path(%r).exists():\n"
            "        armed = False\n"
            "        os.kill(os.getpid(), signal.SIGINT)\n"
            "    return original(self, pgid, which)\n"
            "Run.signal_group = interrupt_at_signal\n"
            "raise SystemExit(main(sys.argv[1:], suite=suite))\n"
            % (str(ROOT), str(self.root), ("tests.test_spawner",), str(grandchild)),
            encoding="utf-8")
        temp = self.temp()
        child = self.launch(driver, ["--jobs", "1"], temp)
        output = child.communicate(timeout=120)[0].decode("utf-8", "replace")
        self.assertEqual(child.returncode, 130, output)
        self.assertTrue(grandchild.exists(), "the fake suite never started its grandchild")
        pid = int(grandchild.read_text(encoding="utf-8"))
        self.addCleanup(kill_if_alive, pid)

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and alive(pid):
            time.sleep(0.05)
        self.assertFalse(alive(pid),
                         f"the descendant {pid} survived an interrupt during retirement")
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [])

    def test_an_interrupt_after_spawn_cannot_cross_the_registration_gap(self):
        grandchild = self.marks / "spawn-race-grandchild"
        leader = self.marks / "spawn-race-leader"
        command = ("import os,pathlib,signal,time; "
                   "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                   "pathlib.Path(%r).write_text(str(os.getpid()), encoding='utf-8'); "
                   "time.sleep(300)" % str(grandchild))
        source = (PRELUDE % str(self.marks)) + (
            "\n\nclass Spawner(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        subprocess.Popen([sys.executable, '-c', %r])\n"
            "        deadline = time.time() + 30\n"
            "        while time.time() < deadline and not pathlib.Path(%r).exists():\n"
            "            time.sleep(0.05)\n"
            "        self.assertTrue(pathlib.Path(%r).exists())\n"
            "        time.sleep(60)\n"
            % (command, str(grandchild), str(grandchild)))
        write_tree(self.root, {"test_spawner": source})

        driver = pathlib.Path(self.home.name) / "spawn-interrupting-driver.py"
        driver.write_text(
            "import os\n"
            "import pathlib\n"
            "import signal\n"
            "import sys\n"
            "import time\n"
            "sys.path.insert(0, %r)\n"
            "from tools.parallel_test import Suite, main\n"
            "suite = Suite(%r, %r, (), method_split=(), pythonpath=None)\n"
            "original = Suite.spawn\n"
            "armed = True\n"
            "def interrupt_after_spawn(self, argv, err):\n"
            "    global armed\n"
            "    child = original(self, argv, err)\n"
            "    if armed and argv[0] == 'run-shard':\n"
            "        armed = False\n"
            "        pathlib.Path(%r).write_text(str(child.pid), encoding='utf-8')\n"
            "        deadline = time.monotonic() + 30\n"
            "        while time.monotonic() < deadline and not pathlib.Path(%r).exists():\n"
            "            time.sleep(0.05)\n"
            "        os.kill(os.getpid(), signal.SIGINT)\n"
            "    return child\n"
            "Suite.spawn = interrupt_after_spawn\n"
            "raise SystemExit(main(sys.argv[1:], suite=suite))\n"
            % (str(ROOT), str(self.root), ("tests.test_spawner",),
               str(leader), str(grandchild)), encoding="utf-8")
        temp = self.temp()
        child = self.launch(driver, ["--jobs", "1"], temp)
        output = child.communicate(timeout=120)[0].decode("utf-8", "replace")
        self.assertEqual(child.returncode, 130, output)
        self.assertTrue(leader.exists(), "the injected spawn never published its leader")
        self.assertTrue(grandchild.exists(), "the fake suite never started its grandchild")
        pids = [int(leader.read_text(encoding="utf-8")),
                int(grandchild.read_text(encoding="utf-8"))]
        for pid in pids:
            self.addCleanup(kill_if_alive, pid)

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and any(alive(pid) for pid in pids):
            time.sleep(0.05)
        survivors = [pid for pid in pids if alive(pid)]
        self.assertEqual(survivors, [],
                         f"the unregistered shard left surviving processes {survivors}")
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [])

    def test_a_signal_during_final_cleanup_is_recorded_until_cleanup_finishes(self):
        write_tree(self.root, {"test_good": case_source(self.marks, "Good", ["test_a"])})
        driver = pathlib.Path(self.home.name) / "cleanup-interrupting-driver.py"
        driver.write_text(
            "import os\n"
            "import signal\n"
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "from tools.parallel_test import Run, Suite, main\n"
            "suite = Suite(%r, %r, (), method_split=(), pythonpath=None)\n"
            "original = Run.shutdown\n"
            "armed = True\n"
            "def interrupt_during_cleanup(self):\n"
            "    global armed\n"
            "    if armed:\n"
            "        armed = False\n"
            "        os.kill(os.getpid(), signal.SIGINT)\n"
            "    return original(self)\n"
            "Run.shutdown = interrupt_during_cleanup\n"
            "raise SystemExit(main(sys.argv[1:], suite=suite))\n"
            % (str(ROOT), str(self.root), ("tests.test_good",)), encoding="utf-8")
        temp = self.temp()
        child = self.launch(driver, ["--jobs", "1"], temp)
        output = child.communicate(timeout=120)[0].decode("utf-8", "replace")
        self.assertEqual(child.returncode, 130, output)
        self.assertIn("[runner] interrupted by signal 2 during cleanup", output)
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [],
                         "a signal interrupted final result-root cleanup")


class AFailingRunAlsoLeavesNothingBehind(DriverCase):

    def test_the_result_root_is_removed_when_the_suite_fails(self):
        write_tree(self.root, {"test_bad": case_source(self.marks, "Bad", ["test_a"],
                                                       failing=["test_a"])})
        temp = self.temp()
        child = self.launch(self.driver(("tests.test_bad",)), ["--jobs", "1"], temp)
        output = child.communicate(timeout=120)[0].decode("utf-8", "replace")
        self.assertEqual(child.returncode, 1, output)
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [])

    def test_a_refused_run_removes_it_too(self):
        write_tree(self.root, {"test_bad": case_source(self.marks, "Bad", ["test_a"])})
        temp = self.temp()
        child = self.launch(self.driver(("tests.test_bad", "tests.test_ghost")), ["--jobs", "1"], temp)
        output = child.communicate(timeout=120)[0].decode("utf-8", "replace")
        self.assertEqual(child.returncode, 2, output)
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [])

    def test_a_failed_shard_does_not_orphan_a_descendant_when_its_leader_exits(self):
        grandchild = self.marks / "failed-shard-grandchild"
        command = ("import os,pathlib,signal,time; "
                   "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                   "pathlib.Path(%r).write_text(str(os.getpid()), encoding='utf-8'); "
                   "time.sleep(300)" % str(grandchild))
        source = (PRELUDE % str(self.marks)) + (
            "\n\nclass Bad(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        subprocess.Popen([sys.executable, '-c', %r])\n"
            "        deadline = time.time() + 30\n"
            "        while time.time() < deadline and not pathlib.Path(%r).exists():\n"
            "            time.sleep(0.05)\n"
            "        self.assertTrue(pathlib.Path(%r).exists())\n"
            "        self.fail('the fake suite failing on purpose')\n"
            % (command, str(grandchild), str(grandchild)))
        write_tree(self.root, {"test_bad": source})
        temp = self.temp()
        child = self.launch(self.driver(("tests.test_bad",)), ["--jobs", "1"], temp)
        output = child.communicate(timeout=120)[0].decode("utf-8", "replace")
        self.assertEqual(child.returncode, 1, output)
        self.assertTrue(grandchild.exists(), "the fake suite never started its grandchild")
        pid = int(grandchild.read_text(encoding="utf-8"))
        self.addCleanup(kill_if_alive, pid)

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and alive(pid):
            time.sleep(0.05)
        self.assertFalse(alive(pid), f"the failed shard's descendant {pid} survived the run")
        self.assertEqual(sorted(path.name for path in temp.iterdir()), [])


class AShardThatDiesWithoutAReportIsAFailure(FakeTreeCase):
    """The failure mode that would otherwise read as green.

    A shard killed by the kernel — OOM, a segfaulting extension, an external
    `kill` — writes no report. Counting a missing report as "no failures found"
    is how a runner claims success for tests it never ran, so it is a failure
    with the child's own stderr attached.
    """

    def test_a_shard_that_kills_its_own_interpreter_is_reported_as_an_error(self):
        source = (PRELUDE % str(self.marks)) + (
            "\n\nclass Suicide(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        sys.stderr.write('about to die\\n')\n"
            "        sys.stderr.flush()\n"
            "        os.kill(os.getpid(), 9)\n")
        write_tree(self.root, {"test_suicide": source})
        code, output = self.run_suite(self.suite(("tests.test_suicide",)), ["--jobs", "1"])
        self.assertEqual(code, 1)
        self.assertIn("[FAIL] tests.test_suicide.Suicide", output)
        self.assertIn("about to die", output)


class CollectionRefusesAModuleItCannotLoad(FakeTreeCase):

    def test_an_unimportable_module_stops_the_run_rather_than_becoming_one_failure(self):
        write_tree(self.root, {"test_broken": "import nonexistent_module_w9707\n"})
        code, output = self.run_suite(self.suite(("tests.test_broken",)), ["--jobs", "1"])
        self.assertEqual(code, 2)
        self.assertIn("collecting tests.test_broken failed", output)


if __name__ == "__main__":
    unittest.main()
