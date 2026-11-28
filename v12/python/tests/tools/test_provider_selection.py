"""Simulated engine/provider; real admission, worker, freeze and ending owners."""
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest import mock

from baton_v12 import provider_policy as policy
from baton_v12.contracts import digest
from baton_v12.contracts.manifest import job_input_identity
from baton_v12.job_manager import submit, sweep
from baton_v12.worker_manager import launch, model_attribution, provider_home
from tests.job_manager import fixtures
from tests.manager import provider_fixtures as fake
from tests.tools import test_native_handoffs as handoffs
from tests.tools import test_stage_execution as existing
from tools import single_worker


class SelectedBase(existing.ComposedOneJobCase):
    """Selected-provider composition and helpers; no test of its own."""
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
        self.environments = []
        self.instructions_at_start = []
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
            # W385853: what the provider child was actually given, recorded
            # before the simulated provider writes anything of its own.
            self.environments.append(dict(options["env"]))
            placed = Path(options["env"]["HOME"], ".claude/CLAUDE.md")
            self.instructions_at_start.append(placed.read_bytes() if placed.is_file() else None)
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

    def turns(self):
        return [argv for argv in self.invocations if argv != ["claude", "--version"]]

    def built_prompts(self):
        """Record what the unchanged prompt builders return."""
        import claude_agent
        built = []
        patches = []
        for name in ("_prompt", "_handoff_prompt", "_review_prompt", "_response_prompt"):
            actual = getattr(claude_agent, name)
            def recording(*args, _actual=actual, _name=name, **kwargs):
                value = _actual(*args, **kwargs)
                built.append((_name, value))
                return value
            patches.append(mock.patch.object(claude_agent, name, side_effect=recording))
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        return built

    def assert_labelled(self, argv, role, built, builder=None):
        adapter = self.config["provider_contract"]["adapter"]
        label = policy.context_label(adapter, role).decode()
        prompt = argv[-1]
        self.assertTrue(prompt.startswith(label + "\n"), prompt[:200])
        original = prompt[len(label) + 1:]
        self.assertIn(original, [value for _name, value in built])
        if builder is not None:
            # The named builder really ran and produced exactly this suffix.
            self.assertIn((builder, original), built)
        self.assertNotIn("Baton execution context", original)
        self.assertEqual(argv, policy.argv(adapter, self.config["provider_contract"]["selection"], prompt))
        other = "review" if role == "implementation" else "implementation"
        self.assertNotIn("Assigned role: " + other, prompt)
        return label

    def fixed_slot(self, home):
        """SIMULATED: a container has one fixed credential slot path; this
        harness gives each attempt its own directory. Later turns are handed
        the first attempt's slot path so the retained reference is the same
        reference, as it is in a container. Nothing else changes."""
        import provider_policy.home as worker_home
        actual_prepare = worker_home.prepare
        slot = os.readlink(home / ".claude/.credentials.json")
        return mock.patch.object(worker_home, "prepare", side_effect=lambda path, **kw: actual_prepare(path, **dict(kw, delivered=slot)))

    def assert_recorded(self, control, attempt, role):
        account = model_attribution.assessment_of(control, attempt)
        selected = model_attribution.selection_of(control, attempt)
        self.assertEqual(selected["phase"], role)
        self.assertEqual((account["outcome"], account["cause"]), ("matched", None))
        self.assertEqual(account["context_label"], policy.context_record(selected["delivery"]["contract"]["adapter"], role))
        self.assertIn("label reported: yes", model_attribution.diagnostic_of(control, attempt))
        return account


