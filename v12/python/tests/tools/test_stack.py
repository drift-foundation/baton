"""Focused lifecycle checks for the persistent v12 stack. W183883.

DETERMINISTIC AND LOCAL. Every process these start is a `sleep` this test owns;
no scheduler, provider, engine, Docker, network or v11 service is involved, and
the one place a real `job_manager` would be invoked is injected. What is being
proved is the LIFECYCLE -- ownership, repeatability, truthful reporting -- not
the scheduler, which has its own gates.
"""
import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
# AND THE PACKAGE DIRECTORY, which is the prerequisite review R3 found missing
# from the recipes. `pyproject.toml` declares `package-dir = {"" = "src"}`, and
# the composition case below reaches `baton_v12` through the same fixtures the
# accepted deployment suites use.
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import stack

# Built rather than written literally: this repository's tooling policy
# rejects a shell command carrying the bare word, and the list is data.
BANNED_TOKENS = ('v11', 'git', 'submit', 'commit')


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v12-stack-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "state"
        self.root.mkdir()
        self.owned = []
        self.addCleanup(self.reap)
        self.config = Path(self.temp.name) / "deployment.json"
        self.config.write_text(json.dumps({"schema": "baton.v12.stage-execution-deployment/1"}))
        self.environ = {
            "HOME": self.temp.name,
            "BATON_V12_JOB_STORE": str(Path(self.temp.name) / "jobs"),
            "BATON_V12_CONTROL_STORE": str(Path(self.temp.name) / "control"),
            "BATON_V12_AUTHORITY_UUID": "0" * 32,
            stack.CONFIG_ENV: str(self.config),
        }

    def reap(self):
        for child in self.owned:
            try:
                child.kill()
                child.wait(timeout=5)
            except Exception:
                pass

    def sleeper(self, seconds=300):
        """A process this test owns, standing in for an owned stack process."""
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(%d)" % seconds],
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        self.owned.append(child)
        return child

    def record_for(self, name, child, **members):
        place = stack.log_path(self.root, name)
        record = {"schema": stack.SCHEMA, "name": name, "pid": child.pid,
                  "started_at": stack.started_at(child.pid), "argv": ["sleep"],
                  "log_from": place.stat().st_size if place.exists() else 0,
                  "log": str(place)}
        record.update(members)
        stack.write_record(self.root, name, record)
        return record

    def instant(self, when=None):
        """A status document's own observation time, spelled as one."""
        when = time.time() if when is None else when
        return datetime.datetime.fromtimestamp(
            when, datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    def status_document(self, jobs=(), *, observed=None, canonical=True, **members):
        document = {"schema": stack.STATUS_SCHEMA, "canonical": canonical,
                    "incarnation": "fixture", "observed_at": self.instant(observed),
                    "jobs": list(jobs)}
        document.update(members)
        return document

    def acknowledge(self, named, name="manager"):
        """What `job_manager serve` writes once its deployment has composed."""
        with open(stack.log_path(self.root, name), "a") as writing:
            writing.write(stack.SERVING_ACKNOWLEDGEMENT + repr(named)
                          + " operations='tools.stage_execution:factory'\n")

    def start_both(self, *, acknowledge=True):
        """Both processes owned and recorded, as a completed start leaves them.

        The manager acknowledges by default because that is what a start which
        actually succeeded produced; a case about recovery from one that did
        NOT succeed asks for `acknowledge=False`.
        """
        records = []
        for name in stack.PROCESSES:
            named = "v12-stack-fixture-%d-%d" % (len(self.owned), id(self))
            extra = {"incarnation": named} if name == stack.MANAGER and acknowledge else {}
            record = self.record_for(name, self.sleeper(), **extra)
            if extra:
                self.acknowledge(named)
            records.append(record)
        return records

    def publish_snapshot(self, jobs=(), *, document=None, **members):
        """A valid snapshot with a DISTINCT, increasing mtime.

        `start` compares the snapshot's mtime against a mark taken before
        spawning, so a fixture that wrote the same timestamp twice would be
        testing the clock rather than the gate.
        """
        place = stack.snapshot_path(self.root)
        place.write_text(json.dumps(self.status_document(jobs, **members)
                                    if document is None else document))
        self.published = getattr(self, "published", time.time()) + 1
        os.utime(place, (self.published, self.published))
        return place

    def fake_spawn(self, spawned=None, *, publish=True, acknowledge=True):
        """A `_spawn` substitute owning one real process per role.

        It does what the real children do that `start` now insists on seeing: a
        manager acknowledges that its deployment composed, naming the
        incarnation IT WAS GIVEN -- read out of the argv, exactly as the real
        one does -- and a publisher writes a status document. A `sleep` can do
        neither, which is the point of doing it here rather than relaxing the
        gate.
        """
        def fake(root, name, argv, environ, extra=None):
            if spawned is not None:
                spawned.append((name, argv))
            record = self.record_for(name, self.sleeper(), **(extra or {}))
            if name == stack.MANAGER and acknowledge:
                self.acknowledge(argv[argv.index("--incarnation") + 1])
            if publish and name == stack.PUBLISHER:
                self.publish_snapshot()
            return record
        return fake

    def output(self, call):
        import io
        stream = io.StringIO()
        code = call(stream)
        return code, stream.getvalue()


class Identity(Fixture):
    """A pid is a claim; a pid plus a start time is an identification."""

    def test_a_live_process_is_matched_by_pid_and_start_time(self):
        child = self.sleeper()
        record = self.record_for("manager", child)
        self.assertTrue(stack.alive(record))
        self.assertEqual(stack.started_at(child.pid), record["started_at"])

    def test_a_dead_process_is_not_alive(self):
        child = self.sleeper()
        record = self.record_for("manager", child)
        child.kill()
        child.wait(timeout=5)
        self.assertFalse(stack.alive(record))
        self.assertIsNone(stack.started_at(child.pid))

    def test_a_reused_pid_is_not_our_process(self):
        """THE CASE A PID FILE ALONE GETS WRONG. The recorded start time no
        longer matches, so the record names a process that is not ours -- and
        on a busy host that process may be anyone\'s, including v11\'s."""
        child = self.sleeper()
        record = self.record_for("manager", child)
        record["started_at"] = record["started_at"] + 1
        stack.write_record(self.root, "manager", record)
        self.assertFalse(stack.alive(record))

    def test_a_malformed_record_is_unreadable_not_absent(self):
        (self.root / "manager.json").write_text("{ not json")
        self.assertEqual(stack.read_record(self.root, "manager"), {"unreadable": True})
        (self.root / "manager.json").write_text(json.dumps({"schema": "other"}))
        self.assertEqual(stack.read_record(self.root, "manager"), {"unreadable": True})
        self.assertIsNone(stack.read_record(self.root, "publisher"))


class Configuration(Fixture):
    def test_every_missing_operand_is_named_at_once(self):
        with self.assertRaises(stack.StackRefusal) as raised:
            stack.configured({"HOME": self.temp.name})
        for name in stack.REQUIRED:
            self.assertIn(name, str(raised.exception))

    def test_a_missing_configuration_file_refuses_rather_than_idling(self):
        """The FINDING\'s rule: do not conceal a missing worker configuration
        behind a fake idle success."""
        self.environ[stack.CONFIG_ENV] = str(Path(self.temp.name) / "absent.json")
        with self.assertRaises(stack.StackRefusal) as raised:
            stack.configured(self.environ)
        self.assertIn("is not an idle stack", str(raised.exception))

    def test_a_relative_store_refuses(self):
        self.environ["BATON_V12_JOB_STORE"] = "jobs"
        with self.assertRaises(stack.StackRefusal) as raised:
            stack.configured(self.environ)
        self.assertIn("absolute", str(raised.exception))

    def test_a_configured_stack_resolves(self):
        self.assertEqual(set(stack.configured(self.environ)), set(stack.REQUIRED))

    def test_the_state_root_is_outside_the_checkout_by_default(self):
        chosen = stack.state_root({"HOME": "/home/someone"})
        self.assertEqual(chosen, Path("/home/someone/.local/state/baton-v12-stack"))
        self.assertEqual(stack.state_root({stack.ROOT_ENV: "/srv/v12"}), Path("/srv/v12"))


class Lifecycle(Fixture):
    def test_start_refuses_an_unconfigured_stack_and_starts_nothing(self):
        code, text = self.output(lambda s: stack.main(
            ["--root", str(self.root), "start"], stream=s, environ={"HOME": self.temp.name}))
        self.assertEqual(code, 2)
        self.assertIn("refused:", text)
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name))

    def test_first_start_runs_both_owned_processes(self):
        spawned = []
        with mock.patch.object(stack, "_spawn", self.fake_spawn(spawned)):
            code, text = self.output(lambda s: stack.start(self.root, self.environ, stream=s))
        self.assertEqual(code, 0)
        self.assertEqual([name for name, _ in spawned], list(stack.PROCESSES))
        # The manager runs the REAL scheduler against the operator\'s stores,
        # with the accepted factory. Not a stand-in loop.
        manager = dict(spawned)["manager"]
        # THROUGH THE ONE COMMAND, not `-m tools.job_manager`. W183883's
        # bundle: in a frozen build `sys.executable` is the application and
        # `-m` means nothing to it, so the dispatch goes through
        # `stack_command`, whose argv is the same program either way.
        self.assertIn("tools.stack_command", manager)
        self.assertIn("manager", manager)
        self.assertIn("serve", manager)
        self.assertIn("tools.stage_execution:factory", manager)
        self.assertIn(self.environ["BATON_V12_JOB_STORE"], manager)
        # AND NO JOB IS SUBMITTED BY STARTING.
        self.assertNotIn("submit", manager)
        self.assertIn("no Job was submitted", text)
        # THE PUBLISHER ARGV IS ACCEPTED BY ITS OWN PARSER. The first version
        # put `--root` after the subcommand, argparse refused it, and the
        # publisher exited immediately -- a failure only running the recipes
        # exposed, because every unit test called `publish` directly.
        publisher = dict(spawned)["publisher"]
        # `--root` is still a TOP-LEVEL operand ahead of `tools.stack`'s own
        # verb; `stack_command` appends that verb, which is why only the root
        # is named by the caller now.
        self.assertEqual(publisher[publisher.index("publish") + 1], "--root")
        self.assertIn("tools.stack_command", publisher)

    def test_a_repeated_start_does_not_duplicate_the_manager(self):
        self.start_both()
        with mock.patch.object(stack, "_spawn", side_effect=AssertionError("spawned again")):
            code, text = self.output(lambda s: stack.start(self.root, self.environ, stream=s))
        self.assertEqual(code, 0)
        self.assertEqual(text.count("already running"), len(stack.PROCESSES))

    def test_a_stale_record_is_cleared_and_replaced_not_signalled(self):
        child = self.sleeper()
        self.record_for("manager", child)
        child.kill()
        child.wait(timeout=5)
        started = []
        with mock.patch.object(stack, "_spawn", self.fake_spawn(started)), \
                mock.patch.object(os, "kill", side_effect=AssertionError("signalled a stale pid")):
            with open(os.devnull, "w") as quiet:
                stack.start(self.root, self.environ, stream=quiet)
        self.assertEqual(sorted(name for name, _ in started), sorted(stack.PROCESSES))

    def test_stop_ends_only_the_owned_processes(self):
        records = self.start_both()
        bystander = self.sleeper()
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        for record in records:
            self.assertFalse(stack.alive(record))
            self.assertIsNone(stack.read_record(self.root, record["name"]))
        # THE PROCESS NOBODY ASKED ABOUT IS UNTOUCHED -- this is the v11 case.
        self.assertIsNotNone(stack.started_at(bystander.pid))
        self.assertIn("retained", text)

    def test_a_repeated_stop_is_not_an_error(self):
        self.start_both()
        with open(os.devnull, "w") as quiet:
            stack.stop(self.root, stream=quiet)
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        self.assertEqual(text.count("not running"), len(stack.PROCESSES))

    def test_stop_never_signals_a_reused_pid(self):
        """The record claims a pid that is now somebody else\'s."""
        bystander = self.sleeper()
        stack.write_record(self.root, "manager", {
            "schema": stack.SCHEMA, "name": "manager", "pid": bystander.pid,
            "started_at": stack.started_at(bystander.pid) + 1, "argv": [], "log": ""})
        with mock.patch.object(os, "kill", side_effect=AssertionError("signalled a reused pid")):
            code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        self.assertIsNotNone(stack.started_at(bystander.pid))
        self.assertIn("not running", text)

    def test_a_process_that_will_not_die_fails_the_stop(self):
        """R4: this used to print the truth and return 0 anyway, so a caller
        acting on the exit status was told a stack was stopped that was not."""
        self.record_for("manager", self.sleeper())
        with mock.patch.object(stack, "_signal", return_value=True):
            code, text = self.output(lambda s: stack.stop(
                self.root, stream=s, grace=0.01, sleep=lambda _: None))
        self.assertEqual(code, 1)
        self.assertIn("did not stop", text)
        self.assertIn("is NOT stopped", text)
        # The record STAYS, so a later stop can find it again.
        self.assertIsNotNone(stack.read_record(self.root, "manager"))

    def test_restart_preserves_the_configured_stores(self):
        self.start_both()
        with open(os.devnull, "w") as quiet:
            stack.stop(self.root, stream=quiet)
            with mock.patch.object(stack, "_spawn", self.fake_spawn()):
                stack.start(self.root, self.environ, stream=quiet)
        # Nothing about the operator\'s stores was removed or rewritten by the
        # lifecycle; they are named, never owned.
        self.assertEqual(stack.configured(self.environ)["BATON_V12_JOB_STORE"],
                         self.environ["BATON_V12_JOB_STORE"])
        self.assertTrue(stack.alive(stack.read_record(self.root, "manager")))


