import os,unittest
from unittest.mock import patch
from tests.tools.test_connected_creation import TheReusableInstanceServesDefinedJobs
original=os.makedirs
removed=[]
def without_fixture_sources(name,*a,**kw):
    if str(name).endswith(('/repo/source-impl-a','/repo/source-review-a')):
        removed.append(str(name));return
    return original(name,*a,**kw)
suite=unittest.defaultTestLoader.loadTestsFromTestCase(TheReusableInstanceServesDefinedJobs)
with patch('os.makedirs',side_effect=without_fixture_sources):
    result=unittest.TextTestRunner(verbosity=1).run(suite)
print('Fixture-only source mkdirs suppressed:',len(removed))
