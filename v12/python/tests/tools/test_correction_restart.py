"""C1/C2 proofs: deterministic provider children and a simulated OCI engine."""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

from tests.tools import correction_restart_trace as proof


def artifact(*, counted_reopen=False):
    world = proof.World()
    try:
        world.setUp()
        return world.run_scenario(counted_reopen=counted_reopen)
    finally:
        world.doCleanups()


def export(document):
    if os.environ.get("BATON_C_EVIDENCE"):
        Path(os.environ["BATON_C_EVIDENCE"]).write_text(json.dumps(document, indent=2) + "\n")


class UsefulCorrection(unittest.TestCase):
    def test_useful_correction_reaches_managed_target(self):
        observed = artifact()
        export(observed)
        self.assertEqual(proof.validate(observed), [])

    def test_unchanged_predecessor_artifacts_still_validate_without_execution(self):
        root = Path(__file__).resolve().parents[4]
        predecessor = root / "work/records/2026/09/finding-v12-deterministic-scheduler-stress/trace-160959-composed.json"
        body = predecessor.read_bytes()
        self.assertEqual(hashlib.sha256(body).hexdigest(), "5a3ead46c46b5586cbd3a74d7454b402fd04dfbe34414e33a061ac9e90fb9303")
        schedules = json.loads(body)["schedules"]
        self.assertEqual(len(schedules), 18)
        for schedule in schedules:
            self.assertEqual(proof.scheduler_trace.validate(schedule["artifact"]), [])


class UsefulCorrectionInvalidEvidence(unittest.TestCase):
    """Every mutation is a synthetic invalid copy, never an owner receipt."""

    @classmethod
    def setUpClass(cls):
        cls.observed = artifact()
        cls().assertEqual(proof.validate(cls.observed), [])
        cls.rejections = []

    @classmethod
    def tearDownClass(cls):
        export({"kind": "C1 synthetic invalid-evidence results", "valid_observation": cls.observed, "rejections": cls.rejections})

    def rejects(self, name, mutate, expected):
        invalid = copy.deepcopy(self.observed)
        invalid["synthetic_invalid_evidence"] = name
        mutate(invalid)
        failures = proof.validate(invalid)
        self.assertIn(expected, {one["code"] for one in failures}, failures)
        self.rejections.append({"kind": "synthetic invalid evidence", "case": name, "expected": expected, "violations": failures})
        self.assertEqual(proof.validate(self.observed), [])

    def test_identical_revised_code_is_rejected(self):
        self.rejects("revised code replaced by original", lambda x: x["revised"]["content"].__setitem__("scale.py", copy.deepcopy(x["initial"]["content"]["scale.py"])), "C1-code-unchanged")

    def test_unexecuted_or_wrong_byte_verifier_is_rejected(self):
        self.rejects("verifier never executed", lambda x: x["verifications"][1].__setitem__("execution", "not-run"), "C1-verifier-execution")
        self.rejects("verifier measures original bytes", lambda x: x["verifications"][1].__setitem__("code_digest", x["initial"]["content"]["scale.py"]["digest"]), "C1-verifier-bytes")
        self.rejects("revised verifier absent", lambda x: x["verifications"].pop(), "C1-verifier-missing")

    def test_target_receipt_naming_original_is_rejected(self):
        self.rejects("target receipt names original revision", lambda x: x["target"]["receipt"].__setitem__("candidate_digest", x["initial"]["checkpoint"]["head_object"]), "C1-target-receipt")
        self.rejects("target content names original code", lambda x: x["target"].__setitem__("code_digest", x["initial"]["content"]["scale.py"]["digest"]), "C1-target-bytes")

    def test_missing_or_forged_changes_requested_verdict_is_rejected(self):
        self.rejects("changes-requested verdict absent", lambda x: x.__setitem__("verdict", None), "C1-incomplete-evidence")
        self.rejects("changes-requested verdict forged", lambda x: x["verdict"].__setitem__("disposition", "accepted"), "C1-verdict")
        self.rejects("verdict names another checkpoint", lambda x: x["verdict"].__setitem__("checkpoint_id", x["revised"]["checkpoint"]["checkpoint_id"]), "C1-verdict-attribution")
        self.rejects("correction names original attempt", lambda x: x["correction"]["evidence"].__setitem__("routed", x["initial"]["settlement"]["attempt_id"]), "C1-correction-route")

    def test_reviewer_context_or_writable_line_access_is_rejected(self):
        self.rejects("reviewer receives producer context", lambda x: x["reviews"][0]["launch"].__setitem__("provider_context", x["initial"]["binding"]), "C1-review-context")
        def writable(x):
            source = next(m for m in x["reviews"][0]["mounts"] if m["target"] == "/input/source")
            source["source"] = x["reviews"][0]["producer_workspace"]
            source["readonly"] = False
        self.rejects("reviewer receives writable producer line", writable, "C1-review-writable-line")
        self.rejects("reviewer receives private mount", lambda x: x["reviews"][0]["mounts"].append({"source": x["reviews"][0]["private_context_root"], "target": "/run/baton/context", "readonly": True}), "C1-review-context")


