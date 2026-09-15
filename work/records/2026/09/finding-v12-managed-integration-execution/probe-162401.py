"""Deterministic owner-surface research; permissive admission is defect evidence."""
import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import integration_capacity as capacity
from baton_v12.worker_manager.offers import claimed_offers_for
from tests.job_manager.test_managed_integration_capacity import CapacityCase


class OwnerSurfaces(CapacityCase):
    def test_existing_readers_expose_offer_and_recorded_attempt_digests(self):
        control = self.claimed("prepare-attempt-1", "prepare-offer-1")
        with control.snapshot():
            [offer] = claimed_offers_for(control, "prepare-attempt-1")
            record = control.operation_record("attempt.record:prepare-attempt-1")
            assignment = self.claim_of("prepare-attempt-1")
        self.assertEqual(record["kind"], "attempt.record")
        self.assertEqual(record["state"], "committed")
        signature = json.loads(record["signature"])
        self.assertEqual(signature["kind"], "attempt.record")
        operands = signature["operands"]
        self.assertEqual(operands["attempt_id"], "prepare-attempt-1")
        self.assertEqual(offer["offer_id"], "prepare-offer-1")
        self.assertEqual(offer["work_id"], assignment["work_ref"]["work_id"])
        self.assertEqual(offer["claim_generation"], assignment["generation"])
        for name in ("input_digest", "profile_digest", "policy_digest"):
            self.assertEqual(offer[name], operands[name])
        print("Existing public snapshot/claimed_offers_for/operation_record expose offer and attempt-record bindings")

    def test_foreign_root_authority_refuses(self):
        store, _stage, allocation = self.reserved()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.register_integration_capacity(
                store, orchestration_id=self.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                authority_uuid="foreign-authority", plan=self.plan())
        self.assertIn("bound to Authority", str(caught.exception))

    def test_current_admission_accepts_a_plan_with_foreign_offer_and_digests(self):
        store, _stage, allocation = self.reserved()
        control = self.claimed("prepare-attempt-1", "prepare-offer-1")
        plan = self.plan(prepare={"execution_offer_id": "unissued-offer",
                                  "profile_digest": "sha256:" + "f" * 64,
                                  "input_digest": "sha256:" + "e" * 64})
        capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=store.authority_uuid, plan=plan)
        answer = capacity.admit_integration_execution(
            store, control, orchestration_id=self.ORCHESTRATION, phase="prepare",
            execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))
        member = next(one for one in answer["members"] if one["phase"] == "prepare")
        self.assertEqual(member["state"], "admitted")
        print("DEFECT OBSERVED: unissued planned offer and mismatched profile/input were admitted")


if __name__ == "__main__":
    unittest.main(verbosity=2)
