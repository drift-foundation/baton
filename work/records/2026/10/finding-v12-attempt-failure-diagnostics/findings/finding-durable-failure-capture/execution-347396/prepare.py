"""W341357 execution preparation only -- the bounded producer slice of W333486.

This is a CHILD SLICE, not a successor packet. Parent W333486 owns the ordinary
status/report integration, the full joined twelve-module gate, the
installed-bundle proof and final acceptance, and is serially blocked on this
child. Every parent packet stays sealed and all five earlier instance roots
stay untouched. Starts no runtime, no engine and no provider, and submits no Job.

THE VEHICLE IS UNCHANGED. Controller `d12769df...`, supervisor baseline
`8e5987f5...`, shutdown helper `af9e5ea6...`, 114 pinned manager files, base
`bc925cf5...` -- the same bytes that carried run340016 end to end and that
reached a worker container in under 20 seconds on every run since, so none of
it is re-argued here. `ENFORCEMENT.md`, `SHUTDOWN.md` and `FAILURE.md` are
carried for the same reason.

WHERE THIS STARTS FROM. Run341360 hit its 900-second lease and froze no result:
no candidate, no proposal, no verification. Its unfrozen working tree survives
read-only in this dossier's evidence, and `recovery-341360/` holds that work as
that run left it -- `worker_manager/failure_cause.py` and
`tests/manager/test_attempt_failure_cause.py` verbatim, plus a producer patch
for `worker_manager` `documents.py`, `intake.py` and `attempts.py`. UNVERIFIED
RECOVERY INPUT, pinned by digest and bound to the digests the reviewer
published independently. `RECOVERY.md` is the account, including the
collision-as-authorization defect already found in it. NOTHING IN THOSE BYTES
HAS EVER BEEN EXECUTED.

THE GATE IS FOCUSED, NOT THE PARENT'S. `FINDING.md` keeps the full joined gate
with the parent, so the sealed argv names five producer modules rather than
twelve. The fifth arrives with the recovery input and is the turn's to extend,
so the gate fails until that is applied and made to pass -- which is the point.
IT HAS STILL NEVER BEEN MEASURED IN ANY RUN.

THIS IS A FRESH IDENTITY FOR AN ACCEPTED PREPARATION. `../execution-341637` was
independently accepted and selected once by owner342358; that invocation failed
provider authentication at 10.56s with no work attempted. Its root now exists
and holds a composed packet, so `stage` would refuse it and `bind` would refuse
a second composition over it. Only the run id, the root and the resultant seal
differ here; the task, recovery, limit and vehicle bytes are carried verbatim.

THE START IS NOT SELECTED. Owner342358's one invocation is consumed. This
prepares exact isolated operands for independent review and a separate
selection; `stage` therefore requires `--acknowledge-unselected-start`.

WHY `bind` WRITES ITS OWN COMMAND DOCUMENT, and why the decision inputs are
snapshots: unchanged from the parent packet this scaffold came from. See
`ENFORCEMENT.md` for the composer defect that makes `commands.json` start wrong
for this vehicle.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PACKET_DIR = 'work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/execution-347396'
REPO = Path('/home/sl/src/baton')
BASE = 'bc925cf5c62d69426ed5862af4d41f4d2a967b0f'
RUN = 'durable-capture-w341357-347396'
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
    'tests.manager.test_intake',
    'tests.manager.test_attempts',
    'tests.manager.test_maintenance',
    'tests.manager.test_contracts_inventory',
    'tests.manager.test_attempt_failure_cause',
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
    "an exact execution selection. Four things to know: TWO earlier packets "
    "were selected and neither ran -- execution-334663 died at startup in "
    "0.506s (FAILURE.md) and execution-341637 failed provider authentication "
    "in 10.56s; no authoring invocation has ever completed for this Work; the "
    "focused gate has never been measured in any run; and the composer "
    "generated commands.json start still names the UNENFORCED supervisor -- "
    "use AUTHORING-COMMAND.json. See ENFORCEMENT.md and SHUTDOWN.md.")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


WORKER_DOCUMENTS = ('TASK.md', 'RECOVERY.md', 'COMPLETION.md', 'FIXTURE.md',
                    'ENFORCEMENT.md', 'SHUTDOWN.md', 'FAILURE.md')


def _recovery_checks(pins, held, repo, read):
    """The retained candidate, held against four independent records.

    Retargeted at `baton.w341357-recovery/3`. The previous revisions pinned a
    PRODUCER DIFF split out of an unfrozen working tree; this one pins the
    EXACT RETAINED CANDIDATE a completed run returned, so the records it is
    checked against are different records:

      1. the pinned bytes on disk, against the pin (done by the caller);
      2. the recovery index, against the pin -- same patch digest, same schema;
      3. the reviewer's INDEPENDENTLY PUBLISHED digests for the patch, the
         transport bundle and the candidate content, so a drift on either side
         is a refusal rather than a silent divergence;
      4. the RUN'S OWN retained evidence index, which is a separate immutable
         record of what that run returned -- head, base and content digest.

    The transport bundle is NOT pinned as a task input, deliberately: this
    campaign creates no version-control object on this host. Its digest is
    still checked against the reviewer's, because a drifted transport means the
    evidence set moved under the packet.
    """
    source = read(repo / held['index'])
    if source.get('schema') != held['index_schema']:
        raise RuntimeError('the recovery index is not '
                           + held['index_schema'] + ': ' + repr(source.get('schema')))
    patch = held['patch_relative']
    if source['candidate_patch']['sha256'] != held['files'][patch]:
        raise RuntimeError('the recovery index and the pins disagree about the '
                           'retained candidate patch')
    if not source.get('agrees_with_reviewer_digests'):
        raise RuntimeError('the recovery index does not record agreement with '
                           "the reviewer's published digests")
    candidate = held['candidate']
    for field in ('head', 'base'):
        if source.get(field) != candidate[field]:
            raise RuntimeError('the recovery index names another candidate '
                               + field)
    if source.get('candidate_content_digest') != candidate['content_digest']:
        raise RuntimeError('the recovery index names another candidate content')
    published = held['reviewer_published_digests']
    if source['reviewer_published_digests'] != published:
        raise RuntimeError("the recovery index carries different reviewer "
                           'digests than these pins')
    if published['candidate_patch'] != held['files'][patch]:
        raise RuntimeError('the pinned candidate patch disagrees with the '
                           "reviewer's published digest")
    bundle = repo / held['transport_bundle']
    if not bundle.is_file():
        raise RuntimeError('the retained candidate transport is absent: '
                           + held['transport_bundle'])
    if hashlib.sha256(bundle.read_bytes()).hexdigest() \
            != published['candidate_objects_bundle']:
        raise RuntimeError('the retained candidate transport is not the '
                           "reviewer's published bytes")
    if held['transport_bundle'] in pins['task_inputs']:
        raise RuntimeError('the candidate transport must NOT be a task input: '
                           'this campaign creates no version-control object on '
                           'this host and restores nothing into the checkout')
    evidence = read(repo / held['run_evidence_index'])
    if evidence['run'] != candidate['run'] \
            or evidence['attempt'] != candidate['attempt']:
        raise RuntimeError('the run evidence index describes another run or '
                           'attempt')
    retained = evidence['candidate']
    if retained['head'] != candidate['head'] \
            or retained['base'] != candidate['base'] \
            or retained['content_digest'] != candidate['content_digest']:
        raise RuntimeError("the run's own evidence index names another "
                           'candidate than these pins')
    if sorted(source['changed_paths']) != sorted(retained['changed_paths']):
        raise RuntimeError('the recovery index and the run evidence disagree '
                           'about the candidate changed paths')
    return source


def _recovery(doc, held):
    return _recovery_checks(doc, held, REPO, lambda place: json.loads(place.read_text()))


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
    # THE RETAINED CANDIDATE IS PINNED THREE WAYS, because this is the first
    # packet that continues from real returned work rather than from committed
    # bytes alone. The patch is the whole delivery: no version-control object is
    # created on this host and nothing is restored into the private checkout,
    # which is why `checkpoint.paths` above stays empty and that refusal keeps
    # its meaning.
    #
    #   1. the patch file's own bytes, against the pin;
    #   2. the pin, against the candidate's OWN disposition record, which is a
    #      separate immutable snapshot of what the run returned;
    #   3. the patch, named as a task input, so it travels as `fixture.files`
    #      and the turn reads exactly these bytes off the read-only mount.
    held = doc['recovery_input']
    # EVERY RECOVERY BYTE, against its pin AND against the parent evidence it
    # was derived from, so a drift in either is fatal here rather than inside a
    # provider turn.
    for relative, expected in sorted(held['files'].items()):
        place = REPO / relative
        if not place.is_file():
            raise RuntimeError('a recovery input is absent: ' + relative)
        if sha(place) != expected:
            raise RuntimeError('a recovery input is not its declared bytes: '
                               + relative)
        if relative not in doc['task_inputs']:
            raise RuntimeError('a recovery input is not a task input, so the '
                               'turn could not read it off the mount: ' + relative)
    _recovery(doc, held)
    # THE WORKER-VISIBLE DOCUMENTS MUST REACH THE WORKER, not just the record.
    # Each is a task input so it travels as fixture.files; refusing here is what
    # makes that structural rather than a habit. review341628 is explicit that
    # placing the completion mechanism only in PROGRESS is insufficient, and
    # FIXTURE.md is the same rule applied to the diagnosis this turn acts on.
    for name in WORKER_DOCUMENTS:
        if not (HERE / name).is_file():
            raise RuntimeError(
                'a worker-visible document this packet depends on is absent: '
                + name)
        if f'{PACKET_DIR}/{name}' not in doc['task_inputs']:
            raise RuntimeError('a worker-visible document is not a task input, '
                               'so the turn could not read it: ' + name)
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
    for name in ('v12/python/tests/manager/test_attempt_failure_cause.py',):
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
        provider_network='bridge', run_id=RUN, work='W341357', claim=347396,
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
        state='prepared-not-executed', work='W341357', authority_uuid=uuid,
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
