import json
from pathlib import Path
import time
import unittest
from tools import parallel_test as runner

out = Path(__file__).resolve().parent
suite = runner.Suite(runner.ROOT, runner.PARALLEL_MODULES, runner.SERIAL_MODULES, supervised=runner.SUPERVISED_MODULES)
suite.check_registry()
suite.check_groups()
(out/'registry.json').write_text(json.dumps({'complete': True, 'modules': len(suite.registered()), 'work_command': suite.group_of('tests.tools.test_work_command')},indent=2)+'\n')
start=time.monotonic()
selected=unittest.defaultTestLoader.loadTestsFromNames([
 'tests.tools.test_work_command',
 'tests.job_manager.test_creation.CreateTimeWorkLabelsAreAppliedByTheActThatMakesTheWork',
 'tests.job_manager.test_creation.WhatItRefusesBeforeAnyEffect.test_no_broad_except_stands_between_a_fault_and_its_caller'])
with (out/'focused.log').open('w') as stream:
 result=unittest.TextTestRunner(stream=stream,verbosity=2).run(selected)
summary={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'seconds':time.monotonic()-start,'ok':result.wasSuccessful()}
(out/'focused.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
raise SystemExit(not result.wasSuccessful())
