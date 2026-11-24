"""Simulated engine/provider; real admission, worker, freeze and ending owners."""
import copy
import json
import os
from pathlib import Path
import subprocess
from unittest import mock

from baton_v12 import provider_policy as policy
from baton_v12.contracts import digest
from baton_v12.contracts.manifest import job_input_identity
from baton_v12.job_manager import submit, sweep
from baton_v12.worker_manager import launch, model_attribution, provider_home
from tests.job_manager import fixtures
from tests.manager import provider_fixtures as fake
from tests.tools import test_stage_execution as existing
from tools import single_worker


class SelectedCase(existing.ComposedOneJobCase):
    def setUp(self):
        super().setUp()
        selected, value = fake.identities()
        profile = dict(value["runtime_profile"], image_digest=self.config["image_digest"], network=self.config["network"])
        adapter = policy.adapter(selected, network=self.config["network"])
        self.config.update(schema=single_worker.PROVIDER_CONFIG_SCHEMA, provider_context=None, verifier_layout=None,
            provider_contract={"selection": selected, "runtime_profile": profile, "adapter": adapter},
            provider_home_root=os.path.join(os.path.dirname(self.config["workspace_storage"]), "job-work"),
            profile_digest=digest(profile), adapter_digest=digest(adapter))
        manifest = copy.deepcopy(self.config["input_manifest"])
        manifest.update(runtime_profile_digest=digest(profile), tool_policy_digest=digest(policy.POLICY))
        manifest.pop("manifest_digest"); manifest["manifest_digest"] = digest(manifest)
        self.config["input_manifest"] = self.manifest = manifest
        self.submission["jobs"][0]["input_digest"] = job_input_identity(manifest)
        for stage in self.submission["jobs"][0]["stages"]:
            stage["profile_digest"] = self.config["profile_digest"]
        self.reported = ["fixture-reported", "fixture-additional"]
        self.measured_build = "2.1.247"
        self.invocations = []
        self.keep_marker = b"simulated-session-only"

    def worker(self, role, **members):
        value = super().worker(role, **members)
        if role == "integration" and "provider_contract" in value["deployment"]:
            # This lane invokes no provider, but shares the Job tool policy.
            deployment = value["deployment"]
            deployment["schema"] = single_worker.LAYOUT_CONFIG_SCHEMA
            deployment.pop("provider_contract"); deployment.pop("provider_home_root")
        return value

    def provider_delivery_for(self, role, attempt):
        worker = self.worker_of(self.composed_for(role), role)
        return worker._provider_delivery({"attempt_id": attempt, **self.stage_for(attempt)})

    def stage_for(self, attempt):
        from baton_v12.job_manager import scheduler, submission
        jobs = self.worker_of(self._composed, "implementation").stage.deployment.jobs
        allocation = scheduler.allocation_of(jobs, attempt)
        return next(one for one in submission.stage_rows(jobs) if one["stage_id"] == allocation["stage_id"])

    def provider(self, **operands):
        original = super().provider(**operands)
        def run(argv, **options):
            if argv[0] != "claude":
                return original(argv, **options)
            self.invocations.append(list(argv))
            self.assertEqual(options["stdin"], subprocess.DEVNULL)
            if argv == ["claude", "--version"]:
                os.write(options["stdout"], (self.measured_build + " (Claude Code)\n").encode())
                return subprocess.CompletedProcess(argv, 0)
            self.assertEqual(argv[-3:-1], ["--model", "fixture-selector"])
            self.assertNotIn("ANTHROPIC_API_KEY", options["env"])
            Path(options["env"]["HOME"], "session-marker").write_bytes(self.keep_marker)
            answer = original(argv, **options)
            if self.reported is not None:
                os.write(options["stdout"], fake.terminal(*self.reported))
            return answer
        return run

    def turn(self, control, role, attempt_id, roots, **operands):
        import provider_policy.home as home
        delivered = self.provider_delivery_for(role, attempt_id)
        mounted = str(provider_home.location(self.config["provider_home_root"], delivered["home_identity"]) / "home")
        actual_check, actual_prepare = home.checked_home, home.prepare
        def translate(path):
            self.assertEqual(path, policy.HOME)
            return mounted
        # Only mount translation is simulated. Real no-follow home checks,
        # credential preparation and the manager's real typed mount still run.
        with mock.patch.object(home, "checked_home", side_effect=lambda path: actual_check(translate(path))), \
             mock.patch.object(home, "prepare", side_effect=lambda path, **kw: actual_prepare(translate(path), **kw)), \
             mock.patch.dict(os.environ, {"BATON_ATTEMPT_LOG_ROOM": os.path.join(self.config["launch_home"], launch.LOG_DIRECTORY, attempt_id)}):
            return super().turn(control, role, attempt_id, roots, **operands)

    def started(self):
        job, control, composed = self.serving()
        submit(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        attempt = self.only_attempt(composed, "implementation")
        return job, control, composed, attempt

    def test_13_positive_implementation_binds_frozen_result_and_checkpoint(self):
        held = self.implemented()
        account = model_attribution.assessment_of(held.control, held.attempt_id)
        self.assertEqual(account["outcome"], "matched")
        self.assertEqual(account["attribution"]["contributors"], self.reported[::-1])
        binding = model_attribution._read(held.control, "provider.attribution-ending", held.attempt_id)
        self.assertIsNotNone(binding["checkpoint_id"])
        self.assertEqual(binding["manifest_digest"], account["manifest_digest"])
        selected = model_attribution.selection_of(held.control, held.attempt_id)
        home = provider_home.location(self.config["provider_home_root"], selected["delivery"]["home_identity"]) / "home"
        self.assertEqual((home / "session-marker").read_bytes(), self.keep_marker)
        self.assertEqual(len(self.invocations), 2)

    def test_14_17_missing_output_holds_without_publication_or_retry(self):
        self.reported = None
        job, control, composed, attempt = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"}), 0)
        for _ in range(4):
            sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assessment_of(control, attempt)
        self.assertEqual(account["cause"], "model-attribution-missing")
        self.assertNotEqual(self.states(job, composed)["implementation"], "completed")
        self.assertNotEqual(self.states(job, composed)["review"], "waiting")
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertEqual(len(self.invocations), 2)

    def reviewed(self, verdict="accepted"):
        held = self.implemented()
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt(held.composed, "review")
        self.assertEqual(self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt),
            edits={"review-report.json": json.dumps({"schema": "baton.review-report/1", "verdict": verdict, "findings": "simulated reviewer"})}), 0)
        held.review = attempt
        return held

    def test_13_review_binds_its_own_evidence_to_verdict(self):
        held = self.reviewed()
        self.drive(held.job, held.composed, "review", "completed")
        binding = model_attribution._read(held.control, "provider.attribution-ending", held.review)
        self.assertIsNotNone(binding["verdict_id"])
        self.assertNotEqual(binding["attempt_id"], held.attempt_id)
        self.assertEqual(model_attribution.assessment_of(held.control, held.review)["outcome"], "matched")
        producer_home = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]["home_identity"]
        reviewer_home = model_attribution.selection_of(held.control, held.review)["delivery"]["home_identity"]
        self.assertNotEqual(provider_home.location(self.config["provider_home_root"], producer_home),
                            provider_home.location(self.config["provider_home_root"], reviewer_home))

    def test_14_conflicting_build_holds_before_checkpoint(self):
        self.measured_build = "2.1.999"
        job, control, composed, attempt = self.started()
        self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        for _ in range(4):
            sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(model_attribution.assessment_of(control, attempt)["cause"], "model-attribution-conflicting")
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertEqual(len(self.invocations), 2)

    def test_32_38_correction_reuses_home_after_positive_runtime_cessation(self):
        from baton_v12.worker_manager import attempts
        held = self.reviewed("changes-requested")
        first = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
        home = provider_home.location(self.config["provider_home_root"], first["home_identity"]) / "home"
        marker = (home / "session-marker").read_bytes()
        # The runtime reader supplies unknown on these ticks; no forced owner
        # action or failed-preparation terminal is permitted in response.
        with mock.patch.object(attempts, "provider_home_cessation_of", return_value=None):
            for _ in range(12):
                sweep(held.job, held.composed, now=fixtures.NOW)
            self.assertEqual(self.states(held.job, held.composed)["implementation"], "claimed")
            self.assertEqual(json.loads((home.parent / "record.json").read_text())["holder"], held.attempt_id)
        self.drive(held.job, held.composed, "implementation", "waiting", ticks=12)
        worker = self.worker_of(held.composed, "implementation")
        second = next(one for one in worker.stage._prepared if one != held.attempt_id)
        self.assertEqual(json.loads((home.parent / "record.json").read_text())["holder"], second)
        self.assertEqual((home / "session-marker").read_bytes(), marker)
        self.assertEqual(attempts.provider_home_cessation_of(held.control, held.attempt_id)["runtime"], "destroyed")

    def test_16_frozen_evidence_survives_store_reopen_and_detects_log_tampering(self):
        from baton_v12.worker_manager import ControlStore
        held = self.implemented()
        account = model_attribution.assessment_of(held.control, held.attempt_id)
        # A fresh reader over the same durable stores computes exactly the
        # same decision; no process, candidate or verdict effect is repeated.
        with ControlStore.open(held.control.database, incarnation="attribution-restart", clock=lambda: fixtures.NOW) as reopened:
            self.assertEqual(model_attribution.assess(reopened, held.attempt_id), account)
            selected = model_attribution.selection_of(reopened, held.attempt_id)
            log = Path(selected["logs_root"], held.attempt_id, "provider.stdout.log")
            log.write_bytes(fake.terminal("other"))
            from baton_v12.contracts import ContractRefusal
            with self.assertRaises(ContractRefusal):
                model_attribution.assess(reopened, held.attempt_id)
        self.assertEqual(len(self.invocations), 2)

    def test_14_review_without_requested_contributor_records_no_verdict(self):
        held = self.implemented()
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt(held.composed, "review")
        self.reported = ["different-model"]
        self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt),
            edits={"review-report.json": json.dumps({"schema": "baton.review-report/1", "verdict": "accepted", "findings": "simulated"})})
        for _ in range(4):
            sweep(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(model_attribution.assessment_of(held.control, attempt)["cause"], "model-attribution-conflicting")
        self.assertIsNone(model_attribution._read(held.control, "provider.attribution-ending", attempt))
        self.assertEqual(self.states(held.job, held.composed)["integration"], "blocked")

    def test_15_foreign_attempt_in_real_frozen_result_is_held(self):
        import claude_agent
        original = claude_agent.ClaudeAgent.work
        def foreign(agent, seen, declared):
            answer = original(agent, seen, declared)
            for output in answer["outputs"]:
                claim = output.get("result_metadata", {}).get("baton.model-attribution/1")
                if claim is not None:
                    claim["attempt_id"] = "another-attempt"
            return answer
        job, control, composed, attempt = self.started()
        with mock.patch.object(claude_agent.ClaudeAgent, "work", foreign):
            self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        for _ in range(4):
            sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(model_attribution.assessment_of(control, attempt)["cause"], "model-attribution-invalid")
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))

    def test_18_35_40_47_home_and_credentials_are_not_output_or_session_resume(self):
        from baton_v12.worker_manager import intake_receipt_of, load_manifest, frozen_output_of
        held = self.implemented()
        selected = model_attribution.selection_of(held.control, held.attempt_id)
        home = provider_home.location(self.config["provider_home_root"], selected["delivery"]["home_identity"]) / "home"
        self.assertTrue((home / ".claude/.credentials.json").is_symlink())
        self.assertEqual(os.readlink(home / ".claude/.credentials.json"), str(Path(self.root, "credential-" + held.attempt_id[:12], "claude")))
        for artifact in intake_receipt_of(held.control, held.attempt_id)["artifacts"]:
            root = Path(artifact["custody_locator"].removeprefix("file://"))
            for path in root.rglob("*"):
                if path.is_file():
                    self.assertNotIn(self.keep_marker, path.read_bytes())
                    self.assertNotIn(b"not-a-credential", path.read_bytes())
        frozen = frozen_output_of(held.control, held.attempt_id)
        self.assertNotIn(str(home), json.dumps(load_manifest(held.control, frozen["manifest_digest"], "resultManifest")))
        diagnostic = model_attribution.diagnostic_of(held.control, held.attempt_id)
        self.assertIn("retained (fresh invocation)", diagnostic)
        self.assertIn("worker: implementation-worker", diagnostic)
        self.assertIn("holder: " + held.attempt_id, diagnostic)
        self.assertNotIn("resumed", diagnostic)
        for argv in self.invocations:
            self.assertNotIn("--resume", argv)
            self.assertNotIn("--session-id", argv)
        from tools import job_observation
        from baton_v12.job_manager import status
        snapshot = status(held.job, held.composed, observed_at=fixtures.NOW)
        stage = next(one for one in snapshot["jobs"][0]["stages"] if one["kind"] == "implementation")
        self.assertEqual(job_observation._stage_line(stage, fixtures.NOW)["model_attribution"], diagnostic, repr(stage))

    def test_20_separation_is_composed_from_selected_providers_and_models(self):
        from tools.stage_execution import provider_separation
        workers = self.composed_document()["workers"]
        self.assertEqual(provider_separation(workers), "same-provider/same-model-fresh-context")
        workers[1]["deployment"]["provider_contract"]["selection"]["requested_model"] = "different"
        self.assertEqual(provider_separation(workers), "same-provider/different-model")
        workers[1]["deployment"]["provider_contract"]["selection"]["provider"] = "simulated-other"
        self.assertEqual(provider_separation(workers), "provider-diverse")

    def test_34_cross_worker_context_and_checkout_overlap_refuse_preflight(self):
        from tools import stage_execution
        from baton_v12.contracts import ContractRefusal
        document = self.composed_document(line_declared_base=self.base)
        home = self.config["provider_home_root"]
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(document, checkout=home)
        document["workers"][1]["deployment"]["credential_home"] = home
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(document, checkout=self.checkout)

    def test_25_simulated_codex_and_claude_share_policy_and_admit_distinct_lanes(self):
        # This table row is a simulation, not Codex flags or qualification.
        synthetic = copy.deepcopy(policy.REALIZATIONS["claude"])
        synthetic["interaction"]["program"] = "simulated-codex"
        synthetic["credentials"] = {"mode": "seeded-retained", "path": "fixture/credential"}
        original = self.worker
        def worker(role, **members):
            value = original(role, **members)
            if role == "review":
                given = value["deployment"]
                selected = dict(given["provider_contract"]["selection"], provider="codex")
                profile = dict(given["provider_contract"]["runtime_profile"], provider="codex")
                adapter = policy.adapter(selected, network=given["network"])
                given.update(provider_contract={"selection": selected, "runtime_profile": profile, "adapter": adapter},
                    profile_digest=digest(profile), profile_name="simulated-codex-profile", adapter_digest=digest(adapter))
                self.submission["jobs"][0]["stages"][1]["profile_name"] = "simulated-codex-profile"
                manifest = copy.deepcopy(given["input_manifest"])
                manifest["runtime_profile_digest"] = digest(profile)
                manifest.pop("manifest_digest"); manifest["manifest_digest"] = digest(manifest)
                given["input_manifest"] = manifest
                self.submission["jobs"][0]["stages"][1]["profile_digest"] = digest(profile)
            return value
        with mock.patch.dict(policy.REALIZATIONS, {"codex": synthetic}), mock.patch.object(self, "worker", side_effect=worker):
            job, control, composed = self.serving()
            submit(job, self.submission)
            producer, reviewer = (self.worker_of(composed, role).given for role in ("implementation", "review"))
            self.assertEqual(producer["input_manifest"]["tool_policy_digest"], reviewer["input_manifest"]["tool_policy_digest"])
            self.assertNotEqual(producer["adapter_digest"], reviewer["adapter_digest"])
            self.assertEqual(self.states(job, composed)["implementation"], "queued")
            self.assertEqual(self.states(job, composed)["review"], "blocked")
            self.assertEqual(reviewer["provider_contract"]["adapter"]["participation_sources"], [])

    def test_41_42_43_seeded_provider_refresh_survives_correction_without_export(self):
        import provider_policy as worker_policy
        sentinel = b"SIMULATED-PRIVATE-CREDENTIAL-NOT-A-SECRET"
        realization = copy.deepcopy(policy.REALIZATIONS["claude"])
        realization["credentials"]["mode"] = "seeded-retained"
        seen_credentials = []
        original_provider = self.provider
        def factory(**operands):
            runner = original_provider(**operands)
            def run(argv, **options):
                if argv[0] == "claude" and "--version" not in argv:
                    credential = Path(options["env"]["HOME"], ".claude/.credentials.json")
                    seen_credentials.append((credential, credential.read_bytes()))
                    credential.write_bytes(sentinel)
                return runner(argv, **options)
            return run
        with mock.patch.dict(policy.REALIZATIONS, {"claude": realization}), \
             mock.patch.dict(worker_policy.REALIZATIONS, {"claude": realization}), \
             mock.patch.object(self, "provider", side_effect=factory):
            adapter = policy.adapter(self.config["provider_contract"]["selection"], network=self.config["network"])
            self.config["provider_contract"]["adapter"] = adapter
            self.config["adapter_digest"] = digest(adapter)
            held = self.reviewed("changes-requested")
            self.drive(held.job, held.composed, "implementation", "waiting", ticks=12)
            second = next(one for one in self.worker_of(held.composed, "implementation").stage._prepared if one != held.attempt_id)
            self.turn(held.control, "implementation", second, self.mounted(held.composed, "implementation", second), edits={"harness.py": "print('second')\n"})
            self.drive(held.job, held.composed, "implementation", "completed")
            self.assertEqual(seen_credentials[0][1], b"not-a-credential\n")
            self.assertEqual(seen_credentials[-1][0], seen_credentials[0][0])
            self.assertEqual(seen_credentials[-1][1], sentinel)
            self.assertEqual(seen_credentials[0][0].stat().st_mode & 0o777, 0o600)
            for path in Path(self.root).rglob("*"):
                if not path.is_file() or path.is_symlink():
                    continue
                if path in {one[0] for one in seen_credentials}:
                    continue
                self.assertNotIn(sentinel, path.read_bytes(), str(path))
            self.assertEqual(len([one for one in self.invocations if "--version" not in one]), 3)

    def test_32_restart_after_review_reuses_retained_home(self):
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution
        held = self.reviewed("changes-requested")
        # Conclude the review without starting a second producer in that sweep.
        sweep(held.job, held.composed, now=fixtures.NOW)
        first = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
        home = provider_home.location(self.config["provider_home_root"], first["home_identity"]) / "home"
        before = (home / "session-marker").read_bytes()
        held.composed.close()
        held.job.close(); held.control.close()
        job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation="home-restart", clock=lambda: fixtures.NOW)
        control = ControlStore.open(self.control_path, incarnation="home-restart", clock=lambda: fixtures.NOW)
        self.addCleanup(job.close); self.addCleanup(control.close)
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
            engine_run=self.engine, credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close); self._composed = composed
        self.drive(job, composed, "implementation", "waiting", ticks=12)
        worker = self.worker_of(composed, "implementation")
        second = next(one for one in worker.stage._prepared if one != held.attempt_id)
        self.assertEqual(json.loads((home.parent / "record.json").read_text())["holder"], second)
        self.assertEqual((home / "session-marker").read_bytes(), before)
        selected = model_attribution.selection_of(control, second)
        self.assertEqual(selected["delivery"]["home_identity"], first["home_identity"])

    def test_26_actual_argv_or_environment_drift_refuses_before_provider(self):
        import claude_agent
        job, control, composed, attempt = self.started()
        roots = self.mounted(composed, "implementation", attempt)
        with mock.patch.object(claude_agent.ClaudeAgent, "provider_arguments", ("--invented-drift",)):
            self.assertNotEqual(self.turn(control, "implementation", attempt, roots), 0)
        self.assertEqual(self.invocations, [])

    def test_27_28_changed_tool_policy_refuses_before_any_runtime(self):
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution
        document = self.composed_document(line_declared_base=self.base)
        manifest = document["workers"][1]["deployment"]["input_manifest"]
        manifest["tool_policy_digest"] = "sha256:" + "f" * 64
        manifest.pop("manifest_digest"); manifest["manifest_digest"] = digest(manifest)
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(document, checkout=self.checkout)

    def test_44_simulated_authentication_failure_has_no_key_or_fallback(self):
        import claude_agent
        old = self.provider
        def factory(**operands):
            runner = old(**dict(operands, status=1))
            def run(argv, **options):
                self.assertFalse(any("API_KEY" in key for key in options.get("env", {})))
                answer = runner(argv, **options)
                return answer
            return run
        job, control, composed, attempt = self.started()
        self.reported = None
        with mock.patch.object(self, "provider", side_effect=factory):
            self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt))
        self.assertEqual(len(self.invocations), 2)  # build probe and one provider; no retry
        # Existing provider-terminal owns the typed authentication/API failure.
        terminal = claude_agent.ClaudeAgent().provider_terminal(1,
            b'{"type":"result","subtype":"error_during_execution","is_error":true,"errors":["authentication failed"]}', partial=False)
        self.assertFalse(terminal["ok"])
        self.assertIsNotNone(terminal["failure_reason"])

    def test_26_environment_drift_refuses_before_build_probe(self):
        import claude_agent
        original = claude_agent.ClaudeAgent._revalidated_environment
        def changed(agent, scratch, environment):
            return dict(original(agent, scratch, environment), ANTHROPIC_API_KEY="synthetic-disallowed")
        job, control, composed, attempt = self.started()
        with mock.patch.object(claude_agent.ClaudeAgent, "_revalidated_environment", changed):
            self.assertNotEqual(self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt)), 0)
        self.assertEqual(self.invocations, [])

    def test_17_legacy_result_without_attribution_is_held_under_new_selection(self):
        import claude_agent
        original = claude_agent.ClaudeAgent.work
        def pre_change(agent, seen, declared):
            answer = original(agent, seen, declared)
            for output in answer["outputs"]:
                output.get("result_metadata", {}).pop("baton.model-attribution/1", None)
            return answer
        job, control, composed, attempt = self.started()
        with mock.patch.object(claude_agent.ClaudeAgent, "work", pre_change):
            self.assertEqual(self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"}), 0)
        for _ in range(4):
            sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(model_attribution.assessment_of(control, attempt)["cause"], "model-attribution-missing")
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertNotEqual(self.states(job, composed)["review"], "waiting")
        self.assertEqual(len(self.invocations), 2)

    def test_16_restart_between_result_and_ending_uses_original_evidence(self):
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution
        job, control, composed, attempt = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"}), 0)
        self.assertIsNone(model_attribution.assessment_of(control, attempt))
        selected = model_attribution.selection_of(control, attempt)
        composed.close(); job.close(); control.close()
        job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation="before-ending", clock=lambda: fixtures.NOW)
        control = ControlStore.open(self.control_path, incarnation="before-ending", clock=lambda: fixtures.NOW)
        self.addCleanup(job.close); self.addCleanup(control.close)
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
            engine_run=self.engine, credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close); self._composed = composed
        self.drive(job, composed, "implementation", "completed")
        self.assertEqual(model_attribution.selection_of(control, attempt), selected)
        self.assertEqual(model_attribution.assessment_of(control, attempt)["outcome"], "matched")
        self.assertIsNotNone(model_attribution._read(control, "provider.attribution-ending", attempt)["checkpoint_id"])
        self.assertEqual(len(self.invocations), 2)

    def test_30_legacy_and_selected_lanes_refuse_one_job_before_effects(self):
        from baton_v12.worker_manager import provider_context as context
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution
        document = self.composed_document(line_declared_base=self.base)
        legacy = document["workers"][1]["deployment"]
        legacy["schema"] = single_worker.LAYOUT_CONFIG_SCHEMA
        legacy.pop("provider_contract"); legacy.pop("provider_home_root")
        manifest = legacy["input_manifest"]
        manifest["tool_policy_digest"] = digest({"schema": "baton.worker-tool-policy/1",
            "argv_policy": dict(context.ARGV_POLICY), "environment_policy": dict(context.ENVIRONMENT_POLICY)})
        manifest.pop("manifest_digest"); manifest["manifest_digest"] = digest(manifest)
        job, control, composed = self.serving(workers=document["workers"])
        worker = self.worker_of(composed, "review")
        stage = dict(kind="review", work_id=legacy["input_manifest"]["work_ref"]["work_id"],
            profile_name=legacy["profile_name"], profile_digest=legacy["profile_digest"])
        perform = mock.Mock()
        with self.assertRaisesRegex(ContractRefusal, "input"):
            worker.admit(perform, stage, self.submission["jobs"][0])
        perform.assert_not_called()
        self.assertEqual(self.invocations, [])

    def test_31_override_home_location_refuses_before_runtime(self):
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution
        document = self.composed_document(line_declared_base=self.base)
        document["workers"][0]["deployment"]["provider_home_root"] = os.path.join(self.root, "override-home")
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(document, checkout=self.checkout)
        self.assertEqual(self.invocations, [])

    def test_46_managed_credential_collision_refuses_composition(self):
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution
        document = self.composed_document(line_declared_base=self.base)
        deployment = document["workers"][0]["deployment"]
        adapter = deployment["provider_contract"]["adapter"]
        adapter["managed_entries"] = [{"path": adapter["credential"]["path"], "content": "simulated"}]
        deployment["adapter_digest"] = digest(adapter)
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(document, checkout=self.checkout)
        self.assertEqual(self.invocations, [])

    def test_45_same_seed_reference_allows_two_workers_and_two_jobs(self):
        realization = copy.deepcopy(policy.REALIZATIONS["claude"])
        realization["credentials"]["mode"] = "seeded-retained"
        with mock.patch.dict(policy.REALIZATIONS, {"claude": realization}):
            adapter = policy.adapter(self.config["provider_contract"]["selection"], network=self.config["network"])
            self.config["provider_contract"]["adapter"] = adapter
            self.config["adapter_digest"] = digest(adapter)
            second = copy.deepcopy(self.submission["jobs"][0])
            second["job_id"] = "job-b"
            for stage in second["stages"]:
                for edge in stage["depends_on"]:
                    edge["job_id"] = "job-b"
            self.submission["jobs"].append(second)
            job, control, composed = self.serving()
            producer, reviewer = (self.worker_of(composed, role).given for role in ("implementation", "review"))
            self.assertEqual(producer["credential_profile"], reviewer["credential_profile"])
            self.assertEqual(producer["provider_contract"]["adapter"]["credential"]["mode"], "seeded-retained")
            submit(job, self.submission)
            from baton_v12.job_manager import status
            snapshot = status(job, composed, observed_at=fixtures.NOW)
            self.assertEqual({one["job_id"] for one in snapshot["jobs"]}, {"job-a", "job-b"})
            self.assertEqual(self.invocations, [])

    def test_R1_prestart_failure_releases_home_to_successor_and_fences_old_start(self):
        from baton_v12.worker_manager import attempts
        from baton_v12.job_manager import submission
        from baton_v12.contracts import ContractRefusal
        job, control, composed = self.serving()
        submit(job, self.submission)
        with mock.patch.object(launch, "materialize", side_effect=ContractRefusal("refused", "precondition", "simulated pre-start delivery failure")):
            for _ in range(12):
                sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(self.states(job, composed)["implementation"], "exceptional")
        worker = self.worker_of(composed, "implementation")
        record_path, = Path(self.config["provider_home_root"]).glob("*/*/record.json")
        record = json.loads(record_path.read_text()); previous = record["holder"]
        self.assertEqual(attempts.provider_home_cessation_of(control, previous)["ended_before_start"], True)
        self.assertEqual(self.invocations, [])
        engine = mock.Mock()
        with self.assertRaisesRegex(ContractRefusal, "preparation already ended"):
            attempts.request_runtime_start(control, engine, attempt_id=previous)
        engine.start.assert_not_called()
        # Explicit successor at the runtime owner boundary, not an automatic
        # Job retry policy. The normal home acquisition and typed mount run.
        successor = "simulated-successor-after-prestart-failure"
        attempts.record_attempt(control, attempt_id=successor, adapter_name="docker",
            adapter_digest=self.config["adapter_digest"], profile_digest=self.config["profile_digest"])
        stage = dict(next(one for one in submission.stage_rows(job) if one["kind"] == "implementation"), attempt_id=successor)
        worker._hold_provider_home(stage)
        selected = model_attribution.selection_of(control, successor)["delivery"]
        mount = provider_home.HomeMount(self.config["provider_home_root"], **selected["home_identity"], attempt_id=successor)
        self.assertEqual(mount.boundary()[0], str(record_path.parent / "home"))
        self.assertEqual(json.loads(record_path.read_text())["holder"], successor)
        self.assertEqual(self.invocations, [])

    def test_R1a_failed_home_creation_releases_preparing_holder_to_successor(self):
        from baton_v12.worker_manager import attempts
        from baton_v12.job_manager import submission
        job, control, composed = self.serving()
        submit(job, self.submission)
        root = os.path.realpath(self.config["provider_home_root"])
        original = os.mkdir
        hits = []
        def full(path, *args, **kwargs):
            if path == "home" and kwargs.get("dir_fd") is not None and os.readlink("/proc/self/fd/" + str(kwargs["dir_fd"])).startswith(root + os.sep):
                hits.append(path)
                raise OSError(28, "simulated disk full during final home creation")
            return original(path, *args, **kwargs)
        with mock.patch.object(os, "mkdir", side_effect=full):
            for _ in range(12):
                sweep(job, composed, now=fixtures.NOW)
        self.assertTrue(hits)
        self.assertEqual(self.states(job, composed)["implementation"], "exceptional")
        record_path, = Path(root).glob("*/*/record.json")
        record = json.loads(record_path.read_text())
        previous = record["holder"]
        self.assertEqual(record["state"], "preparing")
        self.assertFalse((record_path.parent / "home").exists())
        evidence = attempts.provider_home_cessation_of(control, previous)
        self.assertTrue(evidence["ended_before_start"])
        self.assertTrue(provider_home.ceased(evidence, previous))
        # An explicitly supplied successor, not an automatic Job retry.
        successor = "simulated-successor-after-home-creation-failure"
        attempts.record_attempt(control, attempt_id=successor, adapter_name="docker",
            adapter_digest=self.config["adapter_digest"], profile_digest=self.config["profile_digest"])
        stage = dict(next(one for one in submission.stage_rows(job) if one["kind"] == "implementation"), attempt_id=successor)
        worker = self.worker_of(composed, "implementation")
        worker._hold_provider_home(stage)
        selected = model_attribution.selection_of(control, successor)["delivery"]
        mount = provider_home.HomeMount(root, **selected["home_identity"], attempt_id=successor)
        self.assertEqual(mount.boundary()[0], str(record_path.parent / "home"))
        updated = json.loads(record_path.read_text())
        self.assertEqual(updated, dict(record, holder=successor, state="ready"))
        worker._hold_provider_home(stage)
        self.assertEqual(json.loads(record_path.read_text()), updated)
        self.assertEqual(self.invocations, [])

    def test_R1_requested_start_without_cessation_keeps_home_pending(self):
        from baton_v12.worker_manager import attempts, oci
        job, control, composed = self.serving()
        submit(job, self.submission)
        # Interrupt the actual adapter call AFTER the durable start intent.
        with mock.patch.object(oci.OciAdapter, "start", side_effect=KeyboardInterrupt("simulated lost start caller")):
            with self.assertRaises(KeyboardInterrupt):
                for _ in range(12):
                    sweep(job, composed, now=fixtures.NOW)
        record_path, = Path(self.config["provider_home_root"]).glob("*/*/record.json")
        record = json.loads(record_path.read_text()); previous = record["holder"]
        evidence = attempts.provider_home_cessation_of(control, previous)
        self.assertEqual(evidence["runtime"], "start-requested")
        self.assertFalse(provider_home.ceased(evidence, previous))
        with self.assertRaises(provider_home.HomePending):
            provider_home.acquire(self.config["provider_home_root"], **record["identity"], attempt_id="simulated-successor",
                previous_runtime=lambda holder: attempts.provider_home_cessation_of(control, holder))
        self.assertEqual(json.loads(record_path.read_text()), record)
        self.assertEqual(self.invocations, [])

    def test_R3_held_cause_and_owner_action_survive_passes_and_restart(self):
        from baton_v12.job_manager import status, JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution, job_observation
        self.reported = None
        job, control, composed, attempt = self.started()
        self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        def check():
            for _ in range(5):
                sweep(job, composed, now=fixtures.NOW)
            snapshot = status(job, composed, observed_at=fixtures.NOW)
            stage = next(one for one in snapshot["jobs"][0]["stages"] if one["kind"] == "implementation")
            self.assertEqual(stage["runtime"]["model_attribution_hold"], "model-attribution-missing")
            self.assertEqual(job_observation.stage_view(stage, fixtures.NOW)["reason"], "held: model-attribution-missing; owner action needed")
            self.assertEqual(len(self.invocations), 2)
            self.assertNotEqual(self.states(job, composed)["review"], "waiting")
        check()
        composed.close(); job.close(); control.close()
        job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation="held-restart", clock=lambda: fixtures.NOW)
        control = ControlStore.open(self.control_path, incarnation="held-restart", clock=lambda: fixtures.NOW)
        self.addCleanup(job.close); self.addCleanup(control.close)
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
            engine_run=self.engine, credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close); self._composed = composed
        check()
