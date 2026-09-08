"""Offline review of the owner-exported partial run; no runtime or secret access."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORT = Path('/tmp/baton-w106673-live-export-bnhjq5rq')
REPO = next(p for p in HERE.parents if (p / 'AGENTS.md').is_file())


def read(name):
    return json.loads((EXPORT / name).read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def events(name, action):
    return [e for e in read(name + '/events.json') if e['action'] == action]


provenance = read('PROVENANCE.json')
assert len(provenance['files']) == 9
for name, expected in provenance['files'].items():
    assert digest((EXPORT / name).read_bytes()) == expected, name
manifest = json.loads((HERE / 'live-setup-manifest.json').read_text())
manifest_hash = digest((HERE / 'live-setup-manifest.json').read_bytes())
assert manifest_hash == 'c0ec6a1d820894f9a6064b6289824f20fdf296e6e2ea7599df9f22108cbb1b30'
assert len(manifest['files']) == 90
for name, expected in manifest['files'].items():
    assert digest((REPO / name).read_bytes()) == expected, name
package = read('package.json')
assert manifest_hash in package.values()
arms = read('arms.json')
assert set(arms) == {'retained'}
arm = arms['retained']
for field in ['process', 'session', 'workspace']:
    assert arm[field + '_before'] == arm[field + '_after']
for field in ['pidfd_continuously_live', 'first_artifact_verified', 'correction_verified', 'consumption_receipts_verified']:
    assert arm[field] is True

topologies = {}
identities = {}
for name, counts in [('retained-first', (2, 2, 2)), ('restored-first', (1, 1, 0))]:
    rows = read(name + '/events.json')
    stamps = [r['monotonic_ns'] for r in rows]
    assert stamps == sorted(stamps)
    identity = events(name, 'registered')[0]['identity']
    identities[name] = identity
    intent = events(name, 'create-intent')[0]
    assert intent['resume'] is False
    assert intent['workspace_pin'] == identity['workspace']
    quiescent = events(name, 'quiescent')
    assert len(quiescent[0]['processes']) == 2
    assert all(q['processes'] == quiescent[0]['processes'] and q['session'] == intent['requested_session'] for q in quiescent)
    topology = events(name, 'topology')
    output = next(m for m in topology[0]['mounts'] if m['target'] == '/output')
    for event in topology:
        mounts = event['mounts']
        assert all(not m['propagation'] for m in mounts)
        assert 'ro' in next(m for m in mounts if m['target'] == '/')['options']
        aliases = [m for m in mounts if m['device'] == output['device'] and (m['root'] == output['root'] or m['root'].startswith(output['root'] + '/') or output['root'].startswith(m['root'].rstrip('/') + '/'))]
        assert len(aliases) == int(event['attached'])
        if aliases:
            assert aliases[0]['target'] == '/output' and aliases[0]['root'] == output['root'] and 'rw' in aliases[0]['options']
        assert sum(m['target'] == '/output' for m in mounts) == int(event['attached'])
    topologies[name] = [t['attached'] for t in topology]
    gate = read(name + '/gate.json')
    assert (gate['generation'], gate['admissions'], gate['consumed']) == counts
    assert gate['identity'] == identity and gate['phase'] == 'shutdown'
    assert gate['receipt']['identity'] == identity
    assert gate['receipt']['observation'] == {'container_stopped': True, 'init_exited': True, 'survivors': []}
    assert rows[-1]['action'] == 'shutdown-confirmed' and rows[-1]['init_exit_observed'] is True

assert topologies['retained-first'] == [True, True, False, False, True, True, False]
assert topologies['restored-first'] == [True]
turns = events('retained-first', 'turn-complete')
assert len(turns) == 2
for turn in turns:
    assert turn['session'] == arm['session_before']
    assert turn['actual_model'] == arm['actual_model'] == 'claude-fable-5'
    assert turn['cli_version'] == arm['cli_version'] == '2.1.247'
    assert turn['cli_start'] == arm['process_before'][2]
    assert turn['dispatched_ns'] < turn['completed_ns'] < turn['monotonic_ns']
assert arm['end_of_work_ns'] == turns[0]['completed_ns']
assert arm['correction_dispatch_ns'] == turns[1]['dispatched_ns']
assert arm['correction_done_ns'] == turns[1]['completed_ns']
assert arm['correction_dispatch_ns'] - arm['review_ready_ns'] >= arm['review_delay_ns'] == 5000000000
receipts = events('retained-first', 'receipt-consumed')
verified = events('retained-first', 'consumed-and-verified')
assert len(receipts) == len(verified) == 2
for i, receipt in enumerate(receipts):
    r = receipt['receipt']
    assert r['generation'] == i + 1 and r['identity'] == identities['retained-first']
    assert r['observation'] == {'mount_absent': True, 'access': {'event': 'probe', 'writable': False, 'errno': 2}}
    assert turns[i]['monotonic_ns'] < receipt['monotonic_ns'] < verified[i]['monotonic_ns']
    assert verified[i]['corrected'] is bool(i)
    expected = ('def scale(value):\n    return value * ' + str(i + 2) + '\n').encode()
    assert verified[i]['files']['solution.py'] == digest(expected)
assert receipts[0]['receipt']['operation'] != receipts[1]['receipt']['operation']
assert verified[0]['monotonic_ns'] < arm['review_ready_ns'] < turns[1]['dispatched_ns']
assert verified[1]['monotonic_ns'] < arm['verified_correction_ns']
assert events('retained-first', 'shutdown-confirmed')[0]['monotonic_ns'] < events('restored-first', 'create-intent')[0]['monotonic_ns']
assert not events('restored-first', 'turn-complete') and not events('restored-first', 'receipt-consumed')
assert not (EXPORT / 'restored-second').exists()

containers = json.loads((HERE / 'review-live-partial-containers-2026-09-07.json').read_text())['containers']
assert len(containers) == 2
for name, container in zip(['retained-first', 'restored-first'], containers):
    intent = events(name, 'create-intent')[0]
    assert container['id'] == identities[name]['container']
    assert container['image'] == arm['image'] == intent['image']
    assert container['network'] == intent['network_id']
    assert container['labels'] == {'baton.experiment': 'W106673', 'baton.run': intent['nonce']}
    assert container['state']['Status'] == 'exited' and container['state']['Pid'] == 0
    assert not container['state']['Running'] and not container['state']['OOMKilled']
    assert container['user'] == '65532:65532' and container['readonly_root'] is True
    assert container['privileged'] is False and container['cap_drop'] == ['ALL']
    assert container['security_opt'] == ['no-new-privileges']

# Retain exact readable projections, never protected original/session/store data.
retained = HERE / 'live-partial-export-2026-09-07'
for name in ['PROVENANCE.json', *provenance['files']]:
    target = retained / name
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (EXPORT / name).read_bytes()
    if target.exists():
        assert target.read_bytes() == data
    else:
        target.write_bytes(data)
result = {
    'claim': 108110, 'export': str(EXPORT), 'originals_read': False,
    'manifest_sha256': manifest_hash, 'candidate_hashes_matched': 90,
    'export_hashes_matched': 9, 'topology_sequences': topologies,
    'retained_live_continuity': 'accepted within reviewed fixture and exported observations',
    'time_to_verified_correction_seconds': (arm['verified_correction_ns'] - arm['end_of_work_ns']) / 1e9,
    'review_delay_seconds': arm['review_delay_ns'] / 1e9,
    'time_to_review_ready_seconds': (arm['review_ready_ns'] - arm['end_of_work_ns']) / 1e9,
    'correction_response_seconds': (arm['correction_done_ns'] - arm['correction_dispatch_ns']) / 1e9,
    'final_verification_seconds': (arm['verified_correction_ns'] - arm['correction_done_ns']) / 1e9,
    'mount_durations_seconds': {a: events('retained-first', a)[0]['duration_ns'] / 1e9 for a in ['first-detach', 'reattach', 'final-detach']},
    'restoration_observed': False, 'comparison': 'inconclusive',
    'restored_first_last_pre_shutdown_event': read('restored-first/events.json')[-2],
    'independent_container_endings': 'both exited, PID0, no OOM; exit code 1',
    'limits': ['Export hash checks bind supplied projections, not independently reread protected originals.', 'Continuity token verification is attested by reviewed controller; raw token not exported.', 'Missing turn-complete does not establish whether a user frame was sent or a model reply arrived.', 'No credential teardown inspection, provider cause, billing enforcement or production adoption claim.'],
}
(HERE / 'review-live-partial-audit-2026-09-07.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