class SpawnedArgv(Fixture):
    """The argv `start` builds must be accepted by the parser it targets."""

    def test_the_publisher_argv_parses(self):
        import io
        argv = [str(self.root), "publish"]
        stream = io.StringIO()
        # `main` with the same operand order `start` spawns, stopped after one
        # pass so it does not loop.
        with mock.patch.object(stack, "publish", return_value=0) as published:
            code = stack.main(["--root"] + argv, stream=stream, environ=self.environ)
        self.assertEqual(code, 0)
        self.assertTrue(published.called)

    def test_the_reversed_operand_order_is_refused_by_the_parser(self):
        with self.assertRaises(SystemExit):
            stack.main(["publish", "--root", str(self.root)], environ=self.environ)


class Status(Fixture):
    def test_absence_running_and_stale_are_distinguished(self):
        answer = stack.observe(self.root, environ=self.environ)
        self.assertEqual(answer["processes"]["manager"]["state"], "absent")
        record = self.record_for("manager", self.sleeper())
        self.assertEqual(stack.observe(self.root, environ=self.environ)["processes"]["manager"]["state"],
                         "running")
        record["started_at"] += 1
        stack.write_record(self.root, "manager", record)
        self.assertEqual(stack.observe(self.root, environ=self.environ)["processes"]["manager"]["state"],
                         "stale")

    def test_snapshot_freshness_and_absence_are_distinguished(self):
        answer = stack.observe(self.root, environ=self.environ)
        self.assertEqual(answer["snapshot"]["state"], "absent")
        now = time.time()
        self.publish_snapshot(observed=now)
        self.assertEqual(stack.observe(self.root, now=now, environ=self.environ)["snapshot"]["state"],
                         "fresh")
        later = now + stack.PUBLISH_SECONDS * 10
        self.assertEqual(stack.observe(self.root, now=later, environ=self.environ)["snapshot"]["state"],
                         "stale")

    def test_a_freshly_written_document_can_still_be_stalely_observed(self):
        """C4. `observed_at` is the MANAGER'S reading of the store; the file's
        mtime is when somebody wrote it. A document copied into place is new by
        one measure and old by the other, and the old one is the one that says
        whether this describes the world now."""
        now = time.time()
        self.publish_snapshot(observed=now - stack.PUBLISH_SECONDS * 100)
        answer = stack.observe(self.root, now=now, environ=self.environ)["snapshot"]
        self.assertEqual(answer["state"], "stale")
        self.assertGreater(answer["observed_age_seconds"], stack.PUBLISH_SECONDS * 3)
        self.assertLess(answer["published_age_seconds"], stack.PUBLISH_SECONDS * 3)

    def test_an_empty_configured_stack_is_a_valid_idle_state(self):
        self.publish_snapshot()
        answer = stack.observe(self.root, environ=self.environ)
        self.assertEqual(answer["jobs"], {"state": "observed", "count": 0, "canonical": True})
        self.assertEqual(answer["configuration"]["state"], "configured")

    def test_no_snapshot_is_not_an_empty_pipeline(self):
        """`absent` is nobody looked; `unreadable` is we looked and could not
        tell. Neither is zero Jobs."""
        self.assertEqual(stack.observe(self.root, environ=self.environ)["jobs"]["state"], "absent")
        stack.snapshot_path(self.root).write_text("{ torn")
        self.assertEqual(stack.observe(self.root, environ=self.environ)["jobs"]["state"], "unreadable")

    def test_a_document_of_another_schema_is_unreadable_not_empty(self):
        self.publish_snapshot(document={"schema": "baton.v12.job-status/4",
                                        "canonical": True, "jobs": [],
                                        "observed_at": self.instant()})
        answer = stack.observe(self.root, environ=self.environ)
        self.assertEqual(answer["jobs"]["state"], "unreadable")
        self.assertIn(stack.STATUS_SCHEMA, answer["snapshot"]["detail"])

    def test_the_pinned_status_schema_is_the_one_the_manager_writes(self):
        """The constant is copied so this launcher stays standard-library-only;
        this is what keeps the copy from drifting in silence."""
        from baton_v12.job_manager import documents
        self.assertEqual(stack.STATUS_SCHEMA, documents.STATUS_SCHEMA)

    def test_status_reports_an_unconfigured_stack_rather_than_idling(self):
        code, text = self.output(lambda s: stack.status(
            self.root, stream=s, environ={"HOME": self.temp.name}))
        self.assertEqual(code, 0)
        self.assertIn("unconfigured", text)


class Publication(Fixture):
    def test_the_snapshot_is_published_atomically(self):
        """A viewer must never read a half-written document, so publication is
        a rename over a sibling temporary rather than a write in place."""
        seen = []
        real_replace = os.replace

        def watched(source, target):
            seen.append((Path(source).name, Path(target).name))
            return real_replace(source, target)

        done = subprocess.CompletedProcess([], 0, stdout=json.dumps({"jobs": []}), stderr="")
        with mock.patch.object(os, "replace", watched):
            self.assertTrue(stack.publish_once(self.root, self.environ,
                                               runner=lambda *a, **k: done))
        self.assertEqual(seen, [("status.json.tmp", "status.json")])
        self.assertEqual(json.loads(stack.snapshot_path(self.root).read_bytes()), {"jobs": []})

    def test_a_failed_status_leaves_the_previous_snapshot_in_place(self):
        stack.snapshot_path(self.root).write_text(json.dumps({"jobs": ["previous"]}))
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="boom")
        self.assertFalse(stack.publish_once(self.root, self.environ,
                                            runner=lambda *a, **k: failed))
        self.assertEqual(json.loads(stack.snapshot_path(self.root).read_bytes()),
                         {"jobs": ["previous"]})

    def test_the_publisher_refreshes_until_it_is_asked_to_stop(self):
        ticks = []
        done = subprocess.CompletedProcess([], 0, stdout=json.dumps({"jobs": []}), stderr="")
        stack.publish(self.root, environ=self.environ, interval=0,
                      should_continue=lambda: len(ticks) < 3,
                      sleep=lambda _: None,
                      runner=lambda *a, **k: ticks.append(1) or done)
        self.assertEqual(len(ticks), 3)

    def test_the_publisher_observes_read_only(self):
        """It reads with the OBSERVING factory, never the serving one."""
        argv = []
        done = subprocess.CompletedProcess([], 0, stdout="{}", stderr="")
        stack.publish_once(self.root, self.environ,
                           runner=lambda command, **k: argv.extend(command) or done)
        self.assertIn("status", argv)
        self.assertIn("tools.stage_execution:observing_factory", argv)
        self.assertNotIn("tools.stage_execution:factory", argv)
        self.assertNotIn("serve", argv)


class Boundary(unittest.TestCase):
    """What this lifecycle must not reach."""

    def code(self):
        """The module's executable tokens: no comments, no string literals.

        Asserting over raw source would ban the module from EXPLAINING that it
        runs beside the older stack, which is the one thing its header most
        needs to say. Names and attributes are what reach a service; prose is
        not, and a test that cannot tell them apart forbids documentation.
        """
        import io
        import tokenize
        source = Path(stack.__file__).read_text()
        return " ".join(
            text for kind, text, _, _, _ in tokenize.generate_tokens(io.StringIO(source).readline)
            if kind not in (tokenize.COMMENT, tokenize.STRING))

    def test_no_executable_token_reaches_the_older_stack_or_version_control(self):
        for banned in BANNED_TOKENS:
            self.assertNotIn(banned, self.code(), banned)

    def test_the_manager_is_started_with_serve_and_never_submit(self):
        """The argv is where a command would actually be issued, so it is
        checked as a list rather than as a substring of the file."""
        import inspect
        started = inspect.getsource(stack.manager_argv)
        self.assertIn('"serve"', started)
        self.assertNotIn('"submit"', started)

    def test_no_store_is_defaulted_into_the_checkout(self):
        source = Path(stack.__file__).read_text()
        self.assertIn("REQUIRED = (", source)
        for name in stack.REQUIRED:
            self.assertNotIn(name + '", default=', source)



