"""Deterministic shared-output proof. No engine, provider, install or Git process.

The real Claude adapter and worker/host output owners run. Git subprocesses
are a closed replay: this proves output composition, NOT Git transport validity,
live provider behavior, runtime cleanup, or independent acceptance of a guide.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
import prepare

sys.path[:0] = [str(prepare.ROOT / 'v12/worker'), str(prepare.ROOT / 'v12/python/src/baton_v12')]
import claude_agent as agent
import baton_worker as worker
from baton_v12.contracts import ContractRefusal, check_manifest_structure, digest
from baton_v12.worker_manager import sealing, output, intake
from baton_v12.job_manager import review_driver
from baton_v12.integration import driver

UUID = '37068800370688003706880037068800'
HEAD = 'a' * 40
TREE = 'b' * 40
PATH = 'v12/TEMPLATE-JOBS.md'
GUIDE = (prepare.CHILD / 'fixtures/qualifying-TEMPLATE-JOBS.md').read_bytes()


class Replay:
    """Closed process capability: real verification; simulated provider and Git."""
    def __init__(self, role, base, report=True):
        self.role, self.base, self.report = role, base, report
        self.edited = self.committed = False
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append(argv[0])
        if argv[0] == 'git':
            args = argv[argv.index('-C') + 2:]
            while args[0] == '-c':
                args = args[2:]
            op, raw = args[0], ''
            if op == 'rev-parse':
                ref = args[-1]
                raw = TREE if ref == 'HEAD^{tree}' else self.base if ref == 'HEAD^' or ref.startswith(self.base) else HEAD if self.committed or self.role == 'review' else self.base
            elif op == 'status':
                raw = ' M ' + PATH + '\0' if self.edited and not self.committed else ''
            elif op in ('ls-files', 'add', 'merge-base'):
                pass
            elif op == 'commit':
                self.committed = True
            elif op == 'diff':
                raw = 'M\0' + PATH + '\0' if '--name-status' in args else PATH + '\0' if '--name-only' in args else 'deterministic patch fixture\n'
            elif op == 'check-attr':
                raw = PATH + '\0filter\0unspecified\0'
            elif op == 'ls-tree':
                raw = '100644 blob ' + HEAD + '\t' + PATH + '\0'
            elif op == 'cat-file':
                raw = (HEAD + ' blob ' + str(len(GUIDE)) + '\0').encode() + GUIDE + b'\0'
            elif op == 'bundle':
                Path(args[-2]).write_bytes(b'SIMULATED object transport; not a Git bundle\n')
            else:
                raise AssertionError('unselected Git replay operation: ' + repr(args))
            return subprocess.CompletedProcess(argv, 0, raw, '')
        if argv[0] == 'claude':
            if self.role == 'implementation':
                target = Path(kwargs['cwd']) / PATH
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(GUIDE)
                self.edited = True
            elif self.report:
                (Path(kwargs['cwd']) / agent.REVIEW_REPORT).write_text(json.dumps({
                    'schema': agent.REVIEW_REPORT_SCHEMA, 'verdict': 'accepted',
                    'findings': 'SIMULATED provider verdict for shared-output contract only.'}))
            os.write(kwargs['stdout'], b'{"type":"result","subtype":"success","is_error":false}\n')
            return subprocess.CompletedProcess(argv, 0)
        # Only the exact selected verification argv is allowed to run.
        assert list(argv) == self.verification, argv
        return subprocess.run(argv, **kwargs)


def refused(action, kind=(ContractRefusal, agent.TaskRefusal, worker.WorkerFault)):
    try:
        action()
    except kind as error:
        return str(error)
    raise AssertionError('expected refusal')


def run_role(packet, root, role, report=True):
    document = packet['document']
    lane = next(w for w in document['workers'] if w['role'] == role)
    manifest = lane['deployment']['input_manifest']
    task = json.loads(packet['task_bytes'])
    home = root / (role if report else 'review-no-report')
    home.mkdir()
    (home / 'scratch').mkdir()
    inputs, outputs, credentials = [home / name for name in ('input', 'output', 'credentials')]
    for place in (inputs, outputs, credentials):
        place.mkdir()
    (inputs / agent.TASK_DOCUMENT).write_text(packet['task_bytes'])
    (credentials / 'claude').write_text('not-a-credential')
    (outputs / '.git').mkdir()  # inert replay directory; never a Git repository
    (outputs / 'v12').mkdir()
    (outputs / 'v12/python').symlink_to(prepare.ROOT / 'v12/python')
    (inputs / task['source_root']).mkdir()
    replay = Replay(role, task['declared_base'], report)
    replay.verification = task['verification']
    with patch.object(agent, 'INPUT_ROOT', str(inputs)), patch.object(agent, 'OUTPUT_ROOT', str(outputs)), patch.object(agent, 'CREDENTIAL_ROOT', str(credentials)), patch.object(worker, 'OUTPUT_ROOT', str(outputs)):
        impl = agent.ClaudeAgent(run=replay, home=str(home / 'scratch'))
        answer = impl.work({'role': role}, manifest['outputs'])
        measured = worker.answered(manifest['outputs'], answer['outputs'])
        assignment = {'work_ref': manifest['work_ref'], 'participant': lane['participant'], 'generation': 1}
        completion = worker.publish_completion(assignment, answer['disposition'], measured)
        # Missing present output and lying about an optional output remain refusals.
        absent = next(one for one in answer['outputs'] if one['status'] == 'missing-optional')
        lied = copy.deepcopy(answer['outputs'])
        next(one for one in lied if one['name'] == absent['name'])['status'] = 'present'
        missing_refusal = refused(lambda: worker.answered(manifest['outputs'], lied))
        required_declarations = copy.deepcopy(manifest['outputs'])
        next(one for one in required_declarations if one['name'] == absent['name'])['required'] = True
        worker_required_refusal = refused(lambda: worker.answered(required_declarations, answer['outputs']))
    check_manifest_structure(completion, 'completionManifest', what='worker completion')
    request = {'attempt_id': home.name, 'assignment': assignment,
               'disposition': answer['disposition'], 'now': '2026-10-28T03:00:00.000Z',
               'operation': {'operation_id': 'freeze-' + home.name, 'signature_digest': digest(assignment)}}
    custody = str(home / 'custody')
    frozen = sealing.sealed_result(request, roots={'workspace': str(outputs)},
                                  declared=sealing.declared_outputs(manifest['outputs']),
                                  identity=lane['deployment'], custody=custody,
                                  input_manifest_digest=manifest['manifest_digest'])
    check_manifest_structure(frozen, 'resultManifest', what='frozen result')
    output._compare_declared(manifest, frozen, home.name)
    required_manifest = copy.deepcopy(manifest)
    required_manifest['outputs'] = required_declarations
    host_required_refusal = (refused(lambda: output._compare_declared(required_manifest, frozen, home.name))
                             if answer['disposition'] == 'completed' else 'unable result may preserve partial evidence')
    if role == 'review' and report:
        text_only = copy.deepcopy(manifest)
        next(one for one in text_only['outputs'] if one['name'] == 'findings')['constraints']['allowed_media_types'] = ['text/plain']
        media_refusal = refused(lambda: output._compare_declared(text_only, frozen, home.name))
    else:
        media_refusal = None
    collected = sealing.collected_result({
        'attempt_id': home.name, 'assignment': assignment, 'result_id': frozen['result_id'],
        'result_manifest_digest': frozen['manifest_digest'],
        'output_names': [one['name'] for one in manifest['outputs']],
        'operation': {'operation_id': 'collect-' + home.name, 'signature_digest': digest(assignment)}},
        custody=custody, declared=sealing.declared_outputs(manifest['outputs']))
    summary = {'result_id': frozen['result_id'], 'artifacts': [one['artifact'] for one in frozen['outputs'] if one['artifact']]}
    intake._compared(collected, summary, home.name)
    altered = copy.deepcopy(collected)
    altered['artifacts'][0]['bytes'] += 1
    mismatch = refused(lambda: intake._compared(altered, summary, home.name))
    if role == 'implementation':
        proposal = next(one for one in frozen['outputs'] if one['name'] == 'proposal')
        claim = driver._claim_of(proposal)
        damaged = copy.deepcopy(proposal)
        damaged['result_metadata'] = {}
        required = refused(lambda: driver._claim_of(damaged))
    elif report:
        claim = review_driver._review_claim(frozen)
        damaged = copy.deepcopy(frozen)
        next(one for one in damaged['outputs'] if one['name'] == 'logs')['status'] = 'missing-optional'
        required = refused(lambda: review_driver._review_claim(damaged))
        malformed = copy.deepcopy(frozen)
        next(one for one in malformed['outputs'] if one['name'] == 'findings')['result_metadata'][agent.REVIEW_CLAIM_NAMESPACE]['verdict'] = 'looks-good'
        refused(lambda: review_driver._review_claim(malformed))
    else:
        claim = None
        required = refused(lambda: review_driver._review_claim(frozen))
    return {'answer': answer, 'frozen': frozen, 'collected': collected,
            'claim': claim, 'mandatory_role_result_refusal': required,
            'missing_present_output_refusal': missing_refusal,
            'worker_required_output_refusal': worker_required_refusal,
            'host_required_output_refusal': host_required_refusal,
            'text_only_findings_refusal': media_refusal,
            'collection_mismatch_refusal': mismatch,
            'subprocess_boundaries': replay.calls}


def main():
    started = time.monotonic()
    root = Path(tempfile.mkdtemp(prefix='w370688-proof-', dir='/tmp'))
    packet = prepare.compose(UUID, '/tmp/w370688-fixture-destination')
    assert prepare.compose(UUID, '/tmp/w370688-fixture-destination') == packet
    # Change only live canonical record reads, never repository files. The
    # selected snapshots must keep the entire composition byte-identical.
    original_read = Path.read_bytes
    live = {prepare.HERE / name for name in prepare.DECISION_PINS}
    def evolving(path):
        raw = original_read(path)
        return raw + b'\nReviewer checkpoint evolved.\n' if path in live else raw
    with patch.object(Path, 'read_bytes', evolving):
        assert prepare.compose(UUID, '/tmp/w370688-fixture-destination') == packet
    decision_refusals = {}
    for name in prepare.DECISION_PINS:
        selected = prepare.DECISION_INPUTS / name
        def changed(path):
            raw = original_read(path)
            return raw + b'\nUnreviewed change.\n' if path == selected else raw
        with patch.object(Path, 'read_bytes', changed):
            decision_refusals[name] = refused(lambda: prepare.compose(UUID, '/tmp/w370688-fixture-destination'), (ValueError,))
    old = prepare.capacity.compose(UUID, destination='/tmp/w370688-fixture-destination', proposed_grants=True)
    assert packet['task_bytes'] == old['task_bytes']
    assert packet['task_sha256'] == 'c21e6b93bfe199ebb89b3ec7a75e70a5636c52f9986b1afa3709a381c6bd98d7'
    for before, after in zip(old['document']['workers'], packet['document']['workers']):
        left, right = copy.deepcopy(before), copy.deepcopy(after)
        a = left['deployment'].pop('input_manifest')
        b = right['deployment'].pop('input_manifest')
        assert left == right
        for key in ('outputs', 'record_binding', 'manifest_digest'):
            a.pop(key)
            b.pop(key)
        assert a == b
    refused(lambda: prepare.compose(UUID, prepare.capacity.DESTINATION), (ValueError,))
    manifests = [w['deployment']['input_manifest'] for w in packet['document']['workers']]
    assert manifests[0] == manifests[1]
    declarations = manifests[0]['outputs']
    negatives = {}
    for role, names in [('implementation', agent.IMPLEMENTATION_OUTPUTS), ('review', agent.REVIEW_OUTPUTS)]:
        for other in {one['name'] for one in declarations} - set(names):
            bad = copy.deepcopy(declarations)
            next(one for one in bad if one['name'] == other)['required'] = True
            negatives[role + '-requires-' + other] = refused(lambda: agent._selected(bad, names, role))
    roles = {role: run_role(packet, root, role) for role in ('implementation', 'review')}
    no_report = run_role(packet, root, 'review', report=False)
    assert roles['implementation']['answer']['disposition'] == 'completed'
    assert roles['review']['answer']['disposition'] == 'completed'
    assert no_report['answer']['disposition'] == 'unable'
    result = {'schema': 'baton.shared-output-proof/1', 'passed': True,
              'fixture_only': True, 'scratch_retained': str(root),
              'seconds': time.monotonic() - started,
              'packet': packet, 'roles': roles, 'review_without_report': no_report,
              'required_other_role_refusals': negatives,
              'decision_inputs': {'identical_composition_reproduces': True,
                                  'live_record_evolution_changes_nothing': True,
                                  'selected_snapshot_drift_refusals': decision_refusals},
              'limits': ['Git and provider process responses simulated',
                         'transport fixture is not a valid Git bundle',
                         'no manager scheduling, installation, engine, native verdict or runtime cleanup claimed',
                         'real adapter, selected verification command, completion, seal, collection and role claim readers exercised']}
    print(json.dumps(result, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
