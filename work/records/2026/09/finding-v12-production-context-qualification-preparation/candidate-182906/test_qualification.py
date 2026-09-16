"""Focused offline checks. Engine and provider boundaries are deterministic fakes."""
import errno
import importlib.util
import inspect
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

# The GENUINE fixed identity, captured before any test patches it away. Several
# cases below replace ROOT/VOLATILE with temporary directories, so without this
# there is nothing left to assert the real identity against.
REAL_IDENTITY, REAL_ROOT, REAL_VOLATILE = fixture.IDENTITY, fixture.ROOT, fixture.VOLATILE
CONSUMED_IDENTITY = "178579"


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
    def __init__(self, root, nonce, *, missing_model=False, bad_stop=False, bad_state=False,
                 final_lf=True, bad_code=False, bad_initial=False, bad_token=False, usage=None, forged_terminal=None,
                 skip_publish=False, publish_in_turn_two=False, blocked_directory=False):
        self.root, self.nonce = root, nonce
        self.missing_model, self.bad_stop, self.bad_state = missing_model, bad_stop, bad_state
        # The provider's formatting habits are an option, not an assumption:
        # `final_lf=False` reproduces exactly what run179075 wrote.
        self.final_lf, self.bad_code, self.bad_token = final_lf, bad_code, bad_token
        self.bad_initial = bad_initial
        self.skip_publish, self.publish_in_turn_two = skip_publish, publish_in_turn_two
        self.blocked_directory = blocked_directory
        self.blocked = None
        self.usage, self.forged_terminal = usage, forged_terminal
        self.containers = {}
        self.calls = []
        self.token = None

    def artifact(self, expected):
        return expected if self.final_lf else expected[:-1]

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
                # The runtime creates its own state restrictively -- the
                # observed 0o700/0o600 -- and P1a opens exactly these two.
                os.chmod(state.parent, 0o700)
                os.chmod(state, 0o600)
                (home / "irrelevant-cache").write_bytes(b"not-restorable")
                if self.blocked_directory:
                    # A runtime-owned directory that is NOT the project
                    # directory. The worker OWNS it and can enter it; the
                    # manager cannot. Same-UID fixtures cannot express that
                    # difference, so the mode is dropped AFTER publication (see
                    # below) to reproduce the manager-side view.
                    self.blocked = home / ".claude/blocked"
                    self.blocked.mkdir()
                    (self.blocked / "a-file").write_bytes(b"hidden from the collector")
                if self.bad_state:
                    (home / "oauth-token").write_bytes(b"must-refuse")
                (workspace / "solution.py").write_bytes(self.artifact(c.INITIAL.replace(b"* 2", b"* 9") if self.bad_initial else c.INITIAL))
            else:
                assert self.token not in request["prompt"]
                assert not (home / "irrelevant-cache").exists()
                assert state.read_text() == self.token
                (workspace / "solution.py").write_bytes(self.artifact(c.CORRECTED.replace(b"* 3", b"* 4") if self.bad_code else c.CORRECTED))
                (workspace / "continuity.txt").write_text(state.read_text() + ("" if self.bad_token else "\n"))
            # P1a, as the real worker performs it: turn 1 only, and only these
            # two runtime-owned objects.
            # R3/review182326: call the REAL worker publication rather than
            # simulating it, so the controller case actually exercises it.
            published = None
            if not self.skip_publish:
                with mock.patch.object(c, "HOME", str(home)):
                    published = worker.publish(request["session"], request["turn"])
            if self.blocked is not None and self.blocked.exists():
                # Only now: the worker could read its own directory, the
                # manager cannot.
                os.chmod(self.blocked, 0o000)
            if self.publish_in_turn_two and request["turn"] == 2:
                published = {"project_mode": "0o2750", "session_mode": "0o640"}
            value["State"].update(Running=self.bad_stop, Pid=12 if self.bad_stop else 0, Status="running" if self.bad_stop else "exited")
            raw = dict(type="result", subtype="success", is_error=False, session_id=request["session"])
            if self.usage is not None:
                raw["modelUsage"] = self.usage
            elif not self.missing_model:
                raw["modelUsage"] = {c.ACTUAL_MODEL: {}}
            args = c.argv(request["session"], request["turn"], request["prompt"])
            terminal = c.projection(c.encoded(raw), request["session"])
            if self.forged_terminal is not None:
                terminal.update(self.forged_terminal)
            return c.encoded(dict(outcome="observed", provider_started=True, provider_exit=0,
                terminal=terminal, argv=args[:-1] + [{"prompt_sha256": c.sha(args[-1].encode())}],
                environment_keys=sorted(c.environment()), cwd="/output", uid=65532, groups=[c.GROUP], home_mode="0o2770",
                published=published))
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
        """R2 moved this refusal EARLIER. A credential-shaped entry used to be
        caught by the manager's inventory, after the worker had already
        published; the worker now refuses it before any mode change, so the run
        stops at the first arm. Still one container, still no widening or
        retry."""
        fake, result = self.execute(bad_state=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["stage"], "first-turn")
        self.assertEqual(result["failure_code"], "publish-shape")
        self.assertEqual(len(fake.containers), 1)
        self.assertNotIn("promoted", result)

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
        # ROOT/VOLATILE are restored because this class patches them away for
        # its controller cases, and audit now checks the DECLARED identity
        # against the real one.
        with mock.patch.object(fixture, "engine", side_effect=AssertionError("engine")), mock.patch.object(fixture, "credential", side_effect=AssertionError("credential")), \
                mock.patch.object(c, "GROUP", 1001), mock.patch.object(fixture, "ROOT", REAL_ROOT), mock.patch.object(fixture, "VOLATILE", REAL_VOLATILE):
            self.assertEqual(len(fixture.audit()), 64)

    # -- owner179142: the two accepted artifact forms, end to end -----------

    def test_a_missing_final_lf_reaches_turn_two_and_is_observed_not_assumed(self):
        """THE CASE THAT FAILED FOR REAL. Run179075 wrote the expected 38 bytes
        with the final newline absent and refused at `initial-artifact`. Under
        the selected contract that same provider behaviour completes, and the
        record says so in the provider's own bytes rather than in a constant."""
        fake, result = self.execute(final_lf=False)
        self.assertEqual(result["outcome"], "qualified")
        self.assertEqual(len(fake.containers), 2, "the run stopped before turn two")
        self.assertEqual(result["initial_artifact"]["form"], "missing-final-lf")
        self.assertEqual(result["corrected_artifact"]["form"], "missing-final-lf")
        self.assertEqual(result["continuity_artifact"]["form"], "exact")
        for record, expected in ((result["initial_artifact"], c.INITIAL), (result["corrected_artifact"], c.CORRECTED)):
            self.assertEqual(record["observed_sha256"], c.sha(expected[:-1]))
            self.assertEqual(record["expected_sha256"], c.sha(expected))
            self.assertNotEqual(record["observed_sha256"], record["expected_sha256"])
            self.assertEqual((record["observed_bytes"], record["expected_bytes"]), (len(expected) - 1, len(expected)))

    def test_exact_bytes_still_record_an_observed_digest_of_their_own(self):
        _, result = self.execute()
        self.assertEqual(result["initial_artifact"]["form"], "exact")
        self.assertEqual(result["initial_artifact"]["observed_sha256"], c.sha(c.INITIAL))
        self.assertEqual(result["expected_initial_artifact_sha256"], c.sha(c.INITIAL))
        self.assertEqual(result["expected_corrected_artifact_sha256"], c.sha(c.CORRECTED))
        # A CONSTANT IS NOT AN OBSERVATION. The old names said `initial_artifact_sha256`
        # for a value that never came from the provider; they are gone.
        self.assertNotIn("initial_artifact_sha256", result)
        self.assertNotIn("corrected_artifact_sha256", result)

    def test_changed_code_still_refuses_at_the_second_turn(self):
        """The relaxation is one newline wide. A different multiplier is the
        thing the artifact check exists for and still stops the run."""
        for options, form in ((dict(bad_code=True), "mismatch"), (dict(bad_code=True, final_lf=False), "mismatch")):
            with self.subTest(**options):
                self.setUp()
                fake, result = self.execute(**options)
                self.assertEqual(result["outcome"], "failed")
                self.assertEqual(result["failure_code"], "correction-artifact")
                self.assertEqual(result["corrected_artifact"]["form"], form)
                self.assertEqual(len(fake.containers), 2)

    def test_a_token_written_without_its_newline_still_refuses(self):
        """continuity.txt DID NOT MOVE. Its contract is the token plus one
        newline, exactly, and no observation in this campaign supports changing
        it -- the failed run never reached the second turn at all."""
        _, result = self.execute(bad_token=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["failure_code"], "correction-artifact")
        self.assertEqual(result["continuity_artifact"], {"form": "mismatch", "observed_bytes": 32, "expected_bytes": 33})
        self.assertEqual(result["corrected_artifact"]["form"], "exact")

    def test_the_controller_never_rewrites_the_workspace(self):
        """No repair. A refused artifact is left exactly as the provider wrote
        it, so the operator's diagnostic sees the same bytes the fixture did."""
        for options in (dict(final_lf=False), dict(bad_code=True), dict(bad_token=True)):
            with self.subTest(**options):
                self.setUp()
                fake, result = self.execute(**options)
                workspace = self.root / "work"
                written = fake.artifact(c.CORRECTED.replace(b"* 3", b"* 4") if fake.bad_code else c.CORRECTED)
                self.assertEqual((workspace / "solution.py").read_bytes(), written)
                self.assertEqual(sorted(p.name for p in workspace.iterdir()), ["continuity.txt", "solution.py"])

    def test_a_refused_first_turn_artifact_is_recorded_before_it_is_refused(self):
        """RUN179075'S OWN SHAPE. That export carried a failure code and no
        observed bytes, so learning what the provider had actually written took
        a separate operator diagnostic afterwards. The record is now written
        before the refusal, and a first-turn refusal still stops the run."""
        fake, result = self.execute(bad_initial=True)
        self.assertEqual((result["outcome"], result["failure_code"]), ("failed", "initial-artifact"))
        self.assertEqual(result["stage"], "first-turn")
        self.assertEqual(result["initial_artifact"]["form"], "mismatch")
        self.assertEqual(result["initial_artifact"]["observed_sha256"], c.sha(c.INITIAL.replace(b"* 2", b"* 9")))
        self.assertEqual(result["initial_artifact"]["expected_sha256"], c.sha(c.INITIAL))
        self.assertEqual(len(fake.containers), 1, "a refused first turn must not reach restoration")
        self.assertNotIn("promoted", result)

    def test_a_refused_artifact_is_recorded_before_it_is_refused(self):
        """The observed digest survives the refusal, which is the whole point:
        run179075 exported a failure code and no observed bytes, and it took a
        separate operator diagnostic to learn what had actually been written."""
        fake, result = self.execute(bad_code=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["corrected_artifact"]["observed_sha256"], c.sha(c.CORRECTED.replace(b"* 3", b"* 4")))
        events = [c.decoded(line) for line in (self.root / "events.jsonl").read_bytes().splitlines()]
        seen = [e for e in events if e["event"] == "workspace-observed"]
        self.assertEqual([(e["turn"], e["entry_count"], e["expected_set"]) for e in seen], [(1, 1, True), (2, 2, True)])
        # Entry COUNTS, never provider-chosen names.
        self.assertEqual(set(seen[0]) , {"event", "monotonic_ns", "turn", "entry_count", "expected_set"})

    # -- owner179142: the model diagnostics reach the export ----------------

    def test_the_export_carries_why_a_model_did_not_qualify(self):
        _, result = self.execute(usage={"some-other-model": {}})
        self.assertEqual(result["outcome"], "not-qualified")
        terminal = result["arms"][0]["terminal"]
        self.assertIsNone(terminal["actual_model"])
        self.assertEqual(terminal["model_diagnostic"], "missing")
        self.assertEqual(terminal["model_usage_diagnostic"], "other-only")
        self.assertEqual((terminal["model_usage_keys"], terminal["model_usage_keys_capped"], terminal["model_usage_expected_key"]), (1, False, False))
        self.assertNotIn(b"some-other-model", c.encoded(result))

    def forged(self, **patch):
        """Start from the coherent record this fixture actually produces, change
        exactly one thing, and drive it through the real arm."""
        self.setUp()
        fake, result = self.execute(forged_terminal=patch)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["failure_code"], "terminal-record-values")
        # FIRST ARM, before restoration or a second turn.
        self.assertEqual(len(fake.containers), 1)
        self.assertEqual(result["stage"], "first-turn")
        self.assertNotIn("promoted", result)
        return result

    def test_contradictory_cardinality_is_refused_at_the_arm(self):
        """R1, review 2026-09-15T15-39-27Z. Each of these reached `qualified`
        with `consistent=true` before the correction: a singleton reporting two
        keys, a singleton reporting eight and overflow, overflow at one key."""
        self.forged(model_usage_keys=2)
        self.forged(model_usage_keys=8, model_usage_keys_capped=True)
        self.forged(model_usage_keys_capped=True)
        self.forged(model_usage_diagnostic="empty-object", model_usage_keys=0, model_usage_keys_capped=True,
                    model_usage_expected_key=False, model_fields=[], actual_model=None)
        self.forged(model_usage_diagnostic="expected-plus-other", model_usage_keys=1,
                    model_fields=[], actual_model=None)
        self.forged(model_usage_diagnostic="other-only", model_usage_keys=1, model_usage_keys_capped=True,
                    model_usage_expected_key=False, model_fields=[], actual_model=None)
        # A valid boolean in the wrong place, which the identity check alone
        # does not catch.
        self.forged(model_usage_expected_key=False)

    def test_a_diagnostic_about_an_absent_member_is_refused_at_the_arm(self):
        """The fourth reproduced record: `modelUsage` reported as the singleton
        that supplied the model, while the closed member list says the provider
        never sent that field at all."""
        self.forged(members=["is_error", "session_id", "subtype", "type"])
        self.forged(model_diagnostic="expected", model_fields=["model", "modelUsage"])
        # And the mirror: a member present but reported missing.
        self.forged(model_usage_diagnostic="missing", model_usage_keys=None,
                    model_usage_keys_capped=None, model_usage_expected_key=None,
                    model_fields=[], actual_model=None)

    def test_a_terminal_record_that_contradicts_its_own_diagnostics_refuses(self):
        """A forged or drifted record cannot claim a qualified model while its
        diagnostics report a conflict. This is the arm-level guard, not just a
        predicate."""
        for forged in ({"actual_model": c.ACTUAL_MODEL, "model_fields": ["modelUsage"], "model_usage_diagnostic": "other-only"},
                       {"model_usage_keys_capped": 1}, {"model_usage_keys": 99}, {"model_diagnostic": "invented"}):
            with self.subTest(forged=sorted(forged)):
                self.setUp()
                fake, result = self.execute(forged_terminal=forged)
                self.assertEqual(result["outcome"], "failed")
                self.assertEqual(result["failure_code"], "terminal-record-values")
                self.assertEqual(len(fake.containers), 1)


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


