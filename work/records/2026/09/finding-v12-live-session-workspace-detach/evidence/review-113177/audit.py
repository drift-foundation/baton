"""Independent closed-export audit, claim113177. No private runtime reads."""
import hashlib
import json
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parent.parent
REPO = next(p for p in DOSSIER.parents if (p / 'AGENTS.md').is_file())
SOURCE = Path('/tmp/baton-w106673-live-export-k0vmhio5')
NAMES = ['package.json', 'network.json', 'arms.json', 'result.json', 'setup.json',
         'restored-first/events.json', 'restored-first/gate.json',
         'restored-second/events.json', 'restored-second/gate.json']
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
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
assert provenance['original_root'] == '/tmp/baton-w106673-live-nsn38dlq'
assert all(digest(raw[name]) == provenance['files'][name] for name in NAMES)
for name, content in raw.items():
    target = HERE / 'export' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == content
    else:
        with target.open('xb') as stream:
            stream.write(content)
manifest_raw = (DOSSIER / 'evidence/failure-reason-112817-manifest.json').read_bytes()
manifest = json.loads(manifest_raw)
assert digest(manifest_raw) == '3d4332754ab9bdce095f8a31d5e6e010550645f1fa226fc46916db523918f808'
assert data['package.json']['manifest_sha256'] == digest(manifest_raw)
current = {}
for name, expected in manifest['files'].items():
    p = REPO / name
    actual = digest(p.read_bytes()) if p.is_file() and not p.is_symlink() else None
    current[name] = dict(expected=expected, actual=actual, matches=actual == expected)
assert len(current) == 163 and all(row['matches'] for row in current.values())
sys.path.insert(0, str(DOSSIER / 'evidence'))
import real_session_contract as contract
result = data['result.json']
assert result['outcome'] == 'restored-only-passed'
assert result['experiment'] == 'restored-only-separate-run' and result['matched_comparison'] is False
assert data['arms.json'] == result['arms'] and set(result['arms']) == {'restored'}
arm = result['arms']['restored']
assert arm['workspace_before'] == arm['workspace_after']
assert arm['session_before'] == arm['session_after'] == arm['resume_requested']
assert contract.SESSION.fullmatch(arm['session_before'])
assert arm['process_before'] != arm['process_after']
assert all(arm[k] is True for k in ['consumption_receipts_verified','correction_verified','first_artifact_verified','old_container_shutdown_confirmed','final_shutdown_confirmed'])
assert arm['initial_bytes_sha256'] == digest(b'')
assert arm['correction_prompt_sha256'] == digest(contract.CORRECTION.encode())
assert arm['review_delay_ns'] == 5000000000
assert arm['image'] == data['package.json']['image'] == manifest['image']
assert arm['model'] == data['package.json']['model'] == 'claude-fable-5[1m]'
assert arm['cli_version'] == '2.1.247' and arm['actual_model'] == 'claude-fable-5'
rows_by_arm = {}
topologies = {}
processes = {}
containers = json.loads((HERE/'docker-inspect.json').read_text())['containers']
assert len(containers) == 2
for i, name in enumerate(['restored-first', 'restored-second']):
    rows = data[name+'/events.json']
    rows_by_arm[name] = rows
    assert all(a['monotonic_ns'] < b['monotonic_ns'] for a,b in zip(rows,rows[1:]))
    def one(action):
        matches = [e for e in rows if e['action'] == action]
        assert len(matches) == 1, (name, action)
        return matches[0]
    intent, created, registered = one('create-intent'),one('created'),one('registered')
    identity = registered['identity']
    assert intent['resume'] is bool(i)
    assert intent['requested_session'] == arm['session_before']
    assert intent['workspace_pin'] == identity['workspace'] == arm['workspace_before']
    assert created['container'] == identity['container']
    quiescent = [e for e in rows if e['action'] == 'quiescent']
    assert len(quiescent[0]['processes']) == 2
    assert all(e['processes'] == quiescent[0]['processes'] and e['session'] == arm['session_before'] for e in quiescent)
    cli = next(p for p in quiescent[0]['processes'] if p['inner_pid'] == 8)
    process = [identity['container'], cli['pid'],cli['start'],cli['namespace']]
    assert process == arm['process_after' if i else 'process_before']
    processes[name] = process
    topology = [e for e in rows if e['action'] == 'topology']
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
    topologies[name] = [e['attached'] for e in topology]
    assert topologies[name] == ([True] if i == 0 else [True,True,False])
    turn,receipt,verified,shutdown = one('turn-complete'),one('receipt-consumed'),one('consumed-and-verified'),one('shutdown-confirmed')
    assert turn['session'] == arm['session_before'] and turn['actual_model'] == arm['actual_model'] and turn['cli_version'] == arm['cli_version']
    assert turn['cli_start'] == cli['start'] and turn['cli_pid'] == cli['inner_pid']
    assert turn['dispatched_ns'] < turn['completed_ns'] < turn['monotonic_ns'] < receipt['monotonic_ns'] < verified['monotonic_ns']
    assert turn['completed_ns'] == arm['correction_done_ns' if i else 'end_of_work_ns']
    assert verified['corrected'] is bool(i)
    assert verified['files']['solution.py'] == digest(contract.CORRECTED if i else contract.INITIAL)
    assert set(verified['files']) == ({'solution.py','continuity.txt'} if i else {'solution.py'})
    expected = dict(mount_absent=True, access=dict(event='probe',writable=False,errno=2)) if i else dict(container_stopped=True,init_exited=True,survivors=[])
    assert receipt['receipt']['observation'] == expected
    assert receipt['receipt']['identity'] == identity and receipt['receipt']['generation'] == 1
    assert shutdown['container'] == identity['container'] and shutdown['init_exit_observed'] is True
    if i:
        assert one('detach-result')['answer'] == dict(ok=True,errno=None)
        assert turn['monotonic_ns'] < one('detach-result')['monotonic_ns'] < receipt['monotonic_ns']
        assert turn['dispatched_ns'] == arm['correction_dispatch_ns']
        assert verified['monotonic_ns'] < arm['verified_correction_ns'] < shutdown['monotonic_ns']
    else:
        assert shutdown['monotonic_ns'] < receipt['monotonic_ns']
        assert verified['monotonic_ns'] < arm['review_ready_ns']
    gate = data[name+'/gate.json']
    assert gate['identity'] == identity and (gate['generation'],gate['admissions'],gate['consumed']) == (1,1,1)
    assert gate['phase'] == ('shutdown' if i else 'reviewed')
    if i:
        assert gate['receipt']['identity'] == identity and gate['receipt']['generation'] == 1
        assert gate['receipt']['observation'] == dict(container_stopped=True,init_exited=True,survivors=[])
    else:
        assert gate['receipt'] is None
    observations = [e for e in rows if e['action'] == 'supervisor-observation']
    assert [e['stage'] for e in observations] == ['provider-write-intent','provider-write-completed','provider-response-observed','provider-result-validation']
    assert all((e['arm'],e['operation'],e['turn'],e['event']) == (name,'turn',1,'diagnostic') for e in observations)
    assert observations[-1]['result_fields'] == dict(subtype='success',known_subtype=None,is_error='false')
    assert observations[-1]['failure_reason'] == dict(shape='null',http_status=None)
    assert all(a['supervisor_monotonic_ns'] < b['supervisor_monotonic_ns'] for a,b in zip(observations,observations[1:]))
    c = containers[i]
    assert c['id'] == identity['container'] and c['image'] == intent['image'] == arm['image']
    assert c['network'] == intent['network_id'] == data['network.json']['id']
    assert c['labels'] == {'baton.experiment':'W106673','baton.run':intent['nonce']}
    assert c['state']['Status'] == 'exited' and c['state']['Pid'] == 0 and c['state']['Running'] is False and c['state']['OOMKilled'] is False
    assert c['user'] == '65532:65532' and c['readonly_root'] is True and c['privileged'] is False
    assert c['cap_drop'] == ['ALL'] and c['security_opt'] == ['no-new-privileges']
