"""Focused offline checks. Engine and provider boundaries are deterministic fakes."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qualification_contract as c
import qualification_worker as worker

spec = importlib.util.spec_from_file_location("qualification_fixture", HERE / "qualification-fixture.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class Contract(unittest.TestCase):
    def setUp(self):
        self.session = str(uuid.uuid4())

    def result(self, **changes):
        value = dict(type="result", subtype="success", is_error=False, session_id=self.session, modelUsage={c.ACTUAL_MODEL: {}})
        value.update(changes)
        return value

    def test_argv_and_environment_are_the_selected_one_shot_contract(self):
        token = "a" * 32
        first = c.argv(self.session, 1, c.prompt(1, token))
        second = c.argv(self.session, 2, c.prompt(2))
        self.assertEqual([i for i, (a, b) in enumerate(zip(first, second)) if a != b], [7, 9])
        self.assertNotIn(token, second[-1])
        self.assertEqual(first[:7], ["claude", "--print", "--dangerously-skip-permissions", "--output-format", "json", "--model", c.MODEL])
        self.assertEqual(set(c.environment()), {"HOME", "PATH", "TMPDIR", "XDG_CACHE_HOME", "PYTHONPYCACHEPREFIX"})
        self.assertNotIn("--max-turns", first)

    def test_session_model_success_are_observed_and_never_filled_in(self):
        yes = c.projection(c.encoded(self.result()), self.session)
        self.assertTrue(c.success(yes))
        self.assertEqual(yes["actual_model"], c.ACTUAL_MODEL)
        for change in ({"session_id": str(uuid.uuid4())}, {"is_error": True}, {"is_error": "false"}, {"subtype": "error_max_turns"}):
            self.assertFalse(c.success(c.projection(c.encoded(self.result(**change)), self.session)))
        for change in ({"modelUsage": {}}, {"modelUsage": {"unknown-private-model": {}}}, {"model": "different"}):
            self.assertIsNone(c.projection(c.encoded(self.result(**change)), self.session)["actual_model"])

    def test_private_values_and_unknown_names_are_not_exported(self):
        sentinel = "PRIVATE-PROVIDER-TEXT-NEVER-EXPORT"
        raw = self.result(result=sentinel, model=sentinel, api_error_status=sentinel)
        raw[sentinel] = sentinel
        export = c.encoded(c.projection(c.encoded(raw), self.session))
        self.assertNotIn(sentinel.encode(), export)
        self.assertIn(c.sha(sentinel.encode()).encode(), export)

    def test_parser_refuses_duplicate_nonfinite_truncated_and_oversized_records(self):
        for raw in (b'{"type":1,"type":2}', b'{"n":NaN}', b'{', b'x' * (c.LIMIT + 1)):
            with self.subTest(raw=raw[:30]), self.assertRaises(c.Refusal):
                c.projection(raw, self.session)

    def test_arbitrary_exception_text_is_not_a_diagnostic(self):
        self.assertEqual(c.failure_code(ValueError("PRIVATE-TEXT")), "unclassified")
        self.assertEqual(c.failure_code(c.Refusal("PRIVATE-TEXT")), "unclassified")
        self.assertEqual(c.failure_code(c.Refusal("provider-timeout")), "provider-timeout")

    def test_resume_requires_consumed_positive_shutdown(self):
        for receipt in (None, {"consumed": False, "running": False, "pid": 0}, {"consumed": True, "running": True, "pid": 12}):
            with self.assertRaises(c.Refusal):
                c.may_restore(receipt)
        receipt = {"consumed": False, "running": False, "pid": 0}
        c.consume(receipt)
        c.may_restore(receipt)
        with self.assertRaises(c.Refusal):
            c.consume(receipt)


class Files(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w177936-offline-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        (self.home / ".claude").mkdir(parents=True)
        (self.home / ".claude/.credentials.json").symlink_to(c.SLOT)
        self.session = str(uuid.uuid4())

    def state(self):
        path = self.home / ".claude/projects/observed-key" / (self.session + ".jsonl")
        path.parent.mkdir(parents=True)
        path.write_bytes(b"synthetic private session")
        return path

    def test_subset_uses_observed_project_key_and_only_expected_session_file(self):
        own = self.state()
        (self.home / ".claude.json").write_bytes(b"not-to-be-read-configuration")
        with mock.patch.object(c, "read_file", wraps=c.read_file) as reading:
            rows = c.inventory(self.home)
        self.assertFalse(any(str(call.args[0]).endswith(".claude.json") for call in reading.call_args_list))
        chosen = c.subset(rows, self.session)
        self.assertEqual([row["path"] for row in chosen], [str(own.relative_to(self.home))])
        self.assertEqual((chosen[0]["uid"], chosen[0]["gid"], chosen[0]["mode"]), (own.stat().st_uid, own.stat().st_gid, oct(own.stat().st_mode & 0o7777)))
        self.assertNotIn(b"observed-key", c.encoded(c.public_inventory(rows)))

    def test_credential_target_is_never_opened(self):
        self.state()
        with mock.patch.object(c, "read_file", wraps=c.read_file) as reading:
            c.inventory(self.home)
        self.assertTrue(reading.called)
        self.assertFalse(any("credential" in str(call.args[0]) for call in reading.call_args_list))

    def test_bad_credential_and_link_types_refuse_before_contents(self):
        for kind in ("credential", "link", "hardlink", "fifo"):
            with self.subTest(kind=kind):
                path = self.home / ("oauth-token" if kind == "credential" else "unexpected")
                if kind == "link":
                    path.symlink_to(self.root)
                elif kind == "hardlink":
                    source = self.root / "source"
                    source.write_bytes(b"opaque")
                    os.link(source, path)
                elif kind == "fifo":
                    os.mkfifo(path)
                else:
                    path.write_bytes(b"forbidden")
                with mock.patch.object(c, "read_file", side_effect=AssertionError("opened")), self.assertRaises(c.Refusal):
                    c.inventory(self.home)
                path.unlink()

    def test_ambiguous_projects_and_missing_session_do_not_widen_selection(self):
        self.state()
        (self.home / ".claude/projects/another").mkdir()
        with self.assertRaises(c.Refusal):
            c.subset(c.inventory(self.home), self.session)
        with self.assertRaises(c.Refusal):
            c.subset([], self.session)
        shutil.rmtree(self.home / ".claude/projects/another")
        (self.home / ".claude/projects/observed-key/foreign.jsonl").write_bytes(b"foreign")
        with self.assertRaises(c.Refusal):
            c.subset(c.inventory(self.home), self.session)

    def test_entry_and_byte_limits_are_enforced(self):
        self.state()
        with mock.patch.object(c, "STATE_FILES", 2), self.assertRaises(c.Refusal):
            c.inventory(self.home)
        with mock.patch.object(c, "STATE_BYTES", 1), self.assertRaises(c.Refusal):
            c.inventory(self.home)


class FakeEngine:
    """Exercise the real host controller without Docker or provider execution."""
    def __init__(self, root, nonce, *, missing_model=False, bad_stop=False, bad_state=False):
        self.root, self.nonce = root, nonce
        self.missing_model, self.bad_stop, self.bad_state = missing_model, bad_stop, bad_state
        self.containers = {}
        self.calls = []
        self.token = None

    def __call__(self, args, seconds=20):
        self.calls.append(args)
        if args[:2] == ["image", "inspect"]:
            return c.encoded([{"Id": c.IMAGE, "Config": {"Volumes": None}}])
        if args[:2] == ["network", "create"]:
            return b"network-id"
        if args[:2] == ["network", "inspect"]:
            return c.encoded([{"Id": "network-id", "Name": "w177936-" + self.nonce, "Labels": {"baton.qualification": self.nonce}, "Driver": "bridge"}])
        if args[0] == "create":
            turn = len(self.containers) + 1
            if turn == 2:
                assert self.containers["1" * 64]["State"]["Running"] is False
            identity = str(turn) * 64
            mounts = []
            for i, arg in enumerate(args):
                if arg == "--mount":
                    parts = dict(piece.split("=", 1) for piece in args[i + 1].split(",") if "=" in piece)
                    mounts.append({"Type": "bind", "Source": parts["src"], "Destination": parts["dst"], "RW": not args[i + 1].endswith(",readonly"), "Propagation": "rprivate"})
            self.containers[identity] = {"Id": identity, "Image": c.IMAGE, "Config": {"User": c.USER, "Labels": {"baton.qualification": self.nonce}},
                "HostConfig": {"NetworkMode": "network-id", "ReadonlyRootfs": True, "Privileged": False, "PidsLimit": 64, "Memory": 2147483648,
                               "NanoCpus": 1000000000, "GroupAdd": [str(c.GROUP)], "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"]},
                "State": {"Running": False, "Pid": 0, "Status": "created", "ExitCode": 0}, "Mounts": mounts}
            return identity.encode()
        if args[:2] == ["container", "inspect"]:
            return c.encoded([self.containers[args[2]]])
        if args[:2] == ["start", "--attach"]:
            value = self.containers[args[2]]
            mounts = {m["Destination"]: Path(m["Source"]) for m in value["Mounts"]}
            request = c.decoded(c.read_file(mounts["/qualification/request.json"]))
            home = mounts["/run/baton/context"] / "home"
            workspace = mounts["/output"]
            state = home / ".claude/projects/provider-observed-key" / (request["session"] + ".jsonl")
            if request["turn"] == 1:
                self.token = re.search(r"conversation, but do not write.*?: ([0-9a-f]{32})", request["prompt"]).group(1)
                state.parent.mkdir(parents=True)
                state.write_text(self.token)
                (home / "irrelevant-cache").write_bytes(b"not-restorable")
                if self.bad_state:
                    (home / "oauth-token").write_bytes(b"must-refuse")
                (workspace / "solution.py").write_bytes(c.INITIAL)
            else:
                assert self.token not in request["prompt"]
                assert not (home / "irrelevant-cache").exists()
                assert state.read_text() == self.token
                (workspace / "solution.py").write_bytes(c.CORRECTED)
                (workspace / "continuity.txt").write_text(state.read_text() + "\n")
            value["State"].update(Running=self.bad_stop, Pid=12 if self.bad_stop else 0, Status="running" if self.bad_stop else "exited")
            raw = dict(type="result", subtype="success", is_error=False, session_id=request["session"])
            if not self.missing_model:
                raw["modelUsage"] = {c.ACTUAL_MODEL: {}}
            args = c.argv(request["session"], request["turn"], request["prompt"])
            return c.encoded(dict(outcome="observed", provider_started=True, provider_exit=0,
                terminal=c.projection(c.encoded(raw), request["session"]), argv=args[:-1] + [{"prompt_sha256": c.sha(args[-1].encode())}],
                environment_keys=sorted(c.environment()), cwd="/output", uid=65532, groups=[c.GROUP], home_mode="0o2770"))
        raise AssertionError(args)


class Controller(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w177936-controller-offline-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.volatile = self.root / "volatile"
        self.volatile.mkdir()
        self.source = self.root / "synthetic-credential"
        fixture.private_file(self.source, b"not-a-credential")
        self.nonce = uuid.uuid4().hex
        for patch in (mock.patch.object(c, "GROUP", os.getgid()), mock.patch.object(fixture, "VOLATILE", self.volatile),
                      mock.patch.object(fixture, "SOURCE", self.source), mock.patch.object(os, "setsid")):
            patch.start()
            self.addCleanup(patch.stop)

    def execute(self, **options):
        fake = FakeEngine(self.root, self.nonce, **options)
        with mock.patch.object(fixture, "engine", fake), mock.patch.object(subprocess, "Popen", side_effect=AssertionError("offline test invoked process")):
            fixture.controller(self.root, self.nonce)
        return fake, c.decoded(c.read_file(self.root / "outcome.json"))

    def test_two_turn_trace_reconstructs_only_the_subset_and_keeps_token_private(self):
        fake, result = self.execute()
        self.assertEqual(result["outcome"], "qualified")
        self.assertEqual(len(fake.containers), 2)
        self.assertEqual(len(result["arms"]), 2)
        self.assertTrue(all(a["shutdown"]["consumed"] for a in result["arms"]))
        self.assertNotIn(fake.token.encode(), c.encoded(result))
        self.assertEqual(list(self.volatile.iterdir()), [])
        events = [c.decoded(line) for line in (self.root / "events.jsonl").read_bytes().splitlines()]
        consumed = next(i for i, e in enumerate(events) if e["event"] == "shutdown-receipt-consumed" and e["turn"] == 1)
        created = next(i for i, e in enumerate(events) if e["event"] == "container-create-intent" and e["turn"] == 2)
        self.assertLess(consumed, created)
        self.assertEqual(sum(e["event"] == "user-turn-intent" for e in events), 2)
        self.assertEqual(sum(e["event"] == "provider-start-observed" and e["started"] for e in events), 2)

    def test_missing_model_is_a_qualification_failure_even_if_restoration_works(self):
        fake, result = self.execute(missing_model=True)
        self.assertEqual(result["outcome"], "not-qualified")
        self.assertEqual(len(fake.containers), 2)
        self.assertFalse(result["model_observed"])

    def test_unconfirmed_stop_cannot_start_replacement_or_release_credential(self):
        fake, result = self.execute(bad_stop=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(len(fake.containers), 1)
        self.assertTrue((self.volatile / "slot-1").exists())

    def test_capture_refusal_never_widens_the_subset_or_retries(self):
        fake, result = self.execute(bad_state=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["stage"], "collection")
        self.assertEqual(len(fake.containers), 1)

    def test_uncertain_cleanup_retains_the_owned_credential(self):
        fixture.private_file(self.volatile / "slot-1", b"synthetic")
        with mock.patch.object(fixture, "engine", side_effect=c.Refusal("engine-refused")):
            result = fixture.cleanup(self.nonce)
        self.assertFalse(any(r["confirmed"] for r in result))
        self.assertTrue((self.volatile / "slot-1").exists())

    def test_lost_create_answer_is_recovered_by_exact_name_and_nonce(self):
        fixture.private_file(self.volatile / "slot-1", b"synthetic")
        identity = "1" * 64
        state = {"Id": identity, "Image": c.IMAGE, "Config": {"Labels": {"baton.qualification": self.nonce}},
                 "State": {"Running": True, "Pid": 123, "Status": "running", "ExitCode": 0}}
        calls = []

        def engine(args, seconds=20):
            calls.append(args)
            if args[0] == "ps":
                return identity.encode() if args[args.index("--filter") + 1].endswith("-1$") else b""
            if args[:2] == ["container", "inspect"]:
                return c.encoded([state])
            if args[0] == "stop":
                state["State"].update(Running=False, Pid=0, Status="exited")
                return identity.encode()
            if args[0] == "rm":
                self.assertFalse(state["State"]["Running"])
                self.assertEqual(state["State"]["Pid"], 0)
                return identity.encode()
            if args[:2] == ["network", "ls"]:
                return b""
            raise AssertionError(args)

        with mock.patch.object(fixture, "engine", engine):
            result = fixture.cleanup(self.nonce)
        self.assertTrue(all(row["confirmed"] for row in result))
        self.assertTrue(any(call[0] == "stop" for call in calls))
        self.assertEqual(list(self.volatile.iterdir()), [])

    def test_foreign_nonce_is_never_stopped_or_removed(self):
        fixture.private_file(self.volatile / "slot-1", b"synthetic")
        calls = []

        def engine(args, seconds=20):
            calls.append(args)
            if args[0] == "ps":
                return b"foreign"
            if args[:2] == ["container", "inspect"]:
                return c.encoded([{"Image": c.IMAGE, "Config": {"Labels": {"baton.qualification": "foreign"}}}])
            raise AssertionError("mutation attempted")

        with mock.patch.object(fixture, "engine", engine):
            result = fixture.cleanup(self.nonce)
        self.assertFalse(any(row["confirmed"] for row in result))
        self.assertFalse(any(call[0] in ("stop", "rm") for call in calls))
        self.assertTrue((self.volatile / "slot-1").exists())

    def test_existing_run_marker_refuses_before_any_engine_or_credential_use(self):
        with mock.patch.object(fixture, "ROOT", self.root), mock.patch.object(fixture, "audit", return_value="accepted"), \
                mock.patch.object(os, "getuid", return_value=1000), mock.patch.object(os, "getgroups", return_value=[c.GROUP]), \
                mock.patch.object(fixture.grp, "getgrnam", return_value=type("Group", (), {"gr_gid": c.GROUP})()), \
                mock.patch.object(fixture, "engine", side_effect=AssertionError("engine")), \
                mock.patch.object(fixture, "credential", side_effect=AssertionError("credential")), self.assertRaises(FileExistsError):
            fixture.run("accepted")

    def test_audit_never_uses_engine_or_credentials(self):
        with mock.patch.object(fixture, "engine", side_effect=AssertionError("engine")), mock.patch.object(fixture, "credential", side_effect=AssertionError("credential")), mock.patch.object(c, "GROUP", 1001):
            self.assertEqual(len(fixture.audit()), 64)


class ProviderPipe(unittest.TestCase):
    def test_bounded_pipe_uses_a_deterministic_local_process_and_reaps_it(self):
        children = []

        def fake(arguments, **options):
            options.pop("cwd")
            options.pop("env")
            p = subprocess.Popen([sys.executable, "-c", "print('{}')"], **options)
            children.append(p)
            return p

        code, raw = worker.invoke([], {}, seconds=2, run=fake)
        self.assertEqual((code, raw), (0, b"{}\n"))
        self.assertIsNotNone(children[0].returncode)
        with self.assertRaises(ProcessLookupError):
            os.killpg(children[0].pid, 0)

    def test_output_overflow_and_timeout_reap_the_owned_process(self):
        for script in ("import os; os.write(1, b'x'*100000)", "import time; time.sleep(30)"):
            children = []

            def fake(arguments, **options):
                options.pop("cwd")
                options.pop("env")
                p = subprocess.Popen([sys.executable, "-c", script], **options)
                children.append(p)
                return p

            with self.subTest(script=script), self.assertRaises(c.Refusal):
                worker.invoke([], {}, seconds=0.15, run=fake)
            self.assertIsNotNone(children[0].returncode)
            with self.assertRaises(ProcessLookupError):
                os.killpg(children[0].pid, 0)



class TheCorrectedCustodyAndPreflight(unittest.TestCase):
    """R1 and R2 from review 2026-09-15T14-36-52Z, each held by its own case.

    NEITHER NEEDS AN ENGINE. A mode mismatch and an unreserved root are both
    observable offline, which is the whole reason the review could find them
    before the expensive run rather than after it.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w177936-corrected-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    # -- R1: the working copy is writable by the runtime, the inputs are not --

    def written(self, name, **options):
        place = self.root / name
        with mock.patch.object(c, "GROUP", os.getgid()):
            fixture.private_file(place, b"x", **options)
        return stat.S_IMODE(place.lstat().st_mode)

    def test_the_reconstructed_working_copy_is_group_writable(self):
        """The runtime holds the workspace group as a supplementary group, so
        group write is what lets it append to its own restored state. 0640 is
        readable and not appendable, which is an input rather than a working
        copy."""
        self.assertEqual(self.written("copy", group=True, writable=True), 0o660)

    def test_manager_inputs_stay_read_only_for_the_runtime(self):
        """THE OTHER HALF, and the one that must not move. The credential slot
        copy and the request document are mounted read-only and stay 0640; a
        correction that widened every file would have handed the container
        write access to its own bearer."""
        self.assertEqual(self.written("input", group=True), 0o640)
        self.assertEqual(self.written("private"), 0o600)

    def test_only_the_restored_state_is_created_writable(self):
        """Source-level: exactly one call site asks for the writable mode, and
        it is the reconstruction. Asserted against the source rather than a
        comment, because the distinction is the correction."""
        import inspect

        # CALL SITES, not mentions: the helper's own docstring says the word
        # too, and counting prose would make this assertion meaningless.
        calls = [line for line in inspect.getsource(fixture).splitlines()
                 if "private_file(" in line and "def private_file" not in line]
        writable = [line for line in calls if "writable=True" in line]
        self.assertEqual(len(writable), 1, calls)
        self.assertIn("private_file(target,", writable[0])
        # AND EVERY OTHER CALL SITE STAYS AS IT WAS. The credential slot copy
        # and the request document are the container's read-only inputs.
        for line in calls:
            if line is not writable[0]:
                self.assertNotIn("writable", line)

    def test_effective_access_distinguishes_the_two_roles(self):
        """EFFECTIVE ACCESS FOR THE SELECTED OWNER/GROUP RELATIONSHIP, which is
        what the review asked for: a non-owner holding only the group gets
        write on the working copy and not on the inputs."""
        for name, options, group_write in (("wc", {"group": True, "writable": True}, True),
                                           ("in", {"group": True}, False)):
            with self.subTest(role=name):
                mode = self.written(name, **options)
                self.assertTrue(mode & stat.S_IRGRP, "group cannot read")
                self.assertEqual(bool(mode & stat.S_IWGRP), group_write)
                # `other` is empty in both roles.
                self.assertFalse(mode & 0o007)

    # -- R2: every fixed root is reserved before admission -------------------

    def reserved(self, existing):
        """Drive `run` with exactly one of the three roots already present."""
        root = self.root / "run"
        volatile = self.root / "volatile"
        export = root.with_name(root.name + "-export")
        {"root": root, "volatile": volatile, "export": export}[existing].mkdir()
        calls = []
        with mock.patch.object(fixture, "ROOT", root), \
                mock.patch.object(fixture, "VOLATILE", volatile), \
                mock.patch.object(fixture, "audit", return_value="accepted"), \
                mock.patch.object(os, "getuid", return_value=1000), \
                mock.patch.object(os, "getgroups", return_value=[c.GROUP]), \
                mock.patch.object(fixture.grp, "getgrnam",
                                  return_value=type("G", (), {"gr_gid": c.GROUP})()), \
                mock.patch.object(fixture, "engine",
                                  side_effect=AssertionError("engine")), \
                mock.patch.object(fixture, "credential",
                                  side_effect=AssertionError("credential")), \
                mock.patch.object(fixture.multiprocessing, "Process",
                                  side_effect=AssertionError("controller")), \
                self.assertRaises(FileExistsError):
            fixture.run("accepted")
        return root, volatile, export, calls

    def test_each_fixed_root_refuses_before_any_admission(self):
        """A CASE PER ROOT, not only the run marker. The export root used to be
        created after both live turns, so an existing one refused only once the
        identity had been consumed and the turns paid for."""
        for existing in ("root", "volatile", "export"):
            with self.subTest(existing=existing):
                self.setUp()
                self.reserved(existing)

    def test_a_refused_reservation_leaves_no_half_taken_identity(self):
        """Partial reservation unwinds. A refusal that left one of the three
        behind would make the next attempt refuse on the wrong root and report
        the wrong cause."""
        root, volatile, export, _ = self.reserved("export")
        self.assertFalse(root.exists(), "run root survived a refusal")
        self.assertFalse(volatile.exists(), "volatile root survived a refusal")
        self.assertTrue(export.exists(), "the foreign path was not preserved")

    def test_the_reservation_precedes_the_controller_in_source_order(self):
        """Source order, because the defect was an ordering one: the export
        mkdir sat below the controller join and above nothing that mattered."""
        import inspect

        text = inspect.getsource(fixture.run)
        self.assertLess(text.index("EXPORT ="), text.index("multiprocessing.Process"))
        self.assertLess(text.index("place.mkdir"), text.index("multiprocessing.Process"))
        # And it is not created a second time after the turns.
        self.assertEqual(text.count("mkdir(mode=0o700)"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
