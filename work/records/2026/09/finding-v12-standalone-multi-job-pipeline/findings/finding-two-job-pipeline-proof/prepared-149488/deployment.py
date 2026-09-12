"""W71879 future run8 preparation packaging and public-API provisioning; never submits a Job.

prepare writes review inputs beside this script. validate uses a fresh /tmp
Authority to validate the bootstrap/document logic without a runtime. provision
requires selected image evidence and the operator's Git repositories, then
writes only this run's external roots. No raw store access or Git mutation.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from baton_v12.authority import Authority
from baton_v12.contracts import digest, digest_of_bytes
from baton_v12.contracts.manifest import check_manifest_structure
from baton_v12.job_manager.documents import owned_submission
from baton_v12.worker_manager import source_boundary
from tools import dogfood_operator, stage_execution
from target_posture import check_target, manager_git_environment

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parent
CONFIG = HERE / 'frozen-config'
REPO = Path('/home/sl/src/baton')
RUN = Path('/home/sl/.local/state/baton/v12/w71879-run8')
UUID = 'c71879b2000000000000000000000001'
BASE = '2fbb2d456638e5706218020aebfa47f0a82c8920'
TREE = '3492ba64448ab9d39bde53ee6456ce24e74ece2c'
PROVIDER_BASE = 'sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4'
CREATED = '2026-09-12T03:32:20.835Z'
SCOPE = 'scope:w71879-run8'
PROFILE = 'claude-w71879-run8'
REGISTRY = '/home/sl/.baton/credential-sources.json'
CREDENTIAL = {'provider': 'operator-file', 'reference': 'w64268-run1'}
ACTORS = {name: 'baton.proof-' + name for name in
          ('impl-a', 'impl-b', 'review-a', 'review-b', 'integrator',
           'verification', 'review', 'approval', 'observer')}
WORKS = {name: UUID[:8] + '-W' + str(number) for number, name in
         enumerate(('a', 'b', 'verification', 'review', 'approval'), 1)}
ROOT_PATH = str(DOSSIER.relative_to(REPO))


def write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')


def sha(path):
    return digest_of_bytes(path.read_bytes())


def git_read(place, *args):
    return subprocess.run(['git', '--no-optional-locks', '-C', str(place), *args], check=True,
                          capture_output=True, text=True, timeout=10, env=manager_git_environment(RUN / 'target')).stdout.strip()


def baseline():
    check_target(RUN / 'target')
    answer = {}
    for name in ('source', 'target'):
        place = RUN / name
        identity = git_read(place, 'show', '--no-patch', '--format=%H %T', 'HEAD')
        if identity != BASE + ' ' + TREE or git_read(place, 'status', '--porcelain'):
            raise RuntimeError(name + ' is not the clean operator baseline')
        answer[name] = {'path': str(place), 'commit': BASE, 'tree': TREE}
        for original in sorted((DOSSIER / 'prepared-141510/baseline').rglob('*')):
            if original.is_file():
                rel = original.relative_to(DOSSIER / 'prepared-141510/baseline')
                if (place / rel).is_symlink() or (place / rel).read_bytes() != original.read_bytes():
                    raise RuntimeError('operator baseline bytes differ: ' + str(rel))
    return answer


def task_documents():
    a = (DOSSIER / 'prepared-141510/task-a.md').read_text()
    b = (DOSSIER / 'prepared-141510/task-b.md').read_text()
    requests = {'a': (a, 'check_greeting.py'), 'b': (b, 'check_hours.py')}
    duties = {
        'verification': 'Assess whether the delivered causal observations and the actual self-contained check_hours.py establish absent hours behavior on the original base and correct hours/minutes behavior on isolated B and merged B. An unrelated error or unconditional success is insufficient.',
        'review': 'Review the actual merged candidate for correctness and permitted scope. Preserve A and the existing minutes behavior, inspect the new hours implementation and tests, and explain any defect or unauthorized edit.',
        'approval': 'Decide whether this exact merged candidate is acceptable under the supplied task scope, causal evidence and dispatch policy. This is your own independent approval judgment. Original authorization and the other concurrent judges reports are not delivered here; do not claim you read them. Their correlation is performed by their actual owners after judgments return.'}
    for name, duty in duties.items():
        instructions = ('Read /input/judgment.json and the read-only /input/source. '
                        'Judge only the supplied exact candidate and delivered evidence. '
                        'Return an honest accepted/rejected/changes-requested verdict with nonempty findings in the ordinary baton.review-report/1 report. '
                        'Do not modify source or invent receipts.\n\n' + duty +
                        '\n\nThe complete accepted task scope follows. A is already landed; B is being merged.\n\n' + a + '\n\n' + b)
        requests[name] = (instructions, 'check_hours.py')
    return {name: {'schema': 'baton.dogfood-task/2', 'task_id': 'w71879-run8-' + name,
                   'instructions': instructions, 'source_root': 'source',
                   'source_profile': 'git-line', 'declared_base': BASE,
                   'verification': ['python3', check]}
            for name, (instructions, check) in requests.items()}


def policy_documents():
    return {
        'policy': {'work': 'W71879', 'ruling': 'M141636/return149484; run8 preparation and exactly one operator attempt after independent input review authorized; no agent model execution or automatic retry', 'base': BASE,
                   'scope': SCOPE, 'automatic_retry': False, 'ordinary_operator_transitions': 0,
                   'submission': ['job-a', 'job-b'], 'review_before_execution': True},
        'resource_policy': {'wall_seconds': 1200, 'implementation_attempt_seconds': 240,
                            'review_or_judge_attempt_seconds': 180, 'integration_seconds': 120,
                            'runtime_cpus': 2, 'runtime_memory_bytes': 2147483648,
                            'runtime_pids': 512, 'scratch_mounts': [list(item) for item in source_boundary.SCRATCH_MOUNTS],
                            'workspace_declared_capacity_bytes': 536870912,
                            'workspace_capacity_is_quota': False,
                            'run_storage_stop_bytes': 17179869184, 'sample_seconds': 1,
                            'deadline_action': 'exceptional stop; retain evidence; no retry or success repair'},
        'network_policy': {'engine_network': 'bridge', 'purpose': 'selected Claude provider authentication and model requests'},
        'mount_policy': {'source': 'read-only original source and manager-held private git-line',
                         'mutable_storage': str(RUN / 'storage'), 'workspace_group': 1001,
                         'target': str(RUN / 'target'), 'target_reference': 'refs/heads/main'},
        'tool_policy': {'provider_arguments': ['--print', '--dangerously-skip-permissions', '--output-format', 'json'],
                        'model_selection': 'provider default; no distinct-model guarantee',
                        'verification': [['python3', 'check_greeting.py'], ['python3', 'check_hours.py']],
                        'final_verification': ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-v']},
        'credential_policy': {'registry': REGISTRY, 'slots': {'claude': CREDENTIAL},
                              'payload_in_configuration': False, 'every_judge_configured': True},
        'retention_policy': {'disposition': 'retain', 'root': str(RUN), 'automatic_deletion': False}}


def bootstrap(authority_path):
    authority = Authority.create(str(authority_path), authority_uuid=UUID)
    try:
        authority.set_policy('canonical_target', BASE)
        authority.certify_contract('v12-assignment-1', profile=PROFILE)
        for name, actor in ACTORS.items():
            authority.bind_endpoint(actor, 'principal:w71879-run8-' + name)
        for name in ('a', 'b'):
            authority.add_route_handler('proof-impl-' + name, ACTORS['impl-' + name])
            authority.add_route_handler('proof-review-' + name, ACTORS['review-' + name])
            authority.create_work(WORKS[name], 'proof-impl-' + name, contract='v12-assignment-1',
                                  scope=SCOPE, operation_id='provision-job-' + name)
        authority.add_route_handler('proof-integration', ACTORS['integrator'])
        for name, grant in (('verification', 'verify'), ('review', 'review'), ('approval', 'approve')):
            authority.add_route_handler('proof-judge-' + name, ACTORS[name])
            authority.create_work(WORKS[name], 'proof-judge-' + name, contract='v12-assignment-1',
                                  scope=SCOPE, operation_id='provision-judge-' + name)
            authority.grant_capability(ACTORS[name], grant, scope=SCOPE)
        authority.grant_capability(ACTORS['integrator'], 'integrate', scope=SCOPE)
        return {'authority_uuid': authority.authority_uuid, 'policy_generation': authority.policy_generation(),
                'principals': {name: authority.principal_of(actor) for name, actor in ACTORS.items()},
                'works': {name: authority.project_work(work) for name, work in WORKS.items()},
                'grants': {name: authority.grants_of(actor) for name, actor in ACTORS.items()}}
    finally:
        authority.dispose()


def documents(destination, images, authority_facts):
    """Render complete final schemas. Image selection is an explicit input."""
    policies = policy_documents()
    policy_digests = {name + '_digest': digest(value) for name, value in policies.items()}
    for name, value in policies.items():
        write_json(destination / 'policies' / (name + '.json'), value)
    profile = {'name': PROFILE, 'provider': 'Claude CLI', 'selected_base': PROVIDER_BASE,
               'image_variants': images, 'source_profile': 'git-line',
               'roles': ['implementation', 'review', 'integration'],
               'model_selection': 'provider default; shared installation, distinct principals and fresh contexts',
               'credentials': CREDENTIAL, 'network': 'bridge'}
    write_json(destination / 'runtime-profile.json', profile)
    profile_digest = digest(profile)
    toolchain = {'provider_base_image': PROVIDER_BASE,
                 'image_variants': images, 'worker_source_manifest': sha(HERE / 'image-context-manifest.json')}
    write_json(destination / 'toolchain.json', toolchain)
    role_instructions = {'a': sha(DOSSIER / 'prepared-141510/task-a.md'),
                         'b': sha(DOSSIER / 'prepared-141510/task-b.md'),
                         'judges': 'complete scope embedded; judgment.json and read-only source only'}
    write_json(destination / 'role-instructions.json', role_instructions)
    binding = {'root': 'baton', 'path': ROOT_PATH, 'finding_digest': sha(HERE / 'record-snapshot/FINDING.md'),
               'plan_digest': sha(HERE / 'record-snapshot/PLAN.md')}
    tasks = task_documents()
    for name, task in tasks.items():
        write_json(destination / 'tasks' / (name + '.json'), task)
    instructions = ('Import exactly the genuinely accepted candidate from the supplied bundle into the configured target. '
                    'Judge scope against the full candidate and retained independent review/task evidence. '
                    'Respect the specifically scheduled existing greeting test change and preserve unrelated files. '
                    'Refuse unauthorized changes rather than correcting them. Run the supplied required verification and report the actual result.\n\n' +
                    tasks['a']['instructions'] + '\n\n' + tasks['b']['instructions'])
    instructions += """

