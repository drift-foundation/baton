"""Independent deterministic probes: no engine, disposable token stores only."""
import unittest
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal
from tests.manager.test_maintenance import TheRECOVERYHOLDGatesOrdinaryUseAcrossTheTransition as Base

class Probe(Base):
    def test_failed_result_must_keep_hold(self):
        held, fresh, ceased = self.recovered()
        tokens.returned(self.store, fresh, cessation=ceased)
        with self.assertRaises(ContractRefusal):
            tokens.clear_recovery(self.store, held,
                result={'operation':self.recovery,'outcome':'failed'},
                cessation=ceased, why='failed repair cannot release ordinary use')

    def test_old_generation_cannot_be_its_own_recovery(self):
        old, ceased = self.revoked()
        with self.assertRaises(ContractRefusal):
            held = tokens.hold_for_recovery(self.store,self.domain,
                generation=old['generation'], recovery=old['operation'],what='old operation reuse')
            tokens.returned(self.store,old,cessation=ceased,reclaiming=True)
            tokens.clear_recovery(self.store,held,
                result={'operation':old['operation'],'outcome':'normalized'},
                cessation=ceased,why='no recovery generation was executed')

    def test_equal_facts_in_another_store_do_not_transfer_capability(self):
        old, ceased, held = self.holding()
        other = Base()
        other.setUp()
        self.addCleanup(other.doCleanups)
        other_old, other_ceased, other_held = other.holding()
        tokens.returned(other.store,other_old,cessation=other_ceased,reclaiming=True)
        with self.assertRaises(ContractRefusal):
            tokens.acquire(other.store,other.domain,operation=other.recovery,
                           execution='maintenance-foreign',recovering=held)

if __name__ == '__main__':
    suite=unittest.TestSuite(Probe(name) for name in (
        'test_failed_result_must_keep_hold',
        'test_old_generation_cannot_be_its_own_recovery',
        'test_equal_facts_in_another_store_do_not_transfer_capability'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
