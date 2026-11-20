import json,time,unittest
from pathlib import Path
from tools import parallel_test as runner
out=Path(__file__).resolve().parent;start=time.monotonic()
suite=runner.Suite(runner.ROOT,runner.PARALLEL_MODULES,runner.SERIAL_MODULES,supervised=runner.SUPERVISED_MODULES)
suite.check_registry();suite.check_groups()
modules=sorted(suite.registered());assert len(modules)==189
names=['tests.tools.test_work_command','tests.job_manager.test_creation','tests.tools.test_connected_creation','tests.authority.test_work_labels','tests.authority.test_work_label_exposure','tests.tools.test_job_observation','tests.tools.test_job_viewer','tests.tools.test_parallel_runner']
result={'registry_complete':True,'groups_consistent':True,'modules_registered':len(modules),'modules':modules,'groups':{n:suite.group_of(n) for n in names},'seconds':time.monotonic()-start}
assert result['groups']['tests.tools.test_job_observation']==result['groups']['tests.tools.test_work_command']=='tools-pure'
(out/'registry.json').write_text(json.dumps(result,indent=2)+'\n')
start=time.monotonic()
with (out/'observation-smoke.log').open('w') as stream:
 tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.tools.test_job_observation'))
summary={'tests':tested.testsRun,'failures':len(tested.failures),'errors':len(tested.errors),'skips':len(tested.skipped),'seconds':time.monotonic()-start,'ok':tested.wasSuccessful()}
(out/'observation-smoke.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));raise SystemExit(not tested.wasSuccessful())
