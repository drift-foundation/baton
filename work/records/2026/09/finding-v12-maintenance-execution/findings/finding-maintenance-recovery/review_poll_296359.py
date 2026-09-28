"""Observe ordinary preparation polling without changing production behavior."""
import json, unittest
from unittest.mock import patch
from tools import stage_execution
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
original = stage_execution.PreparationRuntime.poll
seen = []
def poll(self, held, parent, job, execution):
    answer = original(self, held, parent, job, execution)
    view = self._operations(held).observe(self._stage(held))
    if len(seen) < 3:
        seen.append({'answer': answer, 'view': view})
    return answer
with patch.object(stage_execution.PreparationRuntime, 'poll', poll):
    result = unittest.TestResult()
    OneManagedPreparationCompletes('test_ordinary_sweeps_retain_and_adopt_one_real_preparation').run(result)
print(json.dumps({'failures':len(result.failures),'errors':len(result.errors),'polls':seen},default=str,indent=2))