class CountedReopen(unittest.TestCase):
    def test_manager_recomposition_preserves_both_positive_counts(self):
        observed = artifact(counted_reopen=True)
        export(observed)
        self.assertEqual(proof.validate(observed, counted_reopen=True), [])

    test_unchanged_predecessor_artifacts_still_validate_without_execution = UsefulCorrection.test_unchanged_predecessor_artifacts_still_validate_without_execution


class CountedReopenInvalidEvidence(unittest.TestCase):
    """Separate mutations of actual provider and engine observations."""

    @classmethod
    def setUpClass(cls):
        cls.observed = artifact(counted_reopen=True)
        cls().assertEqual(proof.validate(cls.observed, counted_reopen=True), [])
        cls.rejections = []

    @classmethod
    def tearDownClass(cls):
        export({"kind": "C2 synthetic invalid-evidence results", "valid_observation": cls.observed, "rejections": cls.rejections})

    def rejects(self, name, mutate, expected):
        invalid = copy.deepcopy(self.observed)
        invalid["synthetic_invalid_evidence"] = name
        mutate(invalid)
        failures = proof.validate(invalid, counted_reopen=True)
        self.assertIn(expected, {one["code"] for one in failures}, failures)
        self.rejections.append({"kind": "synthetic invalid evidence", "case": name, "expected": expected, "violations": failures})
        self.assertEqual(proof.validate(self.observed, counted_reopen=True), [])

    def duplicate(self, stream, point, revised=False):
        def mutate(x):
            counters = x["final_counters"] if point == "final" else x["reopen"][point]
            attempt = x["revised" if revised else "initial"]["binding"]["attempt_id"]
            counters[stream].append(copy.deepcopy(next(one for one in counters[stream] if one["attempt_id"] == attempt)))
        self.rejects(stream + " duplicate at " + point + (" revised use" if revised else " old use"), mutate, "C2-" + stream + ("-new-use" if revised else "-duplicate"))

    def test_duplicate_provider_is_rejected_independently(self):
        self.duplicate("provider", "after")
        self.duplicate("provider", "final")
        self.duplicate("provider", "final", revised=True)

    def test_duplicate_engine_is_rejected_independently(self):
        self.duplicate("engine", "after")
        self.duplicate("engine", "final")
        self.duplicate("engine", "final", revised=True)

    def test_missing_positive_baseline_is_rejected(self):
        for stream in ("provider", "engine"):
            self.rejects("missing " + stream + " baseline", lambda x, stream=stream: x["reopen"]["before"].__setitem__(stream, []), "C2-positive-baseline")

    def test_absent_actual_reopen_is_rejected(self):
        self.rejects("boundary deleted", lambda x: x.pop("reopen"), "C2-incomplete-evidence")
        self.rejects("no close or recompose performed", lambda x: x["reopen"].__setitem__("performed", False), "C2-reopen")

    def test_changed_verdict_checkpoint_or_attempt_is_rejected(self):
        self.rejects("changed verdict attribution", lambda x: x["verdict"].__setitem__("checkpoint_id", x["revised"]["checkpoint"]["checkpoint_id"]), "C1-verdict-attribution")
        self.rejects("changed reopened checkpoint", lambda x: x["reopen"]["durable_after"]["checkpoint"].__setitem__("checkpoint_id", "forged-checkpoint"), "C2-durable-attribution")
        self.rejects("changed provider attempt", lambda x: x["reopen"]["after"]["provider"][0].__setitem__("attempt_id", "forged-attempt"), "C2-provider-duplicate")
        def disguised_provider(x):
            one = copy.deepcopy(x["reopen"]["before"]["provider"][0])
            one["attempt_id"] = "forged-attempt"
            x["final_counters"]["provider"].append(one)
        self.rejects("duplicate use disguised as another attempt", disguised_provider, "C2-provider-attribution")

    def test_forged_context_receipt_is_rejected(self):
        self.rejects("forged restored context receipt", lambda x: x["revised"]["receipt"].__setitem__("use_id", x["initial"]["binding"]["use_id"]), "C1-context-receipt")
