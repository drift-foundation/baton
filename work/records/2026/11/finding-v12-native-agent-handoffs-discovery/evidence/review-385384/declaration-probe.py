import unittest
from tests.tools.test_pool import ComposingCase
from baton_v12.job_manager import role_contract

class DeclarationProbe(ComposingCase):
    def test_native_output_descriptors_match_the_selected_contract(self):
        answer=self.composing(template_version=role_contract.HANDOFF_TEMPLATE)
        actual={x['name']:x for x in answer['worker']['deployment']['input_manifest']['outputs']}
        expected={x['name']:x for x in role_contract.contract_for(role_contract.HANDOFF_TEMPLATE)['outputs']}
        self.assertEqual(actual,expected)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([DeclarationProbe('test_native_output_descriptors_match_the_selected_contract')]))
    raise SystemExit(not result.wasSuccessful())
