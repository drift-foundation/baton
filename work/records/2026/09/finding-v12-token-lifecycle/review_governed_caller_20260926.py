"""Actual governed request_runtime_start with existing deterministic fixtures."""
import unittest
from tests.manager.test_attempts import TheRuntimeIsStartedOnceAndReconciled, Adapter, ATTEMPT
from baton_v12.worker_manager import attempts,tokens
from baton_v12.contracts import ContractRefusal

class BoundAdapter(Adapter):
    def start(self, request, *, bind=None):
        admitted=bind('runtime-1')()
        assert admitted['container']=='runtime-1'
        return super().start(request)

class Caller(unittest.TestCase):
    def fixture(self):
        f=TheRuntimeIsStartedOnceAndReconciled();f.setUp();self.addCleanup(f.doCleanups)
        f.activated()
        attempts.pin_boundary_identity(f.store,attempt_id=ATTEMPT,source=(66,111),workspace=(66,4242))
        return f
    def test_real_caller_can_be_exercised_without_engine(self):
        f=self.fixture()
        answer=attempts.request_runtime_start(f.store,BoundAdapter(),attempt_id=ATTEMPT,govern=tokens.workspace_governance())
        self.assertEqual(answer['decision'],'attached')
        self.assertTrue(tokens.token_of(f.store,'workspace:66:4242',1)['activation_started'])
    def test_reservation_refusal_must_not_leave_unsubmitted_start_pending(self):
        f=self.fixture()
        tokens.acquire(f.store,'workspace:66:4242',operation='other',execution='other')
        adapter=BoundAdapter()
        with self.assertRaises(ContractRefusal):
            attempts.request_runtime_start(f.store,adapter,attempt_id=ATTEMPT,govern=tokens.workspace_governance())
        self.assertEqual(adapter.started,[])
        self.assertNotEqual(f.row()['execution_runtime'],'start-requested',
                            'reservation refused before adapter crossing, but start remains pending')

if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Caller))
    raise SystemExit(not result.wasSuccessful())
