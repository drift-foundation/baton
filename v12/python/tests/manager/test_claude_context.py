"""B: real serving/worker/owner paths, simulated engine and provider process.

No production CLI or manager/runtime UID qualification is claimed. Legacy
deterministic fixtures substitute the OCI context guard. ManagedSessionResume
uses the real candidate grant guard; all launch, mount, runtime, exchange,
retention and ending checks execute.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest import mock

from baton_v12.contracts import (ContractRefusal, digest, digest_of_bytes,
                                 job_input_identity)
from baton_v12.job_manager import submit, sweep, ending, submission, episodes
from baton_v12.worker_manager import provider_context as context, context_delivery as custody
from baton_v12.worker_manager import oci, frozen_output_of, load_manifest
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from tests.manager.test_provider_context import profile
from tests.tools.test_stage_execution import ComposedOneJobCase
from tests.job_manager import fixtures
from tools import stage_execution, single_worker


def declaration():
    return {"name": "provider-context-receipt", "type": "directory-result", "path": "provider-context-receipt", "required": False, "constraints": {"max_bytes": 16384, "max_entries": 1, "allowed_media_types": ["application/octet-stream"], "link_policy": "forbid", "validator_digest": None}}


class ServingContextCase(ComposedOneJobCase):
    def setUp(self):
        super().setUp()
        self.context_root = Path(self.root) / "private-contexts"
        self.context_root.mkdir(mode=0o700)
        self.calls = Path(self.root) / "actual-provider-calls.jsonl"
        self.model_output = None
        self.terminal_fields = {"model": "deterministic-model"}
        self.state_path = ".claude/projects/output/session.json"
        self.provider_records = []
        self.actual_environments = []
        manifest = copy.deepcopy(self.manifest)
        manifest["outputs"].append(declaration())
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        self.manifest = self.config["input_manifest"] = manifest
        # W202663: THE JOB NAMES ITS INPUT'S JOB-SCOPED PROJECTION. The whole
        # manifest digest is the WORKER's runtime identity and is asserted as
        # such further down, where the launch's `runtime_input_digest` is read.
        self.submission["jobs"][0]["input_digest"] = job_input_identity(
            manifest)
        self.context_profile = profile(runtime_profile_digest=self.config["profile_digest"], image_digest=self.config["image_digest"], adapter_digest=self.config["adapter_digest"], retention_policy_digest=self.config["retention_policy_digest"], argv_policy_digest=digest(context.ARGV_POLICY), environment_policy_digest=digest(context.ENVIRONMENT_POLICY))
        self.context_digest = digest(self.context_profile)
        # W177936: the REAL boundary function, captured before the patch so
        # the qualification cases can drive it while the composed flow keeps
        # its explicit substitution.
        self.real_context_execution = oci.OciAdapter._context_execution
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
argv,edits,calls,override,status,state_path,fields=json.loads(sys.argv[1])
session=argv[-2]
state=Path(os.environ["HOME"])/state_path.replace("{conversation_id}",session)
previous=json.loads(state.read_text()) if state.exists() else None
assert (previous is not None)==("--resume" in argv)
if previous: assert previous["session"]==session
state.parent.mkdir(parents=True,exist_ok=True)
for extra in ("memory",): (state.parent/extra).mkdir(exist_ok=True)
for extra in ("backups","shell-snapshots","sessions","session-env"): (Path(os.environ["HOME"])/".claude"/extra).mkdir(parents=True,exist_ok=True)
state.write_text(json.dumps({"session":session,"private":"PRIVATE-CONTEXT-MARKER","turn":1 if previous is None else previous["turn"]+1}))
for name,body in edits.items(): Path(name).write_text(body)
terminal=override if override is not None else json.dumps({"type":"result","subtype":"success","is_error":False,"session_id":session,**fields})
with open(calls,"a") as f: f.write(json.dumps({"argv":argv,"restored":previous is not None,"terminal":terminal+"\\n"})+"\\n")
print(terminal)
sys.exit(status)
'''
            result = subprocess.run([sys.executable, "-c", script, json.dumps([argv, edits or {}, str(self.calls), self.model_output, status, self.state_path, self.terminal_fields])], **options)
            self.provider_records.append(json.loads(self.calls.read_text().splitlines()[-1])["terminal"].encode())
            return result
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
        episode = next(one for one in episodes.episodes_of(job, stage["stage_id"]) if one["attempt_id"] == attempt)
        return ending.ending_of(job, stage["stage_id"], episode["episode"])

    def reopen(self, job, control, composed):
        composed.close()
        job.close()
        control.close()
        job, control = self.stores("context-reopened")
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control, engine_run=self.engine, credential_provider=lambda provider, reference: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return job, control, composed

    def retained_receipt(self, control, attempt):
        frozen = frozen_output_of(control, attempt)
        manifest = load_manifest(control, frozen["manifest_digest"], "resultManifest")
        output = next(one for one in manifest["outputs"] if one["name"] == "provider-context-receipt")
        return json.loads(custody.read_context_receipt(control, attempt_id=attempt, artifact_id=output["artifact"]["artifact_id"], workspace_storage=self.storage))

    def calls_count(self):
        return len(self.calls.read_text().splitlines()) if self.calls.exists() else 0

    def assert_owed(self, job, control, attempt):
        record = self.record(job, attempt)
        self.assertTrue(record is None or record["settlement"] is None)
        self.assertNotEqual(context.context_use_of(control, attempt)["status"], "ready")

    def assert_reported_and_held(self, job, control, composed, attempt):
        """The corrected contract for a turn that ANSWERED and did not
        complete. W239528, owner pass 242683.

        THE SUBJECT IS UNCHANGED and is still asserted: an unhealthy provider
        terminal is not accepted, and its context use is never `ready`. A
        generation whose turn cannot be accounted for stays held, and nothing
        here finalizes one.

        WHAT CHANGED IS THE STAGE. These cases used to assert the ending
        obligation stays owed, which meant the stage projected `answering`
        forever: `review_driver.end_implementation` published
        unconditionally, `integration.retain_proposal` refuses a result that
        is not `completed`, and the ending never reached its own last two acts
        -- fencing the assignment and authorizing cleanup. The owner ran that
        path live with an expired OAuth token: the provider failed in 31 ms,
        the adapter answered `unable`, and the deployment reported nothing for
        the full 900-second bound and left the runtime standing.

        So the ending finishes and SAYS SO. The stage reports `exceptional` --
        the manager's own projection of an `unable` frozen result -- while the
        context use stays held. Two different facts, and this asserts both.

        `assert_owed` is kept for the cases that genuinely still owe an
        ending: a COMPLETED turn whose context finalization refuses reaches a
        different branch, which this correction did not touch.
        """
        self.assertNotEqual(
            context.context_use_of(control, attempt)["status"], "ready")
        self.assertEqual(
            self.states(job, composed).get("implementation"), "exceptional")

    def fault_tick(self, job, composed):
        # Process-loss injection may propagate or be reported by the sweep.
        try:
            return sweep(job, composed, now=fixtures.NOW)
        except RuntimeError as error:
            self.assertEqual(str(error), "injected manager loss")


class ServingBinding(ServingContextCase):
    def test_current_authority_change_between_preparation_and_start_refuses(self):
        job, control, composed = self.serving()
        submit(job, self.submission)
        original = stage_execution.StageComposition.revalidate_context
        fenced = []
        def changed(stage, worker, held):
            current = worker.port.assignment_of(self.work, self.config["authority_uuid"])
            worker.port.cancel(current, "context-prestart-fence", "test ownership changed", self.work, self.config["authority_uuid"])
            fenced.append(held["attempt_id"])
            return original(stage, worker, held)
        with mock.patch.object(stage_execution.StageComposition, "revalidate_context", changed):
            for unused in range(5):
                sweep(job, composed, now=fixtures.NOW)
                if fenced:
                    break
        self.assertEqual(len(fenced), 1)
        self.assertEqual(self.calls_count(), 0)
        self.assertEqual(len(self.engine.starts), 0)
        binding = context.context_invocation_of(control, fenced[0])
        self.assertIsNotNone(binding)
        job, control, composed = self.reopen(job, control, composed)
        for unused in range(2):
            sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(context.context_invocation_of(control, fenced[0]), binding)
        self.assertEqual(len(self.engine.starts), 0)

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
        self.assertEqual(receipt["artifact"]["media_type"], "application/octet-stream")
        self.assertNotIn(b"PRIVATE-CONTEXT-MARKER", body)
        self.assertEqual(len(self.calls.read_text().splitlines()), 1)
        self.assertEqual(len(self.actual_environments), 1)
        self.assertNotIn(self.actual_environments[0]["HOME"], self.actual_environments[0]["TMPDIR"])

    def test_duplicate_exchange_cannot_call_the_provider_again(self):
        job, control, composed, attempt, roots = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"}), 0)
        self.assertEqual(self.turn(control, "implementation", attempt, roots), 0)
        self.assertEqual(self.calls_count(), 1)
        self.drive(job, composed, "implementation", "completed")

    def terminal_refuses(self, value, status=0):
        job, control, composed, attempt, roots = self.started()
        bound = context.context_invocation_of(control, attempt)
        good = {"type": "result", "subtype": "success", "is_error": False, "session_id": bound["conversation_id"], "model": "deterministic-model"}
        self.model_output = value(good)
        self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"}, status=status)
        for unused in range(3):
            sweep(job, composed, now=fixtures.NOW)
        # W239528: REPORTED AND HELD, rather than owed forever.
        self.assert_reported_and_held(job, control, composed, attempt)
        self.assertEqual(self.calls_count(), 1)

    def test_status_zero_with_wrong_uuid_is_unhealthy(self):
        self.terminal_refuses(lambda good: json.dumps(dict(good, session_id="00000000-0000-4000-8000-000000000000")))

    def test_nonzero_with_success_terminal_is_unhealthy(self):
        self.terminal_refuses(json.dumps, status=1)

    def test_status_zero_with_changed_model_is_healthy_and_truthful(self):
        self.terminal_fields = {"model": "foreign-model"}
        held = self.implemented()
        self.assertEqual(context.context_use_of(held.control, held.attempt_id)["status"], "ready")
        receipt = self.retained_receipt(held.control, held.attempt_id)
        self.assertEqual(receipt["model"], "deterministic-model")
        self.assertEqual(receipt["observed_model"], "foreign-model")

    def test_status_zero_without_model_is_healthy_and_diagnostics_are_bound(self):
        self.terminal_fields = {"modelUsage": {"opus": {"inputTokens": 3}, "haiku": {"inputTokens": 2}}}
        held = self.implemented()
        receipt = self.retained_receipt(held.control, held.attempt_id)
        self.assertTrue(receipt["complete"])
        self.assertIsNone(receipt["observed_model"])
        self.assertEqual(receipt["model_diagnostics_digest"], digest(self.terminal_fields))
        self.assertEqual(receipt["provider_result_digest"], digest_of_bytes(self.provider_records[0]))

    def test_status_zero_with_error_is_unhealthy(self):
        self.terminal_refuses(lambda good: json.dumps(dict(good, is_error=True)))

    def test_missing_terminal_is_unhealthy(self):
        self.terminal_refuses(lambda good: "")

    def test_partial_terminal_is_unhealthy(self):
        self.terminal_refuses(lambda good: json.dumps(good)[:-2])

    def test_duplicate_terminal_keys_are_unhealthy(self):
        self.terminal_refuses(lambda good: json.dumps(good)[:-1] + ',"is_error":false}')

    def test_oversized_terminal_is_unhealthy(self):
        import claude_agent
        self.terminal_refuses(lambda good: json.dumps(dict(good, result="x" * (claude_agent.MAX_PROVIDER_RECORD + 1))))

    def test_nonfinite_terminal_numbers_are_unhealthy(self):
        self.terminal_refuses(lambda good: json.dumps(good)[:-1] + ',"modelUsage":{"tokens":1e999}}')

    def test_historical_v2_receipt_still_validates_its_original_model_contract(self):
        import claude_agent
        original = claude_agent.ClaudeAgent._context_result
        def legacy(agent, *args, **kwargs):
            receipt = original(agent, *args, **kwargs)
            receipt["schema"] = context.LEGACY_SERVING_RECEIPT_SCHEMA
            del receipt["model_diagnostics_digest"], receipt["provider_result_digest"]
            return receipt
        with mock.patch.object(claude_agent.ClaudeAgent, "_context_result", legacy):
            held = self.implemented()
        self.assertEqual(context.context_use_of(held.control, held.attempt_id)["status"], "ready")
        self.assertEqual(self.retained_receipt(held.control, held.attempt_id)["schema"], context.LEGACY_SERVING_RECEIPT_SCHEMA)

    def test_intent_before_child_loss_never_reinvokes_the_use(self):
        import claude_agent
        job, control, composed, attempt, roots = self.started()
        original = claude_agent.ClaudeAgent._context_intent
        def lost(agent, bound):
            original(agent, bound)
            raise claude_agent.TaskRefusal("injected loss after invocation intent")
        with mock.patch.object(claude_agent.ClaudeAgent, "_context_intent", lost):
            self.turn(control, "implementation", attempt, roots)
        self.turn(control, "implementation", attempt, roots)
        for unused in range(3):
            sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)
        self.assertEqual(self.calls_count(), 0)
        delivery = custody.context_mount_of(control, custody.configured_context_storage(control), attempt_id=attempt)
        with mock.patch.object(claude_agent, "CONTEXT_ROOT", delivery.boundary()[0]), mock.patch.object(claude_agent, "CREDENTIAL_ROOT", os.path.join(self.root, "credential-" + attempt[:12])):
            with self.assertRaises(claude_agent.TaskRefusal) as refused:
                claude_agent.ClaudeAgent()._context_intent(context.context_invocation_of(control, attempt))
        self.assertIn("already intended", str(refused.exception))


class ServingEnding(ServingContextCase):
    def test_failed_runtime_removal_keeps_context_and_ending_unsettled(self):
        job, control, composed, attempt, roots = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"}), 0)
        engine_type = type(self.engine)
        original = engine_type.__call__
        def refused(engine, argv, **kwargs):
            if argv[1] == "rm":
                return engine_type.answer(status=1, stderr="simulated removal failure")
            return original(engine, argv, **kwargs)
        with mock.patch.object(engine_type, "__call__", refused):
            sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)
        self.assertEqual(self.calls_count(), 1)

    def sealed_fault(self, mutate):
        import claude_agent
        job, control, composed, attempt, roots = self.started()
        original = claude_agent.ClaudeAgent._publish_context_receipt
        def faulty(agent):
            original(agent)
            mutate(Path(claude_agent.OUTPUT_ROOT) / "provider-context-receipt")
        with mock.patch.object(claude_agent.ClaudeAgent, "_publish_context_receipt", faulty):
            self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"})
        for unused in range(3):
            sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)
        self.assertEqual(self.calls_count(), 1)
        job, control, composed = self.reopen(job, control, composed)
        sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)
        self.assertEqual(self.calls_count(), 1)

    def test_sealed_malformed_json_is_not_context_evidence(self):
        self.sealed_fault(lambda root: (root / "receipt.json").write_text("{incomplete"))

    def test_sealed_excessive_json_depth_is_not_context_evidence(self):
        self.sealed_fault(lambda root: (root / "receipt.json").write_text("[" * 2000 + "0" + "]" * 2000))

    def test_sealed_wrong_argv_binding_is_not_context_evidence(self):
        def changed(root):
            path = root / "receipt.json"
            body = json.loads(path.read_text())
            body["argv_digest"] = "sha256:" + "f" * 64
            path.write_text(json.dumps(body))
        self.sealed_fault(changed)

    def test_sealed_duplicate_json_is_not_context_evidence(self):
        def duplicate(root):
            path = root / "receipt.json"
            path.write_text(path.read_text().rstrip()[:-1] + ',"complete":true}')
        self.sealed_fault(duplicate)

    def test_sealed_foreign_receipt_is_not_context_evidence(self):
        def foreign(root):
            path = root / "receipt.json"
            body = json.loads(path.read_text())
            body["attempt_id"] = "another-attempt"
            path.write_text(json.dumps(body))
        self.sealed_fault(foreign)

    def test_sealed_legacy_receipt_cannot_downgrade_serving_evidence(self):
        def legacy(root):
            path = root / "receipt.json"
            body = json.loads(path.read_text())
            body["schema"] = context.RECEIPT_SCHEMA
            path.write_text(json.dumps(body))
        self.sealed_fault(legacy)

    def test_sealed_wrong_filename_is_not_context_evidence(self):
        self.sealed_fault(lambda root: (root / "receipt.json").rename(root / "wrong.json"))

    def test_worker_extra_entries_cannot_pass_collection(self):
        self.sealed_fault(lambda root: (root / "extra").write_text("unexpected"))

    def test_worker_oversized_receipt_cannot_pass_collection(self):
        self.sealed_fault(lambda root: (root / "receipt.json").write_text("x" * 16385))

    def test_worker_link_cannot_pass_collection(self):
        def link(root):
            (root / "receipt.json").unlink()
            (root / "receipt.json").symlink_to("../harness.py")
        self.sealed_fault(link)

    def test_missing_optional_answer_cannot_finalize_implementation(self):
        import claude_agent
        job, control, composed, attempt, roots = self.started()
        original = claude_agent.ClaudeAgent.work
        def withheld(agent, *args, **kwargs):
            value = original(agent, *args, **kwargs)
            root = Path(claude_agent.OUTPUT_ROOT) / "provider-context-receipt"
            (root / "receipt.json").unlink()
            root.rmdir()
            for one in value["outputs"]:
                if one["name"] == "provider-context-receipt":
                    one["status"] = "missing-optional"
            return value
        with mock.patch.object(claude_agent.ClaudeAgent, "work", withheld):
            self.assertEqual(self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"}), 0)
        sweep(job, composed, now=fixtures.NOW)
        frozen = frozen_output_of(control, attempt)
        manifest = load_manifest(control, frozen["manifest_digest"], "resultManifest")
        self.assertEqual(next(one for one in manifest["outputs"] if one["name"] == "provider-context-receipt")["status"], "missing-optional")
        self.assert_owed(job, control, attempt)
        job, control, composed = self.reopen(job, control, composed)
        sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)

    def cut(self, window):
        job, control, composed, attempt, roots = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"}), 0)
        if window == "before-publication":
            patch = mock.patch.object(custody, "seal_generation", side_effect=RuntimeError("injected manager loss"))
        elif window == "after-publication":
            original = context._transition
            def transition(*args, **kwargs):
                if kwargs.get("action") == "finalize":
                    raise RuntimeError("injected manager loss")
                return original(*args, **kwargs)
            patch = mock.patch.object(context, "_transition", transition)
        else:
            patch = mock.patch.object(stage_execution.StageComposition, "_finished", side_effect=RuntimeError("injected manager loss"))
        with patch:
            self.fault_tick(job, composed)
        self.assertIsNone(self.record(job, attempt)["settlement"])
        self.assertFalse(Path(roots["inputs"]).exists())
        self.assertEqual(self.calls_count(), 1)
        starts = len(self.engine.starts)
        job, control, composed = self.reopen(job, control, composed)
        # Historical ending must not require re-materialization or admission.
        with mock.patch.object(context, "admit_context_use", side_effect=AssertionError("fresh admission on reopen")), mock.patch.object(single_worker.launch, "materialize", side_effect=AssertionError("launch recreation on reopen")):
            sweep(job, composed, now=fixtures.NOW)
        self.assertIsNotNone(self.record(job, attempt)["settlement"])
        self.assertEqual(context.context_use_of(control, attempt)["status"], "ready")
        self.assertEqual(self.calls_count(), 1)
        self.assertEqual(len(self.engine.starts), starts)

    def test_reopen_before_generation_publication(self):
        self.cut("before-publication")

    def test_reopen_after_publication_before_context_commit(self):
        self.cut("after-publication")

    def test_reopen_after_context_commit_before_settlement(self):
        self.cut("after-commit")

    def retained_fault(self, mutate, *, committed=False):
        job, control, composed, attempt, roots = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"}), 0)
        target, name = (stage_execution.StageComposition, "_finished") if committed else (custody, "seal_generation")
        with mock.patch.object(target, name, side_effect=RuntimeError("injected manager loss")):
            self.fault_tick(job, composed)
        from baton_v12.worker_manager import intake_receipt_of
        artifact = next(one for one in intake_receipt_of(control, attempt)["artifacts"] if one["custody_locator"].endswith("/provider-context-receipt"))
        root = Path(artifact["custody_locator"][len("file://"):])
        root.chmod(0o700)
        mutate(root)
        root.chmod(0o500)
        job, control, composed = self.reopen(job, control, composed)
        starts = len(self.engine.starts)
        sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)
        self.assertEqual(context.context_use_of(control, attempt)["status"], "held")
        self.assertEqual(self.calls_count(), 1)
        self.assertEqual(len(self.engine.starts), starts)

    def test_retained_changed_bytes_block_reopened_ending(self):
        def corrupt(root):
            path = root / "receipt.json"
            path.chmod(0o600)
            path.write_text("{}")
            path.chmod(0o400)
        self.retained_fault(corrupt)

    def test_retained_missing_file_blocks_reopened_ending(self):
        self.retained_fault(lambda root: (root / "receipt.json").unlink())

    def test_retained_extra_entry_blocks_reopened_ending(self):
        self.retained_fault(lambda root: (root / "extra").write_text("unexpected"))

    def test_retained_link_blocks_reopened_ending(self):
        def link(root):
            path = root / "receipt.json"
            path.rename(root / "original")
            path.symlink_to("original")
        self.retained_fault(link)

    def test_committed_context_does_not_bypass_missing_retained_receipt(self):
        self.retained_fault(lambda root: (root / "receipt.json").unlink(), committed=True)


class RestoredCorrectionBoundary(ServingContextCase):
    FINDINGS = "adjust the implementation"

    def corrected_ready(self):
        """The flow to a BOUND correction: episode 1 served, a
        changes-requested review frozen, the restore use admitted,
        materialized and bound -- the second turn NOT yet run. W177936's
        feedback cases all start here."""
        held = self.implemented()
        first = context.context_invocation_of(held.control, held.attempt_id)
        self.drive(held.job, held.composed, "review", "waiting")
        reviewer = self.only_attempt(held.composed, "review")
        self.assertIsNone(context.context_invocation_of(held.control, reviewer))
        review_launch = self.worker_of(held.composed, "review")._adopted({"attempt_id": reviewer, "job_id": "job-a"}).document
        self.assertNotIn("provider_context", review_launch)
        self.assertNotEqual(review_launch["session"], self.worker_of(held.composed, "implementation")._session_of(held.attempt_id))
        self.assertEqual(review_launch["job_execution"]["runtime_input_digest"], self.manifest["manifest_digest"])
        self.assertEqual(self.turn(held.control, "review", reviewer, self.mounted(held.composed, "review", reviewer), edits={"review-report.json": json.dumps({"schema": "baton.review-report/1", "verdict": "changes-requested", "findings": self.FINDINGS})}), 0)
        self.drive(held.job, held.composed, "implementation", "waiting", ticks=12)
        attempts = self.worker_of(held.composed, "implementation").stage._prepared
        [second] = [one for one in attempts if one != held.attempt_id]
        return held, first, reviewer, second

    def feedback_file(self, held, second):
        bound = context.context_use_of(held.control, second)
        return (self.context_root / bound["context_id"] / "uses"
                / bound["use_id"] / "feedback")

    def test_actual_changes_requested_review_restores_only_fresh_implementation_use(self):
        held, first, reviewer, second = self.corrected_ready()
        review_frozen = frozen_output_of(held.control, reviewer)
        review_result = load_manifest(held.control, review_frozen["manifest_digest"], "resultManifest")
        self.assertEqual(next(one for one in review_result["outputs"] if one["name"] == "provider-context-receipt")["status"], "missing-optional")
        review_start = [one for one in self.engine.starts if "--entrypoint" not in one][1]
        self.assertFalse(any("/run/baton/context" in item for item in review_start))
        bound = context.context_invocation_of(held.control, second)
        self.assertEqual(bound["conversation_id"], first["conversation_id"])
        self.assertEqual(bound["context_id"], first["context_id"])
        self.assertEqual(bound["mode"], "restore")
        for key in ("attempt_id", "use_id", "invocation_id", "delivery_digest"):
            self.assertNotEqual(bound[key], first[key])
        import claude_agent
        original = claude_agent.ClaudeAgent.work
        faults = []
        def observed(agent, *args, **kwargs):
            try:
                return original(agent, *args, **kwargs)
            except Exception as error:
                import traceback
                faults.append(traceback.format_exc())
                raise
        with mock.patch.object(claude_agent.ClaudeAgent, "work", observed):
            self.assertEqual(self.turn(held.control, "implementation", second, self.mounted(held.composed, "implementation", second), edits={"harness.py": "print('correction round')\n"}), 0, faults)
        self.drive(held.job, held.composed, "implementation", "completed")
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        self.assertEqual([one["restored"] for one in calls], [False, True])
        self.assertIn("--session-id", calls[0]["argv"])
        self.assertIn("--resume", calls[1]["argv"])
        # W177936: THE RESUMED CONVERSATION RECEIVES THE REVIEW'S FEEDBACK,
        # and the opening turn did not -- the whole point of the resumption.
        self.assertNotIn("THE REVIEW'S FINDINGS:", calls[0]["argv"][-1])
        self.assertIn("THE REVIEW'S FINDINGS:\n" + self.FINDINGS,
                      calls[1]["argv"][-1])
        self.assertIn(json.loads(self.task_bytes)["instructions"],
                      calls[1]["argv"][-1])
        self.assertNotEqual(self.actual_environments[0]["HOME"], self.actual_environments[1]["HOME"])
        original_state = self.context_root / first["context_id"] / "generations/1/state/.claude/projects/output/session.json"
        self.assertEqual(json.loads(original_state.read_text())["turn"], 1)
        self.assertEqual(json.loads((Path(self.actual_environments[1]["HOME"]) / ".claude/projects/output/session.json").read_text())["turn"], 2)

    def test_the_feedback_prompt_twins_agree(self):
        import claude_agent
        task = json.loads(self.task_bytes)
        self.assertEqual(context.context_prompt(task, self.FINDINGS),
                         claude_agent._prompt(task, self.FINDINGS))
        self.assertEqual(context.context_prompt(task),
                         claude_agent._prompt(task))

    def test_an_oversized_feedback_refuses_on_both_sides(self):
        import claude_agent
        task = json.loads(self.task_bytes)
        oversized = "x" * (context.MAX_FEEDBACK_BYTES + 1)
        with self.assertRaises(Exception):
            context.context_prompt(task, oversized)
        with self.assertRaises(claude_agent.TaskRefusal):
            claude_agent._prompt(task, oversized)

    def test_a_tampered_feedback_file_refuses_before_the_provider(self):
        held, first, reviewer, second = self.corrected_ready()
        place = self.feedback_file(held, second)
        self.assertTrue(place.exists())
        place.chmod(0o600)
        place.write_text("do something else entirely")
        calls_before = len(self.calls.read_text().splitlines()) \
            if self.calls.exists() else 0
        self.assertNotEqual(
            self.turn(held.control, "implementation", second,
                      self.mounted(held.composed, "implementation", second),
                      edits={"harness.py": "print('never runs')\n"}), 0)
        calls_after = len(self.calls.read_text().splitlines()) \
            if self.calls.exists() else 0
        # THE PROVIDER NEVER RAN: the digest gate refused first.
        self.assertEqual(calls_before, calls_after)

    def test_a_missing_feedback_file_refuses_by_name(self):
        held, first, reviewer, second = self.corrected_ready()
        place = self.feedback_file(held, second)
        place.chmod(0o600)
        place.unlink()
        calls_before = len(self.calls.read_text().splitlines()) \
            if self.calls.exists() else 0
        self.assertNotEqual(
            self.turn(held.control, "implementation", second,
                      self.mounted(held.composed, "implementation", second),
                      edits={"harness.py": "print('never runs')\n"}), 0)
        self.assertEqual(
            calls_before,
            len(self.calls.read_text().splitlines())
            if self.calls.exists() else 0)

    def test_a_stray_feedback_file_on_an_open_turn_refuses(self):
        import claude_agent, tempfile
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "feedback").write_text("unexpected")
            agent = claude_agent.ClaudeAgent(run=lambda *a, **k: None)
            with mock.patch.object(claude_agent, "CONTEXT_ROOT", root):
                with self.assertRaisesRegex(
                        claude_agent.TaskRefusal, "open invocation"):
                    agent._context_feedback({"mode": "open"})

    def test_a_fifo_at_the_feedback_name_refuses_without_blocking(self):
        """Review231132 [R1]: a blocking open ran before every gate. The
        nonblocking open cannot block on a FIFO and `fstat` refuses it by
        name, on BOTH modes -- proven here with a real FIFO and no writer,
        the exact shape that hung the reviewer's supervised probe."""
        import claude_agent, tempfile
        for mode in ("restore", "open"):
            with tempfile.TemporaryDirectory() as root:
                os.mkfifo(Path(root) / "feedback")
                agent = claude_agent.ClaudeAgent(run=lambda *a, **k: None)
                with mock.patch.object(claude_agent, "CONTEXT_ROOT", root):
                    with self.assertRaises(claude_agent.TaskRefusal):
                        agent._context_feedback({"mode": mode})

    def test_a_fifo_replacing_the_delivered_feedback_refuses_the_turn(self):
        """The composed half of the same regression: the correction turn
        meets the FIFO, refuses before the provider, and does not hang."""
        held, first, reviewer, second = self.corrected_ready()
        place = self.feedback_file(held, second)
        place.chmod(0o600)
        place.unlink()
        os.mkfifo(place)
        calls_before = len(self.calls.read_text().splitlines()) \
            if self.calls.exists() else 0
        self.assertNotEqual(
            self.turn(held.control, "implementation", second,
                      self.mounted(held.composed, "implementation", second),
                      edits={"harness.py": "print('never runs')\n"}), 0)
        self.assertEqual(
            calls_before,
            len(self.calls.read_text().splitlines())
            if self.calls.exists() else 0)

    def test_a_wrong_or_stale_verdict_refuses_the_feedback_resolution(self):
        held, first, reviewer, second = self.corrected_ready()
        genuine = context.review_cycles.verdict_of
        def stale(store, verdict_id):
            answer = dict(genuine(store, verdict_id))
            answer["checkpoint_id"] = "checkpoint-" + "0" * 64
            return answer
        jobs = self.worker_of(held.composed,
                              "implementation").stage.deployment.jobs
        with mock.patch.object(context.review_cycles, "verdict_of", stale):
            with self.assertRaisesRegex(
                    Exception, "verdict disagrees"):
                context.correction_feedback_of(held.control, jobs, second)

    def test_replay_never_overwrites_the_delivered_feedback(self):
        from baton_v12.worker_manager import context_delivery
        held, first, reviewer, second = self.corrected_ready()
        storage = context_delivery.configured_context_storage(held.control)
        # The same bytes replay as a no-op...
        context_delivery.deliver_feedback(
            held.control, storage, attempt_id=second,
            payload=self.FINDINGS.encode())
        # ...and different bytes refuse rather than replacing the delivery
        # (the custody writer's own collision rule: a size mismatch refuses
        # at the size gate, equal-size different bytes refuse at the byte
        # comparison -- either way nothing is overwritten).
        from baton_v12.contracts import ContractRefusal
        with self.assertRaises(ContractRefusal):
            context_delivery.deliver_feedback(
                held.control, storage, attempt_id=second,
                payload=b"a newly selected report")
        place = self.feedback_file(held, second)
        self.assertEqual(place.read_bytes(), self.FINDINGS.encode())


