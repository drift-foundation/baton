"""C extends the scheduler trace with measured process and owner evidence.

The provider is a deterministic local child; the OCI engine is simulated.
Preparation and apply execute their real worker entrypoints as local children.
This proves manager recomposition, not host-loss or production qualification.
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
record={'attempt_id':attempt,'role':role,'pid':os.getpid(),'use_id':None,'invocation_id':None,'argv_digest':digest(argv),'selector':None,'conversation_id':None,'restored':False}
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

    def __call__(self, argv, **options):
        if argv[1] in ("stop", "rm") and argv[-1] in self.processes:
            process, log = self.processes[argv[-1]]
            if argv[1] == "rm" and process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
        answer = super().__call__(argv, **options)
        if argv[1] != "run" or "--entrypoint" in argv:
            return answer
        labels, mounts = {}, {}
        for index, arg in enumerate(argv[:-1]):
            if arg == "--label":
                key, value = argv[index + 1].split("=", 1)
                labels[key] = value
            if arg == "--mount":
                parts = dict(part.split("=", 1) for part in argv[index + 1].split(",") if "=" in part)
                mounts[parts["target"]] = parts["source"]
        attempt = labels["baton.v12.runtime_attempt_id"]
        self.events.append({"attempt_id": attempt, "operation_id": labels.get("baton.v12.start_operation_id"), "argv_digest": digest(list(argv)), "labels": labels})
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
            answer = original(argv, **options)
            if list(argv[:2]) == ["python3", "harness.py"]:
                root = Path(options["cwd"])
                self.verifications.append({"attempt_id": self.active_attempt, "status": answer.returncode, "code_digest": digest_of_bytes((root / "scale.py").read_bytes()), "verifier_digest": digest_of_bytes((root / "harness.py").read_bytes()), "argv": list(argv)})
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
        return {"binding": binding, "receipt": json.loads(body), "receipt_digest": digest_of_bytes(body), "receipt_entry": receipt["content_manifest"]["entries"][0], "assignment": assignment_of(held.control, attempt), "settlement": settlement, "checkpoint": review_cycles.checkpoint_of(held.control, settlement["evidence"]["checkpoint_id"])}

    def review(self, held, verdict):
        self.until(held, "review", "waiting")
        stage = next(one for one in submission.stages_of(held.job, "job-a") if one["kind"] == "review")
        episode = episodes.live_of(held.job, stage["stage_id"])
        attempt = episode["attempt_id"]
        worker = self.worker_of(held.composed, "review")
        launch = worker._adopted({"attempt_id": attempt, "job_id": "job-a"})
        self.assertNotIn("provider_context", launch.document)
        self.assertIsNone(context.context_invocation_of(held.control, attempt))
        self.assertEqual(self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt), edits={"review-report.json": json.dumps(dict(self.REPORT, verdict=verdict))}), 0)
        return stage, episode, attempt

    def reopen(self, held, first, initial):
        """Retained draft for C2; C1 never calls this boundary."""
        before = {"provider": self.provider_events(), "engine": copy.deepcopy(self.engine.events)}
        old_job, old_control, old_composed = held.job, held.control, held.composed
        old_composed.close(); old_job.close(); old_control.close()
        for owner in (old_job, old_control):
            with self.assertRaises(sqlite3.ProgrammingError):
                owner._connection.execute("SELECT 1")
        held = self.serving()
        self.trace.scenario.reopen_at = self.tick_count
        self.trace.record(self.tick_count, "reopen", outcome="performed", evidence="closed-job-and-control-handles")
        after = {"provider": self.provider_events(), "engine": copy.deepcopy(self.engine.events)}
        self.assertEqual(self.snapshot(held, first), initial)
        return held, before, after

    def run_scenario(self):
        held = self.serving()
        submit(held.job, self.submission)
        self.until(held, "implementation", "waiting")
        first = self.only_attempt(held.composed, "implementation")
        def edits(multiplier):
            return {"scale.py": f"def scale(value):\n    return value * {multiplier}\n", "harness.py": f"from scale import scale\nassert scale(7) == {multiplier * 7}\nassert scale(-2) == {-2 * multiplier}\nprint('verified multiplier {multiplier}')\n"}
        self.assertEqual(self.turn(held.control, "implementation", first, self.mounted(held.composed, "implementation", first), edits=edits(2)), 0)
        self.until(held, "implementation", "completed")
        initial = self.snapshot(held, first)
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
        self.review(held, "accepted")
        judged = set()
        while self.tick_count < 100:
            self.tick(held)
            for key, execution in list(held.composed.deployment.judges.items()):
                if key not in judged:
                    self.judgment_turn(held, execution)
                    judged.add(key)
            if self.states(held.job, held.composed)["integration"] in ("completed", "exceptional"):
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
        return {"schema": SCHEMA, "scheduler": self.trace.artifact(), "initial": initial, "revised": revised, "correction": correction, "verdict": verdict, "review_assignment": assignment_of(held.control, reviewer), "final_counters": {"provider": self.provider_events(), "engine": self.engine.events}, "verifications": self.verifications, "managed": result, "capacity": integration_capacity_of(held.job, result_ids[0]), "target": {"revision": deployment.reconciliation_profile.revision(self.target, "refs/heads/main"), "code_digest": digest_of_bytes(target["stdout"].encode()), "authority_revision": deployment.authority.canonical_target(), "receipt": deployment.authority.receipt(result["derived_proposal_id"], "integration")}, "ticks": self.tick_count}


def validate(artifact):
    """Companion checks use the exported bytes only, never live owner handles."""
    failures = list(scheduler_trace.validate(artifact["scheduler"]))
    if artifact.get("schema") != SCHEMA:
        failures.append({"code": "C-schema"})
    return failures
