"""Independent deterministic storage research; permissive cases record defects."""
import copy
import sqlite3
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import managed_execution as managed
from baton_v12.integration.reconciliation import record_managed_result, managed_result_of
from baton_v12.integration.store import IntegrationStore, upgrade_store
from baton_v12.job_manager import execution_limits
from tests.integration import test_managed_execution as contracts
from tests.integration import test_managed_storage as storage


class Observations(storage.ManagedStorageCase):
    def test_prior_forged_defaults_now_refuse(self):
        for generation in (0, 1):
            for changes in ({"seconds": 7200}, {"default_seconds": 7200},
                            {"seconds": 7200, "default_seconds": 7200}):
                limits = execution_limits.resolved({}, generation)
                limits["boundaries"]["provider_turn"].update(changes)
                with self.assertRaises(ContractRefusal):
                    self.task(execution_limits=limits)

    def test_numeric_equality_accepts_boolean_but_float_is_refused(self):
        limits = execution_limits.resolved({"provider_turn_seconds": 1})
        limits["boundaries"]["provider_turn"]["seconds"] = True
        self.assertIs(self.task(execution_limits=limits)["execution_limits"]["boundaries"]["provider_turn"]["seconds"], True)
        print("DEFECT: boolean effective seconds survive owner equality")
        limits = execution_limits.resolved({})
        limits["boundaries"]["provider_turn"]["default_seconds"] = 3600.0
        with self.assertRaises(ContractRefusal):
            self.task(execution_limits=limits)

    def test_changed_immutable_task_replays_as_original(self):
        store = self.coordinator()
        task = self.task()
        result = self.result(task)
        first = record_managed_result(store, task, result, source_proposal_id=storage.PROPOSAL, target_revision=storage.REVISION)
        for member in ("harness_digest", "task_digest", "input_digest"):
            changed = copy.deepcopy(task)
            changed[member] = "sha256:" + "f" * 64
            replay = record_managed_result(store, changed, result, source_proposal_id=storage.PROPOSAL, target_revision=storage.REVISION)
            self.assertEqual(replay, first)
            self.assertNotEqual(replay["task"][member], changed[member])
            print("DEFECT: changed task", member, "replays without collision")

    def test_reader_accepts_double_representation(self):
        store = self.coordinator()
        record_managed_result(store, self.task(), self.result(), source_proposal_id=storage.PROPOSAL, target_revision=storage.REVISION)
        storage.OneResultPerTargetSnapshotInEitherTable.legacy(self, store)
        self.assertEqual(managed_result_of(store, storage.PREPARE)["target_revision"], storage.REVISION)
        print("DEFECT: managed reader accepts simultaneous legacy representation")

    def test_same_snapshot_second_phase_cannot_be_recorded(self):
        store = self.coordinator()
        record_managed_result(store, self.task(), self.result(), source_proposal_id=storage.PROPOSAL, target_revision=storage.REVISION)
        applying = self.task(phase="apply", execution_attempt_id="apply-attempt-1", parent={"execution_attempt_id": storage.PREPARE, "collected_digest": "sha256:" + "c" * 64})
        with self.assertRaises(ContractRefusal) as caught:
            record_managed_result(store, applying, self.result(applying, collected=None), source_proposal_id=storage.PROPOSAL, target_revision=storage.REVISION)
        self.assertEqual(caught.exception.code, "operation-collision")
        print("OBSERVED: same proposal/target snapshot cannot retain both phase accounts")

    def test_upgrade_does_not_recheck_owned_shape_under_lock(self):
        self.demoted(self.coordinator())
        original = IntegrationStore._adopt
        def interleave(connection, path, accept):
            found = original(connection, path, accept)
            with sqlite3.connect(path, isolation_level=None) as other:
                other.execute("DROP INDEX results_by_submission")
            return found
        with patch.object(IntegrationStore, "_adopt", side_effect=interleave):
            answer = upgrade_store(self.path, incarnation="review", clock=self.clock)
        self.assertTrue(answer["upgraded"])
        self.assertEqual(self.recorded_version(), "6")
        with self.assertRaises(ContractRefusal) as caught:
            self.store()
        self.assertIn("results_by_submission", str(caught.exception))
        print("DEFECT: upgrade commits schema6 after owned shape changes before lock")


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(contracts), loader.loadTestsFromModule(storage), tests])


if __name__ == "__main__":
    unittest.main(verbosity=2)
