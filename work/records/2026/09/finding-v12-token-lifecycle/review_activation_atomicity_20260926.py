"""Current admission contract: independent store races and owner checks."""
import unittest
from tests.manager.token_support import TokenFixture
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal

class AdmissionAtomicity(unittest.TestCase):
    def prepared(self):
        f = TokenFixture(self)
        t = f.held()
        e = f.launched(t)
        return f,t,e

    def test_return_rechecks_activation_inside_transaction(self):
        f,t,e = self.prepared()
        original = f.store.transact
        raced = []
        def interleave(operation, kind, signature, act):
            if kind == tokens.RETURNED_KIND and not raced:
                raced.append(True)
                tokens.admit_activation(f.store,t,container=e['container'])
            return original(operation,kind,signature,act)
        f.store.transact = interleave
        with self.assertRaises(ContractRefusal):
            tokens.returned(f.store,t,cessation=e)
        self.assertEqual(raced,[True])

    def test_wrong_owner_cannot_settle_activation(self):
        f,t,e = self.prepared()
        tokens.admit_activation(f.store,t,container=e['container'])
        with self.assertRaises(ContractRefusal):
            tokens.settle_activation(f.store,dict(t,owner='wrong-owner'),
                                     container=e['container'],started=False)

if __name__ == '__main__':
    unittest.main()
