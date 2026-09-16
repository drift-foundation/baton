"""C extends the scheduler trace with measured process and owner evidence.

The provider is a deterministic local child; the OCI engine is simulated.
Preparation and apply execute their real worker entrypoints as local children.
C1 proves useful correction and reviewed import. C2 adds a counted manager
recomposition in one process; no host-loss or production qualification is claimed.
"""
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from types import MethodType, SimpleNamespace

from baton_v12.contracts import digest, digest_of_bytes
from baton_v12.authority import Authority
from baton_v12.job_manager import submit, sweep, ending, episodes, submission
from baton_v12.job_manager.integration_capacity import integration_capacity_of
from baton_v12.worker_manager import provider_context as context, context_delivery as custody
from baton_v12.worker_manager import frozen_output_of, load_manifest, assignment_of, review_cycles
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from baton_v12.integration import reconciliation
from tests.job_manager import fixtures
from tests.manager.test_claude_context import ServingContextCase
from tests.tools import scheduler_trace, test_stage_execution as stage_fixture
from tools import stage_execution

SCHEMA = "baton.v12.correction-restart-trace/1"
PROVIDER = r'''
import hashlib,json,os,sys
from pathlib import Path
argv,edits,log,bound,attempt,role=json.loads(sys.argv[1])
def digest(value):
    return 'sha256:'+hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
record={'attempt_id':attempt,'role':role,'pid':os.getpid(),'use_id':None,'invocation_id':None,'argv':argv,'argv_digest':digest(argv),'selector':None,'conversation_id':None,'restored':False}
if bound is not None:
    state=Path(os.environ['HOME'])/'.claude/projects/output/session.json'
    previous=json.loads(state.read_text()) if state.exists() else None
    session=argv[-2]
    assert (previous is not None)==('--resume' in argv)
    if previous: assert previous['session']==session
    state.parent.mkdir(parents=True,exist_ok=True)
    state.parent.chmod(0o700);state.parent.parent.chmod(0o700)
    state.write_text(json.dumps({'session':session,'private':'C-PRIVATE-STATE','turn':1 if previous is None else previous['turn']+1}))
    state.chmod(0o600)
    record.update(use_id=bound['use_id'],invocation_id=bound['invocation_id'],selector=argv[-3],conversation_id=session,restored=previous is not None)
with open(log,'a') as out:
    out.write(json.dumps(record,sort_keys=True)+'\n');out.flush();os.fsync(out.fileno())
for name,body in edits.items():Path(name).write_text(body)
if bound is not None: print(json.dumps({'type':'result','subtype':'success','is_error':False,'session_id':argv[-2],'model':bound['reported_model']}))
'''

MANAGED_CHILD = r'''
import functools,json,sys
sys.path.insert(0,sys.argv[1])
import baton_worker
mounts=json.loads(sys.argv[2]);kind=sys.argv[3];scratch=sys.argv[4]
baton_worker.INPUT_ROOT=mounts['/input'];baton_worker.OUTPUT_ROOT=mounts['/output']
launch=next(source for target,source in mounts.items() if target.endswith('launch.json'))
command=next(source for target,source in mounts.items() if target.endswith('/command'))
events=next(source for target,source in mounts.items() if target.endswith('/events'))
if kind=='prepare':
    import reconciliation_entry
    reconciliation_entry.PreparationAgent=functools.partial(reconciliation_entry.PreparationAgent,input_root=mounts['/input/source'],output_root=mounts['/output'],scratch=scratch)
    status=reconciliation_entry.main(place=launch,command_root=command,event_root=events)
else:
    import integration_entry
    import traceback
    original_work=integration_entry.ManagedApplyAgent.work
    def traced_work(self,*args):
        try:return original_work(self,*args)
        except BaseException:
            traceback.print_exc()
            raise
    integration_entry.ManagedApplyAgent.work=traced_work
    original_handle=baton_worker.handle
    def traced_handle(*args):
        try:return original_handle(*args)
        except BaseException:
            traceback.print_exc()
            raise
    baton_worker.handle=traced_handle
    integration_entry.ManagedApplyAgent=functools.partial(integration_entry.ManagedApplyAgent,output_root=mounts['/output'])
    status=integration_entry.main(launch_place=launch,command_root=command,event_root=events,bundle_root=mounts['/input/source'],scratch=scratch)
sys.exit(status)
'''


