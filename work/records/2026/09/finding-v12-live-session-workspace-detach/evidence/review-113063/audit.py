"""Review only the nominated closed export and repository package; no private reads."""
import hashlib
import json
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parent.parent
REPO = next(p for p in DOSSIER.parents if (p / 'AGENTS.md').is_file())
SOURCE = Path('/tmp/baton-w106673-live-export-syxb4jnc')
NAMES = ['package.json', 'network.json', 'result.json', 'setup.json', 'restored-first/events.json', 'restored-first/gate.json']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_export(name):
    p = SOURCE / name
    for parent in [SOURCE, *list(p.relative_to(SOURCE).parents)[:-1]]:
        checked = parent if parent.is_absolute() else SOURCE / parent
        assert stat.S_ISDIR(checked.lstat().st_mode)
    found = p.lstat()
    assert stat.S_ISREG(found.st_mode) and found.st_nlink == 1 and found.st_size <= 4 * 1024 * 1024
    return p.read_bytes()


raw = {name: read_export(name) for name in ['PROVENANCE.json', *NAMES]}
data = {name: json.loads(value) for name, value in raw.items()}
provenance = data['PROVENANCE.json']
assert set(provenance['files']) == set(NAMES)
assert provenance['original_root'] == '/tmp/baton-w106673-live-w8pbhj6e'
assert all(digest(raw[name]) == provenance['files'][name] for name in NAMES)
for name, content in raw.items():
    target = HERE / 'export' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == content
    else:
        with target.open('xb') as stream:
            stream.write(content)

manifest_path = DOSSIER / 'evidence/failure-reason-112817-manifest.json'
manifest_raw = manifest_path.read_bytes()
manifest = json.loads(manifest_raw)
assert digest(manifest_raw) == '3d4332754ab9bdce095f8a31d5e6e010550645f1fa226fc46916db523918f808'
assert data['package.json']['manifest_sha256'] == digest(manifest_raw)
current = {}
for name, expected in manifest['files'].items():
    p = REPO / name
    actual = digest(p.read_bytes()) if p.is_file() and not p.is_symlink() else None
    current[name] = dict(expected=expected, actual=actual, matches=actual == expected)

events = data['restored-first/events.json']
gate = data['restored-first/gate.json']
result = data['result.json']
setup = data['setup.json']
assert all(a['monotonic_ns'] < b['monotonic_ns'] for a, b in zip(events, events[1:]))
created = [e for e in events if e['action'] == 'created']
assert len(created) == 1 and created[0]['container'] == gate['identity']['container']
assert gate['receipt']['identity'] == gate['identity']
assert gate['phase'] == 'shutdown' and gate['consumed'] == 0 and gate['generation'] == gate['receipt']['generation'] == 1
assert gate['receipt']['observation'] == dict(container_stopped=True, init_exited=True, survivors=[])
observations = [e for e in events if e['action'] == 'supervisor-observation']
assert [e['stage'] for e in observations] == ['provider-write-intent', 'provider-write-completed', 'provider-response-observed', 'provider-result-validation', 'provider-result-validation']
assert all((e['arm'], e['operation'], e['turn']) == ('restored-first', 'turn', 1) for e in observations)
assert observations[-2]['result_fields'] == dict(subtype='success', known_subtype=None, is_error='true')
assert observations[-2]['failure_reason'] == dict(shape='null', http_status=None)
assert observations[-1]['event'] == 'refused' and observations[-1]['refusal_code'] == 'provider-result-failed'
assert result['outcome'] == 'failed-or-inconclusive' and result['cleanup_confirmed'] is True
assert result['future_work'] == 'not-admitted-after-ending'
milestones = result['observed_milestones']
assert all(milestones[k] == 1 for k in ['containers_created', 'cli_initializations', 'turn_intents', 'host_turn_writes_observed', 'provider_turn_writes_observed', 'provider_results_observed'])
assert milestones['validated_turn_completions'] == milestones['verified_consumptions'] == 0
assert milestones['actual_models'] == []
assert all(milestones[k] is False for k in ['restoration_verified', 'restore_initialization_observed', 'restored_correction_verified', 'matched_pair_verified'])
assert setup['cleanup_accounted'] is True and setup['partial_setup_unresolved'] is False and setup['store_close'] == 'confirmed'
assert result['cleanup'] == [dict(confirmed=True, nonce=events[0]['nonce'])]
assert events[-1]['action'] == 'shutdown-confirmed' and events[-1]['container'] == created[0]['container']
report = dict(claim=113063, owner_handoff=113059, export_sha256={name: digest(content) for name, content in raw.items()}, package_sha256=digest(manifest_raw), current_inputs=current, current_matches=sum(row['matches'] for row in current.values()), current_total=len(current), event_count=len(events), result_fields=observations[-2]['result_fields'], failure_reason=observations[-2]['failure_reason'], milestones=milestones, local_write_to_result_ns=observations[2]['supervisor_monotonic_ns'] - observations[1]['supervisor_monotonic_ns'], assertions='passed', provenance_limit='Supplied export hashes and reviewed source; protected originals not inspected. Historical cleanup remains controller attestation except separately retained exact Docker stopped-state observation.')
with (HERE / 'audit.json').open('x') as stream:
    json.dump(report, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({k: v for k, v in report.items() if k != 'current_inputs'}, indent=2))
