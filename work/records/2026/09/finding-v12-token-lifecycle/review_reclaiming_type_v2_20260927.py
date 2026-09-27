"""Malformed reclaim selector must not bypass holder expiry (disposable store)."""
import unittest
from test_token_lifecycle import TokenLifecycle
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal

class ReclaimingType(TokenLifecycle):
    def test_string_does_not_enable_expired_return(self):
        token = self.held(seconds=1)
        evidence = self.launched(token)
        self.instant = '2026-09-26T15:00:00.000Z'
        with self.assertRaises(ContractRefusal):
            tokens.returned(self.store, token, cessation=evidence, reclaiming='false')
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)

    def test_integer_does_not_enable_expired_release(self):
        token = self.held(seconds=1)
        evidence = self.launched(token)
        self.instant = '2026-09-26T15:00:00.000Z'
        with self.assertRaises(ContractRefusal):
            tokens.release(self.store, 'line-7/workspace', 'workspace',
                           execution='attempt-a', operation='runtime.start:a',
                           cessation={k: evidence[k] for k in ('container', 'stopped', 'helpers')}, reclaiming=1)
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)

if __name__ == '__main__':
    suite = unittest.TestSuite(ReclaimingType(n) for n in ReclaimingType.__dict__ if n.startswith('test_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