class ProcessEngine(stage_fixture._ConcurrentEngine):
    def __init__(self, world):
        super().__init__()
        self.world = world
        self.processes = {}
        self.events = []
        self.launches = {}

    def __call__(self, argv, **options):
        if argv[1] in ("stop", "rm") and argv[-1] in self.processes:
            process, log = self.processes[argv[-1]]
            if argv[1] == "rm" and process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
        if argv[1] != "run" or "--entrypoint" in argv:
            return super().__call__(argv, **options)
        labels, mounts = {}, {}
        for index, arg in enumerate(argv[:-1]):
            if arg == "--label":
                key, value = argv[index + 1].split("=", 1)
                labels[key] = value
            if arg == "--mount":
                parts = dict(part.split("=", 1) for part in argv[index + 1].split(",") if "=" in part)
                mounts[parts["target"]] = parts["source"]
        attempt = labels["baton.v12.runtime_attempt_id"]
        self.launches[attempt] = json.loads(Path(next(source for target, source in mounts.items() if target.endswith("launch.json"))).read_text())
        # There is no start-operation label. The engine receives the rendered
        # operation identity as --name; count calls, including repeated inputs.
        self.events.append({"attempt_id": attempt, "operation_operand": argv[argv.index("--name") + 1], "argv": list(argv), "argv_digest": digest(list(argv)), "labels": labels})
        answer = super().__call__(argv, **options)
        source = Path(mounts.get("/input/source", "/nonexistent"))
        kind = "apply" if (source / "managed-apply.json").is_file() else "prepare" if attempt.startswith("prepare-") else None
        if kind is not None:
            log = (Path(self.world.root) / (kind + "-" + str(len(self.events)) + ".log")).open("w+")
            worker = Path(__file__).resolve().parents[3] / "worker"
            process = subprocess.Popen([sys.executable, "-B", "-c", MANAGED_CHILD, str(worker), json.dumps(mounts), kind, os.path.join(self.world.root, kind + "-scratch")], stdout=log, stderr=log)
            self.processes[answer["stdout"].strip()] = (process, log)
        return answer

    def close(self):
        for process, log in self.processes.values():
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            log.close()


