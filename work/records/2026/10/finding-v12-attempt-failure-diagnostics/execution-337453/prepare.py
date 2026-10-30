"""W333486 execution preparation only, at the corrected manager-guard checkpoint.

Supersedes `../execution-333504`, `../execution-333707` and
`../execution-334663`, all preserved unchanged. Starts no runtime, no engine
and no provider, and submits no Job.

THE PREVIOUS PACKET WAS SELECTED AND FAILED AT STARTUP. See `FAILURE.md`: the
controller composed two managers for one workspace and `hold_manager_instance`
correctly refused after 0.506s. W334910 corrected that; this packet binds the
corrected controller (`bc8c0363...`, previously `2da6eb36...`) and proposes a
FRESH run identity and destination. The failed instance is preserved and is
never reused, rerun or recovered.

`stage` freezes the manager and supervisor source from the DECLARED BASE and
emits the installation inputs; `bind` runs only after the supported bootstrap
has minted this instance's own execution authority, and additionally writes
`AUTHORING-COMMAND.json` -- see below, because the composer's own
`commands.json` is wrong for this vehicle.

THE START IS NOT SELECTED. The prerequisite that HELD the previous packet is
closed (owner close334628, checkpoint a9f4fa4d), so this is no longer a
blocker. What remains is that nobody has selected this run: independent
preparation review comes first, then an exact execution selection. `stage`
therefore requires `--acknowledge-unselected-start`, so a sequence of
ordinary-looking steps cannot carry an operator into a start nobody chose.

WHY `bind` WRITES ITS OWN COMMAND DOCUMENT. `baseline_bindings.py` is unchanged
at this base (sha256 09fbf3c5...) and its line 721 still composes `start` as
`[python, -B, <supervisor>/baseline.py, --packet, ..., --incarnation, ...]` --
the UNENFORCED path whose `serve` call carries no reclaim argument. The accepted
enforcement entry point is `python -m tools.authoring_enforcement --packet ...`,
run from the staged source so its own `verify_controller` can find itself
pinned. So the generated `commands.json` advertises exactly the vehicle the
prerequisite existed to replace, and this program writes the correct invocation
beside it rather than patching accepted product it does not own. `ENFORCEMENT.md`
reports that composer defect for classification.

WHY THE DECISION INPUTS ARE SNAPSHOTS. Pinning the mutable reviewer-owned
FINDING/PLAN made an earlier packet refuse on every ordinary plan update.
`decisions/` holds byte-for-byte copies with their source digests in
`decisions/INDEX.json`, the packet pins THOSE, and `verify-inputs.py` REPORTS
live-source drift rather than refusing it. Base and source drift stay fatal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
BASE = 'fb48797903160aa764229d58f3a5beaf29648bfc'
RUN = 'attempt-diagnostics-w333486-337453'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
EVIDENCE = HERE / 'decisions/owner-failure-evidence.md'
CONTROLLER = 'tools/authoring_enforcement.py'
RETENTION = 'sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a'
INTEGRATION = dict(profile_kind='git', profile_version=1,
                   integrator_participant='baton.merge',
                   instructions_digest='sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2')
RECEIPTS = dict(verification='baton.verifier', review='baton.approver-review',
                approval='baton.approver')

# THE SEALED ACCEPTANCE GATE. Two groups, two reasons.
#
#   * TEN EXISTING MODULES that must still pass. `test_intake`, `test_tool` and
#     `test_attempts` carry the reclaim/settlement/cancellation composition this
#     correction must attribute. `test_authoring_enforcement` is here because
#     this candidate edits `intake.py` and `attempts.py`, which that module
#     exercises through the enforcement lane cancellation path. Re-measured at
#     THIS base: 1124 tests, all passing, zero skips, 14.095s. Author evidence,
#     not independent product acceptance.
#
#     `tests.manager.test_authoring_manager_guard` is DELIBERATELY ABSENT for a
#     MEASURED CEILING REASON rather than a coverage judgement: 17.643s for 7
#     real-process tests, which with the ten above would put the sealed gate at
#     31.7s against a composer-fixed ceiling of 30, before the two new modules
#     exist. Its coverage is carried by the reused accepted proof in
#     `decisions/guard-integration-result.json` (79 tests, PASS, 15.278s,
#     authority337376), and this candidate does not edit the controller.
#   * TWO NEW MODULES, named as a CONVENTION because a sealed argv cannot name
#     classes that do not exist yet. They do not exist at the base, so this gate
#     FAILS until the turn creates them -- which is the point.
#
# TWO MODULES ARE DELIBERATELY ABSENT and both are the author's EXPLICITLY
# UNVERIFIED baseline reports with no cleanup selected:
# `tests.manager.test_boundary_inventory` does not pass at base and would exceed
# the 30s ceiling alone; `tests.tools.test_packaging` holds the source command
# table against the INSTALLED bundle and SKIPS inside a private checkout, which
# this program refuses.
#
# NOTE FOR WHOEVER RUNS THIS: `tests.manager.test_authoring_enforcement` spawns a
# REAL supervisor and resolves `work/records/2026/09/finding-v12-single-implementation-proof`
# from the checkout root. Measured both ways: 1 error without it, 33 passing with
# it. The private git-line checkout carries it.
GATE = [
    'tests.job_manager.test_status',
    'tests.job_manager.test_delegation',
    'tests.job_manager.test_documents',
    'tests.job_manager.test_tool',
    'tests.manager.test_intake',
    'tests.manager.test_maintenance',
    'tests.manager.test_attempts',
    'tests.tools.test_worker_visibility',
    'tests.manager.test_contracts_inventory',
    'tests.manager.test_authoring_enforcement',
    'tests.manager.test_attempt_failure_cause',
    'tests.tools.test_attempt_diagnostics',
]

# WHY THIS IS A `-c` PROGRAM. The launch envelope is `baton.dogfood-task/2`,
# which carries no `verification_context` member and no environment assignment,
# so the command establishes its own working directory and import path. The
# derived `PYTHONPATH` assignment is not decoration: named cases SPAWN
# subprocesses and `sys.path` is in-process only. It OVERWRITES rather than
# extends, so an ambient value cannot leak in. AND IT ADMITS NO SKIP.
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

# PROPOSED CEILINGS, NOT A PROMISED RUN LENGTH. One provider ceiling of 3600s
# with 60s reserved cleanup inside a 4800s total, one implementation invocation,
# no automatic retry, `report-and-hold`.
#
# `tokens.LIFETIME_SECONDS` IS STILL 900 AND RENEWAL IS STILL W333485'S WORK.
# The accepted controller makes that initial lease actually ENFORCED rather than
# ignored; it does not extend it. So an authoring turn here should expect expiry
# at 900 seconds with cessation ordered and partial output retained. And see
# `FAILURE.md`: no authoring invocation has ever completed for this Work.
# `ENFORCEMENT.md` and `TASK.md` both say so, and `LIMITS-CHECK.json` reports
# what the generated documents actually carry.
BOUNDS = dict(turn_seconds=3600, total_seconds=4800, cleanup_seconds=60,
              implementer_invocations=1, retry=False)

UNSELECTED = (
    "This packet's START IS NOT SELECTED. Both prerequisites are CLOSED "
    "(W333735 at a9f4fa4d, W334910 at fb487979), so this is not a blocker -- "
    "but independent preparation review comes first, then an exact execution "
    "selection. Two things to know: the previous packet WAS selected and died "
    "at startup in 0.506s (FAILURE.md), and the composer generated "
    "commands.json start still names the UNENFORCED supervisor -- use "
    "AUTHORING-COMMAND.json. See ENFORCEMENT.md.")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def committed(relative):
    return subprocess.check_output(['git', 'show', BASE + ':' + relative],
                                   cwd=REPO)


def pins():
    """Every pinned input, held against the tree before anything is written."""
    doc = json.loads((HERE / 'PREPARATION-PINS.json').read_text())
    if doc['base'] != BASE or doc['run_id'] != RUN:
        raise RuntimeError('the pins name another base or run')
    for name, expected in doc['files'].items():
        if sha(REPO / name) != expected:
            raise RuntimeError('selected preparation input drifted: ' + name)
    if sha(Path(DISTRO) / 'baton-v12-stack') \
            != doc['historical_bootstrap_binary_sha256']:
        raise RuntimeError('historical bootstrap binary drifted')
    # THE ACCEPTED CONTROLLER MUST BE PINNED BY THIS PACKET, because its own
    # `verify_controller` requires exactly that: it resolves itself inside the
    # packet's manager source and compares the digest. A packet that staged it
    # without pinning it would refuse at launch rather than here.
    held = doc['authoring_controller']
    if held['relative'] != CONTROLLER \
            or doc['manager_files'].get(CONTROLLER) != held['sha256']:
        raise RuntimeError('the authoring controller is not pinned by this '
                           'packet manager source')
    provenance = json.loads((HERE / 'PROVENANCE.json').read_text())
    if provenance['base'] != BASE or provenance['accepted'] is not False \
            or provenance['run_id'] != RUN:
        raise RuntimeError('the provenance disagrees with this preparation')
    # BOTH FLAGS, because they are two different claims and a probe caught this
    # program checking only the first: `start_authorized` is whether anyone may
    # start, `start_selected` is whether anyone has chosen to. A packet asserting
    # either must not stage.
    if provenance['start_authorized'] is not False \
            or provenance['start_selected'] is not False:
        raise RuntimeError('the provenance claims a start nobody has selected')
    if provenance['enforcement']['document'] != 'ENFORCEMENT.md' \
            or not (HERE / 'ENFORCEMENT.md').is_file():
        raise RuntimeError('the declared enforcement document is absent')
    if provenance['checkpoint']['paths']:
        raise RuntimeError('this preparation carries no restored buffer, and '
                           'the provenance declares one')
    index = json.loads((HERE / 'decisions/INDEX.json').read_text())['snapshots']
    for name, record in index.items():
        place = HERE / 'decisions' / name
        if not place.is_file() or sha(place) != record['snapshot_sha256']:
            raise RuntimeError('decision snapshot damaged or absent: ' + name)
    for name in doc['task_inputs']:
        if not (REPO / name).is_file():
            raise RuntimeError('declared task input is absent: ' + name)
    for name in doc['read_from_checkout_at_base']:
        try:
            committed(name)
        except subprocess.CalledProcessError:
            raise RuntimeError('declared checkout input is not at the base: '
                               + name)
    for name in ('v12/python/tests/manager/test_attempt_failure_cause.py',
                 'v12/python/tests/tools/test_attempt_diagnostics.py'):
        if (REPO / name).exists():
            raise RuntimeError('a gate module the turn must create already '
                               'exists on the host: ' + name)
    return doc


def stage(root, acknowledged=False):
    if not acknowledged:
        raise RuntimeError(UNSELECTED + ' Re-run with '
                           '--acknowledge-unselected-start to prepare anyway; '
                           'preparation produces no execution.')
    print(UNSELECTED, file=sys.stderr)
    selected = pins()
    if not root.is_absolute() or root == REPO or REPO in root.parents:
        raise RuntimeError('select a fresh absolute external preparation root')
    # EVERY BASE BYTE IS RESOLVED AND PROVED BEFORE THE ROOT EXISTS, so a
    # refused stage leaves the filesystem exactly as it found it. Measured while
    # probing an earlier revision: the reference program created the root and
    # wrote 112 files before validating the supervisor digests, and a drift left
    # a half-staged root the refuse-reuse rule then blocked forever.
    held = {}
    for relative, expected in selected['manager_files'].items():
        content = committed('v12/python/' + relative)
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError('manager source drifted: ' + relative)
        held['code/v12/python/' + relative] = (content, expected)
    for name, expected in selected['supervisor_files'].items():
        content = committed(str(OLD.relative_to(REPO) / name))
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError('supervisor source drifted: ' + name)
        held['supervisor/' + name] = (content, expected)
    root.mkdir(mode=0o700)  # refuse reuse, including symlinks
    for relative, (content, expected) in held.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if sha(target) != expected:
            raise RuntimeError('staged source mismatch: ' + relative)
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
                                   source=str(REPO), instance=str(instance),
                                   start_selected=False,
                                   enforcement='ENFORCEMENT.md'))
    print('staged; bootstrap separately with --no-repositories, then bind. '
          'The start is not selected.')


def _authoring_command(root, packet_path):
    """The invocation that actually enforces, and the one to use.

    NOT the composer's. See the module docstring: `commands.json` still names
    `baseline.py`, whose `serve` call carries no reclaim argument. The
    controller must run from the STAGED source so `verify_controller` resolves
    itself inside `manager_source` and matches its pinned digest, and the
    supervisor directory is on the path because `authoring_enforcement` imports
    `baseline`.
    """
    source = root / 'code/v12/python'
    return dict(
        schema='baton.w333486-authoring-command/1',
        why='The composer generated commands.json names the UNENFORCED '
            'supervisor (baseline_bindings.py:721 -> baseline.py, whose serve '
            'call carries no reclaim argument). Use THIS invocation. The '
            'composer defect is reported in ENFORCEMENT.md, not patched.',
        do_not_use=dict(document=str(root / 'packet/commands.json'),
                        member='start'),
        start_selected=False,
        start=[sys.executable or 'python3', '-m', 'tools.authoring_enforcement',
               '--packet', str(packet_path)],
        working_directory=str(source),
        environment={
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONPATH': ':'.join([str(source / 'src'), str(source),
                                    str(root / 'supervisor')]),
            'BATON_V12_STAGE_EXECUTION_CONFIG': str(root / 'packet/deployment.json')},
        controller=dict(relative=CONTROLLER,
                        staged=str(source / CONTROLLER),
                        sha256=sha(source / CONTROLLER)),
        termination='SIGINT/SIGTERM sets the enforcement stop and the reserved '
                    'cleanup window begins; the controller reports state=held. '
                    'A held outcome is not proof of cessation.',
        lease='tokens.LIFETIME_SECONDS is 900 and production renewal is not in '
              'this base. The 3600/4800 ceilings are requested bounds, not a '
              'promised run length; expect enforced expiry at 900 seconds with '
              'partial output retained.')


def bind(root):
    selected = pins()
    staged = json.loads((root / 'stage.json').read_text())
    if staged['base'] != BASE or staged['run_id'] != RUN:
        raise RuntimeError('this root was staged for another run')
    if (root / 'packet/PACKET.json').exists():
        raise RuntimeError('this root already holds a composed packet; '
                           'composing a second one over it would replace the '
                           'documents an owner may already have read')
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
        evidence_digest='sha256:' + sha(EVIDENCE),
        provider_network='bridge', run_id=RUN, work='W333486', claim=337453,
        note='Typed actionable attempt-failure capture across the actual '
             'reclaim, settlement and Authority-fenced cancellation paths, '
             'revalidated against the accepted enforcement bytes; a known '
             'stop/engine failure kept separate from an unknown cessation; one '
             'composed cause with explicit unknown carried to ordinary status; '
             'and one supported read-only diagnostic report with a '
             'demonstrated retained-evidence locator, at the corrected '
             'manager-guard checkpoint. START NOT SELECTED: '
             'independent preparation review precedes an exact execution '
             'selection. Retained proposal requires separate independent '
             'review, with no automatic integration and no acceptance.',
        bounds=BOUNDS, context_mode='fresh',
        task_instructions=(HERE / 'TASK.md').read_text(),
        verification=VERIFICATION)
    places = baseline_bindings.write(str(root / 'packet'), docs)
    baseline.held_packet(places['PACKET.json'])
    baseline.verify_imported_sources(docs['PACKET.json'])
    # THE CORRECT INVOCATION, written beside the composer's wrong one.
    command = _authoring_command(root, places['PACKET.json'])
    emit(root / 'packet/AUTHORING-COMMAND.json', command)
    emit(root / 'PREPARED.json', dict(
        state='prepared-not-executed', work='W333486', authority_uuid=uuid,
        start_authorized=False, start_selected=False,
        enforcement='ENFORCEMENT.md',
        authoring_command=str(root / 'packet/AUTHORING-COMMAND.json'),
        composer_start_is_unenforced=True,
        packet_sha256=sha(places['PACKET.json']),
        artifacts={name: sha(path) for name, path in places.items()},
        authoring_controller=command['controller'],
        independent_review='an independent reviewer consumes this preparation '
                           'packet through v11; execution awaits an exact '
                           'separate selection, and there is no automatic '
                           'acceptance'))
    print('prepared and validated; no job submitted, no engine/provider '
          'invoked. Start not selected. Use packet/AUTHORING-COMMAND.json, '
          'NOT commands.json start -- see ENFORCEMENT.md.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('step', choices=['stage', 'bind'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--acknowledge-unselected-start', action='store_true',
                        help='required by `stage`: confirms ENFORCEMENT.md was '
                             'read and that no execution is selected. '
                             'Preparation produces no execution.')
    args = parser.parse_args()
    if args.step == 'stage':
        stage(Path(args.root),
              acknowledged=args.acknowledge_unselected_start)
    else:
        bind(Path(args.root))
