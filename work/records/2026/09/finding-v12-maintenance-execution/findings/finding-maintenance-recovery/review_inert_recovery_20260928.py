"""No engine: a bound but never activated token cannot prove executed recovery."""
import unittest
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal
from tests.manager.test_maintenance import TheRECOVERYHOLDGatesOrdinaryUseAcrossTheTransition as Base
class Probe(Base):
    def test_inert_container_does_not_prove_success(self):
        old, ceased, held=self.holding()
        tokens.returned(self.store,old,cessation=ceased,reclaiming=True)
        fresh=tokens.acquire(self.store,self.domain,operation=self.recovery,
                             execution='inert-recovery',recovering=held)
        tokens.journal_launch(self.store,fresh,self.recovery)
        tokens.bind_container(self.store,fresh,'container-inert',launch=self.recovery)
        self.assertIsNone(tokens.token_of(self.store,self.domain,fresh['generation'])['activation_started'])
        with self.assertRaises(ContractRefusal):
            tokens.record_recovery_result(self.store,held,fresh,outcome='succeeded')
            end={'domain':self.domain,'generation':fresh['generation'],
                 'launch':self.recovery,'container':'container-inert','stopped':True,'helpers':[]}
            tokens.returned(self.store,fresh,cessation=end)
            tokens.clear_recovery(self.store,held,result={'operation':self.recovery,'outcome':'succeeded'},
                                  cessation=end,why='inert create was not a repair')
        self.assertTrue(tokens.standing_recovery(self.store,self.domain))
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Probe('test_inert_container_does_not_prove_success')]))
    raise SystemExit(not result.wasSuccessful())
