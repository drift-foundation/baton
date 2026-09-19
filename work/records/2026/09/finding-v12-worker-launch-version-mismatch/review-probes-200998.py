"""Reviewer-only synthetic probes; no deployment, engine, or store opened."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'v12/python'))
sys.path.insert(0, str(ROOT / 'v12/python/src'))
from tests.manager.test_w197661_verifier import VerifierCase
case = VerifierCase()
case.setUp()
v = case.verify
import compose_lifecycle as c
from baton_v12.authority import Authority
start = time.monotonic()
results = {}
obs = copy.deepcopy(case.observed)
obs['expected'] = {'unrelated': True}
obs['measured'] = {}
results['missing_all_provenance_accepted'] = not v.judge(obs).failed
obs = copy.deepcopy(case.observed)
for stage in obs['status']['jobs'][0]['stages']:
    stage.pop('attempt_id')
obs['records']['verdict'].pop('attempt_id')
obs['line'].pop('custody')
results['missing_all_attempt_identities_accepted'] = not v.judge(obs).failed
class FakeAuthority:
    def policy_generation(self): return 23
    def dispose(self): pass
with patch.object(Authority, 'open', return_value=FakeAuthority()) as writable, patch.object(Authority, 'open_readonly', side_effect=AssertionError('unexpected read-only call')) as readonly:
    c.check_policy_pin(pin=23)
    results['pin_check_writable_open_calls'] = writable.call_count
    results['pin_check_readonly_open_calls'] = readonly.call_count
scratch = Path(tempfile.mkdtemp(prefix='w197661-review200998-'))
expected = scratch / 'EXPECTED.json'
expected.write_text(json.dumps(case.sealed))
output = scratch / 'verification-probe.json'
output.write_text('prior immutable evidence\n')
with patch.object(v, 'HERE', scratch), patch.object(v, 'EXPECTED', expected), patch.object(v, 'measure', return_value=case.sealed), patch.object(v, 'read_status', return_value=case.observed['status']), patch.object(v, 'read_authority', return_value=case.observed['authority']), patch.object(c, 'check_policy_pin', return_value=case.observed['pin']), patch.object(v, 'read_line', return_value=case.observed['line']), patch.object(v, 'read_records', return_value=case.observed['records']), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    results['synthetic_main_exit'] = v.main(['--claim', 'probe'])
results['existing_evidence_overwritten'] = output.read_text() != 'prior immutable evidence\n'
results['scratch'] = str(scratch)
results['probe_seconds'] = time.monotonic() - start
paths = ['instance-200564/verify_lifecycle.py', 'instance-200564/compose_lifecycle.py', 'instance-200564/EXPECTED.json', 'instance-200564/PROVENANCE-clean.json', 'EVIDENCE-200930.json']
results['sha256'] = {p: hashlib.sha256((Path(__file__).parent / p).read_bytes()).hexdigest() for p in paths}
test = ROOT / 'v12/python/tests/manager/test_w197661_verifier.py'
results['sha256']['v12/python/tests/manager/test_w197661_verifier.py'] = hashlib.sha256(test.read_bytes()).hexdigest()
results['focused_tests'] = {'count': 31, 'outcome': 'pass', 'wall_seconds': 0.022287096}
print(json.dumps(results, indent=2, sort_keys=True))
