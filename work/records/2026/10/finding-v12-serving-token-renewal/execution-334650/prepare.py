"""W333485 preparation only; adapted from reviewed continuation329953. No launch."""
import argparse
import os
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
BASE = 'a9f4fa4da2323a357ae15aefbc5d7d22d41487b6'
RUN = 'serving-renewal-w333485-334650'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
RETENTION = 'sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a'
INTEGRATION = dict(profile_kind='git', profile_version=1,
                   integrator_participant='baton.merge',
                   instructions_digest='sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2')
RECEIPTS = dict(verification='baton.verifier', review='baton.approver-review',
                approval='baton.approver')

GATE = ['tests.job_manager.test_serving_renewal', 'tests.job_manager.test_tool', 'tests.job_manager.test_sweep', 'tests.job_manager.test_execution_limits']
VERIFICATION = ['python3', '-c',
                "import os,sys,unittest; os.chdir('v12/python'); "
                "roots=[os.getcwd(),os.path.join(os.getcwd(),'src')]; "
                "sys.path[:0]=roots; "
                "os.environ['PYTHONPATH']=os.pathsep.join(roots); "
                "names=" + json.dumps(GATE) + "; "
                "r=unittest.TextTestRunner(verbosity=1).run("
                "unittest.defaultTestLoader.loadTestsFromNames(names)); "
                "[print('SKIPPED '+str(one[0])) for one in r.skipped]; "
                "sys.exit(0 if r.wasSuccessful() and not r.skipped else 1)"]

BOUNDS = dict(turn_seconds=3600, total_seconds=4800, cleanup_seconds=60,
              implementer_invocations=1, retry=False)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def committed(relative):
    return subprocess.check_output(['git', 'show', BASE + ':' + relative],
                                   cwd=REPO)


def pins():
    doc = json.loads((HERE / 'PREPARATION-PINS.json').read_text())
    if doc['base'] != BASE:
        raise RuntimeError('the pins name another base')
    for name, expected in doc['files'].items():
        if sha(REPO / name) != expected:
            raise RuntimeError('selected preparation input drifted: ' + name)
    if sha(Path(DISTRO) / 'baton-v12-stack') \
            != doc['historical_bootstrap_binary_sha256']:
        raise RuntimeError('historical bootstrap binary drifted')
    manifest = json.loads((HERE / 'SOURCE.json').read_text())
    if manifest['base'] != BASE:
        raise RuntimeError('source manifest base mismatch')
    for name, expected in manifest['files'].items():
        if hashlib.sha256(committed(name)).hexdigest() != expected:
            raise RuntimeError('committed source drifted: ' + name)
    return doc


def stage(root):
    selected = pins()
    if not root.is_absolute() or root != root.resolve() or root == REPO or REPO in root.parents:
        raise RuntimeError('select a fresh absolute external preparation root')
    root.mkdir(mode=0o700)  # refuse reuse, including symlinks
    source = root / 'code/v12/python'
    for relative, expected in selected['manager_files'].items():
        content = committed('v12/python/' + relative)
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError('manager source drifted: ' + relative)
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if sha(target) != expected:
            raise RuntimeError('staged source mismatch: ' + relative)
    for name, expected in selected['supervisor_files'].items():
        content = committed(str(OLD.relative_to(REPO) / name))
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError('supervisor source drifted: ' + name)
        target = root / 'supervisor' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    instance = root / 'instance'
    emit(root / 'bootstrap-inputs.json', dict(
        schema='baton.v12.stack-bootstrap/1',
        state_root=str(instance / 'deployment-state'),
        checkpoint_profile='git', integration_profile=INTEGRATION,
        retention_policy_digest=RETENTION, retention_disposition='retain',
        pool_generation=1, policy_generation=1,
        receipt_participants=RECEIPTS))
    emit(root / 'stage.json', dict(run_id=RUN, base=BASE,
                                   manager_files=selected['manager_files'],
                                   source=str(REPO), instance=str(instance)))
    print('staged; bootstrap separately with --no-repositories, then bind')


