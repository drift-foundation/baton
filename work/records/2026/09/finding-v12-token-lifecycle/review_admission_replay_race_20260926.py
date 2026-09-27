"""Replay after terminal facts appear between preliminary read and transaction."""
import unittest
from tests.manager.token_support import TokenFixture
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal

class ReplayRace(unittest.TestCase):
    def test_replay_must_not_answer_admission_after_interleaved_return(self):
        f = TokenFixture(self)
        token = f.held()
        evidence = f.launched(token)
        tokens.admit_activation(f.store, token, container=evidence['container'])
        original = f.store.transact
        replacements = []
        def interleave(operation, kind, signature, act):
            if kind == tokens.ACTIVATING_KIND and not replacements:
                tokens.settle_activation(f.store, token, container=evidence['container'], started=False)
                tokens.returned(f.store, token, cessation=evidence)
                replacements.append(tokens.acquire(f.store,f.domain,operation='next',execution='next'))
            return original(operation,kind,signature,act)
        f.store.transact = interleave
        with self.assertRaises(ContractRefusal):
            tokens.admit_activation(f.store, token, container=evidence['container'])
        self.assertEqual(replacements[0]['generation'],2)

if __name__ == '__main__':
    unittest.main()
