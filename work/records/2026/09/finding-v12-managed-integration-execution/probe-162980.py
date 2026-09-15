"""Independent review of new storage API; permissive outcomes are defects."""
import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration.reconciliation import managed_result_of
from tests.integration import test_managed_execution as contracts
from tests.integration import test_managed_storage as storage


class Observations(storage.ManagedStorageCase):
    def test_valid_task_edit_is_not_bound_to_journal_on_read_or_replay(self):
        store = self.coordinator()
        original = self.record(store)
        task = original["phases"]["prepare"]["task"]
        task["harness_digest"] = "sha256:" + "f" * 64
        store._connection.execute("UPDATE managed_integration_phases SET task = ? WHERE managed_result_id = ? AND phase = 'prepare'", (json.dumps(task), storage.ORCHESTRATION))
        self.assertEqual(managed_result_of(store, storage.ORCHESTRATION)["phases"]["prepare"]["task"], task)
        self.assertEqual(self.record(store)["phases"]["prepare"]["task"], task)
        print("DEFECT: semantically valid stored harness substitution survives read and exact original replay")

    def test_removed_phase_accounts_are_answered_without_journal_proof(self):
        store = self.coordinator()
        self.record(store)
        store._connection.execute("DELETE FROM managed_integration_phases WHERE managed_result_id = ?", (storage.ORCHESTRATION,))
        self.assertEqual(managed_result_of(store, storage.ORCHESTRATION)["phases"], {})
        self.assertEqual(self.record(store)["phases"], {})
        print("DEFECT: all phase accounts removed; read and replay return an empty result")

    def test_unjournalled_state_transition_is_answered(self):
        store = self.coordinator()
        self.record(store)
        store._connection.execute("UPDATE managed_integration_results SET state = 'held', reason = 'invented hold' WHERE managed_result_id = ?", (storage.ORCHESTRATION,))
        self.assertEqual(managed_result_of(store, storage.ORCHESTRATION)["state"], "held")
        print("DEFECT: unjournalled preparing-to-held state change is returned")

    def test_apply_parent_can_name_foreign_preparation(self):
        store = self.coordinator()
        phases = self.phases(apply=self.applying(parent={"execution_attempt_id": "foreign-preparation", "collected_digest": "sha256:" + "f" * 64}))
        answer = self.record(store, phases=phases)
        self.assertEqual(answer["phases"]["apply"]["task"]["parent"]["execution_attempt_id"], "foreign-preparation")
        print("DEFECT: apply names another preparation and content while recorded beside this preparation")

    def test_prepare_then_apply_cannot_extend_the_record(self):
        store = self.coordinator()
        self.record(store, phases={"prepare": self.account()})
        with self.assertRaises(ContractRefusal) as caught:
            self.record(store)
        self.assertEqual(caught.exception.code, "operation-collision")
        print("OBSERVED: prepare-only creation cannot later retain apply through the current API")


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(contracts), loader.loadTestsFromModule(storage), tests])


if __name__ == "__main__":
    unittest.main(verbosity=2)