class TheArtifactAndModelCorrection(unittest.TestCase):
    """Owner179142, from review 2026-09-15T15-16-11Z.

    Two bounded decisions: `solution.py` is accepted with or without its one
    final LF, and the closed projection now records WHY a model did not
    qualify. Neither needs an engine, which is why they are checked here.
    """

    def setUp(self):
        self.session = str(uuid.uuid4())

    def result(self, **changes):
        value = dict(type="result", subtype="success", is_error=False, session_id=self.session)
        value.update(changes)
        return c.projection(c.encoded(value), self.session)

    # -- A: exactly two accepted forms --------------------------------------

    def test_both_constants_are_accepted_with_and_without_their_final_lf(self):
        for expected in (c.INITIAL, c.CORRECTED):
            with self.subTest(expected=expected):
                self.assertEqual(c.artifact_form(expected, expected), "exact")
                self.assertEqual(c.artifact_form(expected[:-1], expected), "missing-final-lf")
                self.assertIn(c.artifact_form(expected, expected), c.ARTIFACT_FORMS)
                self.assertIn(c.artifact_form(expected[:-1], expected), c.ARTIFACT_FORMS)

    def test_the_relaxation_is_exactly_one_newline_wide(self):
        """Every one of these was legal under no reading of the selection, and
        each is a way a run could otherwise have been made to pass."""
        for label, raw in (
                ("extra final lf", c.INITIAL + b"\n"),
                ("two extra lf", c.INITIAL + b"\n\n"),
                ("leading newline", b"\n" + c.INITIAL),
                ("leading space", b" " + c.INITIAL),
                ("trailing space", c.INITIAL[:-1] + b" \n"),
                ("trailing space, no lf", c.INITIAL[:-1] + b" "),
                ("crlf", c.INITIAL.replace(b"\n", b"\r\n")),
                ("crlf, no final lf", c.INITIAL.replace(b"\n", b"\r\n")[:-2]),
                ("altered indentation", c.INITIAL.replace(b"    ", b"  ")),
                ("tab indentation", c.INITIAL.replace(b"    ", b"\t")),
                ("altered multiplier", c.INITIAL.replace(b"* 2", b"* 3")),
                ("added comment", b"# generated\n" + c.INITIAL),
                ("trailing comment", c.INITIAL + b"# done\n"),
                ("spaces around operator", c.INITIAL.replace(b"* 2", b"*2")),
                ("empty", b""),
                ("interior lf removed", c.INITIAL.replace(b":\n", b":")),
                ("doubled", c.INITIAL + c.INITIAL)):
            with self.subTest(label=label):
                self.assertEqual(c.artifact_form(raw, c.INITIAL), "mismatch")
                self.assertNotIn("mismatch", c.ARTIFACT_FORMS)

    def test_no_strip_or_normalization_was_introduced(self):
        """Source-level, because the excluded implementations are the risk: a
        later `strip()` would pass every case above and look like a tidy-up."""
        import inspect

        text = inspect.getsource(c.artifact_form)
        body = text.split('"""')[2]
        for banned in (".strip(", ".rstrip(", ".lstrip(", "normalize", "replace(", "splitlines", "decode("):
            self.assertNotIn(banned, body, banned)

    def test_the_observed_digest_is_the_providers_and_the_expected_one_is_ours(self):
        record = c.artifact_record(c.INITIAL[:-1], c.INITIAL)
        self.assertEqual(record, {"form": "missing-final-lf", "observed_sha256": c.sha(c.INITIAL[:-1]),
                                  "observed_bytes": 38, "expected_sha256": c.sha(c.INITIAL), "expected_bytes": 39})
        # The retained diagnostic's 38-byte regular file, reproduced from the
        # public constants alone: 39 expected, 38 observed, one final LF.
        self.assertEqual((len(c.INITIAL), len(c.INITIAL.strip())), (39, 38))
        self.assertEqual(c.artifact_record(b"", c.INITIAL)["form"], "mismatch")

    def test_the_token_record_carries_no_digest_of_the_private_token(self):
        token = uuid.uuid4().hex
        record = c.token_record((token + "\n").encode(), (token + "\n").encode())
        self.assertEqual(record, {"form": "exact", "observed_bytes": 33, "expected_bytes": 33})
        export = c.encoded(record)
        self.assertNotIn(token.encode(), export)
        self.assertNotIn(c.sha((token + "\n").encode()).encode(), export)
        self.assertEqual(c.token_record(token.encode(), (token + "\n").encode())["form"], "mismatch")

    def test_the_prompts_delimit_the_bytes_and_state_the_optional_newline(self):
        """Wording is not acceptance -- a prompt cannot guarantee compliance --
        but the old text ran the expected bytes into the next sentence, which
        left the boundary to be inferred."""
        first, second = c.prompt(1, "a" * 32), c.prompt(2)
        for turn, text, expected in ((1, first, c.INITIAL), (2, second, c.CORRECTED)):
            with self.subTest(turn=turn):
                self.assertIn("<<<BEGIN>>>\n" + expected.decode() + "<<<END>>>\n", text)
                self.assertIn("a final newline after the last line is optional", text)
        self.assertIn("followed by one newline character", second)
        self.assertNotIn("<<<BEGIN>>>", first.split("<<<BEGIN>>>", 1)[1].split("<<<END>>>", 1)[1])

    # -- B: why a model did not qualify, never which one --------------------

    def test_every_observed_model_shape_has_its_own_diagnosis(self):
        cases = {
            "absent": ({}, "missing", "missing", (None, None, None)),
            "expected both": ({"model": c.ACTUAL_MODEL, "modelUsage": {c.ACTUAL_MODEL: {}}}, "expected", "expected-only", (1, False, True)),
            "model wrong type": ({"model": ["x"]}, "wrong-type", "missing", (None, None, None)),
            "model null": ({"model": None}, "wrong-type", "missing", (None, None, None)),
            "model other string": ({"model": "another-model"}, "other-string", "missing", (None, None, None)),
            "usage wrong type": ({"modelUsage": ["x"]}, "missing", "wrong-type", (None, None, None)),
            "usage null": ({"modelUsage": None}, "missing", "wrong-type", (None, None, None)),
            "usage empty": ({"modelUsage": {}}, "missing", "empty-object", (0, False, False)),
            "usage other singleton": ({"modelUsage": {"another-model": {}}}, "missing", "other-only", (1, False, False)),
            "usage several others": ({"modelUsage": {"a": {}, "b": {}}}, "missing", "other-only", (2, False, False)),
            "usage mixed": ({"modelUsage": {c.ACTUAL_MODEL: {}, "a": {}}}, "missing", "expected-plus-other", (2, False, True)),
        }
        for label, (changes, model, usage, counts) in cases.items():
            with self.subTest(label=label):
                record = self.result(**changes)
                self.assertEqual(record["model_diagnostic"], model)
                self.assertEqual(record["model_usage_diagnostic"], usage)
                self.assertEqual((record["model_usage_keys"], record["model_usage_keys_capped"], record["model_usage_expected_key"]), counts)
                self.assertTrue(c.consistent(record))

    def test_the_four_possibilities_run179075_could_not_tell_apart_are_now_distinct(self):
        """THE POINT OF PART B. That export reported `actual_model: null` and
        `model_fields: []` with `modelUsage` present, and nothing in it could
        say whether the member was a non-object, an empty object, one other key
        or several. The raw provider document was never retained, so no later
        inspection can recover the distinction -- only the next run can."""
        shapes = [["x"], {}, {"another-model": {}}, {"a": {}, "b": {}}]
        records = [self.result(modelUsage=shape) for shape in shapes]
        self.assertEqual([(r["actual_model"], r["model_fields"]) for r in records], [(None, [])] * 4,
                         "the old projection was already identical for all four")
        # ONE AND SEVERAL OTHER KEYS SHARE `other-only` ON PURPOSE -- naming a
        # cardinality class would not say which -- so the bounded count is what
        # separates them, and the diagnosis is the pair.
        diagnoses = [(r["model_usage_diagnostic"], r["model_usage_keys"]) for r in records]
        self.assertEqual(diagnoses, [("wrong-type", None), ("empty-object", 0), ("other-only", 1), ("other-only", 2)])
        self.assertEqual(len(set(diagnoses)), 4)
        self.assertTrue(all("modelUsage" in r["members"] for r in records))

    def test_acceptance_did_not_move_a_single_case(self):
        """The diagnostics explain; they do not qualify. A mixed object holding
        the expected key, and a matching `--model` argument, both still fail."""
        self.assertEqual(self.result(model=c.ACTUAL_MODEL)["actual_model"], c.ACTUAL_MODEL)
        self.assertEqual(self.result(modelUsage={c.ACTUAL_MODEL: {}})["actual_model"], c.ACTUAL_MODEL)
        for changes in ({}, {"model": None}, {"model": "another-model"}, {"modelUsage": {}}, {"modelUsage": ["x"]},
                        {"modelUsage": {"another-model": {}}}, {"modelUsage": {c.ACTUAL_MODEL: {}, "a": {}}},
                        {"model": "another-model", "modelUsage": {c.ACTUAL_MODEL: {}}},
                        {"model": c.ACTUAL_MODEL, "modelUsage": {"another-model": {}}}):
            with self.subTest(changes=sorted(changes)):
                record = self.result(**changes)
                self.assertIsNone(record["actual_model"])
                self.assertTrue(c.consistent(record))
        self.assertIn(c.ACTUAL_MODEL, c.MODEL, "the CLI argument alone never qualified a model")

    def test_key_counts_are_bounded_with_an_explicit_overflow_flag(self):
        for count, reported, capped in ((3, 3, False), (c.MODEL_KEY_CAP, c.MODEL_KEY_CAP, False), (c.MODEL_KEY_CAP + 5, c.MODEL_KEY_CAP, True)):
            with self.subTest(count=count):
                record = self.result(modelUsage={"key-%d" % i: {} for i in range(count)})
                self.assertEqual((record["model_usage_keys"], record["model_usage_keys_capped"]), (reported, capped))
                self.assertTrue(c.consistent(record))

    def test_no_model_name_value_or_payload_ever_reaches_the_export(self):
        sentinel = "PRIVATE-MODEL-NEVER-EXPORT"
        record = self.result(model=sentinel, modelUsage={sentinel: {"prose": sentinel, "inputTokens": 1234567}})
        export = c.encoded(record)
        self.assertNotIn(sentinel.encode(), export)
        self.assertNotIn(b"1234567", export)
        self.assertNotIn(b"prose", export)
        self.assertEqual(record["model_diagnostic"], "other-string")
        self.assertEqual(record["model_usage_diagnostic"], "other-only")
        self.assertIsNone(record["actual_model"])

    def usage(self, keys, expected):
        names = ([c.ACTUAL_MODEL] if expected else []) + ["other-%d" % i for i in range(keys - (1 if expected else 0))]
        assert len(names) == keys
        return self.result(modelUsage={name: {} for name in names})

    def test_every_shape_reports_exactly_the_cardinality_it_can_have(self):
        """0/1/2/8/9 keys, with and without the expected key, plus absent and
        wrong-type. 8 is the cap reached exactly and NOT overflow; 9 is clamped
        to 8 and flagged."""
        table = {
            (0, False): ("empty-object", 0, False, False),
            (1, False): ("other-only", 1, False, False),
            (1, True): ("expected-only", 1, False, True),
            (2, False): ("other-only", 2, False, False),
            (2, True): ("expected-plus-other", 2, False, True),
            (8, False): ("other-only", 8, False, False),
            (8, True): ("expected-plus-other", 8, False, True),
            (9, False): ("other-only", 8, True, False),
            (9, True): ("expected-plus-other", 8, True, True),
        }
        for (keys, expected), want in table.items():
            with self.subTest(keys=keys, expected=expected):
                record = self.usage(keys, expected)
                self.assertEqual((record["model_usage_diagnostic"], record["model_usage_keys"],
                                  record["model_usage_keys_capped"], record["model_usage_expected_key"]), want)
                self.assertTrue(c.consistent(record))
                # ONLY the lone expected key qualifies; the rest are diagnoses.
                self.assertEqual(record["actual_model"], c.ACTUAL_MODEL if (keys, expected) == (1, True) else None)
        for label, changes in (("absent", {}), ("wrong-type", {"modelUsage": ["x"]})):
            with self.subTest(label=label):
                record = self.result(**changes)
                self.assertEqual((record["model_usage_keys"], record["model_usage_keys_capped"],
                                  record["model_usage_expected_key"]), (None, None, None))
                self.assertTrue(c.consistent(record))

    def test_a_shape_cannot_claim_a_cardinality_it_excludes(self):
        """The R1 defect, held directly. The old guard checked that each member
        had the right TYPE and RANGE and never asked whether they agreed."""
        for keys, expected, bad in (
                (1, True, {"model_usage_keys": 0}),
                (1, True, {"model_usage_keys": 2}),
                (1, True, {"model_usage_keys": c.MODEL_KEY_CAP}),
                (0, False, {"model_usage_keys": 1}),
                (2, True, {"model_usage_keys": 1}),
                (1, False, {"model_usage_keys": 0}),
                (2, False, {"model_usage_keys": 0})):
            with self.subTest(keys=keys, expected=expected, bad=bad):
                self.assertFalse(c.consistent({**self.usage(keys, expected), **bad}))

    def test_the_expected_key_flag_must_match_its_shape(self):
        """A valid boolean in the wrong place. The identity check catches `1`;
        only this catches `False` where the shape says `True` -- and without it
        a record could name the expected key as present in one member and
        absent in the next."""
        for keys, expected in ((0, False), (1, False), (1, True), (2, False), (2, True), (9, False), (9, True)):
            with self.subTest(keys=keys, expected=expected):
                record = self.usage(keys, expected)
                flipped = not record["model_usage_expected_key"]
                self.assertFalse(c.consistent({**record, "model_usage_expected_key": flipped}))
        # And through the real arm.
        self.assertTrue(c.consistent(self.usage(1, True)))

    def test_overflow_belongs_only_to_the_shapes_that_can_overflow(self):
        """`capped` means the count was CLAMPED, so it can only appear at the
        cap and only where more keys than the cap are possible. A singleton or
        an empty object claiming overflow is a contradiction."""
        for keys, expected in ((9, False), (9, True)):
            self.assertTrue(c.consistent(self.usage(keys, expected)))
        for keys, expected in ((1, True), (0, False), (1, False), (2, True)):
            with self.subTest(keys=keys, expected=expected):
                self.assertFalse(c.consistent({**self.usage(keys, expected), "model_usage_keys_capped": True}))
        # At the cap but not clamped is valid; below the cap and clamped is not.
        for keys in (1, 2, c.MODEL_KEY_CAP - 1):
            with self.subTest(keys=keys):
                self.assertFalse(c.consistent({**self.usage(9, False), "model_usage_keys": keys}))
        self.assertIn("other-only", c.OVERFLOW_SHAPES)
        self.assertIn("expected-plus-other", c.OVERFLOW_SHAPES)
        self.assertEqual(len(c.OVERFLOW_SHAPES), 2)

    def test_a_diagnostic_about_an_absent_member_is_a_contradiction(self):
        """`missing` means the known member was absent and every other
        diagnostic means it was present -- for both fields. Without this a
        record could claim a field the provider never sent supplied the model."""
        present = self.usage(1, True)
        self.assertIn("modelUsage", present["members"])
        self.assertFalse(c.consistent({**present, "members": [m for m in present["members"] if m != "modelUsage"]}))
        absent = self.result()
        self.assertNotIn("modelUsage", absent["members"])
        self.assertNotIn("model", absent["members"])
        for bad in ({"model_usage_diagnostic": "wrong-type"},
                    {"model_diagnostic": "wrong-type"},
                    {"model_diagnostic": "other-string"},
                    {"model_diagnostic": "expected", "model_fields": ["model"], "actual_model": c.ACTUAL_MODEL}):
            with self.subTest(bad=sorted(bad)):
                self.assertFalse(c.consistent({**absent, **bad}))
        # And the mirror, on the real record: present but reported missing.
        named = self.result(model="another-model")
        self.assertIn("model", named["members"])
        self.assertFalse(c.consistent({**named, "model_diagnostic": "missing"}))

    def test_the_shape_table_covers_the_whole_declared_vocabulary(self):
        """The validator is a table; a diagnostic added to the vocabulary
        without a row would otherwise be silently unvalidatable."""
        self.assertEqual(set(c.USAGE_SHAPES), set(c.MODEL_USAGE_DIAGNOSTICS))
        self.assertTrue(c.OVERFLOW_SHAPES < set(c.MODEL_USAGE_DIAGNOSTICS))
        for name, shape in c.USAGE_SHAPES.items():
            with self.subTest(name=name):
                self.assertEqual(set(shape), {"member", "expected_key", "low", "high"})
                if shape["low"] is None:
                    self.assertIsNone(shape["high"])
                    self.assertIsNone(shape["expected_key"])
                else:
                    self.assertLessEqual(shape["low"], shape["high"])
                    self.assertLessEqual(shape["high"], c.MODEL_KEY_CAP)
                    self.assertIs(shape["member"], True)
                self.assertIs(c.consistent({"members": [], "model_fields": [], "actual_model": None,
                                            "model_diagnostic": "missing", "model_usage_diagnostic": "invented",
                                            "model_usage_keys": None, "model_usage_keys_capped": None,
                                            "model_usage_expected_key": None}), False)

    def test_malformed_container_types_are_refused(self):
        record = self.usage(1, True)
        for key, value in (("members", "modelUsage"), ("members", None), ("model_fields", "modelUsage"),
                           ("model_fields", None), ("model_fields", ["model", "invented"]),
                           ("actual_model", "another-model")):
            with self.subTest(key=key, value=value):
                self.assertFalse(c.consistent({**record, key: value}))

    def test_a_truthy_integer_is_not_a_boolean(self):
        """`1 in (None, True, False)` is true in Python, so the validation is
        identity-based. A record substituting 1 for True must not pass."""
        record = self.result(modelUsage={c.ACTUAL_MODEL: {}})
        self.assertTrue(c.consistent(record))
        for key, value in (("model_usage_keys_capped", 0), ("model_usage_keys_capped", 1), ("model_usage_expected_key", 1),
                           ("model_usage_keys", True), ("model_usage_keys", "1"), ("model_usage_keys", c.MODEL_KEY_CAP + 1),
                           ("model_usage_keys", -1), ("model_diagnostic", "invented"), ("model_usage_diagnostic", "invented")):
            with self.subTest(key=key, value=value):
                self.assertFalse(c.consistent({**record, key: value}))

    def test_absent_object_fields_must_stay_absent(self):
        """Wrong-type and missing `modelUsage` get neither invented keys nor
        invented counts."""
        for changes in ({}, {"modelUsage": ["x"]}):
            record = self.result(**changes)
            for key in ("model_usage_keys", "model_usage_keys_capped", "model_usage_expected_key"):
                with self.subTest(changes=sorted(changes), key=key):
                    self.assertIsNone(record[key])
                    self.assertFalse(c.consistent({**record, key: 0}))
                    self.assertFalse(c.consistent({**record, key: False}))


