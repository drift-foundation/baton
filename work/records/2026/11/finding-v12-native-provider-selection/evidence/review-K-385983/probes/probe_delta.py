"""Independent K delta probes for candidate 4980bb47 (R1-R4). The candidate's own composed-Job harness: simulated engine and
provider, real admission, worker entry, stores and home owner. No engine, image or provider. Prints what it observes."""
import json, os, unittest
from pathlib import Path
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import sweep, status, submit, submission
from baton_v12.worker_manager import attempts, launch, model_attribution, provider_home, oci
from tests.job_manager import fixtures
from tests.tools import test_provider_selection as theirs
from tools import job_observation


class Delta(theirs.SelectedCase):
    def record(self):
        path, = Path(self.config["provider_home_root"]).glob("*/*/record.json")
        return path, json.loads(path.read_text())

    def successor(self, control, composed, job, name):
        """An explicit second attempt of the same worker for the same Job, through the worker's own hold."""
        worker = self.worker_of(composed, "implementation")
        attempts.record_attempt(control, attempt_id=name, adapter_name="docker",
            adapter_digest=self.config["adapter_digest"], profile_digest=self.config["profile_digest"])
        stage = dict(next(one for one in submission.stage_rows(job) if one["kind"] == "implementation"), attempt_id=name)
        worker._hold_provider_home(stage)
        return stage

    def passes(self, job, composed, count=12):
        raised = None
        try:
            for _ in range(count):
                sweep(job, composed, now=fixtures.NOW)
        except BaseException as failure:   # noqa: BLE001
            raised = failure
        return raised

    def test_D1_prestart_refusal_now_releases_and_the_old_holder_cannot_start(self):
        job, control, composed = self.serving(); submit(job, self.submission)
        with mock.patch.object(launch, "materialize", side_effect=ContractRefusal("refused", "precondition", "probe: delivery refused")):
            self.passes(job, composed)
        path, record = self.record(); previous = record["holder"]
        evidence = attempts.provider_home_cessation_of(control, previous)
        print("D1 states:", self.states(job, composed), "| record:", record["holder"] == previous, record["state"])
        print("D1 evidence:", evidence, "| ceased:", provider_home.ceased(evidence, previous))
        self.assertTrue(provider_home.ceased(evidence, previous))
        # evidence about this holder does not release for any other holder name
        self.assertFalse(provider_home.ceased(evidence, "someone-else"))
        self.assertFalse(provider_home.ceased(dict(evidence, ended_before_start="yes"), previous))
        self.assertFalse(provider_home.ceased(dict(evidence, ended_before_start=True, runtime="start-requested"), previous))
        self.successor(control, composed, job, "k-successor")
        self.assertEqual(self.record()[1]["holder"], "k-successor")
        engine = mock.Mock()
        for policy in (None,):
            with self.assertRaises(ContractRefusal) as caught:
                attempts.request_runtime_start(control, engine, attempt_id=previous)
            print("D1 delayed start of the released holder:", caught.exception.category, caught.exception.code, "|", str(caught.exception)[:90])
        engine.start.assert_not_called()
        self.assertIsNone(control.operation_record(attempts._start_operation_id(attempts._attempt_row(control, previous))))
        # the old holder cannot take the home back either: the successor's cessation is unproved
        worker = self.worker_of(composed, "implementation")
        stage = dict(next(one for one in submission.stage_rows(job) if one["kind"] == "implementation"), attempt_id=previous)
        with self.assertRaises(provider_home.HomePending):
            worker._hold_provider_home(stage)
        self.assertEqual(self.record()[1]["holder"], "k-successor")
        print("D1 old holder asking for the home back: pending; holder stays k-successor; provider invocations:", len(self.invocations))

    def test_D2_the_fence_is_inside_the_start_transaction(self):
        """The real worker path. A preparation ending commits (as another manager process would write it) after the start
        caller's preliminary checks and immediately before its start transaction. (Two earlier forms of this probe called
        request_runtime_start by hand and stopped at the plan and input-root checks, my misuse; first-run logs retained.)"""
        job, control, composed = self.serving(); submit(job, self.submission)
        store = type(control); real = store.transact
        injected = []
        def racing(self_store, operation_id, kind, signature, act, *a, **k):
            if kind == "runtime.start" and not injected:
                attempt = operation_id and next(row["runtime_attempt_id"] for row in attempts._attempts(self_store, "ORDER BY runtime_attempt_id")
                                                if attempts._start_operation_id(row) == operation_id)
                injected.append(attempt)
                said = attempts._record_preparation_failure(self_store, attempt, attempts._refusal_failure(ContractRefusal("refused", "precondition", "probe: concurrent preparation ending")))
                injected.append(said)
            return real(self_store, operation_id, kind, signature, act, *a, **k)
        starts = []
        real_start = oci.OciAdapter.start
        def counted(adapter, *a, **k):
            starts.append(1); return real_start(adapter, *a, **k)
        with mock.patch.object(store, "transact", racing), mock.patch.object(oci.OciAdapter, "start", counted):
            raised = self.passes(job, composed)
        self.assertTrue(injected, "the start transaction was never reached")
        previous = injected[0]
        row = attempts._attempt_row(control, previous)
        print("D2 passes:", ("RAISED " + type(raised).__name__ + ": " + str(raised)[:120]) if raised else "returned", "| states:", self.states(job, composed))
        print("D2 ending injected before the start transaction:", attempts.attempt_preparation_failure_of(control, previous) is not None, "| start operation journalled:",
              control.operation_record(attempts._start_operation_id(row)) is not None, "| axis:", row["execution_runtime"], "| adapter start calls:", len(starts), "| invocations:", len(self.invocations))
        evidence = attempts.provider_home_cessation_of(control, previous)
        print("D2 evidence:", evidence, "| ceased:", provider_home.ceased(evidence, previous))
        self.assertEqual(len(starts), 0)
        self.assertIsNone(control.operation_record(attempts._start_operation_id(row)))
        self.assertEqual(row["execution_runtime"], "not-started")
        self.assertTrue(provider_home.ceased(evidence, previous))

    def test_D3_an_ending_recorded_after_a_start_was_requested_does_not_release(self):
        job, control, composed = self.serving(); submit(job, self.submission)
        with mock.patch.object(oci.OciAdapter, "start", side_effect=KeyboardInterrupt("probe: start caller lost")):
            raised = self.passes(job, composed)
        self.assertIsInstance(raised, KeyboardInterrupt)
        path, record = self.record(); previous = record["holder"]
        said = attempts._record_preparation_failure(control, previous, attempts._refusal_failure(ContractRefusal("refused", "precondition", "probe: later continuation refused")))   # (first run passed the refusal itself, my misuse)
        ending = attempts.attempt_preparation_failure_of(control, previous)
        evidence = attempts.provider_home_cessation_of(control, previous)
        print("D3 ending recorded after start intent:", ending is not None, "| its axes:", ending and (ending["execution_runtime"], ending["runtime_id"]), "| note:", repr(said)[:80])
        print("D3 evidence:", evidence, "| ceased:", provider_home.ceased(evidence, previous))
        self.assertIsNotNone(ending)
        self.assertFalse(provider_home.ceased(evidence, previous))
        with self.assertRaises(provider_home.HomePending):
            self.successor(control, composed, job, "k-successor")
        self.assertEqual(self.record()[1], record)

    def test_D4_a_start_the_engine_refused(self):
        """Start intent exists and the adapter refused. What does the holder's evidence say, and can a successor ever take the home?"""
        job, control, composed = self.serving(); submit(job, self.submission)
        with mock.patch.object(oci.OciAdapter, "start", side_effect=ContractRefusal("refused", "precondition", "probe: engine refused the start")):
            raised = self.passes(job, composed)
        print("D4 passes:", ("RAISED " + type(raised).__name__ + ": " + str(raised)[:100]) if raised else "returned", "| states:", self.states(job, composed))
        path, record = self.record(); previous = record["holder"]
        raised = self.passes(job, composed)
        row = attempts._attempt_row(control, previous)
        evidence = attempts.provider_home_cessation_of(control, previous)
        print("D4 after 12 more ordinary passes:", ("RAISED " + type(raised).__name__) if raised else "returned", "| states:", self.states(job, composed))
        print("D4 start failure recorded:", attempts.attempt_start_failure_of(control, previous) is not None, "| preparation ending:", attempts.attempt_preparation_failure_of(control, previous) is not None,
              "| axis:", row["execution_runtime"], "| runtime_id:", row["runtime_id"], "| cleanup:", row["cleanup"])
        print("D4 evidence:", evidence, "| ceased:", provider_home.ceased(evidence, previous), "| record state:", record["state"], "| invocations:", len(self.invocations))

    def test_D5_home_creation_itself_fails_after_the_holder_record(self):
        """An ordinary error (not a process death) creating home/ after record.json names the holder."""
        job, control, composed = self.serving(); submit(job, self.submission)
        root = os.path.realpath(self.config["provider_home_root"])
        original = os.mkdir
        hits = []
        def full(path, *args, **kwargs):
            if path == "home" and kwargs.get("dir_fd") is not None and os.readlink("/proc/self/fd/%d" % kwargs["dir_fd"]).startswith(root + os.sep):
                hits.append(1); raise OSError(28, "No space left on device")
            return original(path, *args, **kwargs)
        with mock.patch.object(os, "mkdir", side_effect=full):
            raised = self.passes(job, composed)
        print("D5 passes:", ("RAISED " + type(raised).__name__ + ": " + str(raised)[:100]) if raised else "returned", "| mkdir refusals:", len(hits), "| states:", self.states(job, composed))
        path, record = self.record(); previous = record["holder"]
        evidence = attempts.provider_home_cessation_of(control, previous)
        print("D5 record:", record["state"], "| home exists:", (path.parent / "home").exists(), "| preparation ending:", attempts.attempt_preparation_failure_of(control, previous) is not None)
        print("D5 evidence:", evidence, "| ceased:", provider_home.ceased(evidence, previous))
        try:
            self.successor(control, composed, job, "k-successor")
            print("D5 successor: ACQUIRED; record:", self.record()[1]["holder"], self.record()[1]["state"])
        except provider_home.HomePending as pending:
            print("D5 successor: PENDING —", str(pending), "| record unchanged:", self.record()[1] == record)
        raised = self.passes(job, composed)
        print("D5 after 12 ordinary passes with the disk healthy:", ("RAISED " + type(raised).__name__) if raised else "returned", "| states:", self.states(job, composed), "| record:", self.record()[1]["holder"] == previous, self.record()[1]["state"])

    def test_D6_hold_reason_on_real_status_for_each_cause_and_not_for_matched(self):
        import claude_agent
        def shown(job, composed):
            snapshot = status(job, composed, observed_at=fixtures.NOW)
            stage = next(one for one in snapshot["jobs"][0]["stages"] if one["kind"] == "implementation")
            view = job_observation.stage_view(stage, fixtures.NOW)
            return stage["state"], stage["runtime"].get("model_attribution_hold"), view.get("reason"), view.get("outcome")
        # conflicting: the provider reports another model
        self.reported = ["different-model"]
        job, control, composed, attempt = self.started()
        self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        self.passes(job, composed, 6)
        account = model_attribution.assessment_of(control, attempt)
        print("D6 conflicting:", account["outcome"], account["cause"], "| shown:", shown(job, composed), "| review:", self.states(job, composed)["review"])
        self.assertEqual(shown(job, composed)[1:3], ("model-attribution-conflicting", "held: model-attribution-conflicting; owner action needed"))

    def test_D7_matched_shows_no_hold(self):
        job, control, composed, attempt = self.started()
        self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        self.passes(job, composed, 6)
        account = model_attribution.assessment_of(control, attempt)
        snapshot = status(job, composed, observed_at=fixtures.NOW)
        stage = next(one for one in snapshot["jobs"][0]["stages"] if one["kind"] == "implementation")
        print("D7 matched:", account and (account["outcome"], account.get("cause")), "| hold member present:", "model_attribution_hold" in stage["runtime"], "| reason:", repr(job_observation.stage_view(stage, fixtures.NOW).get("reason")), "| state:", stage["state"])
        self.assertNotIn("model_attribution_hold", stage["runtime"])

    def test_D8_invalid_claim_shows_invalid(self):
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
            self.turn(control, "implementation", attempt, self.mounted(composed, "implementation", attempt), edits={"harness.py": "print('changed')\n"})
        self.passes(job, composed, 6)
        account = model_attribution.assessment_of(control, attempt)
        snapshot = status(job, composed, observed_at=fixtures.NOW)
        stage = next(one for one in snapshot["jobs"][0]["stages"] if one["kind"] == "implementation")
        print("D8 invalid:", account["outcome"], account["cause"], "| reason:", job_observation.stage_view(stage, fixtures.NOW).get("reason"))
        self.assertEqual(job_observation.stage_view(stage, fixtures.NOW)["reason"], "held: model-attribution-invalid; owner action needed")


if __name__ == "__main__":
    suite = unittest.TestSuite(Delta(name) for name in sorted(dir(Delta)) if name.startswith("test_D"))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
