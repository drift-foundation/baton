"""Independent defect observations, not accepted behavior. Disposable fixtures only."""
import unittest
from tests.tools import test_managed_integration as supplied
from baton_v12.integration import enqueue, grant_lease, refuse_entry
from baton_v12.integration.queue import entries_of

class Observations(supplied.PlacementCase):
    def ready(self):
        self.custody()
        self.stopped()

    def test_foreign_same_revision_is_adopted_as_own_swap(self):
        self.ready()
        self.profile.advance(self.repository, reference=self.reference,
                             imported=self.candidate, reviewed=self.base)
        answer = self.publish()
        self.assertEqual(answer['outcome'], 'resumed')
        self.assertEqual(self.standing(), self.candidate)

    def test_completed_retry_accepts_changed_grant(self):
        self.ready()
        self.publish()
        answer = self.publish(lease_id='unrelated-lease', fence=self.fence+99)
        self.assertEqual(answer['outcome'], 'replayed')
        self.assertEqual(answer['lease_id'], 'unrelated-lease')

    def test_completed_retry_returns_foreign_current_revision(self):
        self.ready()
        first = self.publish()
        foreign = self.write_revision('VALUE = 77\n', 'later unrelated movement')
        answer = self.publish()
        self.assertEqual(answer['outcome'], 'replayed')
        self.assertEqual(answer['imported_revision'], foreign)
        self.assertNotEqual(answer['imported_revision'], first['imported_revision'])

    def test_authorized_content_settles_unrelated_entry(self):
        self.ready()
        target = supplied.coordinator_fixtures.TARGET
        refuse_entry(self.coordinator, lease_id='lease-1', canonical_target_id=target,
                     entry_id='entry-1', fence=self.fence,
                     settlement={'reason':'policy','detail':{'why':'release for other entry'}})
        enqueue(self.coordinator, canonical_target_id=target, entry_id='unrelated-entry',
                eligibility=supplied.coordinator_fixtures.eligibility(
                    checkpoint_id='unrelated-checkpoint', work_id='0000000a-W99',
                    proposal_id='unrelated-proposal', result_id='unrelated-result'))
        lease=grant_lease(self.coordinator, canonical_target_id=target,
                          entry_id='unrelated-entry', lease_id='other-lease',
                          integrator_participant='baton.integrator', attempt_id='other-attempt')
        answer=self.publish(entry_id='unrelated-entry', lease_id='other-lease',
                            fence=lease['lease']['fence'])
        self.assertEqual(answer['outcome'], 'published')
        entry=next(e for e in entries_of(self.coordinator,target) if e['entry_id']=='unrelated-entry')
        self.assertEqual(entry['state'],'integrated')
        self.assertEqual(entry['proposal_id'],'unrelated-proposal')
        self.assertEqual(answer['derived_proposal_id'],'derived-proposal-1')
        self.assertTrue(all('entry_id' not in q for q in self.authorization.asked))

if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