class SelectedCase(SelectedBase):
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

    # -- W385853 instruction delivery. The provider is simulated: these prove
    # what Baton composed, placed, passed and bound, not that a vendor CLI
    # loaded a file or that a model understood the label.

    def test_d2_d3_implementation_turn_carries_role_label_and_exact_worker_instructions(self):
        built = self.built_prompts()
        held = self.implemented()
        (argv,) = self.turns()
        label = self.assert_labelled(argv, "implementation", built)
        canonical = (Path(__file__).resolve().parents[4] / "docs/V12-WORKER-INSTRUCTIONS.md").read_bytes()
        entry = self.config["provider_contract"]["adapter"]["managed_entries"][0]
        self.assertEqual(self.instructions_at_start, [canonical])
        self.assertEqual(entry["sha256"], "sha256:" + __import__("hashlib").sha256(canonical).hexdigest())
        self.assertIn(entry["sha256"].removeprefix("sha256:"), label)
        self.assertIn(policy.HOME + "/.claude/CLAUDE.md", label)
        for required in ("You are running as a Baton native v12 worker.", "Assigned role: implementation.",
                         "Does not apply to you:", "It grants no permission"):
            self.assertIn(required, label)
        # Bound by record, not by printing protocol identity to the model.
        selected = model_attribution.selection_of(held.control, held.attempt_id)
        for private in (held.attempt_id, selected["delivery"]["home_identity"]["job_id"],
                        selected["delivery"]["home_identity"]["worker_id"], "/output", "resum"):
            self.assertNotIn(private, label)
        account = model_attribution.assessment_of(held.control, held.attempt_id)
        self.assertEqual(account["outcome"], "matched")
        self.assertEqual(account["context_label"], policy.context_record(selected["delivery"]["contract"]["adapter"], "implementation"))
        self.assertEqual(account["context_label"]["context_label_digest"], "sha256:" + __import__("hashlib").sha256(label.encode()).hexdigest())
        diagnostic = model_attribution.diagnostic_of(held.control, held.attempt_id)
        for shown in ("Native worker role: implementation", account["context_label"]["context_label_digest"],
                      "worker instructions: " + entry["sha256"], "label reported: yes"):
            self.assertIn(shown, diagnostic)
        # Host-only instruction content reaches no composed channel. The NAME
        # AGENTS.md does appear, in the label, to say it does not apply.
        host = (Path(__file__).resolve().parents[4] / "AGENTS.md").read_text().splitlines()
        host_lines = [line for line in host if len(line) > 40]
        composed = "\n".join([*argv, *(value for env in self.environments for value in env.values())])
        for line in host_lines:
            self.assertNotIn(line, composed)
        self.assertNotIn(host_lines[0].encode(), canonical)

    def test_d2_d3_review_turn_carries_its_own_role_label_in_its_own_home(self):
        built = self.built_prompts()
        held = self.reviewed()
        producer, reviewer = self.turns()
        self.assert_labelled(producer, "implementation", built)
        self.assert_labelled(reviewer, "review", built)
        self.assertEqual(self.instructions_at_start[0], self.instructions_at_start[1])
        self.assertIsNotNone(self.instructions_at_start[1])
        self.assertNotEqual(self.environments[0]["HOME"], self.environments[1]["HOME"])
        self.drive(held.job, held.composed, "review", "completed")
        account = model_attribution.assessment_of(held.control, held.review)
        self.assertEqual(account["context_label"]["role"], "review")
        self.assertNotEqual(account["context_label"]["context_label_digest"],
                            model_attribution.assessment_of(held.control, held.attempt_id)["context_label"]["context_label_digest"])

    def test_d4_correction_replaces_entry_keeps_provider_state_and_is_a_fresh_invocation(self):
        built = self.built_prompts()
        held = self.reviewed("changes-requested")
        first = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
        home = provider_home.location(self.config["provider_home_root"], first["home_identity"]) / "home"
        self.drive(held.job, held.composed, "implementation", "waiting", ticks=12)
        worker = self.worker_of(held.composed, "implementation")
        second = next(one for one in worker.stage._prepared if one != held.attempt_id)
        # A provider or model altered the managed file and left its own state.
        (home / ".claude/CLAUDE.md").write_bytes(b"simulated provider rewrite")
        (home / ".claude/provider-own").write_bytes(b"simulated provider state")
        with self.fixed_slot(home):
            self.assertEqual(self.turn(held.control, "implementation", second, self.mounted(held.composed, "implementation", second),
                                       edits={"harness.py": "print('corrected')\n"}), 0)
        correction = self.turns()[-1]
        self.assert_labelled(correction, "implementation", built)
        self.assertEqual(self.instructions_at_start[-1], self.instructions_at_start[0])
        self.assertEqual((home / ".claude/provider-own").read_bytes(), b"simulated provider state")
        self.assertEqual((home / "session-marker").read_bytes(), self.keep_marker)
        for argv in self.invocations:
            self.assertNotIn("--resume", argv)
            self.assertNotIn("--session-id", argv)
        self.assertNotIn("resumed", model_attribution.diagnostic_of(held.control, second))

    def test_d4_delivery_is_in_no_candidate_frozen_output_or_custody(self):
        from baton_v12.worker_manager import intake_receipt_of, load_manifest, frozen_output_of
        held = self.implemented()
        canonical = (Path(__file__).resolve().parents[4] / "docs/V12-WORKER-INSTRUCTIONS.md").read_bytes()
        seen = 0
        for artifact in intake_receipt_of(held.control, held.attempt_id)["artifacts"]:
            for path in Path(artifact["custody_locator"].removeprefix("file://")).rglob("*"):
                if path.is_file():
                    seen += 1
                    self.assertNotIn(b"Baton execution context", path.read_bytes())
                    self.assertNotIn(canonical[:200], path.read_bytes())
                    self.assertNotEqual(path.name, "CLAUDE.md")
        self.assertGreater(seen, 0)
        frozen = load_manifest(held.control, frozen_output_of(held.control, held.attempt_id)["manifest_digest"], "resultManifest")
        self.assertNotIn("Baton execution context", json.dumps(frozen))
        selected = model_attribution.selection_of(held.control, held.attempt_id)
        home = provider_home.location(self.config["provider_home_root"], selected["delivery"]["home_identity"]) / "home"
        self.assertEqual(sorted(str(one.relative_to(home)) for one in home.rglob("*") if not one.is_dir()),
                         [".claude/.credentials.json", ".claude/CLAUDE.md", "session-marker"])

    def refused_turn(self):
        job, control, composed, attempt = self.started()
        try:
            status = self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt),
                               edits={"harness.py": "print('changed')\n"})
        except Exception as failure:  # a refusal before the worker loop is still a refusal
            status = failure
        self.assertEqual(status, 1)
        self.assertEqual(self.invocations, [])
        self.assertEqual(self.instructions_at_start, [])
        return job, control, composed, attempt

    def test_d5_changed_template_refuses_before_any_provider(self):
        import provider_policy as worker_policy
        with mock.patch.object(worker_policy, "LABEL_TEMPLATE", worker_policy.LABEL_TEMPLATE + "one more line\n"):
            self.refused_turn()

    def test_d5_absent_packaged_instructions_refuse_before_any_provider(self):
        import provider_policy as worker_policy
        with mock.patch.object(worker_policy, "INSTRUCTIONS_FILE", "absent.md"):
            self.refused_turn()

    def test_d5_changed_packaged_instructions_refuse_before_any_provider(self):
        import provider_policy as worker_policy
        with mock.patch.object(worker_policy, "worker_instructions", return_value=b"changed bytes"):
            self.refused_turn()

    def test_d5_role_outside_the_label_vocabulary_refuses_before_any_provider(self):
        import provider_policy as worker_policy
        actual = worker_policy.context_label
        def narrowed(document, role):
            # The adapter still equals this build's; only the role is not served.
            return actual(dict(document, context_label=dict(document["context_label"])), "integration" if role == "implementation" else role)
        with mock.patch.object(worker_policy, "context_label", side_effect=narrowed):
            self.refused_turn()

    def held_label(self, alter, cause):
        import claude_agent
        original = claude_agent.ClaudeAgent.work
        def reported(agent, seen, declared):
            answer = original(agent, seen, declared)
            for output in answer["outputs"]:
                alter(output.get("result_metadata", {}))
            return answer
        job, control, composed, attempt = self.started()
        with mock.patch.object(claude_agent.ClaudeAgent, "work", reported):
            self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        for _ in range(6):
            sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assessment_of(control, attempt)
        self.assertEqual((account["outcome"], account["cause"], account["context_label"]), ("held", cause, None))
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertNotEqual(self.states(job, composed)["implementation"], "completed")
        self.assertNotEqual(self.states(job, composed)["review"], "waiting")
        self.assertEqual(len(self.turns()), 1)
        from baton_v12.worker_manager import ControlStore
        with ControlStore.open(control.database, incarnation="label-restart", clock=lambda: fixtures.NOW) as reopened:
            self.assertEqual(model_attribution.assess(reopened, attempt), account)
        from tools import job_observation
        from baton_v12.job_manager import status
        stage = next(one for one in status(job, composed, observed_at=fixtures.NOW)["jobs"][0]["stages"] if one["kind"] == "implementation")
        self.assertEqual(job_observation._reason(stage, stage.get("state")), "held: " + cause + "; owner action needed")
        self.assertIn("label reported: no", model_attribution.diagnostic_of(control, attempt))

    def test_d5_result_without_label_record_is_held_as_missing(self):
        self.held_label(lambda metadata: metadata.pop(policy.LABEL_SCHEMA, None), "context-label-missing")

    def test_d5_result_with_another_label_digest_is_held_as_mismatch(self):
        def alter(metadata):
            if policy.LABEL_SCHEMA in metadata:
                metadata[policy.LABEL_SCHEMA]["context_label_digest"] = policy.context_record(
                    self.config["provider_contract"]["adapter"], "review")["context_label_digest"]
        self.held_label(alter, "context-label-mismatch")

    def test_25_simulated_codex_and_claude_share_policy_and_admit_distinct_lanes(self):
        # This table row is a simulation, not Codex flags or qualification.
        synthetic = copy.deepcopy(policy.REALIZATIONS["claude"])
        synthetic["interaction"]["program"] = "simulated-codex"
        synthetic["credentials"] = {"mode": "seeded-retained", "path": "fixture/credential"}
        original = self.worker
        def worker(role, **members):
            value = original(role, **members)
            if role == "implementation":
                given = value["deployment"]
                selected = dict(given["provider_contract"]["selection"], provider="codex")
                profile = dict(given["provider_contract"]["runtime_profile"], provider="codex")
                adapter = policy.adapter(selected, network=given["network"])
                given.update(provider_contract={"selection": selected, "runtime_profile": profile, "adapter": adapter},
                    credential_slots=["codex"], credential_profile={"codex": given["credential_profile"]["api"]},
                    profile_digest=digest(profile), profile_name="simulated-codex-profile", adapter_digest=digest(adapter))
                self.submission["jobs"][0]["stages"][0]["profile_name"] = "simulated-codex-profile"
                manifest = copy.deepcopy(given["input_manifest"])
                manifest["runtime_profile_digest"] = digest(profile)
                manifest.pop("manifest_digest"); manifest["manifest_digest"] = digest(manifest)
                given["input_manifest"] = manifest
                self.submission["jobs"][0]["stages"][0]["profile_digest"] = digest(profile)
            return value
        # W385853: a realization is composable only with its instruction
        # delivery tables; the simulated row declares simulated ones.
        with mock.patch.dict(policy.REALIZATIONS, {"codex": synthetic}), mock.patch.dict(policy.MANAGED, {"codex": {"path": "fixture/instructions.md", "kind": policy.INSTRUCTIONS_KIND}}), \
                mock.patch.object(self, "worker", side_effect=worker):
            job, control, composed = self.serving()
            submit(job, self.submission)
            producer, reviewer = (self.worker_of(composed, role).given for role in ("implementation", "review"))
            self.assertEqual(producer["input_manifest"]["tool_policy_digest"], reviewer["input_manifest"]["tool_policy_digest"])
            self.assertNotEqual(producer["adapter_digest"], reviewer["adapter_digest"])
            self.assertEqual(self.states(job, composed)["implementation"], "queued")
            self.assertEqual(self.states(job, composed)["review"], "blocked")
            self.assertEqual(producer["provider_contract"]["adapter"]["participation_sources"], [])

    def test_41_42_43_seeded_provider_refresh_survives_correction_without_export(self):
        import provider_policy as worker_policy
        sentinel = b"SIMULATED-PRIVATE-CREDENTIAL-NOT-A-SECRET"
        realization = copy.deepcopy(policy.REALIZATIONS["claude"])
        realization["credentials"]["mode"] = "seeded-retained"
        self.config["credential_slots"] = ["claude"]
        self.config["credential_profile"] = {"claude": self.config["credential_profile"]["api"]}
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
            self.assertEqual(seen_credentials[0][1], self.secret.encode())
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

    def test_seeded_restart_reopens_manager_without_original_source(self):
        self.seeded_restart()

    def test_seeded_missing_credential_refuses_before_source_or_new_runtime(self):
        self.seeded_restart(missing=True)

    def seeded_restart(self, *, missing=False):
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution
        import provider_policy as worker_policy
        realization = copy.deepcopy(policy.REALIZATIONS["claude"])
        realization["credentials"]["mode"] = "seeded-retained"
        self.config["credential_slots"] = ["claude"]
        self.config["credential_profile"] = {"claude": self.config["credential_profile"]["api"]}
        with mock.patch.dict(policy.REALIZATIONS, {"claude": realization}), mock.patch.dict(worker_policy.REALIZATIONS, {"claude": realization}):
            adapter = policy.adapter(self.config["provider_contract"]["selection"], network=self.config["network"])
            self.config["provider_contract"]["adapter"] = adapter
            self.config["adapter_digest"] = digest(adapter)
            held = self.reviewed("changes-requested")
            sweep(held.job, held.composed, now=fixtures.NOW)
            selected = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
            home = provider_home.location(self.config["provider_home_root"], selected["home_identity"]) / "home"
            credential = home / ".claude/.credentials.json"
            credential.write_bytes(b"simulated refreshed credential")
            held.composed.close(); held.job.close(); held.control.close()
            job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation="seed-restart", clock=lambda: fixtures.NOW)
            control = ControlStore.open(self.control_path, incarnation="seed-restart", clock=lambda: fixtures.NOW)
            self.addCleanup(job.close); self.addCleanup(control.close)
            from tools.user_credentials import UserCredentialSources
            from baton_v12.worker_manager.credentials import MAX_BEARER
            source = mock.Mock(wraps=UserCredentialSources(str(Path(self.root) / "absent-synthetic-registry.json"), max_bearer=MAX_BEARER))
            composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
                engine_run=self.engine, credential_provider=source, clock=lambda: fixtures.NOW, checkout=self.checkout)
            self.addCleanup(composed.close); self._composed = composed
            if missing:
                credential.unlink()
                before = len(self.invocations)
                self.drive(job, composed, "implementation", "exceptional", ticks=12)
                source.assert_not_called()
                self.assertEqual(len(self.invocations), before)
                self.assertFalse(credential.exists())
                from baton_v12.worker_manager.attempts import attempt_preparation_failure_of
                # The failure is retained by the actual attempt owner.
                holder = json.loads((home.parent / "record.json").read_text())["holder"]
                failure = attempt_preparation_failure_of(control, holder)
                self.assertIn("credential recovery required", str(failure))
                return
            self.drive(job, composed, "implementation", "waiting", ticks=12)
            second = next(one for one in self.worker_of(composed, "implementation").stage._prepared if one != held.attempt_id)
            self.assertEqual(credential.read_bytes(), b"simulated refreshed credential")
            self.assertEqual(self.turn(control, "implementation", second, self.mounted(composed, "implementation", second), edits={"harness.py": "print('after restart')\n"}), 0)
            self.drive(job, composed, "implementation", "completed")
            source.assert_not_called()
            self.assertEqual(credential.read_bytes(), b"simulated refreshed credential")

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

    def test_d3_d4_restart_then_next_provider_turn_replaces_entry_and_binds_label(self):
        # Review M386040 R2: the restart proof continues THROUGH the next
        # provider turn and its ending, over freshly opened stores.
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution
        built = self.built_prompts()
        held = self.reviewed("changes-requested")
        sweep(held.job, held.composed, now=fixtures.NOW)
        first = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
        home = provider_home.location(self.config["provider_home_root"], first["home_identity"]) / "home"
        held.composed.close()
        held.job.close(); held.control.close()
        job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation="label-restart", clock=lambda: fixtures.NOW)
        control = ControlStore.open(self.control_path, incarnation="label-restart", clock=lambda: fixtures.NOW)
        self.addCleanup(job.close); self.addCleanup(control.close)
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
            engine_run=self.engine, credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close); self._composed = composed
        self.drive(job, composed, "implementation", "waiting", ticks=12)
        second = next(one for one in self.worker_of(composed, "implementation").stage._prepared if one != held.attempt_id)
        self.assertEqual(model_attribution.selection_of(control, second)["delivery"]["home_identity"], first["home_identity"])
        (home / ".claude/CLAUDE.md").write_bytes(b"simulated provider rewrite before restart")
        (home / ".claude/provider-own").write_bytes(b"simulated provider state")
        before = len(self.turns())
        with self.fixed_slot(home):
            self.assertEqual(self.turn(control, "implementation", second, self.mounted(composed, "implementation", second),
                                       edits={"harness.py": "print('after restart')\n"}), 0)
        self.assertEqual(len(self.turns()), before + 1)
        self.assert_labelled(self.turns()[-1], "implementation", built, builder="_prompt")
        canonical = (Path(__file__).resolve().parents[4] / "docs/V12-WORKER-INSTRUCTIONS.md").read_bytes()
        self.assertEqual(self.instructions_at_start[-1], canonical)
        self.assertEqual((home / ".claude/CLAUDE.md").read_bytes(), canonical)
        self.assertEqual((home / ".claude/provider-own").read_bytes(), b"simulated provider state")
        self.assertEqual((home / "session-marker").read_bytes(), self.keep_marker)
        self.assertEqual(self.environments[-1]["HOME"], self.environments[0]["HOME"])
        for _ in range(6):
            sweep(job, composed, now=fixtures.NOW)
        self.assert_recorded(control, second, "implementation")
        self.assertIsNotNone(model_attribution._read(control, "provider.attribution-ending", second)["checkpoint_id"])
        for argv in self.invocations:
            self.assertNotIn("--resume", argv)
            self.assertNotIn("--session-id", argv)

    def caller_prompt_turn(self, role):
        """One `invoke_provider` call as the proved launch, optionally with
        another launch role, and nothing after it: an invocation prepares its
        private child roots exactly once, so this probe ends the turn there."""
        import claude_agent
        room = os.path.realpath(os.path.join(self.root, "caller-room"))
        os.makedirs(room)
        seen_by = {}
        def calling(agent, seen, declared):
            seen_by["launch_role"] = seen["role"]
            try:
                seen_by["answer"] = agent.invoke_provider(prompt="caller prompt, verbatim", room=room,
                                                          seen=seen if role is None else dict(seen, role=role))
            except claude_agent.TaskRefusal as refusal:
                seen_by["refusal"] = refusal
            raise claude_agent.TaskRefusal("the caller-prompt probe ends this turn")
        job, control, composed, attempt = self.started()
        with mock.patch.object(claude_agent.ClaudeAgent, "work", calling):
            self.assertEqual(self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt)), 1)
        self.assertEqual(seen_by["launch_role"], "implementation")
        return seen_by

    def test_d3_caller_prompt_turn_carries_the_label_of_the_proved_launch_role(self):
        # Review M386040 R2, the `invoke_provider` row: under a selected
        # provider policy a caller-supplied prompt is labelled with the role
        # of the launch the caller proved, and is otherwise passed verbatim.
        seen_by = self.caller_prompt_turn(None)
        self.assertTrue(seen_by["answer"]["ok"], seen_by)
        adapter = self.config["provider_contract"]["adapter"]
        (caller,) = self.turns()
        self.assertEqual(caller[-1], policy.context_label(adapter, "implementation").decode() + "\n" + "caller prompt, verbatim")
        self.assertEqual(caller, policy.argv(adapter, self.config["provider_contract"]["selection"], caller[-1]))
        # NOT ASSERTED, AND REPORTED: `invoke_provider` prepares the child
        # home before it binds the caller's launch, so this entry point does
        # not place the managed entry. No production caller launches under a
        # labelled role (see the refusal proof below), so that is unreachable
        # today; this test proves the label and argv of the row only.

    def test_d3_caller_prompt_turn_refuses_the_integration_role_before_any_provider(self):
        # The one production caller of `invoke_provider` is the integration
        # workload, and `integration` is not a role the label vocabulary
        # serves. Such a turn under a selected provider policy refuses before
        # any provider process. This proves that refusal; it is NOT coverage
        # of an integration delivery, which this slice does not provide.
        import claude_agent
        seen_by = self.caller_prompt_turn("integration")
        self.assertNotIn("answer", seen_by)
        self.assertEqual(str(seen_by["refusal"]), "the execution-context label cannot be delivered")
        self.assertIsInstance(seen_by["refusal"].__cause__, __import__("provider_policy").PolicyRefusal)
        self.assertEqual(self.invocations, [])
        self.assertEqual(self.instructions_at_start, [])
        worker = Path(claude_agent.__file__).parent
        callers = sorted(path.name for path in worker.glob("*.py") if "invoke_provider(" in path.read_text() and path.name != "claude_agent.py")
        # The Codex override delegates only after its R1 operand guard;
        # it adds no integration-role support and has no native realization.
        self.assertEqual(callers, ["codex_agent.py", "integration_workload.py"])
        self.assertEqual(self.config["provider_contract"]["adapter"]["context_label"]["roles"], ["implementation", "review"])

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
        self.config["credential_slots"] = ["claude"]
        self.config["credential_profile"] = {"claude": self.config["credential_profile"]["api"]}
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


