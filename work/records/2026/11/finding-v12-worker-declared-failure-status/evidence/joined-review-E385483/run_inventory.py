"""Select permitted inventory cases without changing candidate bytes or assertions."""
import unittest,json
from unittest import mock
from tests.manager import test_boundary_inventory as module
excluded=[]
original=module.EveryProbeProvesItArrived.all_probes

def allowed(self):
    catalog=original(self)
    removed=[key for key in catalog if key[0][1]=='review_cycles.py:_cleaned_review' and key[1]=='a historical review cleanup']
    for key in removed:
        if key not in excluded:excluded.append(key)
    return {key:value for key,value in catalog.items() if key not in removed}

class SelectedCatalog(unittest.TestSuite):
    def run(self,result,debug=False):
        with mock.patch.object(module.EveryProbeProvesItArrived,'all_probes',allowed):
            return super().run(result,debug)

def flatten(suite):
    for test in suite:
        if isinstance(test,unittest.TestSuite):yield from flatten(test)
        else:yield test
suite=unittest.TestSuite()
for test in flatten(unittest.defaultTestLoader.loadTestsFromModule(module)):
    if test.id().endswith('.test_historical_cleanup_document_probe_reaches_its_named_boundary'):
        excluded.append(test.id());continue
    if test.id().endswith('.test_every_declared_probe_reaches_its_named_boundary'):
        suite.addTest(SelectedCatalog([test]))
    else:suite.addTest(test)
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'ran':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'excluded':excluded}),flush=True)
raise SystemExit(not result.wasSuccessful())