class TheFreshRunIdentity(unittest.TestCase):
    """Owner 2026-09-15T18:04:42Z. The 178579 identity was CONSUMED by the failed
    operator run179075 and is not reusable -- the fixture refuses a taken root
    rather than repairing it, so a rerun needs a new name, not a reset marker.
    """

    def test_the_identity_is_not_the_consumed_one(self):
        self.assertEqual(REAL_IDENTITY, "180078")
        self.assertNotEqual(REAL_IDENTITY, CONSUMED_IDENTITY)
        for place in (REAL_ROOT, REAL_VOLATILE, fixture.export_root()):
            with self.subTest(place=str(place)):
                self.assertNotIn(CONSUMED_IDENTITY, str(place))
                self.assertTrue(str(place).endswith(REAL_IDENTITY) or str(place).endswith(REAL_IDENTITY + "-export"))

    def test_the_three_roots_are_one_identity_and_distinct(self):
        roots = [REAL_ROOT, REAL_VOLATILE, fixture.export_root()]
        self.assertEqual(len(set(map(str, roots))), 3)
        for place in roots:
            self.assertIn(REAL_IDENTITY, str(place))
        self.assertEqual(str(fixture.export_root()), str(REAL_ROOT) + "-export")
        self.assertEqual((str(REAL_ROOT), str(REAL_VOLATILE)),
                         ("/tmp/baton-w177936-qualification-180078", "/dev/shm/baton-w177936-qualification-180078"))

    def test_the_export_root_is_derived_in_exactly_one_place(self):
        """A second copy of the derivation is how the declared export root and
        the reserved one would drift apart."""
        import inspect

        text = inspect.getsource(fixture)
        self.assertEqual(text.count('with_name(ROOT.name + "-export")'), 1)
        self.assertIn("EXPORT = export_root()", inspect.getsource(fixture.run))
        self.assertIn("export_root()", inspect.getsource(fixture.audit))

    def test_the_export_root_follows_a_patched_root(self):
        """Tests patch ROOT to a temporary directory; the derived export root
        must follow it rather than staying pinned to the real identity."""
        with tempfile.TemporaryDirectory(prefix="w177936-identity-") as place:
            moved = Path(place) / "run"
            with mock.patch.object(fixture, "ROOT", moved):
                self.assertEqual(fixture.export_root(), moved.with_name("run-export"))

    def test_the_manifest_declares_exactly_the_roots_the_code_would_take(self):
        """Without this the manifest's root fields are decorative: an approved
        manifest could name one identity while the fixture reserved another and
        the digest would still verify."""
        manifest = c.decoded(c.read_file(HERE / "qualification-manifest.json", 256 * 1024))
        self.assertEqual(manifest["run_identity"], REAL_IDENTITY)
        self.assertEqual(manifest["private_root"], str(REAL_ROOT))
        self.assertEqual(manifest["credential_copy_root"], str(REAL_VOLATILE))
        self.assertEqual(manifest["export_root"], str(fixture.export_root()))
        self.assertEqual(manifest["consumed_identity"]["identity"], CONSUMED_IDENTITY)

    def test_a_manifest_naming_another_identity_is_refused(self):
        """Each declared root on its own, plus the identity string."""
        for field in ("run_identity", "private_root", "credential_copy_root", "export_root"):
            with self.subTest(field=field), tempfile.TemporaryDirectory(prefix="w177936-manifest-") as place:
                copy = Path(place)
                for name in ("qualification-fixture.py", "qualification_contract.py",
                             "qualification_worker.py", "test_qualification.py"):
                    shutil.copy2(HERE / name, copy / name)
                manifest = c.decoded(c.read_file(HERE / "qualification-manifest.json", 256 * 1024))
                manifest[field] = manifest[field].replace(REAL_IDENTITY, CONSUMED_IDENTITY)
                (copy / "qualification-manifest.json").write_bytes(c.encoded(manifest))
                with mock.patch.object(fixture, "MANIFEST", copy / "qualification-manifest.json"), \
                        mock.patch.object(fixture, "HERE", copy), \
                        mock.patch.object(fixture, "engine", side_effect=AssertionError("engine")), \
                        mock.patch.object(fixture, "credential", side_effect=AssertionError("credential")), \
                        mock.patch.object(fixture, "ROOT", REAL_ROOT), mock.patch.object(fixture, "VOLATILE", REAL_VOLATILE), \
                        self.assertRaises(c.Refusal) as raised:
                    fixture.audit()
                self.assertEqual(c.failure_code(raised.exception), "manifest-constants")

    def test_the_consumed_roots_are_never_addressable_by_the_running_code(self):
        """Preservation is the point: no run can reach, repair or reset the
        consumed markers, because nothing executable can name them.

        Comments are stripped and everything else kept, so a prose reference to
        the old identity is allowed and a string literal or expression that
        could BUILD one of its paths is not. Asserting over the raw source
        would only have banned explaining the history."""
        import io
        import tokenize

        def executable(module):
            source = inspect.getsource(module)
            return "".join("" if kind == tokenize.COMMENT else text
                           for kind, text, _, _, _ in tokenize.generate_tokens(io.StringIO(source).readline))

        for module in (fixture, c):
            with self.subTest(module=module.__name__):
                self.assertNotIn(CONSUMED_IDENTITY, executable(module))
        # And the history is still explained -- in a comment, where it cannot run.
        self.assertIn(CONSUMED_IDENTITY, inspect.getsource(fixture))


