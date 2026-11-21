import unittest
from tests.job_manager.test_creation import TheSelectedResultContractIsAdmittedBeforeAnyEffect, request

class NativeReplay(TheSelectedResultContractIsAdmittedBeforeAnyEffect):
    def test_native_replay_preserves_admitted_declarations(self):
        asked=request(template=self.HANDOFF)
        held=self.created(request=asked,derivation=self.stating(self.contract_declarations()))
        repeated=self.created(request=asked,derivation=self.stating(self.legacy_declarations()))
        self.assertEqual(repeated,held)
        self.assertEqual(len(self.rows()),1)
        self.assertEqual(len(self.authorization.created),1)
        self.assertEqual(len(self.binding.created),1)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([NativeReplay('test_native_replay_preserves_admitted_declarations')]))
    raise SystemExit(not result.wasSuccessful())
