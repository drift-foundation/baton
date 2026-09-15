"""Independent real public-writer interleaving at the transaction boundary."""
import os
import threading
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import IntegrationStore
from baton_v12.integration.reconciliation import record_managed_result, managed_result_of, result_of
from tests.integration import test_managed_execution as contracts
from tests.integration import test_managed_storage as storage
from tests.integration.test_reconciliation import ResultCase, TARGET, REFERENCE, NOW


class PublicWriterOverlap(ResultCase):
    def overlap(self, first):
        path = os.path.join(self.root, 'coordinator.sqlite3')
        revision = self.profile.revision(self.target, REFERENCE)
        paused, attempted = threading.Event(), threading.Event()
        answers = {}
        trace = []

        def instrument(handle, side):
            if side == first:
                original = handle._now
                once = []
                def hold():
                    if not once and handle._pending is not None:
                        once.append(True)
                        self.assertTrue(handle._connection.in_transaction)
                        trace.append(side + ':inside-write')
                        paused.set()
                        self.assertTrue(attempted.wait(5), 'other public writer never reached BEGIN IMMEDIATE')
                    return original()
                handle._now = hold
            else:
                def observe(sql):
                    if sql.strip().upper() == 'BEGIN IMMEDIATE':
                        trace.append(side + ':begin-write')
                        attempted.set()
                handle._connection.set_trace_callback(observe)

        def managed_thread():
            handle = None
            try:
                handle = IntegrationStore.open(path, incarnation='independent-managed', clock=lambda: NOW)
                instrument(handle, 'managed')
                if first != 'managed':
                    self.assertTrue(paused.wait(5), 'legacy did not enter its real transaction')
                def create():
                    return record_managed_result(handle, storage.submission(source_proposal_id='proposal-b1'), orchestration_id='independent-root', canonical_target_id=TARGET, target_revision=revision)
                answers['managed'] = create()
                self.assertEqual(create(), answers['managed'])
                self.assertEqual(managed_result_of(handle, 'independent-root'), answers['managed'])
            except BaseException as error:
                answers['managed'] = error
            finally:
                if handle is not None:
                    handle.close()

        instrument(self.store, 'legacy')
        thread = threading.Thread(target=managed_thread)
        thread.start()
        try:
            if first == 'managed':
                self.assertTrue(paused.wait(5), 'managed did not enter its real transaction')
            try:
                answers['legacy'] = self.prepare()
            except ContractRefusal as error:
                answers['legacy'] = error
        finally:
            attempted.set()
            thread.join(10)
        self.assertFalse(thread.is_alive())
        other = 'legacy' if first == 'managed' else 'managed'
        self.assertEqual(trace[:2], [first + ':inside-write', other + ':begin-write'])
        self.assertIsInstance(answers[first], dict, str(answers[first]))
        self.assertIsInstance(answers[other], ContractRefusal, str(answers[other]))
        self.assertIn('one submission has one result per target snapshot', str(answers[other]))
        if first == 'legacy':
            self.assertEqual(self.prepare(), answers['legacy'])
            self.assertEqual(result_of(self.store, answers['legacy']['result_id']), answers['legacy'])
        counts = [self.store._connection.execute('SELECT count(*) FROM ' + table).fetchone()[0] for table in ('integration_results', 'managed_integration_results')]
        self.assertEqual(counts, [1, 0] if first == 'legacy' else [0, 1])
        print('PUBLIC WRITERS:', first, 'holds its transaction before', other, 'reaches BEGIN; winner read/replay valid; counts', counts)

    def test_legacy_holds_before_managed_write_attempt(self):
        self.overlap('legacy')

    def test_managed_holds_before_legacy_write_attempt(self):
        self.overlap('managed')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(contracts), loader.loadTestsFromModule(storage), loader.loadTestsFromTestCase(PublicWriterOverlap)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
