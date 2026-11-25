"""Owner B: simulated original provider, real recovery admission and custody.

The existing recovery fixture simulates the already-ended producer/runtime and
Git correspondence. It exercises real Authority, stores, retained disk output,
publication worker, result intake and handoff. No model, image or engine runs.
"""
import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.provider_policy import attribution
from baton_v12.worker_manager import model_attribution, attempt_logs, ControlStore
from baton_v12.job_manager import publication_recovery, publication_execution
from tests.manager import provider_fixtures as fake
from tests.job_manager import test_publication_recovery_execution as execution
from tests.job_manager import test_publication_recovery_admission as admission


class OriginalProducer(execution.PublicationExecutionCase):
    def launched(self, *, now=execution.PUBLISHED):
        reports = []
        for _ in range(4):
            reports.append(self.tick(now))
            view = self.exchange_view()
            if view is not None and view.get("command") is not None:
                return view
        self.fail("publication command missing: " + repr(reports))

    def select_original_provider(self, attempt):
        self.selected = fake.delivery(attempt=attempt, job=self.job_id, authority=admission.UUID)
        self.logs_root = str(Path(self.root, "logs"))
        model_attribution.select(self.control, self.selected, phase="implementation", logs_root=self.logs_root)
        logs = attempt_logs.materialize(self.logs_root, attempt_id=attempt, workspace_group=self.group)
        import claude_agent
        import attempt_log_format
        self.raw = fake.terminal("fixture-reported", "fixture-additional")
        room = attempt_log_format.open_room(logs.log_root)
        capture = claude_agent._Captured(room, attempt_log_format, "provider.stdout")
        capture.wrote(self.raw)
        capture.declare(claude_agent._Outcome.COMPLETED)
        self.claim = attribution.record(self.selected, phase="implementation", evidenced_build="2.1.247", raw=self.raw)

    def write_output(self, *, result=None, **kwargs):
        if result is None:
            result = admission.proposal_result()
            result["provider"]["attribution"] = self.claim
        return super().write_output(result=result, **kwargs)

    def test_B1_original_attribution_travels_through_admission_custody_and_handoff(self):
        self.ready()
        admitted = publication_recovery.admission_for(self.jobs, self.recovery_job_id)
        binding = admitted["candidate"]["model_attribution"]
        self.assertEqual(binding["attempt_id"], self.attempt_id)
        self.assertEqual(binding["tree_digest"], self.original["tree_digest"])
        self.assertEqual(binding["attribution"]["contributors"], ["fixture-additional", "fixture-reported"])
        self.published_once()
        custody = self.collected()
        self.assertEqual(custody["adopted"]["model_attribution"], binding)
        handed = self.handed_off()
        self.assertEqual(handed["candidate"]["model_attribution"], binding)
        self.assertNotEqual(handed["publication_attempt_id"], binding["attempt_id"])
        self.assertIsNone(model_attribution.selection_of(self.control, handed["publication_attempt_id"]))
        self.assertTrue(self.gate()["open"])
        self.assertEqual(self.original_digest(), binding["tree_digest"])

    def test_B2_B3_missing_conflicting_and_cross_attempt_hold_inspection_and_admission(self):
        for claim in (None, dict(self.claim, attempt_id="other-attempt"), dict(self.claim, outcome="conflicting"),
                      attribution.record(self.selected, phase="implementation", evidenced_build="2.1.999", raw=self.raw)):
            with self.subTest(claim=claim):
                document = admission.proposal_result()
                if claim is not None:
                    document["provider"]["attribution"] = claim
                self.write_output(result=document)
                inspected = self.inspected()
                self.assertFalse(inspected["eligible"])
                self.assertTrue(any("model-attribution-" in one["message"] for one in inspected["holds"]))
                with self.assertRaises(ContractRefusal):
                    self.approved(selection=inspected)
        self.assertEqual(self.journal(publication_recovery.ADMITTED_KIND), [])

    def test_B4_cross_candidate_substitution_after_decision_refuses(self):
        self.approved()
        document = admission.proposal_result(head="d" * 40)
        document["provider"]["attribution"] = self.claim
        self.write_output(result=document)
        with self.assertRaises(ContractRefusal):
            self.admit()
        self.assertEqual(self.journal(publication_recovery.ADMITTED_KIND), [])

    def test_B5_log_tampering_after_admission_refuses_custody_and_handoff(self):
        self.ready()
        self.published_once()
        Path(self.logs_root, self.attempt_id, "provider.stdout.log").write_bytes(fake.terminal("wrong"))
        with self.assertRaises(ContractRefusal):
            self.collected()
        with self.assertRaises(ContractRefusal):
            self.handed_off()
        self.assertFalse(self.gate()["open"])

    def test_B6_reopen_replays_admission_and_handoff_without_repeating_publisher(self):
        self.ready()
        self.published_once()
        first = self.collected()
        handed = self.handed_off()
        vectors = list(self.oci.vectors)
        self.assertEqual(self.collected(), first)
        self.assertEqual(self.handed_off(), handed)
        self.assertEqual(self.oci.vectors, vectors)
        with ControlStore.open(self.control.database, incarnation="model-recovery-reopened", clock=self.clock) as reopened:
            held = publication_recovery.admission_for(self.jobs, self.recovery_job_id)
            self.assertEqual(model_attribution.require_recovery(reopened, held["candidate"]["model_attribution"]), held["candidate"]["model_attribution"])
            ports = self.ported()
            again = publication_recovery.admit_publication(self.jobs, reopened, decision_id="D1",
                exclusion=ports["exclusion"], authorization=ports["authorization"], binding=ports["binding"],
                ownership=ports["ownership"], host=ports["host"], source=ports["source"], ending=ports["ending"])
            self.assertEqual(again, held)
        self.assertEqual(len(self.oci.starts), 1)