class SelectedHandoffCase(SelectedBase, handoffs.HandoffJobCase):
    """Review M386040 R2: the native handoff rows under a selected provider
    policy. Real composed owners and worker; the provider is the same
    simulated seam. `HandoffJobCase` supplies the `/3` template Job and the
    bootstrap-composed routing; `SelectedBase` supplies the selection."""
    started = handoffs.HandoffJobCase.started

    def test_d3_continuation_and_response_turns_carry_role_label_entry_and_record(self):
        built = self.built_prompts()
        canonical = (Path(__file__).resolve().parents[4] / "docs/V12-WORKER-INSTRUCTIONS.md").read_bytes()
        held = self.yielded()                      # implementation stops at a clarification
        self.assertEqual(len(self.turns()), 1)
        self.assert_labelled(self.turns()[0], "implementation", built, builder="_handoff_prompt")
        home = provider_home.location(self.config["provider_home_root"],
            model_attribution.selection_of(held.control, held.attempt_id)["delivery"]["home_identity"]) / "home"
        held = self.answered(held)                 # the reviewer's clarification response
        self.assertEqual(len(self.turns()), 2)
        self.assert_labelled(self.turns()[1], "review", built, builder="_response_prompt")
        held = self.resumed(held)                  # the continuation attempt on the retained checkpoint
        (home / ".claude/CLAUDE.md").write_bytes(b"simulated provider rewrite")
        (home / ".claude/provider-own").write_bytes(b"simulated provider state")
        with self.fixed_slot(home):
            self.assertEqual(self.turn(held.control, "implementation", held.resumed, held.resumed_roots,
                                       edits={"harness.py": "print('the finished harness')\n"}), 0)
        self.assertEqual(len(self.turns()), 3)
        continuation = self.turns()[2]
        self.assert_labelled(continuation, "implementation", built, builder="_handoff_prompt")
        self.assertIn(handoffs.ANSWER["body"], continuation[-1])
        # Every turn started with the exact entry in place; the continuation
        # reused the first attempt's home and kept provider-owned state.
        self.assertEqual(self.instructions_at_start, [canonical] * 3)
        self.assertEqual(self.environments[2]["HOME"], self.environments[0]["HOME"])
        self.assertNotEqual(self.environments[1]["HOME"], self.environments[0]["HOME"])
        self.assertEqual((home / ".claude/provider-own").read_bytes(), b"simulated provider state")
        for _ in range(8):
            sweep(held.job, held.composed, now=fixtures.NOW)
        self.assert_recorded(held.control, held.attempt_id, "implementation")
        self.assert_recorded(held.control, held.review, "review")
        self.assert_recorded(held.control, held.resumed, "implementation")
        labels = {attempt: model_attribution.assessment_of(held.control, attempt)["context_label"]["context_label_digest"]
                  for attempt in (held.attempt_id, held.review, held.resumed)}
        self.assertEqual(labels[held.attempt_id], labels[held.resumed])
        self.assertNotEqual(labels[held.attempt_id], labels[held.review])
        for argv in self.invocations:
            self.assertNotIn("--resume", argv)
            self.assertNotIn("--session-id", argv)