class TheChosenDiskRootIsNeverSilentlyReplaced(unittest.TestCase):
    """[I1]'s other half. Correcting the recipe alone would have left an
    operator's selection replaced one layer down."""

    def resolving(self, named):
        from tests.tools import test_stack as owning
        with mock.patch.dict(os.environ, {owning.DISK_ROOT_VARIABLE: named}):
            return owning._disk_root_outside_the_checkout()

    def test_a_root_that_cannot_be_written_is_named_rather_than_passed_over(self):
        with self.assertRaises(AssertionError) as raised:
            self.resolving("/no/such/selected/root")
        said = str(raised.exception)
        self.assertIn("/no/such/selected/root", said)
        self.assertIn("never silently passed over", said)

    def test_a_root_inside_the_checkout_is_named(self):
        from tools import stage_execution
        with self.assertRaises(AssertionError) as raised:
            self.resolving(os.path.join(stage_execution._checkout(), "v12"))
        self.assertIn("inside the checkout", str(raised.exception))

    def test_an_unset_or_blank_selection_still_falls_back(self):
        for blank in ("", "   "):
            with mock.patch.dict(os.environ, {DISK_ROOT_VARIABLE: blank}):
                self.assertTrue(os.path.isdir(_disk_root_outside_the_checkout()),
                                repr(blank))


class TheChildrenAreTheOneCommand(unittest.TestCase):
    """W183883: a deployed bundle cannot start `sys.executable -m tools.X`.

    In a frozen build `sys.executable` IS the application, so that dispatch
    would have started copies of the supervisor with operands it does not
    understand. `stack_command.bundled_argv` owns the one place the two forms
    differ, and both forms reach the same program.
    """

    def test_from_source_the_child_is_this_interpreter_and_the_module(self):
        from tools import stack_command

        argv = stack_command.bundled_argv("manager", ["--store", "/j"])
        self.assertEqual(argv[1:4], ["-m", "tools.stack_command", "manager"])
        self.assertEqual(argv[4:], ["--store", "/j"])

    def test_frozen_the_child_is_the_command_itself(self):
        from tools import stack_command

        with mock.patch.object(stack_command, "frozen", lambda: True), \
                mock.patch.object(stack_command, "executable",
                                  lambda: "/opt/distro/baton-v12-stack"):
            argv = stack_command.bundled_argv("manager", ["--store", "/j"])
        self.assertEqual(argv, ["/opt/distro/baton-v12-stack", "manager",
                                "--store", "/j"])
        # AND NOT AN INTERPRETER OPERAND ANYWHERE, which is the whole point.
        self.assertNotIn("-m", argv)

    def test_a_subcommand_this_command_does_not_serve_is_refused(self):
        from tools import stack_command

        with self.assertRaises(ValueError):
            stack_command.bundled_argv("nonsense", [])

    def test_every_child_the_supervisor_starts_is_a_real_subcommand(self):
        from tools import stack_command

        for name in stack_command.CHILDREN:
            self.assertIn(name, stack_command.COMMANDS, name)


class WhatTheRepositoryIS(Fixture):
    """W183883 review 2026-09-16T14-06-35Z: an installed deployment had a
    `repo/` and a configuration that never mentioned it, and nothing could say
    what the owner's own integration target was without running a repository
    tool. This READS, and runs nothing.

    The fixtures are ordinary files -- a layout, a HEAD, a reference -- because
    what is under test is what this reports about a directory, not a repository
    tool's behaviour. Preparing a real one is the owner's, and this Work
    performs no version-control mutation of any kind.
    """

    def instance_at(self, **configured):
        from tools import instance as instances

        destination = Path(self.temp.name) / "deployment"
        places = instances.layout(str(destination))
        for name in ("stores", "repository", "logs", "state"):
            Path(places[name]).mkdir(parents=True, exist_ok=True)
        Path(places["deployment"]).write_text(json.dumps(
            dict({"schema": "baton.v12.stage-execution-deployment/1"},
                 **configured)))
        return {"destination": str(destination),
                "deployment": places["deployment"]}, places

    def reported(self, **configured):
        out = io.StringIO()
        document, places = self.instance_at(**configured)
        code = stack.repository(document, stream=out)
        return code, out.getvalue(), places

    def layout_at(self, root, *, head="ref: refs/heads/main",
                  commit="a" * 40, bare=True):
        root = Path(root)
        base = root if bare else root / ".git"
        (base / "objects").mkdir(parents=True, exist_ok=True)
        (base / "refs" / "heads").mkdir(parents=True, exist_ok=True)
        (base / "HEAD").write_text(head + "\n")
        if commit is not None and head.startswith("ref: "):
            (base / head[5:].strip()).write_text(commit + "\n")
        return root

    def test_an_empty_workspace_is_said_to_be_empty(self):
        code, said, places = self.reported(
            integration_workspace=None)
        self.assertEqual(code, 0)
        self.assertIn("not configured", said)
        self.assertIn(places["repository"], said)

    def test_a_workspace_inside_the_instance_is_reported_as_inside(self):
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_workspace": places["repository"]}))
        out = io.StringIO()
        self.assertEqual(stack.repository(document, stream=out), 0)
        said = out.getvalue()
        self.assertIn("inside this instance", said)
        self.assertIn("empty", said)

    def test_a_target_OUTSIDE_the_instance_is_said_so_rather_than_refused(self):
        """The target is the owner's repository. It is normal for it to be
        elsewhere, and this reports rather than judges."""
        elsewhere = self.layout_at(Path(self.temp.name) / "their-repository")
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_target": str(elsewhere),
             "integration_target_reference": "refs/heads/main"}))
        out = io.StringIO()
        self.assertEqual(stack.repository(document, stream=out), 0)
        said = out.getvalue()
        self.assertIn("outside this instance", said)
        self.assertIn("a repository (bare)", said)
        self.assertIn("HEAD ref: refs/heads/main", said)
        self.assertIn("a" * 40, said)
        self.assertIn("refs/heads/main", said)

    def test_a_WORK_TREE_is_read_through_its_own_marker(self):
        tree = self.layout_at(Path(self.temp.name) / "work-tree", bare=False)
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_target": str(tree)}))
        out = io.StringIO()
        stack.repository(document, stream=out)
        self.assertIn("a repository (work tree)", out.getvalue())

    def test_a_directory_that_is_not_a_repository_is_said_so(self):
        plain = Path(self.temp.name) / "just-a-directory"
        plain.mkdir()
        (plain / "README").write_text("nothing here")
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_target": str(plain)}))
        out = io.StringIO()
        stack.repository(document, stream=out)
        self.assertIn("no repository layout", out.getvalue())

    def test_an_absent_target_is_named_as_absent(self):
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_target": str(Path(self.temp.name) / "never-made")}))
        out = io.StringIO()
        stack.repository(document, stream=out)
        self.assertIn("ABSENT", out.getvalue())

    def test_the_declared_bases_are_reported_from_the_bindings(self):
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/2",
             "job_bindings": [{"job_id": "job-a", "line_declared_base": "b" * 40},
                              {"job_id": "job-b", "line_declared_base": "c" * 40}]}))
        out = io.StringIO()
        stack.repository(document, stream=out)
        said = out.getvalue()
        self.assertIn("b" * 40, said)
        self.assertIn("c" * 40, said)

    def test_a_workspace_that_is_not_a_repository_says_what_that_costs(self):
        """`reconciliation._prove_isolation` resolves the workspace's own
        repository identity before anything is written, so an empty directory
        is refused THEN -- when a result is ready to import. Saying it here is
        the difference between a deployment you can prepare and one you
        discover."""
        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_workspace": places["repository"]}))
        out = io.StringIO()
        stack.repository(document, stream=out)
        said = out.getvalue()
        self.assertIn("not a repository yet", said)
        self.assertIn("isolation is proved before anything is written", said)

    def test_a_workspace_that_IS_a_repository_says_nothing_of_the_kind(self):
        document, places = self.instance_at()
        self.layout_at(places["repository"], bare=False)
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_workspace": places["repository"]}))
        out = io.StringIO()
        stack.repository(document, stream=out)
        said = out.getvalue()
        self.assertIn("a repository (work tree)", said)
        self.assertNotIn("not a repository yet", said)

    def test_a_deployment_document_it_cannot_read_is_refused(self):
        document, places = self.instance_at()
        Path(places["deployment"]).write_text("{ not a document")
        out = io.StringIO()
        self.assertEqual(stack.repository(document, stream=out), 2)
        self.assertIn("could not be read", out.getvalue())

    def test_the_verb_needs_an_instance(self):
        out = io.StringIO()
        code = stack.main(["--root", str(self.root), "repository"], stream=out,
                          environ=dict(self.environ))
        self.assertEqual(code, 2)
        self.assertIn("needs --instance", out.getvalue())

    def test_nothing_it_reports_is_a_command_it_ran(self):
        """The whole point: this Work performs no version-control mutation,
        and a report that shelled out would be one."""
        import subprocess as watched

        document, places = self.instance_at()
        Path(places["deployment"]).write_text(json.dumps(
            {"schema": "baton.v12.stage-execution-deployment/1",
             "integration_target": str(self.layout_at(
                 Path(self.temp.name) / "their-repository"))}))
        with mock.patch.object(watched, "run",
                               lambda *a, **k: self.fail("it ran something")), \
                mock.patch.object(watched, "Popen",
                                  lambda *a, **k: self.fail("it started something")):
            self.assertEqual(stack.repository(document, stream=io.StringIO()), 0)


