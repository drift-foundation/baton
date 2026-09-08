"""Frozen review tampering through real worker entry and manager result reader.

The child already proves reader refusal. This adds the parent ending and zero
provider boundary at the now accepted child bytes, plus a genuine import control.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
RECORD = HERE.parents[1]
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.manager import test_integration_worker as fixture
from baton_v12.contracts import digest

parent = json.loads((RECORD / 'evidence/review-114828/audit.json').read_text())['paths']
child = json.loads((RECORD / 'findings/finding-import-authorization-evidence/evidence/review-114869/audit.json').read_text())['paths']
expected = {name: data['sha256'] for name, data in parent.items()}
expected.update({name: data['sha256'] for name, data in child.items()})
out = {'claim': 114978, 'at': datetime.now(timezone.utc).isoformat(), 'paths': {}}
for name, wanted in expected.items():
    data = (REPO / name).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    assert sha == wanted, (name, sha, wanted)
    dest = HERE / 'candidate' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    out['paths'][name] = {'sha256': sha, 'matches_independent_acceptance': True}

def probe(mode):
    case = fixture.WorldCase('run')
    case.setUp()
    try:
        root = case.bundle(operation='add')
        evidence = copy.deepcopy(fixture.contract.read_bundle(root)['evidence'])
        account, review = evidence['authority.json'], evidence['review.json']
        original = review['review_result_digest']
        if mode == 'rewritten-output':
            output = account['review']['documents'][0]
            entry = output['files'][0]
            payload = b'JOIN114978 invented permission under an unchanged result identity\n'
            output['bytes'] += len(payload) - entry['bytes']
            entry.update(text=payload.decode(), bytes=len(payload), digest=hashlib.sha256(payload).hexdigest())
            output['tree_digest'] = digest([{'path': f['path'], 'bytes': f['bytes'], 'content_digest': 'sha256:' + f['digest']} for f in output['files']])
            artifact = next(a for a in review['review_result']['artifacts'] if a['output_name'] == output['output_name'])
            artifact.update(content_digest=output['tree_digest'], bytes=output['bytes'])
        elif mode == 'removed-outputs':
            account['review']['documents'] = []
            review['review_result']['artifacts'] = []
        elif mode != 'control':
            raise ValueError(mode)
        if mode != 'control':
            root = case.derived(documents={'authority.json': account, 'review.json': review}, name=mode)
        target = Path(case.target(repository=False))
        before = {str(p.relative_to(target)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'mode': stat.S_IMODE(p.stat().st_mode)} for p in target.rglob('*') if p.is_file()}
        status = case.entry(bundle=root, target=str(target))
        observed = case.observed()
        after = {str(p.relative_to(target)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'mode': stat.S_IMODE(p.stat().st_mode)} for p in target.rglob('*') if p.is_file()}
        if mode == 'control':
            assert observed['result']['outcome'] == 'integrated', observed
            assert (target / case.reviewed()).read_bytes() == case.CANDIDATE
            assert stat.S_IMODE((target / case.reviewed()).stat().st_mode) == 0o644
            assert observed['result']['detail']['verification']['status'] == 0
            assert len(case.commands) == 1
        else:
            assert observed['result']['outcome'] == 'refused', observed
            assert observed['result']['detail']['reason'] == 'bundle-unreadable', observed
            assert 'not the result its own digest names' in observed['result']['detail']['detail']['observed']
            assert len(case.commands) == 0
            assert after == before
            assert digest(review['review_result']) != original
        return {'case': mode, 'entry_status': status, 'provider_turns': len(case.commands), 'target_unchanged': after == before, 'declared_result_digest': original, 'actual_result_digest': digest(review['review_result']), 'identity_preserved': review['review_result_digest'] == account['review']['result_digest'] == original, 'observed': observed}
    finally:
        case.doCleanups()

out['boundary'] = 'real accepted producer, real entry, injected provider subprocess, actual verification subprocess and public manager result parser; disposable plain target and injected revision, no Git or engine operation'
out['cases'] = [probe(mode) for mode in ('control', 'rewritten-output', 'removed-outputs')]
out['post_probe_hashes_match'] = all(hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha for name, sha in expected.items())
assert out['post_probe_hashes_match']
(HERE / 'joined.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
