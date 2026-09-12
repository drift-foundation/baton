"""Run offline package checks; retain output externally without changing candidate."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = next(parent for parent in HERE.parents if (parent / 'v12/python/src/baton_v12').is_dir())
sys.path[:0] = [str(HERE), str(REPO / 'v12/python/src'), str(REPO / 'v12/python'), str(REPO / 'v12/worker')]
retained = Path(tempfile.mkdtemp(prefix='w71879-152563-offline-verification-'))
started = time.monotonic()
output = io.StringIO()
with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py')
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
report = {'scope': 'offline synthetic fixtures only; not integration or host execution evidence',
          'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
          'seconds': time.monotonic() - started, 'retained': str(retained)}
(retained / 'verification.txt').write_text(output.getvalue())
(retained / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(output.getvalue())
print(json.dumps(report, indent=2))
sys.exit(not result.wasSuccessful())
