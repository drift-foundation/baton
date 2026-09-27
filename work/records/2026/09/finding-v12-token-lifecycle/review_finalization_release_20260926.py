"""A refused finalization must not release its governed resource."""
import importlib.util
from pathlib import Path
import unittest
from baton_v12.worker_manager import attempts,tokens
from baton_v12.contracts import ContractRefusal
spec=importlib.util.spec_from_file_location('caller_fixture',Path(__file__).with_name('review_governed_caller_20260926.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FinalizationRelease(unittest.TestCase):
    def test_nonterminal_finalization_refusal_preserves_token(self):
        helper=m.Caller();f=helper.fixture();self.addCleanup(helper.doCleanups)
        govern=tokens.workspace_governance()
        attempts.request_runtime_start(f.store,m.BoundAdapter(),attempt_id=m.ATTEMPT,govern=govern)
        attempts.observe(f.store,attempt_id=m.ATTEMPT,axis='execution_runtime',value='quiescent')
        with self.assertRaises(ContractRefusal):
            attempts.finalize_quiescent_assignment(f.store,f.port,attempt_id=m.ATTEMPT,reason='probe',govern=govern)
        self.assertEqual(len(tokens.outstanding(f.store,'workspace:66:4242')),1,
                         'ineligible finalization released token before its eligibility decision')
if __name__=='__main__':unittest.main()