class CandidateQualificationFlow(RestoredCorrectionBoundary):
    """W177936 QUALIFICATION-CONTRACT-232133, corrected by review232154.

    The SAME composed open->changes-requested->restore flow, under a
    `candidate` profile and one journaled qualification grant -- the
    deterministic suite above is byte-for-byte untouched, which is itself
    the vocabulary's first promise.
    """

    RUN = "qual-run-232193"

    def setUp(self):
        super().setUp()
        self.mint_grant = True
        held = dict(self.context_profile)
        held["qualification"] = "candidate"
        self.context_profile = held
        self.context_digest = digest(held)

    def serving(self, **members):
        job, control, composed = super().serving(**members)
        if self.mint_grant:
            context.authorize_qualification_run(
                control, run_id=self.RUN,
                profile_digest=self.context_digest,
                storage_path=str(self.context_root), authority_uuid=self.config["authority_uuid"], job_id="job-a",
                note="the one qualification run this class drives")
        return job, control, composed

    def test_the_flow_opens_and_restores_on_one_grant(self):
        held, first, reviewer, second = self.corrected_ready()
        self.assertEqual(self.turn(
            held.control, "implementation", second,
            self.mounted(held.composed, "implementation", second),
            edits={"harness.py": "print('correction round')\n"}), 0)
        self.drive(held.job, held.composed, "implementation", "completed")
        chain = context._history(held.control,
                                 context.context_use_of(
                                     held.control, second)["context_id"])
        admits = [one for one in chain if one["action"] == "admit"]
        self.assertEqual(len(admits), 2)
        # THE OPEN CONSUMED THE GRANT AND THE RESTORE RODE IT: one run id,
        # journaled in both admissions' own committed payloads.
        self.assertEqual([one["payload"]["qualification_run"]
                          for one in admits], [self.RUN, self.RUN])

    def test_a_third_generation_refuses_the_grant_cap(self):
        held, first, reviewer, second = self.corrected_ready()
        profile = context.context_profile_of(held.control,
                                             self.context_digest)
        with self.assertRaisesRegex(Exception, "third generation"):
            context._qualified(
                held.control, None,
                {"profile_digest": self.context_digest,
                 "attempt_id": second},
                profile, 2,
                context.context_use_of(held.control,
                                       second)["context_id"])

    def test_without_a_grant_the_opening_admission_refuses(self):
        self.mint_grant = False
        with self.assertRaisesRegex(Exception,
                                    "no live qualification grant"):
            self.implemented()

    def test_a_fresh_run_id_is_a_new_grant_and_a_retry_replays(self):
        held, first, reviewer, second = self.corrected_ready()
        # Exact retry replays the committed grant...
        context.authorize_qualification_run(
            held.control, run_id=self.RUN,
            profile_digest=self.context_digest,
            storage_path=str(self.context_root), authority_uuid=self.config["authority_uuid"], job_id="job-a",
            note="the one qualification run this class drives")
        # ...changed operands under the same run identity refuse...
        with self.assertRaises(Exception):
            context.authorize_qualification_run(
                held.control, run_id=self.RUN,
                profile_digest=self.context_digest,
                storage_path=str(self.context_root), authority_uuid=self.config["authority_uuid"], job_id="job-a",
                note="a different note is a different act")
        # ...and a separately selected later run of the UNCHANGED profile
        # is a fresh grant under its own identity (review232154 R2).
        context.authorize_qualification_run(
            held.control, run_id="qual-run-later",
            profile_digest=self.context_digest,
            storage_path=str(self.context_root), authority_uuid=self.config["authority_uuid"], job_id="job-a",
            note="a later separately selected run")
        self.assertIsNotNone(context.qualification_grant_of(
            held.control, "qual-run-later"))

    def completed_qualification(self):
        held, first, reviewer, second = self.corrected_ready()
        self.assertEqual(self.turn(held.control, "implementation", second, self.mounted(held.composed, "implementation", second), edits={"harness.py": "print('correction round')\n"}), 0)
        self.drive(held.job, held.composed, "implementation", "completed")
        owner = context.context_use_of(held.control, second)["context_id"]
        chain = context._history(held.control, owner)
        finalized = [one for one in chain if one["action"] == "finalize"]
        admits = [one for one in chain if one["action"] == "admit"]
        results = []
        for index, admission in enumerate(admits):
            # Exact simulated provider bytes from the real worker invocation.
            attempt = admission["payload"]["attempt_id"]
            path = Path(self.config["launch_home"]) / "logs" / attempt / "provider.stdout.log"
            body = self.provider_records[index]
            path.write_bytes(body)
            results.append({"path": str(path), "bytes": len(body), "digest": digest_of_bytes(body)})
        report = {"schema": "baton.context-qualification-review/1", "run_id": self.RUN, "context_id": owner, "attempts": [one["payload"]["attempt_id"] for one in admits], "receipt_digests": [one["payload"]["receipt_digest"] for one in finalized], "generation_digests": [one["payload"]["manifest_digest"] for one in finalized], "provider_results": results, "recall": {"expected_digest": digest("synthetic-recall"), "observed_digest": digest("synthetic-recall"), "second_inputs_excluded": True}}
        self.drive(held.job, held.composed, "review", "waiting")
        reviewers = self.worker_of(held.composed, "review").stage._prepared
        [last_review] = [one for one in reviewers if one != reviewer]
        body = json.dumps({"schema": "baton.review-report/1", "verdict": "accepted", "findings": json.dumps(report)})
        self.assertEqual(self.turn(held.control, "review", last_review, self.mounted(held.composed, "review", last_review), edits={"review-report.json": body}), 0)
        self.drive(held.job, held.composed, "review", "completed")
        from baton_v12.worker_manager import attempts, review_cycles
        assignment = attempts.assignment_of(held.control, last_review)
        attachment = review_cycles.review_for_attempt(held.control, attempt_id=last_review, generation=assignment["generation"])
        verdict_id = review_cycles._id("verdict", {"attachment_id": attachment["attachment_id"], "disposition": "accepted"})
        verdict = review_cycles.verdict_of(held.control, verdict_id)
        frozen = load_manifest(held.control, verdict["review_result"]["manifest_digest"], "resultManifest")
        findings = next(one for one in frozen["outputs"] if one["name"] == "findings")
        report_digest = next(one["content_digest"] for one in findings["content_manifest"]["entries"] if one["path"] == "report.json")
        evidence = {"run_id": self.RUN, "context_id": owner, "continuity": {"verdict_id": verdict_id, "report_digest": report_digest}, "evidence_refs": [report_digest]}
        return held, evidence, report

    def test_certification_demands_retirement_and_retained_independent_evidence(self):
        held, evidence, report = self.completed_qualification()
        production = dict(self.context_profile, qualification="production")
        with self.assertRaisesRegex(ContractRefusal, "retired"):
            context.certify_production_profile(held.control, production, evidence)
        context.retire_context(held.control, evidence["context_id"])
        with self.assertRaisesRegex(ContractRefusal, "diverges"):
            context.certify_production_profile(held.control, dict(production, model="somebody-else"), evidence)
        with self.assertRaises(ContractRefusal):
            context.certify_production_profile(held.control, production, dict(evidence, continuity={"verdict_id": "nonexistent-review", "report_digest": digest("unbacked")}))
        context.certify_production_profile(held.control, production, evidence)
        context.certify_production_profile(held.control, production, evidence)
        self.assertIsNotNone(held.control.operation_record(context._id("context-certification", digest(production))))
        # Acceptance cannot turn missing original evidence into a valid retry.
        Path(report["provider_results"][0]["path"]).unlink()
        with self.assertRaisesRegex(ContractRefusal, "unavailable"):
            context.certify_production_profile(held.control, production, evidence)

    def test_certification_rejects_damaged_generation_receipt_report_and_provider_result(self):
        held, evidence, report = self.completed_qualification()
        context.retire_context(held.control, evidence["context_id"])
        production = dict(self.context_profile, qualification="production")
        from baton_v12.worker_manager import intake, review_cycles
        first = report["attempts"][0]
        receipt = next(one for one in intake.intake_receipt_of(held.control, first)["artifacts"] if one["custody_locator"].endswith("/provider-context-receipt"))
        verdict = review_cycles.verdict_of(held.control, evidence["continuity"]["verdict_id"])
        findings = next(one for one in verdict["review_result"]["artifacts"] if one["output_name"] == "findings")
        paths = [self.context_root / evidence["context_id"] / "generations/1/state/.claude/projects/output/session.json", Path(receipt["custody_locator"][7:]) / "receipt.json", Path(findings["locator"][7:]) / "report.json", Path(report["provider_results"][0]["path"])]
        for path in paths:
            with self.subTest(path=path.name):
                original, mode = path.read_bytes(), path.stat().st_mode & 0o777
                path.chmod(0o600)
                path.write_bytes(b"corrupted")
                path.chmod(mode)
                with self.assertRaises(ContractRefusal):
                    context.certify_production_profile(held.control, production, evidence)
                self.assertIsNone(held.control.operation_record(context._id("context-certification", digest(production))))
                path.chmod(0o600)
                path.write_bytes(original)
                path.chmod(mode)
        context.certify_production_profile(held.control, production, evidence)

    def test_the_launch_boundary_mints_and_demands_the_grant(self):
        held, first, reviewer, second = self.corrected_ready()
        grant = context.prove_context_execution(held.control, second)
        bound = context.context_use_of(held.control, second)
        self.assertEqual((grant.context_id, grant.use_id,
                          grant.qualification),
                         (bound["context_id"], bound["use_id"],
                          "candidate"))
        # Shape cannot manufacture the capability...
        with self.assertRaises(Exception):
            context.ExecutionGrant(object(), grant.context_id,
                                   grant.use_id, "candidate")
        # ...and the adapter refuses everything that is not the grant for
        # THIS delivered context.
        from baton_v12.worker_manager import oci as adapter_module
        holder = adapter_module.OciAdapter.__new__(
            adapter_module.OciAdapter)
        holder.context_execution = None
        holder.context_document = {"context_id": grant.context_id,
                                   "use_id": grant.use_id}
        with self.assertRaisesRegex(Exception, "awaits qualified"):
            self.real_context_execution(holder)
        holder.context_execution = grant
        self.real_context_execution(holder)
        holder.context_document = {"context_id": "context-other",
                                   "use_id": grant.use_id}
        with self.assertRaisesRegex(Exception, "does not name"):
            self.real_context_execution(holder)


