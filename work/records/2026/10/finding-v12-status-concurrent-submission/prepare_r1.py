"""W319114 R1 packet preparation only. Never starts a runtime or provider.

THE ONE THING THAT IS DIFFERENT from `prepare.py` beside it: the worker's
declared base is the RETAINED CANDIDATE aa637298b rather than the repository
baseline 9055843b. Review 2026-10-18T02-54-37Z accepted the candidate's
coherence work and requested one correction, so re-deriving it from the baseline
would spend a provider grant redoing accepted work. `source` reconstructs that
commit from the digest-bound bundle in this dossier plus the host repository, and
refuses unless the reconstruction's own HEAD, tree and file digests match the
sealed pins.

NOTHING HERE MUTATES THE HOST REPOSITORY. The reconstruction is a clone into the
fresh external root; the bundle is fetched into that clone. The host repository
is read and never written, and no commit is created anywhere by this script.

stage freezes manager code, reconstructs the candidate source and emits
installation inputs; bind runs only after the supported bootstrap has minted the
isolated execution authority. Product composition and the single-implementation
supervisor are reused unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
# THE RETAINED CANDIDATE, and its parent is the repository baseline.
BASE = 'aa637298bac292058b659df5d147fbddd82c49a6'
BASE_PARENT = '9055843b5d258f5bfbb523815d034ee0c14075d6'
BASE_TREE = '57f5d49cc89fd543345eddf84cb2a95f03eecfd0'
RUN = 'status-race-r1-w319114-319624'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
BUNDLE = HERE / 'evidence/diagnosis-319578/proposal/objects.bundle'
RETENTION = 'sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a'
INTEGRATION = dict(profile_kind='git', profile_version=1, integrator_participant='baton.merge', instructions_digest='sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2')
RECEIPTS = dict(verification='baton.verifier', review='baton.approver-review', approval='baton.approver')
VERIFICATION = ['python3', '-c', "import os,sys,unittest; os.chdir('v12/python'); sys.path[:0]=[os.getcwd(),os.path.join(os.getcwd(),'src')]; import jsonschema; s=unittest.defaultTestLoader.loadTestsFromNames(['tests.job_manager.test_status','tests.job_manager.test_store_readonly']); r=unittest.TextTestRunner(verbosity=1).run(s); sys.exit(not r.wasSuccessful())"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(argv, where=None):
    """One closed command, refused loudly rather than half-performed."""
    done = subprocess.run(argv, cwd=where, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError('preparation command failed: ' + ' '.join(argv)
                           + '\n' + done.stdout + done.stderr)
    return done.stdout.strip()


def pins():
    """Every reused input, and this packet's own, verified before anything runs."""
    mine = json.loads((HERE / 'PINS-319624.json').read_text())
    for name, expected in mine['reused_preparation_pins'].items():
        if sha(REPO / name) != expected:
            raise RuntimeError('reused preparation pin drifted: ' + name)
    doc = json.loads((HERE / 'PREPARATION-PINS.json').read_text())
    for name, expected in doc['files'].items():
        if sha(REPO / name) != expected:
            raise RuntimeError('selected preparation input drifted: ' + name)
    # Both groups are named relative to THIS DOSSIER, which is the only root
    # that stays correct however the record is relocated.
    for group in ('candidate_evidence', 'review_inputs'):
        for name, expected in mine[group].items():
            if sha(HERE / name) != expected:
                raise RuntimeError('pinned ' + group + ' drifted: ' + name)
    if sha(Path(DISTRO) / 'baton-v12-stack') != doc['historical_bootstrap_binary_sha256']:
        raise RuntimeError('historical bootstrap binary drifted')
    if mine['base'] != BASE or mine['base_tree'] != BASE_TREE:
        raise RuntimeError('this script and its pins disagree about the base')
    return doc, mine


def reconstruct(root):
    """The candidate commit, rebuilt from the host repository and the bundle.

    THE HOST REPOSITORY IS READ AND NEVER WRITTEN. The clone is a new repository
    inside the fresh external root, the bundle is fetched into that clone, and no
    commit is created anywhere. This is the step an AUTHORIZED OPERATOR runs:
    repository agents do not perform Git operations that write, even into a
    disposable clone, so `--source reconstruct` is never selected by a preparing
    agent. See `verified` for what is checked either way.

    A REAL BRANCH RATHER THAN A DETACHED HEAD, because the manager clones this
    source with `--no-local`: the git transport only transfers what a ref
    advertises, so the candidate has to be on one.
    """
    source = root / 'source'
    run(['git', 'clone', '--no-hardlinks', '--quiet', str(REPO), str(source)])
    run(['git', '-C', str(source), 'fetch', '--quiet', str(BUNDLE),
         'HEAD:refs/heads/candidate'])
    run(['git', '-C', str(source), 'checkout', '--quiet', 'candidate'])
    return source