class TheInstalledMonitor(Fixture):
    """W183883: an installed instance must be watchable without this checkout.

    The recipe used to rebuild the snapshot path out of an environment variable
    -- a second place for what `snapshot_path` already owns, and one that could
    not answer for an instance at all.
    """

    def watching(self, **named):
        seen = {}

        def viewing(argv, *, stream=None):
            seen["argv"] = list(argv)
            return 0

        from tools import job_viewer

        with mock.patch.object(job_viewer, "main", viewing):
            code = stack.monitor(self.root, stream=io.StringIO(),
                                 **dict({"interval": 5.0, "ticks": 3}, **named))
        return code, seen.get("argv")

    def test_it_watches_THIS_root_s_own_snapshot(self):
        stack.snapshot_path(self.root).write_text("{}")
        code, argv = self.watching()
        self.assertEqual(code, 0)
        self.assertEqual(argv[:2], ["--status", str(stack.snapshot_path(self.root))])
        self.assertIn("--interval", argv)
        self.assertEqual(argv[argv.index("--ticks") + 1], "3")

    def test_the_interval_reaches_the_viewer(self):
        stack.snapshot_path(self.root).write_text("{}")
        _code, argv = self.watching(interval=0.25)
        self.assertEqual(argv[argv.index("--interval") + 1], "0.25")

    def test_a_stack_that_has_published_nothing_is_said_so_rather_than_watched(self):
        with self.assertRaises(stack.StackRefusal) as raised:
            self.watching()
        said = str(raised.exception)
        self.assertIn(str(stack.snapshot_path(self.root)), said)
        self.assertIn("status", said)

    def test_the_verb_reaches_it_through_main(self):
        stack.snapshot_path(self.root).write_text("{}")
        seen = {}
        with mock.patch.object(stack, "monitor",
                               lambda root, **named: seen.update(
                                   dict(named, root=root)) or 0):
            code = stack.main(["--root", str(self.root), "monitor",
                               "--interval", "2", "--ticks", "7"],
                              stream=io.StringIO(), environ=dict(self.environ))
        self.assertEqual(code, 0)
        self.assertEqual(seen["root"], Path(str(self.root)))
        self.assertEqual((seen["interval"], seen["ticks"]), (2.0, 7))

    def test_a_refusal_is_said_in_the_command_s_own_voice(self):
        out = io.StringIO()
        code = stack.main(["--root", str(self.root), "monitor"], stream=out,
                          environ=dict(self.environ))
        self.assertEqual(code, 2)
        self.assertIn("refused:", out.getvalue())

    def test_the_bundled_command_puts_a_verb_s_options_AFTER_the_verb(self):
        """`--instance` is the command's; `--interval` is the monitor's, and
        argparse reads a subcommand's options only after the subcommand. An
        appended verb would have made `monitor --interval 5` unparseable."""
        from tools import stack_command

        seen = {}
        with mock.patch.object(stack, "main",
                               lambda argv: seen.update(argv=list(argv)) or 0):
            stack_command.COMMANDS["monitor"](
                ["--instance", "/srv/d/instance.json", "--interval", "2"])
        self.assertEqual(seen["argv"],
                         ["--instance", "/srv/d/instance.json", "monitor",
                          "--interval", "2"])

    def test_the_older_verbs_are_dispatched_exactly_as_before(self):
        from tools import stack_command

        for verb in ("start", "stop", "status", "publish"):
            seen = {}
            with mock.patch.object(stack, "main",
                                   lambda argv: seen.update(argv=list(argv)) or 0):
                stack_command.COMMANDS[verb](["--instance", "/srv/d/i.json"])
            self.assertEqual(seen["argv"], ["--instance", "/srv/d/i.json", verb],
                             verb)


