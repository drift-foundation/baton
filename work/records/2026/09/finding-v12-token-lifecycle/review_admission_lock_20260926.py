"""Current admission: separate-connection exclusion and terminal refusal."""
import os
import sqlite3
import unittest
from tests.manager.token_support import TokenFixture
from baton_v12.worker_manager import tokens
from baton_v12.worker_manager.store import ControlStore
from baton_v12.contracts import ContractRefusal

class AdmissionLock(unittest.TestCase):
    def prepared(self):
        f=TokenFixture(self); t=f.held(); e=f.launched(t)
        tokens.admit_activation(f.store,t,container=e['container'])
        return f,t,e

    def test_other_connection_cannot_settle_during_admission(self):
        f,t,e=self.prepared()
        other=ControlStore.open(os.path.join(f.root,'control.sqlite3'),incarnation='second',clock=lambda:f.instant)
        self.addCleanup(other.close)
        other._connection.execute('PRAGMA busy_timeout=0')
        original=f.store.operation_record
        checked=[]
        def reading(operation):
            result=original(operation)
            if operation==tokens._activating_id(t['domain'],t['generation']) and not checked:
                checked.append(True)
                with self.assertRaisesRegex(sqlite3.OperationalError,'locked'):
                    tokens.settle_activation(other,t,container=e['container'],started=False)
            return result
        f.store.operation_record=reading
        result=tokens.admit_activation(f.store,t,container=e['container'])
        self.assertEqual(checked,[True]);self.assertEqual(result['generation'],1)
        self.assertTrue(tokens.token_of(other,f.domain,1)['activating'])
        tokens.settle_activation(other,t,container=e['container'],started=False)
        self.assertFalse(tokens.token_of(other,f.domain,1)['activating'])

    def test_terminal_replacement_before_admission_refuses(self):
        f,t,e=self.prepared()
        tokens.settle_activation(f.store,t,container=e['container'],started=False)
        tokens.returned(f.store,t,cessation=e)
        next_token=tokens.acquire(f.store,f.domain,operation='next',execution='next')
        self.assertEqual(next_token['generation'],2)
        with self.assertRaises(ContractRefusal):
            tokens.admit_activation(f.store,t,container=e['container'])

if __name__=='__main__': unittest.main()
