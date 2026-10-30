"""W333486 execution preparation only, at the corrected shutdown checkpoint.

Supersedes `../execution-333504`, `../execution-333707`, `../execution-334663`,
`../execution-337453` and `../execution-339421`, all preserved unchanged. Starts
no runtime, no engine and no provider, and submits no Job.

WHY A SIXTH PACKET, AND IT IS NOT A REBASE. `../execution-339421` pins exactly
the vehicle bytes this packet pins -- controller `d12769df...`, supervisor
baseline `8e5987f5...`, helper `af9e5ea6...`, base `bc925cf5...`, 114 manager
files. Nothing drifted under it. It is superseded for what its DOCUMENTS said,
and `decisions/review-339623.md` is the authority for all four corrections:

  1. its `TASK.md` item 6 told the worker inside the run to report the run's own
     three final results. Impossible: the controller publishes after
     `supervise_process` returns and after child cleanup
     (`authoring_enforcement.py:552-591`) and the supervisor publishes
     post-stop (`baseline.py:1450-1461`), both on the far side of the worker's
     own termination. Post-run collection is now the external operator's and
     reviewer's, with `collect.py` and `COMMANDS.md` step 5 as the executable
     half; the worker reports what it observed before termination plus the
     retained candidate checkpoint.
  2. its `SHUTDOWN.md` read an absent enforcement report as a publication
     timeout, and claimed the controller "writes nothing" on a publication
     `TimeoutError`. Both are false. Absence means unavailable with an UNKNOWN
     cause -- `absent`, `inaccessible`, `pending` and `unknown-cause` are four
     different facts -- and the bound at `authoring_enforcement.py:586-594`
     spans `write_text`, `os.replace` AND `print`, so the file may already
     exist. A timeout is named only on correlated positive evidence.
  3. the previous claim measured the gate by DIRECT HOST PRODUCT TEST
     EXECUTION, outside a preparation-only boundary, and then reported "re-runs
     0" beside the resulting numbers. Corrected additively in `PROGRESS.md`;
     carried here with that attribution; NOT re-measured, because re-running
     them to tidy their provenance would repeat the mistake.
  4. its `Boundaries` banned two sibling-declared files outright. Replaced by
     actual overlap declaration and serial reviewed integration.

WHY THE VEHICLE PINS STILL MATTER. `../execution-337453` -- the packet before
that one -- WAS stale: it named controller `bc8c0363...` and baseline
`c1b0a10e...`, both superseded by the accepted W338305 correction committed at
this base, and `tools/authoring_shutdown.py` did not exist in it at all. The
controller imports that module at its line 26, so a staged manager source
without it cannot import the controller; pinning and staging it is what makes
the corrected vehicle reachable rather than merely committed. `SHUTDOWN.md` is
the account.

AN EARLIER PACKET WAS SELECTED AND FAILED AT STARTUP. See `FAILURE.md`: the
controller composed two managers for one workspace and `hold_manager_instance`
correctly refused after 0.506s. W334910 corrected that, W338305 then corrected
the shutdown/final-report behaviour, and this packet binds both. The failed
instance is preserved and is never reused, rerun or recovered; this packet
proposes a FRESH run identity and a FRESH destination.

`stage` freezes the manager and supervisor source from the DECLARED BASE and
emits the installation inputs; `bind` runs only after the supported bootstrap
has minted this instance's own execution authority, and additionally writes
`AUTHORING-COMMAND.json` -- see below, because the composer's own
`commands.json` is wrong for this vehicle.

THE START IS NOT SELECTED. Every input gate is closed (`remove_dependency`339410,
`wake`339414), so this is not a blocker. What remains is that nobody has
selected this run: independent preparation review comes first, then an exact
execution selection. `stage` therefore requires
`--acknowledge-unselected-start`, so a sequence of ordinary-looking steps
cannot carry an operator into a start nobody chose.

WHY `bind` WRITES ITS OWN COMMAND DOCUMENT. `baseline_bindings.py` is STILL
unchanged at this base (sha256 09fbf3c5..., re-measured) and its line 721 still
composes `start` as `[python, -B, <supervisor>/baseline.py, --packet, ...,
--incarnation, ...]` -- the UNENFORCED path whose `serve` call carries no
reclaim argument. The accepted enforcement entry point is `python -m
tools.authoring_enforcement --packet ...`, run from the staged source so its
own `verify_controller` can find itself pinned. So the generated
`commands.json` advertises exactly the vehicle the prerequisites existed to
replace, and this program writes the correct invocation beside it rather than
patching accepted product it does not own. `ENFORCEMENT.md` reports that
composer defect for classification.

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
BASE = 'bc925cf5c62d69426ed5862af4d41f4d2a967b0f'
RUN = 'attempt-diagnostics-w333486-339628'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
EVIDENCE = HERE / 'decisions/owner-failure-evidence.md'
CONTROLLER = 'tools/authoring_enforcement.py'
SHUTDOWN = 'tools/authoring_shutdown.py'
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
#     exercises through the enforcement lane cancellation path. Measured at THIS
#     base against a clean export: 1124 tests, all passing, zero skips, 13.642s
#     unittest / 14.007s measured.
#
#     READ THE ATTRIBUTION. Those figures were obtained by DIRECT HOST PRODUCT
#     TEST EXECUTION AT CLAIM339421, OUTSIDE that claim's preparation-only
#     boundary. `decisions/review-339623.md` item 3 is the finding and
#     `PROGRESS.md` carries the author's correction. They were NOT re-measured
#     at claim339628 -- re-running them to tidy their provenance would repeat
#     the mistake -- and they are NOT independent product acceptance. THIS CLAIM
#     RAN NO PRODUCT TEST AT ALL.
#
#     TWO REAL-PROCESS MODULES ARE DELIBERATELY ABSENT, both for a MEASURED
#     CEILING REASON rather than a coverage judgement:
#     `tests.manager.test_authoring_shutdown_deadline` costs 51.333s for 4 tests
#     and `tests.manager.test_authoring_manager_guard` 19.888s for 7. Either one
#     alone would break a ceiling the composer fixes at 30s. Both numbers come
#     from the same out-of-boundary claim339421 execution, so BOTH EXCLUSION
#     DECISIONS REST ON OUT-OF-BOUNDARY MEASUREMENTS -- stated rather than
#     laundered. Their coverage is carried by REUSED accepted proof --
#     `decisions/shutdown-review.md` (44 tests, no skips, 72.891s,
#     authority338596) and `decisions/guard-integration-result.json` (79 tests,
#     PASS, 15.278s, authority337376) -- and this candidate edits neither the
#     controller nor the shutdown helper nor the supervisor.
#   * TWO NEW MODULES, named as a CONVENTION because a sealed argv cannot name
#     classes that do not exist yet. They do not exist at the base, so this gate
#     FAILS until the turn creates them -- which is the point.
#
# TWO FURTHER MODULES ARE ABSENT as the author's EXPLICITLY UNVERIFIED baseline
# reports with no cleanup selected: `tests.manager.test_boundary_inventory` does
# not pass at base and would exceed the 30s ceiling alone; `tests.tools.test_packaging`
# holds the source command table against the INSTALLED bundle and SKIPS inside a
# private checkout, which this program refuses.
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
# Re-measured at this base. The accepted controller makes that initial lease
# actually ENFORCED rather than ignored; W338305 then made the ENDING bounded
# and its reports deadline-aware. Neither correction extends the lease. So an
# authoring turn here should expect expiry at 900 seconds with cessation
# ordered and partial output retained. And see `FAILURE.md`: no authoring
# invocation has ever completed for this Work. `ENFORCEMENT.md`, `SHUTDOWN.md`
# and `TASK.md` all say so, and `LIMITS-CHECK.json` reports what the generated
# documents actually carry.
#
# `cleanup_seconds` IS NOW LOAD-BEARING IN A SECOND WAY. `authoring_shutdown.Shutdown`
# derives the whole inner shutdown allowance from it -- `min(maximum, now +
# cleanup_seconds - min(12, cleanup_seconds / 2))` -- and the outer watchdog
# reserves the same tail for kill/reap. At 60s that is a 30s inner allowance
# before the outer backstop, subdivided across cleanup, accounting, workload
# publication, guard stop and guard publication. Lowering it would silently
# shrink the window in which a final report can still be written.
BOUNDS = dict(turn_seconds=3600, total_seconds=4800, cleanup_seconds=60,
              implementer_invocations=1, retry=False)

UNSELECTED = (
    "This packet's START IS NOT SELECTED. Every input gate is closed "
    "(W333735 at a9f4fa4d, W334910 at fb487979, W338305 at bc925cf5), so this "
    "is not a blocker -- but independent preparation review comes first, then "
    "an exact execution selection. Three things to know: an earlier packet WAS "
    "selected and died at startup in 0.506s (FAILURE.md), no authoring "
    "invocation has ever completed for this Work, and the composer generated "
    "commands.json start still names the UNENFORCED supervisor -- use "
    "AUTHORING-COMMAND.json. See ENFORCEMENT.md and SHUTDOWN.md.")


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
    # AND SO MUST THE SHUTDOWN HELPER, for a different and blunter reason: the
    # controller IMPORTS it. A manager source staged without it fails at
    # `from tools.authoring_shutdown import Shutdown, bounded` -- a startup
    # failure, not a refusal, and the previous selected run already taught this
    # campaign what a startup failure costs. Refuse here instead.
    helper = doc['shutdown_helper']
    if helper['relative'] != SHUTDOWN \
            or doc['manager_files'].get(SHUTDOWN) != helper['sha256']:
        raise RuntimeError('the authoring shutdown helper the controller '
                           'imports is not pinned by this packet manager '
                           'source')
    provenance = json.loads((HERE / 'PROVENANCE.json').read_text())
    if provenance['base'] != BASE or provenance['accepted'] is not False \
            or provenance['run_id'] != RUN:
        raise RuntimeError('the provenance disagrees with this preparation')
    # BOTH FLAGS, because they are two different claims and a probe caught an
    # earlier revision checking only the first: `start_authorized` is whether
    # anyone may start, `start_selected` is whether anyone has chosen to. A
    # packet asserting either must not stage.
    if provenance['start_authorized'] is not False \
            or provenance['start_selected'] is not False:
        raise RuntimeError('the provenance claims a start nobody has selected')
    for name in ('ENFORCEMENT.md', 'SHUTDOWN.md'):
        if not (HERE / name).is_file():
            raise RuntimeError('a declared vehicle document is absent: ' + name)
    if provenance['enforcement']['document'] != 'ENFORCEMENT.md' \
            or provenance['shutdown']['document'] != 'SHUTDOWN.md':
        raise RuntimeError('the provenance names another vehicle document')
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
                                   enforcement='ENFORCEMENT.md',
                                   shutdown='SHUTDOWN.md'))
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
        schema='baton.w333486-authoring-command/2',
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
        shutdown_helper=dict(relative=SHUTDOWN,
                             staged=str(source / SHUTDOWN),
                             sha256=sha(source / SHUTDOWN),
                             why='imported by the controller; the vehicle does '
                                 'not start without it'),
        termination='SIGINT/SIGTERM sets the enforcement stop and the reserved '
                    'cleanup window begins; the controller reports state=held. '
                    'A held outcome is not proof of cessation.',
        final_results=dict(
            controller='<outcome_path>.enforcement-<pid>-<ns>.json, named in '
                       'the controller report as enforcement_path',
            workload='<outcome_path>, written by the supervisor before the '
                     'controller publishes',
            shutdown_progress='<status_path>.progress.json, the last shutdown '
                              'step entered; the controller copies it into its '
                              'own report as shutdown_progress',
            rule='A missing or partial final report is INCOMPLETE, never '
                 'success and never proof of cessation. See SHUTDOWN.md.'),
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
        provider_network='bridge', run_id=RUN, work='W333486', claim=339628,
        note='Typed actionable attempt-failure capture across the actual '
             'reclaim, settlement and Authority-fenced cancellation paths; a '
             'known stop/engine failure kept separate from an unknown '
             'cessation; one composed cause with explicit unknown carried to '
             'ordinary status; and one supported read-only diagnostic report '
             'with a demonstrated retained-evidence locator -- at the '
             'corrected authoring-shutdown checkpoint, whose bounded final '
             'reports the turn must report honestly rather than read as '
             'acceptance. START NOT SELECTED: independent preparation review '
             'precedes an exact execution selection. Retained proposal '
             'requires separate independent review, with no automatic '
             'integration and no acceptance.',
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
        enforcement='ENFORCEMENT.md', shutdown='SHUTDOWN.md',
        authoring_command=str(root / 'packet/AUTHORING-COMMAND.json'),
        composer_start_is_unenforced=True,
        packet_sha256=sha(places['PACKET.json']),
        artifacts={name: sha(path) for name, path in places.items()},
        authoring_controller=command['controller'],
        shutdown_helper=command['shutdown_helper'],
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
                        help='required by `stage`: confirms ENFORCEMENT.md and '
                             'SHUTDOWN.md were read and that no execution is '
                             'selected. Preparation produces no execution.')
    args = parser.parse_args()
    if args.step == 'stage':
        stage(Path(args.root),
              acknowledged=args.acknowledge_unselected_start)
    else:
        bind(Path(args.root))
