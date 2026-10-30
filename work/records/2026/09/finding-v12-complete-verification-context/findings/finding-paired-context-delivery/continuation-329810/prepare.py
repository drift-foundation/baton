"""W321776 continuation packet preparation only. Starts no runtime, no engine
and no provider, and submits no Job.

`stage` freezes the manager and supervisor source from the DECLARED BASE and
emits the installation inputs; `bind` runs only after the supported bootstrap
has minted this instance's own execution authority. The product composition and
the single-implementation supervisor are reused unchanged -- this packet selects
them, it does not re-author them.

WHY THE CHECKPOINT IS AN INPUT RATHER THAN A BASE. The reviewed Stage-A slice is
five uncommitted host files. Treating them as source would mean verifying a
candidate assembled from an unaudited tree, so they travel as digest-bound
buffers under `candidate-input/`, are pinned in the packet's own `fixture.files`
(the supervisor refuses a drifted one before anything opens), and are placed
inside the private checkout by `restore.py`, which validates every buffer and
every base file before its first write.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
BASE = 'bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c'
RUN = 'paired-context-w321776-329810'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
RETENTION = 'sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a'
INTEGRATION = dict(profile_kind='git', profile_version=1,
                   integrator_participant='baton.merge',
                   instructions_digest='sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2')
RECEIPTS = dict(verification='baton.verifier', review='baton.approver-review',
                approval='baton.approver')

# THE SEALED ACCEPTANCE GATE, and the three groups in it are there for three
# different reasons.
#
#   * the SIX NAMES OF THE 102-TEST CREDENTIAL GATE, which `PACKET.md` names as
#     the acceptance obligation and which a different passing subset may not
#     substitute for;
#   * the RESTORED CONTRACT (`test_verification_context`) and the image-recipe
#     cases that carry it, so a turn cannot deliver the views by quietly
#     rewriting the contract both views must agree on;
#   * the TWO NEW MODULES, named as a CONVENTION because a sealed argv cannot
#     name classes that do not exist yet. They do not exist at the base, so
#     this gate fails until the turn creates them -- which is the point.
#
# WHY THIS IS A `-c` PROGRAM AND NOT THE PACKET'S LITERAL ARGV. The accepted
# packet's literal argv assumes a working directory and a derived PYTHONPATH,
# and BOTH come from `verification_context` -- a `/3` member. The launch
# envelope is `/2`, which carries no such member, and the argv carries no
# environment assignment, so under `/2` the command must establish its own cwd
# and import path. The literal argv remains the `/3` obligation, exercised in
# the two views the turn produces.
GATE = [
    'tests.manager.test_verification_context',
    'tests.manager.test_verification_views',
    'tests.tools.test_operator_verification_view',
    'tests.manager.test_claude_agent.TheRecipeIsInspectableWithoutADaemon',
    'tests.tools.test_user_credentials',
    'tests.tools.test_dogfood_operator.TheDocumentedCommandIsOneGrantsFile.test_help_names_the_credential_source_the_launcher_requires',
    'tests.tools.test_dogfood_operator.ThePublicRecoveryEndsAnInterruptedAttempt.test_a_recovery_asks_for_no_credential',
    'tests.tools.test_dogfood_operator.TheArcMaterializesBetweenActivationAndRuntimeCreation.test_the_factory_runs_after_activation_and_before_runtime_start',
    'tests.tools.test_dogfood_operator.TheDocumentedRecoveryEndsRealAttachedState.test_an_uncertain_runtime_settles_nothing_and_keeps_the_bearer',
    'tests.manager.test_credentials.TheTrustedProfileMapsEverySlot.test_the_reference_is_opaque',
]
VERIFICATION = ['python3', '-c',
                "import os,sys,unittest; os.chdir('v12/python'); "
                "sys.path[:0]=[os.getcwd(),os.path.join(os.getcwd(),'src')]; "
                "names=" + json.dumps(GATE) + "; "
                "r=unittest.TextTestRunner(verbosity=1).run("
                "unittest.defaultTestLoader.loadTestsFromNames(names)); "
                "[print('SKIPPED '+str(one[0])) for one in r.skipped]; "
                "sys.exit(0 if r.wasSuccessful() and not r.skipped else 1)"]

# VER-5 ADMITS NO SKIP. A skipped case in this gate is an unproven obligation
# wearing a passing exit status, so the program refuses one and prints which.

BOUNDS = dict(turn_seconds=900, total_seconds=1500, cleanup_seconds=60,
              implementer_invocations=1, retry=False)
VERIFICATION_SECONDS = 30
# CARRIED FROM THE ACCEPTED PACKET'S OWN TABLE, as a selection rather than a
# correctness claim. OPERATOR.md records the tension honestly: the comparable
# implementation Job in this campaign (W321528) selected 3600s and still spent
# its turn, so the owner may raise these before selecting execution. They are
# not raised here, because the accepted packet proposed them and raising an
# accepted bound is the owner's act.


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
    # THE LOAD COMMAND IS ONE STRING IN TWO PLACES, so the two are compared
    # rather than trusted: an instruction naming a digest the file does not
    # have is an instruction the agent cannot satisfy.
    load = (HERE / 'LOAD-COMMAND.txt').read_text().strip()
    if load not in (HERE / 'TASK.md').read_text():
        raise RuntimeError('the task does not carry the exact load command')
    if sha(HERE / 'restore.py') not in load:
        raise RuntimeError('the load command names other restore bytes')
    provenance = json.loads((HERE / 'PROVENANCE.json').read_text())
    if provenance['base'] != BASE or provenance['accepted'] is not False:
        raise RuntimeError('the provenance disagrees with this preparation')
    for name, declared in provenance['checkpoint']['paths'].items():
        if sha(HERE / 'candidate-input' / name) != declared['restored_sha256']:
            raise RuntimeError('preserved buffer drifted: ' + name)
        # A FILE THE BASE DOES NOT CARRY IS THE EXPECTED ANSWER for the two new
        # ones, so the absence probe is quiet on purpose: its stderr would read
        # as a fault in the one case the declaration predicts.
        try:
            held = hashlib.sha256(subprocess.check_output(
                ['git', 'show', BASE + ':' + name], cwd=REPO,
                stderr=subprocess.DEVNULL)).hexdigest()
        except subprocess.CalledProcessError:
            held = None
        if held != declared['base_sha256']:
            raise RuntimeError('the base no longer holds the declared bytes '
                               'for ' + name)
    return doc


def stage(root):
    selected = pins()
    if not root.is_absolute() or root == REPO or REPO in root.parents:
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
    staged = json.loads((root / 'stage.json').read_text())
    if staged['base'] != BASE or staged['run_id'] != RUN:
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
        provider_network='bridge', run_id=RUN, work='W321776', claim=329810,
        note='Paired worker and operator verification views, continuing the '
             'preserved Stage-A checkpoint as digest-bound input; retained '
             'proposal requires separate independent review; no automatic '
             'integration and no acceptance.',
        bounds=BOUNDS, context_mode='fresh',
        task_instructions=(HERE / 'TASK.md').read_text(),
        verification=VERIFICATION)
    places = baseline_bindings.write(str(root / 'packet'), docs)
    baseline.held_packet(places['PACKET.json'])
    baseline.verify_imported_sources(docs['PACKET.json'])
    emit(root / 'PREPARED.json', dict(
        state='prepared-not-executed', work='W321776', authority_uuid=uuid,
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
