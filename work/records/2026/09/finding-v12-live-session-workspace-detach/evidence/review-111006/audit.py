"""Offline exported-projection audit; never opens protected runtime or credentials."""
import hashlib
import importlib.util
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[7]
dossier = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
source = Path('/tmp/baton-w106673-live-export-0fj2ypp_')
target = here / 'export'
target.mkdir(exist_ok=True)
def digest(data):
    return hashlib.sha256(data).hexdigest()
provenance_bytes = (source / 'PROVENANCE.json').read_bytes()
provenance = json.loads(provenance_bytes)
expected = {'network.json', 'package.json', 'restored-first/events.json', 'restored-first/gate.json', 'result.json', 'setup.json'}
assert set(provenance['files']) == expected
copies = {}
for name in sorted(expected | {'PROVENANCE.json'}):
    path = source / name
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    if name != 'PROVENANCE.json':
        assert digest(raw) == provenance['files'][name]
    out = target / name
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        with out.open('xb') as stream:
            stream.write(raw)
    assert out.read_bytes() == raw
    copies[name] = digest(raw)
manifest_path = dossier / 'evidence/restore-constructor-manifest.json'
manifest_bytes = manifest_path.read_bytes()
assert digest(manifest_bytes) == 'b6058f4774775c63113f0f9721e264dd317a4f57692b2ebfdf3264511c032c4b'
manifest = json.loads(manifest_bytes)
mismatches = [dict(path=name, expected=expected_hash, observed=digest((repo / name).read_bytes())) for name, expected_hash in manifest['files'].items() if digest((repo / name).read_bytes()) != expected_hash]
events = json.loads((target / 'restored-first/events.json').read_bytes())
result = json.loads((target / 'result.json').read_bytes())
gate = json.loads((target / 'restored-first/gate.json').read_bytes())
created = [e for e in events if e['action'] == 'created']
assert len(created) == 1
assert gate['identity']['container'] == created[0]['container']
assert gate['phase'] == 'shutdown' and gate['consumed'] == 0
assert gate['receipt']['identity'] == gate['identity']
observations = [e for e in events if e['action'] == 'supervisor-observation']
assert [e['stage'] for e in observations] == ['provider-write-intent', 'provider-write-completed', 'provider-response-observed', 'provider-result-validation', 'provider-result-validation']
assert observations[-1]['refusal_code'] == 'provider-result-failed'
assert all(e['arm'] == 'restored-first' and e['turn'] == 1 for e in observations)
assert result['observed_milestones']['validated_turn_completions'] == 0
assert result['observed_milestones']['restoration_verified'] is False
spec = importlib.util.spec_from_file_location('supervisor_probe_111006', dossier / 'evidence/live_supervisor_restore.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
session = '7f00d89f-0210-41d1-b67c-89253119edd7'
valid = dict(type='result', subtype='success', is_error=False, session_id=session, num_turns=1, total_cost_usd=0)
cases = {'different-subtype': dict(subtype='synthetic-error'), 'error-true': dict(is_error=True), 'error-missing': dict(is_error=None), 'subtype-missing': dict(subtype=None)}
probe = {}
for name, updates in cases.items():
    try:
        module.result_projection({**valid, **updates}, session)
    except module.Refusal as error:
        probe[name] = module.refusal_projection(error)
        assert probe[name]['refusal_code'] == 'provider-result-failed'
    else:
        raise AssertionError(name)
assert module.result_projection(valid, session)['session'] == session
output = dict(copied_hashes=copies, candidate_files_checked=len(manifest['files']), candidate_mismatches=mismatches,
              exact_container=created[0]['container'], observations=observations, result_projection_probe=probe,
              protected_originals_read=False, provider_calls=0,
              limitations='Export hashes validate readable projections against supplied provenance; original protected bytes and historical credential teardown are not independently inspected.')
with (here / 'audit.json').open('x') as stream:
    json.dump(output, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(candidate_files_checked=len(manifest['files']), candidate_mismatches=mismatches, exported_data_files=6, provenance_copied=True, synthetic_failure_cases=len(probe), export_and_projection_checks_passed=True)))