class Admission(Fixture):
    """R1. Two starts must not both pass the spawn boundary.

    The reviewer's counterexample held a deterministic barrier at that boundary
    and got two successful starts, four live processes and two ownership
    records -- so the two the second start overwrote were processes no later
    `stop` could ever find. Repeating a start SEQUENTIALLY proved nothing about
    this, which is why the accepted case did not catch it.
    """

    def impatient(self):
        """A monotonic clock that has already passed any bounded wait."""
        first = iter([0.0])
        return lambda: next(first, 1e9)

    def barrier(self, spawned, entered, allowed):
        def blocking(root, name, argv, environ, extra=None):
            spawned.append(name)
            entered.set()
            if not allowed.wait(20):
                raise AssertionError("the barrier was never released")
            record = self.record_for(name, self.sleeper(), **(extra or {}))
            if name == stack.MANAGER:
                self.acknowledge(argv[argv.index("--incarnation") + 1])
            if name == stack.PUBLISHER:
                self.publish_snapshot()
            return record
        return blocking

    def held_open(self, spawned, entered, allowed):
        """A start stopped INSIDE its ownership transition, on its own thread."""
        answered = {}

        def run():
            try:
                with open(os.devnull, "w") as quiet:
                    answered["code"] = stack.start(self.root, self.environ, stream=quiet)
            except BaseException as failure:                # noqa: BLE001
                answered["failure"] = failure

        patched = mock.patch.object(stack, "_spawn",
                                    self.barrier(spawned, entered, allowed))
        patched.start()
        self.addCleanup(patched.stop)
        worker = threading.Thread(target=run)
        worker.start()
        self.addCleanup(worker.join)
        self.assertTrue(entered.wait(20), "the first start never reached its spawn")
        return answered, worker

    def test_a_second_start_cannot_enter_while_the_first_holds_admission(self):
        spawned, entered, allowed = [], threading.Event(), threading.Event()
        answered, worker = self.held_open(spawned, entered, allowed)
        try:
            with self.assertRaises(stack.StackRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.start(self.root, self.environ, stream=quiet,
                                monotonic=self.impatient())
            self.assertIn("lifecycle operation holds", str(raised.exception))
        finally:
            allowed.set()
            worker.join(20)
        self.assertEqual(answered.get("code"), 0, answered.get("failure"))
        # EXACTLY ONE STACK: two spawns, two records, and both of them live.
        self.assertEqual(sorted(spawned), sorted(stack.PROCESSES))
        for name in stack.PROCESSES:
            self.assertTrue(stack.alive(stack.read_record(self.root, name)), name)

    def test_a_stop_cannot_interleave_with_a_start(self):
        """A stop that ran mid-start would clear a record for a process the
        start was at that moment publishing, which is the same orphan."""
        spawned, entered, allowed = [], threading.Event(), threading.Event()
        answered, worker = self.held_open(spawned, entered, allowed)
        try:
            with self.assertRaises(stack.StackRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.stop(self.root, stream=quiet, monotonic=self.impatient())
            self.assertIn("lifecycle operation holds", str(raised.exception))
        finally:
            allowed.set()
            worker.join(20)
        self.assertEqual(answered.get("code"), 0, answered.get("failure"))

    def test_admission_is_released_even_when_its_holder_is_killed(self):
        """An flock rather than a lock FILE, and this is the difference: a
        claim written to disk outlives whatever wrote it, and an operator who
        killed a start would have to know about a stale one."""
        holder = subprocess.Popen(
            [sys.executable, "-c",
             "import fcntl, os, sys, time\n"
             "handle = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)\n"
             "fcntl.flock(handle, fcntl.LOCK_EX)\n"
             "sys.stdout.write('held\\n'); sys.stdout.flush()\n"
             "time.sleep(300)\n", str(stack.lock_path(self.root))],
            stdout=subprocess.PIPE, text=True, start_new_session=True)
        self.owned.append(holder)
        self.addCleanup(holder.stdout.close)
        self.assertEqual(holder.stdout.readline().strip(), "held")
        with self.assertRaises(stack.StackRefusal):
            with stack.admission(self.root, monotonic=self.impatient()):
                pass
        holder.kill()
        holder.wait(timeout=5)
        with stack.admission(self.root, wait=5):
            pass

    def test_a_spawn_that_cannot_be_recorded_leaves_no_orphan(self):
        """R1's last clause. A process admitted but never recorded is owned by
        nobody: no status reports it and no stop can reach it."""
        seen = {}

        def failing(root, name, record):
            seen.update(record)
            raise OSError("the record could not be written")

        with mock.patch.object(stack, "write_record", failing):
            with self.assertRaises(OSError):
                stack._spawn(self.root, "manager",
                             [sys.executable, "-c", "import time; time.sleep(300)"],
                             self.environ)
        self.assertEqual(stack.ownership({"schema": stack.SCHEMA, "pid": seen["pid"],
                                          "started_at": seen["started_at"]}),
                         stack.GONE)
        self.assertIsNone(stack.read_record(self.root, "manager"))


class UnknownOwnership(Fixture):
    """R2. `we cannot tell` is not `nobody is there`.

    The reviewer kept a live original, supplied an unreadable manager record,
    and watched `start` replace it. `read_record` already made the
    distinction; `start` then fed it straight into a liveness test that
    answered False, and a False liveness answer licensed a replacement.
    """

    def test_an_unreadable_record_is_unknown_rather_than_gone(self):
        self.assertEqual(stack.ownership({"unreadable": True}), stack.UNKNOWN)

    def test_a_record_whose_identity_cannot_be_read_is_unknown(self):
        for broken in ({"pid": "one", "started_at": 1}, {"pid": 1},
                       {"pid": 0, "started_at": 1}, {"pid": -1, "started_at": 1}):
            self.assertEqual(stack.ownership(dict(broken, schema=stack.SCHEMA)),
                             stack.UNKNOWN, broken)

    def test_the_proc_read_itself_tells_denial_from_absence(self):
        """The mapping under the substitution the case below makes: a `/proc`
        this process may not read is NOT the kernel saying nobody is there."""
        import builtins
        real = builtins.open

        def denied(name, *rest, **named):
            if type(name) is str and name.startswith("/proc/"):
                raise PermissionError(13, "denied")
            return real(name, *rest, **named)

        with mock.patch.object(builtins, "open", denied):
            self.assertEqual(stack._proc(os.getpid()), ("unknown", None))
        # A pid above any pid_max is a POSITIVE absence.
        self.assertEqual(stack._proc(2 ** 30)[0], "absent")
        self.assertEqual(stack._proc(os.getpid())[0], "R")

    def test_a_denied_process_read_is_unknown_rather_than_absent(self):
        record = self.record_for("manager", self.sleeper())
        real = stack._proc

        def denied(pid):
            return ("unknown", None) if pid == record["pid"] else real(pid)

        with mock.patch.object(stack, "_proc", denied):
            self.assertEqual(stack.ownership(record), stack.UNKNOWN)

    def test_every_positive_absence_is_still_gone(self):
        """The distinction only matters if `gone` is still reachable."""
        child = self.sleeper()
        record = self.record_for("manager", child)
        child.kill()
        child.wait(timeout=5)
        self.assertEqual(stack.ownership(record), stack.GONE)
        reused = dict(record, started_at=record["started_at"] + 1)
        self.assertEqual(stack.ownership(reused), stack.GONE)

    def test_a_terminated_but_unreaped_process_is_gone(self):
        """A zombie keeps its /proc entry AND its original start time, so an
        identity match alone reports a corpse as running."""
        child = subprocess.Popen([sys.executable, "-c", ""],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(child.wait)
        deadline = time.monotonic() + 10
        while stack._proc(child.pid)[0] != "Z" and time.monotonic() < deadline:
            time.sleep(0.01)
        state, started = stack._proc(child.pid)
        self.assertEqual(state, "Z")
        self.assertEqual(stack.ownership({"schema": stack.SCHEMA, "pid": child.pid,
                                          "started_at": started}), stack.GONE)

    def test_start_refuses_to_replace_an_owner_it_cannot_establish(self):
        original = self.sleeper()
        self.record_for("manager", original)
        (self.root / "manager.json").write_text("{ not json")
        with mock.patch.object(stack, "_spawn",
                               side_effect=AssertionError("replaced an unknown owner")), \
                mock.patch.object(os, "kill",
                                  side_effect=AssertionError("signalled an unknown owner")):
            code, text = self.output(lambda s: stack.main(
                ["--root", str(self.root), "start"], stream=s, environ=self.environ))
        self.assertEqual(code, 2)
        self.assertIn("cannot be established", text)
        # THE ORIGINAL IS STILL RUNNING, which is the whole point.
        self.assertIsNotNone(stack.started_at(original.pid))
        # ITS EVIDENCE IS RETAINED, and the recovery is named rather than taken.
        self.assertEqual(stack.read_record(self.root, "manager"), {"unreadable": True})
        self.assertIn(str(self.root / "manager.json"), text)
        self.assertIn(str(stack.log_path(self.root, "manager")), text)

    def test_a_denied_process_read_also_stops_a_start(self):
        record = self.record_for("manager", self.sleeper())
        real = stack._proc

        def denied(pid):
            return ("unknown", None) if pid == record["pid"] else real(pid)

        with mock.patch.object(stack, "_proc", denied), \
                mock.patch.object(stack, "_spawn",
                                  side_effect=AssertionError("started over an unknown owner")):
            code, text = self.output(lambda s: stack.main(
                ["--root", str(self.root), "start"], stream=s, environ=self.environ))
        self.assertEqual(code, 2)
        self.assertIn("cannot be established", text)

    def test_stop_retains_an_unknown_record_and_reports_failure(self):
        (self.root / "manager.json").write_text("{ not json")
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 1)
        self.assertIn("unresolved ownership", text)
        self.assertIn("is NOT stopped", text)
        self.assertEqual(stack.read_record(self.root, "manager"), {"unreadable": True})


class Readiness(Fixture):
    """R3. The documented child has to be able to import, and `start` has to
    find out before it says the stack is up."""

    def test_the_child_environment_carries_this_distributions_package_path(self):
        prepared = stack.child_environment({"PYTHONPATH": "/operator/own"})
        parts = prepared["PYTHONPATH"].split(os.pathsep)
        self.assertEqual(parts[0], str(stack.PACKAGE_PATH))
        self.assertEqual(parts[1], str(stack.DISTRIBUTION))
        # The operator's own path is KEPT, after ours, rather than discarded.
        self.assertIn("/operator/own", parts)
        for part in parts:
            self.assertTrue(os.path.isabs(part), part)

    def test_an_empty_or_absent_operator_path_adds_no_empty_entry(self):
        for given in ({}, {"PYTHONPATH": ""}):
            parts = stack.child_environment(given)["PYTHONPATH"].split(os.pathsep)
            self.assertEqual(parts, [str(stack.PACKAGE_PATH), str(stack.DISTRIBUTION)])

    def test_the_documented_child_can_actually_import_its_package(self):
        """The EXACT failure the review reproduced: `python3 -m
        tools.job_manager` from `v12/python` died on `ModuleNotFoundError: No
        module named 'baton_v12'`, and `start` reported it started anyway."""
        done = subprocess.run(
            [sys.executable, "-m", "tools.job_manager", "--help"],
            cwd=str(stack.DISTRIBUTION),
            env=stack.child_environment({"PATH": os.environ.get("PATH", "")}),
            capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("ModuleNotFoundError", done.stderr)

    def test_the_monitors_child_can_import_the_same_package(self):
        """`monitor` was broken for the identical reason: `job_viewer` imports
        `baton_v12.job_manager`, and the recipe ran a bare python3."""
        done = subprocess.run(
            [sys.executable, "-m", "tools.job_viewer", "--help"],
            cwd=str(stack.DISTRIBUTION),
            env=stack.child_environment({"PATH": os.environ.get("PATH", "")}),
            capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)

    def recipe_bodies(self):
        """Each recipe's own INDENTED body, keyed by the recipe's name.

        A column-0 line that is not a header ends the body: `just` recipe
        bodies are the indented block, and a parser that let file-level
        comments fall into the preceding recipe would answer prose when asked
        what a recipe runs -- which is how this check first passed while a
        comment three recipes away supplied the word it was looking for.
        """
        bodies, name = {}, None
        for line in (_DISTRIBUTION.parent / "justfile").read_text().splitlines():
            if not line.strip():
                continue
            if line[:1] in ("\t", " "):
                if name is not None:
                    bodies[name].append(line)
                continue
            if line.startswith("#") or ":=" in line or ":" not in line:
                name = None
                continue
            name = line.split(":")[0].split()[0]
            bodies[name] = []
        return {name: "\n".join(lines) for name, lines in bodies.items()}

    def test_every_recipe_that_runs_a_child_names_the_runtime_prerequisite(self):
        bodies = self.recipe_bodies()
        for wanted in ("start", "stop", "status", "monitor"):
            self.assertIn(wanted, bodies)
        for name, lines in bodies.items():
            body = "\n".join(lines)
            if "python3 -m tools." not in body:
                continue
            self.assertIn("PYTHONPATH", body, name)

    def test_start_fails_with_the_childs_own_reason_when_it_exits_at_once(self):
        def exiting(message):
            return [sys.executable, "-c",
                    "import sys; sys.stderr.write(%r); raise SystemExit(1)"
                    % (message + "\n")]

        # DISTINCT MESSAGES. If the liveness half of the gate were lost, the
        # refusal would quote the publisher's log instead, and one shared
        # message would have let that pass.
        with mock.patch.object(stack, "manager_argv",
                               lambda settings, named: exiting("No module named baton_v12")), \
                mock.patch.object(stack, "publisher_argv",
                                  lambda root: exiting("the publisher said something else")):
            code, text = self.output(lambda s: stack.main(
                ["--root", str(self.root), "start"], stream=s, environ=self.environ))
        self.assertEqual(code, 2)
        self.assertIn("No module named baton_v12", text)
        self.assertNotIn("ready:", text)
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name))

    def test_start_fails_when_nothing_is_ever_published(self):
        """Both processes alive is not acknowledgement. Only a snapshot is:
        publishing means `job_manager status --observe` read the configured
        stores through the real deployment document."""
        records = []
        with mock.patch.object(stack, "_spawn", self.fake_spawn(publish=False)):
            with self.assertRaises(stack.StackRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.start(self.root, self.environ, stream=quiet,
                                ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("no valid, freshly observed status snapshot was published",
                      str(raised.exception))
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name), name)
            records.append(name)
        self.assertEqual(records, list(stack.PROCESSES))

    def test_a_previous_runs_snapshot_is_not_this_starts_acknowledgement(self):
        self.publish_snapshot()
        with mock.patch.object(stack, "_spawn", self.fake_spawn(publish=False)):
            with self.assertRaises(stack.StackRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.start(self.root, self.environ, stream=quiet,
                                ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("no valid, freshly observed status snapshot was published",
                      str(raised.exception))

    def test_an_unwind_that_cannot_take_a_process_back_retains_its_record(self):
        """TRUTHFUL OWNERSHIP DURING CLEANUP: a record is cleared only for a
        process the unwind positively stopped."""
        import io
        # `_signal` is made to claim success while the process stays up, which
        # is the shape of a stop this unwind cannot complete.
        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn", self.fake_spawn(publish=False)), \
                mock.patch.object(stack, "_signal", return_value=True):
            with self.assertRaises(stack.StackRefusal):
                stack.start(self.root, self.environ, stream=stream,
                            ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("record retained", stream.getvalue())
        for name in stack.PROCESSES:
            self.assertIsNotNone(stack.read_record(self.root, name), name)


class RuntimeBoundary(Fixture):
    """R4. Stopping a supervisor is not evidence that execution finished."""

    def test_no_snapshot_is_unknown_rather_than_nothing_running(self):
        answer = stack.runtime_boundary(self.root)
        self.assertEqual(answer["state"], stack.UNKNOWN)
        self.assertIn("no snapshot", answer["detail"])

    def test_a_stale_snapshot_is_unknown_rather_than_its_own_contents(self):
        """A stale document describes a world the manager has moved on from."""
        stack.snapshot_path(self.root).write_text(json.dumps({"jobs": []}))
        stale = time.time() - stack.PUBLISH_SECONDS * 100
        os.utime(stack.snapshot_path(self.root), (stale, stale))
        self.assertEqual(stack.runtime_boundary(self.root)["state"], stack.UNKNOWN)

    def test_a_torn_snapshot_is_unknown_rather_than_zero(self):
        place = stack.snapshot_path(self.root)
        place.write_text("{ torn")
        soon = time.time() + 1
        os.utime(place, (soon, soon))
        self.assertEqual(stack.runtime_boundary(self.root)["state"], stack.UNKNOWN)

    def test_open_episodes_and_recorded_runtimes_are_counted(self):
        self.publish_snapshot(jobs=[{"stages": [
            {"episodes": [{"ended_state": None}, {"ended_state": "ended"}],
             "runtime": {"state": "running"}},
            {"episodes": [{"ended_state": "ended"}], "runtime": None}]}])
        answer = stack.runtime_boundary(self.root)
        self.assertEqual(answer["state"], "observed")
        self.assertEqual(answer["open_episodes"], 1)
        self.assertEqual(answer["recorded_runtimes"], 1)

    def test_stop_reports_what_it_did_not_resolve(self):
        self.start_both()
        self.publish_snapshot(jobs=[{"stages": [
            {"episodes": [{"ended_state": None}], "runtime": None}]}])
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        self.assertIn("1 open episode", text)
        self.assertIn("does not stop a runtime", text)

    def test_stop_without_a_snapshot_says_unknown_rather_than_none(self):
        self.start_both()
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        self.assertIn("runtime   unknown", text)
        self.assertIn("NOT resolved here", text)

    def test_status_carries_the_same_boundary(self):
        code, text = self.output(lambda s: stack.status(
            self.root, stream=s, environ=self.environ))
        self.assertEqual(code, 0)
        self.assertIn("runtime   unknown", text)




class VisibilityLostDuringCleanup(Fixture):
    """C1. `unknown` AFTER signalling is not completion.

    The accepted cases covered ownership that was unknown when `start` first
    looked. Both cleanup paths then waited for LIVE and cleared the record for
    every other answer -- so a process whose `/proc` stopped answering after it
    was signalled was announced `stopped`, its record deleted, and `stop`
    returned 0, while the process was still running.

    The transition is simulated at the ordinary process-inspection boundary.
    Nothing here claims a real permission change occurred on this host; what is
    under test is what this code does when the answer stops arriving.
    """

    def goes_blind(self, pid):
        """A `_proc` that answers for this pid until a signal, then does not."""
        signalled = []
        real = stack._proc

        def looking(asked):
            if asked == pid and signalled:
                return "unknown", None
            return real(asked)

        def signalling(record, number):
            signalled.append(number)
            return True

        return looking, signalling, signalled

    def test_stop_does_not_announce_a_process_it_can_no_longer_see(self):
        child = self.sleeper()
        record = self.record_for("manager", child)
        looking, signalling, signalled = self.goes_blind(child.pid)
        with mock.patch.object(stack, "_proc", looking), \
                mock.patch.object(stack, "_signal", signalling):
            code, text = self.output(lambda s: stack.stop(
                self.root, stream=s, grace=0.05, sleep=lambda _: None))
        self.assertTrue(signalled)
        self.assertEqual(code, 1)
        self.assertIn("unresolved", text)
        self.assertNotIn("stopped: manager", text)
        # THE RECORD STAYS, and the process is in fact still running.
        self.assertIsNotNone(stack.read_record(self.root, "manager"))
        self.assertIsNotNone(stack.started_at(child.pid))

    def test_a_failed_start_does_not_take_back_what_it_can_no_longer_see(self):
        import io

        holding = []

        def fake(root, name, argv, environ, extra=None):
            record = self.record_for(name, self.sleeper(), **(extra or {}))
            holding.append(record)
            return record

        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn", fake):
            looking, signalling, _ = self.goes_blind(0)
            real = stack._proc

            def blind(asked):
                if any(one["pid"] == asked for one in holding) and blind.lost:
                    return "unknown", None
                return real(asked)
            blind.lost = False

            def signalling_all(record, number):
                blind.lost = True
                return True

            with mock.patch.object(stack, "_proc", blind), \
                    mock.patch.object(stack, "_signal", signalling_all):
                with self.assertRaises(stack.StackRefusal):
                    stack.start(self.root, self.environ, stream=stream,
                                ready_seconds=0.2, sleep=lambda _: None)
        self.assertIn("record retained", stream.getvalue())
        for name in stack.PROCESSES:
            self.assertIsNotNone(stack.read_record(self.root, name), name)

    def test_a_positively_gone_process_is_still_cleared_and_announced(self):
        """The distinction only matters if the ordinary path still works."""
        records = self.start_both()
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        for record in records:
            self.assertIsNone(stack.read_record(self.root, record["name"]))
        self.assertEqual(text.count("stopped: "), len(stack.PROCESSES))


class EveryFailedAdmissionUnwinds(Fixture):
    """C2. `_spawn` raises more than `StackRefusal`.

    Opening the log, `Popen` and writing the record all raise `OSError`, and
    `_start_admitted` caught only refusals -- so a publisher that failed after
    the manager had been admitted escaped with the manager running and
    recorded. That is an unresolved half-start, and the accepted
    record-write case covered only the FIRST process.
    """

    def failing_second(self, failure):
        ordinary = self.fake_spawn()

        def spawning(root, name, argv, environ, extra=None):
            if name == stack.PUBLISHER:
                raise failure
            return ordinary(root, name, argv, environ, extra)
        return spawning

    def start_expecting(self, failure):
        import io

        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn", self.failing_second(failure)):
            with self.assertRaises(type(failure)) as raised:
                stack.start(self.root, self.environ, stream=stream,
                            ready_seconds=0.3, sleep=lambda _: None)
        return raised.exception, stream.getvalue()

    def test_a_publisher_spawn_failure_takes_the_manager_back(self):
        failure, _text = self.start_expecting(OSError("injected publisher spawn failure"))
        # THE ORIGINAL ERROR IS PRESERVED, not replaced by a cleanup refusal.
        self.assertIn("injected publisher spawn failure", str(failure))
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name), name)
        for child in self.owned:
            self.assertIsNotNone(child.poll(), "an admitted process was left running")

    def test_a_publisher_record_failure_takes_the_manager_back_too(self):
        failure, _text = self.start_expecting(
            PermissionError("the publisher record could not be written"))
        self.assertIn("record could not be written", str(failure))
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name), name)

    def test_cleanup_after_an_ordinary_failure_still_keeps_unknown_ownership(self):
        """C1 and C2 meet here: interruption cleanup must not erase what it
        cannot establish."""
        import io

        ordinary = self.fake_spawn()
        holding = []

        def spawning(root, name, argv, environ, extra=None):
            if name == stack.PUBLISHER:
                raise OSError("injected publisher spawn failure")
            record = ordinary(root, name, argv, environ, extra)
            holding.append(record)
            return record

        real = stack._proc

        def blind(asked):
            if any(one["pid"] == asked for one in holding) and blind.lost:
                return "unknown", None
            return real(asked)
        blind.lost = False

        def signalling(record, number):
            blind.lost = True
            return True

        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn", spawning), \
                mock.patch.object(stack, "_proc", blind), \
                mock.patch.object(stack, "_signal", signalling):
            with self.assertRaises(OSError):
                stack.start(self.root, self.environ, stream=stream,
                            ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("record retained", stream.getvalue())
        self.assertIsNotNone(stack.read_record(self.root, stack.MANAGER))


class ServingAcknowledgement(Fixture):
    """C3. A published snapshot is evidence about the OBSERVER.

    `observation_from` builds a reader out of a held configuration;
    `operations_from` opens the Authority, mints and authorizes five sessions,
    runs three worker preflights, opens the integration store and activates the
    pool. So a manager that never initialized -- delayed, or stopped before it
    got there -- passed the old gate while its publisher read an empty store
    perfectly well.
    """

    def test_the_observer_composes_no_deployment(self):
        """The static distinction the whole finding rests on, asserted against
        the functions rather than against prose about them."""
        from tools import stage_execution

        observing = stage_execution.observation_from.__code__.co_names
        serving = stage_execution.operations_from.__code__.co_names
        self.assertIn("held_configuration", observing)
        for act in ("worker_preflight", "_minted", "Authority", "activate_pool"):
            self.assertNotIn(act, observing, act)
            self.assertIn(act, serving, act)

    def test_a_manager_that_never_acknowledges_fails_the_start(self):
        """The reviewer's counterexample: the publisher publishes perfectly
        well, and that says nothing about the serving process."""
        import io

        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn",
                               self.fake_spawn(acknowledge=False, publish=True)):
            with self.assertRaises(stack.StackRefusal) as raised:
                stack.start(self.root, self.environ, stream=stream,
                            ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("never acknowledged", str(raised.exception))
        self.assertIn("the observer composes no deployment", str(raised.exception))
        self.assertNotIn("ready:", stream.getvalue())
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name), name)

    def test_a_previous_runs_acknowledgement_does_not_answer_for_this_start(self):
        """Stale acknowledgement across restart. The line is in the log; it was
        written before this start opened it, and it names another
        incarnation."""
        self.acknowledge("v12-stack-1-1")
        with mock.patch.object(stack, "_spawn",
                               self.fake_spawn(acknowledge=False, publish=True)):
            with self.assertRaises(stack.StackRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.start(self.root, self.environ, stream=quiet,
                                ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("never acknowledged", str(raised.exception))

    def test_an_acknowledgement_naming_another_incarnation_is_not_this_ones(self):
        def fake(root, name, argv, environ, extra=None):
            record = self.record_for(name, self.sleeper(), **(extra or {}))
            if name == stack.MANAGER:
                # Written AFTER this start opened the log, so only the
                # incarnation tells the two apart.
                self.acknowledge("somebody-elses-manager")
            if name == stack.PUBLISHER:
                self.publish_snapshot()
            return record

        with mock.patch.object(stack, "_spawn", fake):
            with self.assertRaises(stack.StackRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.start(self.root, self.environ, stream=quiet,
                                ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("never acknowledged", str(raised.exception))

    def test_an_acknowledgement_written_before_this_start_does_not_count(self):
        """BOTH HALVES ARE LOAD-BEARING, and a reversal probe is how I found
        out that only one of them was held by a check.

        The incarnation tells two managers apart. The offset tells two runs of
        ONE incarnation apart -- which is what a repeated incarnation would
        produce, and nothing in `acknowledged` gets to assume that
        `incarnation()` stays unique.
        """
        named = "v12-stack-repeated"
        self.acknowledge(named)
        place = stack.log_path(self.root, "manager")
        record = {"log": str(place), "log_from": place.stat().st_size,
                  "incarnation": named}
        self.assertFalse(stack.acknowledged(record))
        self.acknowledge(named)
        self.assertTrue(stack.acknowledged(record))

    def test_every_manager_start_is_given_a_fresh_incarnation(self):
        settings = stack.configured(self.environ)
        one = stack.manager_argv(settings, stack.incarnation())
        other = stack.manager_argv(settings, stack.incarnation())
        self.assertNotEqual(one[one.index("--incarnation") + 1],
                            other[other.index("--incarnation") + 1])

    def test_a_manager_already_running_is_not_this_starts_to_acknowledge(self):
        """A second start that only replaces the publisher must not demand an
        acknowledgement from a process it did not spawn."""
        import io

        spawned = []
        with mock.patch.object(stack, "_spawn", self.fake_spawn(spawned)):
            with open(os.devnull, "w") as quiet:
                self.assertEqual(stack.start(self.root, self.environ, stream=quiet), 0)
        manager = stack.read_record(self.root, stack.MANAGER)
        self.assertTrue(stack.acknowledged(manager))

        # The publisher goes away; the manager stays, and is not re-proved.
        publisher = stack.read_record(self.root, stack.PUBLISHER)
        for child in self.owned:
            if child.pid == publisher["pid"]:
                child.kill()
                child.wait(timeout=5)
        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn", self.fake_spawn(spawned)):
            self.assertEqual(stack.start(self.root, self.environ, stream=stream), 0)
        self.assertEqual([name for name, _ in spawned],
                         [stack.MANAGER, stack.PUBLISHER, stack.PUBLISHER])

    def test_status_reports_a_running_manager_that_has_not_acknowledged(self):
        self.record_for("manager", self.sleeper())
        answer = stack.observe(self.root, environ=self.environ)
        self.assertEqual(answer["processes"]["manager"]["state"], "running")
        self.assertIn("unacknowledged", answer["processes"]["manager"]["serving"])


class MalformedSnapshots(Fixture):
    """C4. Validate the document before walking it.

    `{"jobs": [null]}` carried the right shape at the top level, and the walk
    was outside the parse guard -- so it raised `AttributeError` out of a
    `stop` that had already signalled its processes. The viewer's own reader
    learned this for the same input.
    """

    def nested(self):
        return [({"jobs": [None]}, "every Job in this document is a document"),
                ({"jobs": {}}, "this document's jobs are a list"),
                ({"jobs": [{"stages": 3}]}, "a Job's stages are a list"),
                ({"jobs": [{"stages": [None]}]}, "every stage is a document"),
                ({"jobs": [{"stages": [{"episodes": 3}]}]},
                 "a stage's episodes are a list"),
                ({"jobs": [{"stages": [{"episodes": [None]}]}]},
                 "every episode is a document")]

    def test_every_nested_shape_is_refused_before_it_is_walked(self):
        for members, expected in self.nested():
            # Built by overriding the valid document, so a member that collides
            # with a fixture operand still reaches the validator verbatim.
            self.publish_snapshot(document=dict(self.status_document(), **members))
            answer = stack.snapshot(self.root, time.time())
            self.assertEqual(answer["state"], "unreadable", members)
            self.assertIn(expected, answer["detail"], members)
            self.assertEqual(stack.runtime_boundary(self.root)["state"],
                             stack.UNKNOWN, members)

    def test_an_absent_nested_member_is_absence_rather_than_malformation(self):
        """`null` where a list would go is "there are none", which is the same
        latitude the viewer gives a document with no Jobs. It must not become a
        refusal, or an ordinary idle snapshot would read as damaged."""
        self.publish_snapshot(jobs=[{"stages": None}, {}])
        answer = stack.runtime_boundary(self.root)
        self.assertEqual(answer["state"], "observed")
        self.assertEqual(answer["open_episodes"], 0)

    def test_a_stop_over_a_malformed_snapshot_does_not_crash_after_signalling(self):
        """The failure mode that matters: the crash happened AFTER the
        processes had been signalled."""
        self.start_both()
        self.publish_snapshot(document=dict(self.status_document(), jobs=[None]))
        code, text = self.output(lambda s: stack.stop(self.root, stream=s))
        self.assertEqual(code, 0)
        self.assertEqual(text.count("stopped: "), len(stack.PROCESSES))
        self.assertIn("runtime   unknown", text)

    def test_a_document_that_never_says_when_it_looked_is_unreadable(self):
        for when in (None, "", "yesterday", 17):
            document = self.status_document()
            document["observed_at"] = when
            self.publish_snapshot(document=document)
            answer = stack.snapshot(self.root, time.time())
            self.assertEqual(answer["state"], "unreadable", when)
            self.assertIn("observed_at", answer["detail"], when)

    def test_a_non_canonical_snapshot_cannot_say_what_is_not_executing(self):
        """It does not describe every Job, so it cannot support the one claim
        this line is read for."""
        self.publish_snapshot(canonical=False)
        answer = stack.runtime_boundary(self.root)
        self.assertEqual(answer["state"], stack.UNKNOWN)
        self.assertIn("not canonical", answer["detail"])
        # It is still a readable document, and its Jobs still count.
        self.assertEqual(stack.observe(self.root, environ=self.environ)["jobs"]["state"],
                         "observed")

    def test_a_freshly_written_but_stalely_observed_document_is_unknown(self):
        now = time.time()
        self.publish_snapshot(observed=now - stack.PUBLISH_SECONDS * 100)
        answer = stack.runtime_boundary(self.root, now=now)
        self.assertEqual(answer["state"], stack.UNKNOWN)
        self.assertIn("observed", answer["detail"])



class EveryRecordWriteIsInsideTheRollback(Fixture):
    """D1. A process is registered for rollback before anything else can fail.

    `_spawn` wrote the record, the caller wrote it AGAIN to add the manager's
    incarnation, and only then appended it to the unwind list -- so a failure
    in that second write escaped with the manager live and outside the rollback
    it had been promised. The correction removes the second write rather than
    guarding it, and this holds that: the identity is published once, and no
    record write happens after `_spawn` at all.
    """

    def test_the_spawned_identity_is_published_in_one_write(self):
        """Against the REAL `_spawn`, because a substitute cannot be asked how
        many times the real one writes -- which is the whole question."""
        writes = []
        real = stack.write_record

        def counting(root, name, record):
            writes.append(dict(record))
            return real(root, name, record)

        with mock.patch.object(stack, "write_record", counting):
            record = stack._spawn(
                self.root, stack.MANAGER,
                [sys.executable, "-c", "import time; time.sleep(30)"],
                self.environ, extra={"incarnation": "v12-stack-one-write"})
        self.addCleanup(lambda: os.kill(record["pid"], 9))
        self.assertEqual(len(writes), 1, writes)
        # And that ONE write already carries the whole identity, so there is
        # nothing left for a caller to add afterwards.
        self.assertEqual(writes[0]["incarnation"], "v12-stack-one-write")
        self.assertEqual(writes[0]["pid"], record["pid"])

    def test_start_adds_no_record_write_of_its_own_after_a_spawn(self):
        writes = []
        real = stack.write_record

        def counting(root, name, record):
            writes.append(name)
            return real(root, name, record)

        with mock.patch.object(stack, "write_record", counting), \
                mock.patch.object(stack, "_spawn", self.fake_spawn()):
            with open(os.devnull, "w") as quiet:
                self.assertEqual(stack.start(self.root, self.environ, stream=quiet), 0)
        # The fixture's own `record_for` writes once per process, and START adds
        # nothing before or after it: two writes, never three.
        self.assertEqual(writes, list(stack.PROCESSES))

    def test_a_record_write_failure_still_rolls_the_process_back(self):
        """The real `_spawn`, and the one write it makes, made to fail."""
        seen = {}

        def failing(root, name, record):
            seen.update(record)
            raise OSError("the record could not be written")

        with mock.patch.object(stack, "write_record", failing):
            with self.assertRaises(OSError) as raised:
                with open(os.devnull, "w") as quiet:
                    stack.start(self.root, self.environ, stream=quiet,
                                ready_seconds=0.3, sleep=lambda _: None)
        self.assertIn("could not be written", str(raised.exception))
        self.assertEqual(seen.get("name"), stack.MANAGER)
        # It carried its incarnation on the FIRST write, and it is gone again.
        self.assertIn("incarnation", seen)
        self.assertEqual(stack.ownership({"schema": stack.SCHEMA, "pid": seen["pid"],
                                          "started_at": seen["started_at"]}),
                         stack.GONE)
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.root, name), name)

    def test_nothing_is_written_to_a_record_after_a_start_succeeds(self):
        """The `serving_acknowledged` cache is gone: the manager's own log is
        the one place that answer lives, so there is nothing left to fail."""
        with mock.patch.object(stack, "_spawn", self.fake_spawn()):
            with open(os.devnull, "w") as quiet:
                stack.start(self.root, self.environ, stream=quiet)
        record = stack.read_record(self.root, stack.MANAGER)
        self.assertNotIn("serving_acknowledged", record)
        self.assertTrue(stack.acknowledged(record))

    def test_one_process_that_cannot_be_unwound_does_not_hide_the_others(self):
        """D1's last clause. Taking the manager back raises outright, and the
        publisher is still stopped, cleared and accounted for."""
        import io

        really = stack._signal

        def breaking(record, number):
            if record["name"] == stack.MANAGER:
                raise RuntimeError("the manager could not be signalled at all")
            return really(record, number)

        stream = io.StringIO()
        with mock.patch.object(stack, "_spawn", self.fake_spawn(publish=False)), \
                mock.patch.object(stack, "_signal", breaking):
            with self.assertRaises(stack.StackRefusal):
                stack.start(self.root, self.environ, stream=stream,
                            ready_seconds=0.2, sleep=lambda _: None)
        written = stream.getvalue()
        self.assertIn("could not unwind manager", written)
        self.assertIn("RuntimeError", written)
        # The one that could not be taken back keeps its record; the other one
        # was positively stopped, so its record is gone. Neither answer was
        # lost to the other's failure.
        self.assertIsNotNone(stack.read_record(self.root, stack.MANAGER))
        self.assertIsNone(stack.read_record(self.root, stack.PUBLISHER))


class AnExistingManagerNeedsEvidenceToo(Fixture):
    """D2. Liveness is not readiness for a manager this start did not spawn.

    Both the both-live fast return and the publisher-replacement path accepted
    a live manager on the reading that an earlier start had already proved it.
    That is false after an interrupted start, and false after an unwind that
    deliberately retained a live process it could not stop -- and in both cases
    `start` returned 0 while `status` said, simultaneously, unacknowledged.
    """

    def impatient(self):
        first = iter([0.0])
        return lambda: next(first, 1e9)

    def test_both_live_but_unacknowledged_is_not_ready(self):
        self.start_both(acknowledge=False)
        self.publish_snapshot()
        with mock.patch.object(stack, "READY_SECONDS", 0.3), \
                mock.patch.object(stack, "_spawn",
                                  side_effect=AssertionError("started a second manager")):
            code, text = self.output(lambda s: stack.main(
                ["--root", str(self.root), "start"], stream=s, environ=self.environ))
        self.assertEqual(code, 2)
        self.assertIn("never acknowledged", text)
        self.assertIn("ALREADY running when this start arrived", text)
        self.assertNotIn("already running: manager", text)
        # AND IT IS NEITHER KILLED NOR DUPLICATED: this start did not admit it.
        record = stack.read_record(self.root, stack.MANAGER)
        self.assertTrue(stack.alive(record))
        self.assertIn("unacknowledged",
                      stack.observe(self.root, environ=self.environ)
                      ["processes"]["manager"]["serving"])

    def test_replacing_only_the_publisher_still_needs_the_managers_evidence(self):
        records = self.start_both(acknowledge=False)
        for child in self.owned:
            if child.pid == records[1]["pid"]:
                child.kill()
                child.wait(timeout=5)
        with mock.patch.object(stack, "READY_SECONDS", 0.3), \
                mock.patch.object(stack, "_spawn", self.fake_spawn()):
            code, text = self.output(lambda s: stack.main(
                ["--root", str(self.root), "start"], stream=s, environ=self.environ))
        self.assertEqual(code, 2)
        self.assertIn("never acknowledged", text)
        self.assertNotIn("ready:", text)
        # The publisher this start spawned is unwound; the manager is not ours.
        self.assertIsNone(stack.read_record(self.root, stack.PUBLISHER))
        self.assertTrue(stack.alive(stack.read_record(self.root, stack.MANAGER)))

    def test_an_existing_manager_that_acknowledges_late_is_waited_for(self):
        """The legitimate race: a previous start was interrupted while its
        manager was still opening the Authority, and the manager got there."""
        named = "v12-stack-late"
        record = self.record_for("manager", self.sleeper(), incarnation=named)
        self.record_for("publisher", self.sleeper())
        self.publish_snapshot()
        self.assertFalse(stack.acknowledged(record))

        waits = []

        def sleeping(_seconds):
            waits.append(1)
            if len(waits) == 3:
                self.acknowledge(named)

        code, text = self.output(lambda s: stack.start(
            self.root, self.environ, stream=s, ready_seconds=30, sleep=sleeping))
        self.assertEqual(code, 0)
        self.assertIn("has now acknowledged", text)
        self.assertEqual(text.count("already running: "), len(stack.PROCESSES))

    def test_an_acknowledged_manager_is_never_asked_to_initialize_again(self):
        self.start_both()
        with mock.patch.object(stack, "_spawn",
                               side_effect=AssertionError("started a second manager")):
            code, text = self.output(lambda s: stack.start(
                self.root, self.environ, stream=s))
        self.assertEqual(code, 0)
        self.assertEqual(text.count("already running"), len(stack.PROCESSES))
        self.assertNotIn("has now acknowledged", text)

    def test_a_repeated_start_waits_bounded_and_then_refuses(self):
        self.start_both(acknowledge=False)
        with self.assertRaises(stack.StackRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                stack.start(self.root, self.environ, stream=quiet,
                            ready_seconds=0.2, sleep=lambda _: None)
        self.assertIn("run `just stop`", str(raised.exception))


# -- the composition case -----------------------------------------------------
#
# R3's last requirement: the accepted 32 checks proved the LIFECYCLE over
# `sleep` processes and one deliberately invalid document, so the one thing
# they could not see was that the real children cannot even import. This case
# runs the REAL manager, the REAL publisher and the REAL viewer over a VALID
# deployment with an EMPTY Job store, which is the "empty configured stack is a
# valid idle state" the FINDING selected.

DISK_ROOT_VARIABLE = "BATON_V12_STACK_TEST_ROOT"


def _disk_root_outside_the_checkout():
    """A disk-backed directory that is NOT inside the working tree.

    Two rules meet here and the accepted suites only satisfy one each.
    `source_boundary` refuses a workspace on a memory filesystem, so `/tmp` is
    out on a host whose `/tmp` is a tmpfs -- `tests/manager/disk_roots.py`
    answers that by falling back to the DISTRIBUTION. And `stage_execution`
    refuses any configured mutable root inside the checkout, which is exactly
    what that fallback is. The accepted stage suites reconcile the two by
    substituting `_checkout`; a case that runs the real child in its own
    process cannot substitute anything, so it has to find a root that satisfies
    both rules for real.

    A REFUSAL RATHER THAN A SKIP, for `disk_roots`' own stated reason: a case
    that skipped itself would report green on a host where the composition was
    never exercised, and this case exists because something reported success
    without having run.

    AND AN EXPLICIT SELECTION IS NEVER SILENTLY PASSED OVER, which is the other
    half of that same rule and the reason review 2026-09-16T11-53-00Z [I1]
    reaches in here. The recipe used to assign its default over an exported
    root; correcting the recipe alone would have left the selection silently
    REPLACED one layer down, because an unusable named root simply fell through
    to the next candidate. A run whose operator believed something false about
    where its material was going is told, by name.
    """
    from baton_v12.worker_manager.source_boundary import (MEMORY_FILESYSTEMS,
                                                          filesystem_of)
    from tools import stage_execution

    checkout = stage_execution._checkout()
    named = (os.environ.get(DISK_ROOT_VARIABLE) or "").strip()
    tried = []
    for place in ([named] if named else []) + ["/var/tmp",
                                               os.path.expanduser("~/.cache"),
                                               tempfile.gettempdir()]:
        resolved = os.path.realpath(place)
        why = None
        if resolved == checkout or resolved.startswith(checkout.rstrip("/") + "/"):
            why = "it is inside the checkout at " + checkout
        elif not os.path.isdir(resolved) or not os.access(resolved, os.W_OK):
            why = "it is not a directory this process can write"
        else:
            try:
                kind = filesystem_of(resolved)
            except Exception as failure:                    # noqa: BLE001
                why = "this build cannot say what filesystem it is on: " + str(failure)
            else:
                if kind in MEMORY_FILESYSTEMS:
                    why = ("it is on a " + kind + " filesystem, and the workspace "
                           "boundary refuses a workspace on memory")
        if why is None:
            return resolved
        if place == named:
            raise AssertionError(
                DISK_ROOT_VARIABLE + " is " + repr(named) + " and " + why
                + ". An explicitly selected root is never silently passed over; "
                "choose another, or unset it to fall back.")
        tried.append(place + " (" + why + ")")
    raise AssertionError(
        "no disk-backed directory outside the checkout was found for the v12 "
        "stack composition case; tried " + ", ".join(tried) + ". Set "
        + DISK_ROOT_VARIABLE + " to a directory on real storage outside "
        + checkout + ".")


try:
    from tests.manager import disk_roots as _disk_roots
    from tests.tools import test_stage_execution as _stage_case
except ImportError as _failure:                             # pragma: no cover
    _disk_roots = _stage_case = None
    _IMPORT_FAILURE = _failure


@unittest.skipIf(_stage_case is None, "the accepted stage fixtures are not importable")
class ValidIdleComposition(_stage_case.ServingCase if _stage_case else unittest.TestCase):
    """The whole stack, composed for real, idle and empty.

    THE DEPLOYMENT IS THE ACCEPTED FIXTURE'S, not one this case invented. A
    hand-rolled "valid" document would be asserting against this case's own
    idea of validity, which is the same decision `test_stage_execution` states
    when it reuses `SingleWorkerCase` rather than rebuilding it.

    NOTHING IS SUBSTITUTED, because nothing CAN be: the children are separate
    processes reached through `tools.stack`, so they resolve their own
    configuration, open their own stores, compose their own deployment through
    the literal `tools.stage_execution:factory` and hold their own engine. The
    Job store is EMPTY, so the serving loop reconciles nothing, calls no engine
    and reaches no provider -- which is what makes an idle composition checkable
    without a live run.
    """

    def setUp(self):
        chosen = mock.patch.dict(os.environ,
                                 {_disk_roots.VARIABLE: _disk_root_outside_the_checkout()})
        chosen.start()
        self.addCleanup(chosen.stop)
        super().setUp()
        self.state = os.path.join(self.root, "stack-state")
        self.job_store = os.path.join(self.root, "stack-jobs.sqlite3")
        self.control_store = os.path.join(self.root, "stack-control.sqlite3")
        self.addCleanup(self.stop_whatever_is_left)

    def stop_whatever_is_left(self):
        with open(os.devnull, "w") as quiet:
            try:
                stack.stop(self.state, stream=quiet)
            except stack.StackRefusal:
                pass

    def credential_registry(self):
        """A real user-credential registry, so the DEFAULT provider is used.

        `worker_preflight` builds its production provider from
        `credential_sources` when a composer injects none, and the literal
        `factory` injects none -- which is the whole point here, since a child
        process is exactly a composer that cannot inject. Stated locally rather
        than inherited because the accepted case that owns this helper also
        needs a real repository, and an idle empty stack does not.
        """
        source = os.path.join(self.root, "stack-provider.token")
        with open(source, "w", encoding="utf-8") as writing:
            writing.write(self.secret)
        os.chmod(source, 0o600)
        place = os.path.join(self.root, "stack-credential-sources.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump({"schema": "baton.user-credential-sources/1",
                       "sources": [{"provider": "fixture",
                                    "reference": "fixture/one",
                                    "path": source}]}, writing)
        os.chmod(place, 0o600)
        return place

    def deployment(self):
        """The accepted document, with the production credential registry."""
        registry = self.credential_registry()
        document = self.composed_document()
        document["workers"] = [
            dict(one, deployment=dict(one["deployment"],
                                      credential_sources=registry))
            for one in document["workers"]]
        place = os.path.join(self.root, "stack-deployment.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(document, writing)
        return place

    def empty_stores(self):
        """Both stores, created once, so the two children never race to make
        them. An EMPTY Job store: this composition is given no work."""
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import job_manager

        clock = job_manager._utc_clock()
        with JobStore.open(self.job_store,
                           authority_uuid=self.config["authority_uuid"],
                           incarnation="v12-stack-case", clock=clock) as store:
            self.assertEqual(store.authority_uuid, self.config["authority_uuid"])
        with ControlStore.open(self.control_store, incarnation="v12-stack-case",
                               clock=clock):
            pass

    def environment(self):
        self.empty_stores()
        prepared = dict(os.environ)
        prepared.update({
            "BATON_V12_JOB_STORE": self.job_store,
            "BATON_V12_CONTROL_STORE": self.control_store,
            "BATON_V12_AUTHORITY_UUID": self.config["authority_uuid"],
            stack.CONFIG_ENV: self.deployment()})
        return prepared

    def test_the_real_children_compose_an_empty_configured_stack(self):
        import io

        environ = self.environment()
        stream = io.StringIO()
        code = stack.start(self.state, environ, stream=stream)
        started = stream.getvalue()
        self.assertEqual(code, 0, started)
        # POSITIVE ACKNOWLEDGEMENT, not "the kernel forked something".
        self.assertIn("ready:", started)
        for name in stack.PROCESSES:
            self.assertTrue(stack.alive(stack.read_record(self.state, name)),
                            name + ": " + stack._log_tail(self.state, name))

        # C3, END TO END: the acknowledgement is a real line printed by the
        # real `job_manager serve` after its real deployment composed, naming
        # the incarnation THIS start gave it. Everything else here could be
        # true of a manager that never initialized.
        manager = stack.read_record(self.state, stack.MANAGER)
        self.assertTrue(stack.acknowledged(manager))
        self.assertIn(stack.SERVING_ACKNOWLEDGEMENT + repr(manager["incarnation"]),
                      stack.log_path(self.state, stack.MANAGER).read_text())

        # WHAT THE PUBLISHER ACTUALLY WROTE. It can only exist if
        # `job_manager status --observe tools.stage_execution:observing_factory`
        # read these stores through this deployment document.
        published = json.loads(stack.snapshot_path(self.state).read_bytes())
        self.assertEqual(published["jobs"], [])
        self.assertIn("schema", published)

        answer = stack.observe(self.state, environ=environ)
        self.assertEqual(answer["processes"]["manager"]["state"], "running")
        self.assertEqual(answer["processes"]["publisher"]["state"], "running")
        self.assertEqual(answer["snapshot"]["state"], "fresh")
        self.assertEqual(answer["jobs"], {"state": "observed", "count": 0,
                                          "canonical": published.get("canonical")})
        self.assertEqual(answer["configuration"]["state"], "configured")
        # AN EMPTY CONFIGURED STACK IS A VALID IDLE STATE: nothing is executing
        # and that is KNOWN rather than assumed.
        self.assertEqual(answer["runtime"]["state"], "observed")
        self.assertEqual(answer["runtime"]["open_episodes"], 0)

        # THE MONITOR'S OWN CHILD, over the document the publisher wrote.
        viewed = subprocess.run(
            [sys.executable, "-m", "tools.job_viewer",
             "--status", str(stack.snapshot_path(self.state)), "--ticks", "1"],
            cwd=str(stack.DISTRIBUTION),
            env=stack.child_environment({"PATH": os.environ.get("PATH", "")}),
            capture_output=True, text=True, timeout=120)
        self.assertEqual(viewed.returncode, 0, viewed.stderr)

        # AND A SECOND START IS STILL NOT A SECOND MANAGER.
        again = io.StringIO()
        self.assertEqual(stack.start(self.state, environ, stream=again), 0)
        self.assertEqual(again.getvalue().count("already running"),
                         len(stack.PROCESSES))

        stopped = io.StringIO()
        self.assertEqual(stack.stop(self.state, stream=stopped), 0,
                         stopped.getvalue())
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.state, name), name)

    def test_a_deployment_that_does_not_compose_fails_the_start(self):
        """The counterexample to the case above, over the SAME machinery: a
        document the child will refuse produces a non-success start with the
        child's own reason, rather than a comfortable idle."""
        import io

        environ = self.environment()
        broken = os.path.join(self.root, "stack-broken.json")
        document = json.loads(Path(environ[stack.CONFIG_ENV]).read_text())
        document["authority_uuid"] = "f" * 32
        Path(broken).write_text(json.dumps(document))
        environ[stack.CONFIG_ENV] = broken

        stream = io.StringIO()
        with self.assertRaises(stack.StackRefusal) as raised:
            stack.start(self.state, environ, stream=stream, ready_seconds=25)
        self.assertNotIn("ready:", stream.getvalue())
        # THE CHILD'S OWN REASON, carried out of its log rather than paraphrased.
        self.assertIn("did not stay up", str(raised.exception))
        self.assertIn("ContractRefusal", str(raised.exception))
        self.assertIn("f" * 32, str(raised.exception))
        # And it never acknowledged, because it never composed.
        self.assertNotIn(stack.SERVING_ACKNOWLEDGEMENT,
                         stack.log_path(self.state, stack.MANAGER).read_text())
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(self.state, name), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
