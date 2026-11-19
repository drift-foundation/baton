"""Run only selected local observation/lifecycle suites; no providers/engines."""
import json
import os
from pathlib import Path
import time
import unittest

root = Path(__file__).resolve().parent
start = time.monotonic()
suite = unittest.defaultTestLoader.loadTestsFromNames([
    'tests.tools.test_job_observation', 'tests.tools.test_job_viewer',
    'tests.tools.test_stack', 'tests.tools.test_worker_visibility'])
with (root / 'focused.log').open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
           'skips': len(result.skipped), 'seconds': time.monotonic() - start,
           'successful': result.wasSuccessful(), 'scope': 'deterministic shared model, viewer, stack lifecycle and unchanged worker visibility'}
(root / 'focused.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
raise SystemExit(not result.wasSuccessful())
