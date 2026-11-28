"""W386365: an ordinary creation asked of an instance whose manager is SERVING.

THE FIELD BLOCKER THIS REPRODUCES AND CLOSES. Run M386364 started the stack
and then called `manager create`; the command needed the manager-instance
guard the serving manager holds for life, and was refused as a second manager.
Nothing could be submitted to a running instance.

WHAT IS REAL HERE. The instance is installed and configured by the product's
own installer and `pool compose-worker`. The serving side is the real
`job_manager serve` command in this process: the real Job, control and
Authority stores, the real guard, the real sweep and the real composition,
with a deterministic engine and the checkpoint-profile seam every connected
serving case uses. THE OPERATOR'S COMMAND RUNS IN ANOTHER PROCESS, because the
guard is a file lock and only a second process meets it as the field did.

Nothing reaches an engine, a provider or a network.
"""
import io
import json
import os
import signal
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from baton_v12.worker_manager import ControlStore, workspaces

from tools import bootstrap, job_manager, stage_execution
from tools.creation_ports import instance_identity

from tests.tools import test_connected_creation

PYTHON_ROOT = Path(__file__).resolve().parents[2]
FACTORY = "tests.tools.test_creation_while_serving:factory"
# What `factory` composes from. One serving case at a time owns it.
SERVING = {}


def factory(job_store, control_store):
    """The serving command's operations: the real composition over the
    configuration AS IT IS NOW, with the deterministic seams injected."""
    SERVING["composed"] += 1
    return stage_execution.operations_from(
        json.loads(Path(SERVING["configuration"]).read_text()), job_store,
        control_store, engine_run=SERVING["engine"],
        credential_provider=SERVING.get("credential_provider", lambda provider, reference: "a-secret"),
        checkout=SERVING["checkout"], checkpoint_profile=SERVING["profile"])


def observing(job_store, control_store):
    """The publisher's read-only observation, over the same configuration."""
    return stage_execution.observation_from(
        json.loads(Path(SERVING["configuration"]).read_text()), job_store,
        control_store, checkout=SERVING["checkout"])


