"""Independent K review probes, connected: the candidate's own composed-Job harness (simulated engine and provider, real
admission, worker entry, freeze, ending, stores) driven through cases its tests do not ask. No engine, image or provider."""
import json, os, traceback, unittest
from pathlib import Path
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import sweep, status, JobStore
from baton_v12.worker_manager import model_attribution, provider_home, ControlStore
from tests.job_manager import fixtures
from tests.manager import provider_fixtures as fake
from tests.tools import test_provider_selection as theirs
from tools import stage_execution, job_observation

EDIT = {"harness.py": "print('changed')\n"}


class Probe(theirs.SelectedCase):
    def reopened(self, name):
        job = JobStore.open(self.job_path, authority_uuid=self.config["authority_uuid"], incarnation=name, clock=lambda: fixtures.NOW)
        control = ControlStore.open(self.control_path, incarnation=name, clock=lambda: fixtures.NOW)
        self.addCleanup(job.close); self.addCleanup(control.close)
        composed = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret, clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close); self._composed = composed
        return job, control, composed

    def line(self, job, composed, kind):
        snapshot = status(job, composed, observed_at=fixtures.NOW)
        stage = next(one for one in snapshot["jobs"][0]["stages"] if one["kind"] == kind)
        shown = job_observation._stage_line(stage, fixtures.NOW)
        return {key: shown.get(key) for key in ("state", "reason", "model_attribution")} | {"stage_state": stage.get("state"), "gate": stage.get("gate")}

    def test_C1_a_missing_attribution_stays_held_through_many_passes_and_a_restart(self):
        self.reported = None
        job, control, composed, attempt = self.started()
        self.assertEqual(self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits=EDIT), 0)
        for _ in range(20):
            sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assessment_of(control, attempt)
        states = self.states(job, composed)
        print("C1 states after 20 passes:", states)
        print("C1 shown:", json.dumps(self.line(job, composed, "implementation")))
        self.assertEqual((account["outcome"], account["cause"]), ("held", "model-attribution-missing"))
        self.assertEqual(len(self.invocations), 2)
        self.assertNotIn(states["review"], ("waiting", "claimed", "completed"))
        composed.close(); job.close(); control.close()
        job, control, composed = self.reopened("k-probe-restart")
        for _ in range(20):
            sweep(job, composed, now=fixtures.NOW)
        self.assertEqual(model_attribution.assessment_of(control, attempt), account)
        self.assertEqual(len(self.invocations), 2, "a held attribution was retried after restart")
        after = self.states(job, composed)
        print("C1 states after restart and 20 more passes:", after)
        self.assertNotIn(after["review"], ("waiting", "claimed", "completed"))
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        from baton_v12.job_manager import scheduler, submission
        rows = [one for one in submission.stage_rows(job) if one["kind"] == "implementation"]
        print("C1 implementation stage rows:", [{k: one.get(k) for k in ("stage_id", "state", "episode", "held_reason", "reason") if k in one} for one in rows])

    def test_C2_a_worker_that_claims_matched_against_bytes_that_say_otherwise_is_held(self):
        import claude_agent
        original = claude_agent.ClaudeAgent.work
        def lying(agent, seen, declared):
            answer = original(agent, seen, declared)
            for output in answer["outputs"]:
                claim = output.get("result_metadata", {}).get("baton.model-attribution/1")
                if claim is not None:
                    claim.update(contributors=["different-model", "fixture-reported"], outcome="matched",
                                 contributor_sources={"different-model": ["modelUsage"], "fixture-reported": ["modelUsage"]})
            return answer
        self.reported = ["different-model"]
        job, control, composed, attempt = self.started()
        with mock.patch.object(claude_agent.ClaudeAgent, "work", lying):
            self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits=EDIT)
        for _ in range(6):
            sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assessment_of(control, attempt)
        print("C2 account:", account["outcome"], account["cause"])
        self.assertEqual(account["outcome"], "held")
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertNotIn(self.states(job, composed)["review"], ("waiting", "claimed", "completed"))

    def test_C3_what_a_pass_does_when_a_held_attempts_log_is_later_replaced_with_matching_bytes(self):
        self.reported = ["different-model"]
        job, control, composed, attempt = self.started()
        self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits=EDIT)
        for _ in range(4):
            sweep(job, composed, now=fixtures.NOW)
        account = model_attribution.assessment_of(control, attempt)
        self.assertEqual(account["cause"], "model-attribution-conflicting")
        selected = model_attribution.selection_of(control, attempt)
        Path(selected["logs_root"], attempt, "provider.stdout.log").write_bytes(fake.terminal("fixture-reported"))
        raised = None
        try:
            for _ in range(4):
                sweep(job, composed, now=fixtures.NOW)
        except Exception as failure:   # noqa: BLE001 -- the probe records what the pass does
            raised = failure
        print("C3 pass after log replacement:", "RAISED " + type(raised).__name__ + ": " + str(raised)[:160] if raised else "returned normally")
        self.assertEqual(model_attribution.assessment_of(control, attempt), account, "a held decision was upgraded by a replaced log")
        self.assertIsNone(model_attribution._read(control, "provider.attribution-ending", attempt))
        self.assertNotIn(self.states(job, composed)["review"], ("waiting", "claimed", "completed"))

    def test_C4_restart_after_the_home_has_moved_to_the_correction_attempt(self):
        held = self.reviewed("changes-requested")
        self.drive(held.job, held.composed, "implementation", "waiting", ticks=12)
        worker = self.worker_of(held.composed, "implementation")
        second = next(one for one in worker.stage._prepared if one != held.attempt_id)
        first = model_attribution.selection_of(held.control, held.attempt_id)["delivery"]
        record = provider_home.location(self.config["provider_home_root"], first["home_identity"]) / "record.json"
        self.assertEqual(json.loads(record.read_text())["holder"], second)
        print("C4 diagnostic of the FIRST attempt once the second holds:", model_attribution.diagnostic_of(held.control, held.attempt_id))
        held.composed.close(); held.job.close(); held.control.close()
        job, control, composed = self.reopened("k-probe-moved")
        raised = None
        try:
            for _ in range(8):
                sweep(job, composed, now=fixtures.NOW)
            shown = self.line(job, composed, "implementation")
        except Exception as failure:   # noqa: BLE001
            raised = failure; traceback.print_exc()
        print("C4 after restart:", "RAISED " + type(raised).__name__ + ": " + str(raised)[:200] if raised else "passes and status returned normally")
        self.assertIsNone(raised)
        self.assertEqual(json.loads(record.read_text())["holder"], second)
        # (first run: I went on to drive the second attempt after the restart; the harness keeps its mount map in the composition I had closed, so that step was my harness misuse and is removed. The restart question is answered above.)

    def test_C5_the_selection_of_a_started_attempt_cannot_be_replaced(self):
        held = self.implemented()
        selected = model_attribution.selection_of(held.control, held.attempt_id)
        other = fake.delivery(attempt=held.attempt_id, job=selected["delivery"]["home_identity"]["job_id"], requested_model="other", reported_identity="fixture-additional")
        with self.assertRaises(ContractRefusal):
            model_attribution.select(held.control, other, phase="implementation", logs_root=selected["logs_root"], home_root=selected["home_root"])
        self.assertEqual(model_attribution.selection_of(held.control, held.attempt_id), selected)


    def test_C6_a_holder_that_never_started_a_runtime(self):
        """What evidence exists for a holder whose launch was refused after the home was held and before any runtime."""
        from baton_v12.worker_manager import attempts, launch
        job, control, composed = self.serving()
        from baton_v12.job_manager import submit
        submit(job, self.submission)
        calls = []
        def refused(*a, **k):
            calls.append(k.get("attempt_id")); raise ContractRefusal("refused", "precondition", "probe: launch delivery refused")
        raised = None
        with mock.patch.object(launch, "materialize", side_effect=refused):
            try:
                for _ in range(12):
                    sweep(job, composed, now=fixtures.NOW)
            except Exception as failure:   # noqa: BLE001
                raised = failure
        print("C6 passes:", "RAISED " + type(raised).__name__ + ": " + str(raised)[:160] if raised else "returned normally", "| materialize asked for", sorted(set(calls)))
        print("C6 states:", self.states(job, composed))
        root = Path(self.config["provider_home_root"])
        records = [json.loads(one.read_text()) for one in root.glob("*/*/record.json")]
        print("C6 home records:", [(one["holder"], one["state"]) for one in records])
        for one in records:
            evidence = attempts.provider_home_cessation_of(control, one["holder"])
            print("C6 cessation evidence for the holder:", evidence, "| ceased:", provider_home.ceased(evidence, one["holder"]))
        for _ in range(12):
            sweep(job, composed, now=fixtures.NOW)
        print("C6 states after 12 unpatched passes:", self.states(job, composed))
        records = [json.loads(one.read_text()) for one in root.glob("*/*/record.json")]
        print("C6 home records after:", [(one["holder"], one["state"]) for one in records], "| invocations:", len(self.invocations))


    def test_C7_the_real_workers_result_file_carries_the_claim_recovery_reads(self):
        """Owner B's tests inject provider.attribution into a hand-built result. Does the REAL worker write that member,
        equal to the claim the ordinary ending validated, and does the recovery reader accept it against the retained log?"""
        from baton_v12.worker_manager import intake_receipt_of, load_manifest, frozen_output_of
        from baton_v12.job_manager import publication_recovery
        held = self.implemented()
        frozen = frozen_output_of(held.control, held.attempt_id)
        manifest = load_manifest(held.control, frozen["manifest_digest"], "resultManifest")
        claims = [one["result_metadata"]["baton.model-attribution/1"] for one in manifest["outputs"] if "baton.model-attribution/1" in one.get("result_metadata", {})]
        self.assertEqual(len(claims), 1)
        result_path, _ = publication_recovery.producer_entries(publication_recovery.corrective_declaration())
        found = []
        for artifact in intake_receipt_of(held.control, held.attempt_id)["artifacts"]:
            root = Path(artifact["custody_locator"].removeprefix("file://"))
            found += [one for one in ([root] if root.is_file() else root.rglob("*")) if one.is_file() and str(one).endswith(result_path)]
        print("C7 result path the recovery reads:", result_path, "| found in custody:", len(found))
        self.assertTrue(found)
        document = json.loads(found[0].read_bytes())
        inside = document.get("provider", {}).get("attribution")
        print("C7 provider.attribution present in the real result file:", inside is not None, "| equals the validated claim:", inside == claims[0])
        self.assertEqual(inside, claims[0])
        checked = model_attribution.recovery_evidence(held.control, held.attempt_id, candidate={"base": "b", "head": "h"}, tree_digest="sha256:" + "0" * 64,
                                                      result_digest="sha256:" + "1" * 64, claim=inside)
        self.assertEqual(checked["attribution"]["outcome"], "matched")
        for bad in (None, dict(inside, outcome="conflicting"), dict(inside, attempt_id="other")):
            with self.assertRaises(ContractRefusal):
                model_attribution.recovery_evidence(held.control, held.attempt_id, candidate={"base": "b", "head": "h"}, tree_digest="sha256:" + "0" * 64, result_digest="sha256:" + "1" * 64, claim=bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
