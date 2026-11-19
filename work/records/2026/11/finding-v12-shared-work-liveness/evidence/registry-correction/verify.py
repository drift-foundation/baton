"""Bounded W385263 registry delta verification; never selects the full suite."""
import json
from pathlib import Path
import shutil
import signal
import time
import unittest
from tools import parallel_test as runner

out = Path(__file__).resolve().parent
module = 'tests.tools.test_job_observation'
suite = runner.Suite(runner.ROOT, runner.PARALLEL_MODULES, runner.SERIAL_MODULES,
                     supervised=runner.SUPERVISED_MODULES)
started = time.monotonic()
suite.check_registry()
suite.check_groups()
assert module in suite.parallel and suite.group_of(module) == 'tools-pure'
(out / 'registry.json').write_text(json.dumps({
    'complete': True, 'groups_complete': True, 'registered_modules': len(suite.registered()),
    'discovered_modules': len(suite.discovered()), 'module': module,
    'classification': 'parallel', 'group': suite.group_of(module),
    'seconds': time.monotonic() - started}, indent=2) + '\n')

started = time.monotonic()
with (out / 'runner-tests.log').open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName('tests.tools.test_parallel_runner'))
regressions = {'tests': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'skips': len(result.skipped),
               'seconds': time.monotonic() - started, 'ok': result.wasSuccessful()}
(out / 'runner-tests.json').write_text(json.dumps(regressions, indent=2) + '\n')
assert result.wasSuccessful(), regressions

# Use the real registry and runner primitives; select only the new module at
# collection. No registry overrides, no engine/serial/supervised collection.
started = time.monotonic()
with (out / 'accounted-progress.log').open('w') as progress:
    run = runner.Run(suite, jobs_override='2', progress=progress)
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    for sig in previous:
        signal.signal(sig, run.record_signal)
    try:
        result_root = run.open_result_root()
        ids = runner.collect(run, 1, modules=(module,))
        suite.check_collected_ids(ids)
        assert len(ids) == 7 and all(runner.module_of(one) == module for one in ids)
        shards = runner.partition(ids, suite.method_split)
        done = run.drive(runner.shard_work(run, shards, 'parallel'), 2, 'parallel')
        reports = [runner.harvest(item) for item in done]
        ledger = runner.account(ids, reports, suite.optional_skips)
        ledger['ok'] = ledger['ok'] and all(one['ok'] for one in reports)
        ledger['selected_modules'] = [module]
        ledger['reports'] = reports
        shutil.copytree(run.result_root, out / 'accounted-raw')
    finally:
        try:
            run.shutdown()
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    ledger['cleanup_complete'] = not run.live and not result_root.exists()
    ledger['pending_signal'] = run.pending_signal
ledger['seconds'] = time.monotonic() - started
(out / 'accounted.json').write_text(json.dumps(ledger, indent=2) + '\n')
assert ledger['ok'] and ledger['cleanup_complete'] and ledger['pending_signal'] is None, ledger
print(json.dumps({'runner_regressions': regressions, 'accounted_new_module_tests': len(ids),
                  'accounted_ok': ledger['ok'], 'accounted_seconds': ledger['seconds']}))