def verified(source, selected):
    """The source IS the sealed candidate, whoever produced it.

    ONE GATE FOR BOTH ROUTES, which is why `--source` may name an existing
    checkout. A reconstruction and an already-retained checkout are
    interchangeable only if they are proved identical, so HEAD, the tree, the
    parent, worktree cleanliness and every pinned file digest are checked here
    rather than inside whichever branch produced the directory. Anything that
    differs is not the reviewed checkpoint and must not become a worker's base.
    """
    source = Path(source)
    head = run(['git', '-C', str(source), 'rev-parse', '--verify', 'HEAD'])
    tree = run(['git', '-C', str(source), 'rev-parse', '--verify', 'HEAD^{tree}'])
    parent = run(['git', '-C', str(source), 'rev-parse', '--verify', 'HEAD^'])
    if head != BASE or tree != BASE_TREE or parent != BASE_PARENT:
        raise RuntimeError('this source is not the sealed candidate: '
                           f'head={head} tree={tree} parent={parent}')
    if run(['git', '-C', str(source), 'status', '--porcelain']):
        raise RuntimeError('the candidate worktree is not clean')
    for name, expected in selected['candidate_fixture_files'].items():
        if sha(source / name) != expected:
            raise RuntimeError('candidate file drifted: ' + name)
    return source


def stage(root, source):
    doc, selected = pins()
    if source != 'reconstruct':
        held = Path(source)
        if not held.is_absolute() or not (held / '.git').exists():
            raise RuntimeError('--source names `reconstruct` or one absolute '
                               'existing Git checkout of the sealed candidate')
    if not root.is_absolute() or root == REPO or REPO in root.parents:
        raise RuntimeError('select a fresh absolute external preparation root')
    root.mkdir(mode=0o700)  # refuse reuse, including symlinks
    code = root / 'code/v12/python'
    for relative, expected in doc['manager_files'].items():
        origin = REPO / 'v12/python' / relative
        if sha(origin) != expected:
            raise RuntimeError('manager source drifted: ' + relative)
        target = code / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
        if sha(target) != expected:
            raise RuntimeError('staged source mismatch: ' + relative)
    reconstructed = source == 'reconstruct'
    source = verified(reconstruct(root) if reconstructed else source, selected)
    instance = root / 'instance'
    emit(root / 'bootstrap-inputs.json', dict(
        schema='baton.v12.stack-bootstrap/1', state_root=str(instance / 'deployment-state'),
        checkpoint_profile='git', integration_profile=INTEGRATION,
        retention_policy_digest=RETENTION, retention_disposition='retain',
        pool_generation=1, policy_generation=1, receipt_participants=RECEIPTS))
    emit(root / 'stage.json', dict(
        run_id=RUN, base=BASE, base_parent=BASE_PARENT, base_tree=BASE_TREE,
        manager_files=doc['manager_files'], source=str(source),
        source_route='reconstructed' if reconstructed else 'supplied',
        host_repository=str(REPO), bundle=str(BUNDLE), instance=str(instance),
        candidate_fixture_files=selected['candidate_fixture_files']))
    print('staged; candidate source verified at', BASE)
    print('source', '(reconstructed)' if reconstructed else '(supplied)', source)
    print('bootstrap separately with --no-repositories, then bind')


