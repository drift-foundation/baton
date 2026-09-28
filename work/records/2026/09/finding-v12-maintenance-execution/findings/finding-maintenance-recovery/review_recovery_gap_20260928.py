"""Probe real removal admission while recovery hold is the only exclusion."""
import unittest
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import tokens,workspaces
from tests.manager.test_maintenance import TheRECOVERYHOLDExemptsTheRepairItAdmittedAndNothingElse as Base
class Probe(Base):
    def test_removal_refuses_between_old_return_and_recovery_acquisition(self):
        honest=tokens.acquire
        reached=[]
        def paused(control,domain,**kw):
            if kw['operation']==self.recovery:
                reached.append(True)
                self.assertEqual(tokens.outstanding(control,domain),[])
                self.assertTrue(tokens.standing_recovery(control,domain))
                with self.assertRaises(ContractRefusal):
                    workspaces._admitted_removal(control,self.attempt_id,'competing removal during recovery hold')
            return honest(control,domain,**kw)
        with mock.patch.object(tokens,'acquire',side_effect=paused):
            self.revoked_and_held()
        self.assertEqual(reached,[True])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Probe('test_removal_refuses_between_old_return_and_recovery_acquisition')]))
    raise SystemExit(not result.wasSuccessful())