class DeterministicProfilesNeverExecuteForReal(RestoredCorrectionBoundary):
    def test_prove_context_execution_refuses_deterministic(self):
        held = self.implemented()
        with self.assertRaisesRegex(Exception, "deterministic profiles"):
            context.prove_context_execution(held.control, held.attempt_id)


class ManagedSessionResume(ServingContextCase):
    """Real candidate grant, manager, worker, custody and independent review.

    Only the OCI engine and provider subprocess behavior are simulated.
    """
    RUN = "managed-correction-236087"
    FINDINGS = RestoredCorrectionBoundary.FINDINGS
    corrected_ready = RestoredCorrectionBoundary.corrected_ready
    completed_qualification = CandidateQualificationFlow.completed_qualification

    def setUp(self):
        super().setUp()
        self.state_path = ".claude/projects/-output/{conversation_id}.jsonl"
        self.context_profile = dict(self.context_profile, schema=context.SESSION_PROFILE_SCHEMA, qualification="candidate", state_paths=[self.state_path])
        self.context_digest = digest(self.context_profile)
        self.terminal_fields = {"modelUsage": {"opus": {"inputTokens": 3}, "haiku": {"inputTokens": 2}}}
        guard = mock.patch.object(oci.OciAdapter, "_context_execution", self.real_context_execution)
        guard.start()
        self.addCleanup(guard.stop)

    def serving(self, **members):
        job, control, composed = super().serving(**members)
        context.authorize_qualification_run(control, run_id=self.RUN, profile_digest=self.context_digest, storage_path=str(self.context_root), authority_uuid=self.config["authority_uuid"], job_id="job-a", note="one simulated managed correction with the real grant guard")
        return job, control, composed

    def test_managed_correction_and_independent_acceptance_without_model_label(self):
        held, evidence, report = self.completed_qualification()
        self.assertEqual(self.calls_count(), 2)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        self.assertEqual([one["restored"] for one in calls], [False, True])
        self.assertNotIn("THE REVIEW'S FINDINGS:", calls[0]["argv"][-1])
        self.assertIn("THE REVIEW'S FINDINGS:\n" + self.FINDINGS, calls[1]["argv"][-1])
        first, second = report["attempts"]
        one, two = [context.context_invocation_of(held.control, attempt) for attempt in (first, second)]
        self.assertEqual(one["conversation_id"], two["conversation_id"])
        for key in ("attempt_id", "use_id", "invocation_id", "delivery_digest"):
            self.assertNotEqual(one[key], two[key])
        path = self.state_path.replace("{conversation_id}", one["conversation_id"])
        for index in (1, 2):
            state = self.context_root / evidence["context_id"] / "generations" / str(index) / "state" / path
            self.assertEqual(json.loads(state.read_bytes())["turn"], index)
        self.assertNotEqual(self.actual_environments[0]["HOME"], self.actual_environments[1]["HOME"])
        from baton_v12.worker_manager import intake, attempts, review_cycles
        for attempt in (first, second):
            receipt = self.retained_receipt(held.control, attempt)
            self.assertTrue(receipt["complete"])
            self.assertIsNone(receipt["observed_model"])
            cleanup = intake.cleanup_of(held.control, attempt_id=attempt, retention_policy_digest=self.config["retention_policy_digest"])
            self.assertEqual(cleanup["state"], "absent")
            self.assertIn(cleanup["cleanup"], ("complete", "retained"))
            self.assertIsNotNone(self.record(held.job, attempt)["settlement"])
            self.assertEqual(attempts.attempt_runtime_of(held.control, attempt)["execution_runtime"], "destroyed")
            chain, admitted = context._use(held.control, attempt)
            self.assertEqual(review_cycles.writer_of(held.control, admitted["payload"]["writer_id"])["state"], "revoked")
        vectors = self.engine.vectors
        starts = [index for index, argv in enumerate(vectors) if argv[1] == "run" and "--entrypoint" not in argv]
        removals = [index for index, argv in enumerate(vectors) if argv[1] == "rm"]
        self.assertTrue(any(starts[0] < index < starts[1] for index in removals))
        self.assertTrue(any(starts[1] < index < starts[2] for index in removals))
        import claude_agent
        proposals = []
        for attempt in (first, second):
            frozen = frozen_output_of(held.control, attempt)
            manifest = load_manifest(held.control, frozen["manifest_digest"], "resultManifest")
            proposal = next(one for one in manifest["outputs"] if one["name"] == "proposal")
            self.assertEqual(proposal["status"], "present")
            claim = proposal["result_metadata"][claude_agent.CLAIM_NAMESPACE]
            self.assertEqual(claim["base"], self.base)
            proposals.append(claim["head"])
        self.assertNotEqual(*proposals)
        self.assertNotEqual(report["generation_digests"][0], report["generation_digests"][1])
        context.retire_context(held.control, evidence["context_id"])
        production = dict(self.context_profile, qualification="production")
        context.certify_production_profile(held.control, production, evidence)
        self.assertIsNotNone(held.control.operation_record(context._id("context-certification", digest(production))))

    def test_restore_changed_model_keeps_requested_binding(self):
        held, first, reviewer, second = self.corrected_ready()
        self.terminal_fields = {"model": "reported-other", "modelUsage": {"reported-other": {"inputTokens": 5}}}
        roots = self.mounted(held.composed, "implementation", second)
        self.assertEqual(self.turn(held.control, "implementation", second, roots, edits={"harness.py": "print('correction round')\n"}), 0)
        self.assertEqual(self.turn(held.control, "implementation", second, roots), 0)
        self.drive(held.job, held.composed, "implementation", "completed")
        self.assertEqual(self.calls_count(), 2)
        receipt = self.retained_receipt(held.control, second)
        self.assertTrue(receipt["complete"])
        self.assertEqual(receipt["observed_model"], "reported-other")
        self.assertEqual(receipt["model"], "deterministic-model")

    def test_measured_receipt_rejects_substituted_terminal_even_same_session(self):
        held = self.implemented()
        admitted = next(one for one in context._history(held.control, context.context_use_of(held.control, held.attempt_id)["context_id"]) if one["action"] == "admit")
        reader = lambda attempt, artifact: custody.read_context_receipt(held.control, attempt_id=attempt, artifact_id=artifact, workspace_storage=self.storage)
        actual = self.provider_records[0]
        context._receipt(held.control, admitted, reader, terminal_record=actual)
        changed = dict(json.loads(actual), model="unmeasured-label")
        with self.assertRaisesRegex(ContractRefusal, "differs from measured receipt"):
            context._receipt(held.control, admitted, reader, terminal_record=json.dumps(changed).encode())

    test_failed_runtime_removal_keeps_context_and_ending_unsettled = ServingEnding.test_failed_runtime_removal_keeps_context_and_ending_unsettled

    def test_wrong_session_on_restore_cannot_finalize_or_repeat(self):
        held, first, reviewer, second = self.corrected_ready()
        self.model_output = json.dumps({"type": "result", "subtype": "success", "is_error": False, "session_id": "00000000-0000-4000-8000-000000000000"})
        roots = self.mounted(held.composed, "implementation", second)
        self.turn(held.control, "implementation", second, roots, edits={"harness.py": "print('correction round')\n"})
        for unused in range(3):
            sweep(held.job, held.composed, now=fixtures.NOW)
        # W239528: the restore turn answered with a session this manager did
        # not open, so it is `unable`. CANNOT FINALIZE AND CANNOT REPEAT are
        # both still asserted below -- no second generation is written and the
        # provider is not called again -- and the stage now REPORTS the
        # failure instead of owing its ending forever. See
        # `assert_reported_and_held`.
        self.assert_reported_and_held(held.job, held.control, held.composed,
                                      second)
        self.assertEqual(self.calls_count(), 2)
        bound = context.context_use_of(held.control, second)
        self.assertFalse((self.context_root / bound["context_id"] / "generations/2").exists())

    def test_changed_reported_model_also_certifies_as_diagnostics(self):
        self.terminal_fields = {"model": "reported-other", "modelUsage": {"reported-other": {"inputTokens": 5}}}
        held, evidence, report = self.completed_qualification()
        context.retire_context(held.control, evidence["context_id"])
        context.certify_production_profile(held.control, dict(self.context_profile, qualification="production"), evidence)
        self.assertEqual(self.calls_count(), 2)

    def test_missing_conversation_file_cannot_be_replaced_by_another_session(self):
        job, control, composed, attempt, roots = self.started()
        self.state_path = ".claude/projects/-output/00000000-0000-4000-8000-000000000000.jsonl"
        self.turn(control, "implementation", attempt, roots, edits={"harness.py": "print('changed')\n"})
        for unused in range(3):
            sweep(job, composed, now=fixtures.NOW)
        self.assert_owed(job, control, attempt)
        bound = context.context_use_of(control, attempt)
        self.assertFalse((self.context_root / bound["context_id"] / "generations/1").exists())
