"""C1 proof: deterministic provider children and a simulated OCI engine."""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

from tests.tools import correction_restart_trace as proof


def artifact():
    world = proof.World()
    try:
        world.setUp()
        return world.run_scenario()
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