class World(ServingContextCase):
    REPORT = {"schema": "baton.review-report/1", "verdict": "accepted", "findings": "the revised requirement is satisfied"}

    def setUp(self):
        super().setUp()
        self.tick_count = 0
        self.reports = []
        self.provider_log = Path(self.root) / "provider-counter.jsonl"
        self.verifications = []
        self.review_evidence = []
        self.engine = ProcessEngine(self)
        self.addCleanup(self.engine.close)
        methods = stage_fixture.TwoBoundJobsTraverseServingAndCorrection
        self.JUDGMENT_WORKS = methods.JUDGMENT_WORKS
        for name in ("judgment_work", "judgment_execution", "judgment_task_bytes", "judgment_task_document", "judgment_workers", "judgment_turn", "vcs_in"):
            setattr(self, name, MethodType(getattr(methods, name), self))
        self.manifest_over = MethodType(stage_fixture.EachJobBindsItsOwnDeploymentAndLine.manifest_over, self)
        self.deployment_of = lambda value: getattr(value, "composed", value).deployment
        self.target = os.path.join(self.root, "target.git")
        self.assertEqual(stage_execution._git_run(["git", "clone", "--quiet", "--bare", self.source, self.target])["returncode"], 0)
        authority = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.add_route_handler("integration-preparation", "baton.integrator")
        finally:
            authority.dispose()
        judges = self.judgment_workers("job-a")
        self.configuration = self.composed_document(line_declared_base=self.base, integration_preparation=True, policy_generation=self.fixture_policy, result_judgment_workers=judges, integration_target=self.target, integration_target_reference="refs/heads/main", schema="baton.v12.stage-execution-deployment/2", job_bindings=[{"job_id": "job-a", "job_work_id": self.work, "review_work_id": self.work, "line_declared_base": self.base, "canonical_target_id": "target-1", "source_worker_id": "implementation-worker"}])
        self.trace = scheduler_trace.Trace(scheduler_trace.Scenario(name="useful-correction", jobs=copy.deepcopy(self.submission["jobs"]), workers=[], ticks=100, note={"provider": "deterministic local process", "engine": "simulated OCI", "boundary": "C1 useful correction; no reopen"}))

    def serving(self, **unused):
        job, control = self.stores("correction-" + str(self.tick_count))
        configure_workspace_storage(control, self.storage)
        custody.configure_context_storage(control, str(self.context_root), excluded_roots=[self.source, self.storage], runtime_uid=os.getuid())
        context.certify_context_profile(control, self.context_profile)
        composed = stage_execution.operations_from(self.configuration, job, control, engine_run=self.engine, credential_provider=lambda provider, reference: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return SimpleNamespace(job=job, control=control, composed=composed)

    def provider(self, edits=None, status=0):
        original = super().provider(edits, status)
        def run(argv, **options):
            if argv[0] == "claude":
                return subprocess.run([sys.executable, "-B", "-c", PROVIDER, json.dumps([list(argv), edits or {}, str(self.provider_log), self.active_binding, self.active_attempt, self.active_role])], **options)
            verifying = list(argv[:2]) == ["python3", "harness.py"]
            if verifying:
                root = Path(options["cwd"])
                before = {name: digest_of_bytes((root / name).read_bytes()) for name in ("scale.py", "harness.py")}
            started = time.monotonic()
            answer = original(argv, **options)
            if verifying:
                after = {name: digest_of_bytes((root / name).read_bytes()) for name in before}
                self.assertEqual(before, after)
                self.verifications.append({"attempt_id": self.active_attempt, "status": answer.returncode, "code_digest": before["scale.py"], "verifier_digest": before["harness.py"], "argv": list(argv), "before": before, "after": after, "seconds": time.monotonic() - started, "output": answer.stdout, "execution": "real subprocess"})
            return answer
        return run

    def turn(self, control, role, attempt_id, roots, **operands):
        self.active_attempt, self.active_role = attempt_id, role
        self.active_binding = context.context_invocation_of(control, attempt_id)
        return super().turn(control, role, attempt_id, roots, **operands)

    def tick(self, held):
        self.tick_count += 1
        self.assertLessEqual(self.tick_count, 100)
        report = sweep(held.job, held.composed, now=fixtures.NOW)
        self.reports.append(report)
        self.trace.record(self.tick_count, "observe", outcome="observed", evidence=digest_of_bytes(json.dumps(report, sort_keys=True).encode()))
        return report

    def until(self, held, kind, state):
        while self.tick_count < 100:
            report = self.tick(held)
            if self.states(held.job, held.composed).get(kind) == state:
                return
            time.sleep(.02)
        self.fail((kind, state, report))

    def provider_events(self):
        return [json.loads(line) for line in self.provider_log.read_text().splitlines()] if self.provider_log.exists() else []

    def snapshot(self, held, attempt):
        binding = context.context_invocation_of(held.control, attempt)
        frozen = frozen_output_of(held.control, attempt)
        result = load_manifest(held.control, frozen["manifest_digest"], "resultManifest")
        receipt = next(one for one in result["outputs"] if one["name"] == "provider-context-receipt")
        body = custody.read_context_receipt(held.control, attempt_id=attempt, artifact_id=receipt["artifact"]["artifact_id"], workspace_storage=self.storage)
        settlement = self.record(held.job, attempt)["settlement"]
        checkpoint = review_cycles.checkpoint_of(held.control, settlement["evidence"]["checkpoint_id"])
        workspace = next(one["source"] for one in self.mounts_for(attempt) if one["target"] == "/output")
        content = {}
        for name in ("scale.py", "harness.py"):
            answer = stage_execution._git_run(["git", "-C", workspace, "show", checkpoint["head_object"] + ":" + name])
            self.assertEqual(answer["returncode"], 0)
            content[name] = {"text": answer["stdout"], "digest": digest_of_bytes(answer["stdout"].encode())}
        return {"content": content, "binding": binding, "receipt_bytes": body.decode(), "receipt": json.loads(body), "receipt_digest": digest_of_bytes(body), "receipt_entry": receipt["content_manifest"]["entries"][0], "assignment": assignment_of(held.control, attempt), "settlement": settlement, "checkpoint": review_cycles.checkpoint_of(held.control, settlement["evidence"]["checkpoint_id"])}

    def mounts_for(self, attempt):
        vectors = [argv for argv in self.engine.starts if "--entrypoint" not in argv and "baton.v12.runtime_attempt_id=" + attempt in argv]
        self.assertEqual(len(vectors), 1)
        argv = vectors[0]
        mounts = [dict(part.split("=", 1) if "=" in part else (part, True) for part in argv[index + 1].split(",")) for index, name in enumerate(argv[:-1]) if name == "--mount"]
        for mount in mounts:
            mount["readonly"] = mount.get("readonly") in (True, "true")
        return mounts

    def review(self, held, verdict):
        self.until(held, "review", "waiting")
        stage = next(one for one in submission.stages_of(held.job, "job-a") if one["kind"] == "review")
        episode = episodes.live_of(held.job, stage["stage_id"])
        attempt = episode["attempt_id"]
        worker = self.worker_of(held.composed, "review")
        launch = worker._adopted({"attempt_id": attempt, "job_id": "job-a"})
        self.assertNotIn("provider_context", launch.document)
        self.assertIsNone(context.context_invocation_of(held.control, attempt))
        implementation = episodes.live_of(held.job, "job-a/implementation")["attempt_id"]
        line = next(one["source"] for one in self.mounts_for(implementation) if one["target"] == "/output")
        mounts = self.mounts_for(attempt)
        for one in mounts:
            for forbidden in (line, str(self.context_root)):
                common = os.path.commonpath([os.path.realpath(one["source"]), os.path.realpath(forbidden)])
                if common in (os.path.realpath(one["source"]), os.path.realpath(forbidden)):
                    self.assertEqual(forbidden, line)
                    self.assertTrue(one.get("readonly"))
                    self.assertEqual(one["target"], "/input/source")
        source = next(one for one in mounts if one["target"] == "/input/source")
        self.assertTrue(source["readonly"])
        checkpoint = review_cycles.checkpoint_of(held.control, self.record(held.job, implementation)["settlement"]["evidence"]["checkpoint_id"])
        revision = stage_execution._git_run(["git", "-C", source["source"], "rev-parse", "HEAD"])
        self.assertEqual(revision["returncode"], 0)
        self.assertEqual(revision["stdout"].strip(), checkpoint["head_object"])
        self.review_evidence.append({"attempt_id": attempt, "implementation_attempt": implementation, "assignment": assignment_of(held.control, attempt), "launch": launch.document, "mounts": mounts, "producer_workspace": line, "private_context_root": str(self.context_root), "source_revision": revision["stdout"].strip(), "checkpoint_id": checkpoint["checkpoint_id"]})
        self.assertEqual(self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt), edits={"review-report.json": json.dumps(dict(self.REPORT, verdict=verdict))}), 0)
        return stage, episode, attempt

    def reopen(self, held, first, initial):
        """Close manager handles, preserving the external engine and call log."""
        from baton_v12.worker_manager.attempts import attempt_runtime_of
        before = {"provider": self.provider_events(), "engine": copy.deepcopy(self.engine.events)}
        self.assertTrue([one for one in before["provider"] if one["attempt_id"] == first])
        self.assertTrue([one for one in before["engine"] if one["attempt_id"] == first])
        runtime = attempt_runtime_of(held.control, first)
        old_job, old_control, old_composed = held.job, held.control, held.composed
        incarnation = old_control.incarnation
        paths = {"job": self.job_path, "control": self.control_path, "context": str(self.context_root)}
        before_tick = self.tick_count
        configuration_digest = digest_of_bytes(json.dumps(self.configuration, sort_keys=True).encode())
        old_composed.close(); old_job.close(); old_control.close()
        for owner in (old_job, old_control):
            with self.assertRaises(sqlite3.ProgrammingError):
                owner._connection.execute("SELECT 1")
        held = self.serving()
        self.assertIsNot(held.job, old_job)
        self.assertIsNot(held.control, old_control)
        self.assertIsNot(held.composed, old_composed)
        self.assertNotEqual(held.control.incarnation, incarnation)
        self.trace.scenario.reopen_at = self.tick_count
        self.trace.record(self.tick_count, "reopen", outcome="performed", attempt_id=first, operation_id="store.reopen:C2", evidence="closed-job-and-control-handles")
        after = {"provider": self.provider_events(), "engine": copy.deepcopy(self.engine.events)}
        self.assertEqual(before, after)
        reopened = self.snapshot(held, first)
        self.assertEqual(reopened, initial)
        self.assertEqual(attempt_runtime_of(held.control, first), runtime)
        # Execute a real scheduler observation after recomposition. Immediate
        # constructor equality alone cannot prove an old runtime is not restarted.
        self.tick(held)
        observed = {"provider": self.provider_events(), "engine": copy.deepcopy(self.engine.events)}
        return held, {"kind": "manager recomposition in one process", "performed": True, "old_handles_closed": True, "fresh_handles": True, "incarnations": [incarnation, held.control.incarnation], "before_tick": before_tick, "after_tick": self.tick_count, "before_paths": paths, "after_paths": {"job": self.job_path, "control": self.control_path, "context": str(self.context_root)}, "configuration_before": configuration_digest, "configuration_after": digest_of_bytes(json.dumps(self.configuration, sort_keys=True).encode()), "before": before, "after": after, "observed": observed, "durable_before": initial, "durable_after": reopened, "runtime_before": runtime, "runtime_after": attempt_runtime_of(held.control, first)}

    def run_scenario(self, *, counted_reopen=False):
        if counted_reopen:
            self.trace.scenario.name = "counted-reopen"
            self.trace.scenario.note["boundary"] = "manager recomposition in one process; no host or power loss"
        held = self.serving()
        submit(held.job, self.submission)
        self.until(held, "implementation", "waiting")
        first = self.only_attempt(held.composed, "implementation")
        def edits(multiplier):
            return {"scale.py": f"def scale(value):\n    return value * {multiplier}\n", "harness.py": f"from scale import scale\nassert scale(7) == {multiplier * 7}\nassert scale(-2) == {-2 * multiplier}\nprint('verified multiplier {multiplier}')\n"}
        self.assertEqual(self.turn(held.control, "implementation", first, self.mounted(held.composed, "implementation", first), edits=edits(2)), 0)
        self.until(held, "implementation", "completed")
        initial = self.snapshot(held, first)
        boundary = None
        if counted_reopen:
            held, boundary = self.reopen(held, first, initial)
        reviewed_stage, review_episode, reviewer = self.review(held, "changes-requested")
        self.until(held, "implementation", "waiting")
        implementation = submission.stages_of(held.job, "job-a")[0]
        second = episodes.live_of(held.job, implementation["stage_id"])["attempt_id"]
        correction = ending.settlement_of(held.job, reviewed_stage["stage_id"], review_episode["episode"])
        verdict = review_cycles.verdict_of(held.control, correction["evidence"]["verdict_id"])
        self.assertEqual(correction["evidence"]["routed"], second)
        self.assertEqual(self.turn(held.control, "implementation", second, self.mounted(held.composed, "implementation", second), edits=edits(3)), 0)
        self.until(held, "implementation", "completed")
        revised = self.snapshot(held, second)
        accepted_stage, accepted_episode, accepted_attempt = self.review(held, "accepted")
        judged = set()
        while self.tick_count < 100:
            self.tick(held)
            for key, execution in list(held.composed.deployment.judges.items()):
                if key not in judged:
                    self.judgment_turn(held, execution)
                    judged.add(key)
            state = self.states(held.job, held.composed)["integration"]
            if state == "exceptional":
                break
            if state == "completed":
                attempt = episodes.live_of(held.job, "job-a/integration")["attempt_id"]
                if integration_capacity_of(held.job, "integration:" + attempt)["root"]["lifecycle"] == "ended":
                    break
            time.sleep(.02)
        if self.states(held.job, held.composed)["integration"] == "exceptional":
            meaningful = [one for one in self.reports if one.get("started") or one.get("spoken") or one.get("acts")]
            logs = {p.name: p.read_text() for p in Path(self.root).glob("*.log")}
            parent = held.composed.deployment._integration_operations
            if isinstance(parent, stage_execution._PerJobIntegration):
                parent = parent.held["job-a"]
            retained = {key: reconciliation.managed_result_of(held.composed.deployment.integration, key) for key in parent._preparation.adopted}
            stage = next(one for one in submission.stages_of(held.job, "job-a") if one["kind"] == "integration")
            episode = episodes.live_of(held.job, stage["stage_id"])
            from baton_v12.job_manager.projection import stage_states
            from baton_v12.worker_manager import attempt_start_failure_of
            record = {"ending": ending.ending_of(held.job, stage["stage_id"], episode["episode"]), "failure": attempt_start_failure_of(held.control, episode["attempt_id"]), "projection": stage_states(held.job, held.composed), "apply": [(one.request, one.operations._worker.observed_exchange({"attempt_id": attempt})) for attempt, one in getattr(held.composed.integrator, "managed_runtimes", {}).items()]}
            self.fail(json.dumps({"reports": meaningful[-1:], "logs": logs, "retained": retained, "integration_attempt": record}, indent=2))
        self.assertEqual(self.states(held.job, held.composed)["integration"], "completed")
        deployment = held.composed.deployment
        parent = deployment._integration_operations
        if isinstance(parent, stage_execution._PerJobIntegration):
            parent = parent.held["job-a"]
        result_ids = list(parent._preparation.adopted)
        self.assertEqual(len(result_ids), 1)
        result = reconciliation.managed_result_of(deployment.integration, result_ids[0])
        target = stage_execution._git_run(["git", "--git-dir=" + self.target, "show", "refs/heads/main:scale.py"])
        self.assertEqual(target["returncode"], 0)
        self.assertEqual(target["stdout"], edits(3)["scale.py"])
        accepted = ending.settlement_of(held.job, accepted_stage["stage_id"], accepted_episode["episode"])
        accepted_verdict = review_cycles.verdict_of(held.control, accepted["evidence"]["verdict_id"])
        from baton_v12.job_manager.projection import stage_states
        final = stage_states(held.job, held.composed)["job-a/integration"]
        apply_attempt = result["phases"]["apply"]["task"]["execution_attempt_id"]
        apply_frozen = frozen_output_of(held.control, apply_attempt)
        apply_manifest = load_manifest(held.control, apply_frozen["manifest_digest"], "resultManifest")
        apply_launch = self.engine.launches[apply_attempt]
        apply_mounts = self.mounts_for(apply_attempt)
        output = next(one["source"] for one in apply_mounts if one["target"] == "/output")
        self.assertFalse(os.path.lexists(os.path.join(output, "provider-context-receipt")))
        publication = reconciliation.publication_of(deployment.integration, result_ids[0], "apply")
        publication_receipt = deployment.reconciliation_profile.publication_receipt(self.target, publication_id=publication["publication_id"])
        judgments = {kind: deployment.authority.receipt(result["derived_proposal_id"], kind) for kind in ("verification", "review", "approval")}
        artifact = {"accepted": accepted, "accepted_verdict": accepted_verdict, "reviews": self.review_evidence, "final": final, "apply": {"launch": apply_launch, "mounts": apply_mounts, "manifest": apply_manifest, "receipt_path_exists": False}, "publication": publication, "publication_receipt": publication_receipt, "judgments": judgments, "schema": SCHEMA, "scheduler": self.trace.artifact(), "initial": initial, "revised": revised, "correction": correction, "verdict": verdict, "review_assignment": assignment_of(held.control, reviewer), "final_counters": {"provider": self.provider_events(), "engine": self.engine.events}, "verifications": self.verifications, "managed": result, "capacity": integration_capacity_of(held.job, result_ids[0]), "target": {"revision": deployment.reconciliation_profile.revision(self.target, "refs/heads/main"), "code_digest": digest_of_bytes(target["stdout"].encode()), "authority_revision": deployment.authority.canonical_target(), "receipt": deployment.authority.receipt(result["derived_proposal_id"], "integration")}, "ticks": self.tick_count}
        if counted_reopen:
            artifact["reopen"] = boundary
        return artifact