def bind(root):
    selected = pins()
    if (root / 'PREPARED.json').exists() or (root / 'packet').exists():
        raise RuntimeError('refuse rebinding an existing packet')
    staged = json.loads((root / 'stage.json').read_text())
    if staged['base'] != BASE or staged['run_id'] != RUN or staged['manager_files'] != selected['manager_files']:
        raise RuntimeError('this root was staged for another run')
    source = root / 'code/v12/python'
    for relative, expected in staged['manager_files'].items():
        if sha(source / relative) != expected:
            raise RuntimeError('staged manager drifted: ' + relative)
    supervisor = root / 'supervisor'
    for name, expected in selected['supervisor_files'].items():
        if sha(supervisor / name) != expected:
            raise RuntimeError('staged supervisor drifted: ' + name)
    sys.path[:0] = [str(source / 'src'), str(source), str(supervisor)]
    from baton_v12.authority import Authority
    import baseline_bindings
    import baseline
    import prepare_instance
    uuid = json.loads((root / 'instance/bootstrap.json').read_text())['authority_uuid']
    db = root / 'instance/db'
    image = json.loads((OLD / 'IMAGE-ARTIFACT-244216.json').read_text())
    instance = dict(authority_store=str(db / 'authority.sqlite3'),
                    authority_uuid=uuid, job_store=str(db / 'jobs.sqlite3'),
                    control_store=str(db / 'control.sqlite3'),
                    integration_store=str(db / 'integration.sqlite3'),
                    integration_profile=INTEGRATION,
                    retention_policy_digest=RETENTION, runtime_path=DISTRO,
                    build_commit='1e576ff2186db69e8b44da9d38874ff7e99ebbe3')
    # THE INPUTS THE TURN CANNOT PROCEED WITHOUT, pinned as the packet's own
    # fixture so `held_packet` refuses a drifted one BEFORE any store opens.
    fixture = {name: sha(REPO / name) for name in selected['task_inputs']}
    participants = dict(
        implementation='baton.impl',
        implementation_principal='principal:baton.impl',
        review='baton.review', review_principal='principal:baton.review',
        receipts=RECEIPTS, work_id=uuid[:8] + '-W1',
        worker_files=image['all_worker_files'], fixture_files=fixture)
    with Authority.open(instance['authority_store'],
                        expected_authority_uuid=uuid) as authority:
        prepare_instance.prepare(authority,
                                 dict(participants=participants,
                                      instance=instance),
                                 base=BASE, operation_id=RUN + '-prepare')
        participants['implementation_principal'] = authority.principal_of('baton.impl')
        participants['review_principal'] = authority.principal_of('baton.review')
    docs = baseline_bindings.compose(
        instance=instance, run_root=str(root / 'packet'), source_root=str(REPO),
        base=BASE, image_reference=image['reference'],
        image_digest=image['image_config_digest'], cli_build='2.1.247',
        manager_source=str(source), supervisor_path=str(supervisor / 'baseline.py'),
        vectors=str(VECTORS), participants=participants,
        credential_sources='/home/sl/.baton/credential-sources.json',
        credential_profile={'claude': {'provider': 'operator-file',
                                       'reference': 'w202663-development'}},
        evidence_digest='sha256:' + sha(REPO / 'work/records/2026/09/finding-v12-real-jobs-adoption-gate/review-2026-09-29T16-58-33Z.md'),
        provider_network='bridge', run_id=RUN, work='W333485', claim=334650,
        note='Bounded serving token renewal; separate independent review; no automatic integration or acceptance.',
        bounds=BOUNDS, context_mode='fresh',
        task_instructions=(HERE / 'TASK.md').read_text(),
        verification=VERIFICATION)
    places = baseline_bindings.write(str(root / 'packet'), docs)
    baseline.held_packet(places['PACKET.json'])
    baseline.verify_imported_sources(docs['PACKET.json'])
    from tools import authoring_enforcement
    authoring_enforcement.verify_controller(docs['PACKET.json'])
    commands = json.loads(Path(places['commands.json']).read_text())
    commands['environment']['PYTHONPATH'] = os.pathsep.join([str(source / 'src'), str(source), str(supervisor)])
    commands['start'] = [sys.executable, '-B', '-m', 'tools.authoring_enforcement', '--packet', places['PACKET.json']]
    commands['termination'] = 'SIGINT/SIGTERM to the exact outer controller requests cancellation; unknown cessation holds; restart is recovery only, never another author invocation'
    emit(places['commands.json'], commands)
    emit(root / 'PREPARED.json', dict(
        state='prepared-not-executed', work='W333485', authority_uuid=uuid,
        packet_sha256=sha(places['PACKET.json']),
        artifacts={name: sha(path) for name, path in places.items()},
        independent_review='an independent reviewer consumes the immutable '
                           'retained proposal through v11 after exact runtime '
                           'cessation; no automatic acceptance'))
    print('prepared and validated; no job submitted, no engine/provider invoked')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('step', choices=['stage', 'bind'])
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    {'stage': stage, 'bind': bind}[args.step](Path(args.root))