def bind(root):
    doc, selected = pins()
    staged = json.loads((root / 'stage.json').read_text())
    code = root / 'code/v12/python'
    for relative, expected in staged['manager_files'].items():
        if sha(code / relative) != expected:
            raise RuntimeError('staged manager drifted: ' + relative)
    # THE SOURCE IS RE-VERIFIED HERE TOO, by the same gate, because stage and
    # bind are separate operator commands with a bootstrap between them.
    source = verified(staged['source'], selected)
    sys.path[:0] = [str(code / 'src'), str(code), str(OLD)]
    from baton_v12.authority import Authority
    import baseline_bindings
    import baseline
    import prepare_instance
    uuid = json.loads((root / 'instance/bootstrap.json').read_text())['authority_uuid']
    db = root / 'instance/db'
    image = json.loads((OLD / 'IMAGE-ARTIFACT-244216.json').read_text())
    instance = dict(authority_store=str(db / 'authority.sqlite3'), authority_uuid=uuid,
                    job_store=str(db / 'jobs.sqlite3'), control_store=str(db / 'control.sqlite3'),
                    integration_store=str(db / 'integration.sqlite3'), integration_profile=INTEGRATION,
                    retention_policy_digest=RETENTION, runtime_path=DISTRO,
                    build_commit='1e576ff2186db69e8b44da9d38874ff7e99ebbe3')
    participants = dict(implementation='baton.impl', implementation_principal='principal:baton.impl',
                        review='baton.review', review_principal='principal:baton.review',
                        receipts=RECEIPTS, work_id=uuid[:8] + '-W1',
                        worker_files=image['all_worker_files'],
                        # PINNED AT THE CANDIDATE'S BYTES, not the repository's.
                        # The supervisor verifies these under the nominated
                        # source, so a packet pointed at the wrong tree refuses
                        # here rather than inside a provider turn.
                        fixture_files=dict(selected['candidate_fixture_files']))
    with Authority.open(instance['authority_store'], expected_authority_uuid=uuid) as authority:
        prepare_instance.prepare(authority, dict(participants=participants, instance=instance),
                                 base=BASE, operation_id=RUN + '-prepare')
        participants['implementation_principal'] = authority.principal_of('baton.impl')
        participants['review_principal'] = authority.principal_of('baton.review')
    bounds = selected['bounds']
    docs = baseline_bindings.compose(
        instance=instance, run_root=str(root / 'packet'), source_root=str(source), base=BASE,
        image_reference=image['reference'], image_digest=image['image_config_digest'],
        cli_build='2.1.247', manager_source=str(code), supervisor_path=str(OLD / 'baseline.py'),
        vectors=str(VECTORS), participants=participants,
        credential_sources='/home/sl/.baton/credential-sources.json',
        credential_profile={'claude': {'provider': 'operator-file', 'reference': 'w202663-development'}},
        evidence_digest='sha256:' + sha(REPO / 'work/records/2026/09/finding-v12-real-jobs-adoption-gate/review-2026-09-29T16-58-33Z.md'),
        provider_network='bridge', run_id=RUN, work='W319114', claim=319624,
        note='One bounded R1 correction on the retained reviewed candidate; retained proposal requires separate baton.rvpc review; no automatic integration.',
        bounds=dict(turn_seconds=bounds['turn_seconds'], total_seconds=bounds['total_seconds'],
                    cleanup_seconds=bounds['cleanup_seconds'],
                    implementer_invocations=bounds['implementer_invocations'],
                    retry=bounds['retry']),
        context_mode='fresh', task_instructions=(HERE / 'TASK-319624.md').read_text(),
        verification=VERIFICATION)
    places = baseline_bindings.write(str(root / 'packet'), docs)
    baseline.held_packet(places['PACKET.json'])
    baseline.verify_imported_sources(docs['PACKET.json'])
    emit(root / 'PREPARED.json', dict(state='prepared-not-executed', work='W319114',
        claim=319624, run_id=RUN, base=BASE, base_parent=BASE_PARENT, base_tree=BASE_TREE,
        nominated_source=str(source), authority_uuid=uuid,
        packet_sha256=sha(places['PACKET.json']),
        artifacts={name: sha(path) for name, path in places.items()},
        independent_review='baton.rvpc consumes immutable retained proposal through v11 after exact runtime cessation; no automatic acceptance'))
    print('prepared and validated; no job submitted, no engine/provider invoked')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('step', choices=['stage', 'bind'])
    parser.add_argument('--root', required=True)
    # EXPLICIT AND REQUIRED FOR `stage`, never inferred. `reconstruct` is the
    # operator's route and writes a disposable clone; an absolute path is the
    # preflight route over an already-retained checkout. Both pass `verified`.
    parser.add_argument('--source')
    args = parser.parse_args()
    if args.step == 'stage':
        if not args.source:
            parser.error('stage requires --source reconstruct|<absolute checkout>')
        stage(Path(args.root), args.source)
    else:
        bind(Path(args.root))