class TheCollectionCustodyCorrection(unittest.TestCase):
    """CORRECTION-PROPOSAL-180537.md revision 2, selected by owner182261.

    The operator walk found runtime-owned 0o700/0o600 state that excludes the
    host collector: setgid gave group OWNERSHIP and never group PERMISSION BITS.
    Mode 0o000 stands in for that here, because this process owns its synthetic
    tree and only a zeroed owner triad denies it.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w177936-custody-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.session = str(uuid.uuid4())
        self.projects = self.home / ".claude/projects"
        (self.projects / "observed-key").mkdir(parents=True)
        self.state = self.projects / "observed-key" / (self.session + ".jsonl")
        self.state.write_bytes(b"synthetic private session")
        (self.home / ".claude/.credentials.json").symlink_to(c.SLOT)
        for patch in (mock.patch.object(c, "HOME", str(self.home)),
                      mock.patch.object(c, "GROUP", os.getgid())):
            patch.start()
            self.addCleanup(patch.stop)

    def unreadable(self, place):
        os.chmod(place, 0o000)
        self.addCleanup(os.chmod, place, 0o755 if place.is_dir() else 0o644)

    def modes(self):
        return {str(p.relative_to(self.home)): stat.S_IMODE(p.lstat().st_mode)
                for p in sorted(self.home.rglob("*"))}

    # -- P1a: turn 1 only, runtime-owned only, verified through the descriptor --

    def test_turn_one_opens_exactly_two_objects(self):
        os.chmod(self.projects / "observed-key", 0o700)
        os.chmod(self.state, 0o600)
        before = self.modes()
        published = worker.publish(self.session, 1)
        self.assertEqual(published, {"project_mode": "0o2750", "session_mode": "0o640"})
        after = self.modes()
        changed = {k for k in after if after[k] != before[k]}
        self.assertEqual(changed, {".claude/projects/observed-key",
                                   ".claude/projects/observed-key/" + self.session + ".jsonl"})
        self.assertEqual(after[".claude/projects/observed-key"], 0o2750)
        self.assertEqual(after[".claude/projects/observed-key/" + self.session + ".jsonl"], 0o640)

    def test_turn_two_publishes_nothing_and_the_restored_copy_stands(self):
        """THE D2 REGRESSION TEST. Revision 1 of the proposal aimed a chmod at
        the manager-owned 0o660 restored working copy accepted at R1/178875."""
        restored = self.projects / "observed-key" / (self.session + ".jsonl")
        os.chmod(restored, 0o660)
        before = self.modes()
        self.assertIsNone(worker.publish(self.session, 2))
        self.assertEqual(self.modes(), before)
        self.assertEqual(stat.S_IMODE(restored.lstat().st_mode), 0o660)

    def test_a_manager_owned_object_refuses_and_changes_nothing(self):
        """Ownership is checked through the descriptor that would be changed."""
        before = self.modes()
        with mock.patch.object(c, "GROUP", os.getgid() + 1), self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-ownership")
        self.assertEqual(self.modes(), before)

    def test_a_symlink_in_either_position_refuses(self):
        for name in ("directory", "file"):
            with self.subTest(position=name):
                self.setUp()
                if name == "directory":
                    shutil.rmtree(self.projects / "observed-key")
                    (self.root / "decoy").mkdir()
                    (self.projects / "observed-key").symlink_to(self.root / "decoy")
                else:
                    self.state.unlink()
                    (self.root / "decoy.jsonl").write_bytes(b"x")
                    self.state.symlink_to(self.root / "decoy.jsonl")
                with self.assertRaises(c.Refusal) as raised:
                    worker.publish(self.session, 1)
                self.assertIn(c.failure_code(raised.exception), ("publish-type", "publish-shape"))

    def test_an_ambiguous_or_missing_selection_refuses_and_relaxes_nothing(self):
        for label, action in (("second project", lambda: (self.projects / "other-key").mkdir()),
                              ("missing session", lambda: self.state.unlink())):
            with self.subTest(label=label):
                self.setUp()
                os.chmod(self.projects / "observed-key", 0o700)
                action()
                before = self.modes()
                with self.assertRaises(c.Refusal) as raised:
                    worker.publish(self.session, 1)
                self.assertIn(c.failure_code(raised.exception), ("publish-shape", "publish-type"))
                self.assertEqual(self.modes(), before)

    # -- R1: the no-follow chain, not just the final component ---------------

    def outside(self):
        """A decoy tree outside HOME, with modes recorded so a refusal can be
        proved to have changed nothing there."""
        place = self.root / "outside"
        (place / "a-project").mkdir(parents=True)
        victim = place / "a-project" / (self.session + ".jsonl")
        victim.write_bytes(b"outside the home")
        os.chmod(place / "a-project", 0o700)
        os.chmod(victim, 0o600)
        return place, victim

    def test_a_symlinked_ancestor_cannot_reach_outside_the_home(self):
        """R1's first observation: O_NOFOLLOW on the final component leaves the
        PATH unprotected, and a symlinked `.claude/projects` published an object
        outside HOME entirely."""
        place, victim = self.outside()
        shutil.rmtree(self.home / ".claude/projects")
        (self.home / ".claude/projects").symlink_to(place)
        with self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertIn(c.failure_code(raised.exception), ("publish-type", "publish-shape"))
        self.assertEqual(stat.S_IMODE(victim.lstat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((place / "a-project").lstat().st_mode), 0o700)

    def test_a_swap_between_check_and_open_cannot_redirect_the_change(self):
        """R1's race: the session used to be reopened by PATHNAME after its
        directory had been verified, so a rename-and-replace landed the chmod on
        an unrelated decoy. Every child is now opened relative to its verified
        parent descriptor."""
        place, victim = self.outside()
        real = self.projects / "observed-key"
        os.chmod(real, 0o700)
        os.chmod(self.state, 0o600)
        original = os.listdir

        def swap(where):
            names = original(where)
            if real.exists() and not real.is_symlink():
                real.rename(self.root / "moved")
                real.symlink_to(place / "a-project")
            return names

        with mock.patch.object(os, "listdir", swap), self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertIn(c.failure_code(raised.exception), ("publish-type", "publish-shape"))
        self.assertEqual(stat.S_IMODE(victim.lstat().st_mode), 0o600)

    def test_a_type_swapped_after_its_check_cannot_be_followed(self):
        """What O_NOFOLLOW is actually for, now that lstat screens types first.
        The probe that reverted it passed, which meant nothing PROVED it
        load-bearing: lstat rejects a symlink before the open is reached. It
        still matters in the gap between them, so lstat is made to report a
        directory for an entry that is really a link out of the home."""
        place, victim = self.outside()
        (self.home / "sneaky").symlink_to(place)
        honest = os.lstat

        def lying(where, *arguments, **keywords):
            info = honest(where, *arguments, **keywords)
            if where == "sneaky":
                return os.stat_result((stat.S_IFDIR | 0o755,) + tuple(info)[1:])
            return info

        with mock.patch.object(os, "lstat", lying), self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-type")
        self.assertEqual(stat.S_IMODE(victim.lstat().st_mode), 0o600)

    def test_a_hardlinked_session_refuses_before_any_mode_change(self):
        """R1's alias: a chmod reaches every link, and the manager's later
        hardlink refusal cannot undo a mode change that already happened."""
        alias = self.root / "alias.jsonl"
        os.link(self.state, alias)
        os.chmod(self.projects / "observed-key", 0o700)
        os.chmod(self.state, 0o600)
        before = self.modes()
        with self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-alias")
        self.assertEqual(self.modes(), before)
        self.assertEqual(stat.S_IMODE(alias.lstat().st_mode), 0o600)

    def test_a_special_file_substitution_cannot_hang_the_open(self):
        """O_NONBLOCK: a FIFO where the session is expected would otherwise
        block in `open` before `fstat` could reject it."""
        self.state.unlink()
        os.mkfifo(self.state)
        with self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-type")

    def test_a_decoy_swapped_in_at_the_end_of_the_survey_is_not_reached(self):
        """R1's remaining hole, review 2026-09-16T02-11-27Z. The survey used to
        walk descriptors and then REOPEN the targets by path, so replacing the
        project directory with a regular decoy after the walk redirected the
        chmod onto an unsurveyed file while the original kept its mode.
        Verifying a descriptor is worthless if it is not the one you change."""
        decoy = self.root / "decoy.jsonl"
        decoy.write_bytes(b"never surveyed")
        os.chmod(decoy, 0o600)
        real = self.projects / "observed-key"
        os.chmod(real, 0o700)
        os.chmod(self.state, 0o600)
        original = os.listdir
        swapped = {"done": False}

        def swap(where):
            names = original(where)
            # After the project directory has been surveyed, put a regular file
            # in its place.
            if not swapped["done"] and (self.session + ".jsonl") in names:
                swapped["done"] = True
                shutil.rmtree(real)
                shutil.copy2(decoy, real)
            return names

        with mock.patch.object(os, "listdir", swap), self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-shape")
        self.assertTrue(swapped["done"], "the swap did not fire")
        # The unsurveyed decoy now standing in the project's place was never
        # touched, and the file the swap replaced is gone rather than relaxed.
        self.assertEqual(stat.S_IMODE(decoy.lstat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(real.lstat().st_mode), 0o600)

    # -- R2: every forbidden layout refuses BEFORE any mode change -----------

    def test_forbidden_layouts_refuse_and_change_nothing(self):
        """R2. Each of these used to publish and move the selected file
        0600->0640 before anything refused it."""
        cases = {
            "foreign session": lambda: (self.projects / "observed-key" / (str(uuid.uuid4()) + ".jsonl")).write_bytes(b"x"),
            "nested session": lambda: ((self.projects / "observed-key/nested").mkdir(),
                                       (self.projects / "observed-key/nested" / (str(uuid.uuid4()) + ".jsonl")).write_bytes(b"x")),
            "credential-shaped entry": lambda: (self.home / "oauth-token").write_bytes(b"x"),
            # R2's remaining hole: the survey descended only the projects
            # chain, so neither of these was ever seen.
            "credential-shaped under a cache directory": lambda: (
                (self.home / "cache").mkdir(),
                (self.home / "cache/oauth-token").write_bytes(b"x")),
            "credential-shaped under .claude/cache": lambda: (
                (self.home / ".claude/cache").mkdir(),
                (self.home / ".claude/cache/api-key").write_bytes(b"x")),
            "deeply nested credential-shaped entry": lambda: (
                (self.home / "a/b/c").mkdir(parents=True),
                (self.home / "a/b/c/auth_token").write_bytes(b"x")),
            "second project": lambda: (self.projects / "other-key").mkdir(),
        }
        for label, make in cases.items():
            with self.subTest(label=label):
                self.setUp()
                os.chmod(self.projects / "observed-key", 0o700)
                os.chmod(self.state, 0o600)
                make()
                before = self.modes()
                with self.assertRaises(c.Refusal) as raised:
                    worker.publish(self.session, 1)
                self.assertEqual(c.failure_code(raised.exception), "publish-shape")
                self.assertEqual(self.modes(), before, label)
                self.assertEqual(stat.S_IMODE(self.state.lstat().st_mode), 0o600)

    def test_an_unselected_invalid_type_anywhere_refuses(self):
        """R2: the survey ignored types outside the projects chain, so an extra
        link or special file published before the manager's inventory -- which
        admits only directories and regular files -- could refuse it."""
        for label, make in (("stray symlink", lambda: (self.home / "elsewhere").symlink_to("/tmp")),
                            ("symlink in a cache directory", lambda: (
                                (self.home / "cache").mkdir(),
                                (self.home / "cache/link").symlink_to("/tmp"))),
                            ("fifo", lambda: os.mkfifo(self.home / "pipe"))):
            with self.subTest(label=label):
                self.setUp()
                os.chmod(self.projects / "observed-key", 0o700)
                os.chmod(self.state, 0o600)
                make()
                before = self.modes()
                with self.assertRaises(c.Refusal) as raised:
                    worker.publish(self.session, 1)
                self.assertIn(c.failure_code(raised.exception), ("publish-type", "publish-shape"))
                self.assertEqual(self.modes(), before, label)

    def test_a_wrong_uid_object_refuses_on_its_own(self):
        """The existing manager-owned test varies GID. Ownership is two
        conditions and each needs its own case."""
        os.chmod(self.projects / "observed-key", 0o700)
        before = self.modes()
        with mock.patch.object(os, "geteuid", return_value=os.geteuid() + 1), \
                self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-ownership")
        self.assertEqual(self.modes(), before)

    def test_the_expected_credential_link_is_checked_and_never_opened(self):
        """The one credential-shaped name that must survive the survey."""
        self.assertTrue((self.home / ".claude/.credentials.json").is_symlink())
        with mock.patch.object(c, "read_file", side_effect=AssertionError("opened")):
            self.assertEqual(worker.publish(self.session, 1),
                             {"project_mode": "0o2750", "session_mode": "0o640"})
        self.setUp()
        (self.home / ".claude/.credentials.json").unlink()
        (self.home / ".claude/.credentials.json").symlink_to("/elsewhere")
        with self.assertRaises(c.Refusal) as raised:
            worker.publish(self.session, 1)
        self.assertEqual(c.failure_code(raised.exception), "publish-shape")

    # -- P1b: unreadable content tolerated, unreadable structure refused -------

    def test_an_unreadable_non_selected_file_is_recorded_and_the_run_continues(self):
        noise = self.home / "irrelevant-cache"
        noise.write_bytes(b"private")
        self.unreadable(noise)
        rows = c.inventory(self.home)
        row = next(r for r in rows if r["path"] == "irrelevant-cache")
        self.assertEqual(row["content"], "unreadable:EACCES")
        self.assertIsNone(row["sha256"])
        # And the promoted set is untouched.
        chosen = c.subset(rows, self.session)
        self.assertEqual([r["path"] for r in chosen],
                         [".claude/projects/observed-key/" + self.session + ".jsonl"])

    def test_an_unreadable_selected_session_refuses(self):
        self.unreadable(self.state)
        rows = c.inventory(self.home)
        with self.assertRaises(c.Refusal) as raised:
            c.subset(rows, self.session)
        self.assertEqual(c.failure_code(raised.exception), "selected-session-unreadable")

    def test_an_unenterable_directory_refuses_rather_than_reporting_absence(self):
        """THE D1 REGRESSION TEST. The hidden directory CONTAINS a foreign
        session and a credential-shaped entry, so tolerating it would report
        foreign-session-state and unexpected-credential-entry as passed without
        having looked at the names those claims are about."""
        hidden = self.home / ".claude/hidden"
        hidden.mkdir()
        (hidden / (str(uuid.uuid4()) + ".jsonl")).write_bytes(b"a foreign session")
        (hidden / "oauth-token").write_bytes(b"a credential-shaped entry")
        self.unreadable(hidden)
        with self.assertRaises(c.Refusal) as raised:
            c.inventory(self.home)
        self.assertEqual(c.failure_code(raised.exception), "state-coverage-incomplete")

    def test_an_unstattable_entry_refuses_too(self):
        """A valid ADDITIONAL synthetic regression, not the observed operator
        result -- review-2026-09-16T00-41-09Z corrected me on that. The walk
        reported opendir:EACCES on a runtime-owned 0o700 directory. This covers
        the other seam: a 0o600 directory is READABLE, so scandir succeeds and
        every child's stat is what fails."""
        os.chmod(self.projects / "observed-key", 0o600)
        self.addCleanup(os.chmod, self.projects / "observed-key", 0o755)
        with self.assertRaises(c.Refusal) as raised:
            c.inventory(self.home)
        self.assertEqual(c.failure_code(raised.exception), "state-coverage-incomplete")

    def test_the_deliberate_exclusion_stays_distinguishable(self):
        (self.home / ".claude.json").write_bytes(b"not-to-be-read-configuration")
        rows = c.inventory(self.home)
        by_path = {r["path"]: r for r in rows}
        self.assertEqual(by_path[".claude.json"]["content"], "excluded")
        self.assertIsNone(by_path[".claude.json"]["sha256"])
        self.assertEqual(by_path[".claude/.credentials.json"]["content"], "excluded")
        selected = ".claude/projects/observed-key/" + self.session + ".jsonl"
        self.assertEqual(by_path[selected]["content"], "read")
        # Both leave sha256 None, which is exactly why `content` must be explicit.
        self.assertNotEqual(by_path[".claude.json"]["content"],
                            "unreadable:" + c.errno_category(None))

    # -- P1c: the closed failure triple ---------------------------------------

    def test_every_failure_kind_has_its_own_closed_category(self):
        cases = {
            "known-refusal": (c.Refusal("state-coverage-incomplete"), "none"),
            "wrapped-known-refusal": (c.wrapped("state-coverage-incomplete", errno.EIO), "none"),
            "unregistered-refusal": (c.Refusal("PRIVATE-TEXT"), "none"),
            "os-error": (PermissionError(13, "PRIVATE-MESSAGE"), "EACCES"),
            "other": (ValueError("PRIVATE-TEXT"), "none"),
        }
        self.assertEqual(c.failure_detail(c.wrapped("state-coverage-incomplete", errno.EIO))["cause"], "EIO")
        self.assertEqual(c.failure_detail(c.Refusal("state-coverage-incomplete"))["cause"], "none")
        for category, (error, expected_errno) in cases.items():
            with self.subTest(category=category):
                detail = {"step": "source-inventory", **c.failure_detail(error)}
                self.assertEqual(detail["category"], category.replace("wrapped-", ""))
                self.assertEqual(detail["errno"], expected_errno)
                self.assertTrue(c.valid_failure_detail(detail))
                self.assertNotIn("PRIVATE", json.dumps(detail))

    def test_an_unlisted_errno_collapses_and_a_refusal_never_carries_one(self):
        self.assertEqual(c.failure_detail(OSError(errno.EEXIST, "x"))["errno"], "other")
        self.assertEqual(c.errno_category(None), "none")
        self.assertFalse(c.valid_failure_detail(
            {"step": "state-copy", "category": "known-refusal", "errno": "EACCES"}))

    def test_the_projection_boundary_refuses_malformed_details(self):
        good = {"step": "state-copy", "category": "os-error", "errno": "EACCES", "cause": "none"}
        wrapped = {"step": "source-inventory", "category": "known-refusal", "errno": "none", "cause": "EACCES"}
        self.assertTrue(c.valid_failure_detail(good))
        self.assertTrue(c.valid_failure_detail(wrapped))
        self.assertTrue(c.valid_failure_detail({**good, "step": None}))
        for bad in ({**good, "step": "invented"}, {**good, "category": "invented"},
                    {**good, "errno": "EINVENTED"}, {**good, "cause": "EINVENTED"},
                    {"step": None, "category": "os-error", "errno": "none"},
                    {**good, "extra": 1}, "not-a-dict",
                    # Either relationship inverted describes a failure that did
                    # not happen: a refusal with its own errno, or an OS error
                    # that WRAPPED something.
                    {**wrapped, "errno": "EACCES"},
                    {**good, "cause": "EACCES"},
                    {**wrapped, "category": "unregistered-refusal"}):
            with self.subTest(bad=bad):
                self.assertFalse(c.valid_failure_detail(bad))

    def test_the_coverage_refusal_keeps_the_errno_it_was_raised_for(self):
        """R3, at the ACTUAL inventory seam and with different causes, so the
        field is shown to carry information rather than a constant."""
        for number, expected in ((errno.EACCES, "EACCES"), (errno.EIO, "EIO"), (errno.ENOENT, "ENOENT")):
            with self.subTest(errno=expected):
                with mock.patch.object(os, "scandir", side_effect=OSError(number, "CANARY-MESSAGE")), \
                        self.assertRaises(c.Refusal) as raised:
                    c.inventory(self.home)
                detail = {"step": "source-inventory", **c.failure_detail(raised.exception)}
                self.assertEqual(c.failure_code(raised.exception), "state-coverage-incomplete")
                self.assertEqual((detail["cause"], detail["errno"]), (expected, "none"))
                self.assertTrue(c.valid_failure_detail(detail))
                self.assertNotIn("CANARY", json.dumps(detail))

    def test_the_stat_seam_carries_its_cause_too(self):
        """Not mocked: a real 0o600 directory is READABLE, so scandir succeeds
        and each child's stat is what fails."""
        os.chmod(self.projects / "observed-key", 0o600)
        self.addCleanup(os.chmod, self.projects / "observed-key", 0o755)
        with self.assertRaises(c.Refusal) as raised:
            c.inventory(self.home)
        detail = {"step": "source-inventory", **c.failure_detail(raised.exception)}
        self.assertEqual(detail["cause"], "EACCES")
        self.assertTrue(c.valid_failure_detail(detail))

    def test_the_eight_steps_are_exactly_the_reviews(self):
        self.assertEqual(c.COLLECTION_STEPS,
                         ("source-inventory", "subset-selection", "private-layout-save", "destination-home",
                          "state-copy", "restored-inventory", "reconstruction-event", "restored-validation"))


