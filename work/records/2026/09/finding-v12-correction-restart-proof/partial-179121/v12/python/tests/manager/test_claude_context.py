"""B: real serving/worker/owner paths, simulated engine and provider process.

No production CLI or manager/runtime UID qualification is claimed. Only the
adapter's explicit unqualified-OCI guard is replaced for the simulated engine;
all launch, mount, runtime, exchange, retention and ending checks still execute.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.job_manager import submit, sweep, ending, submission, episodes
from baton_v12.worker_manager import provider_context as context, context_delivery as custody
from baton_v12.worker_manager import oci, frozen_output_of, load_manifest
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from tests.manager.test_provider_context import profile
from tests.tools.test_stage_execution import ComposedOneJobCase
from tests.job_manager import fixtures
from tools import stage_execution, single_worker


def declaration():
    return {"name": "provider-context-receipt", "type": "directory-result", "path": "provider-context-receipt", "required": False, "constraints": {"max_bytes": 16384, "max_entries": 1, "allowed_media_types": ["application/json"], "link_policy": "forbid", "validator_digest": None}}


class ServingContextCase(ComposedOneJobCase):
    def setUp(self):
        super().setUp()
        self.context_root = Path(self.root) / "private-contexts"
        self.context_root.mkdir(mode=0o700)
        self.calls = Path(self.root) / "actual-provider-calls.jsonl"
        self.model_output = None
        self.actual_environments = []
        manifest = copy.deepcopy(self.manifest)
        manifest["outputs"].append(declaration())
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        self.manifest = self.config["input_manifest"] = manifest
        self.submission["jobs"][0]["input_digest"] = manifest["manifest_digest"]
        self.context_profile = profile(runtime_profile_digest=self.config["profile_digest"], image_digest=self.config["image_digest"], adapter_digest=self.config["adapter_digest"], retention_policy_digest=self.config["retention_policy_digest"], argv_policy_digest=digest(context.ARGV_POLICY), environment_policy_digest=digest(context.ENVIRONMENT_POLICY))
        self.context_digest = digest(self.context_profile)
        patch = mock.patch.object(oci.OciAdapter, "_context_execution", return_value=None)
        patch.start()
        self.addCleanup(patch.stop)

    def worker(self, role, **members):
        held = super().worker(role, **members)
        if role == "implementation":
            held["deployment"].update(schema=single_worker.CONTEXT_CONFIG_SCHEMA, provider_context={"mode": "required", "storage": str(self.context_root), "profile_digest": self.context_digest})
        return held

    def serving(self, **members):
        self.engine = self.quiescing()
        job, control = self.stores("context-serving")
        configure_workspace_storage(control, self.storage)
        custody.configure_context_storage(control, str(self.context_root), excluded_roots=[self.source, self.storage], runtime_uid=os.getuid())
        context.certify_context_profile(control, self.context_profile)
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base, **members), job, control, engine_run=self.engine, credential_provider=lambda provider, reference: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return job, control, composed

    def provider(self, edits=None, status=0):
        original = super().provider(edits=edits, status=status)
        def run(argv, **options):
            if argv[0] != "claude" or "--model" not in argv:
                return original(argv, **options)
            self.actual_environments.append(dict(options["env"]))
            # A real child reads/restores private bytes and records actual argv.
            script = '''import json,os,sys
from pathlib import Path
argv,edits,calls,override,status=json.loads(sys.argv[1])
session=argv[-2]
state=Path(os.environ["HOME"])/".claude/projects/output/session.json"
previous=json.loads(state.read_text()) if state.exists() else None
assert (previous is not None)==("--resume" in argv)
if previous: assert previous["session"]==session
state.parent.mkdir(parents=True,exist_ok=True)
for parent in (state.parent,state.parent.parent): parent.chmod(0o700)
state.write_text(json.dumps({"session":session,"private":"PRIVATE-CONTEXT-MARKER","turn":1 if previous is None else previous["turn"]+1}))
state.chmod(0o600)
for name,body in edits.items(): Path(name).write_text(body)
with open(calls,"a") as f: f.write(json.dumps({"argv":argv,"restored":previous is not None})+"\\n")
print(override if override is not None else json.dumps({"type":"result","subtype":"success","is_error":False,"session_id":session,"model":"deterministic-model"}))
sys.exit(status)
'''
            return subprocess.run([sys.executable, "-c", script, json.dumps([argv, edits or {}, str(self.calls), self.model_output, status])], **options)
        return run

    def turn(self, control, role, attempt_id, roots, **operands):
        import claude_agent
        binding = context.context_invocation_of(control, attempt_id)
        if binding is None:
            return super().turn(control, role, attempt_id, roots, **operands)
        delivery = custody.context_mount_of(control, custody.configured_context_storage(control), attempt_id=attempt_id)
        with mock.patch.object(claude_agent, "CONTEXT_ROOT", delivery.boundary()[0]):
            return super().turn(control, role, attempt_id, roots, **operands)

    def started(self):
        job, control, composed = self.serving()
        submit(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        attempt = self.only_attempt(composed, "implementation")
        return job, control, composed, attempt, self.mounted(composed, "implementation", attempt)

    def drive(self, job, composed, kind, want, ticks=10):
        reports = []
        for unused in range(ticks):
            reports.append(sweep(job, composed, now=fixtures.NOW))
            if self.states(job, composed).get(kind) == want:
                return self.states(job, composed)
        self.fail(f"{kind} did not reach {want}: {reports}")

    def record(self, job, attempt):
        stage = submission.stages_of(job, "job-a")[0]
        episode = next(one for one in episodes.episodes_of(job, stage["stage_id"]) if one["attempt_id"] == attempt) if hasattr(episodes, "episodes_of") else episodes.live_of(job, stage["stage_id"])
        return ending.ending_of(job, stage["stage_id"], episode["episode"])


class ServingBinding(ServingContextCase):
    def test_real_composition_binds_exact_task_prompt_argv_and_adoption(self):
        import claude_agent
        job, control, composed, attempt, roots = self.started()
        bound = context.context_invocation_of(control, attempt)
        self.assertEqual(bound["task_digest"], digest_of_bytes(self.task_bytes))
        self.assertEqual(context.context_prompt(json.loads(self.task_bytes)), claude_agent._prompt(json.loads(self.task_bytes)))
        self.assertEqual(bound["prompt_digest"], digest_of_bytes(claude_agent._prompt(json.loads(self.task_bytes)).encode()))
        worker = self.worker_of(composed, "implementation")
        self.assertEqual(worker._adopted({"attempt_id": attempt, "job_id": "job-a"}).document["provider_context"], bound)


class WorkerInvocation(ServingContextCase):
    def test_real_worker_retains_measured_receipt_and_finalizes_before_settlement(self):
        held = self.implemented()
        self.assertEqual(context.context_use_of(held.control, held.attempt_id)["status"], "ready")
        self.assertIsNotNone(self.record(held.job, held.attempt_id)["settlement"])
        frozen = frozen_output_of(held.control, held.attempt_id)
        manifest = load_manifest(held.control, frozen["manifest_digest"], "resultManifest")
        receipt = next(one for one in manifest["outputs"] if one["name"] == "provider-context-receipt")
        body = custody.read_context_receipt(held.control, attempt_id=held.attempt_id, artifact_id=receipt["artifact"]["artifact_id"], workspace_storage=self.storage)
        value = json.loads(body)
        self.assertEqual(value["schema"], context.SERVING_RECEIPT_SCHEMA)
        self.assertTrue(value["complete"])
        self.assertEqual(value["observed_conversation_id"], value["conversation_id"])
        self.assertNotIn(b"PRIVATE-CONTEXT-MARKER", body)
        self.assertEqual(len(self.calls.read_text().splitlines()), 1)
        self.assertEqual(len(self.actual_environments), 1)
        self.assertNotIn(self.actual_environments[0]["HOME"], self.actual_environments[0]["TMPDIR"])
