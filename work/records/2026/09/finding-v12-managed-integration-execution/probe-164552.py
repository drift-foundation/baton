"""Independent partial candidate review; observations are not acceptance."""
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.integration.reconciliation import record_managed_result, attach_managed_phase, managed_result_of
from tests.integration import test_managed_execution as contracts
from tests.integration import test_managed_storage as storage


class Observations(storage.ManagedStorageCase):
    def create(self, store, name, revision=storage.REVISION):
        return record_managed_result(store, storage.submission(), orchestration_id=name, canonical_target_id=storage.fixtures.TARGET, target_revision=revision)

    def test_distinct_creation_occupies_another_results_attachment_id(self):
        store = self.coordinator()
        self.create(store, 'root/prepare')
        self.create(store, 'root', 'd' * 40)
        account = self.account(self.task(orchestration_id='root'))
        with self.assertRaises(ContractRefusal) as caught:
            attach_managed_phase(store, managed_result_id='root', task=account['task'], result=account['result'])
        self.assertEqual(caught.exception.code, 'operation-collision')
        self.assertIn('different kind or signature', str(caught.exception))
        print('DEFECT: independent root/prepare creation reserves the root preparation attachment operation ID')

    def test_distinct_creation_collides_in_reverse_order_too(self):
        store = self.coordinator()
        self.create(store, 'root')
        account = self.account(self.task(orchestration_id='root'))
        attach_managed_phase(store, managed_result_id='root', task=account['task'], result=account['result'])
        with self.assertRaises(ContractRefusal) as caught:
            self.create(store, 'root/prepare', 'd' * 40)
        self.assertEqual(caught.exception.code, 'operation-collision')
        print('DEFECT: root preparation attachment prevents independent root/prepare creation at a different snapshot')

    def test_noncanonical_creation_operation_is_accepted_on_read(self):
        store = self.coordinator()
        original = self.create(store, 'root')
        store._connection.execute('UPDATE operations SET operation_id = ? WHERE operation_id = ?', ('result.managed:foreign', 'result.managed:root'))
        store._connection.execute('UPDATE managed_integration_results SET operation_id = ? WHERE managed_result_id = ?', ('result.managed:foreign', 'root'))
        self.assertEqual(managed_result_of(store, 'root'), original)
        print('DEFECT: managed reader accepts a creation act renamed away from the canonical identity while retaining the original signature')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(contracts), loader.loadTestsFromModule(storage), tests])


if __name__ == '__main__':
    unittest.main(verbosity=2)
