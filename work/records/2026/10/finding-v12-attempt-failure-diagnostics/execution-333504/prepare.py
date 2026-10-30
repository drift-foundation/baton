"""W333486 execution preparation only. Starts no runtime, no engine and no
provider, and submits no Job.

`stage` freezes the manager and supervisor source from the DECLARED BASE and
emits the installation inputs; `bind` runs only after the supported bootstrap
has minted this instance's own execution authority. The product composition and
the single-implementation supervisor are reused unchanged -- this packet selects
them, it does not re-author them.

WHY THERE IS NO RESTORE STEP HERE, unlike the 329953 reference this is modelled
on. That packet continued a reviewed slice of five uncommitted host files, so
those bytes had to travel as digest-bound buffers and be placed inside the
private checkout before the turn could begin. This correction begins from
committed bytes alone: every input is at the declared base, and the documents
the turn must READ travel as the packet's own `fixture.files` pins over the
read-only nominated source. Nothing is written back into the checkout, so there
is no buffer to validate and no `restore.py` to name.
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
RUN = 'attempt-diagnostics-w333486-333504'
OLD = REPO / 'work/records/2026/09/finding-v12-single-implementation-proof'
DISTRO = '/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro'
VECTORS = REPO / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
EVIDENCE = REPO / 'work/records/2026/10/finding-v12-native-pilot-instance-packet/OWNER-FAILURE-EVIDENCE-20261019.md'
RETENTION = 'sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a'
INTEGRATION = dict(profile_kind='git', profile_version=1,
                   integrator_participant='baton.merge',
                   instructions_digest='sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2')
RECEIPTS = dict(verification='baton.verifier', review='baton.approver-review',
                approval='baton.approver')

# THE SEALED ACCEPTANCE GATE, and the two groups in it are there for two
# different reasons.
#
#   * NINE EXISTING MODULES that must still pass. They are the producers and
#     consumers this correction moves -- the status document and its contracts,
#     the canonical observation, the read-only tool, the reclaim, the token
#     lifecycle, the attempt readers, the newest read-only projection, and the
#     contracts inventory that holds a new contract to the table. Measured
#     against a clean export of the declared base: 1091 tests, all passing,
#     zero skips, 11.83s.
#   * TWO NEW MODULES, named as a CONVENTION because a sealed argv cannot name
#     classes that do not exist yet. They do not exist at the base, so this
#     gate FAILS until the turn creates them -- which is the point.
#
# TWO MODULES ARE DELIBERATELY ABSENT and `PACKET.md` records why for each:
# `tests.manager.test_boundary_inventory` does not pass at this base (328
# tests, 28 failures, 1 error, 49.469s measured alone on base bytes) and would
# exceed the 30s ceiling by itself; `tests.tools.test_packaging` holds the
# source command table against the INSTALLED bundle, which predates `record`
# and `disposition`, and inside a private checkout it SKIPS -- which this
# program refuses. The packaged-table obligation moves to a source-level case
# in the new tools module instead.
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
# in-process only -- the 329810 revision of the reference program lost a case
# for exactly that reason. It OVERWRITES rather than extends, so whatever
# `PYTHONPATH` the runtime happened to export cannot leak in.
#
# AND IT ADMITS NO SKIP. A skipped case in this gate is an unproven obligation
# wearing a passing exit status, so the program refuses one and prints which.
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

# PROPOSED, AND ONE OF THEM IS NOT THIS PACKET'S TO SET. One provider ceiling
# of 3600s with 60s reserved cleanup inside a 4800s total, one implementation
# invocation, no automatic retry, `report-and-hold`. These are an estimate for
# one invocation -- not a correctness guarantee, not an authorization, and the
# owner still selects execution.
#
# `verification_command_seconds` IS FIXED AT 30 BY THE COMPOSER, in both places
# it appears (`baseline_bindings.py:345`, the execution policy whose digest the
# submission carries, and `:522`, the submission's own `execution_limits`),
# with no compose parameter and no bounds member. `LIMITS-CHECK.json` reports
# what the generated documents actually say rather than what prose wishes, and
# `TASK.md` carries the 11.83s measurement that makes 30s workable for the nine
# existing modules -- leaving roughly 18s for the two new ones, which is a real
# constraint on them and is stated as one.
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
    if provenance['checkpoint']['paths']:
        raise RuntimeError('this preparation carries no restored buffer, and '
                           'the provenance declares one')
    # EVERY TASK INPUT MUST EXIST NOW, because the turn cannot proceed without
    # one and discovering that inside a provider turn wastes the whole turn.
    # Their exact bytes are pinned by `bind` as the packet's own fixture.
    for name in doc['task_inputs']:
        if not (REPO / name).is_file():
            raise RuntimeError('declared task input is absent: ' + name)
    # THE GATE'S NEW MODULES MUST NOT EXIST YET. If one did, the sealed argv
    # would be naming something the base already carries, and this packet would
    # be describing a correction that has partly happened outside v12.
    for name in ('v12/python/tests/manager/test_attempt_failure_cause.py',
                 'v12/python/tests/tools/test_attempt_diagnostics.py'):
        if (REPO / name).exists():
            raise RuntimeError('a gate module the turn must create already '
                               'exists on the host: ' + name)
    return doc


def stage(root):
    selected = pins()
    if not root.is_absolute() or root == REPO or REPO in root.parents:
        raise RuntimeError('select a fresh absolute external preparation root')
    # EVERY BASE BYTE IS RESOLVED AND PROVED BEFORE THE ROOT EXISTS.
    #
    # Measured while probing this program rather than assumed: the 329953
    # reference creates the root and writes its 112 manager files first, and
    # validates the three supervisor digests afterwards -- so a supervisor
    # drift left a HALF-STAGED root behind, which the "refuse reuse" rule in
    # the line above then blocks forever. The owner's repair for a refused
    # stage would have been to delete a directory this packet had just made.
    #
    # So the whole read happens first, in memory, and the root is created only
    # once there is nothing left that can refuse. A refused stage now leaves
    # the filesystem exactly as it found it.
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
                                   source=str(REPO), instance=str(instance)))
    print('staged; bootstrap separately with --no-repositories, then bind')


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
    # fixture so `held_packet` refuses a drifted one BEFORE any store opens.
    # They are READ from the read-only mount and never written back.
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
        provider_network='bridge', run_id=RUN, work='W333486', claim=333504,
        note='Typed actionable attempt-failure capture at the reclaim '
             'boundary, one composed cause with explicit unknown carried to '
             'ordinary status, and one supported read-only diagnostic report '
             'on the packaged surface; retained proposal requires separate '
             'independent review, with no automatic integration and no '
             'acceptance.',
        bounds=BOUNDS, context_mode='fresh',
        task_instructions=(HERE / 'TASK.md').read_text(),
        verification=VERIFICATION)
    places = baseline_bindings.write(str(root / 'packet'), docs)
    baseline.held_packet(places['PACKET.json'])
    baseline.verify_imported_sources(docs['PACKET.json'])
    emit(root / 'PREPARED.json', dict(
        state='prepared-not-executed', work='W333486', authority_uuid=uuid,
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
