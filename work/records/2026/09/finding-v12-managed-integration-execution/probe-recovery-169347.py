"""Independent helper-boundary research; no deployment/engine acceptance."""
import os
import unittest
from tests.tools.test_managed_preparation import TheOperandsAreResolvedFromOwnerAnswers
from baton_v12.integration import managed_execution
from baton_v12.contracts import ContractRefusal

class RecoveryResearch(unittest.TestCase):
    def setUp(self):
        self.world = TheOperandsAreResolvedFromOwnerAnswers("run")
        self.addCleanup(self.world.doCleanups)
        self.world.setUp()

    def test_recovered_request_restores_target_and_derived_digests(self):
        w = self.world
        held = w.resolved()
        place = os.path.join(w.home, "published-" + str(w.published))
        intent = {"request_digest": held["task_digest"]}
        changed = dict(held, published_root=place, task_digest="sha256:" + "f" * 64,
                       input_digest="sha256:" + "e" * 64)
        changed["request"] = dict(held["request"], source=dict(held["request"]["source"], target_revision="f" * 40))
        worker = w.worker.ManagedPreparation.__new__(w.worker.ManagedPreparation)
        recovered = worker._recovered(intent, changed)
        self.assertEqual(recovered["request"], held["request"])
        self.assertEqual(recovered["task_digest"], held["task_digest"])
        self.assertEqual(recovered["input_digest"], held["input_digest"])

    def test_missing_root_operand_skips_recovery_observed(self):
        w = self.world
        held = w.resolved()
        self.assertNotIn("published_root", held)
        worker = w.worker.ManagedPreparation.__new__(w.worker.ManagedPreparation)
        self.assertIs(worker._recovered({"request_digest": held["task_digest"]}, held), held)
        print("OBSERVED: resolver supplies no published_root; recovery silently passes supplied operands through without it.")

    def test_moved_target_fails_resolver_before_recovery_observed(self):
        w = self.world
        published = w.publish(w.accepted(), w.target)
        with self.assertRaises(ContractRefusal) as caught:
            w.resolved(target=w.base, published=published)
        self.assertIn("one document", str(caught.exception))
        print("OBSERVED: fresh-target resolver plus retained publication refuses before ManagedPreparation recovery. Composition must recover before resolving first-sweep operands.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
