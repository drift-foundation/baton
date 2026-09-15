"""Independent deterministic observations; permissive results are defects."""
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.integration.reconciliation import record_managed_result, attach_managed_phase, managed_result_of
from tests.integration import test_managed_execution as contracts
from tests.integration import test_managed_storage as storage


class Observations(storage.ManagedStorageCase):
    def create(self, store, name, revision=storage.REVISION):
        return record_managed_result(store, storage.submission(), orchestration_id=name, canonical_target_id=storage.fixtures.TARGET, target_revision=revision)

    def test_repeated_invalid_attachment_remains_refused(self):
        store = self.coordinator()
        self.record(store, phases=('prepare',))
        account = self.applying(parent={'execution_attempt_id': 'foreign-preparation', 'collected_digest': storage.COLLECTED})
        def attempt():
            return attach_managed_phase(store, managed_result_id=storage.ORCHESTRATION, task=account['task'], result=account['result'])
        with self.assertRaises(ContractRefusal):
            attempt()
        with self.assertRaises(ContractRefusal):
            attempt()
        self.assertEqual(set(managed_result_of(store, storage.ORCHESTRATION)['phases']), {'prepare'})
        print('CORRECTION: invalid attachment is non-durable and remains refused; no success replay defect')

    def test_repeated_creation_collision_retains_same_refusal(self):
        store = self.coordinator()
        self.create(store, 'winner')
        with self.assertRaises(ContractRefusal) as first:
            self.create(store, 'loser')
        with self.assertRaises(ContractRefusal) as repeated:
            self.create(store, 'loser')
        self.assertEqual(first.exception.code, 'operation-collision')
        self.assertEqual(str(first.exception), str(repeated.exception))
        print('CORRECTION: creation collision is non-durable and repeats the same refusal')

    def test_slash_identity_cannot_replay_its_creation(self):
        store = self.coordinator()
        self.assertEqual(self.create(store, 'root/child')['managed_result_id'], 'root/child')
        with self.assertRaises(ContractRefusal) as caught:
            self.create(store, 'root/child')
        self.assertIn('no managed integration result', str(caught.exception))
        print('DEFECT: accepted root/child creation replays by looking up root')

    def test_like_wildcard_matches_another_results_attachments(self):
        store = self.coordinator()
        self.create(store, 'rootA')
        account = self.account(self.task(orchestration_id='rootA'))
        attach_managed_phase(store, managed_result_id='rootA', task=account['task'], result=account['result'])
        with self.assertRaises(ContractRefusal) as caught:
            self.create(store, 'root_', 'd' * 40)
        self.assertIn('rootA/prepare', str(caught.exception))
        print('DEFECT: valid root_ creation mistakes rootA/prepare for its own missing phase')

    def test_case_insensitive_like_matches_a_distinct_identity(self):
        store = self.coordinator()
        self.create(store, 'ROOT')
        account = self.account(self.task(orchestration_id='ROOT'))
        attach_managed_phase(store, managed_result_id='ROOT', task=account['task'], result=account['result'])
        with self.assertRaises(ContractRefusal) as caught:
            self.create(store, 'root', 'd' * 40)
        self.assertIn('ROOT/prepare', str(caught.exception))
        print('DEFECT: valid root creation mistakes ROOT/prepare for its own missing phase')


def load_tests(loader, tests, pattern):
    return tests


if __name__ == '__main__':
    unittest.main(verbosity=2)