class ConfiguredProducer(OriginalProducer):
    def setUp(self):
        super().setUp()
        from baton_v12.worker_manager import attempts
        # Existing original-producer fixture seeds an ended attempt. Supply its
        # synthetic image facts at the normal adapter observation boundary;
        # the host, not this fixture, writes the receipt.
        self.control._connection.execute("UPDATE attempts SET policy_digest = ? WHERE runtime_attempt_id = ?",
            ("sha256:" + "d" * 64, self.attempt_id))
        row = attempts._require_attempt(self.control, self.attempt_id)
        self.image_observation = {"engine": "docker", "runtime_id": row["runtime_id"],
            "image_id": self.selected["contract"]["runtime_profile"]["image_digest"],
            "started_at": "2026-11-25T00:00:00Z", "labels": attempts._runtime_labels(row), "resolution": None}
        if getattr(self, "capture_initial_image", True):
            self.observe_image(self.image_observation)

    def observe_image(self, observation):
        from baton_v12.worker_manager import attempts
        adapter = mock.Mock()
        adapter.observe.return_value = {"state": "quiescent", "why": "simulated ended producer", "image_observation": observation}
        return attempts._observed(adapter, "runtime-" + self.attempt_id, store=self.control, attempt_id=self.attempt_id)

    def select_original_provider(self, attempt):
        from baton_v12 import provider_policy as policy
        from tests.manager import codex_fixtures
        import claude_agent
        import attempt_log_format
        self.enterContext(codex_fixtures.simulated(policy))
        self.selected, self.invocation = codex_fixtures.configured(policy, attempt=attempt,
            job=self.job_id, authority=admission.UUID)
        self.logs_root = str(Path(self.root, "logs"))
        model_attribution.select(self.control, self.selected, phase="implementation", logs_root=self.logs_root)
        logs = attempt_logs.materialize(self.logs_root, attempt_id=attempt, workspace_group=self.group)
        self.raw = (Path(__file__).parents[1]/"manager/fixtures/codex-0.169.0/turn-success.sanitized.jsonl").read_bytes()
        room = attempt_log_format.open_room(logs.log_root)
        for stream, raw in (("provider.stdout", self.raw), ("provider.invocation", json.dumps(self.invocation).encode())):
            capture = claude_agent._Captured(room, attempt_log_format, stream)
            capture.wrote(raw); capture.declare(claude_agent._Outcome.COMPLETED)
        self.claim = attribution.record(self.selected, phase="implementation", evidenced_build="0.169.0",
            raw=self.raw, invocation=self.invocation)

    def test_B1_original_attribution_travels_through_admission_custody_and_handoff(self):
        self.ready()
        binding = publication_recovery.admission_for(self.jobs, self.recovery_job_id)["candidate"]["model_attribution"]
        self.assertEqual(binding["attribution"]["basis"], "configured-model")
        self.assertEqual(binding["attribution"]["actual_participation"], "unknown")
        self.assertEqual(binding["attribution"]["contributors"], [])
        self.published_once()
        self.assertEqual(self.collected()["adopted"]["model_attribution"], binding)
        self.assertEqual(self.handed_off()["candidate"]["model_attribution"], binding)
        self.assertTrue(self.gate()["open"])

    def test_invocation_receipt_tampering_holds_recovery(self):
        self.ready()
        self.published_once()
        changed = dict(self.invocation, prompt_digest="sha256:"+"f"*64)
        Path(self.logs_root, self.attempt_id, "provider.invocation.log").write_bytes(json.dumps(changed).encode())
        with self.assertRaises(ContractRefusal): self.collected()
        with self.assertRaises(ContractRefusal): self.handed_off()
        self.assertFalse(self.gate()["open"])


