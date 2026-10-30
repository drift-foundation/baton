"""W333486 execution preparation only, superseding `../execution-333504`.

Starts no runtime, no engine and no provider, and submits no Job.

`stage` freezes the manager and supervisor source from the DECLARED BASE and
emits the installation inputs; `bind` runs only after the supported bootstrap
has minted this instance's own execution authority. The product composition and
the single-implementation supervisor are reused unchanged -- this packet selects
them, it does not re-author them.

THE START IS HELD AND THIS PROGRAM KNOWS IT. `HOLD.md` records the shared
authoring prerequisite: the selected supervisor calls `serve` with no reclaim
pass, so a 900-second workspace generation is not enforced across the 3600/4800
run these documents request. Preparation is still authorized, so `stage`
requires `--acknowledge-hold` and prints the hold rather than letting a
sequence of ordinary-looking steps carry an operator into a start nobody
selected.

WHY THE DECISION INPUTS ARE SNAPSHOTS. The superseded packet pinned the MUTABLE
reviewer-owned `FINDING.md` and `PLAN.md`, so every ordinary current-plan update
invalidated a sealed packet. Review 2026-10-19T16-44-00Z asked for immutable
snapshots instead: `decisions/` holds byte-for-byte copies with their source
digests in `decisions/INDEX.json`, the packet pins THOSE, and `verify-inputs.py`
REPORTS live-source drift rather than refusing it. Base and source drift stay
fatal, because those decide what is built; a plan update decides what is next.

WHY THERE IS NO RESTORE STEP. This correction begins from committed bytes
alone: every input is at the declared base, and the documents the turn must
READ travel as the packet's own `fixture.files` over the read-only nominated
source. Nothing is written back into the private checkout, so there is no
buffer to validate.
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
RUN = 'attempt-diagnostics-w333486-333707'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
EVIDENCE = HERE / 'decisions/owner-failure-evidence.md'
RETENTION = 'sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a'
INTEGRATION = dict(profile_kind='git', profile_version=1,
                   integrator_participant='baton.merge',
                   instructions_digest='sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2')
RECEIPTS = dict(verification='baton.verifier', review='baton.approver-review',
                approval='baton.approver')

# THE SEALED ACCEPTANCE GATE, unchanged from the superseded packet because the
# modules it names are still the right ones and the base is the same. Two groups,
# two reasons.
#
#   * NINE EXISTING MODULES that must still pass -- the producers and consumers
#     this correction moves. `test_intake` and `test_tool` are in it
#     SPECIFICALLY because the reclaim-to-settlement composition review
#     2026-10-19T16-44-00Z item 2 requires proving lives across those two.
#     Measured by the preparing author against a clean export of the declared
#     base: 1091 tests, all passing, zero skips, 11.830s. Author evidence, not
#     independent product acceptance.
#   * TWO NEW MODULES, named as a CONVENTION because a sealed argv cannot name
#     classes that do not exist yet. They do not exist at the base, so this gate
#     FAILS until the turn creates them -- which is the point.
#
# TWO MODULES ARE DELIBERATELY ABSENT and `PACKET.md` records why for each.
# Both are the author's EXPLICITLY UNVERIFIED baseline reports and neither is
# selected for cleanup: `tests.manager.test_boundary_inventory` does not pass at
# this base (328 tests, 28 failures, 1 error, 49.469s alone) and would exceed the
# 30s ceiling by itself; `tests.tools.test_packaging` holds the source command
# table against the INSTALLED bundle, which predates `record` and `disposition`,
# and inside a private checkout it SKIPS -- which this program refuses. The
# packaged-table obligation moves to a source-level case, and the remaining
# rebuilt-bundle obligation stays explicit in `TASK.md` because source proof is
# not bundle proof.
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
    'tests.manager.test_attempt_failure_cause',
    'tests.tools.test_attempt_diagnostics',
]

# WHY THIS IS A `-c` PROGRAM AND NOT A LITERAL TEST ARGV. The launch envelope is
# `baton.dogfood-task/2`, which carries no `verification_context` member and no
# environment assignment, so the command must establish its own working
# directory and import path. The derived `PYTHONPATH` assignment is not
# decoration: named cases in this tree SPAWN subprocesses, and `sys.path` is
# in-process only. It OVERWRITES rather than extends, so whatever `PYTHONPATH`
# the runtime happened to export cannot leak in.
#
# AND IT ADMITS NO SKIP. A skipped case is an unproven obligation wearing a
# passing exit status, so the program refuses one and prints which.
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

# PROPOSED, AND HELD. One provider ceiling of 3600s with 60s reserved cleanup
# inside a 4800s total, one implementation invocation, no automatic retry,
# `report-and-hold`. These are an estimate for one invocation -- not a
# correctness guarantee, not an authorization, and `HOLD.md` is exactly why they
# are not yet startable: the selected supervisor cannot enforce the 900-second
# resource lease across them.
#
# `verification_command_seconds` IS FIXED AT 30 BY THE COMPOSER, in both places
# it appears (`baseline_bindings.py:345`, the execution policy whose digest the
# submission carries, and `:522`, the submission's own `execution_limits`), with
# no compose parameter. `LIMITS-CHECK.json` reports what the generated documents
# actually say rather than what prose wishes.
BOUNDS = dict(turn_seconds=3600, total_seconds=4800, cleanup_seconds=60,
              implementer_invocations=1, retry=False)

HOLD = ("This packet's START is HELD -- see HOLD.md. The selected baseline.py "
        "supervisor calls serve with no reclaim pass (baseline.py:1207; "
        "manager.py:833 reclaim=None, :879 runs a pass only if reclaim is not "
        "None), so the 900-second workspace generation is not enforced across "
        "the requested 3600/4800 run. Preparation is authorized; starting is "
        "an owner decision on the shared authoring prerequisite.")


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
    provenance = json.loads((HERE / 'PROVENANCE.json').read_text())
    if provenance['base'] != BASE or provenance['accepted'] is not False \
            or provenance['run_id'] != RUN:
        raise RuntimeError('the provenance disagrees with this preparation')
    if provenance['start_authorized'] is not False:
        raise RuntimeError('the provenance claims a start this packet holds')
    if provenance['checkpoint']['paths']:
        raise RuntimeError('this preparation carries no restored buffer, and '
                           'the provenance declares one')
    # THE SNAPSHOTS ARE THE TURN'S INPUTS AND THEY MUST BE INTACT. They live
    # inside this packet, so a difference here is a damaged packet rather than a
    # moved decision -- which is why this one IS fatal while source drift is not.
    index = json.loads((HERE / 'decisions/INDEX.json').read_text())['snapshots']
    for name, held in index.items():
        place = HERE / 'decisions' / name
        if not place.is_file() or sha(place) != held['snapshot_sha256']:
            raise RuntimeError('decision snapshot damaged or absent: ' + name)
    for name in doc['task_inputs']:
        if not (REPO / name).is_file():
            raise RuntimeError('declared task input is absent: ' + name)
    # THE DOCUMENTS READ FROM THE CHECKOUT MUST BE AT THE BASE, because that is
    # where the turn will look for them.
    for name in doc['read_from_checkout_at_base']:
        try:
            committed(name)
        except subprocess.CalledProcessError:
            raise RuntimeError('declared checkout input is not at the base: '
                               + name)
    # THE GATE'S NEW MODULES MUST NOT EXIST YET. If one did, the sealed argv
    # would name something the base already carries, and this packet would be
    # describing a correction that had partly happened outside v12.
    for name in ('v12/python/tests/manager/test_attempt_failure_cause.py',
                 'v12/python/tests/tools/test_attempt_diagnostics.py'):
        if (REPO / name).exists():
            raise RuntimeError('a gate module the turn must create already '
                               'exists on the host: ' + name)
    return doc


def stage(root, acknowledged=False):
    if not acknowledged:
        raise RuntimeError(HOLD + ' Re-run with --acknowledge-hold to prepare '
                                  'anyway; preparation produces no execution.')
    print(HOLD, file=sys.stderr)
    selected = pins()
    if not root.is_absolute() or root == REPO or REPO in root.parents:
        raise RuntimeError('select a fresh absolute external preparation root')
    # EVERY BASE BYTE IS RESOLVED AND PROVED BEFORE THE ROOT EXISTS.
    #
    # Measured while probing the superseded packet rather than assumed: the
    # 329953 reference creates the root and writes its 112 manager files first
    # and validates the three supervisor digests afterwards -- so a supervisor
    # drift left a HALF-STAGED root behind, which the "refuse reuse" rule in the
    # line below then blocks forever. The repair for a refused stage would have
    # been to delete a directory the packet had just made.
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
                                   start_held=True, hold='HOLD.md'))
    print('staged; bootstrap separately with --no-repositories, then bind. '
          'The start remains held.')


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
    # THE DOCUMENTS THE TURN CANNOT PROCEED WITHOUT, pinned as the packet's own
    # fixture so `held_packet` refuses a drifted one BEFORE any store opens. They
    # are this packet's own immutable snapshots plus its task, so an ordinary
    # update to the live reviewer-owned plan cannot invalidate a sealed packet.
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
        provider_network='bridge', run_id=RUN, work='W333486', claim=333707,
        note='Typed actionable attempt-failure capture across the actual '
             'reclaim and settlement paths, a known stop/engine failure kept '
             'separate from an unknown cessation, one composed cause with '
             'explicit unknown carried to ordinary status, and one supported '
             'read-only diagnostic report with a demonstrated retained-evidence '
             'locator. START IS HELD on the shared authoring prerequisite; '
             'retained proposal requires separate independent review, with no '
             'automatic integration and no acceptance.',
        bounds=BOUNDS, context_mode='fresh',
        task_instructions=(HERE / 'TASK.md').read_text(),
        verification=VERIFICATION)
    places = baseline_bindings.write(str(root / 'packet'), docs)
    baseline.held_packet(places['PACKET.json'])
    baseline.verify_imported_sources(docs['PACKET.json'])
    emit(root / 'PREPARED.json', dict(
        state='prepared-not-executed', work='W333486', authority_uuid=uuid,
        start_authorized=False, hold='HOLD.md',
        packet_sha256=sha(places['PACKET.json']),
        artifacts={name: sha(path) for name, path in places.items()},
        independent_review='an independent reviewer consumes this preparation '
                           'packet through v11; actual execution awaits the '
                           'separately selected safe authoring vehicle, and '
                           'there is no automatic acceptance'))
    print('prepared and validated; no job submitted, no engine/provider '
          'invoked. The start remains held -- see HOLD.md.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('step', choices=['stage', 'bind'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--acknowledge-hold', action='store_true',
                        help='required by `stage`: confirms HOLD.md was read. '
                             'Preparation produces no execution.')
    args = parser.parse_args()
    if args.step == 'stage':
        stage(Path(args.root), acknowledged=args.acknowledge_hold)
    else:
        bind(Path(args.root))