class ServingCase(test_connected_creation.ConnectedCreationCase):
    """One reusable instance with two composed workers and no Job."""

    BASE = "a" * 40
    SOURCE = "/srv/the-owners-source"

    @staticmethod
    def git(argv, **named):
        if argv[1] == "clone":
            place = Path(argv[-1])
            (place / "objects" / "info").mkdir(parents=True, exist_ok=True)
            (place / "refs").mkdir(parents=True, exist_ok=True)
            (place / "HEAD").write_text("ref: refs/heads/main\n")
        if "rev-parse" in argv and "--verify" not in argv:
            return SimpleNamespace(returncode=0, stdout=argv[2], stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def bootstrapped(self, document, *operands):
        document.pop("state_root", None) if "--destination" in operands else None
        place = os.path.join(self.root, f"inputs-{len(os.listdir(self.root))}.json")
        Path(place).write_text(json.dumps(document))
        said = {"command": "baton-v12-stack", "frozen": True, "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10, "input-manifest-template": 30, "worker-control-1.0": 20},
                "native_rpds": str(Path(self.stand_in_runtime()) / "_internal" / "lib.so")}
        out = io.StringIO()
        with mock.patch.object(bootstrap, "_identity_of", lambda command, runtime=None, distro=None: said):
            code = bootstrap.main(["--inputs", place, *operands, "--repository-source", self.SOURCE], stream=out, runner=self.git)
        self.assertEqual(code, 0, out.getvalue())

    def pool(self, *, two_codex=False):
        """Install, compose two workers by the product's own verb, configure."""
        from baton_v12.worker_manager import source_boundary
        from tests.job_manager.test_review_driver import Profile
        from tests.tools.test_single_worker import Engine
        from tools import pool

        profile = Profile()
        common = dict(jobs=[], line_declared_base=self.BASE, canonical_target_id=self.BASE, checkpoint_profile=profile.name)
        self.bootstrapped(self.document(workers=[], **common), "--destination", self.state, "--distro", self.stand_in_runtime())
        self.owned = instance_identity(self.state)
        with ControlStore.open(self.owned["control_store"], incarnation="manager-0", clock=lambda: "2026-09-02T00:00:00.000Z"):
            pass
        before = self.configuration()
        task = os.path.join(self.state, "state", "task", "installed-task.json")
        os.makedirs(os.path.dirname(task), exist_ok=True)
        held = json.loads(Path(self.config["task_document"]).read_bytes())
        held["task_id"] = "installed-task"
        Path(task).write_bytes(json.dumps(held, sort_keys=True).encode())
        # A record LOCATOR this case writes itself in its disposable checkout.
        record_path = "work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-protocol-cli"
        record = Path(self.checkout, record_path)
        record.mkdir(parents=True, exist_ok=True)
        (record / "FINDING.md").write_text("# Finding\n")
        (record / "PLAN.md").write_text("# Plan\n")
        lanes = [("impl-a", "implementation", "baton.impl-a"), ("review-a", "review", "baton.reviewer")]
        if two_codex:
            lanes.append(("impl-b", "implementation", "baton.impl-b"))
        workers = []
        for worker_id, role, participant in lanes:
            codex = two_codex and role == "implementation"
            build = "0.169.0" if codex else "2.1.247"
            selected = dict(provider="codex", requested_model="gpt-6-astra", reported_identity="gpt-6-astra", cli_build=build) if codex else None
            if two_codex and not codex:
                selected = dict(provider="claude", requested_model="claude-fable-5", reported_identity="claude-fable-5", cli_build=build)
            worker = pool.composed(before, worker_id=worker_id, role=role, participant=participant,
                image_reference="baton-v12-worker:test", image_digest=self.config["image_digest"], cli_build=build,
                network=self.config["network"], credential_sources=os.path.join(self.root, "credential-sources.json"),
                credentials=["codex=operator-file:" + worker_id if codex else "claude=operator-file:w202663-development"],
                workspace_group=self.config["workspace_group"], task_document=task, record_path=record_path, checkout=self.checkout,
                verifier_layout=source_boundary.image_layout_marker(), provider_selection=selected)["worker"]
            workers.append(worker)
        carried = {name: before[name] for name in ("integration_target", "integration_workspace") if before.get(name)}
        self.bootstrapped(self.document(workers=workers, **common, **carried))
        self.place = self.configuration()["workers"][0]["deployment"]["workspace_storage"]
        self.engine = Engine()
        SERVING.clear()
        SERVING.update(configuration=os.path.join(self.state, "deployment.json"), engine=self.engine,
                       checkout=self.checkout, profile=profile, composed=0)
        self.addCleanup(SERVING.clear)

    # -- the operator's command, in its own process --------------------------

    def command(self, task, statement, *extra):
        argv = [sys.executable, "-B", "-m", "tools.job_manager", *self.argv(task=task, statement=statement), *extra]
        started = time.monotonic()
        done = subprocess.run(argv, cwd=str(PYTHON_ROOT), capture_output=True, text=True, timeout=120,
                              env=dict(os.environ, PYTHONPATH=os.pathsep.join(["src", "."]), PYTHONDONTWRITEBYTECODE="1"))
        return SimpleNamespace(code=done.returncode, out=done.stdout, err=done.stderr, seconds=time.monotonic() - started,
                               said=json.loads(done.stdout) if done.stdout.strip() else None)

    def together(self, *commands):
        """Several commands at once, each in its own process."""
        answers = [None] * len(commands)

        def run(index, operands):
            answers[index] = self.command(*operands)

        threads = [threading.Thread(target=run, args=one) for one in enumerate(commands)]
        for one in threads:
            one.start()
        for one in threads:
            one.join(150)
        return answers

    # -- the serving manager, in this process --------------------------------

    def serve(self, script=None, *, expect=None):
        """Run the real `serve` command here while `script` acts from a
        second thread; the script's end stops the manager politely.

        `serve` installs its signal handlers, which only the main thread may
        do -- so the manager runs here and the operator runs beside it.
        """
        failed, ended, said = [], threading.Event(), io.StringIO()

        def before_serve(number, frame):
            pass

        def driven():
            try:
                limit = time.monotonic() + 60
                if script is None:
                    self.assertTrue(ended.wait(60), "the expected manager interruption never occurred")
                    return
                # Instance ownership can precede the serving loop's stop handler.
                while signal.getsignal(signal.SIGTERM) is before_serve and not ended.wait(0.02):
                    self.assertLess(time.monotonic(), limit, "the manager never installed its stop handler")
                if not ended.is_set():
                    script()
            except BaseException as failure:
                failed.append(failure)
            finally:
                if not ended.is_set():
                    os.kill(os.getpid(), signal.SIGTERM)

        kept = {one: signal.getsignal(one) for one in (signal.SIGINT, signal.SIGTERM)}
        # A manager that failed before installing its own handler must not
        # leave the script's stop signal to end the test process.
        signal.signal(signal.SIGTERM, before_serve)
        beside = threading.Thread(target=driven)
        beside.start()
        raised = None
        try:
            code = job_manager.main(
                ["--store", self.owned["job_store"], "--incarnation", "manager-1", "--authority-uuid", self.owned["authority_uuid"],
                 "serve", "--control", self.owned["control_store"], "--operations", FACTORY, "--interval", "1"], stream=said)
        except BaseException as failure:
            raised = failure
        finally:
            ended.set()
            beside.join(200)
            for one, handler in kept.items():
                signal.signal(one, handler)
        if failed:
            raise failed[0]
        if expect is not None:
            self.assertIsInstance(raised, expect)
            return raised
        if raised is not None:
            raise raised
        self.assertEqual(code, 0)
        return json.loads(said.getvalue())

    # -- readers -------------------------------------------------------------

    def works(self, *work_ids):
        """`(projection or None, creation record or None)` per Work."""
        from baton_v12.authority.api import Authority

        with Authority.open_readonly(self.owned["authority_store"], expected_authority_uuid=self.owned["authority_uuid"]) as held:
            made = {one: held.work_creation(one) for one in work_ids}
            return {one: (None if made[one] is None else held.project_work(one), made[one]) for one in work_ids}

    def recorded(self):
        """What the Job store holds. Opened and closed here, because the
        operator's thread reads it too and a handle belongs to one thread."""
        from baton_v12.job_manager import JobStore, creation

        store = JobStore.open(self.owned["job_store"], authority_uuid=self.owned["authority_uuid"], incarnation="reader-1",
                              clock=job_manager._utc_clock())
        try:
            return self._recorded(store, creation)
        finally:
            store.close()

    @staticmethod
    def _recorded(store, creation):
        jobs = {one["job_id"]: one for one in creation.created_job_rows(store)}
        requests = {one["job_id"]: dict(one) for one in store._connection.execute("SELECT * FROM creation_requests")}
        operations = [one["operation_id"] for one in store._connection.execute(
            "SELECT operation_id FROM operations WHERE kind = ? ORDER BY operation_id", (creation.CREATE_KIND,))]
        stages = {}
        for one in store._connection.execute("SELECT job_id, kind, work_id FROM stages"):
            stages.setdefault(one["job_id"], {})[one["kind"]] = one["work_id"]
        return SimpleNamespace(jobs=jobs, requests=requests, operations=operations, stages=stages)

    def diagnosis(self):
        """Why nothing was dispatched, in the store's own words."""
        from baton_v12.job_manager import JobStore

        store = JobStore.open(self.owned["job_store"], authority_uuid=self.owned["authority_uuid"], incarnation="reader-1",
                              clock=job_manager._utc_clock())
        try:
            said = {"vectors": self.engine.vectors[-4:], "composed": SERVING.get("composed")}
            for table in ("stages", "deferrals", "episodes"):
                said[table] = [dict(one) for one in store._connection.execute(f"SELECT * FROM {table}")]
            return "nothing was dispatched: " + json.dumps(said, default=str)[:6000]
        finally:
            store.close()

    def generated(self, job_id):
        from baton_v12.job_manager import creation

        return creation.generated_work_id(self.owned["authority_uuid"], job_id)


class TwoJobsAreSubmittedToOneServingManager(ServingCase):
    """Contract cases 1 to 4, 7, 8, 10 and 15, in one served run."""

    def test_omitted_worker_names_both_choices_and_creates_no_job(self):
        self.pool(two_codex=True)

        def operator():
            answer = self.command("missing-worker", "No worker selected.")
            self.assertNotEqual(answer.code, 0)
            self.assertIsNone(answer.said)
            self.assertEqual(answer.err.splitlines(), [
                "refused: Choose an implementation worker ('impl-a', 'impl-b') with --implementation-worker WORKER_ID."])
            held = self.recorded()
            self.assertEqual(held.requests["job-missing-worker"]["state"], "refused")
            self.assertNotIn("job-missing-worker", held.jobs)
            self.assertNotIn("job-missing-worker", held.stages)
            self.assertEqual(held.operations, [])

        self.serve(operator)

    def test_selected_codex_workers_overlap_with_distinct_credentials(self):
        from tests.tools.test_stage_execution import _ConcurrentEngine
        self.pool(two_codex=True)
        self.engine = SERVING["engine"] = _ConcurrentEngine()
        requests = []
        def provide(provider, reference):
            requests.append((provider, reference))
            return ("synthetic-" + reference).encode()
        SERVING["credential_provider"] = provide
        def operator():
            commands = [("capacity-" + suffix, "Independent coding task " + suffix,
                         "--implementation-worker", "impl-" + suffix) for suffix in ("a", "b")]
            answers = self.together(*commands)
            for command, answer in zip(commands, answers):
                self.assertEqual(answer.code, 0, answer.err)
                self.assertEqual(answer.said["binding"]["source_worker_id"], command[-1])
                self.assertEqual(self.command(*command).out, answer.out)
            changed = self.command(*commands[0][:-1], "impl-b")
            self.assertNotEqual(changed.code, 0)
            self.assertIn("DIFFERENT", changed.err)
            deadline = time.monotonic() + 30
            while sum(record["running"] for record in self.engine.records.values()) < 2:
                if time.monotonic() > deadline:
                    self.fail(self.diagnosis())
                time.sleep(0.1)
            from concurrent.futures import ThreadPoolExecutor
            from baton_v12.worker_manager import launch
            from codex_agent import CodexAgent

            both_inside_provider = threading.Barrier(2, timeout=10)

            def run_provider(record):
                mounts = {m["Destination"]: Path(m["Source"]) for m in record["mounts"]}
                home = mounts["/run/baton/provider-home"]
                identity = json.loads((home.parent / "record.json").read_bytes())["identity"]
                worker = identity["worker_id"]
                self.assertEqual(identity["job_id"], "job-capacity-" + worker[-1])
                agent = CodexAgent()
                agent._seen = launch.payload_of(json.loads(mounts[launch.LAUNCH_TARGET].read_bytes()))
                scratch = Path(self.root, "scratch-" + worker)
                scratch.mkdir(mode=0o700)
                _, roots = agent._new_ephemera(str(scratch), "provider")
                # Translate this container's retained-home mount into the fixture.
                with mock.patch.object(agent, "_retained_home", return_value=str(home)):
                    environment = agent._closed_environment(home=str(home), roots=roots, scratch=str(scratch))
                argv = agent.provider_argv("Implement " + identity["job_id"])
                self.assertEqual(argv[0:2], ["codex", "exec"])
                self.assertEqual(argv[-3:], ["--model", "gpt-6-astra", "Implement " + identity["job_id"]])
                both_inside_provider.wait()
                return worker, (Path(environment["CODEX_HOME"]) / "auth.json").read_bytes()

            with ThreadPoolExecutor(max_workers=2) as providers:
                self.assertEqual(dict(providers.map(run_provider, list(self.engine.records.values()))),
                                 {"impl-a": b"synthetic-impl-a", "impl-b": b"synthetic-impl-b"})
        self.serve(operator)
        self.assertCountEqual(requests, [("operator-file", "impl-a"), ("operator-file", "impl-b")])
        self.assertEqual(len(self.engine.starts), 2)
        self.assertEqual(len(self.engine.records), 2)
        self.assertEqual(sum(v[1] == "start" for v in self.engine.vectors), 2)

    def test_two_independent_jobs_a_replay_a_changed_intent_and_a_refusal(self):
        self.pool()
        seen = {}

        def operator():
            seen["guard"] = workspaces._HELD_GUARDS[os.path.realpath(self.place)]
            # 1, 2 and 8: two independent submissions, racing from two processes.
            seen["one"], seen["two"] = self.together(("serve-one", "The first served task."),
                                                     ("serve-two", "The second served task."))
            # 3: the first one again, exactly.
            seen["again"] = self.command("serve-one", "The first served task.")
            # 4: the first one's identity with another statement.
            seen["changed"] = self.command("serve-one", "A different task under the same name.")
            # 7: a request this deployment cannot perform -- a route no
            #    configured implementation worker handles.
            seen["refused"] = self.command("serve-three", "The third served task.", "--route", "baton.impl")
            seen["after_refusal"] = self.recorded().requests["job-serve-three"]
            #    ...and the same request again with the fault removed is queued again.
            seen["repaired"] = self.command("serve-three", "The third served task.")
            # 10: the manager serves what it created, with no restart.
            from tests.tools.test_single_worker import launching
            limit = time.monotonic() + 60
            while not any(launching(one) for one in self.engine.vectors):
                self.assertLess(time.monotonic(), limit, self.diagnosis())
                time.sleep(0.1)
            seen["guard_after"] = workspaces._HELD_GUARDS.get(os.path.realpath(self.place))
            seen["holders"] = workspaces.holders_of(self.place)

        report = self.serve(operator)
        one, two, again = seen["one"], seen["two"], seen["again"]
        for answer, job_id in ((one, "job-serve-one"), (two, "job-serve-two"), (seen["repaired"], "job-serve-three")):
            self.assertEqual(answer.code, 0, answer.err)
            self.assertEqual(answer.said["job_id"], job_id)
            self.assertEqual(answer.said["binding"]["job_work_id"], self.generated(job_id))
            self.assertLess(answer.seconds, 30)
        # DISTINCT WORK BINDINGS, each made once and open.
        works = {one.said["binding"]["job_work_id"], two.said["binding"]["job_work_id"],
                 seen["repaired"].said["binding"]["job_work_id"]}
        self.assertEqual(len(works), 3)
        for work_id, (projected, made) in self.works(*works).items():
            self.assertIsNotNone(made, work_id)
            self.assertEqual(projected["status"], "open")
        self.assertEqual(one.said["work"]["state"], "created")
        self.assertEqual(two.said["work"]["state"], "created")
        # THE REPLAY IS THE RECORDED ANSWER, byte for byte, and made nothing.
        self.assertEqual(again.code, 0, again.err)
        self.assertEqual(again.out, one.out)
        held = self.recorded()
        self.assertEqual(sorted(held.jobs), ["job-serve-one", "job-serve-three", "job-serve-two"])
        self.assertEqual(len(held.operations), 3, held.operations)
        self.assertEqual({job: row["state"] for job, row in held.requests.items()},
                         dict.fromkeys(held.jobs, "created"))
        self.assertEqual(held.requests["job-serve-one"]["attempts"], 1)
        # A CHANGED INTENT IS REFUSED BY THE COMMAND and recorded nowhere.
        self.assertNotEqual(seen["changed"].code, 0)
        self.assertIn("DIFFERENT", seen["changed"].err)
        self.assertEqual(seen["changed"].out, "")
        # THE MANAGER'S REFUSAL IS THE COMMAND'S ANSWER, and it kept serving.
        self.assertNotEqual(seen["refused"].code, 0)
        self.assertIn("baton.impl", seen["refused"].err)
        self.assertIn("the serving manager refused creation request", seen["refused"].err)
        self.assertEqual(seen["after_refusal"]["state"], "refused")
        self.assertEqual(held.requests["job-serve-three"]["attempts"], 2)
        # EACH JOB'S STAGES ARE ON ITS OWN WORK, and the binding says so.
        for job_id in held.jobs:
            self.assertEqual(set(held.stages[job_id].values()), {self.generated(job_id)}, job_id)
            self.assertEqual(self.bindings()[job_id]["job_work_id"], self.generated(job_id))
        # THE SOLE MANAGER NEVER GAVE UP ITS INSTANCE: the guard object it
        # took at start is the one it holds after adopting three Jobs, and a
        # released guard is a new object.
        self.assertIs(seen["guard_after"], seen["guard"])
        self.assertGreaterEqual(seen["holders"], 1)
        # ...AND IT ADOPTED THEM IN THIS PROCESS: composed once idle, then
        # again only when a Job was created (never for the refusal alone).
        self.assertGreaterEqual(SERVING["composed"], 2)
        self.assertLessEqual(SERVING["composed"], 4)
        # ONE IMPLEMENTATION WORKER, SO ONE JOB RUNS AND THE OTHERS QUEUE.
        from tests.tools.test_single_worker import launching
        self.assertEqual(len([one for one in self.engine.vectors if launching(one)]), 1, self.engine.vectors)
        self.assertIn("acts", report)
        # 11: BOTH JOBS IN THE OPERATOR'S TERMINAL VIEW, from the document the
        # publisher's own `status --observe` command writes, read by the TUI's
        # own bounded reader.
        from tools import job_tui

        said = io.StringIO()
        self.assertEqual(job_manager.main(
            ["--store", self.owned["job_store"], "--incarnation", "v12-stack-publisher", "--authority-uuid", self.owned["authority_uuid"],
             "status", "--control", self.owned["control_store"], "--observe", FACTORY.replace(":factory", ":observing")], stream=said), 0)
        status = os.path.join(self.root, "status.json")
        Path(status).write_text(said.getvalue())
        session = job_tui.Session(job_tui.source_from(status))
        session.read()
        painted = "\n".join(session.frame(30, 140).lines)
        for job_id in ("job-serve-one", "job-serve-two", "job-serve-three"):
            self.assertIn(job_id, painted)
        shown = {one["job_id"]: one for one in json.loads(said.getvalue())["jobs"]}
        states = sorted(stage["state"] for job in shown.values() for stage in job["stages"] if stage["kind"] == "implementation")
        self.assertEqual(states, ["queued", "queued", "waiting"], shown)


class OneRequestCannotStopTheManager(ServingCase):
    """A creation that faults is answered and the manager keeps serving."""

    def test_an_unexpected_fault_is_answered_and_the_next_request_is_served(self):
        from tools import creation_ports

        self.pool()
        seen = {}
        genuine = creation_ports.DeploymentDerivation.derived

        def faulting(port, selection=None):
            if selection is not None and selection["job_id"] == "job-fault-one":
                raise RuntimeError("an owner port broke")
            return genuine(port, selection=selection) if selection is not None else genuine(port)

        def operator():
            seen["fault"] = self.command("fault-one", "The task whose creation faults.")
            seen["next"] = self.command("fault-two", "The task after it.")

        with mock.patch.object(creation_ports.DeploymentDerivation, "derived", faulting):
            self.serve(operator)
        self.assertNotEqual(seen["fault"].code, 0)
        self.assertIn("unexpected fault (RuntimeError: an owner port broke)", seen["fault"].err)
        self.assertIn("run the same command again", seen["fault"].err)
        self.assertEqual(seen["next"].code, 0, seen["next"].err)
        held = self.recorded()
        self.assertEqual(sorted(held.jobs), ["job-fault-two"])
        self.assertEqual({job: row["state"] for job, row in held.requests.items()},
                         {"job-fault-one": "refused", "job-fault-two": "created"})


class TheDelayedPath(ServingCase):
    """Contract cases 5, 6, 13 and 14: the manager has not answered yet."""

    def held_elsewhere(self):
        """The instance guard, held by this process and performing nothing:
        a manager that is alive and has not reached the request."""
        control = ControlStore.open(self.owned["control_store"], incarnation="manager-1", clock=job_manager._utc_clock())
        self.addCleanup(control.close)
        guard = workspaces.hold_manager_instance(control, self.place)
        self.addCleanup(guard.release)
        return guard

    def test_pending_is_reported_then_recovered_without_a_second_job_or_work(self):
        self.pool()
        guard = self.held_elsewhere()
        # 13: THE WAIT EXPIRES. Exit 3, the request identity, nothing created.
        waited = self.command("late-one", "The delayed task.", "--wait-seconds", "1")
        self.assertEqual(waited.code, job_manager.PENDING_EXIT, waited.err)
        self.assertEqual(waited.said["state"], "pending")
        self.assertEqual(waited.said["job_id"], "job-late-one")
        self.assertGreaterEqual(waited.said["waited_seconds"], 1)
        request_id = waited.said["request_id"]
        # 14: --no-wait returns once the request is durable, and a repeat of
        #     either spelling finds the SAME request.
        immediate = self.command("late-one", "The delayed task.", "--no-wait")
        self.assertEqual(immediate.code, 0, immediate.err)
        self.assertEqual(immediate.said["state"], "pending")
        self.assertEqual(immediate.said["request_id"], request_id)
        self.assertEqual(immediate.said["recorded_at"], waited.said["recorded_at"])
        held = self.recorded()
        self.assertEqual(held.jobs, {})
        self.assertEqual(held.operations, [])
        self.assertEqual(held.requests["job-late-one"]["state"], "pending")
        self.assertEqual(held.requests["job-late-one"]["attempts"], 1)
        late = self.generated("job-late-one")
        self.assertEqual(self.works(late)[late], (None, None))
        self.assertEqual(self.bindings(), {})
        # 5: THE MANAGER REACHES IT -- here by starting, with the request
        #    already recorded -- and the same command now reads the receipt.
        seen = {}

        def operator():
            seen["answer"] = self.command("late-one", "The delayed task.")
            seen["again"] = self.command("late-one", "The delayed task.", "--no-wait")

        self.serve(operator)
        guard.release()
        self.assertEqual(seen["answer"].code, 0, seen["answer"].err)
        self.assertEqual(seen["answer"].said["job_id"], "job-late-one")
        self.assertEqual(seen["again"].out, seen["answer"].out)
        held = self.recorded()
        self.assertEqual(sorted(held.jobs), ["job-late-one"])
        self.assertEqual(len(held.operations), 1)
        self.assertEqual(held.requests["job-late-one"]["request_id"], request_id)
        self.assertEqual(held.requests["job-late-one"]["state"], "created")
        self.assertEqual(held.requests["job-late-one"]["attempts"], 1)
        self.assertIsNotNone(self.works(late)[late][1])

    def test_a_manager_that_dies_between_creating_and_answering_answers_once(self):
        from baton_v12.job_manager import creation_requests

        self.pool()
        guard = self.held_elsewhere()
        self.assertEqual(self.command("crash-one", "The interrupted task.", "--no-wait").code, 0)
        guard.release()

        class Died(Exception):
            pass

        def dying(*arguments, **named):
            raise Died("the manager stopped after creating and before answering")

        # 6: created, and the answer never written.
        with mock.patch.object(creation_requests, "settle", dying):
            self.serve(expect=Died)
        held = self.recorded()
        self.assertEqual(sorted(held.jobs), ["job-crash-one"])
        self.assertEqual(held.requests["job-crash-one"]["state"], "pending")
        # The next manager finds the request, replays the creation and answers.
        seen = {}

        def operator():
            seen["answer"] = self.command("crash-one", "The interrupted task.")
            # A replay can read the created Job before the manager repairs its request row.
            deadline = time.monotonic() + 30
            while self.recorded().requests["job-crash-one"]["state"] == "pending":
                self.assertLess(time.monotonic(), deadline, "the manager never settled the interrupted request")
                time.sleep(0.02)

        self.serve(operator)
        self.assertEqual(seen["answer"].code, 0, seen["answer"].err)
        held = self.recorded()
        self.assertEqual(sorted(held.jobs), ["job-crash-one"])
        self.assertEqual(len(held.operations), 1)
        self.assertEqual(held.requests["job-crash-one"]["state"], "created")
        self.assertEqual(held.requests["job-crash-one"]["attempts"], 1)


class OneIntentPerJobOnBothPaths(ServingCase):
    """W386365 review R1 (review-2026-11-26T06-18-51Z), the reviewer's probe
    `evidence/review-codex-386369/probe_pending_owner.py` made a case.

    A request recorded for a serving manager reserves its Job identity. When
    that manager stops before answering, a DIFFERENT request under the same
    Job must be refused before anything is created, and the original request
    must still recover exactly one Job and one Work, answering with one
    receipt on every path afterwards.
    """

    def test_a_changed_intent_is_refused_after_the_manager_stops_and_the_first_recovers(self):
        self.pool()
        guard = TheDelayedPath.held_elsewhere(self)
        first = self.command("race", "First request", "--no-wait")
        self.assertEqual((first.code, first.said["state"]), (0, "pending"), first.err)
        guard.release()
        # B, with no manager serving: refused at the intent, before any effect.
        changed = self.command("race", "Different request")
        self.assertNotEqual(changed.code, 0)
        self.assertIn("DIFFERENT intent", changed.err)
        self.assertEqual(changed.out, "")
        held = self.recorded()
        self.assertEqual(held.jobs, {})
        self.assertEqual(held.operations, [])
        race = self.generated("job-race")
        self.assertEqual(self.works(race)[race], (None, None))
        self.assertEqual(self.bindings(), {})
        self.assertEqual(held.requests["job-race"]["state"], "pending")
        # A again, with no manager serving: this command performs the request
        # that reserved the identity, and answers it.
        recovered = self.command("race", "First request")
        self.assertEqual(recovered.code, 0, recovered.err)
        self.assertEqual(recovered.said["job_id"], "job-race")
        self.assertEqual(recovered.said["binding"]["job_work_id"], race)
        self.assertIn("First request", json.dumps(recovered.said))
        again = self.command("race", "First request")
        self.assertEqual(again.out, recovered.out)
        # ACROSS A RESTART: a manager now serving answers the same receipt,
        # and B is still refused, now by the creation's own replay.
        seen = {}

        def operator():
            seen["served"] = self.command("race", "First request")
            seen["changed"] = self.command("race", "Different request")

        self.serve(operator)
        self.assertEqual(seen["served"].code, 0, seen["served"].err)
        self.assertEqual(seen["served"].out, recovered.out)
        self.assertNotEqual(seen["changed"].code, 0)
        self.assertIn("DIFFERENT request", seen["changed"].err)
        held = self.recorded()
        self.assertEqual(sorted(held.jobs), ["job-race"])
        self.assertEqual(len(held.operations), 1)
        self.assertEqual((held.requests["job-race"]["state"], held.requests["job-race"]["attempts"]), ("created", 1))
        self.assertIsNotNone(self.works(race)[race][1])
        self.assertEqual(sorted(self.bindings()), ["job-race"])

    def test_replay_cannot_replace_the_route_of_a_pending_request(self):
        self.pool()
        guard = TheDelayedPath.held_elsewhere(self)
        pending = self.command("route", "Routing", "--no-wait")
        self.assertEqual(pending.said["state"], "pending")
        guard.release()
        changed = self.command("route", "Routing", "--route", "baton.impl")
        self.assertNotEqual(changed.code, 0)
        self.assertEqual(self.recorded().requests["job-route"]["state"], "pending")
        resumed = self.command("route", "Routing")
        self.assertEqual(resumed.code, 0, resumed.err)

    def test_a_delayed_performer_cannot_create_after_its_request_is_replaced(self):
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import creation_requests

        self.pool()
        perform = job_manager._performed

        def replace_before_guard(taken, store, control, held, place):
            creation_requests.settle(store, held, "refused", {
                "category": "refused", "code": "precondition", "message": "original attempt refused"})
            changed = dict(held["request"], task=dict(held["request"]["task"], statement="Replacement"))
            creation_requests.record(store, changed, place)
            return perform(taken, store, control, held, place)

        with mock.patch.object(job_manager, "_performed", replace_before_guard):
            with self.assertRaisesRegex(ContractRefusal, "original attempt refused"):
                self.created(task="late", statement="First")
        self.assertFalse(self.recorded().jobs)
        self.assertFalse(self.bindings())
        self.assertEqual(self.works(self.generated("job-late"))[self.generated("job-late")], (None, None))
        self.assertEqual(self.command("late", "Replacement").code, 0)

    def test_with_no_manager_the_command_records_its_intent_before_creating(self):
        """The stopped path reserves through the same row, so its creation
        is held by the identity a later serving request would meet."""
        self.pool()
        made = self.command("plain", "A task created with no manager serving.")
        self.assertEqual(made.code, 0, made.err)
        held = self.recorded()
        self.assertEqual(held.requests["job-plain"]["state"], "created")
        self.assertEqual(json.loads(held.requests["job-plain"]["answer"])["job_id"], "job-plain")
        self.assertEqual(sorted(held.jobs), ["job-plain"])

    def test_a_creation_with_no_request_row_still_replays_and_still_refuses_a_change(self):
        """PRESERVED: every Job created before requests existed has no row."""
        from baton_v12.job_manager import JobStore

        self.pool()
        made = self.command("legacy", "A task created before requests existed.")
        self.assertEqual(made.code, 0, made.err)
        store = JobStore.open(self.owned["job_store"], authority_uuid=self.owned["authority_uuid"], incarnation="legacy",
                              clock=job_manager._utc_clock())
        try:
            with store._connection:
                store._connection.execute("DELETE FROM creation_requests WHERE job_id = 'job-legacy'")
        finally:
            store.close()
        again = self.command("legacy", "A task created before requests existed.")
        self.assertEqual(again.code, 0, again.err)
        self.assertEqual(again.out, made.out)
        self.assertNotIn("job-legacy", self.recorded().requests)
        changed = self.command("legacy", "A changed task.")
        self.assertNotEqual(changed.code, 0)
        self.assertIn("DIFFERENT request", changed.err)
        self.assertNotIn("job-legacy", self.recorded().requests)


if __name__ == "__main__":
    unittest.main()
