"""Read retained run9 evidence; write only this dossier's reconciliation.

No provider streams, credentials, model execution, store repair, or transitions.
This is historical evidence analysis, not a replacement deadline implementation.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import time
from datetime import datetime, timedelta, timezone

from baton_v12.authority import Authority

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
REC = HERE.parent.parent
RUN = Path('/home/sl/.local/state/baton/v12/w71879-run9')
UUID = 'c71879b3000000000000000000000001'
VERIFICATION = 'judgment-4a8cf8b5dda2a25dce32b469cb0f43bfe6a7ee60a4b03de6dc25c10ad0c9851d'


def read(path, limit=65536):
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        child = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        try:
            assert stat.S_ISREG(os.fstat(child).st_mode)
            with os.fdopen(child, 'rb', closefd=False) as stream:
                raw = stream.read(limit + 1)
            assert len(raw) <= limit
            return raw
        finally:
            os.close(child)
    finally:
        os.close(descriptor)


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def main():
    began = time.monotonic()
    sources = {}

    def document(path, copy=None):
        raw = read(path)
        sources[str(path)] = {'sha256': sha(raw), 'bytes': len(raw)}
        if copy:
            (HERE / copy).write_bytes(raw)
        return json.loads(raw)

    result = document(RUN / 'evidence/run-result.json', 'run-result.json')
    raw = read(RUN / 'evidence/samples.jsonl', 128 * 1024 * 1024)
    sources[str(RUN / 'evidence/samples.jsonl')] = {'sha256': sha(raw), 'bytes': len(raw)}
    samples = [json.loads(line) for line in raw.splitlines()]
    transitions = []
    previous = None
    for number, sample in enumerate(samples, 1):
        states = {stage['stage_id']: stage['state'] for job in (sample['status'] or {}).get('jobs', []) for stage in job['stages']}
        if states != previous:
            transitions.append({'sample': number, 'wall_seconds': sample['wall_seconds'], 'states': states})
            previous = states
    assert previous['job-a/integration'] == 'completed'
    assert previous['job-b/integration'] == 'claimed'
    write('sample-transitions.json', transitions)
    write('last-status.json', samples[-1]['status'])
    with Authority.open_readonly(str(RUN / 'authority.sqlite3'), expected_authority_uuid=UUID) as authority:
        claims = {name: {'current': authority.assignment_of(UUID[:8] + '-W' + str(index)),
                         'events': authority.assignment_events(UUID[:8] + '-W' + str(index))}
                  for index, name in enumerate(('a', 'b', 'verification', 'review', 'approval'), 1)}
    write('authority-assignments.json', claims)
    subject_path = RUN / 'state/result-judgments/91bfaeed0719be803da08ea598ea892453a4bdaff4933e026f6c8dbb945b1f62/subject.json'
    subject = document(subject_path, 'subject.json')
    judge_reports = {}
    for kind, attempt in (('review', 'judgment-7726d393de3e99b7d953d0c6a35f29c59b4ce0bbe1ed4c7e542a162d21d94845'),
                          ('approval', 'judgment-78e5208870d271ecf6b6153ba7e92911b100d3695cf11735c591c5b27118b177')):
        home = RUN / 'storage' / attempt / 'custody' / attempt
        sealed = document(home / 'sealed.json', kind + '-sealed.json')
        report = document(home / 'findings/report.json', kind + '-report.json')
        findings = next(one for one in sealed['outputs'] if one['name'] == 'findings')
        entry = next(one for one in findings['content_manifest']['entries'] if one['path'] == 'report.json')
        raw_report = read(home / 'findings/report.json')
        assert sha(raw_report) == entry['content_digest'] and len(raw_report) == entry['bytes']
        assert sealed['disposition'] == 'completed'
        assert sealed['assignment_ref'] == claims[kind]['events'][0]['assignment_ref']
        assert report['schema'] == 'baton.review-report/1' and report['verdict'] == 'accepted'
        assert findings['result_metadata']['baton.checkpoint-review/1'] == {
            'base': subject['source_base'], 'head': subject['candidate'], 'tree': subject['tree'], 'verdict': 'accepted'}
        assert claims[kind]['current'] is None and claims[kind]['events'][-1]['cause'] == 'pass'
        judge_reports[kind] = {'attempt_id': attempt, 'verdict': report['verdict'],
                              'frozen_at': sealed['manager_observed_at'], 'manifest_digest': sealed['manifest_digest'],
                              'report_sha256': sha(raw_report), 'pass_at': claims[kind]['events'][-1]['at']}
    events = RUN / 'launch/verification' / VERIFICATION / 'events'
    verification_events = {name: document(events / (name + '.json'), 'verification-' + name + '.json')
                           for name in ('receipt', 'state-describe', 'state-work')}
    delivered = document(RUN / 'storage' / VERIFICATION / 'inputs/judgment.json', 'verification-subject.json')
    assert delivered == dict(subject, kind='verification')
    for event in verification_events.values():
        assert event['attempt_id'] == VERIFICATION
        assert event['sequence_id'] == verification_events['receipt']['sequence_id']
        assert event['command_digest'] == verification_events['receipt']['command_digest']
    assert verification_events['state-work']['state'] == 'dispatched'
    workspace = RUN / 'storage' / VERIFICATION / 'workspace'
    workspace_names = sorted(str(path.relative_to(workspace)) for path in workspace.rglob('*') if not path.is_dir())
    assert not workspace_names
    assert not (events / 'terminal.json').exists()
    assert not (RUN / 'storage' / VERIFICATION / 'custody' / VERIFICATION / 'sealed.json').exists()
    stopped = result['exceptional_stops'][0]['argv'][-1]
    last_runtime = next(row for row in samples[-1]['runtime_observations'] if row['Id'] == stopped)
    assert last_runtime['Config']['Labels']['baton.v12.runtime_attempt_id'] == VERIFICATION
    assert last_runtime['Config']['Labels']['baton.v12.authority_uuid'] == UUID
    # Standalone direct Docker observations are retained by the managed tool boundary.
    runtime = json.loads((HERE / 'retained-containers.json').read_text())
    assert runtime and not any(row['state']['Running'] for row in runtime)
    verification_runtime = next(row for row in runtime if row['id'] == stopped)
    assert verification_runtime['state']['ExitCode'] == 137 and not verification_runtime['state']['OOMKilled']
    write('retained-containers.json', runtime)
    start = stamp(claims['b']['events'][-1]['at'])
    deadline = start + timedelta(seconds=120)
    judge_start = stamp(claims['verification']['events'][0]['at'])
    accounting = {
        'b_integration_claim': start.isoformat(), 'old_integration_deadline': deadline.isoformat(),
        'verification_claim': judge_start.isoformat(), 'verification_180s_deadline': (judge_start + timedelta(seconds=180)).isoformat(),
        'verification_age_at_old_deadline_seconds': (deadline - judge_start).total_seconds(),
        'verification_own_remaining_at_old_deadline_seconds': 180 - (deadline - judge_start).total_seconds(),
        'a_integration_claim_to_pass_seconds': (stamp(claims['a']['events'][-1]['at']) - stamp(claims['a']['events'][-2]['at'])).total_seconds(),
        'proposed_non_judge_charge_at_old_deadline_seconds': (judge_start - start).total_seconds(),
        'counterfactual_only': 'Interval subtraction at the historical deadline does not establish eventual verification acceptance or import completion.'}
    for kind in ('review', 'approval'):
        accounting[kind + '_claim_to_pass_seconds'] = (stamp(claims[kind]['events'][-1]['at']) - stamp(claims[kind]['events'][0]['at'])).total_seconds()
    assert accounting['verification_age_at_old_deadline_seconds'] == 119.842
    assert accounting['proposed_non_judge_charge_at_old_deadline_seconds'] == 0.158
    write('timing.json', accounting)
    custody = json.loads((REC / 'evidence/run9-freeze-150125/candidate-manifest.json').read_text())['files']
    for name, expected in custody.items():
        raw = read(REPO / name, 16 * 1024 * 1024)
        assert sha(raw) == expected['sha256'] and len(raw) == expected['bytes'], name
    for name, expected in (('selected-images.json', 'sha256:d0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f'),
                           ('execution-review.json', 'sha256:a91d806c71c07e344698569dd44522f80775c888ac2d28606dc519ef448beeb9')):
        assert sha(read(REC / 'prepared-150007' / name, 1024 * 1024)) == expected
    write('source-bindings.json', sources)
    elapsed = time.monotonic() - began
    summary = {'observed_at': datetime.now(timezone.utc).isoformat(), 'samples': len(samples),
               'last_sample_wall_seconds': samples[-1]['wall_seconds'], 'judgments': judge_reports,
               'verification_workspace_names': workspace_names, 'retained_containers': len(runtime), 'running_containers': 0,
               'accepted_candidate_files_unchanged': len(custody), 'markers_unchanged': 2,
               'run9_wall_seconds': result['wall_seconds'], 'nine_failed_attempt_walls_seconds': 1593.8314001880208 + result['wall_seconds'],
               'this_analysis_seconds': elapsed, 'prior_preparation_seconds': 50.14386868789525,
               'cumulative_preparation_and_analysis_seconds': 50.14386868789525 + elapsed,
               'cost_limits': 'Additional untimed reads, one failed coordinator read, host/model billing and earlier rounding remain unmeasured; no model work executed by this script.',
               'limits': 'Retained sealed-file consistency and public Authority pass corroborate reports; coordinator read failed separately. No current intake/coordinator state or eventual verification outcome inferred.'}
    write('summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
