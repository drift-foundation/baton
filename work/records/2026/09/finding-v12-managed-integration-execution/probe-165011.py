"""Independent remaining common apply-path observations, disposable fixtures."""
import unittest
from unittest import mock
from tests.tools import test_managed_integration as supplied
from baton_v12.integration import refuse_entry
from baton_v12.integration.queue import entries_of
from baton_v12.contracts import ContractRefusal
class Observations(supplied.PlacementCase):
    def ready(self):self.custody();self.stopped()
    def test_grant_released_during_final_target_read_still_applies(self):
        self.ready()
        real=self.profile.revision;reads=[]
        def revision(*args,**kwargs):
            result=real(*args,**kwargs);reads.append(result)
            if len(reads)==2:
                refuse_entry(self.coordinator,lease_id='lease-1',canonical_target_id=supplied.coordinator_fixtures.TARGET,
                             entry_id='entry-1',fence=self.fence,settlement={'reason':'policy','detail':{'why':'released during final target read'}})
            return result
        with mock.patch.object(self.profile,'revision',side_effect=revision):
            with self.assertRaises(ContractRefusal):self.publish()
        self.assertEqual(self.standing(),self.candidate)
        self.assertEqual(len(self.target_owner.asked),1)
    def test_fresh_applied_receipt_settles_after_target_drift_before_reply(self):
        self.ready()
        real=self.target_owner.apply
        def apply(request):
            answer=real(request)
            self.profile.advance(self.repository,reference=self.reference,imported=self.base,reviewed=self.candidate)
            return answer
        with mock.patch.object(self.target_owner,'apply',side_effect=apply):
            answer=self.publish()
        self.assertEqual(answer['outcome'],'published')
        self.assertEqual(self.standing(),self.base)
        self.assertEqual(entries_of(self.coordinator,supplied.coordinator_fixtures.TARGET)[0]['state'],'integrated')
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