def validate(artifact, *, counted_reopen=False):
    """Re-derive C1 relationships from exported records, without live owners.

    This is a consistency oracle, not a signature scheme. Provenance is bound
    separately by the supervised export and candidate hashes. C2 callers must
    select counted_reopen, so deleting the boundary cannot downgrade the oracle.
    No producer private state is read here.
    """
    failures = []
    def require(condition, code):
        if not condition:
            failures.append({"code": code})
    try:
        require(artifact["schema"] == SCHEMA, "C1-schema")
        failures.extend(scheduler_trace.validate(artifact["scheduler"]))
        require(0 < artifact["ticks"] <= 100, "C1-ticks")
        initial, revised = artifact["initial"], artifact["revised"]
        require(initial["content"]["scale.py"]["digest"] != revised["content"]["scale.py"]["digest"], "C1-code-unchanged")
        require(initial["checkpoint"]["line_id"] == revised["checkpoint"]["line_id"], "C1-line")
        require(initial["settlement"]["episode"] == 1 and revised["settlement"]["episode"] == 2, "C1-episodes")
        for snapshot in (initial, revised):
            content, checkpoint = snapshot["content"], snapshot["checkpoint"]
            binding, receipt = snapshot["binding"], snapshot["receipt"]
            attempt = snapshot["settlement"]["attempt_id"]
            require(binding["attempt_id"] == snapshot["assignment"]["runtime_attempt_id"] == attempt, "C1-attempt")
            require(snapshot["settlement"]["evidence"]["checkpoint_id"] == checkpoint["checkpoint_id"], "C1-checkpoint")
            require(checkpoint["checkpoint_digest"] == digest(checkpoint["evidence"]), "C1-checkpoint-digest")
            require(checkpoint["fence_digest"] == digest(checkpoint["fence"]) and checkpoint["fence"]["intent"]["attempt_id"] == attempt, "C1-checkpoint-fence")
            for item in content.values():
                require(digest_of_bytes(item["text"].encode()) == item["digest"], "C1-code-digest")
            verifications = [one for one in artifact["verifications"] if one["attempt_id"] == attempt]
            require(len(verifications) == 1, "C1-verifier-missing")
            if len(verifications) == 1:
                one = verifications[0]
                measured = {name: value["digest"] for name, value in content.items()}
                require(one["execution"] == "real subprocess" and one["seconds"] > 0 and one["status"] == 0 and one["argv"] == ["python3", "harness.py"], "C1-verifier-execution")
                require(one["before"] == one["after"] == measured and one["code_digest"] == measured["scale.py"] and one["verifier_digest"] == measured["harness.py"], "C1-verifier-bytes")
            body = snapshot["receipt_bytes"].encode()
            require(json.loads(body) == receipt and digest_of_bytes(body) == snapshot["receipt_digest"] == snapshot["receipt_entry"]["content_digest"] and len(body) == snapshot["receipt_entry"]["bytes"], "C1-context-receipt")
            require(receipt["complete"] is True and receipt["status"] == 0 and receipt["terminal"] == "success", "C1-context-terminal")
            for key in ("attempt_id", "use_id", "invocation_id", "conversation_id", "invocation_binding_digest", "delivery_digest", "argv_digest", "mode"):
                require(receipt[key] == binding[key], "C1-context-binding")
        require(initial["binding"]["mode"] == "open" and revised["binding"]["mode"] == "restore" and initial["binding"]["context_id"] == revised["binding"]["context_id"], "C1-context-continuity")

        def verdict_matches(verdict, settlement, snapshot, disposition):
            checkpoint = snapshot["checkpoint"]
            require(verdict["verdict_id"] == settlement["evidence"]["verdict_id"] and verdict["disposition"] == disposition, "C1-verdict")
            for key in ("checkpoint_id", "checkpoint_digest", "line_id", "revision", "base_object", "head_object", "tree_object", "path_set_digest"):
                require(verdict[key] == checkpoint[key], "C1-verdict-attribution")
            require(verdict["review_result"]["attempt_id"] == settlement["attempt_id"] and verdict["review_result"]["manifest_digest"] == settlement["evidence"]["manifest_digest"], "C1-review-result")
            require(verdict["review_result_digest"] == digest(verdict["review_result"]) and verdict["review_fence_digest"] == digest(verdict["review_fence"]), "C1-review-digest")
            reviews = [one for one in artifact["reviews"] if one["attempt_id"] == settlement["attempt_id"]]
            require(len(reviews) == 1, "C1-review-missing")
            if len(reviews) == 1:
                one = reviews[0]; launch = one["launch"]; assignment = one["assignment"]
                require(one["implementation_attempt"] == snapshot["settlement"]["attempt_id"] and one["checkpoint_id"] == checkpoint["checkpoint_id"] and one["source_revision"] == checkpoint["head_object"], "C1-review-source")
                require(assignment["participant"] == verdict["reviewer_participant"] and assignment["principal"] == verdict["reviewer_principal"] and assignment["generation"] == verdict["review_assignment_generation"], "C1-review-identity")
                require(assignment["participant"] != snapshot["assignment"]["participant"] and assignment["principal"] != snapshot["assignment"]["principal"], "C1-review-isolation")
                require(launch["role"] == "review" and launch["schema"] != "baton.worker-launch/4" and "provider_context" not in launch and launch["job_execution"]["attempt_id"] == one["attempt_id"], "C1-review-context")
                source = [m for m in one["mounts"] if m["target"] == "/input/source"]
                require(len(source) == 1 and source[0].get("readonly") is True, "C1-review-mount")
                for mount in one["mounts"]:
                    # Pure lexical comparison of exported absolute paths; no
                    # filesystem resolution can change this oracle's answer.
                    origin = os.path.normpath(mount["source"])
                    private = os.path.normpath(one["private_context_root"])
                    line = os.path.normpath(one["producer_workspace"])
                    require(os.path.commonpath([origin, private]) not in (origin, private) and not mount["target"].startswith("/run/baton/context"), "C1-review-context")
                    if os.path.commonpath([origin, line]) in (origin, line):
                        require(mount.get("readonly") is True and mount["target"] == "/input/source", "C1-review-writable-line")
        correction = artifact["correction"]
        verdict_matches(artifact["verdict"], correction, initial, "changes-requested")
        require(correction["evidence"]["outcome"] == "correction" and correction["evidence"]["routed"] == revised["settlement"]["attempt_id"], "C1-correction-route")
        verdict_matches(artifact["accepted_verdict"], artifact["accepted"], revised, "accepted")

        managed = artifact["managed"]; target = artifact["target"]
        require(managed["state"] == "imported" and managed["source_checkpoint_id"] == revised["checkpoint"]["checkpoint_id"] and managed["source_verdict_id"] == artifact["accepted_verdict"]["verdict_id"] and managed["source_candidate"] == revised["checkpoint"]["head_object"], "C1-managed-source")
        require(managed["source_checkpoint_digest"] == revised["checkpoint"]["checkpoint_digest"], "C1-managed-checkpoint")
        prepared = managed["prepared"]; phases = managed["phases"]
        require(set(phases) == {"prepare", "apply"}, "C1-managed-phases")
        report = phases["prepare"]["result"]["report"]
        require(report["kind"] == "measured" and report["completed"] == [{"name": "combined", "status": 0}, {"name": "base", "status": 1}, {"name": "isolated", "status": 0}] and report["status"] == 1 and report["not_run"] == [], "C1-preparation")
        require(phases["apply"]["result"]["report"]["status"] == 0 and phases["apply"]["task"]["parent"]["collected_digest"] == phases["prepare"]["result"]["collected"]["manifest_digest"], "C1-apply-parent")
        for state in ("combined", "isolated"):
            entries = {one["path"]: one["content_digest"] for one in prepared["preparation"]["states"][state]["content"]["entries"]}
            require(all(entries[name] == item["digest"] for name, item in revised["content"].items()), "C1-prepared-bytes")
        require(target["code_digest"] == revised["content"]["scale.py"]["digest"], "C1-target-bytes")
        require(target["revision"] == target["authority_revision"] == prepared["head"] and prepared["tree"] == revised["checkpoint"]["tree_object"], "C1-target-revision")
        for kind, expected in (("verification", "passed"), ("review", "accepted"), ("approval", "approved"), ("integration", "integrated")):
            receipt = target["receipt"] if kind == "integration" else artifact["judgments"][kind]
            require(receipt["kind"] == kind and receipt["disposition"] == expected and receipt["candidate_digest"] == target["revision"] and receipt["proposal_id"] == managed["derived_proposal_id"] and receipt["target"] == managed["target_revision"], "C1-target-receipt")
            require(receipt["actor"] != revised["assignment"]["participant"] and bool(receipt["decision"]["principal"]), "C1-judgment-independence")
        publication = artifact["publication"]; local = artifact["publication_receipt"]["document"]
        require(publication["state"] == "settled" and publication["imported_revision"] == target["revision"] and publication["managed_result_id"] == managed["managed_result_id"], "C1-publication")
        require(local["apply"] == phases["apply"] and local["preparation"] == phases["prepare"] and local["publication"]["publication_id"] == publication["publication_id"] and local["publication"]["imported_revision"] == target["revision"] and local["exclusion"]["excluded"] is True, "C1-local-receipt")
        verification = publication["settlement"]["verification"]
        require(verification["status"] == 0 and verification["unchanged"] is True and verification["candidate"] == target["revision"] and verification["harness_digest"] == revised["content"]["harness.py"]["digest"], "C1-import-verification")
        final = artifact["final"]; completion = final["observed"]["integration"]["completion"]
        require(final["state"] == "completed" and completion["integration_receipt_id"] == target["receipt"]["receipt_id"] and completion["managed_result_id"] == managed["managed_result_id"] and completion["execution_runtime"] == "destroyed", "C1-final")
        require(artifact["capacity"]["root"]["lifecycle"] == "ended" and all(m["state"] == "ended" and m["outcome"] == "succeeded" for m in artifact["capacity"]["members"]), "C1-capacity")
        apply = artifact["apply"]
        require(apply["launch"]["role"] == "integration" and apply["launch"]["schema"] != "baton.worker-launch/4" and "provider_context" not in apply["launch"], "C1-apply-context")
        receipt = [one for one in apply["manifest"]["outputs"] if one["name"] == "provider-context-receipt"]
        require(len(receipt) == 1 and receipt[0]["status"] == "missing-optional" and apply["receipt_path_exists"] is False, "C1-apply-receipt")
        require(all(not m["target"].startswith("/run/baton/context") for m in apply["mounts"]), "C1-apply-context")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        failures.append({"code": "C1-incomplete-evidence", "detail": str(error)})
    if counted_reopen:
        failures.extend(validate_reopen(artifact))
    return failures