first,second = rows_by_arm.values()
assert first[-1]['monotonic_ns'] < arm['review_ready_ns'] + arm['review_delay_ns'] <= second[0]['monotonic_ns']
assert result['cleanup'] == [dict(confirmed=True,nonce=rows[0]['nonce']) for rows in [first,second]]
assert result['cleanup_confirmed'] is True and result['future_work'] == 'not-admitted-after-ending'
setup = data['setup.json']
assert setup['cleanup_accounted'] is True and setup['partial_setup_unresolved'] is False and setup['store_close'] == 'confirmed'
m = result['observed_milestones']
assert all(m[k] == 2 for k in ['containers_created','cli_initializations','turn_intents','host_turn_writes_observed','provider_turn_writes_observed','provider_results_observed','validated_turn_completions','verified_consumptions'])
assert all(m[k] is True for k in ['restoration_verified','restore_initialization_observed','restored_correction_verified'])
assert m['retained_correction_verified'] is False and m['matched_pair_verified'] is False and m['actual_models'] == ['claude-fable-5']
timings = dict(end_to_verified_correction_ns=arm['verified_correction_ns']-arm['end_of_work_ns'], review_readiness_ns=arm['review_ready_ns']-arm['end_of_work_ns'], correction_response_ns=arm['correction_done_ns']-arm['correction_dispatch_ns'], final_revocation_and_verification_ns=arm['verified_correction_ns']-arm['correction_done_ns'])
assert timings == result['restoration_timings']
report = dict(claim=113177,owner_handoff=113124,export_sha256={name:digest(value) for name,value in raw.items()},package_sha256=digest(manifest_raw),current_inputs=current,current_matches=163,current_total=163,event_counts={k:len(v) for k,v in rows_by_arm.items()},topologies=topologies,processes=processes,session=arm['session_before'],workspace=arm['workspace_before'],timings_ns=timings,actual_model=arm['actual_model'],milestones=m,assertions='passed',limitations=['Supplied export integrity checked; protected originals not inspected.','Raw continuity token not reopened; exact verifier success is reviewed-controller evidence.','Historical no-survivor and credential release remain controller attestations; current stopped state independently inspected.','Separate restored observation, no matched comparison or production adoption.'])
with (HERE/'audit.json').open('x') as f:
    json.dump(report,f,indent=2,sort_keys=True)
    f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k != 'current_inputs'},indent=2))