Provider completion contract (existing baton.integration-report/1)

After the bounded import/verification task, write one UTF-8 JSON object to the
private report path supplied below under this runtime's exact operands, then
end the provider turn. Write only this provider report outside the target. Do
not publish the manager's integration-result, change version-control state,
repair permissions or bypass any before-write scope, review, base, path, type,
mode or ownership check. Preserve all full-task and existing-test requirements.
Do not start another import or verification attempt, hide a failure or extend
the deadline to produce a successful report.

The object has exactly these eight keys, with no extra diagnostics:
- schema: the literal string "baton.integration-report/1".
- assignment_digest: copy the exact digest string from "The assignment it answers
  is" in this runtime's exact operands below, including its sha256: prefix.
- bundle_digest: copy the exact digest string from "Its measured identity is"
  in this runtime's exact operands below, including its sha256: prefix.
  Never invent either digest, use an earlier run's identity or substitute a
  candidate/blob/instructions digest. Do not put placeholder text in the report.
- outcome: one of ["imported", "refused", "held"]. Report what actually happened:
  imported claims a completed exact import; refused reports inability to proceed;
  held reports an incomplete or uncertain operation. These are provider claims,
  not manager settlement or terminal acceptance.
- phase: one of ["preflight", "import", "verification"], naming where you stopped.
- paths: a sorted, unique JSON array of repository-relative paths actually
  changed, bounded by the supplied path table (at most 251). Use [] if none
  changed. Do not claim planned changes as performed changes.
