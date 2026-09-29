"""Owner-operated W257627 preparation only. Never submits or starts a Job.

The default command is read-only. --prepare performs the reviewed setup under
fresh operational roots. Failure preserves partial outputs and refuses rerun.
Git mutations are performed only by the supported owner bootstrap repository
preparer in new repositories, never in the source checkout.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SPEC = HERE / 'OPERATOR-SPEC-302029.json'


def refuse(message):
    raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regular(path):
    p = Path(path)
    if p.resolve() != p.absolute() or not stat.S_ISREG(p.lstat().st_mode):
        refuse('not a canonical regular file: ' + str(p))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, indent=2, sort_keys=True) + '\n')


def command(argv, *, env=None):
    result = subprocess.run(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    if result.returncode:
        # None of the permitted commands reads bearer bytes.
        refuse('command failed: ' + repr(argv) + '\n' + result.stderr.decode(errors='replace'))
    return result.stdout


def git_env():
    env = dict(os.environ)
    for key in list(env):
        if key.startswith('GIT_'):
            del env[key]
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0')
    return env


def git_read(repo, *args):
    if args[0] not in ('rev-parse', 'show', 'cat-file'):
        refuse('preparation reader accepts read-only Git operations')
    return command(['git', '-C', str(repo), *args], env=git_env())


def fresh(spec):
    roots = [Path(spec[k]) for k in ('instance_root', 'artifact_root')]
    for p in roots:
        if not p.is_absolute() or p.resolve() != p or os.path.lexists(p):
            refuse('fresh canonical root required; preserve existing state: ' + str(p))
        if not p.parent.is_dir():
            refuse('root parent is unavailable: ' + str(p.parent))
    if any(a == b or a in b.parents for a in roots for b in roots if a != b) or roots[0] == roots[1]:
        refuse('operational roots must be distinct and disjoint')


def preflight(spec, *, inspect_image=True):
    fresh(spec)
    if os.getuid() != 1000 or os.getgid() != 1000:
        refuse('reviewed host identity is uid/gid1000; do not run as root')
    if sha(Path(sys.executable).resolve()) != spec['python_sha256']:
        refuse('Python executable differs from the reviewed interpreter')
    repo = Path(spec['repository'])
    for name, expected in spec['files'].items():
        p = repo / name
        regular(p)
        if sha(p) != expected:
            refuse('candidate drift: ' + name)
    for name, expected in spec['recipe_files'].items():
        p = HERE / name
        regular(p)
        if sha(p) != expected:
            refuse('recipe drift: ' + name)
    runtime = Path(spec['installation_runtime'])
    actual = {str(p.relative_to(runtime)): sha(p) for p in runtime.rglob('*') if p.is_file() and not p.is_symlink()}
    if any(p.is_symlink() for p in runtime.rglob('*')) or runtime.resolve() != runtime or actual != spec['installation_files']:
        refuse('installation runtime drift')
    if git_read(repo, 'rev-parse', 'HEAD').decode().strip() != spec['base']:
        refuse('source HEAD changed; retain packet for rebinding review')
    for name, expected in spec['task_files'].items():
        if hashlib.sha256(git_read(repo, 'show', spec['base'] + ':' + name)).hexdigest() != expected:
            refuse('committed task input differs: ' + name)
    if inspect_image:
        held = json.loads(command(['docker', 'image', 'inspect', spec['image_reference'], '--format', '{{json .Id}}']))
        if held != spec['image_digest']:
            refuse('local image differs from selected digest')
    return {'fresh_roots': [spec['instance_root'], spec['artifact_root']], 'candidate_files': len(spec['files']), 'base': spec['base'], 'image_inspected': inspect_image, 'effects': False}


def freeze(spec, root):
    """Copy only pinned source files; never copy/load bytecode caches."""
    repo = Path(spec['repository'])
    destination = root / 'manager-source'
    for name, expected in spec['files'].items():
        source = repo / name
        regular(source)
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            refuse('candidate changed during freeze: ' + name)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(raw)
    return destination


def prepare(spec, *, repository_preparer=None):
    """Called only after read-only preflight; injection is a deterministic test seam."""
    fresh(spec)
    root = Path(spec['instance_root'])
    root.mkdir(mode=0o700)  # Exclusive reservation; no adoption of existing state.
    evidence = root / 'preparation'
    evidence.mkdir(mode=0o700)
    write(evidence / 'selected-inputs.json', spec)
    try:
        frozen = freeze(spec, root)
        python = frozen / 'v12/python'
        helpers = frozen / spec['helper_relative']
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(helpers), str(python / 'src'), str(python)]
        from tools import bootstrap, instance, user_credentials
        from baton_v12.authority import Authority
        import baseline
        import baseline_bindings
        import prepare_instance
        # Refuse ambient source imports; owner runs this as a fresh process.
        for name, module in tuple(sys.modules.items()):
            if name.split('.')[0] in ('baton_v12', 'tools', 'baseline', 'baseline_bindings', 'prepare_instance') and getattr(module, '__file__', None):
                if frozen not in Path(module.__file__).resolve().parents:
                    refuse('module imported outside frozen candidate: ' + name)
        registry = user_credentials._proved_read(spec['credential_registry'], limit=user_credentials.MAX_REGISTRY_BYTES, what='the credential source registry')
        entries = user_credentials.held_registry(json.loads(registry))
        selected = [e for e in entries if (e['provider'], e['reference']) == ('operator-file', 'w202663-development')]
        if len(selected) != 1:
            refuse('selected credential reference is unavailable')
        s = os.lstat(selected[0]['path'])
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o600 or not s.st_size:
            refuse('selected credential source metadata is not private/nonempty')
        # Never resolve/read bearer bytes during preparation.
        bootstrap_input = json.loads((frozen / spec['bootstrap_relative']).read_text())
        bootstrap_input['state_root'] = str(root)
        write(evidence / 'bootstrap-inputs.json', bootstrap_input)
        with (evidence / 'bootstrap.log').open('x') as stream:
            boot = bootstrap.prepare(bootstrap_input, stream=stream)
        write(evidence / 'bootstrap-result.json', boot)
        def repository_runner(argv, **options):
            options['timeout'] = 120
            options['env'] = git_env()
            result = subprocess.run(argv, **options)
            with (evidence / 'repository-commands.jsonl').open('a') as log:
                log.write(json.dumps({'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}) + '\n')
            return result
        with (evidence / 'repositories.log').open('x') as stream:
            repositories = (repository_preparer or bootstrap.prepare_repositories)(bootstrap_input, instance.layout(str(root)), source=spec['repository'], stream=stream, runner=repository_runner)
        write(evidence / 'repositories-result.json', repositories)
        source = Path(instance.layout(str(root))['repository']) / 'workspace'
        if git_read(source, 'rev-parse', 'HEAD').decode().strip() != spec['base']:
            refuse('prepared independent source HEAD differs from declared base')
        for name, expected in spec['task_files'].items():
            regular(source / name)
            if sha(source / name) != expected:
                refuse('prepared task input differs: ' + name)
        # Preserve the historical installation artifact as such. The emitted
        # supervisor/status commands import the corrected frozen source above.
        runtime = root / 'installation-runtime'
        shutil.copytree(spec['installation_runtime'], runtime)
        if instance.manifest(str(runtime))['entries'] != spec['installation_files']:
            refuse('copied installation runtime differs')
        uuid = boot['authority_uuid']
        stores = boot['places']
        participants = {'work_id': uuid[:8] + '-W1', 'implementation': 'baton.impl', 'review': 'baton.review', 'receipts': bootstrap_input['receipt_participants'], 'worker_files': spec['worker_files'], 'fixture_files': spec['task_files']}
        with Authority.open(stores['authority_store'], expected_authority_uuid=uuid) as authority:
            participants['implementation_principal'] = authority.principal_of(participants['implementation'])
            participants['review_principal'] = authority.principal_of(participants['review'])
        selected_instance = {name: stores[name] for name in ('authority_store', 'job_store', 'control_store', 'integration_store')}
        selected_instance.update(authority_uuid=uuid, integration_profile=bootstrap_input['integration_profile'], retention_policy_digest=bootstrap_input['retention_policy_digest'], runtime_path=str(runtime), build_commit=spec['installation_build'])
        task = (source / spec['task_relative']).read_text()
        task += '\nThe supplied excerpt is at ' + spec['excerpt_relative'] + '; read only that source document.\n'
        chosen = dict(instance=selected_instance, source_root=str(source), image_reference=spec['image_reference'], image_digest=spec['image_digest'], cli_build='2.1.247', manager_source=str(python), supervisor_path=str(helpers / 'baseline.py'), vectors=str(frozen / spec['vectors_relative']), participants=participants, credential_sources=spec['credential_registry'], credential_profile={'claude': {'provider': 'operator-file', 'reference': 'w202663-development'}}, evidence_digest='sha256:' + spec['accepted_candidate_sha256'], provider_network='bridge', run_id=spec['run_id'], work='W257627', claim=302029, note='Owner-operated preparation under301930/302026; one useful documentation Job, no automatic integration.', code_boundary=str(frozen), context_mode='fresh', task_instructions=task, verification=['python3', '-c', "from pathlib import Path; p=Path('docs/v12-first-job-inspection.md'); assert p.is_file(); assert len(p.read_text().splitlines()) < 100"])
        selections = evidence / 'selections.json'
        write(selections, {'compose': chosen})
        with (evidence / 'prepare-instance.json').open('x') as stream:
            prepare_instance.main(['--selections', str(selections), '--base', spec['base']], stream=stream)
        documents = baseline_bindings.compose(base=spec['base'], run_root=spec['artifact_root'], **chosen)
        with Authority.open(stores['authority_store'], expected_authority_uuid=uuid) as authority:
            notices = baseline_bindings.preflight(authority, documents, participants)
        if any(not n.startswith('UNVERIFIABLE HERE:') for n in notices):
            refuse('Authority preparation preflight: ' + repr(notices))
        write(evidence / 'authority-preflight.json', {'notices': notices, 'route_and_scoped_grants': 'performed by supported prepare_instance; see captured result'})
        paths = baseline_bindings.write(spec['artifact_root'], documents)
        baseline.held_packet(paths['PACKET.json'])
        write(evidence / 'packet-files.json', {name: {'path': str(path), 'sha256': sha(path)} for name, path in paths.items()})
        # No operations_from, baseline.prepare/supervise, manager serve/start,
        # submission, profile qualification run, engine create/run or model call.
        write(evidence / 'COMPLETE.json', {'preparation_complete': True, 'job_started': False, 'authority_uuid': uuid, 'work_id': participants['work_id'], 'commands': paths['commands.json'], 'packet': paths['PACKET.json'], 'next': 'Independent inspection/review before owner executes emitted start. Stop/status instructions are in commands.json; final human command sheet follows that review.'})
        return str(evidence / 'COMPLETE.json')
    except Exception as error:
        write(evidence / 'FAILED.json', {'type': type(error).__name__, 'message': str(error), 'action': 'Preserve all outputs; do not rerun or remove roots. Return evidence for bounded continuation.'})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Owner only: perform fresh preparation after independent script review; never start Job')
    args = parser.parse_args()
    spec = json.loads(SPEC.read_text())
    print(json.dumps(preflight(spec), indent=2), flush=True)
    if args.prepare:
        print(prepare(spec), flush=True)
    else:
        print('Read-only checks passed; no roots created. Reviewed owner setup command adds --prepare.')


if __name__ == '__main__':
    main()
