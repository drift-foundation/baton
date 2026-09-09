"""Budget2s: cold session replay must preserve the later generation's gate."""
import hashlib
import json
import pathlib
import stat
import time

from baton_v12.authority import Authority, Refusal
from tests.authority.test_session import FencedRouteSession, UUID, WORK, CLAUDE, GEMINI, NOW

started = time.monotonic()
fixture = FencedRouteSession()
result = {}
try:
    fixture.setUp()
    receipt = fixture.claude.route_fenced(fixture.operands)
    fixture.authority.add_route_handler('rview', GEMINI)
    fixture.claude.satisfy_gate({'work_id': WORK, 'operation_id': 'review-absence-original', 'gate': receipt['gate'], 'evidence': {'kind': 'runtime-absent', 'runtime': 'runtime-original'}})
    later = fixture.gemini.claim({'work_id': WORK, 'operation_id': 'review-later-claim'})['assignment']
    fixture.gemini.cancel({'expect': later, 'operation_id': 'review-later-cancel'})
    before = fixture.gemini.project_work(WORK)
    fixture.authority.dispose()
    reopened = Authority.open(fixture.path, expected_authority_uuid=UUID, clock=lambda: NOW)
    fixture.addCleanup(reopened.dispose)
    original = reopened.session(CLAUDE)
    result['replayed_identically'] = original.route_fenced(fixture.operands) == receipt
    result['later_work_unchanged'] = original.project_work(WORK) == before
    result['later_gate'] = before['gate']
    for name, session, operands in (
            ('fresh_old_operation', original, {**fixture.operands, 'operation_id': 'review-fresh-old'}),
            ('foreign_session_replay', reopened.session(GEMINI), fixture.operands)):
        try:
            session.route_fenced(operands)
        except Refusal:
            result[name] = 'refused'
        else:
            result[name] = 'unexpected success'
    assert result['replayed_identically'] and result['later_work_unchanged']
    assert result['fresh_old_operation'] == result['foreign_session_replay'] == 'refused'
finally:
    fixture.doCleanups()
result['elapsed_seconds'] = time.monotonic() - started
root = pathlib.Path('/home/sl/src/baton')
evidence = pathlib.Path(__file__).parent
recorded = json.loads((evidence / 'implementation-125216/final.json').read_text())
result['candidate'] = []
for item in recorded['files']:
    path = root / item['path']
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    mode = oct(stat.S_IMODE(path.stat().st_mode))
    result['candidate'].append({'path': item['path'], 'sha256': sha, 'mode': mode, 'matches': sha == item['sha256'] and mode == item['mode']})
assert all(item['matches'] for item in result['candidate'])
(evidence / 'review-125295-probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