- verification: null if you did not perform verification; otherwise an object
  with exactly argv and status. argv is the actual nonempty command array of
  nonempty strings; status is the observed integer exit status, or null if no
  exit status was obtained. Never substitute zero for a failed, unperformed or
  unfinished check. Preserve the actual nonzero or unavailable result.
- code: null only for outcome imported; otherwise one of ["scope-exceeded",
  "path-unsupported", "target-drift", "target-unwritable", "verification-failed",
  "partial-import", "provider-unable"], chosen for the actual refusal/hold.

An imported claim requires the completed exact candidate at every scheduled
path, phase "verification", the complete sorted scheduled path list, and code
null. If verification was performed and failed or did not finish, report that
failure/uncertainty with the matching refused/held outcome and code, never a
successful import claim. The verification field may be null when the provider
did not run the check; this does not assert that verification passed. The
runtime still independently reads back the target, runs the scheduled check,
and reads back again before composing its own integration result. A valid
report shape alone establishes neither import nor successful verification.
Bound the report to 65536 UTF-8 bytes. Write the private report and end the turn
promptly after this bounded task; do not wait for the manager's settlement.
"""
    instructions += """

Integration Git reads: every Git read must use git --no-optional-locks (place
--no-optional-locks before the subcommand). Ordinary git status or git diff may
refresh the index even when nothing is staged, changing the repository witness.
For example, use git --no-optional-locks status --porcelain and git
--no-optional-locks diff. This permits reads only: do not stage, commit, reset,
change refs/configuration, repair the index or otherwise mutate version-control
state. Preserve every existing scope, review, target, verification and report
requirement. If a required read cannot be performed under these constraints,
stop and report the actual refusal/hold under the existing report contract.
"""
    (destination / 'integration-instructions.txt').write_text(instructions)
    empty = {'entries': [], 'entry_count': 0, 'total_bytes': 0,
             'tree_digest': stage_execution.single_worker.EMPTY_TREE_DIGEST}
    manifests = {}

    def manifest(name, image):
        task_path = destination / 'tasks' / (name + '.json')
        payload = task_path.read_bytes()
        given = dogfood_operator.input_manifest(
            work_ref={'authority_uuid': UUID, 'work_id': WORKS[name]}, staged=empty,
            created_at=CREATED, manifest_id='w71879-run8-' + name,
            assignment_contract='v12-assignment-1',
            human_contract={'artifact_id': 'w71879-task-' + name, 'media_type': 'application/json',
                            'bytes': len(payload), 'content_digest': digest_of_bytes(payload),
                            'locator': 'artifact://contracts/w71879-task-' + name},
            record_binding=binding, role_instructions_digest=digest(role_instructions),
            runtime_profile_digest=profile_digest, toolchain_digest=digest(toolchain),
            worker_image_digest=image, policies=policy_digests)
        given['sources'][0]['consumption'] = source_boundary.source_consumption('git-line')
        constraints = {'max_bytes': 67108864, 'max_entries': 2000,
                       'allowed_media_types': ['application/octet-stream', 'text/plain'],
                       'link_policy': 'forbid', 'validator_digest': None}
        given['outputs'] = [{'name': n, 'type': t, 'path': n, 'required': False,
                             'constraints': constraints} for n, t in
                            (('proposal', 'git-change-proposal'), ('findings', 'directory-result'), ('logs', 'directory-result'))]
        given.pop('manifest_digest')
        given['manifest_digest'] = digest(given)
        return check_manifest_structure(given, 'inputManifest')

    for name in tasks:
        manifests[name] = manifest(name, images['provider'])
        write_json(destination / 'manifests' / (name + '.json'), manifests[name])
    integrator_manifest = manifest('a', images['integration'])
    write_json(destination / 'manifests/integrator.json', integrator_manifest)

    def deployment(actor, name, role, route, *, integration=False):
        given = {'schema': 'baton.v12.single-worker-deployment/4',
                 'authority_store': str(RUN / 'authority.sqlite3'), 'authority_uuid': UUID,
                 'participant': ACTORS[actor], 'principal': authority_facts['principals'][actor],
                 'profile_name': PROFILE, 'profile_digest': profile_digest,
                 'policy_digest': policy_digests['policy_digest'], 'adapter_name': 'docker-single-worker',
                 'adapter_digest': sha(REPO / 'v12/python/src/baton_v12/worker_manager/oci.py'),
                 'engine': 'docker', 'image_digest': images['integration' if integration else 'provider'],
                 'network': 'bridge', 'workspace_storage': str(RUN / 'storage'), 'workspace_group': 1001,
                 'launch_home': str(RUN / 'launch' / actor), 'credential_home': str(RUN / 'credentials' / actor),
                 'credential_sources': REGISTRY, 'credential_slots': ['claude'],
                 'credential_profile': {'claude': CREDENTIAL}, 'nominated_source': str(RUN / 'source'),
                 'workspace_capacity': {'max_bytes': 536870912},
                 'input_manifest': integrator_manifest if integration else manifests[name],
                 'task_document': str(destination / 'tasks' / (name + '.json')),
                 'launch_contract': 'v12-assignment-1', 'launch_role': role, 'review_route': route,
                 'retention_policy_digest': policy_digests['retention_policy_digest'], 'retention_disposition': 'retain'}
        write_json(destination / 'workers' / (actor + '.json'), given)
        return given

    workers = []
    for name in ('a', 'b'):
        for role, actor, route in (('implementation', 'impl-' + name, 'proof-review-' + name),
                                   ('review', 'review-' + name, 'proof-integration')):
            workers.append({'worker_id': actor, 'role': role, 'deployment': deployment(actor, name, role, route)})
    workers.append({'worker_id': 'integrator', 'role': 'integration',
                    'deployment': deployment('integrator', 'a', 'integration', 'proof-integration', integration=True)})
    judges = {name: {'worker_id': 'judge-' + name,
                     'deployment': deployment(name, name, 'review', 'proof-judge-' + name)}
              for name in ('verification', 'review', 'approval')}
    config = {'schema': 'baton.v12.stage-execution-deployment/2',
              'authority_store': str(RUN / 'authority.sqlite3'), 'authority_uuid': UUID,
              'integration_store': str(RUN / 'integration.sqlite3'), 'state_root': str(RUN / 'state'),
              'pool_generation': 1, 'policy_generation': authority_facts['policy_generation'],
              'line_declared_base': BASE, 'receipt_participants': {name: ACTORS[name] for name in judges},
              'job_work_id': WORKS['a'], 'review_work_id': WORKS['a'], 'canonical_target_id': 'w71879-target',
              'checkpoint_profile': 'git',
              'integration_profile': {'profile_kind': 'git', 'profile_version': 1,
                                      'integrator_participant': ACTORS['integrator'],
                                      'instructions_digest': sha(destination / 'integration-instructions.txt')},
              'retention_policy_digest': policy_digests['retention_policy_digest'], 'retention_disposition': 'retain',
              'workers': workers, 'result_judgment_workers': {'job-b': judges},
              'job_bindings': [{'job_id': 'job-' + name, 'job_work_id': WORKS[name], 'review_work_id': WORKS[name],
                                'line_declared_base': BASE, 'canonical_target_id': 'w71879-target',
                                'source_worker_id': 'impl-' + name} for name in ('a', 'b')],
              'integration_target': str(RUN / 'target'), 'integration_target_reference': 'refs/heads/main',
              'integration_workspace': str(RUN / 'integration-workspace'), 'integration_observer': ACTORS['observer'],
              'integration_instructions': str(destination / 'integration-instructions.txt')}
    stage_execution.held_configuration(config)
    jobs = []
    for name in ('a', 'b'):
        dep = {'implementation': [], 'review': [{'job_id': 'job-' + name, 'kind': 'implementation'}],
               'integration': ([{'job_id': 'job-a', 'kind': 'review'}, {'job_id': 'job-b', 'kind': 'review'}]
                               if name == 'a' else [{'job_id': 'job-b', 'kind': 'review'}, {'job_id': 'job-a', 'kind': 'integration'}])}
        jobs.append({'job_id': 'job-' + name, 'input_digest': manifests[name]['manifest_digest'],
                     'policy_digest': policy_digests['policy_digest'],
                     'test_scope': ['tests/test_greeting.py'] if name == 'a' else [], 'terminal_policy': 'report-and-hold',
                     'stages': [{'kind': kind, 'work_id': WORKS[name], 'profile_name': PROFILE,
                                 'profile_digest': profile_digest, 'depends_on': dep[kind]}
                                for kind in ('implementation', 'review', 'integration')]})
    submission = {'schema': 'baton.v12.job-submission/1', 'submission_id': 'w71879-run8', 'jobs': jobs}
    owned_submission(submission)
    write_json(destination / 'stage-execution.json', config)
    write_json(destination / 'submission.json', submission)
    write_json(destination / 'authority-provisioning.json', authority_facts)
    return {'configuration': sha(destination / 'stage-execution.json'), 'submission': sha(destination / 'submission.json')}


def prepare():
    facts = baseline()
    snapshot = HERE / 'record-snapshot'
    snapshot.mkdir(exist_ok=True)
    for name in ('FINDING.md', 'PLAN.md'):
        if not (snapshot / name).exists():
            (snapshot / name).write_bytes((DOSSIER / name).read_bytes())
    context = HERE / 'image-context'
    source_names = ['worker/baton_worker.py', 'worker/claude_agent.py', 'worker/dogfood_entry.py',
                    'worker/integration_contract.py', 'worker/integration_workload.py', 'worker/integration_entry.py',
                    'worker/worker-control-1.0.schema.json', 'worker/Dockerfile.integration']
    source_names += [str(p.relative_to(REPO / 'v12')) for p in sorted((REPO / 'v12/python/src/baton_v12/source_profiles').glob('*.py'))]
    identities = {}
    for name in source_names:
        source = REPO / 'v12' / name
        target = context / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        identities[name] = {'sha256': sha(source), 'bytes': source.stat().st_size}
    write_json(HERE / 'image-context-manifest.json', identities)
    recipe = ('FROM ' + PROVIDER_BASE + '\n' +
              '\n'.join('COPY ' + name + ' /opt/baton/' + Path(name).name for name in source_names
                        if name.startswith('worker/') and name.endswith(('.py', '.json')) and 'integration_' not in name) +
              '\nCOPY python/src/baton_v12/source_profiles /opt/baton/source_profiles\n'
              'USER 65532:65532\nENTRYPOINT ["python3", "/opt/baton/dogfood_entry.py"]\n')
    (context / 'Dockerfile.provider').write_text(recipe)
    for name, task in task_documents().items():
        write_json(HERE / 'tasks' / (name + '.json'), task)
    for name, policy in policy_documents().items():
        write_json(HERE / 'policies' / (name + '.json'), policy)
    write_json(HERE / 'baseline-observation.json', facts)


def validate():
    baseline()
    started = time.monotonic()
    destination = Path(tempfile.mkdtemp(prefix='w71879-149488-validation-'))
    print('Retained validation directory:', destination, flush=True)
    facts = bootstrap(destination / 'authority.sqlite3')
    # Historical image values exercise schema composition ONLY. They are
    # explicitly not selected images, and this validation directory is never
    # the configured run root or an input to actual submission.
    hashes = documents(destination, {'provider': PROVIDER_BASE, 'integration': PROVIDER_BASE}, facts)
    report = {'kind': 'static preparation validation; no factory/stage/runtime/submission',
              'temporary_path_retained': str(destination), 'historical_image_values_are_not_selected': True,
              'public_authority_facts': facts, 'documents': hashes,
              'wall_seconds': time.monotonic() - started}
    write_json(HERE / 'validation.json', report)
    print(json.dumps({'retained': str(destination), 'wall_seconds': report['wall_seconds'], 'documents': hashes}))


def provision():
    baseline()
    source_boundary_path = RUN / 'integration-workspace'
    if git_read(source_boundary_path, 'rev-parse', '--is-bare-repository') != 'true':
        raise RuntimeError('operator must supply the private bare integration workspace')
    if 1001 not in set(os.getgroups()):
        raise RuntimeError('this manager process must hold supplementary workspace gid1001')
    images = json.loads((HERE / 'selected-images.json').read_text())
    if set(images) != {'provider', 'integration'}:
        raise RuntimeError('explicit independently reviewed provider/integration image selection required')
    config = json.loads((CONFIG / 'stage-execution.json').read_text())
    profile = json.loads((CONFIG / 'runtime-profile.json').read_text())
    if images != profile['image_variants']:
        raise RuntimeError('selected images differ from the frozen configuration')
    if (RUN / 'authority.sqlite3').exists():
        raise RuntimeError('fresh provisioning refuses an existing Authority; report partial state')
    for image in images.values():
        if subprocess.run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], check=True,
                          capture_output=True, text=True, timeout=10).stdout.strip() != image:
            raise RuntimeError('selected immutable image is unavailable')
    for path in ('storage', 'state', 'launch', 'credentials', 'evidence'):
        (RUN / path).mkdir(mode=0o700)
    for actor in ACTORS:
        (RUN / 'launch' / actor).mkdir(mode=0o700)
        (RUN / 'credentials' / actor).mkdir(mode=0o700)
    facts = bootstrap(RUN / 'authority.sqlite3')
    if facts['policy_generation'] != config['policy_generation']:
        raise RuntimeError('public bootstrap policy generation differs from the reviewed configuration')
    for worker in config['workers']:
        actor = worker['worker_id']
        if worker['deployment']['principal'] != facts['principals'][actor]:
            raise RuntimeError('public bootstrap principal differs: ' + actor)
    hashes = {'configuration': sha(CONFIG / 'stage-execution.json'), 'submission': sha(CONFIG / 'submission.json')}
    write_json(RUN / 'evidence/provisioning.json', {'authority': facts, 'documents': hashes,
                                                   'submitted': False, 'run_review_required': True})
    print(json.dumps(hashes))


def render():
    """After image build, write exact immutable run inputs within the checkout."""
    baseline()
    images = json.loads((HERE / 'candidate-images.json').read_text())
    if set(images) != {'provider', 'integration'}:
        raise RuntimeError('two actual built candidate image IDs are required')
    facts = json.loads((HERE / 'validation.json').read_text())['public_authority_facts']
    CONFIG.mkdir(exist_ok=False)
    print(json.dumps(documents(CONFIG, images, facts)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'validate', 'render', 'provision'))
    operation = parser.parse_args().operation
    {'prepare': prepare, 'validate': validate, 'render': render, 'provision': provision}[operation]()
