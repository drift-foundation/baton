"""Read-only preparation contract check; no controller, Job or engine starts."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

started = time.monotonic()
here = Path(__file__).resolve().parent
root = Path(sys.argv[1]).resolve()
source = root / 'code/v12/python'
sys.path[:0] = [str(source / 'src'), str(source), str(root / 'supervisor')]
import baseline
from tools import authoring_enforcement
from baton_v12.worker_manager import tokens

packet = baseline.held_packet(str(root / 'packet/PACKET.json'))
baseline.verify_imported_sources(packet)
authoring_enforcement.verify_controller(packet)
commands = json.loads((root / 'packet/commands.json').read_text())
assert commands['start'] == [sys.executable, '-B', '-m', 'tools.authoring_enforcement', '--packet', str(root / 'packet/PACKET.json')]
assert commands['environment']['PYTHONPATH'].split(':') == [str(source / 'src'), str(source), str(root / 'supervisor')]
assert commands['environment']['BATON_V12_STAGE_EXECUTION_CONFIG'] == str(root / 'packet/deployment.json')
accepted = json.loads((here / 'ACCEPTED-PREREQUISITE.json').read_text())
manifest = json.loads((here / 'SOURCE.json').read_text())
for change in accepted['changes']:
    assert manifest['files'][change['path']] == change['candidate_sha256']
    if change['path'].startswith(('v12/python/tools/', 'v12/python/src/')):
        relative = change['path'].removeprefix('v12/python/')
        assert packet['manager_source']['files'][relative] == change['candidate_sha256']
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == change['candidate_sha256']
for mode in ('missing', 'wrong'):
    bad = copy.deepcopy(packet)
    if mode == 'missing':
        del bad['manager_source']['files']['tools/authoring_enforcement.py']
    else:
        bad['manager_source']['files']['tools/authoring_enforcement.py'] = '0' * 64
    try:
        authoring_enforcement.verify_controller(bad)
    except RuntimeError as error:
        assert 'not pinned' in str(error)
    else:
        raise AssertionError('unpinned controller accepted')
policy = json.loads((root / 'packet/policy.json').read_text())
submission = json.loads((root / 'packet/submission.json').read_text())
limits = dict(provider_turn_seconds=3600, verification_command_seconds=30)
assert submission['jobs'][0]['execution_limits'] == limits
assert {key: policy[key] for key in limits} == limits
assert policy['automatic_retry'] is False and policy['implementer_invocations'] == 1
assert submission['jobs'][0]['terminal_policy'] == 'report-and-hold'
assert packet['bounds']['total_seconds'] == 4800 and packet['bounds']['cleanup_seconds'] == 60
assert tokens.LIFETIME_SECONDS == 900 and tokens.RENEWAL_LIMIT == 4 and tokens.STOP_GRACE_SECONDS == 30
assert authoring_enforcement.POLL_SECONDS == 0.25 and authoring_enforcement.ENGINE_SECONDS == 2
for store in ('job_store', 'control_store'):
    assert not Path(packet['deployment'][store]).exists(), 'preparation must not submit or start'
print(json.dumps(dict(state='preparation-contract-passed', accepted_hashes=6, controller_refusals=2,
                     start='tools.authoring_enforcement', limits=limits, total_seconds=4800, cleanup_seconds=60,
                     lifetime_seconds=900, jobs=0, attempts=0, seconds=time.monotonic()-started), sort_keys=True))
