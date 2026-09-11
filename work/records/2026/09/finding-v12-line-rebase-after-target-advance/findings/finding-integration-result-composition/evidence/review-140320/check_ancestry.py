import json
import os
from pathlib import Path
import subprocess
import time

out = Path(__file__).resolve().parent
result = json.loads((out / 'result.json').read_text())
assert result['review_cumulative_charge_seconds'] + 3.1 < 15
argv = ['python3', str(out / 'ancestry.py')]
start = time.monotonic()
with (out / 'independent-ancestry.log').open('wb') as log:
    try:
        code = subprocess.run(argv, cwd='/home/sl/src/baton/v12/python', env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT, timeout=3).returncode
    except subprocess.TimeoutExpired:
        code = 124
elapsed = time.monotonic() - start
run = {'argv': argv, 'cwd': 'v12/python', 'env': {'PYTHONPATH': 'src:tools:.', 'PYTHONDONTWRITEBYTECODE': '1'}, 'elapsed_seconds': elapsed, 'charge_seconds': elapsed + 0.05, 'exit_code': code, 'timeout_seconds': 3}
result['independent_ancestry'] = run
result['review_cumulative_charge_seconds'] += run['charge_seconds']
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(run, indent=2))
print((out / 'independent-ancestry.log').read_text())
print('CUMULATIVE_REVIEW_SECONDS', result['review_cumulative_charge_seconds'])