class ImageReceiptRecovery(unittest.TestCase):
    def setUp(self):
        self.case = ConfiguredProducer("runTest")
        self.case.capture_initial_image = False
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        from baton_v12.worker_manager import image_receipts
        self.receipts = image_receipts

    def evidence(self):
        return self.receipts.evidence(self.case.control, self.case.attempt_id,
                                     model_attribution.selection_of(self.case.control, self.case.attempt_id))

    def test_missing_and_historical_codex_receipt_holds_recovery(self):
        self.assertEqual(self.evidence(), (None, "launched-image-missing"))
        inspected = self.case.inspected()
        self.assertFalse(inspected["eligible"])
        self.assertTrue(any("launched-image-missing" in one["message"] for one in inspected["holds"]))

    def test_wrong_runtime_generation_attempt_and_create_only_are_not_retained(self):
        base = self.case.image_observation
        for changes in ({"runtime_id": "foreign"}, {"started_at": "0001-01-01T00:00:00Z"},
                        {"labels": dict(base["labels"], generation=999)},
                        {"labels": dict(base["labels"], runtime_attempt_id="foreign")}):
            state, _, _ = self.case.observe_image(dict(base, **changes))
            self.assertEqual(state, "quiescent")
            self.assertEqual(self.evidence(), (None, "launched-image-missing"))

    def test_matching_labels_do_not_rescue_wrong_engine_image(self):
        self.case.observe_image(dict(self.case.image_observation, image_id="sha256:" + "f" * 64))
        self.assertEqual(self.evidence()[1], "launched-image-mismatch")
        self.assertFalse(self.case.inspected()["eligible"])

    def test_receipt_is_idempotent_and_conflict_holds_without_cessation_change(self):
        self.case.observe_image(self.case.image_observation)
        receipt, cause = self.evidence(); self.assertIsNone(cause)
        self.case.observe_image(copy.deepcopy(self.case.image_observation))
        self.assertEqual(self.evidence(), (receipt, None))
        state, _, _ = self.case.observe_image(dict(self.case.image_observation, image_id="sha256:" + "f" * 64))
        self.assertEqual(state, "quiescent")
        self.assertEqual(self.evidence(), (receipt, "launched-image-invalid"))
        self.assertFalse(self.case.inspected()["eligible"])

    def test_removed_original_runtime_receipt_survives_reopen_and_binds_recovery(self):
        self.case.observe_image(self.case.image_observation)
        receipt, cause = self.evidence(); self.assertIsNone(cause)
        self.case.ready()
        binding = publication_recovery.admission_for(self.case.jobs, self.case.recovery_job_id)["candidate"]["model_attribution"]
        self.assertEqual(binding["launched_image"], receipt)
        with ControlStore.open(self.case.control.database, incarnation="image-receipt-reopen", clock=self.case.clock) as reopened:
            selected = model_attribution.selection_of(reopened, self.case.attempt_id)
            self.assertEqual(self.receipts.evidence(reopened, self.case.attempt_id, selected), (receipt, None))
            self.assertEqual(model_attribution.require_recovery(reopened, binding), binding)
        self.case.published_once()
        self.assertEqual(self.case.collected()["adopted"]["model_attribution"]["launched_image"], receipt)

    def test_conflict_after_admission_cannot_use_publishers_image(self):
        self.case.observe_image(self.case.image_observation)
        self.case.ready(); self.case.published_once()
        self.case.observe_image(dict(self.case.image_observation, image_id="sha256:" + "f" * 64))
        with self.assertRaises(ContractRefusal): self.case.collected()
        with self.assertRaises(ContractRefusal): self.case.handed_off()

    def test_claude_and_legacy_do_not_require_receipts(self):
        selected = model_attribution.selection_of(self.case.control, self.case.attempt_id)
        changed = copy.deepcopy(selected)
        changed["delivery"]["contract"]["selection"]["provider"] = "claude"
        self.assertEqual(self.receipts.evidence(self.case.control, self.case.attempt_id, changed), (None, None))
        self.assertEqual(self.receipts.evidence(self.case.control, self.case.attempt_id, None), (None, None))


    def test_unavailable_resolution_does_not_erase_retained_engine_binding(self):
        image = "sha256:" + "f" * 64
        observation = dict(self.case.image_observation, image_id=image,
            resolution={"image_id": image, "registry_digest": self.case.image_observation["image_id"]})
        self.case.observe_image(observation)
        receipt, cause = self.evidence(); self.assertIsNone(cause)
        self.case.observe_image(dict(observation, resolution=None))
        self.assertEqual(self.evidence(), (receipt, None))


    def test_lost_receipt_reply_replays_without_rewriting_observation(self):
        actual = model_attribution._write
        def lost(control, kind, attempt, value):
            answer = actual(control, kind, attempt, value)
            if kind == self.receipts.KIND:
                raise OSError("synthetic lost reply after durable image receipt")
            return answer
        with mock.patch.object(model_attribution, "_write", side_effect=lost):
            with self.assertRaises(OSError): self.case.observe_image(self.case.image_observation)
        receipt, cause = self.evidence(); self.assertIsNone(cause)
        self.case.observe_image(self.case.image_observation)
        self.assertEqual(self.evidence(), (receipt, None))

    def test_altered_retained_receipt_refuses_binding(self):
        self.case.observe_image(self.case.image_observation)
        receipt, _ = self.evidence()
        actual = model_attribution._read
        for field, value in (("attempt_id", "another"), ("selection_digest", "sha256:" + "f" * 64),
                             ("profile_digest", "sha256:" + "f" * 64), ("schema", "unsupported")):
            changed = dict(receipt, **{field: value})
            def altered(control, kind, attempt):
                return changed if kind == self.receipts.KIND else actual(control, kind, attempt)
            with self.subTest(field=field), mock.patch.object(model_attribution, "_read", side_effect=altered):
                self.assertEqual(self.evidence()[1], "launched-image-invalid")
