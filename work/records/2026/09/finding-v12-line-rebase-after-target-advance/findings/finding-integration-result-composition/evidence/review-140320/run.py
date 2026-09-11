import json
import os
from pathlib import Path
import subprocess
import time

out = Path(__file__).resolve().parent
result = json.loads((out / 'result.json').read_text())
argv = ['python3', '-m', 'unittest', 'tests.tools.test_stage_execution.TwoBoundJobsTraverseServingAndCorrection.test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET', 'tests.job_manager.test_delegation.TheIntegrationObservationIsBoundBeforeItIsRead']
assert result['review_cumulative_charge_seconds'] + 4.1 < result['review_ceiling_seconds']
env = dict(os.environ, PYTHONPATH='src:tools', PYTHONDONTWRITEBYTECODE='1')
start = time.monotonic()
with (out / 'independent-ab-and-binding.log').open('wb') as log:
    try:
        completed = subprocess.run(argv, cwd='/home/sl/src/baton/v12/python', env=env, stdout=log, stderr=subprocess.STDOUT, timeout=4.0)
        code, timed_out = completed.returncode, False
    except subprocess.TimeoutExpired:
        code, timed_out = 124, True
elapsed = time.monotonic() - start
run = {'argv': argv, 'cwd': 'v12/python', 'env': {'PYTHONPATH': 'src:tools', 'PYTHONDONTWRITEBYTECODE': '1'}, 'elapsed_seconds': elapsed, 'charge_seconds': elapsed + 0.05, 'timeout_seconds': 4.0, 'exit_code': code, 'timed_out': timed_out}
result['independent_ab_and_binding'] = run
result['review_cumulative_charge_seconds'] += run['charge_seconds']
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(run, indent=2))
print((out / 'independent-ab-and-binding.log').read_text())
print('CUMULATIVE_REVIEW_SECONDS', result['review_cumulative_charge_seconds'])
