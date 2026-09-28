import unittest
from unittest import mock
from tools import integration_bundle
from baton_v12.integration import reconciliation
from baton_v12.worker_manager import manifests
from baton_v12.contracts import ContractRefusal
from tests.tools.test_managed_apply import AnOrdinaryManagedIntegration
seen=set()
def wrap(original,label):
    def call(*args,**kwargs):
        answer=original(*args,**kwargs)
        if label not in seen:
            load=manifests.load_manifest
            def missing(store,key,kind):
                return None if kind=="inputManifest" else load(store,key,kind)
            with mock.patch.object(manifests,"load_manifest",missing):
                try: original(*args,**kwargs)
                except ContractRefusal as error:
                    assert "input manifest this manager does not retain" in error.message,error.message
                else: raise AssertionError("missing input accepted by "+label)
            seen.add(label)
        return answer
    return call
with mock.patch.object(integration_bundle,"retained_apply_report",wrap(integration_bundle.retained_apply_report,"success")), mock.patch.object(reconciliation,"managed_apply_failure_evidence",wrap(reconciliation.managed_apply_failure_evidence,"failure")):
    result=unittest.TextTestRunner().run(unittest.TestSuite([AnOrdinaryManagedIntegration("test_preparation_judgments_apply_and_target_settle"),AnOrdinaryManagedIntegration("test_a_failed_apply_is_collected_and_settles_without_a_target_effect")]))
print("MISSING_INPUT_REFUSALS",sorted(seen))
assert seen=={"success","failure"},seen
raise SystemExit(not result.wasSuccessful())