def validate_reopen(artifact):
    """Count raw process/engine observations independently of owner sessions."""
    failures = []
    def require(condition, code):
        if not condition:
            failures.append({"code": code})
    try:
        boundary = artifact["reopen"]
        initial, revised = artifact["initial"], artifact["revised"]
        first, second = initial["binding"], revised["binding"]
        require(boundary["kind"] == "manager recomposition in one process" and boundary["performed"] is True and boundary["old_handles_closed"] is True and boundary["fresh_handles"] is True, "C2-reopen")
        require(len(boundary["incarnations"]) == 2 and all(boundary["incarnations"]) and boundary["incarnations"][0] != boundary["incarnations"][1], "C2-reopen")
        require(boundary["configuration_before"] == boundary["configuration_after"], "C2-configuration")
        require(boundary["before_paths"] == boundary["after_paths"] and set(boundary["before_paths"]) == {"job", "control", "context"}, "C2-durable-paths")
        require(0 < boundary["before_tick"] < boundary["after_tick"] <= artifact["ticks"], "C2-reopen")
        records = [one for one in artifact["scheduler"]["records"] if one["act"] == "reopen"]
        require(len(records) == 1 and records[0]["outcome"] == "performed" and records[0]["attempt_id"] == first["attempt_id"] and records[0]["tick"] == boundary["before_tick"], "C2-reopen")
        require(boundary["durable_before"] == boundary["durable_after"] == initial, "C2-durable-attribution")
        require(boundary["runtime_before"] == boundary["runtime_after"] and boundary["runtime_before"]["attempt_id"] == first["attempt_id"], "C2-runtime")
        require(first["attempt_id"] != second["attempt_id"] and first["use_id"] != second["use_id"] and first["invocation_id"] != second["invocation_id"], "C2-distinct-use")

        streams = [boundary[key] for key in ("before", "after", "observed")] + [artifact["final_counters"]]
        def events(stream, name, attempt):
            return [one for one in stream[name] if one["attempt_id"] == attempt]
        for name in ("provider", "engine"):
            baseline = events(streams[0], name, first["attempt_id"])
            require(len(baseline) == 1, "C2-positive-baseline")
            for stream in streams[1:]:
                require(events(stream, name, first["attempt_id"]) == baseline, "C2-" + name + "-duplicate")
            # The boundary itself starts nothing. Later real scheduler ticks
            # may launch review/correction, but the old attempt must stay fixed.
            require(streams[0][name] == streams[1][name], "C2-" + name + "-duplicate")
            require(not events(streams[0], name, second["attempt_id"]), "C2-new-use-order")
            require(len(events(streams[-1], name, second["attempt_id"])) == 1, "C2-" + name + "-new-use")

        for stream in streams:
            # Changing one attribution operand must not hide a repeated use
            # from an attempt-only filter. Count every matching identity axis.
            for binding in (first, second):
                matched = events(stream, "provider", binding["attempt_id"])
                for key in ("use_id", "invocation_id"):
                    require([one for one in stream["provider"] if one[key] == binding[key]] == matched, "C2-provider-attribution")
            operations = [one["operation_operand"] for one in stream["engine"]]
            require(all(operations.count(value) == 1 for value in operations), "C2-engine-duplicate")
            for one in stream["engine"]:
                argv = one["argv"]
                labels = dict(argv[index + 1].split("=", 1) for index, arg in enumerate(argv[:-1]) if arg == "--label")
                require(argv[1] == "run" and digest(argv) == one["argv_digest"] and labels == one["labels"] and labels["baton.v12.runtime_attempt_id"] == one["attempt_id"], "C2-engine-input")
                require(one["operation_operand"] == argv[argv.index("--name") + 1] and one["operation_operand"].startswith("baton-runtime.start-"), "C2-engine-operation")
            for binding in (first, second):
                for one in events(stream, "provider", binding["attempt_id"]):
                    argv = one["argv"]
                    require(one["role"] == "implementation" and type(one["pid"]) is int and one["pid"] > 0, "C2-provider-process")
                    require(one["use_id"] == binding["use_id"] and one["invocation_id"] == binding["invocation_id"] and one["conversation_id"] == binding["conversation_id"], "C2-provider-attribution")
                    require(digest(argv) == one["argv_digest"] == binding["argv_digest"], "C2-provider-operands")
                    selector = "--session-id" if binding["mode"] == "open" else "--resume"
                    require(argv[0] == "claude" and argv[-3:-1] == [selector, binding["conversation_id"]] and one["selector"] == selector and one["restored"] is (binding["mode"] == "restore"), "C2-provider-operands")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        failures.append({"code": "C2-incomplete-evidence", "detail": str(error)})
    return failures
