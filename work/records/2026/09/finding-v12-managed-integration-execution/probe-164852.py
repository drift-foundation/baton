"""Independent rejected-behavior observations; only disposable fixture stores."""
import unittest
from unittest import mock
from tests.tools import test_managed_integration as supplied
from tests.integration import test_managed_storage as storage
from baton_v12.contracts import ContractRefusal
from baton_v12.integration.reconciliation import publication_of
from baton_v12.integration.queue import entries_of
import integration_placement as placement

class Observations(supplied.PlacementCase):
    def ready(self):
        self.custody()
        self.stopped()

    def intent_only(self):
        with mock.patch.object(self.profile,'advance',side_effect=RuntimeError('interrupted before CAS')):
            with self.assertRaises(RuntimeError):
                self.publish()
        self.assertEqual(self.standing(),self.base)
        row=publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')
        self.assertEqual(row['state'],'intended')
        return row

    def test_foreign_same_revision_after_intent_is_adopted(self):
        self.ready()
        self.intent_only()
        self.profile.advance(self.repository,reference=self.reference,
                             imported=self.candidate,reviewed=self.base)
        self.assertEqual(self.publish()['outcome'],'resumed')

    def test_settlement_commit_before_publication_marker_cannot_resume(self):
        self.ready()
        real=placement.record_publication_effect
        def interrupted(store,publication_id,state):
            if state=='settled':raise RuntimeError('interrupted after queue settlement')
            return real(store,publication_id,state)
        with mock.patch.object(placement,'record_publication_effect',side_effect=interrupted):
            with self.assertRaises(RuntimeError):self.publish()
        self.assertEqual(entries_of(self.coordinator,supplied.coordinator_fixtures.TARGET)[0]['state'],'integrated')
        self.assertEqual(publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'swapped')
        with self.assertRaises(ContractRefusal):self.publish()

    def test_state_only_forgery_is_accepted_as_completed_replay(self):
        self.ready()
        row=self.intent_only()
        self.coordinator._connection.execute('UPDATE managed_publications SET state = ? WHERE publication_id = ?',('settled',row['publication_id']))
        self.assertEqual(publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'settled')
        answer=self.publish()
        self.assertEqual(answer['outcome'],'replayed')
        self.assertEqual(self.standing(),self.base)
        self.assertEqual(entries_of(self.coordinator,supplied.coordinator_fixtures.TARGET)[0]['state'],'leased')

    def test_deleted_intent_journal_is_not_detected_by_reader(self):
        self.ready()
        row=self.intent_only()
        self.coordinator._connection.execute('DELETE FROM operations WHERE operation_id = ?',(row['operation_id'],))
        self.assertEqual(publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['publication_id'],row['publication_id'])

    def test_recorded_swap_is_repeated_after_foreign_move_back_to_base(self):
        self.ready()
        with mock.patch.object(placement,'settle_integrated',side_effect=RuntimeError('interrupted before settlement')):
            with self.assertRaises(RuntimeError):self.publish()
        self.assertEqual(publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'swapped')
        self.profile.advance(self.repository,reference=self.reference,imported=self.base,reviewed=self.candidate)
        real=self.profile.advance
        with mock.patch.object(self.profile,'advance',wraps=real) as spy:
            self.assertEqual(self.publish()['outcome'],'published')
            self.assertEqual(spy.call_count,1)
        self.assertEqual(self.standing(),self.candidate)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(storage))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