class TheCorrectionEndToEnd(unittest.TestCase):
    """The whole point, through the real controller: what used to end as
    `unclassified` now either completes or names the step and errno.

    Composed from Controller's fixture rather than inheriting the class, which
    would have re-run its whole suite and inflated the count.
    """

    setUp = Controller.setUp
    execute = Controller.execute

    def test_the_published_home_is_collected_and_the_run_qualifies(self):
        fake, result = self.execute()
        self.assertEqual(result["outcome"], "qualified")
        self.assertEqual(result["arms"][0]["published"], {"project_mode": "0o2750", "session_mode": "0o640"})
        self.assertIsNone(result["arms"][1]["published"])
        self.assertNotIn("failure_detail", result)
        self.assertNotIn("collection_step", result)

    def test_an_unpublished_home_refuses_at_the_arm(self):
        fake, result = self.execute(skip_publish=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["failure_code"], "worker-observation")
        self.assertEqual(len(fake.containers), 1)

    def test_publishing_in_turn_two_refuses(self):
        """Turn 2's home is manager-reconstructed; a worker claiming to have
        relaxed it is reporting something that must not have happened."""
        fake, result = self.execute(publish_in_turn_two=True)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["failure_code"], "worker-observation")
        self.assertEqual(len(fake.containers), 2)

    def restore_blocked(self, fake):
        if fake.blocked is not None and fake.blocked.exists():
            os.chmod(fake.blocked, 0o755)

    # The selected eight-step x four-kind matrix, at the REAL operations.
    # Each seam is selected by what it is CALLED WITH rather than by how many
    # times it has been called: `save` and `inventory` are each used at several
    # steps, and an occurrence index would silently drift with the code.
    SEAMS = (
        ("source-inventory", c, "inventory", lambda a, k: str(a[0]).endswith("use-1/home")),
        ("subset-selection", c, "subset", lambda a, k: True),
        ("private-layout-save", fixture, "save", lambda a, k: a[0].name == "private-layout.json"),
        ("destination-home", fixture, "prepare_home", lambda a, k: a[1] == 2),
        ("state-copy", fixture, "private_file", lambda a, k: k.get("writable") is True),
        ("restored-inventory", c, "inventory", lambda a, k: str(a[0]).endswith("use-2/home")),
        ("reconstruction-event", fixture, "event", lambda a, k: a[1] == "subset-reconstructed"),
        ("restored-validation", c, "public_inventory", lambda a, k: True),
    )

    KINDS = (("known-refusal", lambda: c.Refusal("state-coverage-incomplete"), "none"),
             ("unregistered-refusal", lambda: c.Refusal("CANARY-CODE"), "none"),
             ("os-error", lambda: PermissionError(errno.EACCES, "CANARY-MESSAGE"), "none"),
             ("other", lambda: ValueError("CANARY-TEXT"), "none"))

    def inject(self, module, name, selects, make):
        """Fail one real operation, the first time it is called with the
        arguments belonging to the step under test."""
        original = getattr(module, name)
        fired = {"done": False}

        def failing(*arguments, **keywords):
            if not fired["done"] and selects(arguments, keywords):
                fired["done"] = True
                raise make()
            return original(*arguments, **keywords)

        return mock.patch.object(module, name, failing)

    def test_every_collection_step_reports_its_own_closed_triple(self):
        """Not a vocabulary assertion: each failure is injected at the actual
        operation and the export must name that step and kind."""
        for step, module, name, selects in self.SEAMS:
            for kind, make, expected_errno in self.KINDS:
                with self.subTest(step=step, kind=kind):
                    self.setUp()
                    with self.inject(module, name, selects, make):
                        fake, result = self.execute()
                    detail = result["failure_detail"]
                    self.assertEqual(result["outcome"], "failed")
                    self.assertEqual(detail["step"], step)
                    self.assertEqual(detail["category"], kind)
                    self.assertEqual(detail["errno"], "EACCES" if kind == "os-error" else expected_errno)
                    self.assertTrue(c.valid_failure_detail(detail))
                    # No second provider turn once collection has failed.
                    self.assertEqual(len(fake.containers), 1)
                    # And nothing the exception carried is exported.
                    self.assertNotIn("CANARY", json.dumps(result))

    def test_a_blocked_directory_names_its_step_and_errno(self):
        """Not a pass -- a REFUSAL, which the proposal says plainly is the
        outcome when the blocking directory is not the project directory. The
        difference from before is that the export says where and why."""
        fake, result = self.execute(blocked_directory=True)
        self.addCleanup(self.restore_blocked, fake)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["failure_code"], "state-coverage-incomplete")
        # R3: the errno the refusal was RAISED FOR survives it. The earlier
        # version of this test asserted "none" while its name claimed the
        # opposite, which is worse than having no test.
        self.assertEqual(result["failure_detail"],
                         {"step": "source-inventory", "category": "known-refusal",
                          "errno": "none", "cause": "EACCES"})
        self.assertTrue(c.valid_failure_detail(result["failure_detail"]))
        self.assertEqual(len(fake.containers), 1)
        self.assertNotIn("promoted", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