class QualificationCredentialPreparation(unittest.TestCase):
    """Synthetic credentials only; no engine, model, or real user registry."""
    def setUp(self):
        import tempfile
        from tests.manager.disk_roots import disk_backed_root
        self.temp = tempfile.TemporaryDirectory(dir=disk_backed_root())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "run"
        self.run.mkdir(mode=0o700)
        self.source = self.root / "synthetic-source"
        self.source.write_bytes(b"synthetic qualification seed")
        self.source.chmod(0o600)
        self.config = self.root / "synthetic-source.json"
        self.config.write_text(json.dumps({"reference": "synthetic", "path": str(self.source)}))
        self.config.chmod(0o600)
        self.selection = dict(execution_root=str(self.run), uid=os.getuid(), gid=os.getgid(),
            authorization_credential_copy="synthetic-only", credential_source_reference="synthetic",
            credential_path_evidence="synthetic", credential_storage_mode_evidence="synthetic",
            private_retention_and_cleanup_owner="synthetic", refresh_copy_disposition="retain synthetic",
            codex_home_relative_to_home="synthetic-codex", credential_relative_path="synthetic-auth",
            instruction_relative_to_home="synthetic-codex/instructions.md")

    def prepare(self, **changes):
        from tools.qualification_credentials import prepare_selected
        return prepare_selected(dict(self.selection, **changes), str(self.config))

    def test_automated_copy_and_restart_without_config_or_source(self):
        self.assertEqual(self.prepare()["credential_lifecycle"], "ready")
        credential = self.run / "live/home/synthetic-codex/synthetic-auth"
        self.assertEqual(credential.read_bytes(), b"synthetic qualification seed")
        self.assertEqual(credential.stat().st_mode & 0o777, 0o600)
        self.assertNotEqual(credential.stat().st_ino, self.source.stat().st_ino)
        credential.write_bytes(b"synthetic refreshed qualification seed")
        self.source.unlink(); self.config.unlink()
        self.assertEqual(self.prepare()["credential_lifecycle"], "ready")
        self.assertEqual(credential.read_bytes(), b"synthetic refreshed qualification seed")

    def test_missing_credential_or_lifecycle_never_reseeds(self):
        from baton_v12.provider_policy import PolicyRefusal
        self.prepare()
        credential = self.run / "live/home/synthetic-codex/synthetic-auth"
        credential.unlink()
        with self.assertRaisesRegex(PolicyRefusal, "credential recovery required"):
            self.prepare()
        self.assertFalse(credential.exists())
        (self.run / "live/credential-state/credential.json").unlink()
        with self.assertRaisesRegex(provider_home.HomeRefusal, "credential recovery required"):
            self.prepare()
        self.assertFalse(credential.exists())

    def test_unselected_copy_refuses_before_source_access_or_writes(self):
        self.config.unlink(); self.source.unlink()
        with self.assertRaisesRegex(ValueError, "selection is incomplete"):
            self.prepare(authorization_credential_copy=None)
        self.assertEqual(list(self.run.iterdir()), [])

    def test_source_reference_mismatch_is_recovery_without_copy(self):
        with self.assertRaisesRegex(ValueError, "source reference disagrees"):
            self.prepare(credential_source_reference="other")
        self.assertFalse((self.run / "live/home/synthetic-codex/synthetic-auth").exists())
        with self.assertRaisesRegex(provider_home.HomeRefusal, "credential recovery required"):
            self.prepare()

    def test_subscription_byte_bounds_and_exact_copy(self):
        from baton_v12.provider_policy.home import MAX_SUBSCRIPTION_BYTES
        for size in (0, MAX_SUBSCRIPTION_BYTES - 1, MAX_SUBSCRIPTION_BYTES, MAX_SUBSCRIPTION_BYTES + 1):
            with self.subTest(size=size):
                run = self.root / ("bound-" + str(size)); run.mkdir(mode=0o700)
                raw = b"\xc3\xa9" * (size // 2) + (b"\xff" if size % 2 else b"")
                self.source.write_bytes(raw)
                if not 0 < size <= MAX_SUBSCRIPTION_BYTES:
                    with self.assertRaises(ValueError) as raised: self.prepare(execution_root=str(run))
                    self.assertNotIn("é", str(raised.exception))
                else:
                    self.prepare(execution_root=str(run))
                    target = run / "live/home/synthetic-codex/synthetic-auth"
                    self.assertEqual(target.read_bytes(), raw)
                    target.write_bytes(b"x" * (MAX_SUBSCRIPTION_BYTES+1))
                    from baton_v12.provider_policy import PolicyRefusal
                    with self.assertRaises(PolicyRefusal): self.prepare(execution_root=str(run))


class CodexToClaude(SelectedBase):
    """Synthetic providers at normal invocation boundary; real pipeline owners."""
    def setUp(self):
        super().setUp()
        import provider_policy as worker_policy
        from tests.manager import codex_fixtures
        self.codex_selected = dict(codex_fixtures.SELECTED)
        adapter = policy.adapter(self.codex_selected, network=self.config["network"])
        profile = dict(self.config["provider_contract"]["runtime_profile"], provider="codex", cli_build="0.169.0")
        self.codex_contract = dict(selection=self.codex_selected, adapter=adapter, runtime_profile=profile)
        self.codex_profile = digest(profile)
        self.submission["jobs"][0]["stages"][0]["profile_name"] = "synthetic-codex"
        self.submission["jobs"][0]["stages"][0]["profile_digest"] = self.codex_profile

    def serving(self, **members):
        from tools import stage_execution
        original = stage_execution.operations_from
        secret = self.secret
        class SyntheticSources:
            def __call__(self, *args): return secret
            def resolve_file(self, *args): return b"SYNTHETIC SUBSCRIPTION FILE\n"
        def compose(*args, **kwargs):
            kwargs["credential_provider"] = SyntheticSources()
            return original(*args, **kwargs)
        with mock.patch.object(stage_execution, "operations_from", side_effect=compose):
            answer = super().serving(**members)
        self.image_test_control = answer[1]
        return answer

    def quiescing(self):
        engine = super().quiescing()
        original = type(engine).__call__
        def observed(engine, argv, **options):
            if hasattr(self, "image_test_control"):
                self.assertFalse(self.image_test_control._connection.in_transaction)
            answer = original(engine, argv, **options)
            if argv[1:4] == ["inspect", "--type", "container"] and answer["status"] == 0:
                document = json.loads(answer["stdout"])
                document["Image"] = engine.image
                document["Config"] = {"Labels": engine.labels}
                document["State"]["StartedAt"] = "2026-11-25T00:00:00Z"
                if getattr(self, "omit_image_evidence", False):
                    document.pop("Image")
                answer = dict(answer, stdout=json.dumps(document))
            return answer
        self.enterContext(mock.patch.object(type(engine), "__call__", observed))
        return engine

    def worker(self, role, **members):
        value = super().worker(role, **members)
        if role == "implementation":
            deployment = value["deployment"]
            deployment.update(provider_contract=copy.deepcopy(self.codex_contract),
                profile_digest=self.codex_profile, adapter_digest=digest(self.codex_contract["adapter"]),
                profile_name="synthetic-codex", credential_slots=["codex"], credential_profile={"codex": deployment["credential_profile"]["api"]})
            manifest = deployment["input_manifest"]
            manifest["runtime_profile_digest"] = self.codex_profile
            manifest.pop("manifest_digest"); manifest["manifest_digest"] = digest(manifest)
        return value

    def provider(self, **operands):
        original = super().provider(**operands)
        def run(argv, **options):
            if argv[0] != "codex": return original(argv, **options)
            if argv == ["codex", "--version"]:
                os.write(options["stdout"], b"codex-cli 0.169.0\n")
            else:
                self.invocations.append(list(argv))
                self.assertEqual(options["env"]["CODEX_HOME"], options["env"]["HOME"] + "/codex")
                self.assertEqual(Path(options["env"]["HOME"], "instructions/WORKER.md").read_bytes(), policy.worker_instructions())
                self.assertEqual(Path(options["env"]["CODEX_HOME"], "auth.json").read_bytes(), b"SYNTHETIC SUBSCRIPTION FILE\n")
                for name, body in (operands.get("edits") or {}).items():
                    self.write(os.path.join(options["cwd"], name), body)
                raw = (Path(__file__).parents[1]/"manager/fixtures/codex-0.169.0/turn-success.sanitized.jsonl").read_bytes()
                os.write(options["stdout"], raw)
            return subprocess.CompletedProcess(argv, 0)
        return run

    def turn(self, control, role, attempt_id, roots, **operands):
        if role != "implementation": return super().turn(control, role, attempt_id, roots, **operands)
        import claude_agent, codex_agent
        credentials = Path(self.root, "credential-" + attempt_id[:12]); credentials.mkdir(exist_ok=True)
        (credentials/"codex").write_text("SYNTHETIC ONLY\n")
        with mock.patch.object(claude_agent, "ClaudeAgent", codex_agent.CodexAgent):
            return super().turn(control, role, attempt_id, roots, **operands)

    def test_cancellation_of_frozen_authentication_failure(self):
        from baton_v12.job_manager import cancellation, ending, scheduler, status, JobStore
        from baton_v12.worker_manager import frozen_output_of, intake, review_cycles, attempts, tokens, ControlStore
        from tools import stage_execution

        held = SelectedCase.reviewed(self, "changes-requested")
        job, control, composed = held.job, held.control, held.composed
        self.drive(job, composed, "implementation", "waiting", ticks=12)
        attempt, = [a for a in self.worker_of(composed, "implementation").stage._prepared if a != held.attempt_id]
        prior = model_attribution._read(control, "provider.attribution-ending", held.review)
        verdict = review_cycles.verdict_of(control, prior["verdict_id"])
        self.assertEqual(verdict["disposition"], "changes-requested")
        uncertain = True
        base_engine = type(self.engine).__call__
        def inspect_engine(engine, argv, **kwargs):
            if argv[1] == "ps" and (argv[-1].startswith("name=") or argv[-1] == "{{.ID}}"):
                return engine.answer(status=1, stderr="fixture inventory unavailable") if uncertain and argv[-1] == "{{.ID}}" else engine.answer(stdout="")
            return base_engine(engine, argv, **kwargs)
        self.enterContext(mock.patch.object(type(self.engine), "__call__", inspect_engine))
        original = self.provider

        def failing_provider(**kwargs):
            run = original(**kwargs)
            def invoke(argv, **opts):
                if argv[:2] == ["codex", "exec"]:
                    os.write(opts["stderr"], b"authentication failed (synthetic)\n")
                    return subprocess.CompletedProcess(argv, 1)
                return run(argv, **opts)
            return invoke

        with mock.patch.object(self, "provider", failing_provider):
            self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt))
        sweep(job, composed, now=fixtures.NOW)
        selected = model_attribution.selection_of(control, attempt)
        diagnostic = Path(selected["logs_root"], attempt, "provider.stderr.log")
        failure = diagnostic.read_bytes()
        self.assertIn(b"authentication failed (synthetic)", failure)
        account = model_attribution.assessment_of(control, attempt)
        self.assertEqual(account["cause"], "model-attribution-faulted")
        frozen = frozen_output_of(control, attempt)
        self.assertEqual(frozen["disposition"], "unable")
        receipt = intake.intake_receipt_of(control, attempt)
        job_id = self.submission["jobs"][0]["job_id"]
        def cancel_status():
            return cancellation.report(job, job_id, now=fixtures.NOW,
                observed_of=lambda entry: cancellation.observed_from(control, entry["attempt"]["attempt_id"]))

        cancellation.request(job, job_id=job_id, reason="retire failed correction")
        alloc = scheduler.allocation_of(job, attempt)
        row = attempts._require_attempt(control, attempt)
        domain = tokens.domain_of("workspace", tokens.workspace_identity(row))
        gen = tokens.generation_of(control, domain, execution=attempt, operation=attempts._start_operation_id(row))
        writer = self.worker_of(composed, "implementation").stage._prepared[attempt]["writer_id"]
        def restart():
            nonlocal job, control, composed
            composed.close()
            job.close()
            control.close()
            job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation="retire-restart", clock=lambda: fixtures.NOW)
            control = ControlStore.open(self.control_path, incarnation="retire-restart", clock=lambda: fixtures.NOW)
            self.addCleanup(job.close)
            self.addCleanup(control.close)
            self.image_test_control = control
            composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
                engine_run=self.engine, credential_provider=lambda *args: self.fail("unexpected new credential request"),
                clock=lambda: fixtures.NOW, checkout=self.checkout)
            self.addCleanup(composed.close)
        restart()
        for _ in range(2):
            report = sweep(job, composed, now=fixtures.NOW)
            self.assertIn("inventory unavailable", str(report["spoken"]))
            self.assertEqual(review_cycles.writer_of(control, writer)["state"], "active")
            self.assertFalse(tokens.token_of(control, domain, gen)["returned"])
            self.assertEqual(scheduler.allocation_of(job, attempt)["allocation_state"], "reserved")
            self.assertEqual(cancel_status()["targets"][0]["state"], "ending-in-progress")
            restart()
        uncertain = False
        from baton_v12.contracts import ContractRefusal
        interrupted = ContractRefusal("unavailable", "transport", "simulated interruption before token return")
        with mock.patch.object(intake, "_released", side_effect=interrupted):
            report = sweep(job, composed, now=fixtures.NOW)
        self.assertIn("simulated interruption", str(report["spoken"]))
        self.assertIsNotNone(intake.cleanup_of(control, attempt_id=attempt, retention_policy_digest=self.config["retention_policy_digest"]))
        self.assertFalse(tokens.token_of(control, domain, gen)["returned"])
        self.assertEqual(scheduler.allocation_of(job, attempt)["allocation_state"], "reserved")
        self.assertIsNone(ending.settlement_of(job, alloc["stage_id"], alloc["episode"]))
        restart()
        for _ in range(2):
            report = sweep(job, composed, now=fixtures.NOW)
        settled = ending.settlement_of(job, alloc["stage_id"], alloc["episode"])
        self.assertIsNotNone(settled, report)
        cleanup = intake.cleanup_of(control, attempt_id=attempt, retention_policy_digest=self.config["retention_policy_digest"])
        self.assertIsNotNone(cleanup)
        self.assertTrue(tokens.token_of(control, domain, gen)["returned"])
        self.assertEqual(scheduler.allocation_of(job, attempt)["allocation_state"], "released")
        returned = control.operation_record(tokens._returned_id(domain, gen))
        self.assertEqual(returned["kind"], tokens.RETURNED_KIND)
        self.assertEqual(sum(v[1:3] == ["rm", "--volumes"] and v[-1] == row["runtime_id"] for v in self.engine.vectors), 1)
        self.assertFalse(any(v[1:3] == ["rm", "--force"] and v[-1] == row["runtime_id"] for v in self.engine.vectors))
        before = list(self.engine.vectors)
        restart()
        cancellation.request(job, job_id=job_id, reason="retire failed correction")
        sweep(job, composed, now=fixtures.NOW)
        self.assertFalse(any(v[1] in ("start", "rm") for v in self.engine.vectors[len(before):]))
        self.assertEqual(ending.settlement_of(job, alloc["stage_id"], alloc["episode"]), settled)
        self.assertEqual(intake.cleanup_of(control, attempt_id=attempt, retention_policy_digest=self.config["retention_policy_digest"]), cleanup)
        self.assertEqual(review_cycles.verdict_of(control, prior["verdict_id"]), verdict)
        self.assertEqual(diagnostic.read_bytes(), failure)
        self.assertEqual(control.operation_record(tokens._returned_id(domain, gen)), returned)
        self.assertEqual(review_cycles.line_of(control, verdict["line_id"])["current_checkpoint_id"], verdict["checkpoint_id"])
        snapshot = status(job, composed, observed_at=fixtures.NOW)["jobs"][0]["cancellation"]
        self.assertEqual(snapshot["shutdown"], "complete", snapshot["targets"])
        self.assertEqual(cancel_status(), snapshot)
        self.assertEqual(model_attribution.assessment_of(control, attempt), account)
        self.assertEqual(intake.intake_receipt_of(control, attempt), receipt)
        self.assertEqual(frozen_output_of(control, attempt), frozen)

    def shared_attribution_text(self, job, composed, attempt):
        import io
        from baton_v12.job_manager import status
        from tools import stack
        from tools.job_observation import job_view

        snapshot = status(job, composed, observed_at=fixtures.NOW)
        view = job_view(snapshot, snapshot["jobs"][0])
        phase, = [one for one in view["phases"] if one["attempt_id"] == attempt]
        stream = io.StringIO()
        stack._print_job_outcomes({"document": snapshot, "state": "fresh", "canonical": True}, stream)
        self.assertIn(phase["model_attribution"], stream.getvalue())
        return phase["model_attribution"]

    def test_refused_image_shows_hold_before_assessment(self):
        from baton_v12.worker_manager import image_receipts
        job, control, composed, attempt = self.started()
        model_attribution._write(control, image_receipts.KIND + "-refused", attempt, {"refused": True})
        self.assertIsNone(model_attribution.assessment_of(control, attempt))
        text = self.shared_attribution_text(job, composed, attempt)
        self.assertTrue(text.startswith("Model attribution held: launched-image-refused."), text)

    def test_missing_image_stays_pending_and_invalid_receipt_shows_hold_before_assessment(self):
        from baton_v12.worker_manager import image_receipts
        self.omit_image_evidence = True
        job, control, composed, attempt = self.started()
        selection = model_attribution.selection_of(control, attempt)
        self.assertEqual(image_receipts.evidence(control, attempt, selection), (None, "launched-image-missing"))
        self.assertTrue(self.shared_attribution_text(job, composed, attempt).startswith("Model attribution pending."))
        model_attribution._write(control, image_receipts.KIND, attempt, {"observation": None})
        self.assertIsNone(model_attribution.assessment_of(control, attempt))
        text = self.shared_attribution_text(job, composed, attempt)
        self.assertTrue(text.startswith("Model attribution held: launched-image-invalid."), text)

    def check_launch_readers(self, receipt_state):
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import frozen_output_of, load_manifest
        job, control, composed, attempt = self.started()
        self.assertIsNone(model_attribution.assessment_of(control, attempt))
        pending = self.shared_attribution_text(job, composed, attempt)
        self.assertTrue(pending.startswith("Model attribution pending."), pending)
        self.assertNotIn("accepted", pending)
        self.assertNotIn("host-validated", pending)
        self.assertEqual(self.turn(control, "implementation", attempt,
            self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"}), 0)
        selected = model_attribution.selection_of(control, attempt)
        room = Path(selected["logs_root"], attempt)
        receipt_path = room / "provider.invocation.log"
        receipt = json.loads(receipt_path.read_bytes())
        self.assertEqual((receipt["schema"], receipt["attempt_id"]), ("baton.codex-launch/1", attempt))
        (room / "provider.stdout.log").unlink()
        if receipt_state == "missing":
            receipt_path.unlink()
        elif receipt_state == "tampered":
            receipt_path.write_text(json.dumps(dict(receipt, attempt_id="foreign")))
        for _ in range(4):
            sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assess(control, attempt)
        evaluated = self.shared_attribution_text(job, composed, attempt)
        self.assertNotIn("Model attribution pending.", evaluated)
        frozen = frozen_output_of(control, attempt)
        manifest = load_manifest(control, frozen["manifest_digest"], "resultManifest")
        claim, = [meta["baton.model-attribution/2"] for output in manifest["outputs"]
                  if "baton.model-attribution/2" in (meta := output.get("result_metadata", {}))]
        self.assertEqual(claim["invocation"], receipt)
        recovery = dict(candidate="fixture-candidate", tree_digest=digest("fixture-tree"),
                        result_digest=frozen["manifest_digest"], claim=claim)
        if receipt_state == "intact":
            self.assertEqual(account["outcome"], "matched")
            self.assertIn("Configured model accepted", evaluated)
            self.assertIn("actual participation unknown", evaluated)
            bound = model_attribution.recovery_evidence(control, attempt, **recovery)
            self.assertEqual(bound["attempt_id"], attempt)
            self.assertEqual(bound["attribution"], account["attribution"])
            self.assertEqual(bound["attribution"]["contributors"], [])
            self.assertEqual(bound["attribution"]["actual_participation"], "unknown")
        else:
            expected = "missing" if receipt_state == "missing" else "invalid"
            self.assertEqual((account["outcome"], account["cause"]), ("held", "model-attribution-" + expected))
            self.assertIn(f"Model attribution held: {account['cause']}.", evaluated)
            self.assertNotIn("Configured model accepted", evaluated)
            with self.assertRaisesRegex(ContractRefusal, "model-attribution-invalid"):
                model_attribution.recovery_evidence(control, attempt, **recovery)

    def test_launch_readers_accept_without_diagnostic_stdout(self):
        self.check_launch_readers("intact")

    def test_launch_readers_hold_absent_attempt_receipt(self):
        self.check_launch_readers("missing")

    def test_launch_readers_hold_foreign_attempt_receipt(self):
        self.check_launch_readers("tampered")

    def image_upgrade_instance(self):
        from tools import instance
        original_worker = self.worker
        def distinct_images(role, **members):
            value = original_worker(role, **members)
            if role == "review":
                deployment = value["deployment"]
                profile = deployment["provider_contract"]["runtime_profile"]
                deployment["image_digest"] = profile["image_digest"] = "sha256:" + "4" * 64
                deployment["profile_name"] = profile["name"] = "initial-fixture-review"
                deployment["profile_digest"] = digest(profile)
                manifest = deployment["input_manifest"]
                manifest.update(runtime_profile_digest=digest(profile), worker_image_digest=profile["image_digest"])
                del manifest["manifest_digest"]
                manifest["manifest_digest"] = digest(manifest)
            return value
        self.enterContext(mock.patch.object(self, "worker", side_effect=distinct_images))
        review = self.worker("review")["deployment"]
        for stage in self.submission["jobs"][0]["stages"]:
            if stage["kind"] == "review":
                stage.update(profile_name=review["profile_name"], profile_digest=review["profile_digest"])
        places = instance.layout(self.root)
        Path(places["stores"]).mkdir(mode=0o700)
        os.rename(self.authority_path, places["authority_store"])
        self.authority_path = self.config["authority_store"] = places["authority_store"]
        self.job_path, self.control_path = places["job_store"], places["control_store"]
        Path(places["distro"]).mkdir()
        Path(places["command"]).write_text("disposable packaged runtime")
        selector = instance.emit(self.root, authority_uuid=self.config["authority_uuid"],
                                 identity={"fixture": True}, runtime=instance.manifest(places["distro"]), now=1)
        instance.publish(places["instance"], selector)
        document = self.composed_document(line_declared_base=self.base)
        instance.publish(places["deployment"], document)
        inputs = {"workers": [dict(one, participant=one["deployment"]["participant"]) for one in document["workers"]],
                  "pool_generation": 1}
        instance.publish(places["install_inputs"], inputs)
        return places, selector, document

    def image_upgrade_engine(self, places, document, provider="claude", version_output=None):
        from tests.tools import test_installed_worker as images
        from tools import worker_image_upgrade
        layouts = images.Fixture()
        layouts.setUp()
        self.addCleanup(layouts.doCleanups)
        (layouts.engine / "images.json").write_text(json.dumps(layouts.images))
        if provider == "claude":
            target, build, role = images.REVIEW, "2.1.248", "review"
            version = build + " (Claude Code)"
        else:
            self.assertEqual(provider, "codex")
            target, build, role = images.IMPL, "0.169.0", "implementation"
            version = "codex-cli " + build
        worker, = [one for one in document["workers"] if one["role"] == role]
        argv = ["upgrade-image", "--instance", places["instance"], "--worker-id", worker["worker_id"],
                "--from-image", worker["deployment"]["image_digest"], "--image", target, "--cli-build", build, "--source", str(images.V12)]
        docker = worker_image_upgrade.installed_worker._docker
        def scripted(program, *args):
            if args[0] == "run":
                self.assertEqual(args[-4:], ("--entrypoint", provider, target, "--version"))
                self.assertIn("--network=none", args)
                return (version if version_output is None else version_output).encode()
            return docker(str(layouts.docker), *args)

        return argv, scripted, target, build

    def assert_upgrade_refused(self, places, argv, engine, *expected):
        import io
        from tools import pool, worker_image_upgrade
        files = [Path(places[key]) for key in ("install_inputs", "deployment")]
        before = [path.read_bytes() for path in files]
        stream = io.StringIO()
        with mock.patch.object(worker_image_upgrade.installed_worker, "_docker", side_effect=engine):
            code = pool.main(argv, stream=stream)
        self.assertEqual(code, 2, stream.getvalue())
        for fragment in expected:
            self.assertIn(fragment, stream.getvalue())
        self.assertEqual([path.read_bytes() for path in files], before)
        self.assertFalse((Path(self.root) / worker_image_upgrade.INTENT).exists())
        self.assertEqual(list(Path(self.root).glob("worker-image-*.json")), [])

    def check_allocated_upgrade(self, recovery):
        from baton_v12.job_manager import episodes, scheduler, submission
        from tools import stage_execution
        places, _, document = self.image_upgrade_instance()
        held = self.implemented()
        stage, = [one for one in submission.stage_rows(held.job) if one["kind"] == "review"]
        live = episodes.live_of(held.job, stage["stage_id"])
        attempt = live["attempt_id"]
        reserved = scheduler.reserve(held.job, episodes.attempting(stage, live))
        state = "reserved"
        if recovery:
            scheduler.require_recovery(held.job, attempt)
            state = "recovery-required"
        held.composed.close()
        argv, scripted, _, _ = self.image_upgrade_engine(places, document)
        engine = mock.Mock(side_effect=scripted)
        self.assert_upgrade_refused(places, argv, engine, reserved["worker_id"], state, stage["stage_id"], attempt)
        engine.assert_not_called()
        self.assertEqual(scheduler.allocation_of(held.job, attempt)["allocation_state"], state)
        if not recovery:
            saved = json.loads(Path(places["deployment"]).read_bytes())
            serving = stage_execution.operations_from(saved, held.job, held.control, engine_run=self.engine,
                credential_provider=lambda *_: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
            self.addCleanup(serving.close)
            self.drive(held.job, serving, "review", "waiting")
            self.assertEqual(self.only_attempt(serving, "review"), attempt)
            self.assertEqual(scheduler.allocation_of(held.job, attempt), reserved)
            worker, = [one for one in document["workers"] if one["worker_id"] == reserved["worker_id"]]
            self.assertEqual(self.engine.image, worker["deployment"]["image_digest"])

    def test_reserved_before_offer_refuses_upgrade_and_original_attempt_launches(self):
        self.check_allocated_upgrade(recovery=False)

    def test_recovery_required_allocation_refuses_upgrade(self):
        self.check_allocated_upgrade(recovery=True)

    def test_wrong_cli_version_refuses_before_publication_for_each_provider(self):
        import io
        from tools import pool, worker_image_upgrade
        places, _, document = self.image_upgrade_instance()
        self.implemented().composed.close()
        for provider, wrong in (("claude", "2.1.247 (Claude Code)"), ("codex", "codex-cli 0.168.0")):
            with self.subTest(provider=provider):
                argv, engine, _, build = self.image_upgrade_engine(places, document, provider, wrong)
                self.assert_upgrade_refused(places, argv, engine, f"{provider} in the selected image did not report CLI build {build}")
        # A blanket refusal of the Codex output format must also fail this regression.
        argv, engine, _, _ = self.image_upgrade_engine(places, document, "codex")
        stream = io.StringIO()
        with mock.patch.object(worker_image_upgrade.installed_worker, "_docker", side_effect=engine):
            self.assertEqual(pool.main(argv, stream=stream), 0, stream.getvalue())

    def interrupted_image_upgrade(self, places, selector, document, argv, scripted):
        import io
        from tools import instance, pool, stack, worker_image_upgrade
        publish = instance.publish
        def interrupt(path, data):
            if Path(path) == Path(places["deployment"]):
                raise OSError("cut between install inputs and active configuration")
            return publish(path, data)
        stream = io.StringIO()
        with mock.patch.object(worker_image_upgrade.installed_worker, "_docker", side_effect=scripted):
            with mock.patch.object(instance, "publish", side_effect=interrupt):
                self.assertEqual(pool.main(argv, stream=stream), 2, stream.getvalue())
                self.assertIn("cut between", stream.getvalue())
            self.assertEqual(json.loads(Path(places["deployment"]).read_bytes()), document)
            self.assertTrue((Path(self.root) / worker_image_upgrade.INTENT).exists())
            with self.assertRaisesRegex(stack.StackRefusal, "pending pool upgrade-image"):
                stack.start(Path(selector["state"]), instance.settings(selector), stream=stream)
            conflict = list(argv)
            conflict[conflict.index("--cli-build") + 1] = "2.1.249"
            self.assertEqual(pool.main(conflict, stream=stream), 2)
            self.assertIn("another image upgrade is pending", stream.getvalue())
            unlink = Path.unlink
            def cut_after_receipt(path, *args, **kwargs):
                if path.name == worker_image_upgrade.INTENT:
                    raise OSError("cut after receipt")
                return unlink(path, *args, **kwargs)
            with mock.patch.object(Path, "unlink", cut_after_receipt):
                self.assertEqual(pool.main(argv, stream=stream), 2)
                self.assertIn("cut after receipt", stream.getvalue())
            receipt_path, = Path(self.root).glob("worker-image-[0-9a-f]*.json")
            committed = receipt_path.read_bytes()
            self.assertEqual(pool.main(argv, stream=stream), 0, stream.getvalue())
            self.assertEqual(pool.main(argv, stream=stream), 0, stream.getvalue())
            self.assertEqual(receipt_path.read_bytes(), committed)
        self.assertEqual(len(list(Path(self.root).glob("worker-image-*.json"))), 1)
        self.assertFalse((Path(self.root) / worker_image_upgrade.INTENT).exists())
        updated = json.loads(Path(places["deployment"]).read_bytes())
        self.assertEqual(updated["workers"][0], document["workers"][0])
        self.assertEqual(updated["pool_generation"], 2)
        self.assertEqual(updated["workers"][1]["deployment"]["input_manifest"],
                         json.loads(Path(places["install_inputs"]).read_bytes())["workers"][1]["deployment"]["input_manifest"])
        return updated

    def test_stopped_image_upgrade_replays_and_launches_only_the_new_claude_image(self):
        from baton_v12.job_manager import scheduler
        from tools import stage_execution

        places, selector, document = self.image_upgrade_instance()
        held = self.implemented()
        prior = self.assert_recorded(held.control, held.attempt_id, "implementation")
        prior_image_receipt = prior["launched_image"]
        old_allocation = scheduler.allocation_of(held.job, held.attempt_id)
        old_image = self.engine.image
        self.assertNotEqual(old_image, document["workers"][1]["deployment"]["image_digest"])
        held.composed.close()

        argv, scripted, target, build = self.image_upgrade_engine(places, document)
        updated = self.interrupted_image_upgrade(places, selector, document, argv, scripted)
        serving = stage_execution.operations_from(updated, held.job, held.control, engine_run=self.engine,
            credential_provider=lambda *_: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(serving.close)
        self._composed = serving
        self.drive(held.job, serving, "review", "waiting")
        attempt = self.only_attempt(serving, "review")
        self.assertEqual(self.engine.image, target)
        delivered = self.provider_delivery_for("review", attempt)
        self.assertEqual(delivered["contract"]["selection"]["cli_build"], build)
        # The fixture's binary version belongs to the actually launched image.
        self.measured_build = {target: build, old_image: "2.1.247"}[self.engine.image]
        self.assertEqual(self.turn(held.control, "review", attempt, self.mounted(serving, "review", attempt),
            edits={"review-report.json": json.dumps({"schema":"baton.review-report/1", "verdict":"accepted", "findings":"simulated"})}), 0)
        self.assertIn(["claude", "--version"], self.invocations)
        for _ in range(5):
            sweep(held.job, serving, now=fixtures.NOW)
        reviewer = model_attribution.assessment_of(held.control, attempt)
        self.assertEqual(reviewer["attribution"]["selected_cli_build"], build)
        self.assertEqual(reviewer["attribution"]["evidenced_cli_build"], build)
        self.assertEqual(reviewer["outcome"], "held")  # synthetic new CLI has no qualified contribution source
        old_delivery = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
        self.assertEqual(old_delivery["contract"]["runtime_profile"]["image_digest"], old_image)
        self.assertEqual(model_attribution.assessment_of(held.control, held.attempt_id)["launched_image"], prior_image_receipt)
        self.assertEqual(scheduler.allocation_of(held.job, held.attempt_id), old_allocation)
        self.assertEqual(model_attribution.assessment_of(held.control, held.attempt_id), prior)
        self.assertEqual(prior["attribution"]["invocation"]["evidenced_cli_build"], "0.169.0")

    def test_previous_claude_attempt_keeps_its_original_profile_image_and_cli_evidence(self):
        import io
        from baton_v12.job_manager import scheduler, status
        from tools import pool, stage_execution, worker_image_upgrade

        places, _selector, document = self.image_upgrade_instance()
        held = self.implemented()
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt(held.composed, "review")
        self.assertEqual(self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt),
            edits={"review-report.json": json.dumps({"schema": "baton.review-report/1", "verdict": "accepted",
                                                     "findings": "simulated"})}), 0)
        self.drive(held.job, held.composed, "review", "completed")
        prior = self.assert_recorded(held.control, attempt, "review")
        selected = model_attribution.selection_of(held.control, attempt)
        allocation = scheduler.allocation_of(held.job, attempt)
        self.assertEqual(prior["attribution"]["evidenced_cli_build"], "2.1.247")
        self.assertEqual(selected["delivery"]["contract"]["runtime_profile"]["image_digest"], self.engine.image)
        held.composed.close()
        argv, scripted, target, _build = self.image_upgrade_engine(places, document)
        stream = io.StringIO()
        with mock.patch.object(worker_image_upgrade.installed_worker, "_docker", side_effect=scripted):
            self.assertEqual(pool.main(argv, stream=stream), 0, stream.getvalue())
        updated = json.loads(Path(places["deployment"]).read_bytes())
        serving = stage_execution.operations_from(updated, held.job, held.control, engine_run=self.engine,
            credential_provider=lambda *_: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(serving.close)
        phases = status(held.job, serving, observed_at=fixtures.NOW)["jobs"][0]["stages"]
        review, = [one for one in phases if one["kind"] == "review"]
        self.assertEqual(review["profile_digest"], allocation["worker_profile_digest"])
        self.assertEqual(model_attribution.assessment_of(held.control, attempt), prior)
        self.assertEqual(model_attribution.selection_of(held.control, attempt), selected)
        self.assertNotEqual(selected["delivery"]["contract"]["runtime_profile"]["image_digest"], target)
        self.assertEqual(scheduler.allocation_of(held.job, attempt), allocation)

    def test_configured_implementation_and_stronger_Claude_review(self):
        held = self.implemented()
        producer = self.assert_recorded(held.control, held.attempt_id, "implementation")
        self.assertEqual(producer["attribution"]["basis"], "configured-model")
        self.assertEqual(producer["attribution"]["contributors"], [])
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt(held.composed, "review")
        self.assertEqual(self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt),
            edits={"review-report.json": json.dumps({"schema":"baton.review-report/1", "verdict":"accepted", "findings":"simulated"})}), 0)
        self.drive(held.job, held.composed, "review", "completed")
        reviewer = self.assert_recorded(held.control, attempt, "review")
        self.assertEqual(reviewer["attribution"]["contributors"], sorted(self.reported))
        self.assertEqual(model_attribution.assessment_of(held.control, held.attempt_id), producer)
        self.assertIsNotNone(model_attribution._read(held.control, "provider.attribution-ending", attempt)["verdict_id"])

    def test_configured_implementation_cannot_rescue_missing_Claude_contributor(self):
        held = self.implemented()
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt(held.composed, "review")
        self.reported = ["other-model"]
        self.turn(held.control, "review", attempt, self.mounted(held.composed, "review", attempt),
            edits={"review-report.json": json.dumps({"schema":"baton.review-report/1", "verdict":"accepted", "findings":"simulated"})})
        for _ in range(4): sweep(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(model_attribution.assessment_of(held.control, attempt)["cause"], "model-attribution-conflicting")
        self.assertIsNone(model_attribution._read(held.control, "provider.attribution-ending", attempt))


    def test_missing_image_holds_frozen_codex_without_holding_cessation(self):
        from baton_v12.worker_manager import attempts
        self.omit_image_evidence = True
        job, control, composed, attempt = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt,
            self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"}), 0)
        for _ in range(4): sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assessment_of(control, attempt)
        self.assertEqual(account["cause"], "launched-image-missing")
        self.assertIsNone(account["launched_image"])
        self.assertEqual(account["outcome"], "held")
        self.assertEqual(account["attribution"]["actual_participation"], "unknown")
        self.assertIn(attempts.attempt_runtime_of(control, attempt)["execution_runtime"], ("quiescent", "destroyed"))
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertNotEqual(self.states(job, composed)["review"], "waiting")
        self.assertIn("host acceptance: held", model_attribution.diagnostic_of(control, attempt))

    def test_frozen_receipt_and_ending_refuse_later_conflicting_engine_evidence(self):
        from baton_v12.worker_manager import image_receipts
        from baton_v12.contracts import ContractRefusal
        held = self.implemented()
        account = model_attribution.assessment_of(held.control, held.attempt_id)
        receipt = account["launched_image"]
        self.assertEqual(receipt["observation"]["image_id"], self.config["image_digest"])
        changed = dict(receipt["observation"], image_id="sha256:" + "f" * 64)
        image_receipts.retain(held.control, held.attempt_id, changed["runtime_id"], changed)
        self.assertEqual(model_attribution.assessment_of(held.control, held.attempt_id), account)
        self.assertIn("host acceptance: held", model_attribution.diagnostic_of(held.control, held.attempt_id))
        with self.assertRaises(ContractRefusal): model_attribution.assess(held.control, held.attempt_id)
        with self.assertRaises(ContractRefusal): model_attribution.bind_ending(held.control, held.attempt_id, {})
